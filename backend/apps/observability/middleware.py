import logging
import re
import time
import uuid

from apps.observability.logging import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

logger = logging.getLogger("practicas.request")


class RequestIdMiddleware:
    """Tags each request with an id, echoes it in the response and logs one line per request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming if SAFE_REQUEST_ID.fullmatch(incoming) else uuid.uuid4().hex
        request.request_id = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = self.get_response(request)
            response[REQUEST_ID_HEADER] = request_id
            logger.info(
                "%s %s %s",
                request.method,
                request.path,
                response.status_code,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            return response
        finally:
            request_id_var.reset(token)

    def process_exception(self, request, exception):
        logger.exception(
            "Unhandled exception on %s %s",
            request.method,
            request.path,
            extra={"request_id": request.request_id},
        )
