"""Read-only demo HTTP adapter. X-Rol selects synthetic data, never identity."""

from functools import wraps

from django.http import JsonResponse

from . import facade
from .views import solo_en_debug


def json_error(status, code, message, **extra):
    return JsonResponse({"error": {"code": code, "message": message, **extra}}, status=status)


def consulta_demo(view):
    @wraps(view)
    @solo_en_debug
    def wrapper(request, *args, **kwargs):
        if request.method != "GET":
            response = json_error(405, "metodo_no_permitido", "Solo se permite GET.")
            response["Allow"] = "GET"
            return response
        rol = request.headers.get("X-Rol")
        if rol not in facade.ROLES:
            return json_error(401, "sin_sesion", "Seleccione una persona sintética con X-Rol.")
        try:
            return view(request, rol, *args, **kwargs)
        except facade.PracticeQueryError as error:
            return json_error(error.status, error.code, str(error))

    return wrapper


@consulta_demo
def lista_practicas(request, rol):
    return JsonResponse({"practicas": facade.practicas_de(rol)})


@consulta_demo
def detalle_practica(request, rol, practica_id):
    return JsonResponse(facade.practica_de_id(practica_id, rol))
