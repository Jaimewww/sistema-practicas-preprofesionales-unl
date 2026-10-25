"""Contract shared by the two write APIs integrated from #69 (PATCH) and #67 (POST).

Both endpoints live in the same module and use the same demo adapter, so these
tests go through the public HTTP interface and pin what must not leak from one to
the other: each route answers only its own method with its own `Allow`, the
`PATCH` stays callable without a CSRF token while the `POST` keeps Django's CSRF
check, `DEBUG=False` closes both, and each endpoint keeps its error shape. The
session the report endpoint writes needs a database, so these are `TestCase`.
"""

import json

from django.test import Client, TestCase, override_settings

from .tests import pdf

API = "/api/v1"
PRACTICAS = f"{API}/practicas/"
DETALLE = f"{API}/practicas/1/"
REPORTES = f"{API}/practicas/1/reportes/"
PENDIENTES = f"{API}/pendientes/reporte-1-8/"
SESSION_KEY = "prototipo_reportes"
COOKIE = "prototipo_validaciones"


def reporte(**overrides):
    data = {
        "semana": "9",
        "actividades": "Calificación de los talleres 9 y 10.",
        "horas": "10",
        "evidencias": [pdf("talleres-semana-9.pdf")],
    }
    data.update(overrides)
    return data


def rol_header(rol: str | None):
    """`X-Rol` as Django 5 test headers; no header at all when the role is missing."""
    return {"x-rol": rol} if rol else {}


@override_settings(DEBUG=True)
class ApiContratoIntegradoTests(TestCase):
    def setUp(self):
        self.client = Client()

    def patch(self, body=None, clave="reporte-1-8", rol: str | None = "tutor_academico", client=None):
        cuerpo = {"decision": "aprobado"} if body is None else body
        return (client or self.client).patch(
            f"{API}/pendientes/{clave}/",
            data=json.dumps(cuerpo),
            content_type="application/json",
            headers=rol_header(rol),
        )

    def post(self, client=None, rol: str | None = "estudiante", **overrides):
        return (client or self.client).post(
            REPORTES, reporte(**overrides), headers=rol_header(rol)
        )

    def get(self, url, rol: str | None = "estudiante", client=None):
        return (client or self.client).get(url, headers=rol_header(rol))

    def test_each_route_answers_its_own_method(self):
        self.assertEqual(self.get(PRACTICAS).status_code, 200)
        self.assertEqual(self.post().status_code, 201)
        self.assertEqual(self.patch().status_code, 200)

    def test_each_route_rejects_the_other_methods_with_its_allow_header(self):
        permitido = {PRACTICAS: "GET", DETALLE: "GET", REPORTES: "POST", PENDIENTES: "PATCH"}
        for url, metodo in permitido.items():
            for method in ("get", "post", "put", "patch", "delete", "head", "options"):
                if method.upper() == metodo:
                    continue
                with self.subTest(url=url, method=method):
                    response = getattr(self.client, method)(
                        url, headers=rol_header("tutor_academico")
                    )
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(response.headers["Allow"], metodo)
                    if method != "head":
                        self.assertEqual(response.json()["error"]["code"], "metodo_no_permitido")

    def test_each_write_endpoint_keeps_its_own_role(self):
        self.assertEqual(self.post(rol="tutor_academico").status_code, 403)
        self.assertEqual(self.patch(rol="estudiante").status_code, 403)
        self.assertEqual(self.patch(rol=None).status_code, 401)
        self.assertEqual(self.post(rol=None).status_code, 401)

    def test_decision_endpoint_keeps_its_csrf_exemption(self):
        client = Client(enforce_csrf_checks=True)
        response = self.patch(client=client)
        self.assertEqual(response.status_code, 200)
        self.assertIn(COOKIE, response.cookies)

    def test_report_endpoint_keeps_the_django_csrf_check(self):
        client = Client(enforce_csrf_checks=True)
        before = self.get(DETALLE, client=client).json()
        response = self.post(client=client)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(SESSION_KEY, client.session)
        self.assertEqual(self.get(DETALLE, client=client).json(), before)

    def test_report_endpoint_accepts_a_request_with_the_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/prototipo/reporte-semanal/nuevo/")
        token = client.cookies["csrftoken"].value
        response = client.post(
            REPORTES,
            reporte(),
            HTTP_X_CSRFTOKEN=token,
            headers=rol_header("estudiante"),
        )
        self.assertEqual(response.status_code, 201)

    @override_settings(DEBUG=False)
    def test_debug_off_closes_both_endpoints_even_with_a_role(self):
        for rol in (None, "estudiante", "tutor_academico"):
            with self.subTest(rol=rol):
                self.assertEqual(self.get(PRACTICAS, rol=rol).status_code, 404)
                self.assertEqual(self.post(rol=rol).status_code, 404)
                self.assertEqual(self.patch(rol=rol).status_code, 404)

    def test_an_invalid_decision_still_answers_422_without_touching_the_browser_state(self):
        for body in ({"decision": None}, {"decision": ["aprobado"]}, {"decision": "borrar"}):
            with self.subTest(body=body):
                response = self.patch(body=body)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response["Content-Type"], "application/json")
                self.assertEqual(response.json()["error"]["code"], "dato_invalido")
                self.assertNotIn(COOKIE, response.cookies)
                self.assertNotIn(COOKIE, self.client.cookies)
        self.assertEqual(self.patch().status_code, 200)

    def test_each_endpoint_keeps_its_own_error_shape(self):
        self.assertEqual(self.patch().status_code, 200)
        repetido = self.patch()
        self.assertEqual(repetido.status_code, 409)
        self.assertEqual(repetido.json()["error"]["recurso"], PENDIENTES)
        invalido = self.post(horas="11")
        self.assertEqual(invalido.status_code, 422)
        self.assertIn("horas", invalido.json()["error"]["campos"])
        self.assertNotIn("recurso", invalido.json()["error"])
        self.assertEqual(self.post().status_code, 201)
        ya_enviado = self.post()
        self.assertEqual(ya_enviado.status_code, 409)
        self.assertNotIn("recurso", ya_enviado.json()["error"])

    def test_each_endpoint_writes_only_its_own_browser_state(self):
        self.post()
        self.assertIn(SESSION_KEY, self.client.session)
        self.assertNotIn(COOKIE, self.client.cookies)
        otro = Client()
        self.assertEqual(self.patch(client=otro).status_code, 200)
        self.assertIn(COOKIE, otro.cookies)
        self.assertNotIn(SESSION_KEY, otro.session)

    def test_the_practice_query_still_shows_the_reports_of_that_session(self):
        antes = self.get(DETALLE).json()
        self.assertEqual(self.post().status_code, 201)
        despues = self.get(DETALLE).json()
        self.assertEqual(despues["horas_en_revision"], antes["horas_en_revision"] + 10)
        semana = next(r for r in despues["reportes"] if r["semana"] == 9)
        self.assertEqual(semana["estado"], "en_revision")
        self.assertEqual(self.get(DETALLE, client=Client()).json(), antes)
