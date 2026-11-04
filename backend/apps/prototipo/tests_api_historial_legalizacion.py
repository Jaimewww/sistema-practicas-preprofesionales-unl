"""Public contract of issue #62 (test-first): read-only history and annex legalization.

Both endpoints reuse the facade and DTO of the API and the signed demo state shared
with the screens. These tests go through the public HTTP interface: the history has
no write route, legalization is Secretary-only with a fixed audit author, CSRF stays
enforced, and a rejected request changes neither the stored state nor the cookie.
"""

import time
from datetime import date
from unittest.mock import patch

from django.core import signing
from django.test import Client, SimpleTestCase, override_settings

from . import sample_data as data
from . import secretaria

API = "/api/v1"
HISTORIAL = f"{API}/practicas/{{}}/historial/"
LEGALIZACION = f"{API}/anexos/{{}}/legalizacion/"
COOKIE = "prototipo_secretaria_v2"
COOKIE_ANTERIOR = "prototipo_secretaria"
S1 = "/prototipo/secretaria/anexos/"
S2 = "/prototipo/secretaria/anexos/{}/legalizar/"

HISTORY_FIELDS = {
    "estado_anterior", "estado_anterior_display", "estado_nuevo",
    "estado_nuevo_display", "autor", "fecha", "motivo",
}
ANEXO_FIELDS = {
    "id", "nombre", "tipo", "archivo", "estado", "estado_display",
    "legalizado_por", "legalizado_el",
}


def rol_header(rol):
    """`X-Rol` as Django 5 test headers; no header at all when the role is missing."""
    return {"x-rol": rol} if rol else {}


