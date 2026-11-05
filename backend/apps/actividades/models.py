"""Modelos de actividades: el plan de actividades del estudiante (T022).

``PlanActividades`` es la entidad de HU-01/RF-01: la práctica, la versión del
plan, el contenido que el estudiante se compromete a cumplir y su estado. Las
transiciones (enviar, devolver, aprobar), el incremento de versión por
devolución y la validación del tutor son T024 y no están implementados aquí.
"""

from django.core.exceptions import ValidationError
from django.db import models

MENSAJE_VERSION = "La versión del plan debe ser un número entero positivo."


def validar_version_positiva(version):
    """Exige una versión desde 1; la primera versión del plan es la 1.

    Es un validador de campo, no ``Model.clean()``: Django lo ejecuta dentro de
    ``Field.clean()`` después de convertir el valor, así que un valor no
    numérico falla como ``ValidationError`` de campo y nunca llega aquí.
    """
    if version < 1:
        raise ValidationError(MENSAJE_VERSION)


class PlanActividades(models.Model):
    """Plan de actividades de una práctica (HU-01, RF-01).

    ``version`` empieza en 1 y la aporta quien crea la fila: la devolución que
    genera una versión nueva es T024, así que el modelo no incrementa ni
    renumera nada. ``contenido`` es obligatorio y el estado inicial es
    ``en_revision``; aprobar y devolver son transiciones de T024.

    ``practica`` usa ``PROTECT`` y las filas se conservan: una versión anterior
    no se borra al registrar otra. La versión debe ser un entero positivo y la
    comprueba ``validar_version_positiva`` dentro de ``full_clean()``. Este
    modelo no llama a ``full_clean()`` desde ``save()`` ni desde
    ``objects.create()``.
    """

    class Estado(models.TextChoices):
        EN_REVISION = "en_revision", "En revisión"
        APROBADO = "aprobado", "Aprobado"
        DEVUELTO = "devuelto", "Devuelto"

    practica = models.ForeignKey(
        "practicas.Practica",
        on_delete=models.PROTECT,
        related_name="planes_actividades",
    )
    version = models.PositiveIntegerField(
        default=1, validators=[validar_version_positiva]
    )
    contenido = models.TextField()
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.EN_REVISION
    )

    class Meta:
        verbose_name = "plan de actividades"
        verbose_name_plural = "planes de actividades"

    def __str__(self):
        return f"Plan v{self.version} - práctica {self.practica_id}"
