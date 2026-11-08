import json
import logging
import re

from django.http import HttpResponse
from django.test import Client, SimpleTestCase, override_settings
from django.urls import path

from apps.observability.logging import JsonFormatter, RequestIdFilter, request_id_var

SECRET_MESSAGE = "db password is hunter2"
HEX_ID = re.compile(r"^[0-9a-f]{32}$")


def ok_view(request):
    return HttpResponse("ok")


def boom_view(request):
    raise RuntimeError(SECRET_MESSAGE)


urlpatterns = [
    path("ok/", ok_view),
    path("boom/", boom_view),
]


@override_settings(ROOT_URLCONF=__name__)
class RequestIdMiddlewareTests(SimpleTestCase):
    """Every response carries X-Request-ID and the same id reaches the logs."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)

    def test_header_present_on_200(self):
        response = self.client.get("/ok/")
        self.assertEqual(response.status_code, 200)
        self.assertRegex(response["X-Request-ID"], HEX_ID)

    def test_header_present_on_404(self):
        response = self.client.get("/missing/")
        self.assertEqual(response.status_code, 404)
        self.assertRegex(response["X-Request-ID"], HEX_ID)

    def test_header_present_on_500(self):
        with self.assertLogs("practicas.request", level="ERROR"):
            response = self.client.get("/boom/")
        self.assertEqual(response.status_code, 500)
        self.assertRegex(response["X-Request-ID"], HEX_ID)

    def test_valid_incoming_id_is_echoed(self):
        response = self.client.get("/ok/", headers={"X-Request-ID": "abc-123_X.y"})
        self.assertEqual(response["X-Request-ID"], "abc-123_X.y")

    def test_invalid_incoming_id_is_replaced(self):
        for bad in ["has space", "semi;colon", "<script>", "a" * 65]:
            with self.subTest(bad=bad):
                response = self.client.get("/ok/", headers={"X-Request-ID": bad})
                self.assertNotEqual(response["X-Request-ID"], bad)
                self.assertRegex(response["X-Request-ID"], HEX_ID)

    def test_each_request_without_header_gets_a_distinct_id(self):
        first = self.client.get("/ok/")["X-Request-ID"]
        second = self.client.get("/ok/")["X-Request-ID"]
        self.assertNotEqual(first, second)

    def test_request_id_is_stored_on_the_request(self):
        response = self.client.get("/ok/", headers={"X-Request-ID": "req-1"})
        self.assertEqual(response.wsgi_request.request_id, "req-1")

    def test_request_log_carries_the_same_id(self):
        with self.assertLogs("practicas.request", level="INFO") as captured:
            response = self.client.get("/ok/?token=s3cr3t", headers={"X-Request-ID": "req-2"})
        record = captured.records[-1]
        self.assertEqual(record.request_id, "req-2")
        self.assertEqual(response["X-Request-ID"], record.request_id)
        self.assertEqual(record.method, "GET")
        self.assertEqual(record.path, "/ok/")
        self.assertEqual(record.status, 200)
        self.assertGreaterEqual(record.duration_ms, 0)
        self.assertNotIn("s3cr3t", captured.output[-1])

    def test_unhandled_exception_is_logged_with_request_id(self):
        with self.assertLogs("practicas.request", level="ERROR") as captured:
            self.client.get("/boom/", headers={"X-Request-ID": "req-3"})
        record = captured.records[0]
        self.assertEqual(record.request_id, "req-3")
        self.assertIsNotNone(record.exc_info)

    def test_500_body_does_not_leak_exception_details(self):
        with self.assertLogs("practicas.request", level="ERROR"):
            response = self.client.get("/boom/")
        body = response.content.decode()
        self.assertNotIn(SECRET_MESSAGE, body)
        self.assertNotIn("Traceback", body)
        self.assertNotIn("RuntimeError", body)

    def test_request_id_context_is_cleared_after_the_request(self):
        self.client.get("/ok/", headers={"X-Request-ID": "req-4"})
        self.assertEqual(request_id_var.get(), "-")


class LoggingTests(SimpleTestCase):
    def _record(self, **extra):
        record = logging.LogRecord("practicas.test", logging.INFO, __file__, 1, "hello %s", ("world",), None)
        for key, value in extra.items():
            setattr(record, key, value)
        return record

    def test_filter_injects_request_id_from_context(self):
        token = request_id_var.set("ctx-1")
        try:
            record = self._record()
            RequestIdFilter().filter(record)
        finally:
            request_id_var.reset(token)
        self.assertEqual(record.request_id, "ctx-1")

    def test_filter_uses_dash_outside_a_request(self):
        record = self._record()
        RequestIdFilter().filter(record)
        self.assertEqual(record.request_id, "-")

    def test_json_formatter_outputs_one_valid_json_object(self):
        record = self._record(request_id="req-5", status=200)
        line = JsonFormatter().format(record)
        self.assertNotIn("\n", line)
        data = json.loads(line)
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["logger"], "practicas.test")
        self.assertEqual(data["message"], "hello world")
        self.assertEqual(data["request_id"], "req-5")
        self.assertEqual(data["status"], 200)
        self.assertIn("timestamp", data)

    def test_json_formatter_includes_exception_on_one_line(self):
        try:
            raise ValueError("kaboom")
        except ValueError:
            import sys

            record = self._record()
            record.exc_info = sys.exc_info()
        line = JsonFormatter().format(record)
        self.assertNotIn("\n", line)
        self.assertIn("ValueError", json.loads(line)["exception"])
