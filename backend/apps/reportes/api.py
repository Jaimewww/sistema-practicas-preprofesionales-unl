"""Endpoints del tutor académico para validar/devolver reportes (RF-03, #122).

``GET /api/v1/pendientes/`` lista los reportes en revisión de las prácticas
asignadas al tutor activo. ``POST /api/v1/reportes/{id}/validar/`` marca el
reporte «validado» y registra la ``Validacion``. ``POST
/api/v1/reportes/{id}/devolver/`` lo marca «devuelto» con observación
obligatoria. Todos responden con el envelope de #77 y fail-closed: sin token
401, rol ajeno 403, reporte fuera de ``en_revision`` 409
(``reporte_no_en_revision``) y práctica que no está en curso 409
(``practica_no_en_curso``, CU-01 2b). La cola lista solo prácticas en curso.
"""

from collections.abc import Mapping

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
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

from apps.practicas.models import Practica
from apps.reportes.models import MENSAJE_SEMANA_DUPLICADA, ReporteSemanal
from apps.reportes.serializers import ReporteSemanalSerializer
from apps.reportes.services import (
    MENSAJE_TUTOR,
    devolver_reporte,
    validar_reporte,
)
from apps.seguridad.permissions import (
    PermitirPracticaVisible,
    SinFilaEs401,
    rol_requerido,
)
from apps.usuarios.models import Usuario

MENSAJE_ACTOR = "Solo el estudiante de la práctica puede registrar sus reportes semanales."


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


class ReportePracticaView(SinFilaEs401, APIView):
    """Registra el reporte semanal de la práctica; solo su propio estudiante."""

    # #79: permiso de rol (solo estudiante registra reportes) y de objeto con el
    # alcance de T019; los chequeos explícitos de abajo quedan como segunda
    # barrera (D5, defensa en profundidad).
    permission_classes = [
        rol_requerido(Usuario.Rol.ESTUDIANTE, mensaje=MENSAJE_ACTOR),
        PermitirPracticaVisible,
    ]

    @extend_schema(
        summary="Registrar el reporte semanal de una práctica",
        request=ReporteSemanalSerializer,
        responses={
            201: ReporteSemanalSerializer,
            400: OpenApiResponse(
                description=(
                    "Validación de la entrada: cuerpo que no es objeto, campo no "
                    "admitido, semana u horas inválidas (máximo 168 por semana) o "
                    "ayudantía con más de 10 horas."
                )
            ),
            401: OpenApiResponse(description="Sin actor autenticado (`no_autenticado`)."),
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
        with transaction.atomic():
            practica = (
                Practica.objects.select_for_update()
                .filter(pk=practica_id, estudiante_id=actor.pk)
                .first()
            )
            if practica is None:
                raise NotFound()
            self.check_object_permissions(request, practica)
            if practica.estado != Practica.Estado.EN_CURSO:
                raise PracticaNoEnCurso(MENSAJE_NO_EN_CURSO.format(estado=practica.estado))
            serializer = ReporteSemanalSerializer(
                data=request.data, context={"practica": practica}
            )
            serializer.is_valid(raise_exception=True)
            if semana_ya_reportada(practica, serializer.validated_data["semana"]):
                raise SemanaDuplicada()
            try:
                with transaction.atomic():
                    reporte = serializer.save(practica=practica)
            except IntegrityError as error:
                if not es_semana_unica(error):
                    raise
                raise SemanaDuplicada() from None
        return Response(
            ReporteSemanalSerializer(reporte).data, status=status.HTTP_201_CREATED
        )

MENSAJE_NO_EN_CURSO = (
    "La práctica está en «{estado}»: solo una práctica en curso admite reportes semanales."
)

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


def _traducir(error):
    """Mapea las claves de ValidationError a excepciones DRF del código HTTP correcto."""
    claves = list(error.message_dict)
    if "practica" in claves:
        raise PracticaNoEnCurso(error.message_dict["practica"][0]) from None
    if "estado" in claves:
        raise ReporteNoEnRevision(error.message_dict["estado"][0]) from None
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


class PendienteCardSerializer(serializers.Serializer):
    """Proyección de la cola del tutor: los campos mínimos de decisión."""

    id = serializers.IntegerField()
    practica_id = serializers.IntegerField()
    semana = serializers.IntegerField()
    horas_reportadas = serializers.IntegerField()
    estado = serializers.CharField()


class ObservacionSerializer(serializers.Serializer):
    observacion = serializers.CharField()


class PendientesView(APIView):
    """``GET /api/v1/pendientes/``: cola de reportes en revisión del tutor."""

    permission_classes = [IsAuthenticated, rol_requerido(
        Usuario.Rol.TUTOR_ACADEMICO, mensaje=MENSAJE_PENDIENTES,
    )]

    @extend_schema(
        summary="Listar los reportes pendientes de validación",
        responses={
            200: PendienteCardSerializer(many=True),
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
        return Response(list(consulta))


class ValidarReporteView(APIView):
    """``POST /api/v1/reportes/{id}/validar/``: marca el reporte «validado»."""

    permission_classes = [IsAuthenticated, rol_requerido(
        Usuario.Rol.TUTOR_ACADEMICO, mensaje=MENSAJE_TUTOR,
    )]

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
        return Response({
            "id": reporte.pk, "practica_id": reporte.practica_id,
            "semana": reporte.semana, "horas_reportadas": reporte.horas_reportadas,
            "estado": reporte.estado,
        })


class DevolverReporteView(APIView):
    """``POST /api/v1/reportes/{id}/devolver/``: devolución con observación."""

    permission_classes = [IsAuthenticated, rol_requerido(
        Usuario.Rol.TUTOR_ACADEMICO, mensaje=MENSAJE_TUTOR,
    )]

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
                reporte=reporte, autor=request.user, observacion=observacion,
            )
        except DjangoValidationError as error:
            _traducir(error)
        return Response({
            "id": reporte.pk, "practica_id": reporte.practica_id,
            "semana": reporte.semana, "horas_reportadas": reporte.horas_reportadas,
            "estado": reporte.estado,
        })
