"""Production JSON contract for active alerts (RF-07, C-05)."""

import yaml
from django.test import TestCase, override_settings

from apps.alertas.models import Alerta
from tests.unit.test_consulta_alertas import ConsultaAlertasFixturesMixin

URL = "/api/v1/alertas/"
PASSWORD = "test-alerts-password"


class AlertasApiTests(ConsultaAlertasFixturesMixin, TestCase):
    def _get_as(self, usuario):
        usuario.set_password(PASSWORD)
        usuario.save(update_fields=["password"])
        sesion = self.client.post(
            "/api/v1/auth/token/",
            {"username": usuario.username, "password": PASSWORD},
            content_type="application/json",
        )
        self.assertEqual(sesion.status_code, 200)
        token = sesion.json()["data"]["access"]
        return self.client.get(URL, HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_requires_jwt_even_with_demo_role_header(self):
        respuesta = self.client.get(URL, HTTP_X_ROL="tutor_academico")
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(
            respuesta.headers["Content-Type"], "application/json; charset=utf-8"
        )
        self.assertFalse(respuesta.json()["success"])
        self.assertIsNone(respuesta.json()["data"])

    def test_student_gets_only_active_alerts_for_their_practice_and_role(self):
        Alerta.objects.filter(pk=self.alerta_rezago.pk).update(atendida=True)
        estado = list(Alerta.objects.order_by("pk").values())
        respuesta = self._get_as(self.estudiante)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.json()["data"],
            [
                {
                    "id": self.alerta_reporte.pk,
                    "tipo": self.alerta_reporte.tipo,
                    "practica_id": self.practica.pk,
                    "fecha": self.alerta_reporte.fecha.isoformat(),
                }
            ],
        )
        self.assertEqual(list(Alerta.objects.order_by("pk").values()), estado)

    def test_authenticated_role_without_alerts_gets_empty_list(self):
        respuesta = self._get_as(self.director)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["data"], [])

    @override_settings(DEBUG=True)
    def test_schema_declares_list_and_jwt(self):
        respuesta = self.client.get("/api/v1/schema/")
        self.assertEqual(respuesta.status_code, 200)
        schema = yaml.safe_load(respuesta.content)
        rutas = schema["paths"][URL]
        self.assertEqual(set(rutas), {"get"})
        operacion = rutas["get"]
        self.assertEqual(operacion["security"], [{"jwtAuth": []}])
        self.assertEqual(set(operacion["responses"]), {"200", "401"})
