# pyright: reportMissingImports=false
"""Endpoints del plan de actividades (S8, HU-01, RF-01, RF-03) sobre los servicios de T024.

``GET /api/v1/practicas/{id}/plan/`` lista las versiones del plan de una práctica
visible (``practicas_visibles_para``), de la más nueva a la más antigua.
``POST /api/v1/practicas/{id}/plan/`` envía el plan o, tras una devolución, la
versión siguiente; solo el estudiante de la práctica. ``POST
/api/v1/planes/{id}/aprobar/`` y ``…/devolver/`` los decide solo el tutor
académico con asignación activa; aprobar pasa la práctica a «en curso».

Fail-closed y en el envelope de #77: sin token o cuenta inactiva 401, rol ajeno
403, práctica o plan fuera de alcance el mismo 404 que lo inexistente, cuerpo
inválido 400 y estado que no admite la acción 409 con código de máquina:
``practica_no_admite_plan`` (la práctica no está asignada ni en curso),
``plan_no_reenviable`` (la última versión está en revisión o aprobada) y
``plan_no_en_revision`` (el plan ya se decidió). Primero el permiso, después el
estado; un rechazo no escribe nada.

La guarda de la práctica es de la vista: el servicio solo rechaza el envío en un
estado final, y al aprobar una práctica suspendida responde con la clave «autor»
del coordinador (sería un 403 engañoso para el tutor asignado) y en «en revisión
final» recorrería la arista de vuelta a «en curso».

Bloqueos: el envío bloquea solo la práctica (``select_for_update``) y lee los
planes sin bloquearlos, así que nunca espera por una fila de plan; inserta la
versión nueva bajo ese bloqueo. Aprobar y devolver bloquean el plan y después la
práctica, como ``aprobar_plan``/``devolver_plan``. Solo las decisiones esperan con
una fila tomada (el plan, por la práctica) y el envío no espera por planes, así que
no hay ciclo de espera entre las tres escrituras.
"""

from collections.abc import Mapping

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from apps.actividades.models import MENSAJE_OBSERVACION, PlanActividades
from apps.actividades.serializers import (
    MENSAJE_CAMPO_NO_ADMITIDO_DEVOLVER,
    MENSAJE_CUERPO_PLAN,
    EnvioPlanSerializer,
    PlanActividadesSerializer,
)
from apps.actividades.services import (
    MENSAJE_ESTUDIANTE,
    MENSAJE_TUTOR,
    aprobar_plan,
    devolver_plan,
    enviar_plan,
)
from apps.practicas.models import AsignacionTutor, Practica
from apps.seguridad.permissions import (
    PermitirPracticaVisible,
    SinFilaEs401,
    rol_requerido,
)
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import practicas_visibles_para

__all__ = ["MENSAJE_CUERPO_DEVOLVER", "MENSAJE_CUERPO_PLAN"]

MENSAJE_CUERPO_DEVOLVER = "El cuerpo debe ser un objeto JSON con «observacion»."
MENSAJE_PRACTICA_NO_ADMITE_PLAN = (
    "La práctica está en «{estado}»: el plan de actividades solo se envía, aprueba "
    "o devuelve con la práctica asignada o en curso."
)
ESTADOS_CON_PLAN = frozenset({Practica.Estado.ASIGNADA, Practica.Estado.EN_CURSO})

SoloEstudiante = rol_requerido(Usuario.Rol.ESTUDIANTE, mensaje=MENSAJE_ESTUDIANTE)
SoloTutorAcademico = rol_requerido(Usuario.Rol.TUTOR_ACADEMICO, mensaje=MENSAJE_TUTOR)


