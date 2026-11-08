from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from . import sample_data as data


@override_settings(DEBUG=True)
class DirectorSecretariaTests(SimpleTestCase):
    def url(self, name, *args):
        return reverse(f"prototipo:{name}", args=args)

    # --- Director (D1-D2) --------------------------------------------------

    def test_director_closed_practices_list_renders(self):
        response = self.client.get(self.url("cierres_director"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CORDOVA VAZQUEZ JOSE LUIS")
        self.assertContains(response, "AYOVI CANDO MARIA FERNANDA")
        self.assertNotContains(response, data.USUARIO["nombre"])  # practice 1 is not closed

    def test_director_practice_detail_read_only(self):
        response = self.client.get(self.url("practica_director", 8), {"tab": "resultado"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["practica"]["estado"], "cerrada")
        self.assertContains(response, "Resultado de la evaluación final")

        # Tabs exist (resumen has no query string, the rest include tab=).
        self.assertContains(response, 'href="/prototipo/director/practicas/8/"')
        for tab in ("plan", "reportes", "informe", "anexos", "historial", "resultado"):
            self.assertContains(response, f"tab={tab}")

    def test_director_history_tab_is_read_only_and_matches_the_api(self):
        response = self.client.get(self.url("practica_director", 8), {"tab": "historial"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historial de estados")
        historial = response.context["historial"]
        self.assertTrue(historial)
        for estado in {entrada["estado_nuevo_display"] for entrada in historial}:
            self.assertContains(response, estado)
        self.assertNotContains(response, "Marcar como legalizado")
        api = self.client.get("/prototipo/api/v1/practicas/8/historial/", headers={"x-rol": "director"}).json()
        self.assertEqual(
            [(e["estado_anterior"], e["estado_nuevo"], e["autor"], e["fecha"].isoformat()) for e in historial],
            [(e["estado_anterior"], e["estado_nuevo"], e["autor"], e["fecha"]) for e in api["historial"]],
        )

    def test_director_sees_a_closure_made_in_the_same_browser(self):
        self.assertEqual(self.client.get(self.url("practica_director", 7)).status_code, 404)
        self.assertEqual(
            self.client.post(
                "/prototipo/coordinador/practicas/7/cerrar/", {"confirmar": "on"}
            ).status_code,
            302,
        )
        response = self.client.get(self.url("practica_director", 7), {"tab": "historial"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["practica"]["estado"], "cerrada")
        self.assertEqual(response.context["historial"][-1]["estado_nuevo"], "cerrada")
        self.assertEqual(response.context["historial"][-1]["autor"], data.COORDINADOR)
        self.assertContains(self.client.get(self.url("cierres_director")), self.url("practica_director", 7))
        self.assertEqual(Client().get(self.url("practica_director", 7)).status_code, 404)

    def test_director_cannot_open_non_closed_practice(self):
        self.assertEqual(self.client.get(self.url("practica_director", 1)).status_code, 404)

    def test_director_practice_has_no_actions(self):
        response = self.client.get(self.url("practica_director", 8))
        self.assertNotContains(response, "Cerrar práctica")
        self.assertNotContains(response, "Suspender práctica")

    # --- Secretaría (S1-S2) ------------------------------------------------

    def test_secretaria_pending_annexes_list_renders(self):
        response = self.client.get(self.url("anexos_secretaria"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["items"])
        self.assertTrue(all(item["anexo"]["estado"] == "pendiente" for item in response.context["items"]))

    def test_secretaria_legalize_form_renders(self):
        response = self.client.get(self.url("legalizar_anexo", 802))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Marcar como legalizado")

    def test_secretaria_legalize_already_legalized_shows_notice(self):
        response = self.client.get(self.url("legalizar_anexo", 801))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ya fue legalizado")
        self.assertNotContains(response, "Marcar como legalizado")

    def test_secretaria_legalize_repeated_post_is_409_with_the_message(self):
        response = self.client.post(self.url("legalizar_anexo", 801))
        self.assertEqual(response.status_code, 409)
        self.assertContains(response, "ya fue legalizado", status_code=409)
        self.assertNotContains(response, "Marcar como legalizado", status_code=409)

    def test_secretaria_screen_state_reaches_the_api_and_the_previous_cookie_migrates(self):
        from django.core import signing

        from . import secretaria

        previa = {"legalizaciones": {"802": {"autor": data.SECRETARIA, "fecha": data.HOY.isoformat()}}}
        self.client.cookies["prototipo_secretaria"] = signing.dumps(
            previa, salt=secretaria.SALT, compress=True
        )
        listado = self.client.get(self.url("anexos_secretaria"))
        self.assertFalse(any(item["anexo"]["id"] == 802 for item in listado.context["items"]))
        self.assertEqual(listado.cookies["prototipo_secretaria_v2"]["path"], "/")
        repetido = self.client.post(
            "/prototipo/api/v1/anexos/802/legalizacion/", headers={"x-rol": "secretaria"}
        )
        self.assertEqual(repetido.status_code, 409)
        self.assertEqual(
            self.client.post(self.url("legalizar_anexo", 701)).status_code, 302
        )

    def test_secretaria_legalize_persists_in_this_browser_only(self):
        response = self.client.post(self.url("legalizar_anexo", 802), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anexos pendientes de legalización")
        # The annex no longer appears in this browser.
        self.assertFalse(any(item["anexo"]["id"] == 802 for item in response.context["items"]))
        # It still appears in a fresh browser.
        fresh = Client().get(self.url("anexos_secretaria"))
        self.assertTrue(any(item["anexo"]["id"] == 802 for item in fresh.context["items"]))

    def test_secretaria_unknown_annex_returns_404(self):
        self.assertEqual(self.client.get(self.url("legalizar_anexo", 99999)).status_code, 404)

    # --- DEBUG protection --------------------------------------------------

    @override_settings(DEBUG=False)
    def test_prototype_routes_are_404_without_debug(self):
        for name, args in (
            ("cierres_director", ()),
            ("practica_director", (8,)),
            ("anexos_secretaria", ()),
            ("legalizar_anexo", (802,)),
        ):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(self.url(name, *args)).status_code, 404)
