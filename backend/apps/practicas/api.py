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

``POST /api/v1/practicas/{id}/informe-externo/`` (RF-08, HU-07) es el adaptador del
servicio ``registrar_informe_externo``: cuerpo multipart con ``contenido`` o
``archivo``, y el permiso se resuelve contra el ``tutor_entidad`` **guardado** de
esa práctica laboral, no contra el alcance de lectura (``practicas_visibles_para``
excluye la comunitaria y devolvería un 404 indistinguible, pero el contrato de
HU-07 caso 3 pide distinguir la práctica ajena del permiso denegado).

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
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from apps.actividades.models import InformeEstudiante
from apps.actividades.services import (
    MENSAJE_ESTUDIANTE_INFORME,
    MENSAJE_INFORME_DUPLICADO,
    MENSAJE_TUTOR_ENTIDAD_INFORME,
    presentar_informe_final,
    registrar_informe_externo,
    ultima_devolucion_informe_estudiante,
)
from apps.practicas.models import Practica
from apps.practicas.services import registrar_inicio_practica
from apps.reportes.api import DevolucionSerializer
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


class InformeExternoEntradaSerializer(serializers.Serializer):
    """Entrada multipart del informe final: ``contenido``, ``archivo`` o ninguno.

    Los dos campos son opcionales en el esquema a propósito: el data-model exige
    «contenido **o** archivo» —exactamente uno—, y esa regla la decide la entidad
    (``InformeFinal.clean``), no el parser. Así el rechazo de los dos vacíos y el
    de los dos llenos vuelven con las dos claves del dominio en un solo 400, en
    lugar de dos mensajes de campo distintos.
    """

    contenido = serializers.CharField(required=False, allow_blank=True)
    archivo = serializers.FileField(required=False)

    def entrada(self) -> dict[str, Any]:
        """Los dos valores ya validados por DRF; cualquiera puede faltar.

        DRF no declara el tipo de ``validated_data``: el ``cast`` documenta el
        valor dinámico y evita tipar de más la mezcla de DRF con las anotaciones
        del proyecto.
        """
        datos = cast("dict[str, Any]", self.validated_data)
        return {"contenido": datos.get("contenido"), "archivo": datos.get("archivo")}


class InformeFinalSerializer(serializers.Serializer):
    """Proyección del informe final: la fila, sin URL de descarga.

        ``archivo`` sale como la ruta guardada y no como URL: los settings no
    definen ``MEDIA_URL``, así que un ``FileField`` con ``use_url`` fallaría al
        representar la fila. El nombre visible del archivo original queda en la
        misma cadena que devuelve el almacenamiento.
    """

    id = serializers.IntegerField(read_only=True)
    practica_id = serializers.IntegerField(read_only=True)
    tutor_entidad_id = serializers.IntegerField(read_only=True)
    contenido = serializers.CharField(read_only=True, allow_null=True)
    archivo = serializers.SerializerMethodField()
    fecha = serializers.DateTimeField(read_only=True)

    def get_archivo(self, informe) -> str | None:
        """Ruta relativa del archivo guardado, o ``None`` si el informe es texto."""
        return informe.archivo.name or None


class InformeDuplicado(APIException):
    """La práctica ya tiene un informe final: el segundo intento es 409."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = MENSAJE_INFORME_DUPLICADO
    default_code = "informe_duplicado"


class InformeSinTraduccion(APIException):
    """Clave de dominio no prevista: 500 de fallo cerrado, sin su mensaje."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Ocurrió un error inesperado."
    default_code = "error_interno"


CLAVES_DEL_INFORME = frozenset({"practica", "autor", "informe", "contenido", "archivo"})


def _traducir_informe(error) -> NoReturn:
    """Traduce el ``ValidationError`` del dominio por claves, nunca por su texto.

    ``informe`` es el 409 del duplicado, ``practica`` el 404 de una fila
    inexistente, ``autor`` el 403 del tutor de entidad ajeno y ``contenido``/
    ``archivo`` el 400 de la entrada. Cualquier otra clave es un cambio de dominio
    no previsto: falla cerrado con el 500 del contrato y sin publicar el mensaje
    del dominio.
    """
    mensajes = error.message_dict
    if set(mensajes) - CLAVES_DEL_INFORME:
        raise InformeSinTraduccion() from None
    if "informe" in mensajes:
        raise InformeDuplicado(mensajes["informe"][0]) from None
    if "practica" in mensajes:
        raise NotFound(mensajes["practica"][0]) from None
    if "autor" in mensajes:
        raise PermissionDenied(mensajes["autor"][0]) from None
    if set(mensajes) & {"contenido", "archivo"}:
        raise serializers.ValidationError(mensajes) from None
    raise InformeSinTraduccion() from None


