"""Demo HTTP adapter. X-Rol selects synthetic data, never identity.

Reports a student sends live in that client's session (`facade.SESSION_KEY`);
tutor decisions, coordinator changes and secretary legalizations live in signed
cookies. Write endpoints update this client's demo state, not shared domain records.
"""

from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import coordinador, facade, secretaria, validaciones
from .views import contexto_demo, solo_en_debug


def json_error(status, code, message, **extra):
    return JsonResponse({"error": {"code": code, "message": message, **extra}}, status=status)


def error_json(request, error):
    """JSON error that keeps only the fields the error carries (e.g. `campos` of a 422)."""
    return json_error(error.status, error.code, str(error), **error.extra)


def error_de_escritura(request, error):
    """Write error that names the resource on a conflict (PATCH, cierre and legalización)."""
    extra = {"recurso": request.path} if error.status == 409 else {}
    return json_error(error.status, error.code, str(error), **error.extra, **extra)


def _demo(metodo, *roles, formatea=error_json, exenta_csrf=False, conocidos=()):
    """One method (and optional roles) per demo endpoint; X-Rol selects, never authenticates.

    `conocidos` lists the demo persons this endpoint knows: a role outside it is 401,
    a known role outside `roles` is 403, so the new director/secretary identities
    answer 403 on their endpoints without opening the older ones.
    `exenta_csrf` is opt-in per endpoint: only the endpoints that document a
    `csrf_exempt` demo scope are exempt, so no other write inherits the exemption.
    """
    personas = tuple(dict.fromkeys(facade.ROLES + conocidos + roles))

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
            if rol not in personas:
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
historial_demo = _demo("GET", *facade.ROLES_HISTORIAL, conocidos=facade.ROLES_DEMO)
legalizaciones_demo = _demo("POST", *facade.ROLES_LEGALIZACION, conocidos=facade.ROLES_DEMO,
                            formatea=error_de_escritura)
decisiones_demo = _demo(
    "PATCH", "tutor_academico", formatea=error_de_escritura, exenta_csrf=True
)


@consulta_demo
def lista_alertas(request, rol):
    return JsonResponse(facade.alertas_de(rol, request.GET.get("tipo", ""), **contexto_demo(request)))


@historial_demo
def historial_practica(request, rol, practica_id):
    """RF-10: read-only history, same projection for the director and the coordinator."""
    return JsonResponse({"historial": facade.historial_de(practica_id, rol, **contexto_demo(request))})


@legalizaciones_demo
def legalizar_anexo(request, rol, anexo_id):
    """RF-04: the Secretary legalizes an annex; the audit author is derived, not sent."""
    anexo, estado = facade.legalizar_anexo(anexo_id, rol, secretaria.leer_estado(request))
    return secretaria.guardar_estado(request, JsonResponse(anexo), estado)


@_demo("POST", "coordinador", formatea=error_de_escritura)
def cierre_practica(request, rol, practica_id):
    practica, estado = facade.cerrar_practica(practica_id, rol, **contexto_demo(request))
    return coordinador.guardar_estado(request, JsonResponse(practica), estado)


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
