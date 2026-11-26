"""La restricción «exactamente uno de plan, reporte o informe del estudiante» (RF-16).

C-04 y el Corte B (plan:103-127) reutilizan ``Validacion`` como decisión del
tutor académico y extienden su regla de «exactamente uno de plan o reporte» a
«exactamente uno de plan, reporte o informe final del estudiante». La
``CheckConstraint`` la impone la base y ``clean()`` la repite dentro de
``full_clean()``, así que ``objects.create()`` —que no ejecuta ``full_clean()``—
también falla. Las filas existentes ya cumplían la regla anterior, que es un caso
particular de la nueva: la migración ``0006`` solo recrea la restricción.

Los archivos del informe van a un ``MEDIA_ROOT`` temporal, nunca al árbol de
trabajo.
"""

import importlib
import shutil
import tempfile
from collections.abc import Callable
from datetime import date
from typing import cast

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from apps.actividades.models import (
    MENSAJE_EXACTAMENTE_UNO,
    InformeEstudiante,
    PlanActividades,
    Validacion,
)
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario

PDF = b"%PDF-1.4\n% informe final del estudiante\n"
MODULO_MIGRACION = "apps.actividades.migrations.0006_informe_estudiante"
NOMBRE_RESTRICCION = "actividades_validacion_plan_reporte_o_informe"
NOMBRE_RESTRICCION_ANTERIOR = "actividades_validacion_plan_o_reporte"


def pdf(nombre="informe-estudiante.pdf", contenido=PDF):
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


class MediaTemporalMixin:
    """``MEDIA_ROOT`` efímero: el archivo de prueba nunca cae en el repositorio.

    Es un mixin, no un ``TestCase``: el ``super()`` de un ``classmethod`` en una
    clase plana no declara ``setUpClass``/``tearDownClass``, así que el ``cast``
    documenta el contrato que aporta la clase de prueba que lo mezcla.
    """

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp(prefix="rf16-validacion-")
        cls._override_media = override_settings(MEDIA_ROOT=cls._media)
        cls._override_media.enable()
        cast(type[TestCase], super()).setUpClass()

    @classmethod
    def tearDownClass(cls):
        try:
            cast(type[TestCase], super()).tearDownClass()
        finally:
            cls._override_media.disable()
            shutil.rmtree(cls._media, ignore_errors=True)


class ValidacionInformeFixturesMixin:
    """Una práctica con su plan, su reporte y su informe final del estudiante."""

    assertEqual: Callable[..., None]
    assertIn: Callable[..., None]
    assertIsNone: Callable[..., None]
    assertTrue: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(codigo="ING-SIS", nombre="Sistemas")
        cls.entidad = EntidadReceptora.objects.create(nombre="Junta Parroquial")
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            nombre="Estudiante",
            email="estudiante1@example.com",
            rol=Usuario.Rol.ESTUDIANTE,
            password=None,
        )
        cls.tutor = Usuario.objects.create_user(
            username="academico1",
            nombre="Tutor",
            email="academico1@example.com",
            rol=Usuario.Rol.TUTOR_ACADEMICO,
            carrera=cls.carrera,
            password=None,
        )
        cls.practica = Practica(
            estudiante=cls.estudiante,
            carrera=cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
        )
        cls.practica.full_clean()
        cls.practica.save()

    def crear_plan(self):
        return PlanActividades.objects.create(
            practica=self.practica, version=1, contenido="Plan aprobado."
        )

    def crear_reporte(self):
        return ReporteSemanal.objects.create(
            practica=self.practica, semana=1, horas_reportadas=8
        )

    def crear_informe(self):
        return InformeEstudiante.objects.create(
            practica=self.practica,
            estudiante=self.estudiante,
            version=1,
            archivo=pdf(),
        )


