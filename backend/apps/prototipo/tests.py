import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from .forms import ReporteSemanalForm
from .sample_data import SEMANAS_PARA_REPORTAR, TUTOR_ACADEMICO, USUARIO

MB = 1024 * 1024
PDF_HEADER = b"%PDF-1.4\n"


def pdf(name="evidencia.pdf", size=2048):
    return SimpleUploadedFile(
        name,
        PDF_HEADER + b"0" * (size - len(PDF_HEADER)),
        content_type="application/pdf",
    )


def form_data(**overrides):
    data = {
        "semana": SEMANAS_PARA_REPORTAR[0][0],
        "actividades": "Apoyo en la calificación de talleres de Programación.",
        "horas": "8",
    }
    data.update(overrides)
    return data


@override_settings(DEBUG=True)
class MiPracticaPageTests(SimpleTestCase):
    url = "/prototipo/mi-practica/"

    def setUp(self):
        self.client = Client()

    def test_resumen_answers_200_with_state_and_hours(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mi práctica")
        self.assertContains(response, "En curso")
        self.assertContains(response, "Horas validadas")
        self.assertContains(response, "Horas en revisión")
        self.assertContains(response, "Horas requeridas")

    def test_tabs_are_present_and_the_active_one_is_marked(self):
        response = self.client.get(self.url)
        for label in ("Resumen", "Plan", "Reportes semanales", "Informe final"):
            self.assertContains(response, label)
        self.assertContains(response, 'aria-current="page"')

    def test_laboral_ayudantia_is_rezagada_by_default(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Rezagada")
        self.assertContains(response, "Ayudantía de docencia")

    def test_comunitaria_is_al_dia(self):
        response = self.client.get(self.url, {"practica": "comunitaria"})
        self.assertContains(response, "Al día")
        self.assertContains(response, "Proyecto de vinculación")
        self.assertNotContains(response, "Rezagada")

    def test_reportes_tab_shows_every_report_state(self):
        response = self.client.get(self.url, {"tab": "reportes"})
        self.assertEqual(response.status_code, 200)
        for state in ("Validado", "En revisión", "Devuelto"):
            self.assertContains(response, state)
        self.assertContains(response, "Observación")
        self.assertContains(response, "Validado por")
        self.assertContains(response, "Confirmado por la entidad")

    def test_unknown_tab_falls_back_to_resumen(self):
        response = self.client.get(self.url, {"tab": "inexistente"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Avance frente a lo esperado")

    @override_settings(DEBUG=False)
    def test_returns_404_when_debug_is_off(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)


@override_settings(DEBUG=True)
class ReporteSemanalPageTests(TestCase):  # a valid POST writes the session
    url = "/prototipo/reporte-semanal/nuevo/"

    def setUp(self):
        self.client = Client()

    def test_form_answers_200_with_labels(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for label in ("Semana:", "Actividades realizadas:", "Horas:", "Evidencias:"):
            self.assertContains(response, label)
        self.assertContains(response, "(*)")
        self.assertContains(response, "Guardar")
        self.assertContains(response, "Cancelar")
        self.assertContains(response, "5 MB")

    def test_errores_param_renders_the_error_states(self):
        response = self.client.get(self.url, {"errores": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Una ayudantía no puede reportar más de 10")
        self.assertContains(response, "Art. 341 del Reglamento")
        self.assertContains(response, "solo se admiten archivos PDF")
        self.assertContains(response, "5 MB")
        self.assertContains(response, 'aria-invalid="true"')

    def test_post_with_errors_rerenders_the_form(self):
        response = self.client.post(self.url, form_data(horas="11"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Art. 341 del Reglamento")

    def test_valid_post_redirects_to_next(self):
        next_url = "/prototipo/mi-practica/?tab=reportes"
        response = self.client.post(
            f"{self.url}?next={next_url}",
            {**form_data(), "evidencias": [pdf()]},
        )
        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_external_next_is_ignored(self):
        response = self.client.post(
            f"{self.url}?next=https://example.com/",
            {**form_data(), "evidencias": [pdf()]},
        )
        self.assertRedirects(
            response, reverse("prototipo:mi_practica"), fetch_redirect_response=False
        )

    @override_settings(DEBUG=False)
    def test_returns_404_when_debug_is_off(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, form_data()).status_code, 404)


class ReporteSemanalFormTests(SimpleTestCase):
    def build(self, *, ayudantia=True, evidencia=None, **overrides):
        files = MultiValueDict(
            {"evidencias": [evidencia if evidencia is not None else pdf()]}
        )
        return ReporteSemanalForm(
            form_data(**overrides),
            files,
            es_ayudantia=ayudantia,
            semanas=SEMANAS_PARA_REPORTAR,
        )

    def test_accepts_exactly_10_hours_in_ayudantia(self):
        self.assertTrue(self.build(horas="10").is_valid())

    def test_rejects_11_hours_in_ayudantia_citing_art_341(self):
        form = self.build(horas="11")
        self.assertFalse(form.is_valid())
        self.assertIn("Art. 341", " ".join(str(e) for e in form.errors["horas"]))

    def test_allows_more_than_10_hours_outside_ayudantia(self):
        self.assertTrue(self.build(ayudantia=False, horas="12").is_valid())

    def test_rejects_non_pdf(self):
        png = SimpleUploadedFile("foto.png", b"\x89PNG\r\n" + b"0" * 100, "image/png")
        form = self.build(evidencia=png)
        self.assertFalse(form.is_valid())
        self.assertIn("PDF", " ".join(str(e) for e in form.errors["evidencias"]))

    def test_rejects_pdf_extension_without_pdf_content(self):
        fake = SimpleUploadedFile("falso.pdf", b"not really a pdf", "application/pdf")
        self.assertFalse(self.build(evidencia=fake).is_valid())

    def test_rejects_file_over_5_mb(self):
        form = self.build(evidencia=pdf(size=5 * MB + 1))
        self.assertFalse(form.is_valid())
        self.assertIn("5 MB", " ".join(str(e) for e in form.errors["evidencias"]))

    def test_reports_every_invalid_file_and_requires_at_least_one(self):
        files = MultiValueDict(
            {
                "evidencias": [
                    SimpleUploadedFile("a.png", b"\x89PNG", "image/png"),
                    pdf("b.pdf", size=5 * MB + 1),
                ]
            }
        )
        form = ReporteSemanalForm(
            form_data(), files, es_ayudantia=True, semanas=SEMANAS_PARA_REPORTAR
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors["evidencias"]), 2)
        empty = ReporteSemanalForm(
            form_data(), MultiValueDict(), es_ayudantia=True, semanas=SEMANAS_PARA_REPORTAR
        )
        self.assertFalse(empty.is_valid())
        self.assertIn("evidencias", empty.errors)

    def test_accepts_file_of_exactly_5_mb(self):
        self.assertTrue(self.build(evidencia=pdf(size=5 * MB)).is_valid())


class HealthStillWorksTests(SimpleTestCase):
    def test_health_answers_200_with_the_prototype_installed(self):
        self.assertEqual(Client().get("/health/").status_code, 200)


@override_settings(DEBUG=True)
class IndicePageTests(SimpleTestCase):
    """The /prototipo/ index lists every screen by actor plus the API v1 map."""

    url = "/prototipo/"

    def setUp(self):
        self.client = Client()

    def test_index_answers_200_and_groups_screens_by_actor(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estudiante")
        self.assertContains(response, "Tutor académico")
        self.assertContains(response, "Tutor de la entidad")
        for screen in ("Mi práctica", "Pendientes de revisión", "Mis practicantes"):
            self.assertContains(response, screen)

    def test_index_links_to_the_installed_screens(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'href="/prototipo/mi-practica/"')
        self.assertContains(response, 'href="/prototipo/tutor/pendientes/"')
        self.assertContains(response, 'href="/prototipo/entidad/practicantes/"')

    def test_index_has_the_api_v1_section_with_the_first_resource(self):
        response = self.client.get(self.url)
        self.assertContains(response, "API v1")
        self.assertContains(response, 'href="/api/v1/practicas/"')

    def test_role_selector_renders_the_same_practices_as_the_api(self):
        for role in ("estudiante", "tutor_academico", "tutor_entidad", "coordinador"):
            response = self.client.get(self.url, {"rol": role})
            self.assertEqual(response.status_code, 200)
            for practice in self.client.get("/api/v1/practicas/", HTTP_X_ROL=role).json()["practicas"]:
                self.assertContains(response, practice["estudiante"])
        self.assertNotContains(self.client.get(self.url), "QUIZHPE GUAMÁN ANDREA SOFÍA")

    @override_settings(DEBUG=False)
    def test_returns_404_when_debug_is_off(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)


@override_settings(DEBUG=True)
class ApiPracticasTests(SimpleTestCase):
    """GET /api/v1/practicas/ and /api/v1/practicas/<id>/ per emulated role."""

    list_url = "/api/v1/practicas/"

    def setUp(self):
        self.client = Client()

    @override_settings(DEBUG=False)
    def test_api_is_unavailable_outside_debug_even_with_a_role(self):
        for url in (self.list_url, f"{self.list_url}1/"):
            for role in (None, "coordinador"):
                headers = {"X-Rol": role} if role else {}
                self.assertEqual(self.client.get(url, headers=headers).status_code, 404)

    def test_read_only_methods_reject_writes_without_changing_data(self):
        for url in (self.list_url, f"{self.list_url}1/"):
            before = self.client.get(url, HTTP_X_ROL="estudiante").content
            for method in ("post", "put", "patch", "delete", "head", "options"):
                response = getattr(self.client, method)(url, HTTP_X_ROL="estudiante")
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.headers["Allow"], "GET")
                if method != "head":
                    self.assertEqual(response.json()["error"]["code"], "metodo_no_permitido")
            self.assertEqual(self.client.get(url, HTTP_X_ROL="estudiante").content, before)

    def test_unknown_role_is_not_an_identity(self):
        response = self.client.get(self.list_url, HTTP_X_ROL="administrador")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "sin_sesion")

    def test_each_role_has_exact_demo_scope(self):
        for role, expected in (
            ("estudiante", {1, 2}), ("tutor_academico", {1, 3, 4, 5, 6}),
            ("tutor_entidad", {1, 3}), ("coordinador", {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}),
        ):
            with self.subTest(role=role):
                response = self.client.get(self.list_url, HTTP_X_ROL=role)
                self.assertEqual(response.status_code, 200)
                self.assertEqual({p["id"] for p in response.json()["practicas"]}, expected)

    def test_list_answers_200_with_the_shape_of_a_sample_item(self):
        response = self.client.get(self.list_url, HTTP_X_ROL="estudiante")
        self.assertEqual(response.status_code, 200)
        practicas = response.json()["practicas"]
        self.assertEqual(len(practicas), 2)
        item = practicas[0]
        for field in (
            "id",
            "estudiante",
            "tipo",
            "estado",
            "estado_display",
            "horas_requeridas",
            "horas_validadas",
            "horas_en_revision",
            "url",
        ):
            self.assertIn(field, item)

    def test_list_is_scoped_to_the_emulated_role(self):
        estudiante = self.client.get(
            self.list_url, HTTP_X_ROL="estudiante"
        ).json()["practicas"]
        self.assertEqual(
            {p["estudiante"] for p in estudiante}, {USUARIO["nombre"]}
        )
        coordinador = self.client.get(
            self.list_url, HTTP_X_ROL="coordinador"
        ).json()["practicas"]
        self.assertGreater(len(coordinador), len(estudiante))
        tutor = self.client.get(self.list_url, HTTP_X_ROL="tutor_academico").json()[
            "practicas"
        ]
        self.assertTrue(all(p["tutor_academico"] == TUTOR_ACADEMICO for p in tutor))

    def test_detail_answers_200_with_hours_breakdown(self):
        response = self.client.get(f"{self.list_url}1/", HTTP_X_ROL="estudiante")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["id"], 1)
        self.assertEqual(body["horas_validadas"], 42)
        self.assertEqual(body["horas_en_revision"], 8)
        self.assertEqual(body["horas_requeridas"], 160)
        self.assertEqual(body["plan"]["validado_el"], "2026-04-10")
        self.assertEqual(len(body["reportes"]), 9)
        self.assertEqual(body["reportes"][0]["desde"], "2026-04-06")
        self.assertNotIn("pendientes", body)
        for field in ("estado", "horas_validadas", "horas_en_revision", "horas_requeridas"):
            self.assertIn(field, body)

    def test_list_without_identity_answers_401_json(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "sin_sesion")

    def test_detail_of_a_foreign_practice_answers_403_without_altering(self):
        before = self.client.get(self.list_url, HTTP_X_ROL="coordinador").content
        response = self.client.get(f"{self.list_url}4/", HTTP_X_ROL="estudiante")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "fuera_de_rol")
        self.assertEqual(self.client.get(self.list_url, HTTP_X_ROL="coordinador").content, before)

    def test_coordinator_excludes_other_careers_and_dto_excludes_internal_fields(self):
        from .sample_data import _practicas

        practices = _practicas()
        practices[0]["internal_note"] = "not-public"
        practices[0]["plan"]["internal_note"] = "not-public"
        practices[1]["carrera"] = "Otra carrera"
        with patch("apps.prototipo.facade._practicas", return_value=practices):
            response = self.client.get(self.list_url, HTTP_X_ROL="coordinador")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                {p["id"] for p in response.json()["practicas"]}, {1, 3, 4, 5, 6, 7, 8, 9, 10}
            )
            self.assertEqual(self.client.get(f"{self.list_url}2/", HTTP_X_ROL="coordinador").status_code, 403)
            detail = self.client.get(f"{self.list_url}1/", HTTP_X_ROL="coordinador")
            self.assertEqual(detail.status_code, 200)
            self.assertNotContains(detail, "internal_note")

    def test_detail_of_unknown_practice_answers_404_json(self):
        response = self.client.get(f"{self.list_url}999/", HTTP_X_ROL="coordinador")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "recurso_inexistente")


@override_settings(DEBUG=True)
class ApiPendientesTests(SimpleTestCase):
    """PATCH /api/v1/pendientes/<clave>/: the tutor approves or returns a document."""

    COOKIE = "prototipo_validaciones"
    clave = "reporte-1-8"

    def setUp(self):
        self.client = Client()

    def url(self, clave=None):
        return f"/api/v1/pendientes/{clave or self.clave}/"

    def patch_json(self, body, clave=None, role="tutor_academico", client=None):
        data = body if isinstance(body, str) else json.dumps(body)
        headers = {"HTTP_X_ROL": role} if role else {}
        return (client or self.client).patch(
            self.url(clave), data=data, content_type="application/json", **headers
        )

    def assertRejected(self, response, status, code):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.json()["error"]["code"], code)
        self.assertNotIn(self.COOKIE, response.cookies)
        self.assertNotIn(self.COOKIE, self.client.cookies)

    def test_aprobado_validates_the_report_and_records_who_and_when(self):
        response = self.patch_json({"decision": "aprobado"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["clave"], "reporte-1-8")
        self.assertEqual(body["estado"], "validado")
        self.assertEqual(body["validado_por"], TUTOR_ACADEMICO)
        self.assertEqual(body["validado_el"], "2026-06-05")
        self.assertEqual(body["observacion"], "")
        self.assertIn(self.COOKIE, response.cookies)

    def test_aprobado_also_validates_a_plan_and_a_final_report(self):
        for clave, tipo in (("plan-4", "plan"), ("informe-6", "informe")):
            with self.subTest(clave=clave):
                response = self.patch_json({"decision": "aprobado"}, clave=clave)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["tipo"], tipo)
                self.assertEqual(response.json()["estado"], "validado")

    def test_devuelto_returns_the_document_with_the_observation(self):
        response = self.patch_json({"decision": "devuelto", "observacion": "Falta firma"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["estado"], "devuelto")
        self.assertEqual(body["observacion"], "Falta firma")
        self.assertEqual(body["validado_por"], TUTOR_ACADEMICO)
        self.assertIn(self.COOKIE, response.cookies)

    def test_a_500_character_observation_is_accepted(self):
        response = self.patch_json({"decision": "devuelto", "observacion": "x" * 500})
        self.assertEqual(response.status_code, 200)

    def test_decisions_never_mutate_the_shared_sample_data(self):
        from .sample_data import get_pendiente

        self.patch_json({"decision": "aprobado"})
        self.assertEqual(get_pendiente(self.clave)["estado"], "en_revision")

    def test_decisions_delete_nothing_from_the_practice(self):
        before = self.client.get("/api/v1/practicas/1/", HTTP_X_ROL="tutor_academico").json()
        self.patch_json({"decision": "aprobado"})
        after = self.client.get("/api/v1/practicas/1/", HTTP_X_ROL="tutor_academico").json()
        self.assertEqual(len(after["reportes"]), len(before["reportes"]))

    def test_malformed_body_answers_400(self):
        for body in ("{no es json", "[1, 2]", '"aprobado"', ""):
            with self.subTest(body=body):
                self.assertRejected(self.patch_json(body), 400, "solicitud_malformada")

    def test_missing_or_unknown_role_answers_401(self):
        for role in (None, "administrador"):
            with self.subTest(role=role):
                self.assertRejected(
                    self.patch_json({"decision": "aprobado"}, role=role), 401, "sin_sesion"
                )

    def test_other_roles_answer_403(self):
        for role in ("estudiante", "tutor_entidad", "coordinador"):
            with self.subTest(role=role):
                self.assertRejected(
                    self.patch_json({"decision": "aprobado"}, role=role), 403, "fuera_de_rol"
                )

    def test_a_document_of_another_tutor_answers_403_not_404(self):
        response = self.patch_json({"decision": "aprobado"}, clave="reporte-2-9")
        self.assertRejected(response, 403, "fuera_de_rol")

    def test_unknown_key_answers_404(self):
        for clave in ("otra-cosa", "informe-99"):
            with self.subTest(clave=clave):
                response = self.patch_json({"decision": "aprobado"}, clave=clave)
                self.assertRejected(response, 404, "recurso_inexistente")

    def test_other_methods_answer_405_with_allow_patch(self):
        for method in ("get", "post", "put", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url(), HTTP_X_ROL="tutor_academico")
                self.assertRejected(response, 405, "metodo_no_permitido")
                self.assertEqual(response.headers["Allow"], "PATCH")

    def test_an_already_closed_sample_document_answers_409(self):
        response = self.patch_json({"decision": "aprobado"}, clave="reporte-1-3")
        self.assertRejected(response, 409, "transicion_invalida")
        self.assertEqual(response.json()["error"]["recurso"], self.url("reporte-1-3"))

    def test_repeating_a_decision_answers_409_and_keeps_the_first(self):
        first = self.patch_json({"decision": "aprobado"})
        cookie = self.client.cookies[self.COOKIE].value
        second = self.patch_json({"decision": "devuelto", "observacion": "Otra"})
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["error"]["code"], "transicion_invalida")
        self.assertNotIn(self.COOKIE, second.cookies)
        self.assertEqual(self.client.cookies[self.COOKIE].value, cookie)
        self.assertEqual(first.json()["estado"], "validado")

    def test_invalid_decision_answers_422(self):
        for body in ({}, {"decision": "borrar"}, {"decision": None}, {"decision": 1}):
            with self.subTest(body=body):
                self.assertRejected(self.patch_json(body), 422, "dato_invalido")

    def test_a_non_string_decision_answers_422_without_touching_the_stored_state(self):
        """A JSON list or object is unhashable: it is invalid input (422), never a 500."""
        self.patch_json({"decision": "aprobado"}, clave="plan-4")
        cookie = self.client.cookies[self.COOKIE].value
        detalle = self.client.get("/api/v1/practicas/1/", HTTP_X_ROL="tutor_academico").json()
        for decision in (["aprobado"], {"valor": "aprobado"}, [], {}):
            with self.subTest(decision=decision):
                response = self.patch_json({"decision": decision})
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response["Content-Type"], "application/json")
                self.assertEqual(response.json()["error"]["code"], "dato_invalido")
                self.assertNotIn(self.COOKIE, response.cookies)
                self.assertEqual(self.client.cookies[self.COOKIE].value, cookie)
                self.assertEqual(
                    self.client.get(
                        "/api/v1/practicas/1/", HTTP_X_ROL="tutor_academico"
                    ).json(),
                    detalle,
                )
                decidido = self.client.get(self.revisar("plan-4"))
                self.assertContains(decidido, "Validado")
                self.assertNotContains(decidido, 'value="devolver"')

    def test_devuelto_needs_a_valid_observation(self):
        for observacion in (None, "", "   ", 5, "x" * 501):
            with self.subTest(observacion=observacion):
                body = {"decision": "devuelto", "observacion": observacion}
                self.assertRejected(self.patch_json(body), 422, "dato_invalido")
        self.assertRejected(self.patch_json({"decision": "devuelto"}), 422, "dato_invalido")

    def test_curl_style_requests_do_not_need_a_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        response = self.patch_json({"decision": "aprobado"}, client=client)
        self.assertEqual(response.status_code, 200)

    def test_the_endpoint_is_unavailable_outside_debug(self):
        with override_settings(DEBUG=False):
            for role in (None, "tutor_academico"):
                response = self.patch_json({"decision": "aprobado"}, role=role)
                self.assertEqual(response.status_code, 404)

    def test_patch_on_the_read_only_practice_endpoints_still_answers_405(self):
        for url in ("/api/v1/practicas/", "/api/v1/practicas/1/"):
            response = self.client.patch(url, HTTP_X_ROL="estudiante")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response.headers["Allow"], "GET")

    def test_cookie_overflow_answers_500_error_interno_without_a_cookie(self):
        with patch("apps.prototipo.validaciones.LIMITE_COOKIE", 10):
            response = self.patch_json({"decision": "aprobado"})
        self.assertRejected(response, 500, "error_interno")

    # T2 / T1 integration: the screens share the cookie overlay with the API.

    def revisar(self, clave=None):
        return reverse("prototipo:revisar", args=[clave or self.clave])

    def test_an_api_decision_shows_in_t2_without_the_decision_form(self):
        self.patch_json({"decision": "aprobado"})
        response = self.client.get(self.revisar())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Validado")
        self.assertContains(response, TUTOR_ACADEMICO)
        self.assertNotContains(response, 'value="devolver"')

    def test_an_api_return_shows_its_observation_in_t2(self):
        self.patch_json({"decision": "devuelto", "observacion": "Falta firma"})
        response = self.client.get(self.revisar())
        self.assertContains(response, "Devuelto con observación")
        self.assertContains(response, "Falta firma")

    def test_a_t2_decision_makes_the_api_answer_409(self):
        self.client.post(self.revisar(), {"accion": "validar"})
        response = self.patch_json({"decision": "aprobado"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "transicion_invalida")

    def test_t2_renders_the_json_result_below_the_form(self):
        response = self.client.post(self.revisar(), {"accion": "validar"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<pre")
        self.assertContains(response, "&quot;estado&quot;: &quot;validado&quot;")
        self.assertContains(response, "&quot;clave&quot;: &quot;reporte-1-8&quot;")
        self.assertIn(self.COOKIE, response.cookies)

    def test_t2_return_renders_the_observation_in_the_json(self):
        response = self.client.post(
            self.revisar(), {"accion": "devolver", "observacion": "Adjunte la firma."}
        )
        self.assertContains(response, "&quot;estado&quot;: &quot;devuelto&quot;")
        self.assertContains(response, "&quot;observacion&quot;: &quot;Adjunte la firma.&quot;")

    def test_t2_renders_the_error_body_when_the_decision_was_already_made(self):
        self.patch_json({"decision": "aprobado"})
        response = self.client.post(self.revisar(), {"accion": "devolver", "observacion": "Otra"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "notice--warn")
        self.assertContains(response, "&quot;code&quot;: &quot;transicion_invalida&quot;")
        self.assertNotContains(response, "Devuelto con observación")

    def test_t2_form_errors_render_no_json_and_set_no_cookie(self):
        response = self.client.post(self.revisar(), {"accion": "devolver", "observacion": " "})
        self.assertContains(response, "Escriba una observación")
        self.assertNotContains(response, "<pre")
        self.assertNotIn(self.COOKIE, response.cookies)

    def test_t2_still_answers_404_for_closed_or_foreign_keys(self):
        self.patch_json({"decision": "aprobado"}, clave="reporte-2-9")
        for clave in ("reporte-1-3", "reporte-2-9", "informe-99"):
            with self.subTest(clave=clave):
                self.assertEqual(self.client.get(self.revisar(clave)).status_code, 404)
                response = self.client.post(self.revisar(clave), {"accion": "validar"})
                self.assertEqual(response.status_code, 404)

    def test_t1_hides_the_items_already_decided(self):
        inbox = reverse("prototipo:pendientes_revision")
        self.assertContains(self.client.get(inbox), self.revisar())
        self.patch_json({"decision": "aprobado"})
        response = self.client.get(inbox)
        self.assertNotContains(response, self.revisar())
        self.assertContains(response, self.revisar("plan-4"))

    def test_t1_hides_items_decided_in_t2_too(self):
        self.client.post(self.revisar("plan-4"), {"accion": "validar"})
        response = self.client.get(reverse("prototipo:pendientes_revision"))
        self.assertNotContains(response, self.revisar("plan-4"))
        self.assertContains(response, self.revisar())

    def test_t2_overflow_keeps_the_item_pending_and_shows_the_500_body(self):
        with patch("apps.prototipo.validaciones.LIMITE_COOKIE", 10):
            response = self.client.post(self.revisar(), {"accion": "validar"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&quot;code&quot;: &quot;error_interno&quot;")
        self.assertContains(response, 'value="validar"')
        self.assertNotContains(response, "notice--ok")
        self.assertNotIn(self.COOKIE, response.cookies)
