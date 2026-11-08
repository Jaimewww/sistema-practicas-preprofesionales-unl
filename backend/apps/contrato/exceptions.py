"""Exception handler del contrato universal de respuesta (#77, S2-S4).

Traduce validación, autenticación, permisos, 404 y cualquier excepción no
controlada al envelope de S4, con ``message`` corto en español:

* validación con ``detail`` por campo -> ``errors`` ``{campo: [textos]}``;
* errores planos -> ``errors`` ``{"detail": texto, "code": codigo}``, con un
  ``code`` legible por máquina (``no_autenticado``, ``permiso_denegado``,
  ``no_encontrado``, ``demasiadas_solicitudes`` (429, con ``Retry-After``),
  ``error_interno`` o el código propio de la ``APIException``,
  p. ej. el de un 409).

El 500 arma un cuerpo genérico: ni el mensaje original, ni la traza, ni variables
locales salen por el wire (la traza queda solo en el log del proceso). El handler
nunca devuelve ``None``, así que DRF no re-lanza y tampoco aparece su 500 por
defecto ni el HTML de depuración con ``DEBUG`` encendido.

El ``detail`` de una ``APIException`` sí se conserva: lo escribe el servidor y es
parte del contrato con el cliente. La autenticación real (token/JWT) es de #79.

El 401 y el 404 son genéricos a propósito (no revelan el motivo de la
autenticación ni si el recurso existe); el 403 y las ``APIException`` conservan
el ``detail`` del servidor. Como el handler por defecto de DRF, marca la
transacción para rollback con ``set_rollback`` cuando ``ATOMIC_REQUESTS`` está
activo, para que una petición fallida no deje escrituras a medias.
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
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import set_rollback

logger = logging.getLogger(__name__)

MENSAJE_VALIDACION = "Datos inválidos."
MENSAJE_SOLICITUD = "Solicitud inválida."
MENSAJE_AUTENTICACION = "Autenticación requerida."
DETALLE_AUTENTICACION = "Se requiere autenticación."
CODIGO_AUTENTICACION = "no_autenticado"
MENSAJE_PERMISO = "Permiso denegado."
DETALLE_PERMISO = "No tiene permiso para esta operación."
CODIGO_PERMISO = "permiso_denegado"
MENSAJE_LIMITE = "Demasiadas solicitudes."
DETALLE_LIMITE = "Demasiados intentos. Intente de nuevo en {espera} segundos."
DETALLE_LIMITE_SIN_ESPERA = "Demasiados intentos. Intente de nuevo más tarde."
CODIGO_LIMITE = "demasiadas_solicitudes"
MENSAJE_NO_ENCONTRADO = "Recurso no encontrado."
DETALLE_NO_ENCONTRADO = "No encontrado."
CODIGO_NO_ENCONTRADO = "no_encontrado"
MENSAJE_INTERNO = "Error interno del servidor."
DETALLE_INTERNO = "Ocurrió un error inesperado."
CODIGO_INTERNO = "error_interno"


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


def _codigo(exc):
    """Código de la ``APIException``: el suyo si es un texto, si no el por defecto."""
    codigo = exc.get_codes()
    return codigo if isinstance(codigo, str) else exc.default_code


def _detalle_permiso(exc):
    """Conserva el texto que escribió el servidor; el de fábrica (inglés) se sustituye."""
    if isinstance(exc, PermissionDenied) and str(exc.detail) != str(exc.default_detail):
        return str(exc.detail)
    return DETALLE_PERMISO


def _cabeceras(exc):
    """Replica las cabeceras que DRF deriva de la excepción (401 y reintentos)."""
    cabeceras = {}
    if getattr(exc, "auth_header", None):
        cabeceras["WWW-Authenticate"] = exc.auth_header
    if getattr(exc, "wait", None):
        cabeceras["Retry-After"] = str(exc.wait)
    return cabeceras


def _respuesta(estado, mensaje, detalle, codigo, exc):
    return Response(
        envelope(False, mensaje, errors={"detail": detalle, "code": codigo}),
        status=estado,
        headers=_cabeceras(exc),
    )


def envelope_exception_handler(exc, context):
    # Igual que el handler por defecto de DRF: deshace la transacción de la petición.
    set_rollback()
    if isinstance(exc, ValidationError):
        return Response(
            envelope(False, MENSAJE_VALIDACION, errors=_errores(exc.detail)),
            status=exc.status_code,
            headers=_cabeceras(exc),
        )
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        return _respuesta(
            401, MENSAJE_AUTENTICACION, DETALLE_AUTENTICACION, CODIGO_AUTENTICACION, exc
        )
    if isinstance(exc, (Http404, NotFound)):
        return _respuesta(
            404, MENSAJE_NO_ENCONTRADO, DETALLE_NO_ENCONTRADO, CODIGO_NO_ENCONTRADO, exc
        )
    if isinstance(exc, (PermissionDenied, PermisoDenegado)):
        return _respuesta(403, MENSAJE_PERMISO, _detalle_permiso(exc), CODIGO_PERMISO, exc)
    if isinstance(exc, Throttled):
        detalle = (
            DETALLE_LIMITE.format(espera=exc.wait)
            if exc.wait
            else DETALLE_LIMITE_SIN_ESPERA
        )
        return _respuesta(429, MENSAJE_LIMITE, detalle, CODIGO_LIMITE, exc)
    if isinstance(exc, APIException):
        errores = _errores(exc.detail)
        if "detail" in errores:
            errores["code"] = _codigo(exc)
        return Response(
            envelope(False, MENSAJE_SOLICITUD, errors=errores),
            status=exc.status_code,
            headers=_cabeceras(exc),
        )
    logger.error(
        "Excepción no controlada en la API v1: %s", type(exc).__name__, exc_info=True
    )
    return _respuesta(500, MENSAJE_INTERNO, DETALLE_INTERNO, CODIGO_INTERNO, exc)
