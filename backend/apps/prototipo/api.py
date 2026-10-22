"""Demo HTTP adapter. X-Rol selects synthetic data, never identity.

Reports a student sends live in that client's session (`facade.SESSION_KEY`);
nothing is shared between clients and nothing is stored in a database table.
"""

from functools import wraps

from django.http import JsonResponse

from . import facade
from .views import envios_de_sesion, solo_en_debug


def json_error(status, code, message, **extra):
    return JsonResponse({"error": {"code": code, "message": message, **extra}}, status=status)


def _demo(method):
    def decorator(view):
        @wraps(view)
        @solo_en_debug
        def wrapper(request, *args, **kwargs):
            if request.method != method:
                response = json_error(
                    405, "metodo_no_permitido", f"Solo se permite {method}."
                )
                response["Allow"] = method
                return response
            rol = request.headers.get("X-Rol")
            if rol not in facade.ROLES:
                return json_error(401, "sin_sesion", "Seleccione una persona sintética con X-Rol.")
            try:
                return view(request, rol, *args, **kwargs)
            except facade.PracticeQueryError as error:
                return json_error(error.status, error.code, str(error), **error.extra)

        return wrapper

    return decorator


consulta_demo = _demo("GET")
escritura_demo = _demo("POST")


@consulta_demo
def lista_practicas(request, rol):
    return JsonResponse({"practicas": facade.practicas_de(rol, envios_de_sesion(request))})


@consulta_demo
def detalle_practica(request, rol, practica_id):
    return JsonResponse(facade.practica_de_id(practica_id, rol, envios_de_sesion(request)))


@escritura_demo
def reportes_practica(request, rol, practica_id):
    reporte, envios = facade.registrar_reporte(
        practica_id, rol, request.POST, request.FILES, envios_de_sesion(request)
    )
    request.session[facade.SESSION_KEY] = envios
    response = JsonResponse({"reporte": reporte}, status=201)
    response["Location"] = f"/api/v1/practicas/{practica_id}/"
    return response
