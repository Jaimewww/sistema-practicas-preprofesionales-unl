"""Política pura del plazo de un reporte semanal faltante (HU-06 #1, RF-07, T12).

Una semana completa se ancla en la **fecha real** de inicio de la práctica
(decisión ``practice_start``): la semana 1 empieza el día del inicio real y
cierra seis días después, así que la semana *n* cierra en ``inicio + 7n − 1``.
Con un inicio el jueves 9 de abril de 2026, la semana 1 cierra el miércoles 15.

El plazo de reporte (``ConfiguracionCarrera.plazo_reporte_dias``, 3 por defecto)
es de **días naturales**, como en el demo: no se descuentan sábados, domingos ni
feriados. El último día oportuno es ``cierre + plazo`` y «vencido» es
estrictamente después de ese día.

La función es pura: recibe el inicio real, el número de semana, la fecha
evaluada y el plazo; no lee el reloj, no consulta la base de datos, no arma un
calendario de semanas esperadas, no evalúa semanas parciales ni emite alertas.
Por eso la prueba es ``SimpleTestCase``: cualquier consulta fallaría.
"""

from datetime import date

from django.test import SimpleTestCase

from apps.alertas.plazos_reporte import MENSAJE_SEMANA, evaluar_plazo_reporte_semanal

# Inicio de referencia en lunes para leer el cierre con su día de la semana.
LUNES = date(2026, 4, 6)
# Inicio del ejemplo de L24: la semana 1 no cierra el domingo sino el miércoles.
JUEVES = date(2026, 4, 9)


def evaluar(inicio, semana, fecha, plazo=3):
    return evaluar_plazo_reporte_semanal(
        fecha_inicio_real=inicio,
        numero_semana=semana,
        fecha=fecha,
        plazo_reporte_dias=plazo,
    )


class CierreDeSemanaCompletaTests(SimpleTestCase):
    """La semana *n* cierra en ``inicio real + 7n − 1`` días."""

    def test_semana_1_cierra_seis_dias_despues_del_inicio(self):
        resultado = evaluar(LUNES, 1, LUNES, plazo=0)

        self.assertEqual(resultado.fecha_cierre, date(2026, 4, 12))

    def test_inicio_en_jueves_corre_el_cierre_al_miercoles(self):
        # L24: inicio jue 9 abr 2026 → la semana 1 cierra el mié 15 abr 2026.
        resultado = evaluar(JUEVES, 1, JUEVES, plazo=0)

        self.assertEqual(resultado.fecha_cierre, date(2026, 4, 15))

    def test_semana_8_cierra_en_el_dia_56(self):
        # 8 semanas completas: 7 × 8 − 1 = 55 días después del inicio.
        resultado = evaluar(LUNES, 8, LUNES, plazo=0)

        self.assertEqual(resultado.fecha_cierre, date(2026, 5, 31))

    def test_el_cierre_no_depende_de_la_fecha_evaluada(self):
        temprano = evaluar(LUNES, 8, date(2026, 4, 6))
        tarde = evaluar(LUNES, 8, date(2027, 4, 6))

        self.assertEqual(temprano.fecha_cierre, tarde.fecha_cierre)


class BordeDelPlazoEnDiasNaturalesTests(SimpleTestCase):
    """El último día oportuno es ``cierre + plazo``; vence al día siguiente."""

    def test_ultimo_dia_oportuno_y_dia_siguiente(self):
        # Cierre dom 12 abr 2026 + 3 días naturales = mié 15 abr 2026.
        justo = evaluar(LUNES, 1, date(2026, 4, 15), plazo=3)
        vencido = evaluar(LUNES, 1, date(2026, 4, 16), plazo=3)

        self.assertEqual(justo.ultimo_dia_oportuno, date(2026, 4, 15))
        self.assertFalse(justo.vencido)
        self.assertTrue(vencido.vencido)

    def test_plazo_0_vence_el_dia_posterior_al_cierre(self):
        cierre = evaluar(LUNES, 2, date(2026, 4, 19), plazo=0)
        posterior = evaluar(LUNES, 2, date(2026, 4, 20), plazo=0)

        self.assertEqual(cierre.fecha_cierre, date(2026, 4, 19))
        self.assertEqual(cierre.ultimo_dia_oportuno, date(2026, 4, 19))
        self.assertFalse(cierre.vencido)
        self.assertTrue(posterior.vencido)

    def test_plazo_configurado_distinto_de_3(self):
        # Cierre de la semana 1 dom 12 abr 2026; con 10 días el 22 abr no vence.
        justo = evaluar(LUNES, 1, date(2026, 4, 22), plazo=10)
        vencido = evaluar(LUNES, 1, date(2026, 4, 23), plazo=10)

        self.assertEqual(justo.ultimo_dia_oportuno, date(2026, 4, 22))
        self.assertFalse(justo.vencido)
        self.assertTrue(vencido.vencido)


