"""Renderer del contrato universal de respuesta (#77, S2-S4).

Envuelve la carga cruda de toda respuesta DRF con estado < 400 en
``{"success", "message", "data", "errors", "meta"}`` (``meta`` vacío y ``errors``
en ``null``, según S4). Las respuestas >= 400 ya vienen envueltas desde
``apps.contrato.exceptions``: el renderer las deja pasar tal cual, de modo que el
shape del error tiene un solo dueño y el renderer no puede duplicar el envelope.

``204 No Content``: DRF no recorta el cuerpo por estado (``Response.render``
siempre llama al renderer), así que el «sin cuerpo» se logra aquí devolviendo
``b""`` antes de serializar nada.

La serialización usa ``DjangoJSONEncoder``: fechas, horas, Decimals y UUIDs de
la carga salen formateados por Django, no como ``TypeError`` del ``json`` base.
"""

import json

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.renderers import BaseRenderer

CLAVES_ENVELOPE = frozenset({"success", "message", "data", "errors", "meta"})

MENSAJES_EXITO = {
    200: "Operación exitosa.",
    201: "Recurso creado.",
    202: "Solicitud aceptada.",
}
MENSAJE_EXITO_POR_DEFECTO = "Operación exitosa."


class SuccessEnvelopeRenderer(BaseRenderer):
    """Único renderer por defecto: no queda camino que salga sin envelope."""

    media_type = "application/json"
    format = "json"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        respuesta = (renderer_context or {}).get("response")
        estado = getattr(respuesta, "status_code", 200)
        if estado == 204:
            return b""
        if estado >= 400:
            cuerpo = data
        else:
            cuerpo = {
                "success": True,
                "message": MENSAJES_EXITO.get(estado, MENSAJE_EXITO_POR_DEFECTO),
                "data": data,
                "errors": None,
                "meta": {},
            }
        return json.dumps(
            cuerpo, ensure_ascii=False, cls=DjangoJSONEncoder
        ).encode(self.charset)
