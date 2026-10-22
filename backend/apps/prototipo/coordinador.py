"""Prototype state, isolated per browser; no database or production permissions.

Only coordinator decisions/configuration are kept in a signed, expiring cookie.
Sample data is rebuilt for every request. The original history is never edited.
"""
from datetime import date

from django.core import signing
from django.http import Http404, HttpResponseForbidden

from . import sample_data as data

COOKIE = "prototipo_coordinador"
SALT = "prototipo.coordinador.v1"

TRANSICIONES = {
    "suspender": ({"en_curso"}, "suspendida", "Suspender práctica"),
    "reanudar": ({"suspendida"}, "en_curso", "Reanudar práctica"),
    "cancelar": ({"suspendida"}, "cancelada", "Cancelar práctica"),
    "cerrar": ({"en_revision_final"}, "cerrada", "Cerrar práctica"),
}


def leer_estado(request):
    try:
        return signing.loads(request.COOKIES.get(COOKIE, ""), salt=SALT, max_age=86400)
    except signing.BadSignature:
        return {"cambios": {}, "configuracion": {}}


def guardar_estado(request, response, estado):
    value = signing.dumps(estado, salt=SALT, compress=True)
    # Leave room for the cookie attributes; never silently lose a long demo.
    if len(value) > 3500:
        return HttpResponseForbidden("La demostración alcanzó su límite. Restablezca los datos para continuar.")
    response.set_cookie(COOKIE, value, max_age=86400, path="/prototipo/",
                        httponly=True, samesite="Lax", secure=request.is_secure())
    return response


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
