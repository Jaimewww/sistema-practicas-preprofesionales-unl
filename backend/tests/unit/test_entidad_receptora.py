"""Tests del catálogo de entidades receptoras (data-model.md, T014)."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.entidades.models import EntidadReceptora

NOMBRE = "Hospital Central"


class EntidadReceptoraValidacionTests(TestCase):
    """nombre es el único campo obligatorio."""

    def test_nombre_es_obligatorio(self):
        sin_nombre = EntidadReceptora(nombre="")

        with self.assertRaises(ValidationError) as error:
            sin_nombre.full_clean()

        self.assertIn("nombre", error.exception.message_dict)
        self.assertEqual(EntidadReceptora.objects.count(), 0)

    def test_entidad_valida_se_guarda_y_se_lee(self):
        entidad = EntidadReceptora(nombre=NOMBRE)
        entidad.full_clean()
        entidad.save()
        entidad.refresh_from_db()

        self.assertEqual(EntidadReceptora.objects.count(), 1)
        self.assertEqual(entidad.nombre, NOMBRE)

    def test_el_nombre_no_es_unico(self):
        EntidadReceptora.objects.create(nombre=NOMBRE)
        EntidadReceptora.objects.create(nombre=NOMBRE)

        self.assertEqual(EntidadReceptora.objects.filter(nombre=NOMBRE).count(), 2)
