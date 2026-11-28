# pyright: reportMissingImports=false
"""Endpoints del tutor académico para validar/devolver reportes (RF-03, #122).

``GET /api/v1/pendientes/`` lista los reportes en revisión de las prácticas
asignadas al tutor activo. ``GET /api/v1/reportes/{id}/`` (RF-03, S6) es la
lectura del reporte individual con la observación de su última devolución.
``POST /api/v1/reportes/{id}/validar/`` marca el
reporte «validado» y registra la ``Validacion``. ``POST
/api/v1/reportes/{id}/devolver/`` lo marca «devuelto» con observación
obligatoria. ``POST /api/v1/reportes/{id}/reenviar/`` (#124) devuelve a «en
revisión» la fila devuelta y la deja lista para corregir. ``GET
/api/v1/practicas/{id}/horas/`` (#126) lee las horas acumuladas con el alcance
de filas de T019. ``POST /api/v1/reportes/{id}/confirmacion/`` (RF-08, HU-07)
registra quién confirmó el reporte de su practicante y cuándo. Todos responden
con el envelope de #77 y fail-closed: sin token 401, rol ajeno 403 o práctica
fuera de alcance 404 según la ruta, estado del reporte que no admite la
transición 409 (``reporte_no_en_revision`` o ``reporte_no_devuelto``) y práctica
que no está en curso 409 (``practica_no_en_curso``, CU-01 2b). La cola lista
solo prácticas en curso.

C-03 (#157): ``GET /api/v1/practicas/{id}/reportes/`` lista los reportes de la
práctica con el detalle ampliado; el ``POST`` de esa ruta admite, además del
JSON legado, ``multipart/form-data`` con ``actividades`` y ``evidencias`` (PDF
de hasta 5 MB); el reenvío admite PDFs nuevos opcionales, guardados como la
versión siguiente; y ``GET /api/v1/reportes/{id}/evidencias/{evidencia_id}/``
descarga un PDF con el alcance de filas de T019, sin URL pública de archivos.
"""

