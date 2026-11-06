"""Modelo del reporte semanal (S4) y el «exactamente uno» de Validacion (S7, #78).

S4: ``semana`` y ``horas_reportadas`` positivas, ``fecha_registro`` automática,
``estado`` nace ``en_revision`` y la base impone una sola versión activa por
semana. S7: ``Validacion`` gana ``reporte_id`` opcional y la ``CheckConstraint``
«exactamente uno» junto a ``plan_id``; la migración 0003 dice lo mismo que el
modelo.
"""

import importlib
from datetime import date

from apps.actividades.models import MENSAJE_EXACTAMENTE_UNO, PlanActividades, Validacion
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.reportes.models import (
    MENSAJE_HORAS,
    MENSAJE_SEMANA,
    MENSAJE_SEMANA_DUPLICADA,
    ReporteSemanal,
)
from apps.usuarios.models import Usuario
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

NOMBRE_RESTRICCION = "actividades_validacion_plan_o_reporte"
MODULO_MIGRACION = "apps.actividades.migrations.0003_validacion_reporte"


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username, nombre=username.title(), email=f"{username}@example.com",
        rol=rol, carrera=carrera, password=None,
    )


class ReportesFixturesMixin:
    """Un estudiante con dos prácticas laborales propias y un tutor académico."""

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.entidad = EntidadReceptora.objects.create(
            nombre="Junta Parroquial de San Lucas"
        )
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario("academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.practica = cls.crear_practica(240)
        cls.otra_practica = cls.crear_practica(120)

    @classmethod
    def crear_practica(cls, horas):
        practica = Practica(
            estudiante=cls.estudiante, carrera=cls.carrera, entidad=cls.entidad,
            periodo=cls.periodo, tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA, horas_requeridas=horas,
        )
        practica.full_clean()
        practica.save()
        return practica

    def crear_reporte(self, **extra):
        reporte = ReporteSemanal(
            **{"practica": self.practica, "semana": 1, "horas_reportadas": 8, **extra}
        )
        reporte.full_clean()
        reporte.save()
        return reporte


class ReporteSemanalTests(ReportesFixturesMixin, TestCase):
    """Campos, reglas positivas, estado inicial y unicidad por semana (S4)."""

    def test_nace_en_revision_con_su_semana_y_sus_horas(self):
        reporte = self.crear_reporte(semana=3, horas_reportadas=12)
        guardado = ReporteSemanal.objects.get(pk=reporte.pk)
        self.assertEqual(guardado.estado, ReporteSemanal.Estado.EN_REVISION)
        self.assertEqual((guardado.semana, guardado.horas_reportadas), (3, 12))

    def test_la_semana_debe_ser_positiva(self):
        for semana in (0, -1):
            with self.subTest(semana=semana):
                reporte = ReporteSemanal(
                    practica=self.practica, semana=semana, horas_reportadas=8
                )
                with self.assertRaises(ValidationError) as error:
                    reporte.full_clean()
                self.assertIn(MENSAJE_SEMANA, str(error.exception))
                self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_las_horas_reportadas_deben_ser_positivas(self):
        for horas in (0, -1):
            with self.subTest(horas=horas):
                reporte = ReporteSemanal(
                    practica=self.practica, semana=1, horas_reportadas=horas
                )
                with self.assertRaises(ValidationError) as error:
                    reporte.full_clean()
                self.assertIn(MENSAJE_HORAS, str(error.exception))
                self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_el_vocabulario_de_estados_es_el_del_data_model(self):
        self.assertEqual(
            set(ReporteSemanal.Estado.values), {"en_revision", "validado", "devuelto"}
        )
        reporte = ReporteSemanal(
            practica=self.practica, semana=1, horas_reportadas=8, estado="aprobado"
        )
        with self.assertRaises(ValidationError) as error:
            reporte.full_clean()
        self.assertIn("estado", error.exception.message_dict)

    def test_una_sola_version_activa_por_semana_se_impone_en_la_base(self):
        self.crear_reporte()
        with self.assertRaises(ValidationError) as error:
            self.crear_reporte()
        self.assertIn(MENSAJE_SEMANA_DUPLICADA, str(error.exception))
        with transaction.atomic(), self.assertRaises(IntegrityError):
            ReporteSemanal.objects.create(
                practica=self.practica, semana=1, horas_reportadas=4
            )
        self.assertEqual(ReporteSemanal.objects.count(), 1)

    def test_la_misma_semana_en_otra_practica_se_admite(self):
        self.crear_reporte()
        self.crear_reporte(practica=self.otra_practica)
        self.assertEqual(ReporteSemanal.objects.count(), 2)

    def test_la_fecha_de_registro_es_automatica(self):
        campo = ReporteSemanal._meta.get_field("fecha_registro")
        self.assertTrue(campo.auto_now_add and not campo.editable)
        reporte = self.crear_reporte()
        self.assertLessEqual(reporte.fecha_registro, timezone.now())
        self.assertIsNotNone(ReporteSemanal.objects.get(pk=reporte.pk).fecha_registro)

    def test_el_reporte_no_inventa_contenido_ni_version(self):
        nombres = {campo.name for campo in ReporteSemanal._meta.get_fields()}
        self.assertNotIn("contenido", nombres)
        self.assertNotIn("version", nombres)
        self.assertLessEqual(
            {"practica", "semana", "horas_reportadas", "fecha_registro", "estado"},
            nombres,
        )

    def test_la_practica_con_reportes_no_se_elimina(self):
        self.crear_reporte()
        with self.assertRaises(ProtectedError):
            self.practica.delete()


class ValidacionExactamenteUnoTests(ReportesFixturesMixin, TestCase):
    """``plan_id`` o ``reporte_id``, exactamente uno (S7)."""

    def setUp(self):
        self.reporte = self.crear_reporte()
        self.plan = PlanActividades.objects.create(
            practica=self.practica, contenido="Actividades previstas."
        )

    def crear_validacion(self, **extra):
        return Validacion(
            practica=self.practica, autor=self.tutor,
            decision=Validacion.Decision.APROBADO, **extra,
        )

    def test_un_plan_sin_reporte_sigue_siendo_valido(self):
        validacion = self.crear_validacion(plan=self.plan)
        validacion.full_clean()
        validacion.save()
        self.assertIsNone(Validacion.objects.get().reporte_id)

    def test_un_reporte_sin_plan_es_valido(self):
        validacion = self.crear_validacion(reporte=self.reporte)
        validacion.full_clean()
        validacion.save()
        self.assertEqual(Validacion.objects.get().reporte_id, self.reporte.pk)

    def test_ni_plan_ni_reporte_se_rechaza_sin_escribir(self):
        with self.assertRaises(ValidationError) as error:
            self.crear_validacion().full_clean()
        self.assertIn(MENSAJE_EXACTAMENTE_UNO, str(error.exception))
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Validacion.objects.create(
                practica=self.practica, autor=self.tutor,
                decision=Validacion.Decision.APROBADO,
            )
        self.assertEqual(Validacion.objects.count(), 0)

    def test_plan_y_reporte_juntos_se_rechazan_sin_escribir(self):
        with self.assertRaises(ValidationError) as error:
            self.crear_validacion(plan=self.plan, reporte=self.reporte).full_clean()
        self.assertIn(MENSAJE_EXACTAMENTE_UNO, str(error.exception))
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Validacion.objects.create(
                practica=self.practica, autor=self.tutor, plan=self.plan,
                reporte=self.reporte, decision=Validacion.Decision.APROBADO,
            )
        self.assertEqual(Validacion.objects.count(), 0)


class MigracionValidacionReporteTests(ReportesFixturesMixin, TestCase):
    """La migración 0003 declara lo mismo que el modelo (S7)."""

    def operaciones(self):
        migracion = importlib.import_module(MODULO_MIGRACION).Migration
        return {type(operacion).__name__: operacion for operacion in migracion.operations}

    def test_agrega_el_reporte_y_deja_el_plan_opcional(self):
        operaciones = self.operaciones()
        # ``AddField``/``AlterField`` llevan el nombre en la operación, no en el campo.
        self.assertEqual(
            operaciones["AddField"].field.deconstruct()[1:],
            Validacion._meta.get_field("reporte").deconstruct()[1:],
        )
        plan = Validacion._meta.get_field("plan")
        self.assertTrue(plan.null and plan.blank)
        self.assertEqual(
            operaciones["AlterField"].field.deconstruct()[1:], plan.deconstruct()[1:]
        )

    def test_declara_la_restriccion_exactamente_uno(self):
        del_modelo = next(
            restriccion for restriccion in Validacion._meta.constraints
            if restriccion.name == NOMBRE_RESTRICCION
        )
        self.assertEqual(
            self.operaciones()["AddConstraint"].constraint.deconstruct(),
            del_modelo.deconstruct(),
        )


class ParidadDeMigracionTests(TestCase):
    """S7: la migración 0003 y el modelo Validacion no divergeen."""

    def test_deconstruccion_igual_al_estado_de_la_migración(self):
        from django.db.migrations.loader import MigrationLoader

        estado = MigrationLoader(None, ignore_no_migrations=True).project_state(
            ("actividades", "0003_validacion_reporte")
        )
        entidad = estado.models[("actividades", "validacion")]
        for nombre in ("plan", "reporte"):
            campo = entidad.get_field(nombre)
            modelo = Validacion._meta.get_field(nombre)
            self.assertEqual(
                (modelo.null, modelo.blank), (campo.null, campo.blank), nombre
            )
        nombres = [c.name for c in Validacion._meta.constraints]
        self.assertIn("actividades_validacion_plan_o_reporte", nombres)
