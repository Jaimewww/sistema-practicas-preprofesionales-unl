"""Diario de estados de la práctica, de solo inserción (T016, RF-10). Ver README."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.practicas.models import Practica

MENSAJE_INMUTABLE = "El historial de estados es de solo inserción: no se puede modificar ni borrar un registro."
MENSAJE_INSERCION = "El historial pide inserción fila a fila con full_clean(); bulk_create no se permite."
MENSAJE_ESTADO_ANTERIOR = "El estado anterior solo puede quedar vacío en el registro inicial."
MENSAJE_MOTIVO = "El motivo es obligatorio al suspender o cancelar una práctica."


class HistorialEstadoQuerySet(models.QuerySet):
    """Solo inserción: todo camino masivo de escritura falla cerrado.

    ``update()``, ``delete()``, ``bulk_update()`` y ``bulk_create()`` no pasan por
    el ``save()`` ni el ``delete()`` del modelo.
    """

    def update(self, **kwargs):
        raise ValidationError(MENSAJE_INMUTABLE)

    def delete(self):
        raise ValidationError(MENSAJE_INMUTABLE)

    def bulk_update(self, objs, fields, *args, **kwargs):
        raise ValidationError(MENSAJE_INMUTABLE)

    def bulk_create(self, objs, *args, **kwargs):
        raise ValidationError(MENSAJE_INSERCION)


class HistorialEstado(models.Model):
    """Estado anterior, nuevo, autor, fecha automática y motivo (RF-10).

    ``estado_anterior`` es nulo solo en el registro inicial; el motivo es
    obligatorio al suspender y al cancelar (RF-13); reanudar no lo exige, aunque
    se conserva si se da. ``full_clean()`` los
    valida; ``save()`` no. ``objects`` es también el gestor base porque el gestor
    inverso reasigna con él.
    """

    practica = models.ForeignKey(
        Practica, on_delete=models.PROTECT, related_name="historial_estados"
    )
    estado_anterior = models.CharField(
        max_length=20, choices=Practica.Estado.choices, null=True, blank=True
    )
    estado_nuevo = models.CharField(max_length=20, choices=Practica.Estado.choices)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="historial_estados"
    )
    fecha = models.DateTimeField(auto_now_add=True, editable=False)
    motivo = models.TextField(blank=True, default="")

    objects = HistorialEstadoQuerySet.as_manager()

    class Meta:
        verbose_name = "historial de estado"
        verbose_name_plural = "historial de estados"
        ordering = ["pk"]
        base_manager_name = "objects"

    def __str__(self):
        return f"Práctica {self.practica_id}: {self.estado_anterior or 'inicio'} → {self.estado_nuevo}"

    def clean(self):
        """Exige motivo en suspensión y cancelación."""
        super().clean()
        errores = {}
        if self.estado_anterior is None and self._hay_registros_previos():
            errores["estado_anterior"] = MENSAJE_ESTADO_ANTERIOR
        if self._exige_motivo() and not (self.motivo or "").strip():
            errores["motivo"] = MENSAJE_MOTIVO
        if errores:
            raise ValidationError(errores)

    def _exige_motivo(self):
        """Compara por igualdad, sin hashear: un valor inválido no debe romper."""
        return self.estado_nuevo in (Practica.Estado.SUSPENDIDA, Practica.Estado.CANCELADA)

    def _hay_registros_previos(self):
        """Indica si la práctica ya tiene historial, es decir, si no es el inicio."""
        if not self.practica_id:
            return False
        registros = HistorialEstado.objects.filter(practica_id=self.practica_id)
        if self.pk is not None:
            registros = registros.exclude(pk=self.pk)
        return registros.exists()

    def _fila_existente(self, using=None):
        if self.pk is None:
            return False
        alias = using or self._state.db or "default"
        return HistorialEstado.objects.using(alias).filter(pk=self.pk).exists()

    def save_base(self, raw=False, force_insert=False, force_update=False, using=None, update_fields=None):
        """Acepta solo altas nuevas; cualquier reescritura falla cerrado."""
        if not self._state.adding or self._fila_existente(using):
            raise ValidationError(MENSAJE_INMUTABLE)
        return super().save_base(raw=raw, force_insert=True, using=using, update_fields=update_fields)

    def delete(self, using=None, keep_parents=False):
        raise ValidationError(MENSAJE_INMUTABLE)
