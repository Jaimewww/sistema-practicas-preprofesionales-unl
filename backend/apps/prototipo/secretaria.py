"""Prototype state for secretary legalization actions, isolated per browser.

No database or production permissions. Legalizations are kept in a signed,
expiring cookie so the demo survives page reloads.
"""
from datetime import date

from django.core import signing
from django.http import HttpResponseForbidden

from . import sample_data as data

COOKIE = "prototipo_secretaria"
SALT = "prototipo.secretaria.v1"


def leer_estado(request):
    try:
        return signing.loads(request.COOKIES.get(COOKIE, ""), salt=SALT, max_age=86400)
    except signing.BadSignature:
        return {"legalizaciones": {}}


def guardar_estado(request, response, estado):
    value = signing.dumps(estado, salt=SALT, compress=True)
    if len(value) > 3500:
        return HttpResponseForbidden("La demostración alcanzó su límite. Restablezca los datos para continuar.")
    response.set_cookie(COOKIE, value, max_age=86400, path="/prototipo/",
                        httponly=True, samesite="Lax", secure=request.is_secure())
    return response


def aplicar_legalizaciones(practicas, estado):
    """Apply persisted legalizations to the rebuilt sample practices."""
    for practica in practicas:
        if practica["carrera"] != data.CARRERA_COORDINADOR:
            continue
        for anexo in practica.get("anexos", []):
            legalizacion = estado.get("legalizaciones", {}).get(str(anexo["id"]))
            if legalizacion:
                anexo["estado"] = "legalizado"
                anexo["estado_display"] = data.ESTADO_ANEXO["legalizado"]
                anexo["legalizado_por"] = legalizacion["autor"]
                anexo["legalizado_el"] = date.fromisoformat(legalizacion["fecha"])
    return practicas


def legalizar_anexo(estado, anexo_id, autor):
    legalizaciones = estado.setdefault("legalizaciones", {})
    legalizaciones[str(anexo_id)] = {"autor": autor, "fecha": data.HOY.isoformat()}
