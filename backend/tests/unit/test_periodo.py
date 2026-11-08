"""Tests del catálogo de períodos académicos (data-model.md, T015)."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.practicas.models import Periodo

INICIO = date(2026, 1, 1)
FIN = date(2026, 1, 7)
MENSAJE_FIN = "La fecha de fin debe ser posterior a la fecha de inicio."


def datos_periodo(**overrides):
    datos = {"nombre": "2026-1", "fecha_inicio": INICIO, "fecha_fin": FIN}
    datos.update(overrides)
    return datos


def crear_periodo(**overrides):
    return Periodo.objects.create(**datos_periodo(**overrides))


class PeriodoDiasTotalesTests(TestCase):
    """El conteo es inclusivo: del 1 al 7 de enero son 7 días, no 6."""

    def test_del_1_al_7_de_enero_son_7_dias(self):
        periodo = Periodo(**datos_periodo())

        self.assertEqual(periodo.dias_totales, 7)

    def test_dias_adyacentes_son_2_dias(self):
        periodo = Periodo(
            **datos_periodo(fecha_inicio=date(2026, 3, 1), fecha_fin=date(2026, 3, 2))
        )

        self.assertEqual(periodo.dias_totales, 2)

    def test_dias_totales_se_calcula_con_las_fechas_guardadas(self):
        periodo = crear_periodo()
        periodo.refresh_from_db()

        self.assertEqual(periodo.fecha_inicio, INICIO)
        self.assertEqual(periodo.fecha_fin, FIN)
        self.assertEqual(periodo.dias_totales, 7)

    def test_dias_totales_no_admite_asignacion(self):
        periodo = crear_periodo()

        with self.assertRaises(AttributeError):
            setattr(periodo, "dias_totales", 99)

        periodo.refresh_from_db()
        self.assertEqual((periodo.fecha_inicio, periodo.fecha_fin), (INICIO, FIN))
        self.assertEqual(periodo.dias_totales, 7)
        self.assertEqual(Periodo.objects.count(), 1)


class PeriodoValidacionTests(TestCase):
    """nombre, fecha_inicio y fecha_fin obligatorios; el fin es posterior al inicio."""

    def test_fecha_fin_igual_al_inicio_es_rechazada(self):
        mismo_dia = Periodo(**datos_periodo(fecha_fin=INICIO))

        with self.assertRaises(ValidationError) as error:
            mismo_dia.full_clean()

        self.assertEqual(error.exception.message_dict["fecha_fin"], [MENSAJE_FIN])
        self.assertEqual(Periodo.objects.count(), 0)

    def test_fecha_fin_anterior_al_inicio_es_rechazada(self):
        invertido = Periodo(**datos_periodo(fecha_inicio=FIN, fecha_fin=INICIO))

        with self.assertRaises(ValidationError) as error:
            invertido.full_clean()

        self.assertEqual(error.exception.message_dict["fecha_fin"], [MENSAJE_FIN])
        self.assertEqual(Periodo.objects.count(), 0)

    def test_fechas_validas_se_guardan_y_se_leen(self):
        periodo = Periodo(**datos_periodo())
        periodo.full_clean()
        periodo.save()
        periodo.refresh_from_db()

        self.assertEqual(Periodo.objects.count(), 1)
        self.assertEqual(periodo.nombre, "2026-1")
        self.assertEqual(periodo.fecha_inicio, INICIO)
        self.assertEqual(periodo.fecha_fin, FIN)

    def test_nombre_es_obligatorio(self):
        sin_nombre = Periodo(**datos_periodo(nombre=""))

        with self.assertRaises(ValidationError) as error:
            sin_nombre.full_clean()

        self.assertIn("nombre", error.exception.message_dict)
        self.assertEqual(Periodo.objects.count(), 0)

    def test_fecha_inicio_es_obligatoria(self):
        sin_inicio = Periodo(**datos_periodo(fecha_inicio=None))

        with self.assertRaises(ValidationError) as error:
            sin_inicio.full_clean()

        self.assertIn("fecha_inicio", error.exception.message_dict)
        self.assertEqual(Periodo.objects.count(), 0)

    def test_fecha_fin_es_obligatoria(self):
        sin_fin = Periodo(**datos_periodo(fecha_fin=None))

        with self.assertRaises(ValidationError) as error:
            sin_fin.full_clean()

        self.assertIn("fecha_fin", error.exception.message_dict)
        self.assertEqual(Periodo.objects.count(), 0)


class PeriodoSinRestriccionesExtraTests(TestCase):
    """No hay unicidad de nombre ni restricción de solapamiento entre períodos."""

    def test_se_guardan_dos_periodos_con_el_mismo_nombre_y_fechas_solapadas(self):
        crear_periodo()
        crear_periodo(fecha_inicio=date(2026, 1, 5), fecha_fin=date(2026, 1, 12))

        self.assertEqual(Periodo.objects.filter(nombre="2026-1").count(), 2)


class PeriodoRestriccionEnBaseTests(TestCase):
    """El orden de las fechas también lo impone la base, sin pasar por full_clean()."""

    def test_fin_igual_o_anterior_al_inicio_es_rechazado_por_la_base(self):
        for fin in (INICIO, date(2025, 12, 31)):
            with self.subTest(fin=fin), self.assertRaises(IntegrityError), transaction.atomic():
                Periodo.objects.create(**datos_periodo(fecha_fin=fin))

        self.assertEqual(Periodo.objects.count(), 0)

    def test_fin_posterior_al_inicio_se_guarda(self):
        crear_periodo()

        self.assertEqual(Periodo.objects.count(), 1)
