"""Tests del modelo AsignacionTutor (data-model.md, T015)."""

from datetime import date

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.usuarios.models import Usuario

MENSAJE_ACTIVA_DUPLICADA = (
    "Ya existe una asignación activa para esta práctica; "
    "cierre la asignación vigente antes de crear otra."
)
MENSAJE_FECHAS = "La fecha de fin no puede ser anterior a la fecha de inicio."


class AsignacionTutorFixturesMixin:
    """Carrera, práctica y tutores válidos compartidos por las pruebas."""

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
        cls.tutor = Usuario.objects.create_user(
            username="tutor1",
            nombre="Luis Paredes",
            email="luis@example.com",
            rol=Usuario.Rol.TUTOR_ACADEMICO,
            carrera=cls.carrera,
            password=None,
        )
        cls.otro_tutor = Usuario.objects.create_user(
            username="tutor2",
            nombre="Marta Ruiz",
            email="marta@example.com",
            rol=Usuario.Rol.TUTOR_ACADEMICO,
            carrera=cls.carrera,
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

    def asignar(self, practica=None, tutor=None, desde=date(2026, 3, 1), hasta=None):
        asignacion = AsignacionTutor(
            practica=practica or self.practica,
            tutor_academico=tutor or self.tutor,
            desde=desde,
            hasta=hasta,
        )
        asignacion.full_clean()
        asignacion.save()
        return asignacion


class AsignacionTutorCamposTests(AsignacionTutorFixturesMixin, TestCase):
    """práctica, tutor académico y desde son obligatorios; hasta nulo es activa."""

    def test_campos_obligatorios_ausentes_se_rechazan_sin_guardar(self):
        for campo in ("practica", "tutor_academico", "desde"):
            with self.subTest(campo=campo):
                incompleta = AsignacionTutor(
                    practica=self.practica,
                    tutor_academico=self.tutor,
                    desde=date(2026, 3, 1),
                )
                setattr(incompleta, campo, None)
                with self.assertRaises(ValidationError) as error:
                    incompleta.full_clean()
                self.assertIn(campo, error.exception.message_dict)
                self.assertEqual(AsignacionTutor.objects.count(), 0)

    def test_hasta_nulo_es_la_asignacion_activa(self):
        asignacion = self.asignar()
        asignacion.refresh_from_db()

        self.assertIsNone(asignacion.hasta)
        self.assertEqual(AsignacionTutor.objects.filter(hasta__isnull=True).count(), 1)


class AsignacionTutorUnicaActivaTests(AsignacionTutorFixturesMixin, TestCase):
    """Un solo tutor académico activo por práctica, con historial conservado."""

    def test_duplicado_activo_full_clean_falla_con_mensaje(self):
        self.asignar()
        duplicada = AsignacionTutor(
            practica=self.practica,
            tutor_academico=self.otro_tutor,
            desde=date(2026, 4, 1),
        )

        with self.assertRaises(ValidationError) as error:
            duplicada.full_clean()
        self.assertEqual(
            error.exception.message_dict[NON_FIELD_ERRORS], [MENSAJE_ACTIVA_DUPLICADA]
        )
        self.assertEqual(AsignacionTutor.objects.count(), 1)

    def test_escritura_directa_sin_full_clean_la_rechaza_la_base(self):
        original = self.asignar()
        pk_original = original.pk
        casos = {
            "objects.create": lambda: AsignacionTutor.objects.create(
                practica=self.practica,
                tutor_academico=self.otro_tutor,
                desde=date(2026, 4, 1),
            ),
            "save": lambda: AsignacionTutor(
                practica=self.practica,
                tutor_academico=self.otro_tutor,
                desde=date(2026, 4, 1),
            ).save(),
        }

        for nombre, escritura in casos.items():
            with self.subTest(escritura=nombre):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    escritura()
                filas = list(AsignacionTutor.objects.order_by("pk"))
                self.assertEqual(len(filas), 1)
                self.assertEqual(filas[0].pk, pk_original)
                self.assertEqual(filas[0].tutor_academico_id, self.tutor.pk)
                self.assertEqual(filas[0].desde, date(2026, 3, 1))
                self.assertIsNone(filas[0].hasta)

    def test_cerrar_la_anterior_y_abrir_otra_conserva_el_historial(self):
        anterior = self.asignar()
        pk_anterior = anterior.pk
        anterior.hasta = date(2026, 3, 31)
        anterior.full_clean()
        anterior.save()

        nueva = self.asignar(tutor=self.otro_tutor, desde=date(2026, 4, 1))
        anterior.refresh_from_db()

        self.assertEqual(anterior.pk, pk_anterior)
        self.assertEqual(anterior.hasta, date(2026, 3, 31))
        self.assertEqual(anterior.tutor_academico_id, self.tutor.pk)
        self.assertIsNone(nueva.hasta)
        self.assertEqual(
            AsignacionTutor.objects.filter(practica=self.practica, hasta__isnull=True).count(), 1
        )
        self.assertEqual(
            AsignacionTutor.objects.filter(practica=self.practica).count(), 2
        )

    def test_varias_asignaciones_cerradas_conviven(self):
        self.asignar(desde=date(2026, 1, 1), hasta=date(2026, 1, 31))
        self.asignar(tutor=self.otro_tutor, desde=date(2026, 2, 1), hasta=date(2026, 2, 28))

        self.assertEqual(
            AsignacionTutor.objects.filter(
                practica=self.practica, hasta__isnull=False
            ).count(),
            2,
        )

    def test_practicas_distintas_tienen_su_activa_y_el_tutor_puede_repetirse(self):
        otra = self.crear_practica()
        self.asignar(practica=self.practica, tutor=self.tutor)
        self.asignar(practica=otra, tutor=self.tutor)

        self.assertEqual(AsignacionTutor.objects.filter(hasta__isnull=True).count(), 2)
        self.assertEqual(
            AsignacionTutor.objects.filter(tutor_academico=self.tutor).count(), 2
        )


class AsignacionTutorFechasTests(AsignacionTutorFixturesMixin, TestCase):
    """El intervalo desde/hasta se valida solo cuando ambas fechas existen."""

    def test_hasta_anterior_a_desde_se_rechaza_sin_guardar(self):
        invalida = AsignacionTutor(
            practica=self.practica,
            tutor_academico=self.tutor,
            desde=date(2026, 3, 10),
            hasta=date(2026, 3, 9),
        )

        with self.assertRaises(ValidationError) as error:
            invalida.full_clean()
        self.assertEqual(error.exception.message_dict["hasta"], [MENSAJE_FECHAS])
        self.assertEqual(AsignacionTutor.objects.count(), 0)

    def test_hasta_igual_a_desde_se_acepta(self):
        asignacion = self.asignar(desde=date(2026, 3, 10), hasta=date(2026, 3, 10))
        asignacion.refresh_from_db()

        self.assertEqual(asignacion.hasta, date(2026, 3, 10))
        self.assertEqual(AsignacionTutor.objects.count(), 1)
