# pyright: reportMissingImports=false
"""Servicios de validación del reporte semanal: validar, devolver y reenviar (#122).

RF-03 (S3): el tutor académico valida o devuelve el reporte semanal y la
devolución exige observación. RF-04 (S4): cada decisión queda registrada en
``Validacion`` con su autor y su fecha. S5/S6: el reporte nace ``en_revision`` y
solo desde ahí se valida o se devuelve; la validación de un reporte lleva
``reporte`` (nunca ``plan``) y la ``CheckConstraint`` «exactamente uno» lo exige.

La devolución es **solo de estado**: deja la misma fila en «devuelto» para que el
estudiante corrija y reenvíe con ``reenviar_reporte``, que la vuelve a dejar
«en_revision». El reporte no tiene ``version`` (data-model §ReporteSemanal): la
que tiene versión es el plan, y esta unidad no inventa una ni migra nada (decisión
O1 del feature doc). ``validar_reporte`` no toca el plan ni el estado de la
práctica: solo marca el reporte y registra la validación. Las horas empiezan a
contar para el acumulado cuando el tutor las valida (S7); ``horas_practica`` las
proyecta en solo lectura para RF-05/HU-04 (#126), sin acumular contadores aparte.

``_exigir_tutor`` y ``_registrar_validacion`` se replican aquí con las mismas
claves de error que las de ``apps.actividades.services`` (decisión D2): el
constructor cambia ``plan`` por ``reporte`` y ningún servicio importa las
funciones privadas de otra app.

Son acciones para **llamadores internos de confianza**: no hay DTOs ni
``PermissionDenied``; el permiso se falla cerrado con ``ValidationError`` en la
clave de actor, antes que el estado, y un rechazo no escribe nada. Las tres
acciones exigen la práctica «en_curso» (CU-01 2b, ``spec.md:497``): con la
práctica suspendida, cancelada o cerrada se rechazan con la clave «practica».
"""

from contextlib import contextmanager

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.actividades.models import MENSAJE_OBSERVACION, Validacion
from apps.practicas.models import AsignacionTutor, Practica
from apps.reportes.models import (
    UMBRAL_REVISION_HORAS,
    EvidenciaReporte,
    ReporteSemanal,
)
from apps.usuarios.models import Usuario

Estado = ReporteSemanal.Estado
Decision = Validacion.Decision

MENSAJE_REPORTE = "El reporte debe estar guardado para cambiar de estado."
MENSAJE_AUTOR = "El autor de la acción debe ser un usuario guardado."
MENSAJE_ESTUDIANTE = (
    "Solo el estudiante de la práctica puede reenviar su reporte semanal."
)
MENSAJE_TUTOR = (
    "Solo el tutor académico activo de la práctica puede validar su reporte semanal."
)
MENSAJE_ESTADO_REPORTE = (
    "Transición no permitida: el reporte está en «{estado}» y solo se valida uno "
    "«en_revision»."
)
MENSAJE_PRACTICA_NO_EN_CURSO = (
    "La práctica está en «{estado}»: solo en una práctica en curso se valida, "
    "devuelve o reenvía un reporte semanal."
)
MENSAJE_REENVIO = (
    "No se puede reenviar el reporte: está en «{estado}»; "
    "solo se reenvía después de una devolución."
)


def horas_practica(practica):
    """Horas acumuladas de una práctica a partir de sus reportes guardados.

    Solo los reportes «validado» suman a ``horas_validadas`` y solo los
    «en_revision» a ``horas_en_revision``; un «devuelto» no cuenta en ninguna
    de las dos. ``horas_requeridas`` se lee de la práctica —el valor que copió
    la asignación— y ``horas_faltantes`` es la diferencia contra las validadas,
    con cero como piso para no reportar un faltante negativo.

    ``semana_en_revision`` es la señal de RF-02/S5 que el tutor ya usa: se
    enciende si algún reporte no devuelto supera ``UMBRAL_REVISION_HORAS`` (40).
    Se calcula con las horas guardadas, no con la marca ``requiere_revision``,
    para que la lectura no dependa de que esa columna esté sincronizada. Esta
    función solo lee: no crea, no actualiza y no acumula nada por su cuenta.
    """
    resumen = practica.reportes.aggregate(
        horas_validadas=Sum("horas_reportadas", filter=Q(estado=Estado.VALIDADO)),
        horas_en_revision=Sum("horas_reportadas", filter=Q(estado=Estado.EN_REVISION)),
    )
    validadas = resumen["horas_validadas"] or 0
    en_revision = resumen["horas_en_revision"] or 0
    requeridas = practica.horas_requeridas
    return {
        "horas_validadas": validadas,
        "horas_en_revision": en_revision,
        "horas_requeridas": requeridas,
        "horas_faltantes": max(0, requeridas - validadas),
        "semana_en_revision": practica.reportes.exclude(estado=Estado.DEVUELTO)
        .filter(horas_reportadas__gt=UMBRAL_REVISION_HORAS)
        .exists(),
    }