class EvaluacionAntesDelCierreTests(SimpleTestCase):
    """Antes del cierre la semana todavía no venció, con cualquier plazo."""

    def test_el_dia_del_cierre_no_esta_vencido(self):
        resultado = evaluar(LUNES, 1, date(2026, 4, 12), plazo=0)

        self.assertFalse(resultado.vencido)

    def test_dia_intermedio_de_la_semana_no_esta_vencido(self):
        resultado = evaluar(LUNES, 3, date(2026, 4, 22), plazo=3)

        self.assertEqual(resultado.fecha_cierre, date(2026, 4, 26))
        self.assertFalse(resultado.vencido)

    def test_fecha_anterior_al_inicio_no_esta_vencida(self):
        resultado = evaluar(LUNES, 1, date(2026, 4, 5), plazo=0)

        self.assertFalse(resultado.vencido)


class DiasNaturalesNoHabilesTests(SimpleTestCase):
    """El plazo corre en días naturales: el fin de semana también cuenta."""

    def test_fin_de_semana_cuenta_en_el_plazo(self):
        # Inicio dom 5 abr 2026: la semana 1 cierra el sáb 11 abr 2026.
        inicio = date(2026, 4, 5)
        domingo = evaluar(inicio, 1, date(2026, 4, 12), plazo=1)
        lunes = evaluar(inicio, 1, date(2026, 4, 13), plazo=1)

        self.assertEqual(domingo.fecha_cierre, date(2026, 4, 11))
        self.assertEqual(domingo.ultimo_dia_oportuno, date(2026, 4, 12))
        self.assertFalse(domingo.vencido)
        self.assertTrue(lunes.vencido)


class CalendarioEnElBordeTests(SimpleTestCase):
    """El cálculo es aritmética de fechas, no un calendario de semanas."""

    def test_semana_que_cruza_el_anio(self):
        # Inicio lun 28 dic 2026; la semana 2 cierra el dom 10 ene 2027.
        inicio = date(2026, 12, 28)
        justo = evaluar(inicio, 2, date(2027, 1, 13), plazo=3)
        vencido = evaluar(inicio, 2, date(2027, 1, 14), plazo=3)

        self.assertEqual(justo.fecha_cierre, date(2027, 1, 10))
        self.assertFalse(justo.vencido)
        self.assertTrue(vencido.vencido)

    def test_semana_que_cruza_el_29_de_febrero(self):
        # Inicio jue 24 feb 2028 (bisiesto); la semana 1 cierra el mié 1 mar 2028.
        inicio = date(2028, 2, 24)
        justo = evaluar(inicio, 1, date(2028, 3, 3), plazo=2)
        vencido = evaluar(inicio, 1, date(2028, 3, 4), plazo=2)

        self.assertEqual(justo.fecha_cierre, date(2028, 3, 1))
        self.assertEqual(justo.ultimo_dia_oportuno, date(2028, 3, 3))
        self.assertFalse(justo.vencido)
        self.assertTrue(vencido.vencido)


class SemanaInvalidaTests(SimpleTestCase):
    """La semana es un número entero positivo; la 1 es la primera."""

    def test_semana_0_se_rechaza(self):
        with self.assertRaisesMessage(ValueError, MENSAJE_SEMANA):
            evaluar(LUNES, 0, LUNES)

    def test_semana_negativa_se_rechaza(self):
        with self.assertRaisesMessage(ValueError, MENSAJE_SEMANA):
            evaluar(LUNES, -1, LUNES)

    def test_semana_1_es_valida(self):
        resultado = evaluar(LUNES, 1, LUNES)

        self.assertEqual(resultado.fecha_cierre, date(2026, 4, 12))