class InformeExternoView(SinFilaEs401, APIView):
    """``POST /api/v1/practicas/{id}/informe-externo/``: informe final (HU-07).

    El rol ``tutor_entidad`` se comprueba en ``initial()``, antes de la fila y del
    cuerpo, así que un rol ajeno recibe 403 aunque la práctica no exista. La fila
    se busca por ``pk`` **sin** acotar con ``practicas_visibles_para``: el
    contrato de HU-07 caso 3 distingue la práctica ajena (403, la decide el
    servicio contra el ``tutor_entidad`` guardado) de la inexistente (404), y el
    alcance de lectura devolvería un 404 indistinguible en los dos casos. La
    vista no escribe ni cambia el estado de la práctica (S9).
    """

    permission_classes = (
        rol_requerido(
            Usuario.Rol.TUTOR_ENTIDAD,
            mensaje=MENSAJE_TUTOR_ENTIDAD_INFORME,
        ),
    )

    @extend_schema(
        summary="Registrar el informe final de la entidad sobre una práctica",
        request={"multipart/form-data": InformeExternoEntradaSerializer},
        responses={
            200: InformeFinalSerializer,
            400: OpenApiResponse(
                description=(
                    "Validación de la entrada: ni «contenido» ni «archivo», los "
                    "dos a la vez, o un archivo que no es un PDF de hasta 5 MB."
                )
            ),
            401: OpenApiResponse(
                description="Sin actor autenticado (`no_autenticado`)."
            ),
            403: OpenApiResponse(
                description=(
                    "El actor no es tutor de entidad (`permiso_denegado`), o no es "
                    "el tutor de entidad de esa práctica laboral."
                )
            ),
            404: OpenApiResponse(
                description="La práctica no existe (`no_encontrado`)."
            ),
            409: OpenApiResponse(
                description=(
                    "La práctica ya tiene un informe final registrado "
                    "(`informe_duplicado`)."
                )
            ),
        },
    )
    def post(self, request, practica_id):
        practica = Practica.objects.filter(pk=practica_id).first()
        if practica is None:
            raise NotFound()
        entrada = cast(
            InformeExternoEntradaSerializer,
            InformeExternoEntradaSerializer(data=request.data),
        )
        entrada.is_valid(raise_exception=True)
        datos = entrada.entrada()
        try:
            informe = registrar_informe_externo(
                practica=practica,
                autor=request.user,
                contenido=datos["contenido"],
                archivo=datos["archivo"],
            )
        except DjangoValidationError as error:
            _traducir_informe(error)
        return Response(InformeFinalSerializer(informe).data)


class InformeFinalEstudianteEntradaSerializer(serializers.Serializer):
    """Entrada multipart del informe final del estudiante: un PDF obligatorio.

    El campo es obligatorio en el esquema y el tipo y el tamaño los decide la
    entidad (``validar_archivo_informe``, ADR 0005): la vista no repite esa
    regla, solo la traduce.
    """

    archivo = serializers.FileField()

    def archivo_declarado(self):
        """El archivo ya validado por DRF; el ``cast`` documenta su tipo dinámico."""
        datos = cast("dict[str, Any]", self.validated_data)
        return datos["archivo"]


class InformeEstudianteSerializer(serializers.Serializer):
    """Proyección del informe del estudiante: la fila, sin URL de descarga."""

    id = serializers.IntegerField(read_only=True)
    practica_id = serializers.IntegerField(read_only=True)
    version = serializers.IntegerField(read_only=True)
    estado = serializers.CharField(read_only=True)
    fecha = serializers.DateTimeField(read_only=True)


class InformeEstudianteDetalleSerializer(serializers.Serializer):
    """Última versión del informe, con la devolución cuando la hay (S6)."""

    id = serializers.IntegerField()
    version = serializers.IntegerField()
    estado = serializers.CharField()
    fecha = serializers.DateTimeField()
    devolucion = DevolucionSerializer(allow_null=True)


class PracticaNoEnRevisionFinal(APIException):
    """La práctica no está «en revisión final»: presentar el informe es 409."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "practica_no_en_revision_final"


class InformePendienteEstudiante(APIException):
    """La última versión sigue pendiente o ya validada: presentar otra es 409."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "informe_pendiente"


