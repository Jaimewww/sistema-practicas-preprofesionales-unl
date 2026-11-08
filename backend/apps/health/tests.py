from unittest import mock

from django.db import OperationalError
from django.test import Client, TestCase


class HealthEndpointTests(TestCase):
    """The /health/ endpoint reports 200 when the database answers, 503 otherwise."""

    def setUp(self):
        self.client = Client()

    def test_health_returns_ok(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "checks": {"database": "ok"}})

    def test_health_answers_json(self):
        response = self.client.get("/health/")
        self.assertEqual(response["Content-Type"].split(";")[0], "application/json")

    def test_health_returns_503_when_database_is_down(self):
        with mock.patch(
            "django.db.connection.ensure_connection",
            side_effect=OperationalError("connection to server at 10.0.0.5 refused"),
        ):
            with self.assertLogs("apps.health", level="WARNING"):
                response = self.client.get("/health/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(), {"status": "error", "checks": {"database": "unavailable"}}
        )

    def test_503_body_does_not_leak_error_details(self):
        with mock.patch(
            "django.db.connection.ensure_connection",
            side_effect=OperationalError("connection to server at 10.0.0.5 refused"),
        ):
            with self.assertLogs("apps.health", level="WARNING"):
                response = self.client.get("/health/")
        self.assertNotIn("10.0.0.5", response.content.decode())

    def test_503_still_carries_request_id(self):
        with mock.patch(
            "django.db.connection.ensure_connection", side_effect=OperationalError("down")
        ):
            with self.assertLogs("apps.health", level="WARNING"):
                response = self.client.get("/health/")
        self.assertTrue(response["X-Request-ID"])