class ValidacionInformeModeloTests(
    MediaTemporalMixin, ValidacionInformeFixturesMixin, TestCase
):
    """La decisión sobre el informe convive con las de plan y reporte."""

    def test_una_validacion_con_solo_informe_final_se_guarda(self):
        informe = self.crear_informe()
        validacion = Validacion(
            practica=self.practica,
            informe_estudiante=informe,
            decision=Validacion.Decision.APROBADO,
            autor=self.tutor,
        )

        validacion.full_clean()
        validacion.save()

        guardada = Validacion.objects.get()
        self.assertEqual(guardada.informe_estudiante_id, informe.pk)
        self.assertIsNone(guardada.plan_id)
        self.assertIsNone(guardada.reporte_id)
        self.assertEqual(guardada.autor_id, self.tutor.pk)

    def test_con_dos_referencias_falla_en_la_base_y_en_full_clean(self):
        informe = self.crear_informe()
        reporte = self.crear_reporte()

        with self.assertRaises(ValidationError) as error:
            Validacion(
                practica=self.practica,
                reporte=reporte,
                informe_estudiante=informe,
                decision=Validacion.Decision.APROBADO,
                autor=self.tutor,
            ).full_clean()
        self.assertIn(MENSAJE_EXACTAMENTE_UNO, str(error.exception))

        with transaction.atomic(), self.assertRaises(IntegrityError):
            Validacion.objects.create(
                practica=self.practica,
                reporte=reporte,
                informe_estudiante=informe,
                decision=Validacion.Decision.APROBADO,
                autor=self.tutor,
            )
        self.assertEqual(Validacion.objects.count(), 0)

    def test_con_plan_y_reporte_juntos_sigue_fallando(self):
        """PRESERVE: la regla anterior («uno de dos») sigue vigente en la base."""
        plan = self.crear_plan()
        reporte = self.crear_reporte()

        with self.assertRaises(ValidationError) as error:
            Validacion(
                practica=self.practica,
                plan=plan,
                reporte=reporte,
                decision=Validacion.Decision.APROBADO,
                autor=self.tutor,
            ).full_clean()
        self.assertIn(MENSAJE_EXACTAMENTE_UNO, str(error.exception))
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Validacion.objects.create(
                practica=self.practica,
                plan=plan,
                reporte=reporte,
                decision=Validacion.Decision.APROBADO,
                autor=self.tutor,
            )
        self.assertEqual(Validacion.objects.count(), 0)

    def test_ni_plan_ni_reporte_ni_informe_se_rechaza_sin_escribir(self):
        with self.assertRaises(ValidationError) as error:
            Validacion(
                practica=self.practica,
                decision=Validacion.Decision.APROBADO,
                autor=self.tutor,
            ).full_clean()
        self.assertIn(MENSAJE_EXACTAMENTE_UNO, str(error.exception))
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Validacion.objects.create(
                practica=self.practica,
                decision=Validacion.Decision.APROBADO,
                autor=self.tutor,
            )
        self.assertEqual(Validacion.objects.count(), 0)

    def test_una_version_repetida_del_informe_falla_en_la_base(self):
        self.crear_informe()

        with transaction.atomic(), self.assertRaises(IntegrityError):
            InformeEstudiante.objects.create(
                practica=self.practica,
                estudiante=self.estudiante,
                version=1,
                archivo=pdf(),
            )
        self.assertEqual(InformeEstudiante.objects.count(), 1)

    def test_la_restriccion_nueva_declara_exactamente_uno_de_tres(self):
        nombres = {restriccion.name for restriccion in Validacion._meta.constraints}

        self.assertIn(NOMBRE_RESTRICCION, nombres)
        self.assertNotIn(NOMBRE_RESTRICCION_ANTERIOR, nombres)

    def test_la_migracion_recrea_la_restriccion_en_una_sola_operacion(self):
        """Corte B: se quita la anterior y se crea la nueva en la misma migración."""
        migracion = importlib.import_module(MODULO_MIGRACION).Migration
        nombres = [type(operacion).__name__ for operacion in migracion.operations]
        restricciones = {
            operacion.name: operacion
            for operacion in migracion.operations
            if hasattr(operacion, "name")
        }

        self.assertIn("RemoveConstraint", nombres)
        self.assertIn("AddConstraint", nombres)
        self.assertEqual(
            restricciones["actividades_validacion_plan_o_reporte"].name,
            NOMBRE_RESTRICCION_ANTERIOR,
        )
        del_modelo = next(
            restriccion
            for restriccion in Validacion._meta.constraints
            if restriccion.name == NOMBRE_RESTRICCION
        )
        nueva = next(
            operacion
            for operacion in migracion.operations
            if getattr(operacion, "constraint", None) is not None
            and operacion.constraint.name == NOMBRE_RESTRICCION
        )
        self.assertEqual(nueva.constraint.deconstruct(), del_modelo.deconstruct())
