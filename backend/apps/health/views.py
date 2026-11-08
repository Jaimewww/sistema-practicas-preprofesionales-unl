import logging

from django.db import Error, connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health(request):
    """Readiness check: 200 when the database answers, 503 otherwise."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Error:
        logger.warning("Health check: database unavailable", exc_info=True)
        return JsonResponse(
            {"status": "error", "checks": {"database": "unavailable"}}, status=503
        )
    return JsonResponse({"status": "ok", "checks": {"database": "ok"}})
