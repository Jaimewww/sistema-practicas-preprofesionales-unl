"""Endpoints de prácticas de la API real: lista, detalle y fecha real de inicio.

La lista y el detalle (S2, #78) son de solo lectura y solo las filas que
``practicas_visibles_para`` (T019) entrega al actor guardado: la vista no calcula
permisos propios. Al llamar al helper sin consulta, el alcance parte de todas las
prácticas; pasarle una consulta vacía sigue devolviendo vacío. El detalle de una
práctica fuera de su alcance responde 404, igual que una que no existe. La tarjeta
expone lo mínimo y nada sensible (sin motivos ni proyecto).

``POST /api/v1/practicas/{id}/inicio/`` (T11, RF-11) es el adaptador HTTP fino del
servicio de dominio ``registrar_inicio_practica``: no añade reglas de negocio, solo
lee el cuerpo estricto, acota la práctica al alcance del actor y traduce el
``ValidationError`` del dominio por claves. El actor es siempre el usuario
autenticado del servidor.

#79 (D5): el alcance de filas sigue siendo el del helper y encima van los permisos
DRF de ``apps.seguridad`` —toda la API real es auth-first y el permiso de objeto
declara la misma regla en la capa de permisos—, sin reimplementar T019.
"""

from collections.abc import Callable, Mapping
from datetime import date
from typing import Any, NoReturn, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, serializers, status
from rest_framework.exceptions import APIException, NotFound
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from apps.practicas.models import Practica
from apps.practicas.services import registrar_inicio_practica
from apps.seguridad.permissions import (
    PermitirPracticaVisible,
    SinFilaEs401,
    rol_requerido,
)
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import practicas_visibles_para


# Es un ``Serializer`` explícito y no un ``ModelSerializer``: el ``Meta`` anidado
# de ``ModelSerializer`` solo existe en los stubs de DRF —en ejecución cada
# serializador aporta el suyo— y el checker lo trata como un reemplazo
# incompatible. Los campos replican el orden, el tipo y el read-only que
# ``ModelSerializer`` derivaba del modelo; el payload y el OpenAPI no cambian y
# lo comprueba ``test_reportes_serializer_parity``.
class PracticaCardSerializer(serializers.Serializer):
    """Proyección mínima de una práctica: seis campos de solo lectura."""

    # DRF deriva la PK del modelo (``BigAutoField``) como ``BigIntegerField`` con
    # etiqueta «ID»; se declara igual para conservar el campo tal cual.
    id = serializers.BigIntegerField(read_only=True, label="ID")
    estudiante_id = serializers.IntegerField(read_only=True)
    tipo = serializers.ChoiceField(choices=Practica.Tipo.choices, read_only=True)
    subtipo = serializers.ChoiceField(choices=Practica.Subtipo.choices, read_only=True)
    estado = serializers.ChoiceField(choices=Practica.Estado.choices, read_only=True)
    horas_requeridas = serializers.IntegerField(read_only=True)


@extend_schema_view(get=extend_schema(summary="Prácticas visibles para el actor"))
class PracticasListaView(SinFilaEs401, generics.ListAPIView):
    """``GET /api/v1/practicas/``: prácticas visibles del actor (RF-11)."""

    serializer_class = PracticaCardSerializer
    permission_classes = (PermitirPracticaVisible,)

    def get_queryset(self):
        return practicas_visibles_para(self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de una práctica visible para el actor",
        responses={
            200: PracticaCardSerializer,
            404: OpenApiResponse(
                description=(
                    "La práctica no existe o está fuera del alcance del actor "
                    "(`no_encontrado`); ambos casos responden igual."
                )
            ),
        },
    )
)
class PracticaDetalleView(SinFilaEs401, generics.RetrieveAPIView):
    """``GET /api/v1/practicas/{id}/``: 404 fuera del alcance o inexistente."""

    serializer_class = PracticaCardSerializer
    permission_classes = (PermitirPracticaVisible,)
    lookup_url_kwarg = "practica_id"

    def get_queryset(self):
        return practicas_visibles_para(self.request.user)


MENSAJE_INICIO = (
    "Solo el coordinador activo de la carrera de la práctica puede registrar "
    "su fecha real de inicio."
)
MENSAJE_CUERPO_INICIO = "El cuerpo debe ser un objeto JSON con «fecha»."
MENSAJE_CAMPO_NO_ADMITIDO_INICIO = (
    "Campo no admitido: la fecha real de inicio solo envía «fecha»."
)


