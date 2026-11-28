"""Modelo del reporte semanal del estudiante (S4, HU-02, RF-02).

``ReporteSemanal`` guarda la semana del período, las horas declaradas, la fecha
automática de registro y el estado. Las horas no cuentan para el acumulado
hasta que el tutor académico las valida, así que aquí solo nacen ``en_revision``
y nada se acumula.

C-03 (#157, D1') suma ``actividades`` —el texto de la semana—. El reporte sigue
sin ``contenido`` ni ``version`` (data-model §ReporteSemanal): la versión vive
solo en ``EvidenciaReporte``, que guarda cada PDF privado de una versión del
reporte; la API nunca actualiza ni borra esas filas.
"""

from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models

from apps.actividades.models import validar_archivo_informe

if TYPE_CHECKING:
    # ``Any`` y ``RelatedManager`` solo los necesita el analizador estático para
    # el acceso inverso de ``Validacion.reporte``.
    from typing import Any

    from django.db.models.fields.related_descriptors import RelatedManager

MENSAJE_SEMANA = "La semana del reporte debe ser un número entero positivo."
MENSAJE_HORAS = "Las horas reportadas deben ser un número entero positivo."
MENSAJE_SEMANA_DUPLICADA = "La práctica ya tiene un reporte registrado para esa semana."
MAX_HORAS_SEMANA = 168  # 7 días × 24 h: nadie puede reportar más en una semana.
UMBRAL_REVISION_HORAS = 40  # Más de 40 h/semana se identifican para el tutor (S5).
MENSAJE_TOPE_SEMANAL = (
    f"Una semana tiene {MAX_HORAS_SEMANA} horas: no se pueden reportar más."
)
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


def validar_tope_semanal(horas):
    """Tope físico: una semana no tiene más de 168 horas."""
    if horas > MAX_HORAS_SEMANA:
        raise ValidationError(MENSAJE_TOPE_SEMANAL)


class ReporteSemanal(models.Model):
    """Reporte de una semana de la práctica (HU-02, RF-02).

    ``semana`` es la semana del período —un entero libre que aporta quien
    registra; el calendario del período no se recalcula aquí— y
    ``horas_reportadas`` es positiva. La base impone una sola versión activa por
    semana con una ``UniqueConstraint`` por ``(practica, semana)``: la regla vale
    también para ``objects.create()``, que no ejecuta ``full_clean()``. ``estado``
    inicia ``en_revision`` y ``fecha_registro`` la pone la base al insertar.
    ``requiere_revision`` lo calcula ``save()``: ``True`` si las horas superan 40
    (escenario S5 de la spec); ninguna semana puede pasar de 168 horas.

    ``ingreso_revision_en`` es un dato **interno del servidor** (no editable y
    ausente del serializer): lo fija el alta en ``ReportePracticaView`` y lo
    vuelve a fijar el reenvío en ``reenviar_reporte``. Es ``NULL`` cuando se
    desconoce —filas creadas por otra vía o anteriores a esta columna—, porque
    ``fecha_registro`` no distingue un alta inicial de un reenvío histórico.
    """

    if TYPE_CHECKING:
        practica_id: int
        validaciones: RelatedManager[Any]
        evidencias: "RelatedManager[EvidenciaReporte]"

    class Estado(models.TextChoices):
        EN_REVISION = "en_revision", "En revisión"
        VALIDADO = "validado", "Validado"
        DEVUELTO = "devuelto", "Devuelto"

    practica = models.ForeignKey(
        "practicas.Practica", on_delete=models.PROTECT, related_name="reportes"
    )
    semana = models.PositiveIntegerField(validators=[validar_semana_positiva])
    horas_reportadas = models.PositiveIntegerField(
        validators=[validar_horas_positivas, validar_tope_semanal]
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ingreso_revision_en = models.DateTimeField(null=True, blank=True, editable=False)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.EN_REVISION
    )
    requiere_revision = models.BooleanField(default=False, editable=False)
    actividades = models.TextField(blank=True, default="")

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

    def save(self, *args, **kwargs):
        """Deriva ``requiere_revision`` de las horas: más de 40 se señalan al tutor."""
        self.requiere_revision = self.horas_reportadas > UMBRAL_REVISION_HORAS
        campos = kwargs.get("update_fields")
        if campos is not None:
            kwargs["update_fields"] = {*campos, "requiere_revision"}
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reporte semana {self.semana} - práctica {self.practica_id}"


def ruta_evidencia_reporte(instance, filename):
    """Ruta única: ``reportes_evidencias/practica-<id>/<uuid>.pdf``.

    Misma regla que ``ruta_informe_estudiante``: dos evidencias no se pisan en
    el disco y el nombre del cliente queda solo en ``EvidenciaReporte.nombre``.
    """
    sufijo = Path(str(filename)).suffix.lower() or ".pdf"
    practica_id = instance.reporte.practica_id
    return f"reportes_evidencias/practica-{practica_id}/{uuid4().hex}{sufijo}"


class EvidenciaReporte(models.Model):
    """PDF privado de una versión del reporte semanal (C-03, RNF-05, D2).

    ``version`` numera las entregas del reporte (D1'): el alta multipart guarda la
    1 y el reenvío con PDFs nuevos guarda la siguiente a la mayor; las anteriores
    se conservan. El
    archivo es un PDF de hasta 5 MB (``validar_archivo_informe``, ADR 0005) y no
    tiene URL pública: se descarga por la ruta autenticada del reporte.
    """

    if TYPE_CHECKING:
        reporte_id: int

    reporte = models.ForeignKey(
        ReporteSemanal, on_delete=models.PROTECT, related_name="evidencias"
    )
    version = models.PositiveIntegerField()
    archivo = models.FileField(
        upload_to=ruta_evidencia_reporte, validators=[validar_archivo_informe]
    )
    nombre = models.CharField(max_length=255)
    tamano_bytes = models.PositiveIntegerField()
    subida_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "evidencia de reporte"
        verbose_name_plural = "evidencias de reportes"
        ordering = ("version", "pk")

    def __str__(self):
        return f"Evidencia v{self.version} - reporte {self.reporte_id}"