@contextmanager
def evidencias_atomicas():
    """Borra los PDF ya escritos si la operación no termina (C-03, D4/D5).

    La transacción revierte las filas, pero no los archivos: quien escribe
    evidencias registra cada ``FieldFile`` guardado en la lista que entrega este
    contexto y, ante cualquier excepción —incluido un fallo al confirmar la
    transacción que va dentro—, se eliminan antes de propagarla.
    """
    guardadas = []
    try:
        yield guardadas
    except BaseException:
        for archivo in guardadas:
            archivo.storage.delete(archivo.name)
        raise


def guardar_evidencias(*, reporte, archivos, guardadas):
    """Guarda cada PDF ya validado como evidencia de la versión actual (D2).

    El nombre del cliente queda solo en ``nombre``; el archivo va a la ruta uuid
    de ``ruta_evidencia_reporte``. Cada archivo escrito se suma a ``guardadas``
    antes de insertar su fila, para que ``evidencias_atomicas`` lo borre si una
    escritura posterior falla.
    """
    evidencias = []
    for archivo in archivos:
        evidencia = EvidenciaReporte(
            reporte=reporte,
            version=reporte.version,
            nombre=archivo.name,
            tamano_bytes=archivo.size,
        )
        evidencia.archivo.save(archivo.name, archivo, save=False)
        guardadas.append(evidencia.archivo)
        evidencia.save()
        evidencias.append(evidencia)
    return evidencias


def ultima_devolucion(reporte):
    """Última ``Validacion`` de devolución del reporte, o ``None`` si no hay.

    Es la lectura que cierra el bucle de corrección de HU-03 (RF-03, S6): el
    estudiante recupera la observación con la que el tutor devolvió su reporte.
    Se ordena por ``fecha`` y, en empate, por ``pk``: dos devoluciones del mismo
    reporte se resuelven por la última escrita y la lectura es determinista.
    Solo lee: no crea, actualiza ni borra nada.
    """
    if not getattr(reporte, "pk", None):
        return None
    return (
        Validacion.objects.filter(
            reporte_id=reporte.pk, decision=Decision.DEVUELTO
        )
        .select_related("autor")
        .order_by("-fecha", "-pk")
        .first()
    )


def _autor_guardado(autor):
    """Devuelve la fila guardada del actor; el objeto del llamador no decide nada."""
    fila = None
    if getattr(autor, "pk", None):
        fila = Usuario.objects.filter(pk=autor.pk).only("rol", "is_active").first()
    if fila is None:
        raise ValidationError({"autor": [MENSAJE_AUTOR]})
    return fila


def _exigir_tutor(fila, practica_id):
    """Solo el tutor académico activo de esa práctica; el staff no evita la regla."""
    asignado = AsignacionTutor.objects.filter(
        practica_id=practica_id, tutor_academico_id=fila.pk, hasta__isnull=True
    ).exists()
    if not (fila.is_active and fila.rol == Usuario.Rol.TUTOR_ACADEMICO and asignado):
        raise ValidationError({"autor": [MENSAJE_TUTOR]})


def _exigir_estudiante(fila, practica_id):
    """Solo el estudiante activo de la propia práctica reenvía su reporte."""
    practica = Practica.objects.filter(pk=practica_id).only("estudiante_id").first()
    if not (
        fila.is_active
        and fila.rol == Usuario.Rol.ESTUDIANTE
        and practica is not None
        and practica.estudiante_id == fila.pk
    ):
        raise ValidationError({"autor": [MENSAJE_ESTUDIANTE]})


def _registrar_validacion(reporte, autor, decision, observacion=""):
    """Registra autor y fecha de la decisión sobre el reporte (RF-04, S4)."""
    validacion = Validacion(
        practica_id=reporte.practica_id,
        reporte=reporte,
        decision=decision,
        observacion=observacion,
        autor=autor,
    )
    validacion.full_clean()
    validacion.save()
    return validacion


def _reporte_bloqueado(reporte):
    """Relee el reporte con la fila bloqueada: manda su estado guardado."""
    if not getattr(reporte, "pk", None):
        raise ValidationError({"reporte": [MENSAJE_REPORTE]})
    return ReporteSemanal.objects.select_for_update().get(pk=reporte.pk)


