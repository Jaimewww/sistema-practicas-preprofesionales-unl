"""Modelos de entidades receptoras (T014, data-model.md)."""

from django.db import models


class EntidadReceptora(models.Model):
    """Institución donde el estudiante realiza sus prácticas.

    Solo se exige ``nombre``: no hay convenio, contacto ni vigencia en el
    catálogo. La validación se hace con ``full_clean()``; ``save()`` y
    ``objects.create()`` no la ejecutan, como en cualquier modelo de Django.
    """

    nombre = models.CharField(max_length=200)

    class Meta:
        verbose_name = "entidad receptora"
        verbose_name_plural = "entidades receptoras"

    def __str__(self):
        return self.nombre
