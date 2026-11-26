"""Servicio de escritura de la configuración por carrera (RF-12, C-17, D1-D4).

Mecanismo interno de ``ConfiguracionCarrera``: upsert de **una** modalidad por
llamada sobre la fila ``(carrera, modalidad, vigente_desde)`` (D1/D3), con el
historial intacto —otra fecha agrega una fila nueva, nunca reescribe la anterior
(D2)— y sin tocar ninguna ``Practica``: las horas ya copiadas al asignar no
cambian y solo las asignaciones nuevas leen la configuración nueva (S6/S7, D4).

D3 revisada: la idempotencia la da este servicio, **no** una ``UniqueConstraint``
(el modelo solo conserva las dos ``CheckConstraint``). Buscar-y-actualizar bajo
``select_for_update()`` evita duplicar la fila del mismo día; el coste asumido es
que dos ``PUT`` simultáneos podrían crear dos filas de ese día, la misma
tolerancia que ya existía.

El permiso lo decide la fila **guardada** del actor, no el objeto del llamador:
solo el coordinador activo **de esa carrera** escribe. Un autor sin permiso lanza
``ValidationError`` con la clave ``autor`` y no deja ninguna escritura.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.carreras.models import ConfiguracionCarrera
from apps.usuarios.models import Usuario

MENSAJE_COORDINADOR_CONFIGURACION = (
    "Solo el coordinador activo de la carrera puede guardar su configuración."
)
MENSAJE_CARRERA_CONFIGURACION = "La configuración necesita una carrera guardada."
MENSAJE_AUTOR_CONFIGURACION = "El autor debe ser un usuario guardado."

# Las claves que el upsert escribe; el resto de la fila no cambia.
CAMPOS_DE_CONFIGURACION = (
    "modalidad",
    "horas_requeridas",
    "plazo_reporte_dias",
    "plazo_revision_dias",
    "umbral_rezago",
    "vigente_desde",
)


def _exigir_coordinador_de_carrera(
    carrera, autor, mensaje=MENSAJE_COORDINADOR_CONFIGURACION
):
    """El rol y la carrera salen de la fila guardada, no del objeto del llamador."""
    fila = (
        Usuario.objects.filter(pk=autor.pk).only("rol", "is_active", "carrera").first()
    )
    if not (
        fila is not None
        and fila.is_active
        and fila.rol == Usuario.Rol.COORDINADOR
        and fila.carrera_id == carrera.pk
    ):
        raise ValidationError({"autor": [mensaje]})


def guardar_configuracion(*, carrera, autor, datos):
    """Guarda la configuración de una modalidad de ``carrera`` y la devuelve.

    ``datos`` trae las seis claves ya validadas por el contrato
    (``ConfiguracionCarreraEntradaSerializer.datos``). La fila de ese día se
    busca con ``select_for_update()`` dentro de la transacción: si existe se
    **actualiza** (D3, repetir el mismo día es idempotente) y si no se crea una
    nueva (D2). El modelo se valida con ``full_clean()`` —incluidas las dos
    ``CheckConstraint``— antes de guardar.

    No escribe ni modifica ``Practica``: el endpoint no reescribe las horas ya
    copiadas (D4). El alcance es el coordinador activo de esa carrera; cualquier
    otro actor, otro rol o un coordinador de otra carrera recibe ``ValidationError``
    en la clave ``autor`` sin dejar escrituras.
    """
    if not getattr(carrera, "pk", None):
        raise ValidationError({"carrera": [MENSAJE_CARRERA_CONFIGURACION]})
    if not getattr(autor, "pk", None):
        raise ValidationError({"autor": [MENSAJE_AUTOR_CONFIGURACION]})
    with transaction.atomic():
        _exigir_coordinador_de_carrera(carrera, autor)
        configuracion = (
            ConfiguracionCarrera.objects.select_for_update()
            .filter(
                carrera=carrera,
                modalidad=datos["modalidad"],
                vigente_desde=datos["vigente_desde"],
            )
            .first()
        )
        if configuracion is None:
            configuracion = ConfiguracionCarrera(carrera=carrera)
        for campo in CAMPOS_DE_CONFIGURACION:
            setattr(configuracion, campo, datos[campo])
        configuracion.full_clean()
        configuracion.save()
    return configuracion
