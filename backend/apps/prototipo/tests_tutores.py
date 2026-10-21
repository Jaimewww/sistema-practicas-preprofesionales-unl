from decimal import Decimal

from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from .forms import (
    EvaluacionFinalForm,
    RevisionForm,
    resultado_evaluacion,
)
from .sample_data import (
    TUTOR_ACADEMICO,
    pendientes_de_revision,
    practicas_del_tutor,
)

FECHA_HOY = "05/06/2026"  # sample_data.HOY


def revisar_url(clave):
    return reverse("prototipo:revisar", args=[clave])


def practica_url(name, practica_id, *args):
    return reverse(f"prototipo:{name}", args=[practica_id, *args])


# --- Tutor académico ---------------------------------------------------------


@override_settings(DEBUG=True)
class PendientesRevisionPageTests(SimpleTestCase):
    """T1: a single inbox with plans, weekly reports and final reports."""

    url = "/prototipo/tutor/pendientes/"

    def setUp(self):
        self.client = Client()

    def test_lists_the_three_types_with_date_wait_and_deadline_mark(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pendientes de revisión")
        for label in ("Plan de actividades", "Reporte semanal", "Informe final"):
            self.assertContains(response, label)
        self.assertContains(response, "Fecha de envío")
        self.assertContains(response, "Días hábiles de espera")
        self.assertContains(response, "Fuera de plazo")
        self.assertContains(response, revisar_url("reporte-1-8"))

    def test_inbox_only_has_items_in_review_of_practices_the_tutor_tutors(self):
        items = pendientes_de_revision()
        self.assertTrue(items)
        for item in items:
            self.assertEqual(item["practica"]["tutor_academico"], TUTOR_ACADEMICO)
            self.assertEqual(item["estado"], "en_revision")
        claves = {item["clave"] for item in items}
        # Week 9 of the comunitaria is in review, but its tutor is someone else.
        self.assertNotIn("reporte-2-9", claves)
        response = self.client.get(self.url)
        self.assertNotContains(response, "Junta Parroquial de San Lucas")
        self.assertNotContains(response, revisar_url("reporte-2-9"))

    def test_marks_out_of_deadline_after_five_business_days(self):
        items = {item["clave"]: item for item in pendientes_de_revision()}
        self.assertTrue(items["reporte-3-7"]["fuera_de_plazo"])
        self.assertFalse(items["reporte-1-8"]["fuera_de_plazo"])
        self.assertEqual(items["plan-4"]["dias_espera"], 5)
        self.assertFalse(items["plan-4"]["fuera_de_plazo"])

    def test_oldest_item_comes_first(self):
        fechas = [item["enviado_el"] for item in pendientes_de_revision()]
        self.assertEqual(fechas, sorted(fechas))

    def test_empty_state_has_a_message(self):
        response = self.client.get(self.url, {"vacio": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tiene pendientes de revisión.")
        self.assertNotContains(response, "<table")

    def test_menu_shows_the_tutor_sections(self):
        response = self.client.get(self.url)
        self.assertContains(response, reverse("prototipo:mis_tutorados"))
        self.assertContains(response, "Mis tutorados")
        self.assertNotContains(response, "Mis prácticas")


@override_settings(DEBUG=True)
class RevisarPageTests(SimpleTestCase):
    """T2: the same review screen for plans, reports and final reports."""

    def setUp(self):
        self.client = Client()
        self.url = revisar_url("reporte-1-8")

    def test_report_shows_its_content_and_both_actions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semana 8")
        self.assertContains(response, "En revisión")
        self.assertContains(response, "Actividades")
        self.assertContains(response, "Evidencias")
        self.assertContains(response, 'value="validar"')
        self.assertContains(response, 'value="devolver"')
        self.assertContains(response, "Observación")

    def test_same_screen_serves_plan_and_final_report(self):
        plan = self.client.get(revisar_url("plan-4"))
        self.assertEqual(plan.status_code, 200)
        self.assertContains(plan, "Plan de actividades")
        informe = self.client.get(revisar_url("informe-6"))
        self.assertEqual(informe.status_code, 200)
        self.assertContains(informe, "Informe final")
        for response in (plan, informe):
            self.assertContains(response, 'value="validar"')
            self.assertContains(response, 'value="devolver"')

    def test_validar_records_who_and_when(self):
        response = self.client.post(self.url, {"accion": "validar"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Validado")
        self.assertContains(response, TUTOR_ACADEMICO)
        self.assertContains(response, FECHA_HOY)
        self.assertNotContains(response, 'value="devolver"')

    def test_devolver_without_observacion_is_rejected(self):
        response = self.client.post(self.url, {"accion": "devolver", "observacion": "  "})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Escriba una observación")
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, "En revisión")
        self.assertNotContains(response, "Devuelto con observación")

    def test_devolver_with_observacion_returns_it_to_the_student(self):
        observacion = "Adjunte la lista de asistencia firmada."
        response = self.client.post(
            self.url, {"accion": "devolver", "observacion": observacion}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Devuelto con observación")
        self.assertContains(response, observacion)
        self.assertContains(response, TUTOR_ACADEMICO)
        self.assertContains(response, FECHA_HOY)

    def test_errores_param_renders_the_error_state(self):
        response = self.client.get(self.url, {"errores": "1"})
        self.assertContains(response, "Escriba una observación")

    def test_items_outside_the_inbox_answer_404(self):
        # Another tutor's report, an already validated one and a made-up key.
        for clave in ("reporte-2-9", "reporte-1-3", "informe-99", "otra-cosa"):
            self.assertEqual(self.client.get(revisar_url(clave)).status_code, 404)
        response = self.client.post(revisar_url("reporte-2-9"), {"accion": "validar"})
        self.assertEqual(response.status_code, 404)

    def test_delete_is_not_allowed(self):
        self.assertEqual(self.client.delete(self.url).status_code, 405)


class RevisionFormTests(SimpleTestCase):
    def test_validar_needs_no_observacion(self):
        self.assertTrue(RevisionForm({"accion": "validar"}).is_valid())

    def test_devolver_requires_observacion_citing_rf_03_rule(self):
        form = RevisionForm({"accion": "devolver", "observacion": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("observacion", form.errors)

    def test_devolver_with_observacion_is_valid(self):
        form = RevisionForm({"accion": "devolver", "observacion": "Falta la evidencia."})
        self.assertTrue(form.is_valid())

    def test_unknown_action_is_rejected(self):
        self.assertFalse(RevisionForm({"accion": "borrar"}).is_valid())


@override_settings(DEBUG=True)
class MisTutoradosPageTests(SimpleTestCase):
    """T3: practices tutored by the academic tutor, with state and hours."""

    url = "/prototipo/tutor/tutorados/"

    def setUp(self):
        self.client = Client()

    def test_lists_tutored_practices_with_state_and_hours(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mis tutorados")
        for practica in practicas_del_tutor():
            self.assertContains(response, practica["estudiante"])
            self.assertContains(response, practica_url("practica_tutor", practica["id"]))
        for label in ("En curso", "Asignada", "En revisión final", "Horas validadas"):
            self.assertContains(response, label)
        self.assertNotContains(response, "Junta Parroquial de San Lucas")

    def test_each_practice_has_a_single_active_academic_tutor(self):
        practicas = practicas_del_tutor()
        self.assertTrue(practicas)
        for practica in practicas:
            self.assertEqual(practica["tutor_academico"], TUTOR_ACADEMICO)

    def test_empty_state_has_a_message(self):
        response = self.client.get(self.url, {"vacio": "1"})
        self.assertContains(response, "No tiene prácticas asignadas como tutor académico.")


@override_settings(DEBUG=True)
class PracticaTutorPageTests(SimpleTestCase):
    """T4: practice detail shared with the coordinator, without closing actions."""

    def setUp(self):
        self.client = Client()
        self.url = practica_url("practica_tutor", 1)

    def test_detail_with_tabs_and_no_closing_actions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Datos de la práctica")
        self.assertContains(response, "Horas validadas")
        for label in ("Resumen", "Plan", "Reportes semanales", "Informe final"):
            self.assertContains(response, label)
        # The shell's "Cerrar el menú" button is fine; the C3 actions are not.
        for action in ("Cerrar práctica", "Suspender", "Reanudar", "Cancelar", "Historial"):
            self.assertNotContains(response, action)
        self.assertContains(response, practica_url("evaluacion_final", 1))

    def test_reportes_tab_links_the_report_in_review_to_t2(self):
        response = self.client.get(self.url, {"tab": "reportes"})
        self.assertContains(response, revisar_url("reporte-1-8"))
        self.assertContains(response, "Confirmado por la entidad")

    def test_practice_of_another_tutor_answers_404(self):
        self.assertEqual(self.client.get(practica_url("practica_tutor", 2)).status_code, 404)
        self.assertEqual(
            self.client.get(practica_url("practica_tutor", 999)).status_code, 404
        )


@override_settings(DEBUG=True)
class EvaluacionFinalPageTests(SimpleTestCase):
    """T5: final evaluation in percent; «aprobada» from 70 % (RF-17, Art. 339)."""

    def setUp(self):
        self.client = Client()
        self.url = practica_url("evaluacion_final", 5)

    def test_form_explains_the_rule(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Desempeño:")
        self.assertContains(response, "70 %")
        self.assertContains(response, "Art. 339")

    def test_70_percent_is_aprobada_with_author_and_date(self):
        response = self.client.post(self.url, {"porcentaje": "70"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aprobada")
        self.assertNotContains(response, "No aprobada")
        self.assertContains(response, TUTOR_ACADEMICO)
        self.assertContains(response, FECHA_HOY)

    def test_69_99_percent_is_no_aprobada(self):
        response = self.client.post(self.url, {"porcentaje": "69.99"})
        self.assertContains(response, "No aprobada")

    def test_percentage_out_of_range_is_rejected(self):
        response = self.client.post(self.url, {"porcentaje": "101"})
        self.assertContains(response, "entre 0 y 100")
        self.assertContains(response, 'aria-invalid="true"')

    def test_missing_external_report_blocks_the_evaluation(self):
        response = self.client.post(practica_url("evaluacion_final", 6), {"porcentaje": "90"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se puede registrar la evaluación final")
        self.assertContains(response, "el informe externo")
        self.assertNotContains(response, "Aprobada")

    def test_practice_of_another_tutor_answers_404(self):
        url = practica_url("evaluacion_final", 2)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {"porcentaje": "90"}).status_code, 404)


class EvaluacionFinalFormTests(SimpleTestCase):
    def test_resultado_follows_the_70_percent_rule(self):
        self.assertEqual(resultado_evaluacion(Decimal("70"))[0], "aprobada")
        self.assertEqual(resultado_evaluacion(Decimal("100"))[0], "aprobada")
        self.assertEqual(resultado_evaluacion(Decimal("69.99"))[0], "no_aprobada")
        self.assertEqual(resultado_evaluacion(Decimal("0"))[0], "no_aprobada")

    def test_accepts_bounds_and_rejects_outside(self):
        self.assertTrue(EvaluacionFinalForm({"porcentaje": "0"}).is_valid())
        self.assertTrue(EvaluacionFinalForm({"porcentaje": "100"}).is_valid())
        self.assertFalse(EvaluacionFinalForm({"porcentaje": "-1"}).is_valid())
        self.assertFalse(EvaluacionFinalForm({"porcentaje": "100.01"}).is_valid())

    def test_rejects_when_a_requirement_is_missing(self):
        form = EvaluacionFinalForm(
            {"porcentaje": "90"}, faltantes=["el informe externo"]
        )
        self.assertFalse(form.is_valid())
        self.assertIn("el informe externo", " ".join(form.non_field_errors()))


class TutorScreensOnlyInDebugTests(SimpleTestCase):
    def test_every_tutor_screen_answers_404_when_debug_is_off(self):
        urls = [
            reverse("prototipo:pendientes_revision"),
            revisar_url("reporte-1-8"),
            reverse("prototipo:mis_tutorados"),
            practica_url("practica_tutor", 1),
            practica_url("evaluacion_final", 5),
        ]
        client = Client()
        with override_settings(DEBUG=False):
            for url in urls:
                self.assertEqual(client.get(url).status_code, 404, url)