@override_settings(DEBUG=True)
class HistorialLegalizacionTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def historial(self, practica_id=8, rol: str | None = "director", client=None):
        return (client or self.client).get(HISTORIAL.format(practica_id), headers=rol_header(rol))

    def legalizar(self, anexo_id=802, rol: str | None = "secretaria", client=None, **datos):
        return (client or self.client).post(
            LEGALIZACION.format(anexo_id), datos, headers=rol_header(rol)
        )

    def pendientes(self, client=None):
        return (client or self.client).get(S1).context["items"]

    # --- Historial (RF-10, HU-09) -----------------------------------------

    def test_history_lists_each_change_with_the_audit_fields_and_has_no_write_route(self):
        response = self.historial(8)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        historial = response.json()["historial"]
        self.assertEqual(len(historial), 4)
        for entrada in historial:
            self.assertEqual(set(entrada), HISTORY_FIELDS)
            date.fromisoformat(entrada["fecha"])
        self.assertEqual(historial[0]["estado_anterior"], "")
        self.assertEqual(historial[0]["estado_anterior_display"], "")
        self.assertEqual(
            (historial[-1]["estado_anterior"], historial[-1]["estado_nuevo"]),
            ("en_revision_final", "cerrada"),
        )
        self.assertEqual(historial[-1]["estado_nuevo_display"], data.ESTADO_PRACTICA["cerrada"])
        self.assertEqual(historial[-1]["autor"], data.COORDINADOR)
        self.assertTrue(historial[-1]["motivo"])
        # Solo lectura: ninguna escritura tiene ruta y el historial no cambia.
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                respuesta = getattr(self.client, method)(
                    HISTORIAL.format(8), headers=rol_header("director")
                )
                self.assertEqual(respuesta.status_code, 405)
                self.assertEqual(respuesta.headers["Allow"], "GET")
        self.assertEqual(self.historial(8).json()["historial"], historial)

    def test_history_roles_career_and_missing_practice(self):
        for rol in (None, "desconocido"):
            respuesta = self.historial(8, rol=rol)
            self.assertEqual(respuesta.status_code, 401)
            self.assertEqual(respuesta.json()["error"]["code"], "sin_sesion")
        for rol in ("estudiante", "tutor_academico", "tutor_entidad", "secretaria"):
            respuesta = self.historial(8, rol=rol)
            self.assertEqual(respuesta.status_code, 403)
            self.assertEqual(respuesta.json()["error"]["code"], "fuera_de_rol")
        for rol in ("director", "coordinador"):
            self.assertEqual(self.historial(8, rol=rol).status_code, 200)
            ajena = self.historial(1000, rol=rol)
            self.assertEqual(ajena.status_code, 403)
            self.assertEqual(ajena.json()["error"]["code"], "fuera_de_rol")
            inexistente = self.historial(99999, rol=rol)
            self.assertEqual(inexistente.status_code, 404)
            self.assertEqual(inexistente.json()["error"]["code"], "recurso_inexistente")
        with override_settings(DEBUG=False):
            self.assertEqual(self.historial(8).status_code, 404)

    def test_history_shows_the_coordinator_changes_of_the_same_browser(self):
        antes = self.historial(1).json()["historial"]
        self.assertEqual(
            self.client.post("/prototipo/coordinador/practicas/1/suspender/", {"motivo": "Licencia"}).status_code,
            302,
        )
        suspendida = self.historial(1).json()["historial"]
        self.assertEqual(len(suspendida), len(antes) + 1)
        self.assertEqual(suspendida[-1]["estado_nuevo"], "suspendida")
        self.assertEqual(suspendida[-1]["autor"], data.COORDINADOR)
        self.assertEqual(suspendida[-1]["motivo"], "Licencia")
        self.assertEqual(
            self.client.post(f"{API}/practicas/7/cierre/", headers=rol_header("coordinador")).status_code,
            200,
        )
        cierre = self.historial(7).json()["historial"][-1]
        self.assertEqual((cierre["estado_anterior"], cierre["estado_nuevo"]), ("en_revision_final", "cerrada"))
        self.assertEqual(cierre["autor"], data.COORDINADOR)
        # Otro navegador no hereda esos cambios y los datos de ejemplo siguen intactos.
        otro = Client()
        self.assertEqual(self.historial(1, client=otro).json()["historial"], antes)
        self.assertEqual(self.historial(7, client=otro).json()["historial"][-1]["estado_nuevo"], "en_revision_final")

    # --- Legalización (RF-04, HU-09) --------------------------------------

    def test_secretary_legalizes_with_the_fixed_author_and_repeating_is_409(self):
        respuesta = self.legalizar(802, autor="OTRA PERSONA", legalizado_por="FALSA")
        self.assertEqual(respuesta.status_code, 200)
        payload = respuesta.json()
        self.assertEqual(set(payload), ANEXO_FIELDS)
        self.assertEqual(payload["id"], 802)
        self.assertEqual(payload["estado"], "legalizado")
        self.assertEqual(payload["estado_display"], data.ESTADO_ANEXO["legalizado"])
        self.assertEqual(payload["legalizado_por"], data.SECRETARIA)
        self.assertEqual(payload["legalizado_el"], data.HOY.isoformat())
        cookie = respuesta.cookies[COOKIE]
        self.assertEqual(cookie["path"], "/")
        self.assertEqual(cookie["max-age"], 86400)
        self.assertTrue(cookie["httponly"])
        repetido = self.legalizar(802)
        self.assertEqual(repetido.status_code, 409)
        self.assertEqual(repetido.json()["error"]["code"], "transicion_invalida")
        self.assertEqual(repetido.json()["error"]["recurso"], LEGALIZACION.format(802))
        self.assertNotIn(COOKIE, repetido.cookies)
        # El ejemplo compartido no se muta: otro navegador puede legalizar el mismo anexo.
        self.assertEqual(self.legalizar(802, client=Client()).status_code, 200)
        self.assertTrue(any(item["anexo"]["id"] == 802 for item in self.pendientes(Client())))

    def test_denied_legalizations_publish_no_cookie_and_change_no_state(self):
        self.assertTrue(any(item["anexo"]["id"] == 802 for item in self.pendientes()))
        for rol in (None, "desconocido"):
            respuesta = self.legalizar(802, rol=rol)
            self.assertEqual(respuesta.status_code, 401)
            self.assertEqual(respuesta.json()["error"]["code"], "sin_sesion")
        for rol in ("estudiante", "tutor_academico", "tutor_entidad", "director", "coordinador"):
            respuesta = self.legalizar(802, rol=rol)
            self.assertEqual(respuesta.status_code, 403)
            self.assertEqual(respuesta.json()["error"]["code"], "fuera_de_rol")
        ajena = self.legalizar(100201)  # anexo de otra carrera
        self.assertEqual(ajena.status_code, 403)
        self.assertEqual(ajena.json()["error"]["code"], "fuera_de_rol")
        faltante = self.legalizar(99999)
        self.assertEqual(faltante.status_code, 404)
        self.assertEqual(faltante.json()["error"]["code"], "recurso_inexistente")
        self.assertNotIn(COOKIE, self.client.cookies)
        self.assertTrue(any(item["anexo"]["id"] == 802 for item in self.pendientes()))
        with override_settings(DEBUG=False):
            self.assertEqual(self.legalizar(802).status_code, 404)
        self.assertEqual(self.legalizar(802).status_code, 200)

    def test_legalization_answers_only_post(self):
        for method in ("get", "put", "patch", "delete", "head", "options"):
            with self.subTest(method=method):
                respuesta = getattr(self.client, method)(
                    LEGALIZACION.format(802), headers=rol_header("secretaria")
                )
                self.assertEqual(respuesta.status_code, 405)
                self.assertEqual(respuesta.headers["Allow"], "POST")
        self.assertNotIn(COOKIE, self.client.cookies)

    def test_legalization_keeps_the_django_csrf_check(self):
        client = Client(enforce_csrf_checks=True)
        rechazado = self.legalizar(802, client=client)
        self.assertEqual(rechazado.status_code, 403)
        self.assertNotIn(COOKIE, client.cookies)
        self.assertTrue(any(item["anexo"]["id"] == 802 for item in self.pendientes(client)))
        client.get(S2.format(802))
        token = client.cookies["csrftoken"].value
        aceptado = client.post(
            LEGALIZACION.format(802), HTTP_X_CSRFTOKEN=token, headers=rol_header("secretaria")
        )
        self.assertEqual(aceptado.status_code, 200)
        self.assertIn(COOKIE, aceptado.cookies)

    def test_secretary_cookie_migrates_expires_and_never_silently_loses_state(self):
        previa = {"legalizaciones": {"802": {"autor": data.SECRETARIA, "fecha": data.HOY.isoformat()}}}
        self.client.cookies[COOKIE_ANTERIOR] = signing.dumps(
            previa, salt=secretaria.SALT, compress=True
        )
        migrada = self.client.get(S1)
        self.assertFalse(any(item["anexo"]["id"] == 802 for item in migrada.context["items"]))
        self.assertIn(COOKIE, migrada.cookies)
        self.assertEqual(migrada.cookies[COOKIE]["path"], "/")
        # La cookie migrada llega al API: la legalización previa se conserva y suma otra.
        self.assertEqual(self.legalizar(802).status_code, 409)
        self.assertEqual(self.legalizar(701).status_code, 200)
        self.assertContains(self.client.get(S2.format(701)), "ya fue legalizado")
        # Firma forjada y cookie vencida: se ignoran por completo.
        forjada = Client()
        forjada.cookies[COOKIE] = "forjada"
        self.assertEqual(self.legalizar(802, client=forjada).status_code, 200)
        vencida = Client()
        reciente = time.time() - 3600
        with patch("django.core.signing.time.time", return_value=reciente):
            vencida.cookies[COOKIE] = signing.dumps(
                {"legalizaciones": {}}, salt=secretaria.SALT, compress=True
            )
        with patch("django.core.signing.time.time", return_value=reciente + 90000):
            self.assertEqual(self.legalizar(802, client=vencida).status_code, 200)
        # Límite de la cookie: 500 sin publicar cookie ni éxito.
        limite = Client()
        with patch.object(secretaria, "LIMITE_COOKIE", 1):
            respuesta = self.legalizar(802, client=limite)
        self.assertEqual(respuesta.status_code, 500)
        self.assertEqual(respuesta.json()["error"]["code"], "error_interno")
        self.assertNotIn(COOKIE, limite.cookies)
        self.assertEqual(self.legalizar(802, client=limite).status_code, 200)

    def test_api_and_screens_share_the_legalization_state_in_both_directions(self):
        self.assertEqual(self.legalizar(802).status_code, 200)
        pantalla = self.client.get(S2.format(802))
        self.assertContains(pantalla, "ya fue legalizado")
        self.assertNotContains(pantalla, "Marcar como legalizado")
        fresco = Client()
        self.assertContains(fresco.get(S2.format(802)), "Marcar como legalizado")
        repetido = self.client.post(S2.format(802))
        self.assertEqual(repetido.status_code, 409)
        self.assertContains(repetido, "ya fue legalizado", status_code=409)
        # Al revés: legalizar desde la pantalla deja el anexo en el estado del API.
        otro = Client()
        self.assertEqual(otro.post(S2.format(701)).status_code, 302)
        self.assertEqual(self.legalizar(701, client=otro).status_code, 409)

    # --- Compatibilidad con los aportes anteriores ------------------------

    def test_older_endpoints_keep_their_previous_access(self):
        for url in (f"{API}/practicas/", f"{API}/practicas/1/", f"{API}/alertas/"):
            for rol in ("director", "secretaria"):
                with self.subTest(url=url, rol=rol):
                    self.assertEqual(self.client.get(url, headers=rol_header(rol)).status_code, 401)
            self.assertEqual(self.client.get(url, headers=rol_header("coordinador")).status_code, 200)
        pendiente = self.client.patch(
            f"{API}/pendientes/reporte-1-8/",
            data='{"decision": "aprobado"}',
            content_type="application/json",
            headers=rol_header("director"),
        )
        self.assertEqual(pendiente.status_code, 401)
