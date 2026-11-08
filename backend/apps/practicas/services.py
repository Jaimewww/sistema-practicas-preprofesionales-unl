"""Servicios internos de ``Practica``: transiciones (T017, T008, RF-10) y asignación
con copia de horas (T018, T010, RF-12).

Mecanismo de bajo nivel para **llamadores internos de confianza**: valida la tabla de
``data-model.md``, comprueba el permiso de las aristas que solo produce el coordinador,
exige el motivo donde lo exige el diario y escribe el estado nuevo y su
``HistorialEstado`` en una sola transacción. No es una acción pública ni un cierre:
las condiciones de RF-09 (horas, informes, evaluación) y el alcance de lectura de
RF-11 son T019/T051/T054 y no viven aquí.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.auditoria.models import MENSAJE_MOTIVO, HistorialEstado
from apps.carreras.models import ConfiguracionCarrera
from apps.practicas.models import Practica
from apps.usuarios.models import Usuario

Estado = Practica.Estado

MENSAJE_PRACTICA = "La práctica debe estar guardada para cambiar de estado."
MENSAJE_ESTADO_INVALIDO = "El estado destino no pertenece al vocabulario de Practica.Estado."
MENSAJE_TRANSICION = "Transición no permitida: de «{origen}» a «{destino}»."
MENSAJE_TERMINAL = "La práctica está en «{estado}», un estado final sin transiciones."
MENSAJE_MOTIVO_TEXTO = "El motivo debe ser texto."
MENSAJE_AUTOR = "El autor de la transición debe ser un usuario guardado."
MENSAJE_COORDINADOR = (
    "Solo el coordinador activo de la carrera de la práctica puede suspenderla, "
    "reanudarla, cancelarla o cerrarla."
)

# Las siete aristas de data-model.md; cualquier otra es ilegal.
ARISTAS = {
    Estado.ASIGNADA: {Estado.EN_CURSO},
    Estado.EN_CURSO: {Estado.EN_REVISION_FINAL, Estado.SUSPENDIDA},
    Estado.EN_REVISION_FINAL: {Estado.EN_CURSO, Estado.CERRADA},
    Estado.SUSPENDIDA: {Estado.EN_CURSO, Estado.CANCELADA},
    Estado.CERRADA: set(),
    Estado.CANCELADA: set(),
}
ESTADOS_FINALES = {Estado.CERRADA, Estado.CANCELADA}
# Motivo obligatorio al suspender y cancelar (RF-13, Clarification de spec.md);
# reanudar no lo exige. Es la misma regla que HistorialEstado.
ARISTAS_CON_MOTIVO = {
    (Estado.EN_CURSO, Estado.SUSPENDIDA),
    (Estado.SUSPENDIDA, Estado.CANCELADA),
}
# Solo el coordinador activo de la carrera de la práctica suspende, reanuda,
# cancela y cierra (spec.md Clarification, RF-13, HU-08). Las demás aristas siguen
# siendo mecanismo interno: aprobar_plan ya exige al tutor académico.
ARISTAS_DE_COORDINADOR = {
    (Estado.EN_CURSO, Estado.SUSPENDIDA),
    (Estado.SUSPENDIDA, Estado.EN_CURSO),
    (Estado.SUSPENDIDA, Estado.CANCELADA),
    (Estado.EN_REVISION_FINAL, Estado.CERRADA),
}


def _exigir_coordinador_de(practica, autor):
    """El rol y la carrera salen de la fila guardada, no del objeto del llamador."""
    fila = Usuario.objects.filter(pk=autor.pk).only("rol", "is_active", "carrera").first()
    if not (
        fila is not None
        and fila.is_active
        and fila.rol == Usuario.Rol.COORDINADOR
        and fila.carrera_id == practica.carrera_id
    ):
        raise ValidationError({"autor": [MENSAJE_COORDINADOR]})


def cambiar_estado_practica(*, practica, nuevo_estado, autor, motivo=""):
    """Cambia el estado de ``practica`` y registra el historial en una transacción.

    Decide con la fila bloqueada y recién leída, nunca con el objeto del llamador
    (puede estar obsoleto), y devuelve esa instancia guardada. ``motivo`` queda en el
    historial y, al suspender o cancelar, en el campo de motivo, conservando lo
    anterior. Suspender, reanudar, cancelar y cerrar solo los produce el coordinador
    activo de la carrera de la práctica (clave «autor»). Ante un destino malformado,
    una arista inexistente, un estado final, un autor sin permiso o un motivo ausente
    (solo al suspender y cancelar) lanza ``ValidationError`` sin dejar ninguna
    escritura. Orden de los rechazos: estado final, destino inválido, arista ilegal,
    permiso y, por último, motivo.
    """
    if not getattr(practica, "pk", None):
        raise ValidationError({"practica": [MENSAJE_PRACTICA]})
    if not isinstance(nuevo_estado, str):
        raise ValidationError({"estado": [MENSAJE_ESTADO_INVALIDO]})
    if motivo is None:
        motivo = ""
    if not isinstance(motivo, str):
        raise ValidationError({"motivo": [MENSAJE_MOTIVO_TEXTO]})
    if not getattr(autor, "pk", None):
        raise ValidationError({"autor": [MENSAJE_AUTOR]})

    with transaction.atomic():
        bloqueada = Practica.objects.select_for_update().get(pk=practica.pk)
        origen = bloqueada.estado
        if origen in ESTADOS_FINALES:
            raise ValidationError({"estado": [MENSAJE_TERMINAL.format(estado=origen)]})
        if nuevo_estado not in Estado.values:
            raise ValidationError({"estado": [MENSAJE_ESTADO_INVALIDO]})
        if nuevo_estado not in ARISTAS.get(origen, ()):
            raise ValidationError(
                {"estado": [MENSAJE_TRANSICION.format(origen=origen, destino=nuevo_estado)]}
            )
        if (origen, nuevo_estado) in ARISTAS_DE_COORDINADOR:
            _exigir_coordinador_de(bloqueada, autor)
        texto = motivo.strip()
        if (origen, nuevo_estado) in ARISTAS_CON_MOTIVO and not texto:
            raise ValidationError({"motivo": [MENSAJE_MOTIVO]})
        campos = ["estado"]
        bloqueada.estado = nuevo_estado
        if nuevo_estado == Estado.SUSPENDIDA:
            bloqueada.motivo_suspension = texto
            campos.append("motivo_suspension")
        elif nuevo_estado == Estado.CANCELADA:
            bloqueada.motivo_cancelacion = texto
            campos.append("motivo_cancelacion")
        bloqueada.save(update_fields=campos)
        registro = HistorialEstado(
            practica=bloqueada, estado_anterior=origen,
            estado_nuevo=nuevo_estado, motivo=texto, autor=autor,
        )
        registro.full_clean()
        registro.save()
    return bloqueada


MENSAJE_CONFIGURACION = (
    "No hay una configuración de carrera vigente para esa modalidad: "
    "no se puede asignar la práctica."
)
MENSAJE_AUTOR_ASIGNACION = "El autor de la asignación debe ser un usuario guardado."


def _configuracion_vigente(carrera, modalidad, hoy):
    """Configuración de esa carrera y modalidad vigente en ``hoy``, o ``None``.

    La más reciente gana; la de mayor ``pk`` resuelve el empate del mismo día.
    """
    return (
        ConfiguracionCarrera.objects.filter(
            carrera=carrera, modalidad=modalidad, vigente_desde__lte=hoy
        )
        .order_by("-vigente_desde", "-pk")
        .first()
    )


def asignar_practica(
    *, estudiante, carrera, periodo, tipo, autor,
    entidad=None, subtipo="", proyecto_vinculacion="", tutor_entidad=None,
):
    """Crea la ``Practica`` asignada y su registro inicial de historial.

    Uso interno de confianza: el día se lee con ``timezone.localdate()`` en cada
    llamada y solo cuenta la configuración de la misma carrera y modalidad con
    ``vigente_desde`` no posterior a hoy; la más reciente gana y la de mayor ``pk``
    desempata. No hay respaldo a otra carrera, otra modalidad, una configuración
    futura ni horas del sistema: sin configuración vigente lanza ``ValidationError``
    («No hay una configuración de carrera vigente para esa modalidad: no se puede
    asignar la práctica.») sin escribir nada.

    Las horas se copian de esa configuración y el estado inicial es siempre
    ``asignada``: el llamador no puede fijar ni las horas ni el estado porque no son
    parámetros. La práctica se valida con ``full_clean()`` y se guarda junto con su
    ``HistorialEstado`` inicial (sin estado anterior, con este ``autor`` persistente)
    en una sola transacción; si el diario falla, no queda la práctica.
    """
    if not getattr(autor, "pk", None):
        raise ValidationError({"autor": [MENSAJE_AUTOR_ASIGNACION]})
    practica = Practica(
        estudiante=estudiante, carrera=carrera, entidad=entidad, periodo=periodo,
        tipo=tipo, subtipo=subtipo, proyecto_vinculacion=proyecto_vinculacion,
        tutor_entidad=tutor_entidad,
    )
    # Las reglas de tipo y del vínculo externo se resuelven antes del lookup de configuración.
    practica.clean()
    with transaction.atomic():
        configuracion = _configuracion_vigente(carrera, tipo, timezone.localdate())
        if configuracion is None:
            raise ValidationError({"carrera": [MENSAJE_CONFIGURACION]})
        practica.horas_requeridas = configuracion.horas_requeridas
        practica.estado = Estado.ASIGNADA
        practica.full_clean()
        practica.save()
        registro = HistorialEstado(
            practica=practica, estado_anterior=None,
            estado_nuevo=Estado.ASIGNADA, motivo="", autor=autor,
        )
        registro.full_clean()
        registro.save()
    return practica
