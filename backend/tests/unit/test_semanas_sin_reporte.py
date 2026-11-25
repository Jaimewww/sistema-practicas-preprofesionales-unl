"""Selección pura de semanas completas sin reporte (HU-06 #1, RF-07, T14).

La selección decide, a una fecha explícita, qué **semanas completas** están
vencidas y siguen sin reporte. Las semanas se numeran desde el inicio real y **no
se renumeran**: si la semana 3 se omite, la siguiente sigue siendo la 4. Una
semana se omite cuando ya fue reportada (una semana ``devuelto`` ya se envió,
L28) o cuando toca una suspensión explícita, incluidos los días de transición
(L29: parte de ese día pudo estar suspendida).

La función es pura: recibe fechas e intervalos confirmados, no lee el reloj, no
consulta la base de datos, no interpreta historial, no infiere un fin real y no
escribe nada; de ahí el ``SimpleTestCase``.
"""

from datetime import date

from django.test import SimpleTestCase

from apps.alertas.plazos_reporte import (
    MENSAJE_FIN_REAL,
    MENSAJE_SUSPENSION,
    semanas_sin_reporte_vencidas,
)

# Inicio de referencia en lunes: la semana 1 va del 6 al 12 de abril de 2026.
LUNES = date(2026, 4, 6)
# Inicio del ejemplo de L24: la semana 1 cierra el miércoles, no el domingo.
JUEVES = date(2026, 4, 9)


def seleccionar(
    fecha, *, inicio=LUNES, plazo=3, reportadas=(), suspensiones=(), fin=None
):
    return semanas_sin_reporte_vencidas(
        fecha_inicio_real=inicio,
        fecha=fecha,
        plazo_reporte_dias=plazo,
        semanas_reportadas=reportadas,
        suspensiones=suspensiones,
        fecha_fin_real=fin,
    )


def numeros(resultado):
    return [semana.numero_semana for semana in resultado]


class SemanasCompletasVencidasTests(SimpleTestCase):
    """Solo las semanas cerradas y vencidas a la fecha, en orden ascendente."""

    def test_devuelve_las_vencidas_en_orden_ascendente(self):
        # Cierres: 12 y 19 de abril (plazo 3 → vencen el 16 y el 23), 26 de
        # abril (vence el 29). El 1 de mayo la semana 4 (cierra el 3) no está
        # completa todavía.
        resultado = seleccionar(date(2026, 5, 1))

        self.assertEqual(numeros(resultado), [1, 2, 3])
        self.assertEqual(
            [
                (s.fecha_inicio, s.fecha_cierre, s.ultimo_dia_oportuno)
                for s in resultado
            ],
            [
                (date(2026, 4, 6), date(2026, 4, 12), date(2026, 4, 15)),
                (date(2026, 4, 13), date(2026, 4, 19), date(2026, 4, 22)),
                (date(2026, 4, 20), date(2026, 4, 26), date(2026, 4, 29)),
            ],
        )

    def test_numeracion_anclada_en_el_inicio_real(self):
        # Jue 9 abr → semana 1 del 9 al 15, no del 6 al 12; la 2 vence el 25.
        resultado = seleccionar(date(2026, 4, 23), inicio=JUEVES)

        self.assertEqual(numeros(resultado), [1])
        self.assertEqual(
            (resultado[0].fecha_inicio, resultado[0].fecha_cierre),
            (JUEVES, date(2026, 4, 15)),
        )

    def test_ultimo_dia_oportuno_no_vence_y_el_siguiente_si(self):
        self.assertEqual(seleccionar(date(2026, 4, 15)), ())
        resultado = seleccionar(date(2026, 4, 16))

        self.assertEqual(numeros(resultado), [1])
        self.assertEqual(resultado[0].ultimo_dia_oportuno, date(2026, 4, 15))
        # Plazo configurado: con 0 la semana 1 vence el 13; con 10, el 21.
        self.assertEqual(numeros(seleccionar(date(2026, 4, 13), plazo=0)), [1])
        self.assertEqual(seleccionar(date(2026, 4, 22), plazo=10), ())

    def test_semana_que_cierra_despues_de_la_fecha_no_se_examina(self):
        # El 11 de abril la semana 1 no cerró; el 12 ya cerró pero falta plazo.
        self.assertEqual(seleccionar(date(2026, 4, 11)), ())
        self.assertEqual(seleccionar(date(2026, 4, 12)), ())

    def test_sin_fin_real_conocido_no_se_infiere_un_cierre(self):
        # El 20 de mayo vencen 1-5; la 6 vence el 20 y todavía está en plazo.
        resultado = seleccionar(date(2026, 5, 20))

        self.assertEqual(numeros(resultado), [1, 2, 3, 4, 5])
        self.assertEqual(resultado[-1].fecha_cierre, date(2026, 5, 10))


