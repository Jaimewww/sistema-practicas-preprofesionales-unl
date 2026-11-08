"""Modelos de actividades: el plan de actividades y su validación (T022, T023).

``PlanActividades`` es la entidad de HU-01/RF-01: la práctica, la versión del
plan, el contenido que el estudiante se compromete a cumplir y su estado.
``Validacion`` es la decisión del tutor académico sobre un plan (RF-03, RF-04).
Las transiciones (enviar, devolver, aprobar) son T024 y viven en
``apps/actividades/services.py``; aquí solo están las entidades y sus reglas.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

MENSAJE_VERSION = "La versión del plan debe ser un número entero positivo."
MENSAJE_DECISION = "La decisión debe ser «aprobado» o «devuelto»."
MENSAJE_OBSERVACION = "La observación es obligatoria cuando la decisión es «devuelto»."


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

    ``version`` empieza en 1 y la aporta quien crea la fila: el servicio de
    T024 crea la versión siguiente cuando el estudiante reenvía tras una
    devolución, así que el modelo no incrementa ni renumera nada. La pareja
    (``practica``, ``version``) es única en la base: la invariante no depende
    solo del bloqueo del servicio. ``contenido`` es obligatorio y el estado inicial es
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
        constraints = [
            models.UniqueConstraint(
                fields=["practica", "version"],
                name="actividades_plan_version_unica_por_practica",
                violation_error_message=(
                    "Esa versión del plan ya existe para esta práctica."
                ),
            )
        ]

    def __str__(self):
        return f"Plan v{self.version} - práctica {self.practica_id}"


class Validacion(models.Model):
    """Decisión del tutor académico sobre un plan o un reporte (T023, RF-03, RF-04).

    El data-model pide «exactamente uno de los dos» entre ``plan_id`` y
    ``reporte_id``. ``ReporteSemanal`` todavía no existe (es otra unidad de
    ``actividades``), así que hoy sólo uno de los dos lados puede presentarse:
    ``plan`` es obligatorio tanto en la base como en ``full_clean()``. Cuando
    llegue el reporte, ``plan`` pasará a opcional junto a ``reporte`` y la regla
    «exactamente uno» se impondrá con ``CheckConstraint``; escribir hoy esa
    restricción sobre una columna inexistente inventaría esquema.

    ``decision`` solo admite «aprobado» o «devuelto», y ``observacion`` es
    obligatoria con «devuelto»: se valida en ``clean()`` dentro de
    ``full_clean()``, como el resto de las reglas condicionales del proyecto.
    ``autor`` y ``fecha`` son automáticos en el sentido de RF-04: la fecha la
    pone la base al insertar y el autor lo escribe el servicio que valida.
    """

    class Decision(models.TextChoices):
        APROBADO = "aprobado", "Aprobado"
        DEVUELTO = "devuelto", "Devuelto"

    practica = models.ForeignKey(
        "practicas.Practica", on_delete=models.PROTECT, related_name="validaciones"
    )
    plan = models.ForeignKey(
        PlanActividades, on_delete=models.PROTECT, related_name="validaciones"
    )
    decision = models.CharField(
        max_length=20, choices=Decision.choices,
        error_messages={"invalid_choice": MENSAJE_DECISION},
    )
    observacion = models.TextField(blank=True, default="")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="validaciones"
    )
    fecha = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = "validación"
        verbose_name_plural = "validaciones"

    def __str__(self):
        return f"Validación {self.get_decision_display()} - plan {self.plan_id}"

    def clean(self):
        """Exige observación no vacía cuando la decisión es «devuelto»."""
        super().clean()
        if self.decision == self.Decision.DEVUELTO and not (self.observacion or "").strip():
            raise ValidationError({"observacion": MENSAJE_OBSERVACION})
