"""Política pura del plazo de revisión (HU-06 #2, CU-03 «más allá», T041).

La regla del spec: «un reporte sin revisar **más allá del plazo de revisión** de
su carrera» produce la alerta al tutor académico. «Más allá» es estrictamente
más días que el límite vigente, y el plazo se cuenta en **días hábiles**.

Decisión del usuario (L10): el calendario es «lunes a viernes, como en el
demo». Se cuentan solo las fechas de lunes a viernes **posteriores** al ingreso
a revisión y hasta la fecha evaluada inclusive, es decir el intervalo
``(ingreso, fecha]``; un feriado entre semana cuenta como día hábil, porque el
demo solo excluye sábado y domingo.

La función es pura: recibe el ingreso a revisión, la fecha evaluada y el límite
configurado; no lee el reloj, no consulta la base de datos, no emite alertas y
no resuelve destinatarios. Por eso la prueba es ``SimpleTestCase``: cualquier
consulta a la base fallaría.
"""

from datetime import date

from django.test import SimpleTestCase

from apps.alertas.services import evaluar_plazo_revision

# Lunes de referencia; las fechas concretas de cada clase llevan su día en el
# comentario para que el límite se lea sin calcularlo a mano.
LUNES = date(2026, 3, 2)


def evaluar(ingreso, fecha, limite=5):
    return evaluar_plazo_revision(
        fecha_ingreso=ingreso, fecha=fecha, plazo_revision_dias=limite
    )


class BordeDelPlazoTests(SimpleTestCase):
    """Con límite 5, el quinto día hábil no vence y el sexto sí."""

    def test_quinto_dia_habil_no_esta_vencido(self):
        # (lun 2, lun 9]: mar 3, mié 4, jue 5, vie 6, lun 9 = 5 días hábiles.
        resultado = evaluar(LUNES, date(2026, 3, 9))

        self.assertEqual(resultado.dias_habiles, 5)
        self.assertFalse(resultado.vencido)

    def test_sexto_dia_habil_esta_vencido(self):
        # El martes 10 suma el sexto día hábil: 6 > 5.
        resultado = evaluar(LUNES, date(2026, 3, 10))

        self.assertEqual(resultado.dias_habiles, 6)
        self.assertTrue(resultado.vencido)


class FinDeSemanaEnElBordeTests(SimpleTestCase):
    """El sábado y el domingo no suman días hábiles."""

    def test_domingo_tras_la_semana_completa_no_esta_vencido(self):
        # Ingreso el vie 6: lun 9 a vie 13 son 5 días hábiles; el dom 15 no suma.
        resultado = evaluar(date(2026, 3, 6), date(2026, 3, 15))

        self.assertEqual(resultado.dias_habiles, 5)
        self.assertFalse(resultado.vencido)

    def test_lunes_siguiente_al_domingo_si_esta_vencido(self):
        resultado = evaluar(date(2026, 3, 6), date(2026, 3, 16))

        self.assertEqual(resultado.dias_habiles, 6)
        self.assertTrue(resultado.vencido)

    def test_ingreso_en_sabado_no_cuenta_el_fin_de_semana(self):
        # Ingreso el sáb 7: los 5 días hábiles son lun 9 a vie 13.
        resultado = evaluar(date(2026, 3, 7), date(2026, 3, 13))

        self.assertEqual(resultado.dias_habiles, 5)
        self.assertFalse(resultado.vencido)


class FechaAnteriorOIgualAlIngresoTests(SimpleTestCase):
    """El intervalo es (ingreso, fecha]: no hay días hábiles antes ni el mismo día."""

    def test_fecha_igual_al_ingreso_no_esta_vencida(self):
        resultado = evaluar(LUNES, LUNES, limite=0)

        self.assertEqual(resultado.dias_habiles, 0)
        self.assertFalse(resultado.vencido)

    def test_fecha_anterior_al_ingreso_no_esta_vencida(self):
        resultado = evaluar(LUNES, date(2026, 2, 27), limite=0)

        self.assertEqual(resultado.dias_habiles, 0)
        self.assertFalse(resultado.vencido)


class LimiteConfiguradoTests(SimpleTestCase):
    """El límite entra como dato: no está fijado en 5 ni en otro valor."""

    def test_limite_3_al_tercer_dia_habil_no_vence_y_al_cuarto_si(self):
        # (lun 2, jue 5] = mar 3, mié 4, jue 5 = 3 días hábiles.
        justo = evaluar(LUNES, date(2026, 3, 5), limite=3)
        # (lun 2, vie 6] suma el cuarto día hábil.
        vencido = evaluar(LUNES, date(2026, 3, 6), limite=3)

        self.assertEqual(justo.dias_habiles, 3)
        self.assertFalse(justo.vencido)
        self.assertEqual(vencido.dias_habiles, 4)
        self.assertTrue(vencido.vencido)

    def test_limite_0_vence_el_primer_dia_habil_posterior(self):
        vencido = evaluar(LUNES, date(2026, 3, 3), limite=0)

        self.assertEqual(vencido.dias_habiles, 1)
        self.assertTrue(vencido.vencido)


class FeriadoEntreSemanaTests(SimpleTestCase):
    """Un feriado de lunes a viernes cuenta como día hábil (decisión weekdays_only)."""

    def test_jueves_y_viernes_santos_cuentan_como_dias_habiles(self):
        # Ingreso lun 30 mar; (lun 30, lun 6 abr] = mar 31, mié 1, jue 2 y
        # vie 3 (Semana Santa) y lun 6 = 5 días hábiles, todos contados.
        resultado = evaluar(date(2026, 3, 30), date(2026, 4, 6))

        self.assertEqual(resultado.dias_habiles, 5)
        self.assertFalse(resultado.vencido)

    def test_el_dia_posterior_al_feriado_es_el_sexto_dia_habil(self):
        resultado = evaluar(date(2026, 3, 30), date(2026, 4, 7))

        self.assertEqual(resultado.dias_habiles, 6)
        self.assertTrue(resultado.vencido)


class CalculoSinRecorridoTests(SimpleTestCase):
    """El conteo se resuelve por semanas completas, no día a día."""

    def test_rango_largo_suma_cinco_por_semana(self):
        # Un año exacto de 365 días desde el lunes 2 mar 2026: 52 semanas de 5
        # días hábiles más 1 día restante (el propio lunes final, hábil).
        resultado = evaluar(LUNES, date(2027, 3, 2))

        self.assertEqual(resultado.dias_habiles, 52 * 5 + 1)
        self.assertTrue(resultado.vencido)
