"""Modelos de prácticas y su catálogo de períodos académicos (T015, data-model.md).

``Periodo`` es el catálogo de períodos. ``Practica`` registra la asignación
básica de un estudiante en una entidad, carrera y período, con su tipo,
subtipo, proyecto de vinculación, horas requeridas y estado. La asignación de
tutores (``AsignacionTutor``) llega en una tarea posterior.
"""

from django.conf import settings
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


class Practica(models.Model):
    """Práctica asignada a un estudiante en un período (RF-14).

    Las horas requeridas las aporta quien asigna la práctica: no se leen de
    ``ConfiguracionCarrera`` ni se recalculan al cambiar la configuración
    (el servicio de copia automática es T018). El estado inicial es
    ``asignada``; las transiciones y los motivos obligatorios son T017.

    Las reglas condicionales de ``tipo`` se validan con ``full_clean()``;
    ``save()`` y ``objects.create()`` no la ejecutan.
    """

    class Tipo(models.TextChoices):
        LABORAL = "laboral", "Laboral"
        COMUNITARIA = "comunitaria", "Comunitaria"

    class Subtipo(models.TextChoices):
        PRACTICA = "practica", "Práctica"
        PASANTIA = "pasantia", "Pasantía"
        AYUDANTIA_DOCENCIA = "ayudantia_docencia", "Ayudantía de docencia"
        AYUDANTIA_INVESTIGACION = (
            "ayudantia_investigacion",
            "Ayudantía de investigación",
        )

    class Estado(models.TextChoices):
        ASIGNADA = "asignada", "Asignada"
        EN_CURSO = "en_curso", "En curso"
        EN_REVISION_FINAL = "en_revision_final", "En revisión final"
        CERRADA = "cerrada", "Cerrada"
        SUSPENDIDA = "suspendida", "Suspendida"
        CANCELADA = "cancelada", "Cancelada"

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="practicas",
    )
    carrera = models.ForeignKey(
        "carreras.Carrera",
        on_delete=models.PROTECT,
        related_name="practicas",
    )
    entidad = models.ForeignKey(
        "entidades.EntidadReceptora",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="practicas",
    )
    periodo = models.ForeignKey(
        "practicas.Periodo",
        on_delete=models.PROTECT,
        related_name="practicas",
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    subtipo = models.CharField(
        max_length=30, choices=Subtipo.choices, blank=True, default=""
    )
    proyecto_vinculacion = models.CharField(max_length=200, blank=True, default="")
    horas_requeridas = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ASIGNADA
    )
    motivo_suspension = models.TextField(blank=True, default="")
    motivo_cancelacion = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "práctica"
        verbose_name_plural = "prácticas"

    def __str__(self):
        return f"Práctica {self.pk} - {self.get_tipo_display()}"

    def clean(self):
        """Exige entidad y subtipo laboral, y proyecto en la comunitaria."""
        super().clean()
        errores = {}
        if self.tipo == self.Tipo.LABORAL:
            if not self.entidad_id:
                errores["entidad"] = (
                    "La entidad receptora es obligatoria para las prácticas laborales."
                )
            if not self.subtipo:
                errores["subtipo"] = (
                    "El subtipo es obligatorio para las prácticas laborales."
                )
        elif self.tipo == self.Tipo.COMUNITARIA:
            if self.subtipo:
                errores["subtipo"] = "El subtipo solo aplica a las prácticas laborales."
            if not self.proyecto_vinculacion:
                errores["proyecto_vinculacion"] = (
                    "El proyecto de vinculación es obligatorio para las prácticas comunitarias."
                )
        if errores:
            raise ValidationError(errores)
