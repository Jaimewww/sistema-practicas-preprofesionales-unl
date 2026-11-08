"""Modelos de carreras y su configuración de prácticas (RF-12)."""

from django.db import models


class Carrera(models.Model):
    """Programa de estudios al que pertenecen las prácticas y sus usuarios."""

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)

    class Meta:
        verbose_name = "carrera"
        verbose_name_plural = "carreras"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ConfiguracionCarrera(models.Model):
    """Horas, plazos y umbral de rezago de una carrera para una modalidad.

    Cada carrera define las horas requeridas de cada modalidad: el sistema no
    fija un valor por defecto. Se admiten varias filas históricas por carrera.
    """

    class Modalidad(models.TextChoices):
        LABORAL = "laboral", "Laboral"
        COMUNITARIA = "comunitaria", "Comunitaria"

    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.PROTECT,
        related_name="configuraciones",
    )
    modalidad = models.CharField(max_length=20, choices=Modalidad.choices)
    horas_requeridas = models.PositiveIntegerField()
    plazo_reporte_dias = models.PositiveSmallIntegerField(default=3)
    plazo_revision_dias = models.PositiveSmallIntegerField(default=5)
    umbral_rezago = models.PositiveSmallIntegerField(default=80)
    vigente_desde = models.DateField()

    class Meta:
        verbose_name = "configuración de carrera"
        verbose_name_plural = "configuraciones de carrera"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(horas_requeridas__gt=0),
                name="carreras_configuracion_horas_requeridas_positivas",
                violation_error_message="Las horas requeridas deben ser mayores que cero.",
            ),
            models.CheckConstraint(
                condition=models.Q(umbral_rezago__lte=100),
                name="carreras_configuracion_umbral_rezago_hasta_100",
                violation_error_message="El umbral de rezago es un porcentaje: máximo 100.",
            ),
        ]

    def __str__(self):
        return f"{self.carrera.codigo} - {self.modalidad} desde {self.vigente_desde}"
