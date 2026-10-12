from django.http import JsonResponse


def health(request):
    """Liveness check: answers 200 with a JSON payload."""
    return JsonResponse({"status": "ok"})
