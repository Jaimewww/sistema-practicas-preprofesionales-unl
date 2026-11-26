"""Endpoint de configuración por carrera (RF-12, C-17, D1-D5).

``PUT /api/v1/carreras/{codigo}/configuracion/`` es el adaptador HTTP fino de
``guardar_configuracion``: no añade reglas de negocio, solo lee el cuerpo
estricto, busca la carrera por ``codigo`` y traduce el ``ValidationError`` del
dominio por claves (``autor`` es el 403 del coordinador de otra carrera).
El actor es siempre el usuario autenticado del servidor; el cuerpo no puede
elegir la carrera, la fila ni el autor.

Orden de los rechazos: primero el rol —``rol_requerido`` corre en ``initial()``,
antes de la carrera y del cuerpo—, después el 404 de un código inexistente y por
último el 400 de la entrada. El alcance de carrera (otro coordinador) lo decide
el servicio contra la fila guardada del actor, así que responde 403 (D5).

No hay ``DELETE`` ni ``GET``: C-17 solo escribe y la lectura de la configuración
vigente la hacen los servicios de alertas (RF-07).
"""

from collections.abc import Callable
from typing import NoReturn, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from apps.carreras.models import Carrera
from apps.carreras.serializers import (
    ConfiguracionCarreraEntradaSerializer,
    ConfiguracionCarreraSerializer,
)
from apps.carreras.services import (
    MENSAJE_COORDINADOR_CONFIGURACION,
    guardar_configuracion,
)
from apps.seguridad.permissions import SinFilaEs401, rol_requerido
from apps.usuarios.models import Usuario

# Claves que el dominio puede devolver; cualquier otra falla cerrada.
CLAVES_DE_CONFIGURACION = frozenset(
    {
        "autor",
        "carrera",
        "modalidad",
        "horas_requeridas",
        "plazo_reporte_dias",
        "plazo_revision_dias",
        "umbral_rezago",
        "vigente_desde",
    }
)


class ConfiguracionSinTraduccion(APIException):
    """Clave de dominio no prevista: 500 de fallo cerrado, sin su mensaje."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Ocurrió un error inesperado."
    default_code = "error_interno"


def _traducir_configuracion(error) -> NoReturn:
    """Traduce el ``ValidationError`` del dominio por claves, nunca por su texto.

    ``autor`` es el 403 del coordinador de otra carrera, ``carrera`` el 404 de una
    carrera que ya no existe y el resto son 400 de campo. Un error de validación
    global del modelo (``__all__``) sale como ``non_field_errors``. Cualquier otra
    clave es un cambio de dominio no previsto: falla cerrado con el 500 del
    contrato y sin publicar el mensaje del dominio.
    """
    mensajes = error.message_dict
    if set(mensajes) - CLAVES_DE_CONFIGURACION - {"__all__"}:
        raise ConfiguracionSinTraduccion() from None
    if "autor" in mensajes:
        raise PermissionDenied(mensajes["autor"][0]) from None
    if "carrera" in mensajes:
        raise NotFound(mensajes["carrera"][0]) from None
    if "__all__" in mensajes:
        raise serializers.ValidationError(
            {str(api_settings.NON_FIELD_ERRORS_KEY): mensajes["__all__"]}
        ) from None
    raise serializers.ValidationError(mensajes) from None


class ConfiguracionCarreraView(SinFilaEs401, APIView):
    """``PUT /api/v1/carreras/{codigo}/configuracion/``: configuración (C-17).

    El rol ``coordinador`` se comprueba en ``initial()``, antes de la carrera y
    del cuerpo, así que un rol ajeno recibe 403 aunque el código no exista. La
    carrera se busca por ``codigo`` sin acotar por el actor: el 404 es el mismo
    para una inexistente, y el alcance por carrera lo decide el servicio con la
    fila guardada del actor (403, D5).
    """

    permission_classes = (
        rol_requerido(
            Usuario.Rol.COORDINADOR,
            mensaje=MENSAJE_COORDINADOR_CONFIGURACION,
        ),
    )

    def permission_denied(self, request, message=None, code=None):
        """Declara el ``NoReturn`` de ``APIView`` y delega la regla en el mixin.

        ``SinFilaEs401.permission_denied`` siempre termina lanzando —``401`` para
        una cuenta sin fila vigente y, si no, el ``PermissionDenied`` de DRF—,
        pero al ser una clase plana el checker infiere ``None`` y la mezcla con
        ``APIView`` (que declara ``NoReturn``) queda incompatible. El ``cast``
        documenta esa invariante; la regla sigue viviendo en ``apps.seguridad`` y
        no se reimplementa acá.
        """
        denegar = cast("Callable[..., NoReturn]", SinFilaEs401.permission_denied)
        denegar(self, request, message=message, code=code)

    @extend_schema(
        summary="Guardar la configuración de una carrera por modalidad",
        request=ConfiguracionCarreraEntradaSerializer,
        responses={
            200: ConfiguracionCarreraSerializer,
            400: OpenApiResponse(
                description=(
                    "Validación de la entrada: cuerpo que no es objeto, clave "
                    "ajena, campo obligatorio ausente, modalidad distinta de "
                    "«laboral»/«comunitaria», horas requeridas en cero o menos, "
                    "plazos negativos o umbral fuera de 0–100."
                )
            ),
            401: OpenApiResponse(
                description="Sin actor autenticado (`no_autenticado`)."
            ),
            403: OpenApiResponse(
                description=(
                    "El actor no es coordinador (`permiso_denegado`) o es "
                    "coordinador de otra carrera."
                )
            ),
            404: OpenApiResponse(
                description="No hay una carrera con ese código (`no_encontrado`)."
            ),
        },
    )
    def put(self, request, codigo):
        carrera = Carrera.objects.filter(codigo=codigo).first()
        if carrera is None:
            raise NotFound()
        # DRF declara el constructor como ``Serializer | ListSerializer`` según
        # ``many``; sin ``many`` siempre es esta clase.
        entrada = cast(
            ConfiguracionCarreraEntradaSerializer,
            ConfiguracionCarreraEntradaSerializer(data=request.data),
        )
        entrada.is_valid(raise_exception=True)
        try:
            configuracion = guardar_configuracion(
                carrera=carrera,
                autor=request.user,
                datos=entrada.datos(),
            )
        except DjangoValidationError as error:
            _traducir_configuracion(error)
        return Response(ConfiguracionCarreraSerializer(configuracion).data)
