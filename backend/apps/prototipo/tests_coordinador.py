import csv
import io
from datetime import date
from time import perf_counter
from unittest.mock import patch

from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from . import sample_data as data


@override_settings(DEBUG=True)
class CoordinadorTests(SimpleTestCase):
    def url(self, name, *args):
        return reverse(f"prototipo:{name}", args=args)

    def test_all_screens_render(self):
        for name, args in (
            ("practicas_carrera", ()), ("alertas", ()),
            ("practica_coordinador", (7,)), ("cerrar_practica", (7,)),
            ("estado_practica", (1, "suspender")),
            ("consolidado_carrera", ()), ("configuracion_carrera", ()),
            ("consolidado_general", ()),
        ):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(self.url(name, *args)).status_code, 200)

    def test_filters_and_career_isolation(self):
        url = self.url("practicas_carrera")
        response = self.client.get(url)
        self.assertEqual(len(response.context["practicas"]), 150)
        self.assertTrue(all(p["carrera"] == data.CARRERA for p in response.context["practicas"]))
        response = self.client.get(url, {"tipo": "comunitaria", "estado": "cerrada"})
        self.assertTrue(response.context["practicas"])
        self.assertTrue(all(p["tipo"] == "comunitaria" and p["estado"] == "cerrada"
                            for p in response.context["practicas"]))
        self.assertContains(self.client.get(url, {"q": "inexistente"}), "Ninguna práctica")
        for name, args in (("practica_coordinador", (1000,)),
                           ("cerrar_practica", (1000,)),
                           ("estado_practica", (1000, "cancelar"))):
            self.assertEqual(self.client.get(self.url(name, *args)).status_code, 403)
            self.assertEqual(self.client.post(self.url(name, *args), {"motivo": "Prueba"}).status_code,
                             405 if name == "practica_coordinador" else 403)

    def test_closing_persists_in_this_browser_only(self):
        url = self.url("cerrar_practica", 7)
        response = self.client.post(url, {"confirmar": "on"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["practica"]["estado"], "cerrada")
        history = self.client.get(self.url("practica_coordinador", 7), {"tab": "historial"})
        self.assertEqual(history.context["practica"]["historial"][-1]["autor"], data.COORDINADOR)
        self.assertEqual(self.client.post(url, {"confirmar": "on"}).status_code, 400)
        self.assertEqual(Client().get(self.url("practica_coordinador", 7)).context["practica"]["estado"], "en_revision_final")

    def test_close_with_failed_evaluation_preserves_result_in_csv(self):
        response = self.client.post(self.url("cerrar_practica", 10), {"confirmar": "on"}, follow=True)
        self.assertEqual(response.context["practica"]["resultado"], "no_aprobada")
        self.assertEqual(response.context["practica"]["horas_validadas"], 160)
        response = self.client.get(self.url("consolidado_carrera"), {"formato": "csv"})
        rows = list(csv.DictReader(io.StringIO(response.content.decode())))
        row = next(r for r in rows if r["Estudiante"] == "SALAZAR VEGA MARÍA JOSÉ")
        self.assertEqual(row["Resultado"], "No aprobada")

    def test_reset_and_modified_cookie(self):
        self.client.post(self.url("cerrar_practica", 7), {"confirmar": "on"})
        self.client.post(self.url("restablecer_prototipo"))
        url = self.url("practica_coordinador", 7)
        self.assertEqual(self.client.get(url).context["practica"]["estado"], "en_revision_final")
        self.client.cookies["prototipo_coordinador"] = "firma-manipulada"
        self.assertEqual(self.client.get(url).context["practica"]["estado"], "en_revision_final")

    def test_incomplete_closing_and_confirmation_rejected(self):
        self.assertContains(self.client.post(self.url("cerrar_practica", 7), {}), "confirm", status_code=200)
        response = self.client.post(self.url("cerrar_practica", 6), {"confirmar": "on"})
        self.assertContains(response, "No se puede cerrar", status_code=200)
        self.assertEqual(self.client.get(self.url("practica_coordinador", 6)).context["practica"]["estado"], "en_revision_final")

    def test_suspend_resume_cancel_and_terminal_states(self):
        suspend = self.url("estado_practica", 1, "suspender")
        self.assertContains(self.client.post(suspend, {"motivo": "  "}), "motivo")
        before = self.client.get(self.url("practica_coordinador", 1)).context["practica"]["horas_validadas"]
        for action, state in (("suspender", "suspendida"), ("reanudar", "en_curso"), ("suspender", "suspendida"), ("cancelar", "cancelada")):
            response = self.client.post(self.url("estado_practica", 1, action), {"motivo": "Licencia"}, follow=True)
            self.assertEqual(response.context["practica"]["estado"], state)
            self.assertEqual(response.context["practica"]["horas_validadas"], before)
        self.assertEqual(self.client.post(suspend, {"motivo": "Otra"}).status_code, 400)
        self.assertEqual(self.client.get(self.url("estado_practica", 8, "reanudar")).status_code, 400)
        self.assertEqual(self.client.get(self.url("estado_practica", 1, "inventar")).status_code, 400)

    def test_all_detail_tabs_and_read_only_actions(self):
        for tab in ("resumen", "plan", "reportes", "informe", "historial"):
            self.assertEqual(self.client.get(self.url("practica_coordinador", 7), {"tab": tab}).status_code, 200)
        response = self.client.get(self.url("practica_coordinador", 8))
        self.assertNotContains(response, "Cerrar práctica")
        self.assertNotContains(response, "Registrar la evaluación final")
        self.assertContains(self.client.get(self.url("practica_coordinador", 9), {"tab": "informe"}), "No aprobada")

    def test_configuration_validates_and_preserves_assigned_hours(self):
        url = self.url("configuracion_carrera")
        values = {"horas_laboral": 240, "horas_comunitaria": 120,
                  "horas_laboral_distancia": 256, "horas_comunitaria_distancia": 144,
                  "plazo_reporte_dias": 3, "plazo_revision_dias": 5, "umbral_rezago": 90}
        self.assertContains(self.client.post(url, {**values, "umbral_rezago": 101}), "100")
        self.assertContains(self.client.post(url, values), "Configuración guardada")
        self.assertEqual(self.client.get(url).context["form"].initial["umbral_rezago"], 90)
        response = self.client.get(self.url("practica_coordinador", 1))
        self.assertEqual(response.context["practica"]["umbral_rezago"], 90)
        self.assertEqual(response.context["practica"]["horas_requeridas"], 160)

    def test_consolidated_csv_scope_encoding_dates_and_filters(self):
        for name, general in (("consolidado_carrera", False), ("consolidado_general", True)):
            response = self.client.get(self.url(name), {"formato": "csv"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("charset=utf-8", response["Content-Type"])
            rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
            self.assertTrue(rows)
            self.assertEqual(len({r["Carrera"] for r in rows}) > 1, general)
            for row in rows:
                date.fromisoformat(row["Fecha de cierre"])
                self.assertTrue(row["Resultado"])
            response = self.client.get(self.url(name), {"componente": "comunitaria", "formato": "csv"})
            rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
            self.assertTrue(all(r["Componente"] == "Comunitaria" for r in rows))
        self.assertContains(self.client.get(self.url("consolidado_general"), {"periodo": "inexistente"}), "Sin prácticas cerradas")

    def test_debug_guard_and_csrf(self):
        with override_settings(DEBUG=False):
            for name, args in (("practicas_carrera", ()), ("alertas", ()),
                               ("practica_coordinador", (7,)), ("cerrar_practica", (7,)),
                               ("estado_practica", (1, "suspender")), ("consolidado_carrera", ()),
                               ("consolidado_general", ()), ("configuracion_carrera", ())):
                self.assertEqual(self.client.get(self.url(name, *args)).status_code, 404)
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.url("cerrar_practica", 7), {"confirmar": "on"}).status_code, 403)

    @patch.object(data, "_practicas", return_value=[])
    @patch.object(data, "_ESTADOS_SINTETICOS", ("en_curso",))
    def test_ten_dashboard_loads_below_two_seconds(self, _fixtures):
        timings = []
        for _ in range(10):
            start = perf_counter()
            response = self.client.get(self.url("practicas_carrera"))
            timings.append(perf_counter() - start)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["practicas"]), 150)
            self.assertTrue(all(p["estado"] == "en_curso" for p in response.context["practicas"]))
        self.assertLess(max(timings), 2)

    def test_business_day_deadline_and_inactive_alerts(self):
        p = data.get_practica_de_la_carrera(3)
        alerts = data.alertas_de(p)
        self.assertTrue(any(a["tipo"] == "revision_pendiente" for a in alerts))
        for a in alerts:
            if a["tipo"] == "revision_pendiente":
                self.assertLess(a["fecha"].weekday(), 5)
        self.assertEqual(data.sumar_dias_habiles(date(2026, 5, 22), 5), date(2026, 5, 29))
        p["estado"] = "suspendida"
        self.assertEqual(data.alertas_de(p), [])

    def test_alert_types_filters_and_empty_state(self):
        url = self.url("alertas")
        response = self.client.get(url)
        self.assertEqual({a["tipo"] for a in response.context["alertas"]}, set(data.TIPOS_ALERTA))
        for tipo in data.TIPOS_ALERTA:
            response = self.client.get(url, {"tipo": tipo})
            self.assertTrue(response.context["alertas"])
            self.assertTrue(all(a["tipo"] == tipo for a in response.context["alertas"]))
        self.assertContains(self.client.get(url, {"tipo": "inexistente"}), "No hay alertas activas")

    def test_closed_and_assigned_fixtures_are_consistent(self):
        for p in data.practicas_todas():
            if p["estado"] == "asignada":
                self.assertNotEqual(p["plan"]["estado"], "validado")
            if p["estado"] == "cerrada":
                self.assertFalse(data.faltantes_cierre(p))
                self.assertTrue(all(r["validado_el"] <= data.fecha_cierre(p) for r in p["reportes"]))
                self.assertEqual(p["historial"][-1]["autor"], data.COORDINADOR)
