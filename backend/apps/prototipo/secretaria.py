"""Prototype state for secretary legalization actions, isolated per browser.

No database or production permissions. Legalizations are kept in a signed,
expiring cookie shared by the API and the S1/S2 screens, so the demo survives
page reloads. The shared sample data is never mutated.
"""
from datetime import date
from functools import wraps

from django.core import signing

from . import sample_data as data

COOKIE_ANTERIOR = "prototipo_secretaria"
COOKIE = "prototipo_secretaria_v2"
SALT = "prototipo.secretaria.v1"
LIMITE_COOKIE = 3500


def leer_estado(request):
    """Read the shared cookie; a legacy cookie is still valid until it migrates."""
    try:
        value = request.COOKIES.get(COOKIE, request.COOKIES.get(COOKIE_ANTERIOR, ""))
        return signing.loads(value, salt=SALT, max_age=86400)
    except signing.BadSignature:
        return {"legalizaciones": {}}


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
    """A legacy cookie only reaches /prototipo/: migrate it before the API reads it."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        if (COOKIE_ANTERIOR in request.COOKIES and COOKIE not in request.COOKIES
                and COOKIE not in response.cookies and response.status_code == 200):
            return guardar_estado(request, response, leer_estado(request))
        return response
    return wrapper


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
