"""Servicio interno de transiciones de estado de ``Practica`` (T017, T008, RF-10).

Mecanismo de bajo nivel para **llamadores internos de confianza**: valida la tabla de
``data-model.md``, exige el motivo donde lo exige el diario y escribe el estado nuevo y
su ``HistorialEstado`` en una sola transacción. No es una acción pública ni un cierre:
RF-09 y los permisos de RF-11 son T019/T024/T051/T054 y no viven aquí.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.auditoria.models import MENSAJE_MOTIVO, HistorialEstado
from apps.practicas.models import Practica

Estado = Practica.Estado

MENSAJE_PRACTICA = "La práctica debe estar guardada para cambiar de estado."
MENSAJE_ESTADO_INVALIDO = "El estado destino no pertenece al vocabulario de Practica.Estado."
MENSAJE_TRANSICION = "Transición no permitida: de «{origen}» a «{destino}»."
MENSAJE_TERMINAL = "La práctica está en «{estado}», un estado final sin transiciones."
MENSAJE_MOTIVO_TEXTO = "El motivo debe ser texto."
MENSAJE_AUTOR = "El autor de la transición debe ser un usuario guardado."

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
# Motivo obligatorio al suspender, reanudar y cancelar, igual que HistorialEstado.
ARISTAS_CON_MOTIVO = {
    (Estado.EN_CURSO, Estado.SUSPENDIDA),
    (Estado.SUSPENDIDA, Estado.EN_CURSO),
    (Estado.SUSPENDIDA, Estado.CANCELADA),
}


def cambiar_estado_practica(*, practica, nuevo_estado, autor, motivo=""):
    """Cambia el estado de ``practica`` y registra el historial en una transacción.

    Decide con la fila bloqueada y recién leída, nunca con el objeto del llamador
    (puede estar obsoleto), y devuelve esa instancia guardada. ``motivo`` queda en el
    historial y, al suspender o cancelar, en el campo de motivo, conservando lo
    anterior. Ante un destino malformado, una arista inexistente, un estado final o
    un motivo ausente lanza ``ValidationError`` sin dejar ninguna escritura.
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
