"""Política pura de rezago por horas (HU-06, CU-03, T040).

La regla del spec: «horas esperadas a una fecha = horas requeridas × (días
transcurridos ÷ días del período)» y hay rezago cuando las horas validadas más
las en revisión quedan **por debajo** del umbral de rezago (80 % por defecto) de
las horas esperadas. El ejemplo canónico es 240 h en 16 semanas: en la semana 8
se esperan 120 h y la alerta se genera por debajo de 96 h, no al llegar a 96.

``Periodo.dias_totales`` cuenta el inicio y el fin (ambos incluidos); estos
tests usan la misma convención. La función es pura: recibe la fecha y las horas,
no lee el reloj, no consulta la base de datos y no emite alertas. Por eso la
prueba es ``SimpleTestCase``: cualquier consulta a la base fallaría.
"""

from datetime import date, timedelta
from fractions import Fraction

from apps.alertas.services import evaluar_rezago
from django.test import SimpleTestCase

# 16 semanas inclusivas: del día 1 al 112.
INICIO = date(2026, 1, 5)
FIN = INICIO + timedelta(days=111)
# El día 56 es el último de la semana 8 (56 días inclusivos).
FIN_SEMANA_8 = INICIO + timedelta(days=55)
MENSAJE_PERIODO = "La fecha de fin debe ser posterior a la fecha de inicio."


def evaluar(fecha, validadas, en_revision, umbral=80, requeridas=240):
    return evaluar_rezago(
        horas_requeridas=requeridas,
        horas_validadas=validadas,
        horas_en_revision=en_revision,
        fecha_inicio=INICIO,
        fecha_fin=FIN,
        fecha=fecha,
        umbral_rezago=umbral,
    )


class EjemploCanonicoDelSpecTests(SimpleTestCase):
    """240 h en 16 semanas, semana 8: 120 esperadas y 96 mínimas."""

    def test_semana_8_con_95_horas_esta_en_rezago(self):
        resultado = evaluar(FIN_SEMANA_8, validadas=50, en_revision=45)

        self.assertEqual(resultado.horas_esperadas, Fraction(120))
        self.assertEqual(resultado.horas_minimas, Fraction(96))
        self.assertTrue(resultado.en_rezago)

    def test_semana_8_con_96_horas_no_esta_en_rezago(self):
        resultado = evaluar(FIN_SEMANA_8, validadas=50, en_revision=46)

        self.assertEqual(resultado.horas_minimas, Fraction(96))
        self.assertFalse(resultado.en_rezago)

    def test_ambos_saldos_se_suman_sin_redondear(self):
        """95 h en validadas y 1 h en revisión alcanzan justo las 96 mínimas."""
        resultado = evaluar(FIN_SEMANA_8, validadas=95, en_revision=1)

        self.assertFalse(resultado.en_rezago)


class UmbralConfiguradoTests(SimpleTestCase):
    """El umbral entra como dato: no está fijado en 80 ni en otro valor."""

    def test_umbral_configurado_en_70_no_es_el_80_por_defecto(self):
        resultado = evaluar(FIN_SEMANA_8, validadas=95, en_revision=0, umbral=70)

        self.assertEqual(resultado.horas_esperadas, Fraction(120))
        self.assertEqual(resultado.horas_minimas, Fraction(84))
        self.assertFalse(resultado.en_rezago)

    def test_limite_con_umbral_configurado_en_70(self):
        bajo = evaluar(FIN_SEMANA_8, validadas=83, en_revision=0, umbral=70)
        justo = evaluar(FIN_SEMANA_8, validadas=84, en_revision=0, umbral=70)

        self.assertTrue(bajo.en_rezago)
        self.assertFalse(justo.en_rezago)


class FechasFueraDelPeriodoTests(SimpleTestCase):
    """Los días transcurridos se acotan al período, nunca al reloj."""

    def test_fecha_anterior_al_inicio_no_espera_horas(self):
        resultado = evaluar(INICIO - timedelta(days=1), validadas=0, en_revision=0)

        self.assertEqual(resultado.horas_esperadas, Fraction(0))
        self.assertEqual(resultado.horas_minimas, Fraction(0))
        self.assertFalse(resultado.en_rezago)

    def test_fecha_posterior_al_fin_no_supera_las_horas_requeridas(self):
        bajo = evaluar(FIN + timedelta(days=30), validadas=100, en_revision=91)
        justo = evaluar(FIN + timedelta(days=30), validadas=100, en_revision=92)

        self.assertEqual(bajo.horas_esperadas, Fraction(240))
        self.assertEqual(bajo.horas_minimas, Fraction(192))
        self.assertTrue(bajo.en_rezago)
        self.assertFalse(justo.en_rezago)

    def test_el_primer_dia_del_periodo_cuenta_como_un_dia(self):
        bajo = evaluar(INICIO, validadas=1, en_revision=0)
        justo = evaluar(INICIO, validadas=2, en_revision=0)

        self.assertEqual(bajo.horas_esperadas, Fraction(15, 7))
        self.assertEqual(bajo.horas_minimas, Fraction(12, 7))
        self.assertTrue(bajo.en_rezago)
        self.assertFalse(justo.en_rezago)


class FraccionSinRedondeoTests(SimpleTestCase):
    """El umbral y las horas esperadas se comparan como fracciones exactas."""

    def test_limite_con_minimas_fraccionarias(self):
        # 58 días inclusivos: esperadas = 240 × 58/112 = 870/7 ≈ 124,2857;
        # mínimas al 80 % = 696/7 ≈ 99,4286. Con 99 h hay rezago; redondear
        # las mínimas a 99 lo ocultaría.
        fecha = INICIO + timedelta(days=57)
        bajo = evaluar(fecha, validadas=60, en_revision=39)
        justo = evaluar(fecha, validadas=60, en_revision=40)

        self.assertEqual(bajo.horas_esperadas, Fraction(870, 7))
        self.assertEqual(bajo.horas_minimas, Fraction(696, 7))
        self.assertTrue(bajo.en_rezago)
        self.assertFalse(justo.en_rezago)


class PeriodoInvalidoTests(SimpleTestCase):
    """Un período con el fin no posterior al inicio se rechaza."""

    def test_fin_igual_al_inicio_se_rechaza(self):
        with self.assertRaises(ValueError) as error:
            evaluar_rezago(
                horas_requeridas=240,
                horas_validadas=0,
                horas_en_revision=0,
                fecha_inicio=INICIO,
                fecha_fin=INICIO,
                fecha=INICIO,
                umbral_rezago=80,
            )

        self.assertEqual(str(error.exception), MENSAJE_PERIODO)

    def test_fin_anterior_al_inicio_se_rechaza(self):
        with self.assertRaises(ValueError) as error:
            evaluar_rezago(
                horas_requeridas=240,
                horas_validadas=0,
                horas_en_revision=0,
                fecha_inicio=FIN,
                fecha_fin=INICIO,
                fecha=INICIO,
                umbral_rezago=80,
            )

        self.assertEqual(str(error.exception), MENSAJE_PERIODO)