class RegistrarInicioPracticaSerializer(serializers.Serializer):
    """Entrada estricta: un objeto JSON con una sola clave, ``fecha``.

    Rechaza con 400 los cuerpos que no son objeto y cualquier clave distinta de
    ``fecha``, incluidas las que fija el servidor (``id``, ``fecha_inicio_real``)
    y la práctica del path: el cliente nunca elige a qué fila escribe.
    """

    fecha = serializers.DateField()

    def to_internal_value(self, data: object) -> dict:
        """Acepta solo un objeto JSON con la clave ``fecha``.

        ``data`` es el cuerpo crudo: puede ser una lista, un texto o un número,
        y por eso entra como ``object`` y se estrecha acá.
        """
        if not isinstance(data, Mapping):
            raise serializers.ValidationError(
                {str(api_settings.NON_FIELD_ERRORS_KEY): [MENSAJE_CUERPO_INICIO]}
            )
        sobrantes = sorted(set(data) - set(self.fields))
        if sobrantes:
            raise serializers.ValidationError(
                {campo: [MENSAJE_CAMPO_NO_ADMITIDO_INICIO] for campo in sobrantes}
            )
        return super().to_internal_value(data)

    def fecha_declarada(self) -> date:
        """La fecha ya validada por ``DateField``.

        DRF no declara el tipo de ``validated_data``: el ``cast`` documenta el
        valor dinámico que ya validó el campo y evita tipar de más la mezcla de
        DRF con las anotaciones del proyecto.
        """
        datos = cast("dict[str, Any]", self.validated_data)
        return cast("date", datos["fecha"])


class InicioPracticaSerializer(serializers.Serializer):
    """Respuesta: la práctica tocada y la fecha real de inicio guardada."""

    id = serializers.IntegerField(read_only=True)
    fecha_inicio_real = serializers.DateField(read_only=True)


class InicioNoEnCurso(APIException):
    """El dominio rechaza la declaración porque la práctica no está «en curso».

    Comparte el código de máquina del POST de reportes a propósito: el cliente
    decide por ``practica_no_en_curso``, no por el texto.
    """

    status_code = status.HTTP_409_CONFLICT
    default_code = "practica_no_en_curso"


class InicioSinTraduccion(APIException):
    """Clave de dominio no prevista: 500 de fallo cerrado, sin su mensaje."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Ocurrió un error inesperado."
    default_code = "error_interno"


CLAVES_DE_INICIO = frozenset({"fecha", "estado"})


def _traducir_inicio(error):
    """Traduce el ``ValidationError`` del dominio por claves, nunca por su texto.

    ``estado`` es el único rechazo que no es de entrada (409); ``fecha`` es 400 de
    campo. Cualquier otra clave es un cambio de dominio no previsto: falla cerrado
    con el 500 del contrato y sin publicar el mensaje del dominio.
    """
    mensajes = error.message_dict
    if set(mensajes) - CLAVES_DE_INICIO:
        raise InicioSinTraduccion() from None
    if "estado" in mensajes:
        raise InicioNoEnCurso(mensajes["estado"][0]) from None
    if "fecha" in mensajes:
        raise serializers.ValidationError({"fecha": mensajes["fecha"]}) from None
    raise InicioSinTraduccion() from None


class InicioPracticaView(SinFilaEs401, APIView):
    """``POST /api/v1/practicas/{id}/inicio/``: fecha real de inicio (T11).

    El rol ``coordinador`` y el alcance de carrera se comprueban **antes** de leer
    el cuerpo: los permisos de la vista corren en ``initial()`` y la práctica se
    busca acotada con ``practicas_visibles_para``. Una práctica de otra carrera y
    una inexistente responden el mismo 404 genérico, incluso con un cuerpo
    malformado, así que la respuesta no revela existencia. El actor es el usuario
    autenticado del servidor; el cuerpo solo aporta ``fecha``.
    """

    permission_classes = (
        rol_requerido(Usuario.Rol.COORDINADOR, mensaje=MENSAJE_INICIO),
        PermitirPracticaVisible,
    )

    def permission_denied(self, request, message=None, code=None) -> NoReturn:
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
        summary="Registrar la fecha real de inicio de una práctica",
        request=RegistrarInicioPracticaSerializer,
        responses={
            200: InicioPracticaSerializer,
            400: OpenApiResponse(
                description=(
                    "Validación de la entrada: cuerpo que no es objeto, clave "
                    "distinta de «fecha», fecha ausente o mal formada, fecha futura "
                    "o una segunda fecha distinta de la ya registrada (la guardada "
                    "no se revela)."
                )
            ),
            401: OpenApiResponse(
                description="Sin actor autenticado (`no_autenticado`)."
            ),
            403: OpenApiResponse(
                description=(
                    "El actor no es coordinador (`permiso_denegado`); se comprueba "
                    "antes que el cuerpo y que la existencia de la práctica."
                )
            ),
            404: OpenApiResponse(
                description=(
                    "La práctica no existe o está fuera del alcance del actor "
                    "(`no_encontrado`); ambos casos responden igual."
                )
            ),
            409: OpenApiResponse(
                description=("La práctica no está «en curso» (`practica_no_en_curso`).")
            ),
        },
    )
    def post(self, request, practica_id):
        practica = practicas_visibles_para(request.user).filter(pk=practica_id).first()
        if practica is None:
            raise NotFound()
        self.check_object_permissions(request, practica)
        # DRF declara el constructor como ``Serializer | ListSerializer`` según
        # ``many``; sin ``many`` siempre es esta clase.
        entrada = cast(
            RegistrarInicioPracticaSerializer,
            RegistrarInicioPracticaSerializer(data=request.data),
        )
        entrada.is_valid(raise_exception=True)
        try:
            practica = registrar_inicio_practica(
                practica=practica,
                fecha=entrada.fecha_declarada(),
                autor=request.user,
            )
        except DjangoValidationError as error:
            _traducir_inicio(error)
        return Response(InicioPracticaSerializer(practica).data)
