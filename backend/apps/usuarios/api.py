# pyright: reportMissingImports=false
"""Perfil del usuario autenticado: ``GET /api/v1/me/`` (S7, brecha 1 de la matriz).

El front lo lee tras el login para saber el rol y armar su menú. Responde con la
fila guardada y activa del actor, releída por ``pk``: el objeto del llamador no
decide nada. Sin token, con un token inválido o con la cuenta inactiva o borrada
responde 401 en el envelope de ADR-0012; cualquier rol del MVP puede leer el
suyo y nadie lee el de otro (la ruta no recibe id).
"""

from typing import ClassVar

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.seguridad.permissions import SinFilaEs401, rol_requerido
from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioActualSerializer


class UsuarioActualView(SinFilaEs401, APIView):
    """``GET /api/v1/me/``: id, nombre, email, rol y carrera del actor."""

    permission_classes: ClassVar[list] = [rol_requerido(*Usuario.Rol.values)]

    @extend_schema(
        summary="Perfil del usuario autenticado",
        responses={
            200: UsuarioActualSerializer,
            401: OpenApiResponse(
                description=(
                    "Sin token, token inválido o vencido, o cuenta inactiva o "
                    "borrada (`no_autenticado`)."
                )
            ),
            405: OpenApiResponse(
                description="Método distinto de GET (`method_not_allowed`)."
            ),
        },
    )
    def get(self, request):
        fila = Usuario.objects.filter(pk=request.user.pk, is_active=True).first()
        if fila is None:
            raise NotAuthenticated()
        return Response(UsuarioActualSerializer(fila).data)
