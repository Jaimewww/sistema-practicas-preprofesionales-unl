"""Contrato del demo que comparten las rutas de escritura del #69 (PATCH) y del #62 (legalización).

Las rutas JSON del demo viven en ``/prototipo/api/v1/`` (#79): ya no comparten prefijo con
la API real. Las que caían en ``/api/v1/practicas/`` (lista, detalle y el POST de
reportes) se retiraron con #78: esos caminos ya son la API real de ``apps.practicas`` y
``apps.reportes``. Lo que queda aquí se prueba por la interfaz HTTP pública y fija lo que
no debe filtrarse entre rutas: cada ruta responde solo a su método con su propio
``Allow``, el ``PATCH`` sigue siendo invocable sin token CSRF, ``DEBUG=False`` las cierra y
cada endpoint conserva su forma de error. El estado del reporte vive en la sesión, así
que estas pruebas son ``TestCase``.
"""

import json
import time
from unittest.mock import patch

from django.core import signing
from django.test import Client, TestCase, override_settings

from . import validaciones

API = "/prototipo/api/v1"
HISTORIAL = f"{API}/practicas/1/historial/"
LEGALIZACION = f"{API}/anexos/802/legalizacion/"
PENDIENTES = f"{API}/pendientes/reporte-1-8/"
COOKIE = "prototipo_validaciones"


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

    def legalizar(self, rol: str | None = "secretaria", client=None):
        return (client or self.client).post(LEGALIZACION, headers=rol_header(rol))

    def get(self, url, rol: str | None = "estudiante", client=None):
        return (client or self.client).get(url, headers=rol_header(rol))

    def test_each_route_answers_its_own_method(self):
        self.assertEqual(self.get(HISTORIAL, rol="director").status_code, 200)
        self.assertEqual(self.legalizar().status_code, 200)
        self.assertEqual(self.patch().status_code, 200)

    def test_each_route_rejects_the_other_methods_with_its_allow_header(self):
        permitido = {PENDIENTES: "PATCH", HISTORIAL: "GET", LEGALIZACION: "POST"}
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
        self.assertEqual(self.patch(rol="estudiante").status_code, 403)
        self.assertEqual(self.patch(rol=None).status_code, 401)
        # La legalización del #62 es solo de la Secretaría.
        for rol in ("estudiante", "tutor_academico", "coordinador", "director"):
            self.assertEqual(self.legalizar(rol=rol).status_code, 403)
        self.assertEqual(self.legalizar(rol=None).status_code, 401)

    def test_decision_endpoint_keeps_its_csrf_exemption(self):
        client = Client(enforce_csrf_checks=True)
        response = self.patch(client=client)
        self.assertEqual(response.status_code, 200)
        self.assertIn(COOKIE, response.cookies)

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

    def test_the_decision_endpoint_keeps_its_own_error_shape(self):
        self.assertEqual(self.patch().status_code, 200)
        repetido = self.patch()
        self.assertEqual(repetido.status_code, 409)
        self.assertEqual(repetido.json()["error"]["recurso"], PENDIENTES)

    def test_the_decision_endpoint_writes_only_its_own_browser_state(self):
        self.assertEqual(self.patch().status_code, 200)
        self.assertIn(COOKIE, self.client.cookies)
        otro = Client()
        self.assertEqual(otro.get(HISTORIAL, headers=rol_header("director")).status_code, 200)
        self.assertNotIn(COOKIE, otro.cookies)

    def test_the_csrf_exemption_does_not_reach_any_screen_write(self):
        client = Client(enforce_csrf_checks=True)
        for url in (
            "/prototipo/tutor/pendientes/reporte-1-8/",   # T2
            "/prototipo/reporte-semanal/nuevo/",          # E4
            "/prototipo/reiniciar-demo/",                 # E2
            "/prototipo/coordinador/restablecer/",        # coordinador
            "/prototipo/coordinador/practicas/1/cerrar/", # coordinador
            "/prototipo/secretaria/anexos/1/legalizar/",  # secretaría
        ):
            with self.subTest(url=url):
                self.assertEqual(client.post(url, {}).status_code, 403)

    def test_the_decision_cookie_expires_after_24_hours_and_ignores_forgeries(self):
        decision = {"decisiones": {"reporte-1-8": {"estado": "validado", "observacion": ""}}}
        reciente = time.time() - 3600
        with patch("django.core.signing.time.time", return_value=reciente):
            valor = signing.dumps(decision, salt=validaciones.SALT, compress=True)
        vigente = Client()
        vigente.cookies[COOKIE] = valor
        self.assertEqual(self.patch(client=vigente).status_code, 409)
        vencida = Client()
        vencida.cookies[COOKIE] = valor
        with patch("django.core.signing.time.time", return_value=reciente + 90000):
            self.assertEqual(self.patch(client=vencida).status_code, 200)
        forjada = Client()
        forjada.cookies[COOKIE] = valor[:-4] + ("aaaa" if not valor.endswith("aaaa") else "bbbb")
        self.assertEqual(self.patch(client=forjada).status_code, 200)