class InformeEstudianteSinTraduccion(APIException):
    """Clave de dominio no prevista: 500 de fallo cerrado, sin su mensaje."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Ocurrió un error inesperado."
    default_code = "error_interno"


CLAVES_DEL_INFORME_ESTUDIANTE = frozenset(
    {"practica", "autor", "estado", "informe", "archivo"}
)


def _traducir_informe_estudiante(error) -> NoReturn:
    """Traduce el ``ValidationError`` del dominio por claves, nunca por su texto.

    ``estado`` es el 409 de la práctica que no está «en revisión final»,
    ``informe`` el 409 de la versión pendiente, ``practica`` el 404, ``autor`` el
    403 y ``archivo`` el 400 de la entrada. Cualquier otra clave es un cambio de
    dominio no previsto: falla cerrado con el 500 del contrato.
    """
    mensajes = error.message_dict
    if set(mensajes) - CLAVES_DEL_INFORME_ESTUDIANTE:
        raise InformeEstudianteSinTraduccion() from None
    if "estado" in mensajes:
        raise PracticaNoEnRevisionFinal(mensajes["estado"][0]) from None
    if "informe" in mensajes:
        raise InformePendienteEstudiante(mensajes["informe"][0]) from None
    if "practica" in mensajes:
        raise NotFound(mensajes["practica"][0]) from None
    if "autor" in mensajes:
        raise PermissionDenied(mensajes["autor"][0]) from None
    if "archivo" in mensajes:
        raise serializers.ValidationError({"archivo": mensajes["archivo"]}) from None
    raise InformeEstudianteSinTraduccion() from None


class InformeFinalEstudianteView(SinFilaEs401, APIView):
    """``POST`` y ``GET`` de ``/api/v1/practicas/{id}/informe-final/`` (C-10, RF-16).

    El ``POST`` es el adaptador fino de ``presentar_informe_final``: cuerpo
    multipart con ``archivo``, el actor es siempre el usuario autenticado y la
    práctica se busca acotada con ``practicas_visibles_para``, así que la de otro
    estudiante responde el mismo 404 que una inexistente y no revela si existe.
    La primera presentación crea la versión 1 y, tras una devolución, el mismo
    POST crea la siguiente; con una versión pendiente o ya validada responde 409.

    El ``GET`` es la lectura de la última versión con la observación de su
    devolución. Es multirrol —no exige un rol concreto— y el alcance de filas de
    T019 decide: el estudiante dueño, su tutor académico y los roles con carrera
    la alcanzan, y el 404 es el mismo para una práctica ajena, una inexistente y
    una práctica que todavía no tiene informe.
    """

    permission_classes = (PermitirPracticaVisible,)
    post_permission_classes = (
        rol_requerido(Usuario.Rol.ESTUDIANTE, mensaje=MENSAJE_ESTUDIANTE_INFORME),
        PermitirPracticaVisible,
    )

    def get_permissions(self):
        """La lectura es multirrol; solo el ``POST`` exige el rol de estudiante.

        ``rol_requerido`` se comprueba en ``initial()``, antes de la fila, así que
        dejarlo puesto en el ``GET`` convertiría al tutor en 403 en lugar del
        alcance de lectura. El ``POST`` conserva las dos capas de #79 (D5).
        """
        if self.request.method == "POST":
            return [permiso() for permiso in self.post_permission_classes]
        return [IsAuthenticated(), PermitirPracticaVisible()]

    @extend_schema(
        summary="Presentar el informe final del estudiante",
        request={"multipart/form-data": InformeFinalEstudianteEntradaSerializer},
        responses={
            201: InformeEstudianteSerializer,
            400: OpenApiResponse(
                description=(
                    "Validación de la entrada: falta el archivo, o no es un PDF de "
                    "hasta 5 MB."
                )
            ),
            401: OpenApiResponse(
                description="Sin actor autenticado (`no_autenticado`)."
            ),
            403: OpenApiResponse(
                description="El actor no es estudiante (`permiso_denegado`)."
            ),
            404: OpenApiResponse(
                description=(
                    "La práctica no existe o no es del actor (`no_encontrado`); "
                    "ambos casos responden igual."
                )
            ),
            409: OpenApiResponse(
                description=(
                    "La práctica no está «en revisión final» "
                    "(`practica_no_en_revision_final`) o la última versión del "
                    "informe no está «devuelta» (`informe_pendiente`)."
                )
            ),
        },
    )
    def post(self, request, practica_id):
        practica = practicas_visibles_para(request.user).filter(pk=practica_id).first()
        if practica is None:
            raise NotFound()
        self.check_object_permissions(request, practica)
        entrada = cast(
            InformeFinalEstudianteEntradaSerializer,
            InformeFinalEstudianteEntradaSerializer(data=request.data),
        )
        entrada.is_valid(raise_exception=True)
        try:
            informe = presentar_informe_final(
                practica=practica,
                autor=request.user,
                archivo=entrada.archivo_declarado(),
            )
        except DjangoValidationError as error:
            _traducir_informe_estudiante(error)
        return Response(
            InformeEstudianteSerializer(informe).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Consultar el informe final del estudiante y su devolución",
        responses={
            200: InformeEstudianteDetalleSerializer,
            401: OpenApiResponse(description="Sin actor autenticado."),
            404: OpenApiResponse(
                description=(
                    "La práctica no existe, está fuera del alcance del actor o no "
                    "tiene informe (`no_encontrado`); todos responden igual."
                )
            ),
        },
    )
    def get(self, request, practica_id):
        practica = practicas_visibles_para(request.user).filter(pk=practica_id).first()
        if practica is None:
            raise NotFound()
        self.check_object_permissions(request, practica)
        informe = (
            InformeEstudiante.objects.filter(practica_id=practica.pk)
            .order_by("-version")
            .first()
        )
        if informe is None:
            raise NotFound()
        devolucion = None
        if informe.estado == InformeEstudiante.Estado.DEVUELTO:
            devolucion = ultima_devolucion_informe_estudiante(informe)
        return Response(
            InformeEstudianteDetalleSerializer(
                {
                    "id": informe.pk,
                    "version": informe.version,
                    "estado": informe.estado,
                    "fecha": informe.fecha,
                    "devolucion": None
                    if devolucion is None
                    else {
                        "observacion": devolucion.observacion,
                        "autor_id": devolucion.autor_id,
                        "fecha": devolucion.fecha,
                    },
                }
            ).data
        )
