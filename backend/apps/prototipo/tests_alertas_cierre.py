"""Public contract and browser integration of issue #61 (test-first)."""
import copy
import time
from datetime import date, timedelta
from unittest.mock import patch

from django.core import signing
from django.test import Client, SimpleTestCase, TestCase, override_settings

from . import coordinador, facade, sample_data as data

ALERTAS = "/api/v1/alertas/"
C2 = "/prototipo/coordinador/alertas/"
COOKIE = "prototipo_coordinador_v2"


def cierre(practica_id=7):
    return f"/api/v1/practicas/{practica_id}/cierre/"


def detalle(practica_id=7):
    return f"/prototipo/coordinador/practicas/{practica_id}/"


@override_settings(DEBUG=True)
class AlertasCierreTests(SimpleTestCase):
    def alertas(self, rol="coordinador", **params):
        return self.client.get(ALERTAS, params, HTTP_X_ROL=rol)

    def cerrar(self, practica_id=7, rol="coordinador"):
        return self.client.post(cierre(practica_id), HTTP_X_ROL=rol)

    def test_alert_dto_has_no_recursive_domain_data_and_count_precedes_filter(self):
        response = self.alertas()
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], len(payload["alertas"]))
        self.assertGreater(payload["count"], 0)
        self.assertEqual({a["tipo"] for a in payload["alertas"]}, set(data.TIPOS_ALERTA))
        ordering = [(a["fecha"], a["practica"]["id"]) for a in payload["alertas"]]
        self.assertEqual(ordering, sorted(ordering, reverse=True))
        for alerta in payload["alertas"]:
            date.fromisoformat(alerta["fecha"])
            self.assertEqual(set(alerta), {"tipo", "tipo_display", "estado_badge", "detalle", "fecha", "practica"})
            self.assertNotIn("reportes", alerta["practica"])
            self.assertNotIn("alertas", alerta["practica"])
            self.assertEqual(alerta["practica"]["carrera"], data.CARRERA)
        for tipo in data.TIPOS_ALERTA:
            filtered = self.alertas(tipo=tipo).json()
            self.assertEqual(filtered["count"], payload["count"])
            self.assertTrue(filtered["alertas"])
            self.assertTrue(all(a["tipo"] == tipo for a in filtered["alertas"]))
        self.assertEqual(self.alertas(tipo="inexistente").json()["alertas"], [])

    def test_alert_recipients_and_career_isolation(self):
        scopes = {"estudiante": {1, 2}, "tutor_academico": {1, 3, 4, 5, 6}}
        for rol, scope in scopes.items():
            payload = self.alertas(rol).json()
            self.assertTrue(payload["alertas"])
            self.assertTrue(all(a["practica"]["id"] in scope for a in payload["alertas"]))
            if rol == "estudiante":
                self.assertLessEqual({a["tipo"] for a in payload["alertas"]}, {"reporte_no_enviado", "rezago"})
        self.assertEqual(self.alertas("tutor_entidad").json(), {"count": 0, "alertas": []})
        self.assertTrue(any(a["practica"]["id"] >= 100 for a in self.alertas().json()["alertas"]))
        self.assertEqual(self.cerrar(1000).status_code, 403)
        self.assertEqual(self.cerrar(99999).status_code, 404)

    def test_protocol_methods_roles_and_debug(self):
        for url, allowed in ((ALERTAS, "GET"), (cierre(), "POST")):
            for method in ("get", "post", "patch", "put", "delete", "head", "options"):
                if method.upper() == allowed:
                    continue
                response = getattr(self.client, method)(url, HTTP_X_ROL="coordinador")
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response["Allow"], allowed)
            for role in (None, "desconocido"):
                headers = {"X-Rol": role} if role else {}
                response = getattr(self.client, allowed.lower())(url, headers=headers)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["error"]["code"], "sin_sesion")
            with override_settings(DEBUG=False):
                self.assertEqual(getattr(self.client, allowed.lower())(url, HTTP_X_ROL="coordinador").status_code, 404)
        for rol in ("estudiante", "tutor_academico", "tutor_entidad"):
            self.assertEqual(self.cerrar(rol=rol).status_code, 403)
        self.assertNotIn(COOKIE, self.client.cookies)

    def test_success_is_visible_in_api_history_screen_and_consolidated(self):
        before = self.client.get(detalle()).context["practica"]["historial"]
        response = self.cerrar()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "cerrada")
        self.assertEqual(response.json()["resultado"], "aprobada")
        self.assertEqual(response.cookies[COOKIE]["path"], "/")
        self.assertEqual(response.cookies[COOKIE]["max-age"], 86400)
        self.assertTrue(response.cookies[COOKIE]["httponly"])
        practice = self.client.get(detalle()).context["practica"]
        self.assertEqual(len(practice["historial"]), len(before) + 1)
        self.assertEqual(practice["historial"][-1]["autor"], data.COORDINADOR)
        self.assertEqual(self.client.get("/api/v1/practicas/7/", HTTP_X_ROL="coordinador").json()["estado"], "cerrada")
        self.assertContains(self.client.get("/prototipo/coordinador/consolidado/"), practice["estudiante"])
        repeated = self.cerrar()
        self.assertEqual(repeated.status_code, 409)
        self.assertEqual(repeated.json()["error"]["faltante"], [])
        self.assertEqual(self.client.get(detalle()).context["practica"]["historial"], practice["historial"])
        self.assertEqual(Client().get(detalle()).context["practica"]["estado"], "en_revision_final")

    def test_each_missing_requirement_rejects_without_cookie_or_history_changes(self):
        for key in ("horas", "informe_final", "informe_externo", "evaluacion"):
            practices = data.practicas_todas()
            practice = next(p for p in practices if p["id"] == 7)
            if key == "horas":
                practice["reportes"][-1]["estado"] = "en_revision"
            else:
                practice[key] = None
            before = copy.deepcopy(practice["historial"])
            with patch.object(data, "practicas_todas", side_effect=lambda: copy.deepcopy(practices)):
                response = self.cerrar()
            self.assertEqual(response.status_code, 409, key)
            error = response.json()["error"]
            self.assertEqual(error["code"], "transicion_invalida")
            self.assertEqual(error["recurso"], cierre())
            self.assertEqual(len(error["faltante"]), 1)
            self.assertNotIn(COOKIE, response.cookies)
            self.assertEqual(practice["historial"], before)
        response = self.cerrar(6)
        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.json()["error"]["faltante"])
        for practica_id in (1, 8):
            self.assertEqual(self.cerrar(practica_id).status_code, 409)

    def test_close_preserves_69_and_70_percent_and_community_project_report(self):
        for percent, result in ((69, "no_aprobada"), (70, "aprobada")):
            practices = data.practicas_todas()
            practice = next(p for p in practices if p["id"] == 7)
            practice["tipo"] = "comunitaria"
            practice["tutor_entidad"] = ""
            practice["evaluacion"].update(porcentaje=percent, resultado=result, resultado_display=data.RESULTADO_PRACTICA[result])
            self.client = Client()
            with patch.object(data, "practicas_todas", side_effect=lambda: copy.deepcopy(practices)):
                response = self.cerrar()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["resultado"], result)
            self.assertEqual(response.json()["estado"], "cerrada")

    def test_html_fallback_and_api_use_the_same_close_service(self):
        url = "/prototipo/coordinador/practicas/7/cerrar/"
        self.assertContains(self.client.get(url), "data-cierre-api")
        self.assertEqual(self.client.post(url, {"confirmar": "on"}).status_code, 302)
        self.assertEqual(self.cerrar().status_code, 409)
        self.assertEqual(self.client.get("/api/v1/practicas/7/", HTTP_X_ROL="coordinador").json()["estado"], "cerrada")
        c2 = self.client.get(C2)
        self.assertContains(c2, "data-alertas-lista")
        self.assertContains(c2, "data-alertas-count")
        self.assertEqual(len(c2.context["alertas"]), self.alertas().json()["count"])
        self.assertContains(Client().post("/prototipo/coordinador/practicas/6/cerrar/", {"confirmar": "on"}), "No se puede cerrar")

    def test_close_csrf_required_and_valid_token_works(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(cierre(), HTTP_X_ROL="coordinador").status_code, 403)
        self.assertNotIn(COOKIE, client.cookies)
        client.get("/prototipo/coordinador/practicas/7/cerrar/")
        response = client.post(cierre(), HTTP_X_ROL="coordinador", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 200)

    def test_cookie_legacy_migration_expiry_tampering_reset_and_limit(self):
        state = {"cambios": {}, "configuracion": {"umbral_rezago": 90}}
        self.client.cookies["prototipo_coordinador"] = signing.dumps(state, salt=coordinador.SALT, compress=True)
        migrated = self.client.get(C2)
        self.assertIn(COOKIE, migrated.cookies)
        self.assertEqual(migrated.cookies[COOKIE]["path"], "/")
        self.assertEqual(self.client.get(detalle(1)).context["practica"]["umbral_rezago"], 90)
        reset = self.client.post("/prototipo/coordinador/restablecer/")
        self.assertEqual(reset.cookies[COOKIE]["max-age"], 0)
        self.assertEqual(reset.cookies["prototipo_coordinador"]["max-age"], 0)
        self.assertEqual(reset.cookies["prototipo_coordinador"]["path"], "/prototipo/")
        self.client = Client()
        self.assertEqual(self.cerrar().status_code, 200)
        cookie = self.client.cookies[COOKIE].value
        for value in (cookie + "forjada",):
            self.client.cookies[COOKIE] = value
            self.assertEqual(self.client.get(detalle()).context["practica"]["estado"], "en_revision_final")
        self.client.cookies[COOKIE] = cookie
        with patch("django.core.signing.time.time", return_value=time.time() + 90000):
            self.assertEqual(self.client.get(detalle()).context["practica"]["estado"], "en_revision_final")
        self.client = Client()
        with patch.object(coordinador, "LIMITE_COOKIE", 1):
            response = self.cerrar()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "error_interno")
        self.assertNotIn(COOKIE, response.cookies)
        self.assertEqual(self.client.get(detalle()).context["practica"]["estado"], "en_revision_final")
        with patch.object(coordinador, "LIMITE_COOKIE", 1):
            response = self.client.post("/prototipo/coordinador/configuracion/", data.CONFIGURACION_CARRERA)
        self.assertContains(response, "La demostración alcanzó su límite")
        self.assertNotContains(response, "Configuración guardada")
        self.assertNotIn(COOKIE, response.cookies)

    def test_deadline_boundaries_and_inactive_practices(self):
        practice = data._pasantia_lista_para_cerrar()
        practice["estado"] = "en_curso"
        practice["reportes"] = [data._reporte(1, 0, "sin_reporte")]
        data._avance(practice, practice["reportes"])
        deadline = practice["reportes"][0]["hasta"] + timedelta(days=3)
        with patch.object(data, "HOY", deadline):
            self.assertFalse(any(a["tipo"] == "reporte_no_enviado" for a in data.alertas_de(practice)))
        with patch.object(data, "HOY", deadline + timedelta(days=1)):
            self.assertTrue(any(a["tipo"] == "reporte_no_enviado" for a in data.alertas_de(practice)))
        report = data._reporte(1, 10, "en_revision", enviado_el=date(2026, 5, 29))
        practice["reportes"] = [report]
        with patch.object(data, "HOY", date(2026, 6, 5)):
            self.assertFalse(any(a["tipo"] == "revision_pendiente" for a in data.alertas_de(practice)))
        with patch.object(data, "HOY", date(2026, 6, 8)):
            self.assertTrue(any(a["tipo"] == "revision_pendiente" for a in data.alertas_de(practice)))
        for state in ("suspendida", "cancelada", "cerrada"):
            practice["estado"] = state
            self.assertEqual(data.alertas_de(practice), [])

    def test_configuration_and_tutor_decisions_reach_alerts_and_hours(self):
        before = self.alertas("tutor_academico").json()
        response = self.client.patch("/api/v1/pendientes/reporte-3-7/", '{"decision":"aprobado"}', content_type="application/json", HTTP_X_ROL="tutor_academico")
        self.assertEqual(response.status_code, 200)
        after = self.alertas("tutor_academico").json()
        self.assertLess(after["count"], before["count"])
        practice = self.client.get("/api/v1/practicas/3/", HTTP_X_ROL="tutor_academico").json()
        self.assertEqual(next(r for r in practice["reportes"] if r["semana"] == 7)["estado"], "validado")
        self.assertEqual(self.client.get(detalle(3)).context["practica"]["horas_validadas"], practice["horas_validadas"])
        config = {**data.CONFIGURACION_CARRERA, "umbral_rezago": 1, "plazo_revision_dias": 100, "plazo_reporte_dias": 100}
        self.client.post("/prototipo/coordinador/configuracion/", config)
        remaining = self.alertas().json()["alertas"]
        self.assertFalse(any(a["tipo"] in {"reporte_no_enviado", "revision_pendiente", "rezago"} for a in remaining))

    def test_lag_exact_threshold_and_configurable_threshold(self):
        practice = data._pasantia_lista_para_cerrar()
        practice["estado"] = "en_curso"
        practice["semana_actual"] = 8
        practice["reportes"] = [data._validado(week, 8) for week in range(1, 9)]
        with patch.object(data, "practicas_todas", side_effect=lambda: [copy.deepcopy(practice)]):
            self.assertEqual(facade.alertas_de("coordinador")["count"], 0)  # 64 / 80 expected = 80 %
            state = {"configuracion": {"umbral_rezago": 90}}
            self.assertEqual(facade.alertas_de("coordinador", estado=state)["count"], 1)
            practice["reportes"][-1]["horas"] = 7
            self.assertEqual(facade.alertas_de("coordinador")["alertas"][0]["tipo"], "rezago")

    def test_final_report_validation_unlocks_close_in_the_same_browser(self):
        practice = data._pasantia_lista_para_cerrar()
        practice["tutor_academico"] = data.TUTOR_ACADEMICO
        practice["informe_final"]["estado"] = "en_revision"
        with patch.object(data, "_practicas", side_effect=lambda: [copy.deepcopy(practice)]):
            self.assertEqual(self.cerrar().status_code, 409)
            response = self.client.patch("/api/v1/pendientes/informe-7/", '{"decision":"aprobado"}', content_type="application/json", HTTP_X_ROL="tutor_academico")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.cerrar().status_code, 200)

    def test_suspension_and_forged_cookie_do_not_leak_or_keep_active_alerts(self):
        self.assertTrue(any(a["practica"]["id"] == 1 for a in self.alertas().json()["alertas"]))
        self.client.post("/prototipo/coordinador/practicas/1/suspender/", {"motivo": "Licencia"})
        self.assertFalse(any(a["practica"]["id"] == 1 for a in self.alertas().json()["alertas"]))
        self.assertEqual(self.cerrar(1).status_code, 409)
        self.client.cookies[COOKIE] = "forjada"
        self.assertTrue(any(a["practica"]["id"] == 1 for a in self.alertas().json()["alertas"]))


@override_settings(DEBUG=True)
class AlertasSessionTests(TestCase):
    def test_report_from_session_updates_coordinator_api_and_screen(self):
        from .tests_reportes import reporte

        before = self.client.get(detalle(1)).context["practica"]
        self.assertEqual(self.client.post("/api/v1/practicas/1/reportes/", reporte(), HTTP_X_ROL="estudiante").status_code, 201)
        practice = self.client.get(detalle(1)).context["practica"]
        self.assertEqual(practice["horas_en_revision"], before["horas_en_revision"] + 10)
        api = self.client.get("/api/v1/practicas/1/", HTTP_X_ROL="coordinador").json()
        self.assertEqual(api["horas_en_revision"], practice["horas_en_revision"])
        self.assertEqual(Client().get(detalle(1)).context["practica"]["horas_en_revision"], before["horas_en_revision"])
