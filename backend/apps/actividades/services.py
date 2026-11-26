"""Servicios internos del plan de actividades: enviar, devolver y aprobar (T024).

HU-01/RF-01/RF-03 sobre ``PlanActividades``: el estudiante registra su plan y lo
envía a revisión; el tutor académico activo lo devuelve con observación o lo
aprueba, y la aprobación pasa la práctica a «en curso» con el servicio de
transiciones de T017. La versión es incremental por devolución (data-model.md):
devolver deja la misma fila en «devuelto» para que el estudiante la corrija, y la
versión siguiente nace solo cuando el estudiante reenvía; mientras la última
versión esté «en revisión» o «aprobado» no se admite otro envío. El actor se
comprueba contra la fila guardada, nunca contra el objeto del llamador, y la
práctica se lee bloqueada para que la versión siguiente no se repita.

RF-08/HU-07 añade aquí las dos acciones del tutor de entidad (S5):
``confirmar_reporte`` escribe la ``ConfirmacionEntidad`` del reporte semanal de
su practicante y ``registrar_informe_externo`` escribe el ``InformeFinal`` de la
práctica. El permiso de las dos es el mismo y sale de la fila guardada: el
tutor de entidad **persistido** de esa práctica **laboral** (data-model.md,
regla de ``ConfirmacionEntidad``), y cualquier otro tutor de entidad, un rol
ajeno o una práctica comunitaria —que no tiene tutor de entidad— se rechaza.
Ninguna de las dos toca ``Practica.estado`` ni ``HistorialEstado`` (S9).

Son acciones para **llamadores internos de confianza**: no hay vistas, endpoints,
DTOs ni ``PermissionDenied`` (T025). El permiso se falla cerrado con
``ValidationError`` en la clave de actor.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from apps.actividades.models import (
    MENSAJE_OBSERVACION,
    ConfirmacionEntidad,
    InformeFinal,
    PlanActividades,
    Validacion,
)
from apps.practicas.models import AsignacionTutor, Practica
from apps.practicas.services import (
    ESTADOS_FINALES,
    MENSAJE_TERMINAL,
    cambiar_estado_practica,
)
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario

Estado = PlanActividades.Estado
Decision = Validacion.Decision

MENSAJE_PLAN = "El plan de actividades debe estar guardado para cambiar de estado."
MENSAJE_PRACTICA = (
    "La práctica debe estar guardada para registrar el plan de actividades."
)
MENSAJE_AUTOR = "El autor de la acción debe ser un usuario guardado."
MENSAJE_ESTUDIANTE = (
    "Solo el estudiante de la práctica puede enviar su plan de actividades."
)
MENSAJE_TUTOR = "Solo el tutor académico activo de la práctica puede validar su plan de actividades."
MENSAJE_TUTOR_ENTIDAD_CONFIRMACION = (
    "Solo el tutor de entidad de esa práctica laboral puede confirmar sus "
    "reportes semanales."
)
MENSAJE_TUTOR_ENTIDAD_INFORME = (
    "Solo el tutor de entidad de esa práctica laboral puede registrar su informe final."
)
MENSAJE_REPORTE_CONFIRMACION = (
    "El reporte debe estar guardado para confirmar la entidad."
)
MENSAJE_PRACTICA_INFORME = (
    "La práctica debe estar guardada para registrar el informe final."
)
MENSAJE_CONFIRMACION_DUPLICADA = (
    "El reporte ya tiene la confirmación de la entidad: no se confirma dos veces."
)
MENSAJE_INFORME_DUPLICADO = (
    "La práctica ya tiene un informe final registrado: no se registra dos veces."
)
MENSAJE_CONTENIDO_INFORME = "El contenido del informe final debe ser texto."
MENSAJE_REENVIO = (
    "No se puede enviar un plan nuevo: la última versión está «{estado}»; "
    "solo se reenvía después de una devolución."
)
MENSAJE_ESTADO_PLAN = "Transición no permitida: el plan está en «{estado}» y solo se valida uno «en_revision»."


def _autor_guardado(autor):
    """Devuelve la fila guardada del actor; el objeto del llamador no decide nada."""
    fila = None
    if getattr(autor, "pk", None):
        fila = Usuario.objects.filter(pk=autor.pk).only("rol", "is_active").first()
    if fila is None:
        raise ValidationError({"autor": [MENSAJE_AUTOR]})
    return fila


def _practica_bloqueada(pk):
    """Relee la práctica con la fila bloqueada: manda su estado guardado."""
    return Practica.objects.select_for_update().get(pk=pk)


def _siguiente_version(practica_id):
    """Versión máxima registrada más uno; la calcula el servicio bajo el bloqueo."""
    ultima = PlanActividades.objects.filter(practica_id=practica_id).aggregate(
        Max("version")
    )["version__max"]
    return (ultima or 0) + 1


def _exigir_reenvio_permitido(practica_id):
    """La versión siguiente solo nace tras una devolución (data-model.md).

    Si la última versión está «en revisión» o «aprobado», enviar de nuevo la
    duplicaría o pisaría lo que el tutor ya tiene o ya resolvió.
    """
    ultima = (
        PlanActividades.objects.filter(practica_id=practica_id)
        .order_by("-version")
        .only("estado")
        .first()
    )
    if ultima is not None and ultima.estado != Estado.DEVUELTO:
        raise ValidationError(
            {"estado": [MENSAJE_REENVIO.format(estado=ultima.estado)]}
        )


def _exigir_tutor(fila, practica_id):
    """Solo el tutor académico activo de esa práctica; el staff no evita la regla."""
    asignado = AsignacionTutor.objects.filter(
        practica_id=practica_id, tutor_academico_id=fila.pk, hasta__isnull=True
    ).exists()
    if not (fila.is_active and fila.rol == Usuario.Rol.TUTOR_ACADEMICO and asignado):
        raise ValidationError({"autor": [MENSAJE_TUTOR]})


def _exigir_en_revision(plan):
    if plan.estado != Estado.EN_REVISION:
        raise ValidationError(
            {"estado": [MENSAJE_ESTADO_PLAN.format(estado=plan.estado)]}
        )


def _registrar_validacion(plan, autor, decision, observacion=""):
    """Registra autor y fecha de la decisión (RF-04, S12)."""
    validacion = Validacion(
        practica_id=plan.practica_id,
        plan=plan,
        decision=decision,
        observacion=observacion,
        autor=autor,
    )
    validacion.full_clean()
    validacion.save()
    return validacion


def enviar_plan(*, practica, contenido, autor):
    """Registra el plan y lo deja ``en_revision``; la primera versión es la 1.

    El autor debe ser el estudiante de la propia práctica, la práctica no puede
    estar en un estado final y la última versión no puede estar «en revisión» ni
    «aprobado» (clave «estado»): primero el permiso, después el estado. Tras una
    devolución el reenvío crea la versión siguiente con el contenido corregido. La
    versión la decide el servicio (máxima registrada más uno, bajo la fila
    bloqueada) y el estado inicial no es un parámetro del llamador.
    """
    fila = _autor_guardado(autor)
    if not getattr(practica, "pk", None):
        raise ValidationError({"practica": [MENSAJE_PRACTICA]})
    with transaction.atomic():
        bloqueada = _practica_bloqueada(practica.pk)
        if not (
            fila.is_active
            and fila.rol == Usuario.Rol.ESTUDIANTE
            and bloqueada.estudiante_id == fila.pk
        ):
            raise ValidationError({"autor": [MENSAJE_ESTUDIANTE]})
        if bloqueada.estado in ESTADOS_FINALES:
            raise ValidationError(
                {"estado": [MENSAJE_TERMINAL.format(estado=bloqueada.estado)]}
            )
        _exigir_reenvio_permitido(bloqueada.pk)
        plan = PlanActividades(
            practica=bloqueada,
            version=_siguiente_version(bloqueada.pk),
            contenido=contenido,
            estado=Estado.EN_REVISION,
        )
        plan.full_clean()
        plan.save()
    return plan


def devolver_plan(*, plan, autor, observacion):
    """Devuelve un plan ``en_revision`` al estudiante para que lo corrija.

    Exige observación no vacía (S7/S12), escribe la ``Validacion`` con decisión
    «devuelto» y esa observación, y marca la fila como ``devuelto``. No crea
    ninguna versión: la siguiente nace cuando el estudiante reenvía con
    ``enviar_plan`` (HU-01 criterio 2; Art. 336a). Devuelve esa misma fila.
    """
    fila = _autor_guardado(autor)
    if not getattr(plan, "pk", None):
        raise ValidationError({"plan": [MENSAJE_PLAN]})
    if not isinstance(observacion, str) or not observacion.strip():
        raise ValidationError({"observacion": [MENSAJE_OBSERVACION]})
    with transaction.atomic():
        bloqueado = PlanActividades.objects.select_for_update().get(pk=plan.pk)
        practica = _practica_bloqueada(bloqueado.practica_id)
        _exigir_tutor(fila, practica.pk)
        _exigir_en_revision(bloqueado)
        _registrar_validacion(bloqueado, fila, Decision.DEVUELTO, observacion.strip())
        bloqueado.estado = Estado.DEVUELTO
        bloqueado.save(update_fields=["estado"])
    return bloqueado


def aprobar_plan(*, plan, autor):
    """Aprueba un plan ``en_revision`` y pasa la práctica a «en curso».

    Escribe la ``Validacion`` con decisión «aprobado» (sin observación), marca el
    plan como ``aprobado`` y cambia la práctica con ``cambiar_estado_practica`` de
    T017, que es quien decide la arista y escribe el historial. Una práctica ya en
    «en curso» es idempotente: no vuelve a llamar al servicio y no duplica
    historial. Cualquier otro estado no recorre la arista y T017 lanza su
    ``ValidationError`` tal cual (en una práctica suspendida, el permiso de
    reanudar es del coordinador y la clave es «autor»); la transacción no deja el
    plan aprobado.
    """
    fila = _autor_guardado(autor)
    if not getattr(plan, "pk", None):
        raise ValidationError({"plan": [MENSAJE_PLAN]})
    with transaction.atomic():
        bloqueado = PlanActividades.objects.select_for_update().get(pk=plan.pk)
        practica = _practica_bloqueada(bloqueado.practica_id)
        _exigir_tutor(fila, practica.pk)
        _exigir_en_revision(bloqueado)
        _registrar_validacion(bloqueado, fila, Decision.APROBADO)
        bloqueado.estado = Estado.APROBADO
        bloqueado.save(update_fields=["estado"])
        if practica.estado != Practica.Estado.EN_CURSO:
            cambiar_estado_practica(
                practica=practica, nuevo_estado=Practica.Estado.EN_CURSO, autor=fila
            )
    return bloqueado


def _exigir_tutor_entidad(fila, practica, mensaje):
    """Solo el ``tutor_entidad`` guardado de esa práctica **laboral** (HU-07 caso 3).

    La regla del data-model es «el tutor de entidad solo puede confirmar reportes
    de **sus** practicantes»: la única fuente del permiso es la columna
    ``tutor_entidad`` de la fila guardada de la práctica, no una asignación
    aparte ni el objeto del llamador. Una práctica comunitaria no tiene tutor de
    entidad (``Practica.clean`` lo prohíbe), así que la misma comparación la
    rechaza sin una rama propia y sin revelar a un tutor ajeno de qué tipo es la
    práctica. ``mensaje`` es el texto del rechazo de la acción que lo llama, para
    que cada endpoint tenga el suyo.
    """
    if not (
        fila.is_active
        and fila.rol == Usuario.Rol.TUTOR_ENTIDAD
        and practica.tipo == Practica.Tipo.LABORAL
        and practica.tutor_entidad_id == fila.pk
    ):
        raise ValidationError({"autor": [mensaje]})


def confirmar_reporte(*, reporte, autor):
    """Confirma el reporte semanal del practicante del tutor de entidad (HU-07).

    Escribe la ``ConfirmacionEntidad`` con el actor guardado —autor y fecha
    automáticos de HU-07 caso 2— y **no** cambia el estado del reporte, el de la
    práctica ni el historial (S9). Un reporte se confirma una sola vez: la
    segunda vez lanza ``ValidationError`` en la clave ``confirmacion`` y la
    ``UniqueConstraint`` de la base lo respalda.

    Orden de los rechazos: reporte guardado (clave ``reporte``), permiso sobre la
    práctica guardada (clave ``autor``) y duplicado (clave ``confirmacion``). La
    fila del reporte se lee con ``select_for_update`` para que dos confirmaciones
    simultáneas del mismo reporte no se serialicen mal.
    """
    fila = _autor_guardado(autor)
    if not getattr(reporte, "pk", None):
        raise ValidationError({"reporte": [MENSAJE_REPORTE_CONFIRMACION]})
    with transaction.atomic():
        bloqueado = ReporteSemanal.objects.select_for_update().get(pk=reporte.pk)
        practica = _practica_bloqueada(bloqueado.practica_id)
        _exigir_tutor_entidad(fila, practica, MENSAJE_TUTOR_ENTIDAD_CONFIRMACION)
        if ConfirmacionEntidad.objects.filter(reporte_id=bloqueado.pk).exists():
            raise ValidationError({"confirmacion": [MENSAJE_CONFIRMACION_DUPLICADA]})
        confirmacion = ConfirmacionEntidad(reporte=bloqueado, tutor_entidad=fila)
        confirmacion.full_clean()
        confirmacion.save()
    return confirmacion


def registrar_informe_externo(*, practica, autor, contenido=None, archivo=None):
    """Registra el informe final del tutor de entidad sobre su práctica (HU-07).

    El informe queda asociado a la práctica con su autor y su fecha (HU-07 caso
    1). El data-model pide «contenido **o** archivo» y el modelo lo impone como
    «exactamente uno»: ni los dos vacíos ni los dos llenos entran, y el rechazo
    vuelve en las dos claves para que el cliente sepa qué corregir. El ``archivo``
    se valida como PDF de hasta 5 MB (ADR 0005, S8) dentro de ``full_clean()``, que
    es la misma validación de tipo y tamaño que repetiría un serializer: no
    depende de que la vista la duplique.

    Una práctica registra un solo informe: el segundo intento lanza
    ``ValidationError`` en la clave ``informe``. Orden de los rechazos: práctica
    guardada (clave ``practica``), permiso (clave ``autor``), duplicado (clave
    ``informe``) y, al final, las reglas de la entidad (claves ``contenido`` y
    ``archivo``). No cambia el estado de la práctica ni escribe historial (S9).

    El vacío de ``archivo`` se normaliza a la cadena vacía antes de construir la
    fila: el vacío de un ``FileField`` es ``""``, no ``None``, y una fila con
    ``NULL`` en esa columna rompería la ``CheckConstraint`` «exactamente uno»
    —que se evalúa igual en Python y en SQL— además del ``NOT NULL``.
    """
    fila = _autor_guardado(autor)
    if not getattr(practica, "pk", None):
        raise ValidationError({"practica": [MENSAJE_PRACTICA_INFORME]})
    if contenido is not None and not isinstance(contenido, str):
        raise ValidationError({"contenido": [MENSAJE_CONTENIDO_INFORME]})
    texto = (contenido or "").strip() or None
    with transaction.atomic():
        bloqueada = _practica_bloqueada(practica.pk)
        _exigir_tutor_entidad(fila, bloqueada, MENSAJE_TUTOR_ENTIDAD_INFORME)
        if InformeFinal.objects.filter(practica_id=bloqueada.pk).exists():
            raise ValidationError({"informe": [MENSAJE_INFORME_DUPLICADO]})
        informe = InformeFinal(
            practica=bloqueada,
            tutor_entidad=fila,
            contenido=texto,
            archivo=archivo or "",
        )
        informe.full_clean()
        informe.save()
    return informe
