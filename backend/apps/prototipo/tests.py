from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from .forms import ReporteSemanalForm
from .sample_data import SEMANAS_PARA_REPORTAR

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
class ReporteSemanalPageTests(SimpleTestCase):
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
        self.assertIn("Art. 341", " ".join(form.errors["horas"]))

    def test_allows_more_than_10_hours_outside_ayudantia(self):
        self.assertTrue(self.build(ayudantia=False, horas="12").is_valid())

    def test_rejects_non_pdf(self):
        png = SimpleUploadedFile("foto.png", b"\x89PNG\r\n" + b"0" * 100, "image/png")
        form = self.build(evidencia=png)
        self.assertFalse(form.is_valid())
        self.assertIn("PDF", " ".join(form.errors["evidencias"]))

    def test_rejects_pdf_extension_without_pdf_content(self):
        fake = SimpleUploadedFile("falso.pdf", b"not really a pdf", "application/pdf")
        self.assertFalse(self.build(evidencia=fake).is_valid())

    def test_rejects_file_over_5_mb(self):
        form = self.build(evidencia=pdf(size=5 * MB + 1))
        self.assertFalse(form.is_valid())
        self.assertIn("5 MB", " ".join(form.errors["evidencias"]))

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
