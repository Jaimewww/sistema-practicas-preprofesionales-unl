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
contar para el acumulado cuando el tutor las valida (S7); el acumulado lo calcula
la unidad de RF-20, no este servicio.

``_exigir_tutor`` y ``_registrar_validacion`` se replican aquí con las mismas
claves de error que las de ``apps.actividades.services`` (decisión D2): el
constructor cambia ``plan`` por ``reporte`` y ningún servicio importa las
funciones privadas de otra app.

Son acciones para **llamadores internos de confianza**: no hay DTOs ni
``PermissionDenied``; el permiso se falla cerrado con ``ValidationError`` en la
clave de actor, antes que el estado, y un rechazo no escribe nada.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.actividades.models import MENSAJE_OBSERVACION, Validacion
from apps.practicas.models import AsignacionTutor, Practica
from apps.reportes.models import ReporteSemanal
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
MENSAJE_REENVIO = (
    "No se puede reenviar el reporte: está en «{estado}»; "
    "solo se reenvía después de una devolución."
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
    guardado (clave «reporte») y que el estado sea «en_revision» (clave «estado»),
    en ese orden: primero el permiso, después el estado. Escribe la ``Validacion``
    con decisión «aprobado» —autor y fecha automáticos de RF-04— y deja la misma
    fila en «validado». No cambia el plan ni el estado de la práctica y no crea
    ninguna fila nueva. Devuelve el reporte bloqueado y actualizado.
    """
    fila = _autor_guardado(autor)
    with transaction.atomic():
        bloqueado = _reporte_bloqueado(reporte)
        _exigir_tutor(fila, bloqueado.practica_id)
        _exigir_en_revision(bloqueado)
        _registrar_validacion(bloqueado, fila, Decision.APROBADO)
        bloqueado.estado = Estado.VALIDADO
        bloqueado.save(update_fields=["estado"])
    return bloqueado


def devolver_reporte(*, reporte, autor, observacion):
    """Devuelve un reporte ``en_revision`` al estudiante para que lo corrija.

    Exige observación no vacía (S3/S6), escribe la ``Validacion`` con decisión
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
        _exigir_en_revision(bloqueado)
        _registrar_validacion(bloqueado, fila, Decision.DEVUELTO, texto)
        bloqueado.estado = Estado.DEVUELTO
        bloqueado.save(update_fields=["estado"])
    return bloqueado


def reenviar_reporte(*, reporte, autor):
    """Reenvía el reporte devuelto: «devuelto» -> «en_revision», misma fila.

    Solo el estudiante de la práctica (clave «autor») y solo después de una
    devolución (clave «estado»); el reenvío no es una validación, así que no
    escribe ``Validacion``, no crea versiones y no renueva la fecha de registro.
    Devuelve la fila bloqueada y actualizada.
    """
    fila = _autor_guardado(autor)
    with transaction.atomic():
        bloqueado = _reporte_bloqueado(reporte)
        _exigir_estudiante(fila, bloqueado.practica_id)
        if bloqueado.estado != Estado.DEVUELTO:
            raise ValidationError(
                {"estado": [MENSAJE_REENVIO.format(estado=bloqueado.estado)]}
            )
        bloqueado.estado = Estado.EN_REVISION
        bloqueado.save(update_fields=["estado"])
    return bloqueado
