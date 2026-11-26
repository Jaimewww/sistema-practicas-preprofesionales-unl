"""API JSON de alertas activas (T18, C-05).

``GET /api/v1/alertas/`` expone de solo lectura las alertas activas que le
corresponden al actor autenticado. El alcance no lo decide la vista: lo aporta
``alertas_visibles_para`` (T17), que relee el rol guardado y cruza el alcance de
filas con los destinatarios por tipo. La vista solo exige JWT; sin actor
autenticado la respuesta es 401 y con un actor sin alertas correspondientes,
200 con lista vacía. No escribe, no atiende alertas ni acepta encabezados del
prototipo.
"""

from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework.fields import CharField, DateField, IntegerField
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.alertas.consultas import alertas_visibles_para


class AlertasView(APIView):
    """``GET /api/v1/alertas/``: alertas activas visibles para el actor."""

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Listar las alertas activas del actor autenticado",
        responses={
            200: inline_serializer(
                "AlertaActivaCard",
                fields={
                    "id": IntegerField(),
                    "tipo": CharField(),
                    "practica_id": IntegerField(),
                    "fecha": DateField(),
                },
                many=True,
            ),
            401: OpenApiResponse(description="Sin actor autenticado (JWT requerido)."),
        },
    )
    def get(self, request):
        consulta = alertas_visibles_para(request.user).values(
            "id", "tipo", "practica_id", "fecha"
        )
        return Response(list(consulta))