def _exigir_practica_en_curso(practica_id):
    """CU-01 2b (spec.md:497): solo una práctica «en_curso» admite la acción.

    Se comprueba después del permiso y antes del estado del reporte, con la fila
    de la práctica bloqueada para que una suspensión concurrente no se cuele.
    """
    estado = (
        Practica.objects.select_for_update()
        .filter(pk=practica_id)
        .values_list("estado", flat=True)
        .first()
    )
    if estado != Practica.Estado.EN_CURSO:
        raise ValidationError(
            {"practica": [MENSAJE_PRACTICA_NO_EN_CURSO.format(estado=estado)]}
        )


def _exigir_en_revision(reporte):
    if reporte.estado != Estado.EN_REVISION:
        raise ValidationError(
            {"estado": [MENSAJE_ESTADO_REPORTE.format(estado=reporte.estado)]}
        )


def _exigir_observacion(observacion):
    if not isinstance(observacion, str) or not observacion.strip():
        raise ValidationError({"observacion": [MENSAJE_OBSERVACION]})
    return observacion.strip()


def validar_reporte(*, reporte, autor):
    """Valida un reporte ``en_revision`` del tutor académico de esa práctica.

    Exige el actor guardado y el tutor activo asignado (clave «autor»), el reporte
    guardado (clave «reporte»), la práctica «en_curso» (clave «practica», CU-01
    2b) y que el estado sea «en_revision» (clave «estado»), en ese orden: primero
    el permiso, después el estado. Escribe la ``Validacion``
    con decisión «aprobado» —autor y fecha automáticos de RF-04— y deja la misma
    fila en «validado». No cambia el plan ni el estado de la práctica y no crea
    ninguna fila nueva. Devuelve el reporte bloqueado y actualizado.
    """
    fila = _autor_guardado(autor)
    with transaction.atomic():
        bloqueado = _reporte_bloqueado(reporte)
        _exigir_tutor(fila, bloqueado.practica_id)
        _exigir_practica_en_curso(bloqueado.practica_id)
        _exigir_en_revision(bloqueado)
        _registrar_validacion(bloqueado, fila, Decision.APROBADO)
        bloqueado.estado = Estado.VALIDADO
        bloqueado.save(update_fields=["estado"])
    return bloqueado


def devolver_reporte(*, reporte, autor, observacion):
    """Devuelve un reporte ``en_revision`` al estudiante para que lo corrija.

    Exige observación no vacía (S3/S6) y, como ``validar_reporte``, el tutor
    activo, la práctica «en_curso» (clave «practica») y el reporte «en_revision»;
    escribe la ``Validacion`` con decisión
    «devuelto» y esa observación, y marca la misma fila como «devuelto» (S8). No
    crea versiones ni filas: el reporte no tiene ``version`` (O1) y la semana de la
    práctica es única, así que la corrección es el reenvío de esa misma fila.
    Devuelve esa misma fila.
    """
    fila = _autor_guardado(autor)
    texto = _exigir_observacion(observacion)
    with transaction.atomic():
        bloqueado = _reporte_bloqueado(reporte)
        _exigir_tutor(fila, bloqueado.practica_id)
        _exigir_practica_en_curso(bloqueado.practica_id)
        _exigir_en_revision(bloqueado)
        _registrar_validacion(bloqueado, fila, Decision.DEVUELTO, texto)
        bloqueado.estado = Estado.DEVUELTO
        bloqueado.save(update_fields=["estado"])
    return bloqueado


def reenviar_reporte(*, reporte, autor):
    """Reenvía el reporte devuelto: «devuelto» -> «en_revision», misma fila.

    Solo el estudiante de la práctica (clave «autor»), con la práctica «en_curso»
    (clave «practica», CU-01 2b) y solo después de una devolución (clave
    «estado»); el reenvío no es una validación, así que no
    escribe ``Validacion``, no crea versiones y no renueva la fecha de registro.
    Sí vuelve a fijar ``ingreso_revision_en`` con el reloj del servidor, después
    de los chequeos y bajo el bloqueo de la fila, para que el plazo de revisión
    cuente desde este ingreso. Devuelve la fila bloqueada y actualizada.
    """
    fila = _autor_guardado(autor)
    with transaction.atomic():
        bloqueado = _reporte_bloqueado(reporte)
        _exigir_estudiante(fila, bloqueado.practica_id)
        _exigir_practica_en_curso(bloqueado.practica_id)
        if bloqueado.estado != Estado.DEVUELTO:
            raise ValidationError(
                {"estado": [MENSAJE_REENVIO.format(estado=bloqueado.estado)]}
            )
        bloqueado.estado = Estado.EN_REVISION
        bloqueado.ingreso_revision_en = timezone.now()
        bloqueado.save(update_fields=["estado", "ingreso_revision_en"])
    return bloqueado
