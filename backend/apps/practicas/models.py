"""Modelos del catálogo de períodos académicos (T015, data-model.md).

``Practica`` y ``AsignacionTutor`` llegan en tareas posteriores; este módulo
solo contiene el catálogo de períodos.
"""

from django.core.exceptions import ValidationError
from django.db import models


class Periodo(models.Model):
    """Período académico con fechas inclusivas.

    ``dias_totales`` es una propiedad derivada, no un contador almacenado: cuenta
    desde el inicio hasta el fin, ambos incluidos (del 1 al 7 de enero son 7
    días, no 6). La validación de fechas se hace con ``full_clean()``; ``save()``
    y ``objects.create()`` no la ejecutan, como en cualquier modelo de Django.
    """

    nombre = models.CharField(max_length=200)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        verbose_name = "período"
        verbose_name_plural = "períodos"

    def __str__(self):
        return f"{self.nombre} ({self.fecha_inicio} - {self.fecha_fin})"

    def clean(self):
        super().clean()
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError(
                {
                    "fecha_fin": "La fecha de fin debe ser posterior a la fecha de inicio."
                }
            )

    @property
    def dias_totales(self):
        """Días del período contando el inicio y el fin (ambos incluidos)."""
        return (self.fecha_fin - self.fecha_inicio).days + 1
