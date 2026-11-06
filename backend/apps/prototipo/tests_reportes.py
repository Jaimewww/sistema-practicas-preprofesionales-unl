"""Las pantallas E4/E2 del reporte semanal y el índice del demo (issues #64 y #78).

El POST JSON de reportes se retiró con #78: la API real de prácticas vive en
``apps/reportes`` y su flujo completo está en ``tests/integration/test_reportes_flujo.py``.
Aquí queda la pantalla E4, que escribe el reporte en la sesión de este navegador.
"""

from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from .sample_data import HOY, _practicas
from .tests import pdf


def plan_en_revision():
    """Patch the sample data so the student's labor practice has no approved plan."""
    practicas = _practicas()
    practicas[0]["plan"]["estado"] = "en_revision"
    practicas[0]["plan"]["enviado_el"] = HOY
    return patch("apps.prototipo.sample_data._practicas", return_value=practicas)

E2 = "/prototipo/mi-practica/"
E4 = "/prototipo/reporte-semanal/nuevo/"
RESET = "/prototipo/reiniciar-demo/"


def reporte(**overrides):
    data = {
        "semana": "9",
        "actividades": "Calificación de los talleres 9 y 10.\nTutoría de refuerzo.",
        "horas": "10",
        "evidencias": [pdf("talleres-semana-9.pdf")],
    }
    data.update(overrides)
    return data


@override_settings(DEBUG=True)
class ReporteSemanalSessionPageTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_e4_valid_post_shows_the_report_in_review_on_e2(self):
        response = self.client.post(f"{E4}?practica=laboral", reporte(), follow=True)
        self.assertRedirects(response, E2)
        self.assertContains(response, "Reporte de la semana 9 enviado a revisión.")
        self.assertContains(response, "10 h esperando la validación")
        self.assertContains(response, "Reiniciar demo")
        self.assertEqual(response.context["practica"]["horas_en_revision"], 8 + 10)

    def test_index_maps_the_real_api_and_reflects_the_session(self):
        before = self.client.get("/prototipo/", {"rol": "estudiante"})
        self.assertContains(before, "Las prácticas y su registro de reportes ya son la API real (#78)")
        self.assertContains(before, "<td>42 / 8 / 160</td>", html=True)
        self.client.post(E4, reporte())
        after = self.client.get("/prototipo/", {"rol": "estudiante"})
        self.assertContains(after, "<td>42 / 18 / 160</td>", html=True)
        self.assertNotContains(after, "<td>42 / 8 / 160</td>", html=True)

    def test_e4_shows_rule_errors_without_storing(self):
        response = self.client.post(f"{E4}?practica=laboral", reporte(horas="11"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Art. 341 del Reglamento")
        self.assertNotIn("prototipo_reportes", self.client.session)

    def test_e4_offers_returned_weeks_and_rejects_a_week_already_sent(self):
        form = self.client.get(E4)
        self.assertContains(form, 'value="5"')
        self.client.post(E4, reporte())
        response = self.client.post(E4, reporte())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "La semana 9 ya tiene un reporte en revisión.")

    def test_e4_shows_a_missing_plan_as_a_form_error(self):
        with plan_en_revision():
            response = self.client.post(E4, reporte())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "La práctica no tiene un plan de actividades aprobado.")
        self.assertContains(response, "No se pudo guardar el reporte")
        self.assertNotIn("prototipo_reportes", self.client.session)

    def test_reset_clears_the_demo_state(self):
        self.client.post(E4, reporte())
        self.assertEqual(self.client.get(RESET).status_code, 405)
        response = self.client.post(RESET)
        self.assertRedirects(response, E2, fetch_redirect_response=False)
        self.assertNotIn("prototipo_reportes", self.client.session)
        self.assertEqual(self.client.get(E2).context["practica"]["horas_en_revision"], 8)

    @override_settings(DEBUG=False)
    def test_reset_is_unavailable_outside_debug(self):
        self.assertEqual(self.client.post(RESET).status_code, 404)
