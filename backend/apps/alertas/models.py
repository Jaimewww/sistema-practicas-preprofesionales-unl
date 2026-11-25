"""Modelo de alertas de atraso (T042, HU-06, CU-03).

``Alerta`` es el aviso por un atraso o un pendiente de una práctica. Los tres
tipos son los del data-model —reporte no enviado, revisión pendiente y rezago—;
RF-18 (incumplimiento reportado por el tutor de entidad) no es una causa de
alerta de esta unidad. Django asigna ``fecha`` al crear la fila y ``atendida``
nace falsa.

La causa de una alerta es el par práctica/tipo: a lo sumo una activa por par.
La ``UniqueConstraint`` condicional de ``Meta`` lo impone en la base, así que
``objects.create()`` y ``save()`` —que no ejecutan ``full_clean()``— también
fallan con ``IntegrityError``. Las filas atendidas se conservan como historial y
no bloquean una nueva alerta activa de la misma causa.

Los destinatarios no se persisten: ``destinatarios`` los deriva del tipo con el
mapeo de HU-06 (roles, no identidades) y todavía no autoriza ni notifica nada.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

from django.db import models

from apps.usuarios.models import Usuario

MENSAJE_ALERTA_ACTIVA_DUPLICADA = (
    "Ya existe una alerta activa de este tipo para la práctica; "
    "no se genera otra hasta que la vigente se marque como atendida."
)


class Alerta(models.Model):
    """Aviso de atraso o pendiente de una práctica (RF-07, HU-06).

    ``practica`` es obligatoria y se protege contra el borrado en cascada, igual
    que las demás referencias a ``Practica``. La unicidad condicional de la
    causa activa vale para cualquier escritura, no solo para ``full_clean()``.
    """

    class Tipo(models.TextChoices):
        REPORTE_NO_ENVIADO = "reporte_no_enviado", "Reporte no enviado"
        REVISION_PENDIENTE = "revision_pendiente", "Revisión pendiente"
        REZAGO = "rezago", "Rezago"

    practica: models.ForeignKey = models.ForeignKey(
        "practicas.Practica", on_delete=models.PROTECT, related_name="alertas"
    )
    tipo: models.CharField = models.CharField(max_length=20, choices=Tipo.choices)
    fecha: models.DateField = models.DateField(auto_now_add=True)
    atendida: models.BooleanField = models.BooleanField(default=False)

    if TYPE_CHECKING:
        # Django agrega estos atributos al construir la clase del modelo.
        get_tipo_display: Callable[[], str]
        practica_id: int

    class Meta:
        verbose_name = "alerta"
        verbose_name_plural = "alertas"
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["practica", "tipo"],
                condition=models.Q(atendida=False),
                name="alertas_alerta_activa_unica",
                violation_error_message=MENSAJE_ALERTA_ACTIVA_DUPLICADA,
            )
        ]

    def __str__(self):
        return f"Alerta {self.get_tipo_display()} - práctica {self.practica_id}"

    @property
    def destinatarios(self):
        """Roles a los que corresponde la alerta según su tipo (HU-06)."""
        return DESTINATARIOS_POR_TIPO[self.tipo]


# HU-06 #1 y #3: el reporte no enviado y el rezago llegan al estudiante, a su
# tutor académico y al coordinador. HU-06 #2 y CU-03 1b: la revisión pendiente
# solo al tutor académico. Son roles derivados, no destinatarios concretos.
DESTINATARIOS_POR_TIPO = {
    Alerta.Tipo.REPORTE_NO_ENVIADO: (
        Usuario.Rol.ESTUDIANTE,
        Usuario.Rol.TUTOR_ACADEMICO,
        Usuario.Rol.COORDINADOR,
    ),
    Alerta.Tipo.REVISION_PENDIENTE: (Usuario.Rol.TUTOR_ACADEMICO,),
    Alerta.Tipo.REZAGO: (
        Usuario.Rol.ESTUDIANTE,
        Usuario.Rol.TUTOR_ACADEMICO,
        Usuario.Rol.COORDINADOR,
    ),
}