from collections.abc import Mapping
from typing import NoReturn

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.http import FileResponse
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
)
from rest_framework import serializers, status
from rest_framework.exceptions import (
    APIException,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from apps.actividades.models import InformeEstudiante
from apps.actividades.services import (
    MENSAJE_CONFIRMACION_DUPLICADA,
    MENSAJE_TUTOR_ENTIDAD_CONFIRMACION,
    confirmar_reporte,
    devolver_informe_estudiante,
    validar_informe_estudiante,
)
from apps.practicas.models import Practica
from apps.reportes.models import (
    MENSAJE_SEMANA_DUPLICADA,
    EvidenciaReporte,
    ReporteSemanal,
)
from apps.reportes.serializers import (
    ReenvioConEvidenciasSerializer,
    ReporteConEvidenciasSerializer,
    ReporteSemanalSerializer,
)
from apps.reportes.services import (
    MENSAJE_ESTUDIANTE,
    MENSAJE_TUTOR,
    con_detalle,
    devolver_reporte,
    evidencias_atomicas,
    horas_practica,
    reenviar_reporte,
    validar_reporte,
)
from apps.seguridad.permissions import (
    PermitirPracticaVisible,
    SinFilaEs401,
    rol_requerido,
)
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import practicas_visibles_para

MENSAJE_ACTOR = (
    "Solo el estudiante de la práctica puede registrar sus reportes semanales."
)


def actor_estudiante(usuario):
    """Estudiante activo desde la fila guardada; el objeto del llamador no decide."""
    if not isinstance(usuario, Usuario) or getattr(usuario, "pk", None) is None:
        raise NotAuthenticated()
    fila = Usuario.objects.filter(pk=usuario.pk, is_active=True).only("rol").first()
    if fila is None:
        raise NotAuthenticated()
    if fila.rol != Usuario.Rol.ESTUDIANTE:
        raise PermissionDenied(MENSAJE_ACTOR)
    return fila


class DevolucionSerializer(serializers.Serializer):
    """La devolución que el estudiante necesita leer para corregir (S6)."""

    observacion = serializers.CharField()
    autor_id = serializers.IntegerField()
    fecha = serializers.DateTimeField()


RUTA_DESCARGA_EVIDENCIA = "/api/v1/reportes/{reporte_id}/evidencias/{evidencia_id}/"


class EvidenciaReporteSerializer(serializers.Serializer):
    """Metadatos de un PDF del reporte y su ruta autenticada de descarga (D7, D8).

    ``descarga`` es la ruta de la API que exige token y alcance, nunca la ruta de
    almacenamiento ni una URL pública del archivo.
    """

    id = serializers.IntegerField()
    version = serializers.IntegerField()
    nombre = serializers.CharField()
    tamano_bytes = serializers.IntegerField()
    subida_en = serializers.DateTimeField()
    descarga = serializers.CharField()


class ReporteDetalleSerializer(serializers.Serializer):
    """Detalle de un reporte: sus cinco campos y la devolución, si la hay.

    C-03 (D7) suma ``actividades``, la ``version`` vigente (la mayor de sus
    evidencias, 1 sin ninguna), las ``evidencias`` de todas las versiones y el
    historial ``devoluciones``; ``devolucion`` conserva su semántica legada.
    """

    id = serializers.IntegerField()
    semana = serializers.IntegerField()
    horas_reportadas = serializers.IntegerField()
    estado = serializers.CharField()
    fecha_registro = serializers.DateTimeField()
    devolucion = DevolucionSerializer(allow_null=True)
    actividades = serializers.CharField(allow_blank=True)
    version = serializers.IntegerField()
    evidencias = EvidenciaReporteSerializer(many=True)
    devoluciones = DevolucionSerializer(many=True)


def _devolucion_de(reporte):
    """La última devolución, solo mientras el reporte siga «devuelto».

    Después de un reenvío el reporte vuelve a «en revisión»: la observación
    anterior ya no describe su estado, así que no se publica (S6). Es la última
    del historial precargado por ``con_detalle`` (orden ``fecha``, ``pk``).
    """
    if reporte.estado != ReporteSemanal.Estado.DEVUELTO or not reporte.devoluciones:
        return None
    return reporte.devoluciones[-1]


def _devolucion_publicada(devolucion):
    """Proyección de la devolución: observación, autor y fecha (S6)."""
    if devolucion is None:
        return None
    return {
        "observacion": devolucion.observacion,
        "autor_id": devolucion.autor_id,
        "fecha": devolucion.fecha,
    }


def detalle_de(reporte):
    """Proyección del detalle ampliado; la comparten la lista y el detalle.

    El reporte llega de ``con_detalle``: la ``version`` vigente (D1', la mayor de
    sus evidencias, 1 sin ninguna) sale de las filas ya precargadas.
    """
    evidencias = list(reporte.evidencias.all())
    return {
        "id": reporte.pk,
        "semana": reporte.semana,
        "horas_reportadas": reporte.horas_reportadas,
        "estado": reporte.estado,
        "fecha_registro": reporte.fecha_registro,
        "devolucion": _devolucion_publicada(_devolucion_de(reporte)),
        "actividades": reporte.actividades,
        "version": max((evidencia.version for evidencia in evidencias), default=1),
        "evidencias": [
            {
                "id": evidencia.pk,
                "version": evidencia.version,
                "nombre": evidencia.nombre,
                "tamano_bytes": evidencia.tamano_bytes,
                "subida_en": evidencia.subida_en,
                "descarga": RUTA_DESCARGA_EVIDENCIA.format(
                    reporte_id=reporte.pk, evidencia_id=evidencia.pk
                ),
            }
            for evidencia in evidencias
        ],
        "devoluciones": [
            _devolucion_publicada(devolucion) for devolucion in reporte.devoluciones
        ],
    }


class ReportePracticaView(SinFilaEs401, APIView):
    """Registra el reporte semanal de la práctica; solo su propio estudiante.

    C-03: el ``GET`` lista los reportes de la práctica (detalle ampliado) para
    todo actor con alcance de filas; el ``POST`` acepta JSON legado o multipart
    con evidencias, y un rechazo no deja filas ni archivos (D4, D6).
    """

    # #79: permiso de rol (solo estudiante registra reportes) y de objeto con el
    # alcance de T019; los chequeos explícitos de abajo quedan como segunda
    # barrera (D5, defensa en profundidad).
    permission_classes = (
        rol_requerido(Usuario.Rol.ESTUDIANTE, mensaje=MENSAJE_ACTOR),
        PermitirPracticaVisible,
    )

    def get_permissions(self):
        """La lista (C-03, D6) es multirrol; el ``POST`` sigue siendo del estudiante.

        ``rol_requerido`` se comprueba en ``initial()``: dejarlo en el ``GET``
        convertiría al tutor en 403 en lugar del alcance de filas de T019.
        """
        if self.request.method == "GET":
            return [IsAuthenticated(), PermitirPracticaVisible()]
        return [permiso() for permiso in self.permission_classes]

    @extend_schema(
        summary="Listar los reportes semanales de una práctica",
        responses={
            200: ReporteDetalleSerializer(many=True),
            401: OpenApiResponse(description="Sin actor autenticado."),
            404: OpenApiResponse(
                description=(
                    "La práctica no existe o está fuera del alcance del actor "
                    "(`no_encontrado`); ambos casos responden igual."
                )
            ),
        },
    )
    def get(self, request, practica_id):
        practica = practicas_visibles_para(request.user).filter(pk=practica_id).first()
        if practica is None:
            raise NotFound()
        self.check_object_permissions(request, practica)
        reportes = con_detalle(practica.reportes.order_by("semana"))
        return Response(
            ReporteDetalleSerializer(
                [detalle_de(reporte) for reporte in reportes], many=True
            ).data
        )

    @extend_schema(
        summary="Registrar el reporte semanal de una práctica",
        description=(
            "JSON (o formulario) con `semana` y `horas_reportadas`: el contrato "
            "legado. `multipart/form-data` suma `actividades` (texto obligatorio) "
            "y `evidencias` (uno o más PDF de hasta 5 MB, la versión 1). Un "
            "rechazo no deja filas ni archivos."
        ),
        request={
            "application/json": ReporteSemanalSerializer,
            "application/x-www-form-urlencoded": ReporteSemanalSerializer,
            "multipart/form-data": ReporteConEvidenciasSerializer,
        },
        responses={
            201: ReporteSemanalSerializer,
            400: OpenApiResponse(
                description=(
                    "Validación de la entrada: cuerpo que no es objeto, campo no "
                    "admitido, semana u horas inválidas (máximo 168 por semana), "
                    "ayudantía con más de 10 horas o, en multipart, actividades "
                    "vacías o evidencias ausentes, que no son PDF o de más de 5 MB."
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
                    "La práctica no existe o no es del estudiante (`no_encontrado`); "
                    "ambos casos responden igual."
                )
            ),
            409: OpenApiResponse(
                description=(
                    "La práctica no está en curso (`practica_no_en_curso`) o la "
                    "semana ya tiene reporte (`semana_duplicada`)."
                )
            ),
        },
    )
    def post(self, request, practica_id):
        actor = actor_estudiante(request.user)
        # C-03 (D4): ``multipart/form-data`` suma actividades y PDFs; cualquier
        # otro cuerpo sigue el contrato JSON legado sin cambios.
        entrada = (
            ReporteConEvidenciasSerializer
            if es_multipart(request)
            else ReporteSemanalSerializer
        )
        with evidencias_atomicas() as guardadas, transaction.atomic():
            practica = (
                Practica.objects.select_for_update()
                .filter(pk=practica_id, estudiante_id=actor.pk)
                .first()
            )
            if practica is None:
                raise NotFound()
            self.check_object_permissions(request, practica)
            if practica.estado != Practica.Estado.EN_CURSO:
                raise PracticaNoEnCurso(
                    MENSAJE_NO_EN_CURSO.format(estado=practica.estado)
                )
            serializer = entrada(
                data=request.data,
                context={"practica": practica, "guardadas": guardadas},
            )
            serializer.is_valid(raise_exception=True)
            if semana_ya_reportada(practica, serializer.validated_data["semana"]):
                raise SemanaDuplicada()
            try:
                with transaction.atomic():
                    # ``ingreso_revision_en`` es interno: el servidor lo fija con su
                    # reloj dentro de la misma escritura que crea la fila, nunca el
                    # cliente ni ``ReporteSemanal.save()`` compartido.
                    reporte = serializer.save(
                        practica=practica, ingreso_revision_en=timezone.now()
                    )
            except IntegrityError as error:
                if not es_semana_unica(error):
                    raise
                raise SemanaDuplicada() from None
        return Response(
            ReporteSemanalSerializer(reporte).data, status=status.HTTP_201_CREATED
        )


def es_multipart(request):
    return request.content_type.startswith("multipart/form-data")


MENSAJE_NO_EN_CURSO = "La práctica está en «{estado}»: solo una práctica en curso admite reportes semanales."


class PracticaNoEnCurso(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "practica_no_en_curso"


class SemanaDuplicada(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = MENSAJE_SEMANA_DUPLICADA
    default_code = "semana_duplicada"


RESTRICCION_SEMANA_UNICA = "reportes_reporte_semana_unica"

COLUMNAS_SEMANA_UNICA = (
    "reportes_reportesemanal.practica_id",
    "reportes_reportesemanal.semana",
)


def semana_ya_reportada(practica, semana):
    return ReporteSemanal.objects.filter(practica=practica, semana=semana).exists()


def es_semana_unica(error):
    """¿Este ``IntegrityError`` es la restricción de semana única y no otra?"""
    nombre = getattr(getattr(error.__cause__, "diag", None), "constraint_name", None)
    texto = str(error)
    return (
        nombre == RESTRICCION_SEMANA_UNICA
        or RESTRICCION_SEMANA_UNICA in texto
        or all(columna in texto for columna in COLUMNAS_SEMANA_UNICA)
    )


class ReporteNoEnRevision(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "reporte_no_en_revision"


class ReporteNoDevuelto(APIException):
    """Solo se reenvía lo que el tutor devolvió: «en revisión»/«validado» es 409."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "reporte_no_devuelto"


def _traducir(error, *, clase_estado: type[APIException] = ReporteNoEnRevision):
    """Mapea las claves de ValidationError a excepciones DRF del código HTTP correcto.

    La clave «estado» es la única ambigua: el 409 de ``validar``/``devolver``
    (``reporte_no_en_revision``) y el del reenvío (``reporte_no_devuelto``)
    comparten clave pero no código, así que la vista que traduce elige la clase.
    """
    claves = list(error.message_dict)
    if "practica" in claves:
        raise PracticaNoEnCurso(error.message_dict["practica"][0]) from None
    if "estado" in claves:
        raise clase_estado(error.message_dict["estado"][0]) from None
    if "reporte" in claves:
        raise NotFound(error.message_dict["reporte"][0]) from None
    if "autor" in claves or "tutor" in claves:
        clave = "autor" if "autor" in claves else "tutor"
        raise PermissionDenied(error.message_dict[clave][0]) from None
    if "observacion" in claves:
        raise serializers.ValidationError(error.message_dict) from None
    raise APIException(error.message_dict) from None


MENSAJE_CUERPO_DEVOLVER = "El cuerpo debe ser un objeto JSON con «observacion»."

MENSAJE_PENDIENTES = (
    "Solo el tutor académico puede consultar su cola de reportes pendientes."
)
MENSAJE_REVISION_INFORMES = (
    "Solo el tutor académico puede revisar los informes finales de sus practicantes."
)


class PendienteCardSerializer(serializers.Serializer):
    """Proyección de la cola del tutor: los campos mínimos de decisión."""

    id = serializers.IntegerField()
    practica_id = serializers.IntegerField()
    semana = serializers.IntegerField()
    horas_reportadas = serializers.IntegerField()
    estado = serializers.CharField()


class ObservacionSerializer(serializers.Serializer):
    observacion = serializers.CharField()


class PendienteInformeSerializer(serializers.Serializer):
    """El informe final del estudiante en la cola del tutor, con su ``clave``.

    Los reportes semanales de la cola conservan su tarjeta de cinco campos; el
    informe final se identifica con la clave ``informe-<id>``, que es el mismo
    esquema con el que el demo ya nombraba este pendiente (``informe-<id>``) y no
    choca con ninguna clave existente.
    """

    clave = serializers.CharField()
    id = serializers.IntegerField()
    practica_id = serializers.IntegerField()
    version = serializers.IntegerField()
    estado = serializers.CharField()


def tarjeta_informe(informe):
    """Proyección del informe pendiente, con su clave ``informe-<id>``."""
    return {
        "clave": f"informe-{informe.pk}",
        "id": informe.pk,
        "practica_id": informe.practica_id,
        "version": informe.version,
        "estado": informe.estado,
    }


class ReporteDetalleView(SinFilaEs401, APIView):
    """``GET /api/v1/reportes/{id}/``: lectura de un reporte con su devolución.

    Es la lectura multirrol de S6 y no exige un rol concreto, sino que la
    práctica del reporte esté dentro del alcance de filas de T019
    (``practicas_visibles_para``). Por eso la consulta se acota al ``pk`` pedido
    **y** a ese alcance: un reporte de una práctica ajena responde el mismo 404
    que uno inexistente, sin revelar si existe. La observación sale solo cuando
    el reporte está «devuelto», con el autor y la fecha de su última devolución;
    la vista solo lee.

    C-03 (D7) amplía la lectura con ``actividades``, ``version``, las
    ``evidencias`` de todas las versiones (con su ruta de descarga autenticada) y
    el historial ``devoluciones``; los campos legados no cambian.
    """

    permission_classes = (
        IsAuthenticated,
        PermitirPracticaVisible,
    )

    @extend_schema(
        summary="Consultar un reporte semanal y la observación de su devolución",
        responses={
            200: ReporteDetalleSerializer,
            401: OpenApiResponse(description="Sin actor autenticado."),
            404: OpenApiResponse(
                description=(
                    "El reporte no existe o su práctica está fuera del alcance del "
                    "actor (`no_encontrado`); ambos casos responden igual."
                )
            ),
        },
    )
    def get(self, request, reporte_id):
        reporte = (
            con_detalle(
                ReporteSemanal.objects.filter(
                    practica__in=practicas_visibles_para(request.user)
                )
            )
            .filter(pk=reporte_id)
            .first()
        )
        if reporte is None:
            raise NotFound()
        self.check_object_permissions(request, reporte.practica)
        return Response(ReporteDetalleSerializer(detalle_de(reporte)).data)


class DescargaEvidenciaView(SinFilaEs401, APIView):
    """``GET /api/v1/reportes/{id}/evidencias/{evidencia_id}/``: el PDF (D8, S4).

    Es la única salida del archivo: no hay ``MEDIA_URL`` ni URL pública. La
    evidencia se busca acotada a su reporte **y** a ``practicas_visibles_para``,
    así que la de una práctica ajena, la de otro reporte, una inexistente y una
    cuyo archivo falta o no se puede leer responden el mismo 404. Responde el PDF como adjunto con el nombre original.
    """

    permission_classes = (
        IsAuthenticated,
        PermitirPracticaVisible,
    )

    @extend_schema(
        summary="Descargar una evidencia PDF de un reporte semanal",
        responses={
            (200, "application/pdf"): OpenApiResponse(
                response=OpenApiTypes.BINARY,
                description="El PDF como adjunto, con su nombre original.",
            ),
            401: OpenApiResponse(description="Sin actor autenticado."),
            404: OpenApiResponse(
                description=(
                    "La evidencia no existe, no es de ese reporte o su práctica está "
                    "fuera del alcance del actor (`no_encontrado`); todos responden "
                    "igual."
                )
            ),
        },
    )
    def get(self, request, reporte_id, evidencia_id):
        evidencia = (
            EvidenciaReporte.objects.filter(
                pk=evidencia_id,
                reporte_id=reporte_id,
                reporte__practica__in=practicas_visibles_para(request.user),
            )
            .select_related("reporte__practica")
            .first()
        )
        if evidencia is None:
            raise NotFound()
        self.check_object_permissions(request, evidencia.reporte.practica)
        try:
            archivo = evidencia.archivo.open("rb")
        except OSError:
            # Archivo ausente o ilegible en el almacenamiento: el mismo 404 que
            # una evidencia fuera de alcance, sin revelar que la fila existe.
            raise NotFound() from None
        return FileResponse(
            archivo,
            as_attachment=True,
            filename=evidencia.nombre,
            content_type="application/pdf",
        )


class HorasPracticaSerializer(serializers.Serializer):
    """Proyección de solo lectura de las horas acumuladas de una práctica."""

    horas_validadas = serializers.IntegerField()
    horas_en_revision = serializers.IntegerField()
    horas_requeridas = serializers.IntegerField()
    horas_faltantes = serializers.IntegerField()
    semana_en_revision = serializers.BooleanField()


class PendientesView(APIView):
    """``GET /api/v1/pendientes/``: cola de reportes en revisión del tutor."""

    permission_classes = (
        IsAuthenticated,
        rol_requerido(
            Usuario.Rol.TUTOR_ACADEMICO,
            mensaje=MENSAJE_PENDIENTES,
        ),
    )

    @extend_schema(
        summary="Listar los pendientes de validación: reportes e informes finales",
        responses={
            200: PolymorphicProxySerializer(
                component_name="PendienteCola",
                serializers=[PendienteCardSerializer, PendienteInformeSerializer],
                resource_type_field_name=None,
                many=True,
            ),
            401: OpenApiResponse(description="Sin actor autenticado."),
            403: OpenApiResponse(description="El actor no es tutor académico."),
        },
    )
    def get(self, request):

        consulta = (
            ReporteSemanal.objects.filter(
                estado=ReporteSemanal.Estado.EN_REVISION,
                practica__estado=Practica.Estado.EN_CURSO,
                practica__asignaciones_tutor__tutor_academico=request.user,
                practica__asignaciones_tutor__hasta__isnull=True,
            )
            .order_by("-fecha_registro")
            .values("id", "practica_id", "semana", "horas_reportadas", "estado")
        )
        informes = (
            InformeEstudiante.objects.filter(
                estado=InformeEstudiante.Estado.EN_REVISION,
                practica__asignaciones_tutor__tutor_academico=request.user,
                practica__asignaciones_tutor__hasta__isnull=True,
            )
            .order_by("-fecha")
            .only("pk", "practica_id", "version", "estado")
        )
        # La cola del tutor suma los informes finales del estudiante (RF-16) a los
        # reportes semanales: las tarjetas de reporte conservan sus cinco campos y
        # el informe llega con su clave `informe-<id>`, sin tocar las anteriores.
        return Response([*consulta, *(tarjeta_informe(fila) for fila in informes)])


class ValidarReporteView(APIView):
    """``POST /api/v1/reportes/{id}/validar/``: marca el reporte «validado»."""

    permission_classes = (
        IsAuthenticated,
        rol_requerido(
            Usuario.Rol.TUTOR_ACADEMICO,
            mensaje=MENSAJE_TUTOR,
        ),
    )

    @extend_schema(
        summary="Validar un reporte semanal",
        request=None,
        responses={
            200: PendienteCardSerializer,
            401: OpenApiResponse(description="Sin actor autenticado."),
            403: OpenApiResponse(description="El actor no es tutor académico."),
            404: OpenApiResponse(description="Reporte inexistente o fuera de alcance."),
            409: OpenApiResponse(
                description=(
                    "El reporte no está «en revisión» (`reporte_no_en_revision`) o "
                    "la práctica no está en curso (`practica_no_en_curso`)."
                )
            ),
        },
    )
    def post(self, request, reporte_id):
        reporte = ReporteSemanal.objects.filter(
            pk=reporte_id,
            practica__asignaciones_tutor__tutor_academico=request.user,
            practica__asignaciones_tutor__hasta__isnull=True,
        ).first()
        if reporte is None:
            raise NotFound("Reporte inexistente.")
        try:
            reporte = validar_reporte(reporte=reporte, autor=request.user)
        except DjangoValidationError as error:
            _traducir(error)
        return Response(
            {
                "id": reporte.pk,
                "practica_id": reporte.practica_id,
                "semana": reporte.semana,
                "horas_reportadas": reporte.horas_reportadas,
                "estado": reporte.estado,
            }
        )


class DevolverReporteView(APIView):
    """``POST /api/v1/reportes/{id}/devolver/``: devolución con observación."""

    permission_classes = (
        IsAuthenticated,
        rol_requerido(
            Usuario.Rol.TUTOR_ACADEMICO,
            mensaje=MENSAJE_TUTOR,
        ),
    )

    @extend_schema(
        summary="Devolver un reporte semanal con observación",
        request=ObservacionSerializer,
        responses={
            200: PendienteCardSerializer,
            400: OpenApiResponse(
                description="Observación obligatoria o cuerpo que no es objeto."
            ),
            401: OpenApiResponse(description="Sin actor autenticado."),
            403: OpenApiResponse(description="El actor no es tutor académico."),
            404: OpenApiResponse(description="Reporte inexistente o fuera de alcance."),
            409: OpenApiResponse(
                description=(
                    "El reporte no está «en revisión» (`reporte_no_en_revision`) o "
                    "la práctica no está en curso (`practica_no_en_curso`)."
                )
            ),
        },
    )
    def post(self, request, reporte_id):
        if not isinstance(request.data, Mapping):
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: [MENSAJE_CUERPO_DEVOLVER]}
            )
        observacion = request.data.get("observacion")
        reporte = ReporteSemanal.objects.filter(
            pk=reporte_id,
            practica__asignaciones_tutor__tutor_academico=request.user,
            practica__asignaciones_tutor__hasta__isnull=True,
        ).first()
        if reporte is None:
            raise NotFound("Reporte inexistente.")
        try:
            reporte = devolver_reporte(
                reporte=reporte,
                autor=request.user,
                observacion=observacion,
            )
        except DjangoValidationError as error:
            _traducir(error)
        return Response(
            {
                "id": reporte.pk,
                "practica_id": reporte.practica_id,
                "semana": reporte.semana,
                "horas_reportadas": reporte.horas_reportadas,
                "estado": reporte.estado,
            }
        )


class ReenviarReporteView(SinFilaEs401, APIView):
    """``POST /api/v1/reportes/{id}/reenviar/``: «devuelto» -> «en revisión».

    Solo el estudiante de la práctica reenvía (#124, S8). El reporte se busca
    acotado a sus prácticas —``practica__estudiante_id``—, así que el de otro
    estudiante responde el mismo 404 que un id inexistente: la respuesta no
    revela si el reporte existe. Es la misma fila, sin ``version`` y sin escribir
    ``Validacion`` (eso es validar, no reenviar).

    C-03 (D5): un cuerpo ``multipart/form-data`` con ``evidencias`` guarda los
    PDFs como la versión siguiente en ``EvidenciaReporte``; se validan antes de
    escribir y un rechazo no deja filas ni archivos.
    """

    permission_classes = (
        rol_requerido(Usuario.Rol.ESTUDIANTE, mensaje=MENSAJE_ESTUDIANTE),
    )

    @extend_schema(
        summary="Reenviar un reporte semanal devuelto",
        description=(
            "Sin cuerpo: el reenvío legado. `multipart/form-data` con `evidencias` "
            "(uno o más PDF de hasta 5 MB) las guarda como la versión siguiente; "
            "las anteriores y la observación del tutor se conservan."
        ),
        request={
            "multipart/form-data": ReenvioConEvidenciasSerializer,
            "application/json": {
                "type": "object",
                "description": "Reenvío legado: cuerpo vacío.",
            },
        },
        responses={
            200: PendienteCardSerializer,
            400: OpenApiResponse(
                description=(
                    "Multipart sin evidencias o con un archivo que no es PDF o "
                    "supera 5 MB; no se escribe nada."
                )
            ),
            401: OpenApiResponse(description="Sin actor autenticado."),
            403: OpenApiResponse(description="El actor no es estudiante."),
            404: OpenApiResponse(description="Reporte inexistente o fuera de alcance."),
            409: OpenApiResponse(
                description=(
                    "El reporte no está «devuelto» (`reporte_no_devuelto`): solo se "
                    "reenvía después de una devolución; o la práctica no está en "
                    "curso (`practica_no_en_curso`)."
                )
            ),
        },
    )
    def post(self, request, reporte_id):
        actor = actor_estudiante(request.user)
        reporte = ReporteSemanal.objects.filter(
            pk=reporte_id,
            practica__estudiante_id=actor.pk,
        ).first()
        if reporte is None:
            raise NotFound("Reporte inexistente.")
        evidencias = []
        if es_multipart(request):
            # C-03 (D5): PDFs nuevos opcionales, validados antes de escribir.
            entrada = ReenvioConEvidenciasSerializer(data=request.data)
            entrada.is_valid(raise_exception=True)
            evidencias = entrada.validated_data["evidencias"]
        with evidencias_atomicas() as guardadas:
            try:
                reporte = reenviar_reporte(
                    reporte=reporte,
                    autor=actor,
                    evidencias=evidencias,
                    guardadas=guardadas,
                )
            except DjangoValidationError as error:
                _traducir(error, clase_estado=ReporteNoDevuelto)
        return Response(
            {
                "id": reporte.pk,
                "practica_id": reporte.practica_id,
                "semana": reporte.semana,
                "horas_reportadas": reporte.horas_reportadas,
                "estado": reporte.estado,
            }
        )


class HorasPracticaView(SinFilaEs401, APIView):
    """``GET /api/v1/practicas/{id}/horas/``: horas acumuladas de la práctica.

    Es una lectura multirrol: no exige un rol concreto, sino que la práctica esté
    dentro del alcance de filas de T019 del actor (``practicas_visibles_para``).
    Por eso el estudiante solo alcanza la suya, el tutor académico las asignadas
    activas y los roles con carrera las de su carrera. La consulta se acota al
    ``pk`` pedido y una práctica fuera de alcance responde el mismo 404 que una
    inexistente, sin revelar si existe. No escribe nada: el cálculo se hace sobre
    los reportes guardados.
    """

    permission_classes = (
        IsAuthenticated,
        PermitirPracticaVisible,
    )

    @extend_schema(
        summary="Consultar las horas acumuladas de una práctica",
        responses={
            200: HorasPracticaSerializer,
            401: OpenApiResponse(description="Sin actor autenticado."),
            404: OpenApiResponse(
                description=(
                    "La práctica no existe o está fuera del alcance del actor "
                    "(`no_encontrado`); ambos casos responden igual."
                )
            ),
        },
    )
    def get(self, request, practica_id):
        practica = practicas_visibles_para(request.user).filter(pk=practica_id).first()
        if practica is None:
            raise NotFound()
        self.check_object_permissions(request, practica)
        return Response(horas_practica(practica))


class ConfirmacionDuplicada(APIException):
    """El reporte ya tiene la confirmación de su tutor de entidad (HU-07).

    El servicio rechaza la segunda confirmación y la ``UniqueConstraint`` de
    ``ConfirmacionEntidad`` la respalda en la base: la máquina del cliente decide
    por ``confirmacion_duplicada``, no por el texto.
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = MENSAJE_CONFIRMACION_DUPLICADA
    default_code = "confirmacion_duplicada"


class ConfirmacionEntidadSerializer(serializers.Serializer):
    """Proyección de la confirmación: quién la hizo y cuándo (HU-07 caso 2)."""

    id = serializers.IntegerField(read_only=True)
    reporte_id = serializers.IntegerField(read_only=True)
    tutor_entidad_id = serializers.IntegerField(read_only=True)
    fecha = serializers.DateTimeField(read_only=True)


CLAVES_DE_CONFIRMACION = frozenset({"confirmacion", "reporte", "autor"})


def _traducir_confirmacion(error) -> NoReturn:
    """Traduce el ``ValidationError`` del dominio por claves, nunca por su texto.

    La clave ``confirmacion`` es el 409 del duplicado, ``reporte`` el 404 de una
    fila inexistente y ``autor`` el 403 del tutor de entidad ajeno. Cualquier otra
    clave es un cambio de dominio no previsto y falla cerrado con el 500 del
    contrato, sin publicar el mensaje del dominio.
    """
    mensajes = error.message_dict
    if set(mensajes) - CLAVES_DE_CONFIRMACION:
        raise APIException(mensajes) from None
    if "confirmacion" in mensajes:
        raise ConfirmacionDuplicada(mensajes["confirmacion"][0]) from None
    if "reporte" in mensajes:
        raise NotFound(mensajes["reporte"][0]) from None
    if "autor" in mensajes:
        raise PermissionDenied(mensajes["autor"][0]) from None
    raise APIException(mensajes) from None


class ConfirmarReporteEntidadView(SinFilaEs401, APIView):
    """``POST /api/v1/reportes/{id}/confirmacion/``: confirmación de la entidad.

    El rol ``tutor_entidad`` se comprueba en ``initial()``, antes de mirar el
    reporte: un rol ajeno recibe 403 aunque el id no exista. La fila se busca por
    ``pk`` sin acotar al alcance de lectura porque el contrato de HU-07 caso 3
    distingue la práctica **ajena** (403) de la **inexistente** (404); el permiso
    real lo decide el servicio contra el ``tutor_entidad`` guardado de la
    práctica. La vista no escribe: delega en ``confirmar_reporte``, que tampoco
    cambia el estado del reporte ni el de la práctica (S9).
    """

    permission_classes = (
        rol_requerido(
            Usuario.Rol.TUTOR_ENTIDAD,
            mensaje=MENSAJE_TUTOR_ENTIDAD_CONFIRMACION,
        ),
    )

    @extend_schema(
        summary="Confirmar un reporte semanal como tutor de entidad",
        request=None,
        responses={
            200: ConfirmacionEntidadSerializer,
            401: OpenApiResponse(
                description="Sin actor autenticado (`no_autenticado`)."
            ),
            403: OpenApiResponse(
                description=(
                    "El actor no es tutor de entidad (`permiso_denegado`), o no es "
                    "el tutor de entidad de la práctica laboral del reporte."
                )
            ),
            404: OpenApiResponse(description="Reporte inexistente (`no_encontrado`)."),
            409: OpenApiResponse(
                description=(
                    "El reporte ya tiene la confirmación de la entidad "
                    "(`confirmacion_duplicada`)."
                )
            ),
        },
    )
    def post(self, request, reporte_id):
        reporte = ReporteSemanal.objects.filter(pk=reporte_id).first()
        if reporte is None:
            raise NotFound("Reporte inexistente.")
        try:
            confirmacion = confirmar_reporte(reporte=reporte, autor=request.user)
        except DjangoValidationError as error:
            _traducir_confirmacion(error)
        return Response(ConfirmacionEntidadSerializer(confirmacion).data)


class InformeNoEnRevision(APIException):
    """El informe del estudiante ya no está «en revisión»: la decisión es 409."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "informe_no_en_revision"


class DecisionInformeSinTraduccion(APIException):
    """Clave de dominio no prevista: 500 de fallo cerrado, sin su mensaje."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Ocurrió un error inesperado."
    default_code = "error_interno"


CLAVES_DE_DECISION_INFORME = frozenset({"informe", "autor", "estado", "observacion"})


def _traducir_decision_informe(error) -> NoReturn:
    """Traduce el ``ValidationError`` del informe por claves, nunca por su texto.

    ``estado`` es el 409 de un informe que ya no está «en revisión», ``informe``
    el 404 de una fila inexistente, ``autor`` el 403 del tutor ajeno y
    ``observacion`` el 400 de la devolución sin observación. Cualquier otra clave
    es un cambio de dominio no previsto: falla cerrado con el 500 del contrato.
    """
    mensajes = error.message_dict
    if set(mensajes) - CLAVES_DE_DECISION_INFORME:
        raise DecisionInformeSinTraduccion() from None
    if "estado" in mensajes:
        raise InformeNoEnRevision(mensajes["estado"][0]) from None
    if "informe" in mensajes:
        raise NotFound(mensajes["informe"][0]) from None
    if "autor" in mensajes:
        raise PermissionDenied(mensajes["autor"][0]) from None
    if "observacion" in mensajes:
        raise serializers.ValidationError(mensajes) from None
    raise DecisionInformeSinTraduccion() from None


class ValidarInformeEstudianteView(APIView):
    """``POST /api/v1/informes-estudiante/{id}/validar/``: C-04 sobre el informe.

    Es la decisión del tutor académico sobre el informe final del estudiante
    (HU-10 caso 2). El rol se comprueba en ``initial()`` y la fila se busca por
    ``pk`` **sin** acotar al alcance de lectura, para que el servicio distinga el
    permiso (403, el tutor no es el de esa práctica) del 404 del informe
    inexistente; la regla vive en el servicio y la vista solo la traduce. No
    cambia ``Practica.estado`` ni escribe historial (P-05 abierta).
    """

    permission_classes = (
        IsAuthenticated,
        rol_requerido(Usuario.Rol.TUTOR_ACADEMICO, mensaje=MENSAJE_REVISION_INFORMES),
    )

    @extend_schema(
        summary="Validar el informe final del estudiante",
        request=None,
        responses={
            200: PendienteInformeSerializer,
            401: OpenApiResponse(description="Sin actor autenticado."),
            403: OpenApiResponse(
                description="El actor no es tutor académico, o no es el de esa práctica."
            ),
            404: OpenApiResponse(description="Informe inexistente (`no_encontrado`)."),
            409: OpenApiResponse(
                description="El informe no está «en revisión» (`informe_no_en_revision`)."
            ),
        },
    )
    def post(self, request, informe_id):
        informe = InformeEstudiante.objects.filter(pk=informe_id).first()
        if informe is None:
            raise NotFound()
        try:
            informe = validar_informe_estudiante(informe=informe, autor=request.user)
        except DjangoValidationError as error:
            _traducir_decision_informe(error)
        return Response(PendienteInformeSerializer(tarjeta_informe(informe)).data)


class DevolverInformeEstudianteView(APIView):
    """``POST /api/v1/informes-estudiante/{id}/devolver/``: devolución con observación.

    La devolución exige observación (C-04, HU-10 caso 2) y es **solo de estado**:
    deja el informe «devuelto» para que el estudiante lo corrija y lo reenvíe, y
    no cambia ``Practica.estado`` ni habilita el cierre. El permiso y el 404 se
    resuelven igual que en la validación.
    """

    permission_classes = (
        IsAuthenticated,
        rol_requerido(Usuario.Rol.TUTOR_ACADEMICO, mensaje=MENSAJE_REVISION_INFORMES),
    )

    @extend_schema(
        summary="Devolver el informe final del estudiante con observación",
        request=ObservacionSerializer,
        responses={
            200: PendienteInformeSerializer,
            400: OpenApiResponse(description="Observación obligatoria."),
            401: OpenApiResponse(description="Sin actor autenticado."),
            403: OpenApiResponse(
                description="El actor no es tutor académico, o no es el de esa práctica."
            ),
            404: OpenApiResponse(description="Informe inexistente (`no_encontrado`)."),
            409: OpenApiResponse(
                description="El informe no está «en revisión» (`informe_no_en_revision`)."
            ),
        },
    )
    def post(self, request, informe_id):
        observacion = (request.data or {}).get("observacion")
        informe = InformeEstudiante.objects.filter(pk=informe_id).first()
        if informe is None:
            raise NotFound()
        try:
            informe = devolver_informe_estudiante(
                informe=informe, autor=request.user, observacion=observacion
            )
        except DjangoValidationError as error:
            _traducir_decision_informe(error)
        return Response(PendienteInformeSerializer(tarjeta_informe(informe)).data)