class PracticaNoAdmitePlan(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "practica_no_admite_plan"


class PlanNoReenviable(APIException):
    """La versión siguiente solo nace tras una devolución (data-model.md)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "plan_no_reenviable"


class PlanNoEnRevision(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "plan_no_en_revision"


def _exigir_practica_con_plan(practica):
    if practica.estado not in ESTADOS_CON_PLAN:
        raise PracticaNoAdmitePlan(
            MENSAJE_PRACTICA_NO_ADMITE_PLAN.format(estado=practica.estado)
        )


def _traducir(error, *, clase_estado):
    """Mapea las claves de ``ValidationError`` del servicio a excepciones DRF.

    La clave «estado» es la única ambigua: en el envío es la última versión que no
    admite reenvío y al decidir es el plan que ya no está en revisión, así que la
    vista que traduce elige la clase. La práctica en estado final ya la rechazó la
    guarda de la vista, con la fila bloqueada.
    """
    claves = error.message_dict
    if "estado" in claves:
        raise clase_estado(claves["estado"][0]) from None
    if "autor" in claves:
        raise PermissionDenied(claves["autor"][0]) from None
    if "plan" in claves or "practica" in claves:
        raise NotFound() from None
    if "observacion" in claves or "contenido" in claves:
        raise serializers.ValidationError(claves) from None
    raise APIException(claves) from None


def _planes_de(practica):
    return (
        PlanActividades.objects.filter(practica=practica)
        .prefetch_related("validaciones")
        .order_by("-version")
    )


def _proyectar(plan):
    """Relee el plan con sus validaciones para la respuesta de la escritura."""
    plan = PlanActividades.objects.prefetch_related("validaciones").get(pk=plan.pk)
    return PlanActividadesSerializer(plan).data


class PlanPracticaView(SinFilaEs401, APIView):
    """``GET``/``POST /api/v1/practicas/{id}/plan/``: versiones y envío del plan."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [SoloEstudiante(), PermitirPracticaVisible()]
        return [PermitirPracticaVisible()]

    @extend_schema(
        summary="Listar las versiones del plan de actividades de una práctica",
        responses={
            200: PlanActividadesSerializer(many=True),
            401: OpenApiResponse(description="Sin actor autenticado (`no_autenticado`)."),
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
        return Response(PlanActividadesSerializer(_planes_de(practica), many=True).data)

    @extend_schema(
        summary="Enviar el plan de actividades (o su versión siguiente)",
        request=EnvioPlanSerializer,
        responses={
            201: PlanActividadesSerializer,
            400: OpenApiResponse(
                description=(
                    "Cuerpo que no es objeto, campo no admitido o `contenido` "
                    "ausente o vacío."
                )
            ),
            401: OpenApiResponse(description="Sin actor autenticado (`no_autenticado`)."),
            403: OpenApiResponse(description="El actor no es estudiante (`permiso_denegado`)."),
            404: OpenApiResponse(
                description=(
                    "La práctica no existe o es de otro estudiante (`no_encontrado`); "
                    "ambos casos responden igual."
                )
            ),
            409: OpenApiResponse(
                description=(
                    "La práctica no está asignada ni en curso "
                    "(`practica_no_admite_plan`) o la última versión está en "
                    "revisión o aprobada (`plan_no_reenviable`)."
                )
            ),
        },
    )
    def post(self, request, practica_id):
        with transaction.atomic():
            practica = (
                Practica.objects.select_for_update()
                .filter(pk=practica_id, estudiante_id=request.user.pk)
                .first()
            )
            if practica is None:
                raise NotFound()
            self.check_object_permissions(request, practica)
            _exigir_practica_con_plan(practica)
            serializer = EnvioPlanSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                plan = enviar_plan(
                    practica=practica,
                    contenido=serializer.validated_data["contenido"],
                    autor=request.user,
                )
            except DjangoValidationError as error:
                _traducir(error, clase_estado=PlanNoReenviable)
                raise
        return Response(_proyectar(plan), status=status.HTTP_201_CREATED)


def _plan_del_tutor_bloqueado(plan_id, tutor):
    """Plan de una práctica con asignación activa del tutor, con las filas bloqueadas.

    Fuera de alcance es el mismo 404 que inexistente. Se bloquea el plan y después
    la práctica, el mismo orden que ``aprobar_plan``/``devolver_plan``; el envío solo
    bloquea la práctica y no espera por planes, así que no se forma un ciclo.
    """
    asignadas = AsignacionTutor.objects.filter(
        tutor_academico_id=tutor.pk, hasta__isnull=True
    ).values("practica_id")
    plan = (
        PlanActividades.objects.select_for_update()
        .filter(pk=plan_id, practica_id__in=asignadas)
        .first()
    )
    if plan is None:
        raise NotFound()
    practica = Practica.objects.select_for_update().get(pk=plan.practica_id)
    return plan, practica


RESPUESTAS_DECISION = {
    200: PlanActividadesSerializer,
    401: OpenApiResponse(
        description="Sin actor autenticado o cuenta inactiva (`no_autenticado`)."
    ),
    403: OpenApiResponse(description="El actor no es tutor académico (`permiso_denegado`)."),
    404: OpenApiResponse(
        description=(
            "El plan no existe o no es de una práctica asignada al tutor "
            "(`no_encontrado`); ambos casos responden igual."
        )
    ),
    409: OpenApiResponse(
        description=(
            "La práctica no está asignada ni en curso (`practica_no_admite_plan`) "
            "o el plan no está en revisión (`plan_no_en_revision`)."
        )
    ),
}


class AprobarPlanView(SinFilaEs401, APIView):
    """``POST /api/v1/planes/{id}/aprobar/``: plan aprobado y práctica en curso."""

    permission_classes = (SoloTutorAcademico,)

    @extend_schema(
        summary="Aprobar un plan de actividades",
        request=None,
        responses=RESPUESTAS_DECISION,
    )
    def post(self, request, plan_id):
        with transaction.atomic():
            plan, practica = _plan_del_tutor_bloqueado(plan_id, request.user)
            _exigir_practica_con_plan(practica)
            try:
                plan = aprobar_plan(plan=plan, autor=request.user)
            except DjangoValidationError as error:
                _traducir(error, clase_estado=PlanNoEnRevision)
        return Response(_proyectar(plan))


class ObservacionPlanSerializer(serializers.Serializer):
    observacion = serializers.CharField()


class DevolverPlanView(SinFilaEs401, APIView):
    """``POST /api/v1/planes/{id}/devolver/``: devolución con observación obligatoria.

    El cuerpo es exactamente ``{"observacion": …}``: un campo de más es un 400
    (``{campo: [MENSAJE_CAMPO_NO_ADMITIDO_DEVOLVER]}``), como en el envío; nunca se
    ignora.
    """

    permission_classes = (SoloTutorAcademico,)

    @extend_schema(
        summary="Devolver un plan de actividades con observación",
        request=ObservacionPlanSerializer,
        responses={
            **RESPUESTAS_DECISION,
            400: OpenApiResponse(
                description=(
                    "Cuerpo que no es objeto, campo no admitido u observación "
                    "ausente o vacía."
                )
            ),
        },
    )
    def post(self, request, plan_id):
        if not isinstance(request.data, Mapping):
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: [MENSAJE_CUERPO_DEVOLVER]}
            )
        observacion = request.data.get("observacion")
        with transaction.atomic():
            plan, practica = _plan_del_tutor_bloqueado(plan_id, request.user)
            sobrantes = sorted(set(request.data) - {"observacion"})
            if sobrantes:
                raise serializers.ValidationError(
                    {campo: [MENSAJE_CAMPO_NO_ADMITIDO_DEVOLVER] for campo in sobrantes}
                )
            if not isinstance(observacion, str) or not observacion.strip():
                raise serializers.ValidationError({"observacion": [MENSAJE_OBSERVACION]})
            _exigir_practica_con_plan(practica)
            try:
                plan = devolver_plan(plan=plan, autor=request.user, observacion=observacion)
            except DjangoValidationError as error:
                _traducir(error, clase_estado=PlanNoEnRevision)
        return Response(_proyectar(plan))
