"""Exception handler del contrato universal de respuesta (#77, S2-S4).

Traduce validación, autenticación, permisos, 404 y cualquier excepción no
controlada al envelope de S4, con ``message`` corto en español:

* validación con ``detail`` por campo -> ``errors`` ``{campo: [textos]}``;
* errores planos -> ``errors`` ``{"detail": texto}``.

El 500 arma un cuerpo genérico: ni el mensaje original, ni la traza, ni variables
locales salen por el wire (la traza queda solo en el log del proceso). El handler
nunca devuelve ``None``, así que DRF no re-lanza y tampoco aparece su 500 por
defecto ni el HTML de depuración con ``DEBUG`` encendido.

El ``detail`` de una ``APIException`` sí se conserva: lo escribe el servidor y es
parte del contrato con el cliente. La autenticación real (token/JWT) es de #79.
"""

import logging

from django.core.exceptions import PermissionDenied as PermisoDenegado
from django.http import Http404
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response

logger = logging.getLogger(__name__)

MENSAJE_VALIDACION = "Datos inválidos."
MENSAJE_SOLICITUD = "Solicitud inválida."
MENSAJE_AUTENTICACION = "Autenticación requerida."
DETALLE_AUTENTICACION = "Se requiere autenticación."
MENSAJE_PERMISO = "Permiso denegado."
DETALLE_PERMISO = "No tiene permiso para esta operación."
MENSAJE_NO_ENCONTRADO = "Recurso no encontrado."
DETALLE_NO_ENCONTRADO = "No encontrado."
MENSAJE_INTERNO = "Error interno del servidor."
DETALLE_INTERNO = "Ocurrió un error inesperado."


def envelope(success, message, data=None, errors=None):
    """Arma el envelope de S4; el orden de claves es el del contrato."""
    return {
        "success": success,
        "message": message,
        "data": data,
        "errors": errors,
        "meta": {},
    }


def _normalizar(detalle):
    """Lleva el ``detail`` de DRF (texto, lista o dict anidado) a tipos simples."""
    if isinstance(detalle, dict):
        return {campo: _normalizar(valor) for campo, valor in detalle.items()}
    if isinstance(detalle, (list, tuple)):
        return [str(item) for item in detalle]
    return str(detalle)


def _errores(detalle):
    normalizado = _normalizar(detalle)
    return normalizado if isinstance(normalizado, dict) else {"detail": normalizado}


def _cabeceras(exc):
    """Replica las cabeceras que DRF deriva de la excepción (401 y reintentos)."""
    cabeceras = {}
    if getattr(exc, "auth_header", None):
        cabeceras["WWW-Authenticate"] = exc.auth_header
    if getattr(exc, "wait", None):
        cabeceras["Retry-After"] = str(exc.wait)
    return cabeceras


def _respuesta(estado, mensaje, detalle, exc):
    return Response(
        envelope(False, mensaje, errors={"detail": detalle}),
        status=estado,
        headers=_cabeceras(exc),
    )


def envelope_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response(
            envelope(False, MENSAJE_VALIDACION, errors=_errores(exc.detail)),
            status=exc.status_code,
            headers=_cabeceras(exc),
        )
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        return _respuesta(401, MENSAJE_AUTENTICACION, DETALLE_AUTENTICACION, exc)
    if isinstance(exc, (Http404, NotFound)):
        return _respuesta(404, MENSAJE_NO_ENCONTRADO, DETALLE_NO_ENCONTRADO, exc)
    if isinstance(exc, (PermissionDenied, PermisoDenegado)):
        return _respuesta(403, MENSAJE_PERMISO, DETALLE_PERMISO, exc)
    if isinstance(exc, APIException):
        return Response(
            envelope(False, MENSAJE_SOLICITUD, errors=_errores(exc.detail)),
            status=exc.status_code,
            headers=_cabeceras(exc),
        )
    logger.error(
        "Excepción no controlada en la API v1: %s", type(exc).__name__, exc_info=True
    )
    return _respuesta(500, MENSAJE_INTERNO, DETALLE_INTERNO, exc)
