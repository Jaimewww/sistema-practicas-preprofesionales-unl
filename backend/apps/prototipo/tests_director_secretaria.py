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
        for tab in ("plan", "reportes", "informe", "anexos", "resultado"):
            self.assertContains(response, f"tab={tab}")

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
