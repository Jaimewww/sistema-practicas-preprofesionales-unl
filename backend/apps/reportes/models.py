"""Modelo del reporte semanal del estudiante (S4, HU-02, RF-02).

``ReporteSemanal`` guarda la semana del período, las horas declaradas, la fecha
automática de registro y el estado. El data-model no define ``contenido`` ni
``version`` para los reportes y este modelo no los inventa: la devolución con
versión nueva pertenece a la validación del tutor. Las horas no cuentan para el
acumulado hasta que el tutor académico las valida, así que aquí solo nacen
``en_revision`` y nada se acumula.
"""

from django.core.exceptions import ValidationError
from django.db import models

MENSAJE_SEMANA = "La semana del reporte debe ser un número entero positivo."
MENSAJE_HORAS = "Las horas reportadas deben ser un número entero positivo."
MENSAJE_SEMANA_DUPLICADA = "La práctica ya tiene un reporte registrado para esa semana."
MAX_HORAS_AYUDANTIA = 10  # RF-15, Art. 341: límite semanal de una ayudantía.
MENSAJE_AYUDANTIA = (
    f"Una ayudantía no puede reportar más de {MAX_HORAS_AYUDANTIA} horas semanales "
    "(Art. 341 del Reglamento de Régimen Académico)."
)


def validar_semana_positiva(semana):
    """Exige una semana desde 1; la numeración la aporta el estudiante.

    Es un validador de campo, no ``Model.clean()``: Django lo ejecuta dentro de
    ``Field.clean()`` después de convertir el valor, así que un valor no numérico
    falla como ``ValidationError`` de campo y nunca llega aquí.
    """
    if semana < 1:
        raise ValidationError(MENSAJE_SEMANA)


def validar_horas_positivas(horas):
    """``PositiveIntegerField`` admite el 0; las horas reportadas empiezan en 1."""
    if horas < 1:
        raise ValidationError(MENSAJE_HORAS)


class ReporteSemanal(models.Model):
    """Reporte de una semana de la práctica (HU-02, RF-02).

    ``semana`` es la semana del período —un entero libre que aporta quien
    registra; el calendario del período no se recalcula aquí— y
    ``horas_reportadas`` es positiva. La base impone una sola versión activa por
    semana con una ``UniqueConstraint`` por ``(practica, semana)``: la regla vale
    también para ``objects.create()``, que no ejecuta ``full_clean()``. ``estado``
    inicia ``en_revision`` y ``fecha_registro`` la pone la base al insertar.
    """

    class Estado(models.TextChoices):
        EN_REVISION = "en_revision", "En revisión"
        VALIDADO = "validado", "Validado"
        DEVUELTO = "devuelto", "Devuelto"

    practica = models.ForeignKey(
        "practicas.Practica", on_delete=models.PROTECT, related_name="reportes"
    )
    semana = models.PositiveIntegerField(validators=[validar_semana_positiva])
    horas_reportadas = models.PositiveIntegerField(validators=[validar_horas_positivas])
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.EN_REVISION
    )

    class Meta:
        verbose_name = "reporte semanal"
        verbose_name_plural = "reportes semanales"
        constraints = [
            models.UniqueConstraint(
                fields=["practica", "semana"],
                name="reportes_reporte_semana_unica",
                violation_error_message=MENSAJE_SEMANA_DUPLICADA,
            )
        ]

    def __str__(self):
        return f"Reporte semana {self.semana} - práctica {self.practica_id}"
