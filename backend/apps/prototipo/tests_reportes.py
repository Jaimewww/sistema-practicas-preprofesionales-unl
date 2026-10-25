"""POST /api/v1/practicas/<id>/reportes/ and its E4 integration (issue #64).

State is scoped to the sender's session, so these tests need a database.
"""

from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from .sample_data import HOY, _practicas
from .tests import MB, pdf


def plan_en_revision():
    """Patch the sample data so the student's labor practice has no approved plan."""
    practicas = _practicas()
    practicas[0]["plan"]["estado"] = "en_revision"
    practicas[0]["plan"]["enviado_el"] = HOY
    return patch("apps.prototipo.sample_data._practicas", return_value=practicas)

API = "/api/v1/practicas/"
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
class ApiReportesTests(TestCase):
    url = f"{API}1/reportes/"

    def setUp(self):
        self.client = Client()

    def post(self, url: str | None = None, rol: str | None = "estudiante", **overrides):
        headers = {"X-Rol": rol} if rol else {}
        return self.client.post(url or self.url, reporte(**overrides), headers=headers)

    def detail(self, practica_id=1, client=None):
        response = (client or self.client).get(f"{API}{practica_id}/", HTTP_X_ROL="estudiante")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def semana(self, body, numero):
        return next(r for r in body["reportes"] if r["semana"] == numero)

    def assert_rejected(self, response, status, code):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["error"]["code"], code)

    def assert_unchanged(self, before, practica_id=1):
        self.assertEqual(self.detail(practica_id), before)
        self.assertNotIn("prototipo_reportes", self.client.session)

    def test_valid_report_answers_201_and_the_practice_reflects_it(self):
        before = self.detail()
        response = self.post()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Location"], f"{API}1/")
        body = response.json()["reporte"]
        self.assertEqual(body["semana"], 9)
        self.assertEqual(body["horas"], 10)
        self.assertEqual(body["estado"], "en_revision")
        self.assertEqual(body["estado_display"], "En revisión")
        self.assertEqual(
            body["actividades"],
            ["Calificación de los talleres 9 y 10.", "Tutoría de refuerzo."],
        )
        self.assertEqual(body["evidencias"], ["talleres-semana-9.pdf"])
        self.assertEqual(body["enviado_el"], "2026-06-05")
        self.assertEqual(body["versiones"], [])
        after = self.detail()
        self.assertEqual(after["horas_en_revision"], before["horas_en_revision"] + 10)
        self.assertEqual(after["horas_validadas"], before["horas_validadas"])
        self.assertEqual(self.semana(after, 9)["estado"], "en_revision")

    def test_ayudantia_accepts_exactly_10_hours_and_rejects_11_citing_art_341(self):
        before = self.detail()
        response = self.post(horas="11")
        self.assert_rejected(response, 422, "dato_invalido")
        self.assertIn("Art. 341", response.json()["error"]["campos"]["horas"][0])
        self.assert_unchanged(before)
        self.assertEqual(self.post(horas="10").status_code, 201)

    def test_non_ayudantia_accepts_more_than_10_hours(self):
        response = self.post(url=f"{API}2/reportes/", semana="10", horas="12")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.detail(2)["horas_en_revision"], 6 + 12)

    def test_invalid_fields_and_files_answer_422_without_changing_anything(self):
        before = self.detail()
        heavy = pdf("informe.pdf", size=5 * MB + 1)
        cases = {
            "horas": {"horas": "0"},
            "actividades": {"actividades": ""},
            "evidencias": {"evidencias": [pdf("foto.png")]},
        }
        for field, overrides in cases.items():
            with self.subTest(field=field):
                response = self.post(**overrides)
                self.assert_rejected(response, 422, "dato_invalido")
                self.assertIn(field, response.json()["error"]["campos"])
        for files, message in (([heavy], "5 MB"), ([], "al menos un archivo PDF")):
            response = self.post(evidencias=files)
            self.assert_rejected(response, 422, "dato_invalido")
            self.assertIn(message, response.json()["error"]["campos"]["evidencias"][0])
        self.assert_unchanged(before)

    def test_accepts_an_evidence_of_exactly_5_mb(self):
        self.assertEqual(self.post(evidencias=[pdf(size=5 * MB)]).status_code, 201)

    def test_week_not_offered_answers_422(self):
        before = self.detail()
        for semana in ("12", "abc", ""):
            with self.subTest(semana=semana):
                response = self.post(semana=semana)
                self.assert_rejected(response, 422, "dato_invalido")
                self.assertIn("semana", response.json()["error"]["campos"])
        self.assert_unchanged(before)

    def test_week_already_in_review_or_validated_answers_409(self):
        before = self.detail()
        for semana in ("8", "1"):
            with self.subTest(semana=semana):
                self.assert_rejected(self.post(semana=semana), 409, "transicion_invalida")
        self.assert_unchanged(before)
        self.assertEqual(self.post().status_code, 201)
        self.assert_rejected(self.post(), 409, "transicion_invalida")

    def test_resending_a_returned_report_keeps_the_previous_version(self):
        returned = self.semana(self.detail(), 5)
        self.assertEqual(returned["estado"], "devuelto")
        response = self.post(semana="5", horas="6")
        self.assertEqual(response.status_code, 201)
        body = response.json()["reporte"]
        self.assertEqual(body["estado"], "en_revision")
        self.assertEqual(body["observacion"], "")
        self.assertEqual(len(body["versiones"]), 1)
        previous = body["versiones"][0]
        self.assertEqual(previous["estado"], "devuelto")
        self.assertEqual(previous["observacion"], returned["observacion"])
        self.assertEqual(previous["validado_por"], returned["validado_por"])
        self.assertEqual(self.semana(self.detail(), 5)["versiones"], body["versiones"])
        self.assert_rejected(self.post(semana="5"), 409, "transicion_invalida")

    def test_practice_without_an_approved_plan_answers_409(self):
        with plan_en_revision():
            before = self.detail()
            response = self.post()
            self.assert_rejected(response, 409, "transicion_invalida")
            self.assertIn("plan de actividades aprobado", response.json()["error"]["message"])
            self.assert_unchanged(before)

    def test_foreign_or_unknown_practice_answers_403_and_404(self):
        before = self.detail(1)
        self.assert_rejected(self.post(url=f"{API}3/reportes/"), 403, "fuera_de_rol")
        self.assert_rejected(self.post(url=f"{API}999/reportes/"), 404, "recurso_inexistente")
        self.assert_unchanged(before)

    def test_only_the_student_role_can_send_reports(self):
        for rol in ("tutor_academico", "tutor_entidad", "coordinador"):
            with self.subTest(rol=rol):
                self.assert_rejected(self.post(rol=rol), 403, "fuera_de_rol")
        for rol in (None, "administrador"):
            with self.subTest(rol=rol):
                self.assert_rejected(self.post(rol=rol), 401, "sin_sesion")
        self.assertNotIn("prototipo_reportes", self.client.session)

    def test_other_methods_answer_405_with_allow_post(self):
        for method in ("get", "put", "patch", "delete", "head", "options"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url, HTTP_X_ROL="estudiante")
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response["Allow"], "POST")
                if method != "head":
                    self.assertEqual(response.json()["error"]["code"], "metodo_no_permitido")
        self.assertNotIn("prototipo_reportes", self.client.session)

    def test_state_is_scoped_to_the_session(self):
        self.assertEqual(self.post().status_code, 201)
        other = Client()
        self.assertEqual(self.semana(self.detail(client=other), 9)["estado"], "sin_reporte")

    def test_csrf_is_enforced_for_session_state(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(self.url, reporte(), HTTP_X_ROL="estudiante")
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("prototipo_reportes", client.session)

    @override_settings(DEBUG=False)
    def test_endpoint_is_unavailable_outside_debug(self):
        self.assertEqual(self.post().status_code, 404)


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
        api = self.client.get(f"{API}1/", HTTP_X_ROL="estudiante").json()
        self.assertEqual(api["horas_en_revision"], 8 + 10)

    def test_index_lists_the_endpoint_and_reflects_the_session(self):
        before = self.client.get("/prototipo/", {"rol": "estudiante"})
        self.assertContains(before, "Envío de reportes semanales (#64)")
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
        api = self.client.get(f"{API}1/", HTTP_X_ROL="estudiante").json()
        self.assertEqual(api["horas_en_revision"], 8)

    @override_settings(DEBUG=False)
    def test_reset_is_unavailable_outside_debug(self):
        self.assertEqual(self.client.post(RESET).status_code, 404)
