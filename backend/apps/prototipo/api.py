"""Demo HTTP adapter. X-Rol selects synthetic data, never identity."""

from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import facade, validaciones
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


def escritura_demo(metodo, *roles):
    """One write method for the given roles. Not CSRF-protected: X-Rol is a demo selector."""

    def decorator(view):
        @wraps(view)
        @csrf_exempt
        @solo_en_debug
        def wrapper(request, *args, **kwargs):
            if request.method != metodo:
                response = json_error(405, "metodo_no_permitido", f"Solo se permite {metodo}.")
                response["Allow"] = metodo
                return response
            rol = request.headers.get("X-Rol")
            if rol not in facade.ROLES:
                return json_error(401, "sin_sesion", "Seleccione una persona sintética con X-Rol.")
            if rol not in roles:
                return json_error(403, "fuera_de_rol", "La acción no corresponde a tu rol.")
            try:
                return view(request, rol, *args, **kwargs)
            except facade.PracticeQueryError as error:
                return error_de_escritura(request, error)

        return wrapper

    return decorator


def error_de_escritura(request, error):
    extra = {"recurso": request.path} if error.status == 409 else {}
    return json_error(error.status, error.code, str(error), **extra)


@escritura_demo("PATCH", "tutor_academico")
def decidir_pendiente(request, rol, clave):
    estado = validaciones.leer_estado(request)
    pendiente = validaciones.localizar(clave, estado)
    datos = validaciones.leer_cuerpo(request.body)
    validaciones.registrar(pendiente, estado, datos)
    response = JsonResponse(validaciones.to_pendiente_dto(pendiente))
    if not validaciones.guardar_estado(request, response, estado):
        raise facade.PracticeQueryError(500, "error_interno", "La demostración alcanzó su límite.")
    return response
