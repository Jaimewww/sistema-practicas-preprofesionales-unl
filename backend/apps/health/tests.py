from django.test import Client, SimpleTestCase


class HealthEndpointTests(SimpleTestCase):
    """The /health/ endpoint must answer 200 OK with a JSON payload."""

    def setUp(self):
        self.client = Client()

    def test_health_returns_ok(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_answers_json(self):
        response = self.client.get("/health/")
        self.assertEqual(response["Content-Type"].split(";")[0], "application/json")
