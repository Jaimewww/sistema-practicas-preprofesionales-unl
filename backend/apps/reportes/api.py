"""Endpoint de registro del reporte semanal (S2-S5, #78).

``POST /api/v1/practicas/{id}/reportes/`` es el único camino de escritura de esta
unidad y decide en este orden, sin escribir nada hasta el final: la práctica debe
existir (404), el actor debe ser el estudiante guardado de la propia práctica
(400 en ``actor``; validar es de la unidad de validación del tutor), la práctica
no puede estar en un estado final (400 con el mensaje de T017) y por último valida
el serializer (400). El envelope y los códigos de error vienen de #77.

S5: la ayudantía con más de 10 horas se rechaza con el mensaje del Art. 341 (lo
hace el serializer). La práctica laboral o comunitaria con más de 40 horas **se
acepta**: el data-model dice que «se identifica para revisión del tutor» y ese
señalamiento no se construye en esta unidad (ver README).
"""

from django.db import IntegrityError, transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.practicas.models import Practica
from apps.practicas.services import ESTADOS_FINALES, MENSAJE_TERMINAL
from apps.reportes.models import MENSAJE_SEMANA_DUPLICADA
from apps.reportes.serializers import ReporteSemanalSerializer
from apps.usuarios.models import Usuario

MENSAJE_ACTOR = "Solo el estudiante de la práctica puede registrar sus reportes semanales."
MENSAJE_ACTOR_INVALIDO = "El actor debe ser un usuario guardado y activo."
MENSAJE_PRACTICA = "La práctica indicada no existe."

# Proyección documental del cuerpo del POST: los dos campos que escribe el cliente.
# La validación real la hace ``ReporteSemanalSerializer``.
EntradaReporte = inline_serializer(
    name="ReporteSemanalEntrada",
    fields={
        "semana": serializers.IntegerField(min_value=1),
        "horas_reportadas": serializers.IntegerField(min_value=1),
    },
)


def actor_guardado(usuario):
    """Rol y vigencia desde la fila guardada; el objeto del llamador no decide."""
    if not isinstance(usuario, Usuario) or getattr(usuario, "pk", None) is None:
        raise ValidationError({"actor": [MENSAJE_ACTOR_INVALIDO]})
    fila = Usuario.objects.filter(pk=usuario.pk, is_active=True).only("rol").first()
    if fila is None:
        raise ValidationError({"actor": [MENSAJE_ACTOR_INVALIDO]})
    return fila


class ReportePracticaView(APIView):
    """Registra el reporte semanal de la práctica; solo su propio estudiante."""

    @extend_schema(
        summary="Registrar el reporte semanal de una práctica",
        request=EntradaReporte,
        responses={
            201: ReporteSemanalSerializer,
            400: OpenApiResponse(
                description=(
                    "Validación de la entrada, actor que no es el estudiante dueño, "
                    "práctica en estado final o semana ya reportada."
                )
            ),
            404: OpenApiResponse(description="La práctica no existe."),
        },
    )
    def post(self, request, practica_id):
        practica = Practica.objects.filter(pk=practica_id).first()
        if practica is None:
            raise NotFound(MENSAJE_PRACTICA)
        fila = actor_guardado(request.user)
        if not (fila.rol == Usuario.Rol.ESTUDIANTE and practica.estudiante_id == fila.pk):
            raise ValidationError({"actor": [MENSAJE_ACTOR]})
        if practica.estado in ESTADOS_FINALES:
            raise ValidationError(
                {"estado": [MENSAJE_TERMINAL.format(estado=practica.estado)]}
            )
        serializer = ReporteSemanalSerializer(
            data=request.data, context={"practica": practica}
        )
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                reporte = serializer.save(practica=practica)
        except IntegrityError:
            # Carrera entre dos envíos: la restricción de la base es la última red.
            raise ValidationError({"semana": [MENSAJE_SEMANA_DUPLICADA]}) from None
        return Response(
            ReporteSemanalSerializer(reporte).data, status=status.HTTP_201_CREATED
        )
