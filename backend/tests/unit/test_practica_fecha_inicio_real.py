"""Tests de ``Practica.fecha_inicio_real`` (T9, RF-07, S1/S3).

La fecha real de inicio es un dato **opcional y del servidor**: no tiene valor por
defecto, no se rellena en filas históricas y no se deriva de fechas, estados ni
del historial. Este corte solo la persiste: la captura operativa, sus validaciones
de negocio y el calendario de reportes son T10.
"""

from datetime import date
from typing import cast

from django.db import models
from django.forms import modelform_factory
from django.test import TestCase

from apps.actividades.services import aprobar_plan
from apps.practicas.models import AsignacionTutor, Practica
from apps.usuarios.models import Usuario
from tests.unit.test_asignacion_practica import AsignacionFixturesMixin
from tests.unit.test_plan_actividades import PlanActividadesFixturesMixin
from tests.unit.test_practica import PracticaFixturesMixin

INICIO = date(2026, 4, 6)


class FechaInicioRealPersistenciaTests(PracticaFixturesMixin, TestCase):
    """Se guarda solo la fecha explícita; omitirla deja NULL, sin valor por defecto."""

    def test_la_fecha_explicita_se_guarda_y_se_relee(self):
        practica = self.guardar(**self.datos_laboral(fecha_inicio_real=INICIO))
        practica.refresh_from_db()

        self.assertEqual(practica.fecha_inicio_real, INICIO)

    def test_omitirla_deja_null_sin_relleno_ni_inferencia(self):
        practica = self.guardar(**self.datos_laboral())
        practica.refresh_from_db()

        self.assertIsNone(practica.fecha_inicio_real)
        self.assertEqual(
            Practica.objects.filter(fecha_inicio_real__isnull=True).count(), 1
        )

    def test_es_un_campo_del_servidor_sin_valor_por_defecto(self):
        campo = cast(models.Field, Practica._meta.get_field("fecha_inicio_real"))

        self.assertIsInstance(campo, models.DateField)
        self.assertTrue(campo.null)
        self.assertTrue(campo.blank)
        self.assertFalse(campo.has_default())
        self.assertFalse(campo.editable)

    def test_no_aparece_en_los_formularios_genericos(self):
        formulario = modelform_factory(Practica, fields="__all__")

        self.assertNotIn("fecha_inicio_real", formulario.base_fields)


class FechaInicioRealAsignacionTests(AsignacionFixturesMixin, TestCase):
    """El alta interna de T018 deja la fecha real en NULL: no hay relleno histórico."""

    def test_el_alta_interna_no_sintetiza_la_fecha(self):
        self.configurar(240)

        practica = self.asignar_nueva()

        self.assertIsNone(practica.fecha_inicio_real)
        self.assertIsNone(Practica.objects.get(pk=practica.pk).fecha_inicio_real)


class FechaInicioRealAprobacionPlanTests(PlanActividadesFixturesMixin, TestCase):
    """Aprobar el plan pasa a «en curso» sin inventar la fecha real de inicio."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.tutor = Usuario.objects.create_user(
            username="academico1",
            nombre="Luis Paredes",
            email="academico@example.com",
            rol=Usuario.Rol.TUTOR_ACADEMICO,
            carrera=cls.carrera,
            password=None,
        )
        AsignacionTutor.objects.create(
            practica=cls.practica, tutor_academico=cls.tutor, desde=date(2026, 3, 1)
        )

    def test_aprobar_el_plan_no_fija_la_fecha_real(self):
        aprobar_plan(plan=self.guardar(), autor=self.tutor)
        self.practica.refresh_from_db()

        self.assertEqual(self.practica.estado, Practica.Estado.EN_CURSO)
        self.assertIsNone(self.practica.fecha_inicio_real)