class FinRealConocidoTests(SimpleTestCase):
    """Un fin real explícito acota las semanas examinadas; nunca se inventa."""

    def test_ninguna_semana_cierra_despues_del_fin_real(self):
        resultado = seleccionar(date(2026, 5, 20), fin=date(2026, 4, 19))

        self.assertEqual(numeros(resultado), [1, 2])
        self.assertEqual(resultado[-1].fecha_cierre, date(2026, 4, 19))

    def test_fin_real_a_mitad_de_semana_excluye_esa_semana_incompleta(self):
        # Fin mié 15: la semana 1 (cierra el 12) entra; la 2 (cierra el 19) no.
        resultado = seleccionar(date(2026, 5, 20), fin=date(2026, 4, 15))

        self.assertEqual(numeros(resultado), [1])
        self.assertEqual(seleccionar(date(2026, 5, 20), fin=date(2026, 4, 10)), ())

    def test_fin_real_anterior_al_inicio_real_se_rechaza(self):
        with self.assertRaisesMessage(ValueError, MENSAJE_FIN_REAL):
            seleccionar(date(2026, 5, 20), fin=date(2026, 4, 5))


class SemanasReportadasTests(SimpleTestCase):
    """Una semana ya enviada se omite sin renumerar el resto."""

    def test_semana_reportada_se_omite_sin_renumerar(self):
        resultado = seleccionar(date(2026, 5, 1), reportadas={2})

        self.assertEqual(numeros(resultado), [1, 3])
        # La semana 3 conserva su anclaje: 20-26 de abril, vence el 29.
        self.assertEqual(
            (resultado[1].fecha_inicio, resultado[1].fecha_cierre),
            (date(2026, 4, 20), date(2026, 4, 26)),
        )

    def test_numeros_fuera_del_calendario_se_ignoran_sin_mutar(self):
        reportadas = {0, 99}

        resultado = seleccionar(date(2026, 5, 1), reportadas=reportadas)

        self.assertEqual(numeros(resultado), [1, 2, 3])
        self.assertEqual(reportadas, {0, 99})
        self.assertEqual(seleccionar(date(2026, 5, 1), reportadas={1, 2, 3}), ())


class SuspensionesTests(SimpleTestCase):
    """Cualquier semana que toque una suspensión se omite, bordes incluidos."""

    def test_semana_que_toca_la_suspension_se_omite(self):
        # La suspensión del 20 al 21 de abril cae dentro de la semana 3.
        resultado = seleccionar(
            date(2026, 5, 10), suspensiones=[(date(2026, 4, 20), date(2026, 4, 21))]
        )

        self.assertEqual(numeros(resultado), [1, 2, 4])

    def test_dias_de_transicion_en_los_bordes_omiten_la_semana(self):
        # Lunes 13 = primer día de la 2; domingo 12 = cierre de la 1.
        en_inicio = seleccionar(
            date(2026, 5, 1), suspensiones=[(date(2026, 4, 13), date(2026, 4, 13))]
        )
        en_cierre = seleccionar(
            date(2026, 5, 1), suspensiones=[(date(2026, 4, 12), date(2026, 4, 12))]
        )

        self.assertEqual(numeros(en_inicio), [1, 3])
        self.assertEqual(numeros(en_cierre), [2, 3])

    def test_intervalo_que_cruza_dos_semanas_omite_ambas(self):
        # Del domingo 19 (cierre de la 2) al lunes 20 (inicio de la 3).
        resultado = seleccionar(
            date(2026, 5, 1), suspensiones=[(date(2026, 4, 19), date(2026, 4, 20))]
        )

        self.assertEqual(numeros(resultado), [1])

    def test_varias_suspensiones_acotan_varias_semanas(self):
        # Las dos primeras tocan las semanas 3 y 4; las demás no se superponen.
        resultado = seleccionar(
            date(2026, 5, 10),
            suspensiones=[
                (date(2026, 4, 20), date(2026, 4, 20)),
                (date(2026, 5, 3), date(2026, 5, 3)),
                (date(2026, 3, 1), date(2026, 4, 5)),
                (date(2026, 5, 11), date(2026, 5, 12)),
            ],
        )

        self.assertEqual(numeros(resultado), [1, 2])

    def test_intervalo_invertido_se_rechaza_aunque_no_afecte(self):
        with self.assertRaisesMessage(ValueError, MENSAJE_SUSPENSION):
            seleccionar(
                date(2026, 5, 1),
                suspensiones=[(date(2026, 4, 21), date(2026, 4, 20))],
            )
        with self.assertRaisesMessage(ValueError, MENSAJE_SUSPENSION):
            seleccionar(
                date(2026, 4, 1),
                suspensiones=[(date(2026, 7, 2), date(2026, 7, 1))],
            )


class PurezaTests(SimpleTestCase):
    """No hay reloj, base de datos ni mutación: la entrada queda intacta."""

    def test_devuelve_una_tupla_y_no_muta_los_intervalos(self):
        suspensiones = [(date(2026, 4, 20), date(2026, 4, 21))]

        resultado = seleccionar(date(2026, 5, 10), suspensiones=suspensiones)

        self.assertIsInstance(resultado, tuple)
        self.assertEqual(suspensiones, [(date(2026, 4, 20), date(2026, 4, 21))])
