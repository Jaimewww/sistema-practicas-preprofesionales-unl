"""Demo HTTP adapter. X-Rol selects synthetic data, never identity.

Reports a student sends live in that client's session (`facade.SESSION_KEY`);
tutor decisions live in a signed cookie, never in a database table.
"""

from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import facade, validaciones
from .views import envios_de_sesion, solo_en_debug


def json_error(status, code, message, **extra):
    return JsonResponse({"error": {"code": code, "message": message, **extra}}, status=status)


def error_json(request, error):
    """JSON error that keeps only the fields the error carries (e.g. `campos` of a 422)."""
    return json_error(error.status, error.code, str(error), **error.extra)


def error_de_escritura(request, error):
    """Write error that names the resource on a conflict (PATCH and screen T2 use it)."""
    extra = {"recurso": request.path} if error.status == 409 else {}
    return json_error(error.status, error.code, str(error), **extra)


def _demo(metodo, *roles, formatea=error_json, exenta_csrf=False):
    """One method (and optional roles) per demo endpoint; X-Rol selects, never authenticates.

    `exenta_csrf` is opt-in per endpoint: only the endpoints that document a
    `csrf_exempt` demo scope are exempt, so no other write inherits the exemption.
    """

    def decorator(view):
        @wraps(view)
        @solo_en_debug
        def wrapper(request, *args, **kwargs):
            if request.method != metodo:
                response = json_error(
                    405, "metodo_no_permitido", f"Solo se permite {metodo}."
                )
                response["Allow"] = metodo
                return response
            rol = request.headers.get("X-Rol")
            if rol not in facade.ROLES:
                return json_error(401, "sin_sesion", "Seleccione una persona sintética con X-Rol.")
            if roles and rol not in roles:
                return json_error(403, "fuera_de_rol", "La acción no corresponde a tu rol.")
            try:
                return view(request, rol, *args, **kwargs)
            except facade.PracticeQueryError as error:
                return formatea(request, error)

        return csrf_exempt(wrapper) if exenta_csrf else wrapper

    return decorator


consulta_demo = _demo("GET")
reportes_demo = _demo("POST")
decisiones_demo = _demo(
    "PATCH", "tutor_academico", formatea=error_de_escritura, exenta_csrf=True
)


@consulta_demo
def lista_practicas(request, rol):
    return JsonResponse({"practicas": facade.practicas_de(rol, envios_de_sesion(request))})


@consulta_demo
def detalle_practica(request, rol, practica_id):
    return JsonResponse(facade.practica_de_id(practica_id, rol, envios_de_sesion(request)))


@reportes_demo
def reportes_practica(request, rol, practica_id):
    reporte, envios = facade.registrar_reporte(
        practica_id, rol, request.POST, request.FILES, envios_de_sesion(request)
    )
    request.session[facade.SESSION_KEY] = envios
    response = JsonResponse({"reporte": reporte}, status=201)
    response["Location"] = f"/api/v1/practicas/{practica_id}/"
    return response


@decisiones_demo
def decidir_pendiente(request, rol, clave):
    estado = validaciones.leer_estado(request)
    pendiente = validaciones.localizar(clave, estado)
    datos = validaciones.leer_cuerpo(request.body)
    validaciones.registrar(pendiente, estado, datos)
    response = JsonResponse(validaciones.to_pendiente_dto(pendiente))
    if not validaciones.guardar_estado(request, response, estado):
        raise facade.PracticeQueryError(500, "error_interno", "La demostración alcanzó su límite.")
    return response
