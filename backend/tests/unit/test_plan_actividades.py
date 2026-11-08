"""Tests del modelo PlanActividades (HU-01, RF-01, data-model.md, T022)."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.actividades.models import PlanActividades
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.usuarios.models import Usuario

MENSAJE_VERSION = "La versión del plan debe ser un número entero positivo."


class PlanActividadesFixturesMixin:
    """Carrera, período, estudiante y práctica compartidos por las pruebas."""

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(codigo="ING-SIS", nombre="Ingeniería de Sistemas")
        cls.entidad = EntidadReceptora.objects.create(nombre="Junta Parroquial de San Lucas")
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            nombre="Ana Torres",
            email="ana@example.com",
            rol=Usuario.Rol.ESTUDIANTE,
            password=None,
        )
        cls.practica = cls.crear_practica()

    @classmethod
    def crear_practica(cls):
        practica = Practica(
            estudiante=cls.estudiante,
            carrera=cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
        )
        practica.full_clean()
        practica.save()
        return practica

    def datos(self, **overrides):
        datos = {
            "practica": self.practica,
            "contenido": "Actividades previstas para la práctica.",
        }
        datos.update(overrides)
        return datos

    def guardar(self, **datos):
        plan = PlanActividades(**self.datos(**datos))
        plan.full_clean()
        plan.save()
        return plan


class PlanActividadesValoresInicialesTests(PlanActividadesFixturesMixin, TestCase):
    """El plan nace en revisión, en la versión 1 y con su contenido (HU-01)."""

    def test_estado_inicial_es_en_revision(self):
        plan = self.guardar()
        plan.refresh_from_db()

        self.assertEqual(plan.estado, "en_revision")
        self.assertEqual(plan.get_estado_display(), "En revisión")
        self.assertEqual(PlanActividades.objects.count(), 1)

    def test_version_inicial_es_uno(self):
        plan = self.guardar()
        plan.refresh_from_db()

        self.assertEqual(plan.version, 1)

    def test_contenido_se_guarda(self):
        plan = self.guardar(contenido="Elaborar el diagnóstico de la organización.")
        plan.refresh_from_db()

        self.assertEqual(plan.contenido, "Elaborar el diagnóstico de la organización.")


class PlanActividadesCamposObligatoriosTests(PlanActividadesFixturesMixin, TestCase):
    """práctica, versión, contenido y estado son obligatorios."""

    def test_campos_obligatorios_ausentes_se_rechazan_sin_guardar(self):
        casos = {
            "practica": None,
            "version": None,
            "contenido": "",
            "estado": "",
        }

        for campo, valor in casos.items():
            with self.subTest(campo=campo):
                incompleto = PlanActividades(**self.datos(**{campo: valor}))
                with self.assertRaises(ValidationError) as error:
                    incompleto.full_clean()
                self.assertIn(campo, error.exception.message_dict)
                self.assertEqual(PlanActividades.objects.count(), 0)


class PlanActividadesEstadosTests(PlanActividadesFixturesMixin, TestCase):
    """Los tres estados del plan son válidos y no se admiten otros (HU-01)."""

    def test_los_tres_estados_del_plan_se_guardan(self):
        for version, estado in enumerate(("en_revision", "aprobado", "devuelto"), start=1):
            with self.subTest(estado=estado):
                plan = self.guardar(estado=estado, version=version)
                plan.refresh_from_db()
                self.assertEqual(plan.estado, estado)

        self.assertEqual(PlanActividades.objects.count(), 3)

    def test_estado_fuera_del_vocabulario_es_rechazado(self):
        invalido = PlanActividades(**self.datos(estado="validado"))

        with self.assertRaises(ValidationError) as error:
            invalido.full_clean()

        self.assertIn("estado", error.exception.message_dict)
        self.assertEqual(PlanActividades.objects.count(), 0)


class PlanActividadesVersionTests(PlanActividadesFixturesMixin, TestCase):
    """La versión se aporta explícitamente; el modelo no la incrementa."""

    def test_version_no_positiva_es_rechazada(self):
        for version in (0, -1):
            with self.subTest(version=version):
                invalido = PlanActividades(**self.datos(version=version))
                with self.assertRaises(ValidationError) as error:
                    invalido.full_clean()
                self.assertIn("version", error.exception.message_dict)
                if version == 0:
                    self.assertEqual(error.exception.message_dict["version"], [MENSAJE_VERSION])
                self.assertEqual(PlanActividades.objects.count(), 0)

    def test_version_no_numerica_se_rechaza_sin_romper_full_clean(self):
        valido = self.guardar()
        invalido = PlanActividades(**self.datos(version="no-es-numero"))

        with self.assertRaises(ValidationError) as error:
            invalido.full_clean()

        self.assertIn("version", error.exception.message_dict)
        self.assertEqual(PlanActividades.objects.count(), 1)
        self.assertEqual(PlanActividades.objects.get(pk=valido.pk).version, 1)

    def test_las_versiones_explicitas_se_conservan_como_filas(self):
        devuelto = self.guardar(version=1, estado="devuelto")
        reenviado = self.guardar(version=2, contenido="Actividades corregidas.")

        devuelto.refresh_from_db()
        reenviado.refresh_from_db()

        self.assertEqual(devuelto.version, 1)
        self.assertEqual(devuelto.estado, "devuelto")
        self.assertEqual(reenviado.version, 2)
        self.assertEqual(reenviado.estado, "en_revision")
        self.assertEqual(self.practica.planes_actividades.count(), 2)

    def test_la_misma_version_de_una_practica_no_se_duplica_en_la_base(self):
        self.guardar(version=1)

        with self.assertRaises(IntegrityError), transaction.atomic():
            PlanActividades.objects.create(**self.datos(version=1))

        self.assertEqual(self.practica.planes_actividades.count(), 1)

    def test_la_misma_version_en_otra_practica_es_valida(self):
        otra = self.crear_practica()
        self.guardar(version=1)

        PlanActividades.objects.create(**self.datos(practica=otra, version=1))

        self.assertEqual(PlanActividades.objects.filter(version=1).count(), 2)


class PlanActividadesProteccionTests(PlanActividadesFixturesMixin, TestCase):
    """La práctica de un plan no se elimina en cascada."""

    def test_eliminar_la_practica_es_rechazado(self):
        self.guardar()

        with self.assertRaises(ProtectedError), transaction.atomic():
            self.practica.delete()

        self.assertEqual(PlanActividades.objects.count(), 1)
