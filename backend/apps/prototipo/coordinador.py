"""Prototype state, isolated per browser; no database or production permissions.

Only coordinator decisions/configuration are kept in a signed, expiring cookie.
Sample data is rebuilt for every request. The original history is never edited.
"""
from datetime import date
from functools import wraps

from django.core import signing
from django.http import Http404

from . import sample_data as data

COOKIE_ANTERIOR = "prototipo_coordinador"
COOKIE = "prototipo_coordinador_v2"
SALT = "prototipo.coordinador.v1"
LIMITE_COOKIE = 3500

TRANSICIONES = {
    "suspender": ({"en_curso"}, "suspendida", "Suspender práctica"),
    "reanudar": ({"suspendida"}, "en_curso", "Reanudar práctica"),
    "cancelar": ({"suspendida"}, "cancelada", "Cancelar práctica"),
    "cerrar": ({"en_revision_final"}, "cerrada", "Cerrar práctica"),
}


def leer_estado(request):
    try:
        value = request.COOKIES.get(COOKIE, request.COOKIES.get(COOKIE_ANTERIOR, ""))
        return signing.loads(value, salt=SALT, max_age=86400)
    except signing.BadSignature:
        return {"cambios": {}, "configuracion": {}}


def firmar_estado(estado):
    value = signing.dumps(estado, salt=SALT, compress=True)
    # Leave room for the cookie attributes; never silently lose a long demo.
    if len(value) > LIMITE_COOKIE:
        from .facade import PracticeQueryError

        raise PracticeQueryError(500, "error_interno", "La demostración alcanzó su límite. Restablezca los datos para continuar.")
    return value


def guardar_estado(request, response, estado):
    response.set_cookie(COOKIE, firmar_estado(estado), max_age=86400, path="/",
                        httponly=True, samesite="Lax", secure=request.is_secure())
    return response


def migrar_cookie(view):
    """A legacy cookie only reaches /prototipo/: migrate it before JS uses /api/."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        if (COOKIE_ANTERIOR in request.COOKIES and COOKIE not in request.COOKIES
                and COOKIE not in response.cookies and response.status_code == 200):
            return guardar_estado(request, response, leer_estado(request))
        return response
    return wrapper


def configuracion(estado):
    return {**data.CONFIGURACION_CARRERA, **estado.get("configuracion", {})}


def aplicar_estado(practicas, estado):
    config = configuracion(estado)
    for practica in practicas:
        # Other careers keep their own configuration and history.
        if practica["carrera"] != data.CARRERA_COORDINADOR:
            continue
        for cambio in estado.get("cambios", {}).get(str(practica["id"]), []):
            entrada = {**cambio, "fecha": date.fromisoformat(cambio["fecha"])}
            practica["historial"].append(entrada)
            practica["estado"] = entrada["estado_nuevo"]
        for entrada in practica["historial"]:
            for campo in ("estado_anterior", "estado_nuevo"):
                entrada[campo + "_display"] = data.ESTADO_PRACTICA.get(entrada[campo], "")
        practica["estado_display"] = data.ESTADO_PRACTICA[practica["estado"]]
        if practica["estado"] == "cerrada":
            practica["resultado"] = practica["evaluacion"]["resultado"]
            practica["resultado_display"] = data.RESULTADO_PRACTICA[practica["resultado"]]
            practica["estado_display"] += f" ({practica['resultado_display'].lower()})"
        practica["estado_badge"] = data._clave_badge(practica)
        practica["umbral_rezago"] = config["umbral_rezago"]
        practica["horas_minimas"] = round(practica["horas_esperadas"] * config["umbral_rezago"] / 100)
        practica["rezagada"] = practica["horas_validadas"] + practica["horas_en_revision"] < practica["horas_minimas"]
        practica["horas_estado"] = "rezagada" if practica["rezagada"] else "al_dia"
        practica["horas_estado_display"] = "Rezagada" if practica["rezagada"] else "Al día"
        practica["alertas"] = data.alertas_de(practica, config)
    return practicas


def practicas_propias(estado):
    return aplicar_estado(data.practicas_de_la_carrera(), estado)


def practica_propia(practica_id, estado):
    practica = next((p for p in practicas_propias(estado) if p["id"] == practica_id), None)
    if practica:
        return practica
    if any(p["id"] == practica_id for p in data.practicas_de_otras_carreras()):
        return None  # Known record, outside this coordinator's career: 403.
    raise Http404


def registrar_cambio(estado, practica, nuevo, motivo):
    cambios = estado.setdefault("cambios", {}).setdefault(str(practica["id"]), [])
    cambios.append({"estado_anterior": practica["estado"], "estado_nuevo": nuevo,
                    "autor": data.COORDINADOR, "fecha": data.HOY.isoformat(), "motivo": motivo})
