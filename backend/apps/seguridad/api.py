"""Rutas de token de la API real (#79, D2): obtener el par y refrescar el access.

Las dos vistas heredan de ``simplejwt`` —el flujo lo resuelve la librería— y solo
agregan la documentación de ``drf-spectacular``. El cuerpo lo envuelve el renderer
del contrato (#77), así que ``data`` es ``{access, refresh}`` al obtener y
``{access}`` al refrescar. Rotación, revocación y tiempo de vida quedan para el
ADR (#84): aquí corren los valores por defecto de la librería.

Son las únicas dos rutas públicas de la API real: sin credenciales no hay a dónde
pedir el token, así que llevan ``AllowAny`` explícito (sin autenticación) y no
arrastran el 401 por defecto de #79.
"""

from typing import ClassVar

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

ParDeTokens = inline_serializer(
    name="ParDeTokens",
    fields={
        "access": serializers.CharField(read_only=True),
        "refresh": serializers.CharField(read_only=True),
    },
)
AccessRenovado = inline_serializer(
    name="AccessRenovado",
    fields={"access": serializers.CharField(read_only=True)},
)
Credenciales = inline_serializer(
    name="Credenciales",
    fields={
        "username": serializers.CharField(),
        "password": serializers.CharField(style={"input_type": "password"}),
    },
)
Refresco = inline_serializer(
    name="Refresco",
    fields={"refresh": serializers.CharField()},
)


class TokenObtainEnvelopeView(TokenObtainPairView):
    """``POST /api/v1/auth/token/``: credenciales -> ``{access, refresh}``."""

    permission_classes: ClassVar[list] = [AllowAny]
    authentication_classes: ClassVar[list] = []

    @extend_schema(
        summary="Obtener el par de tokens JWT",
        request=Credenciales,
        responses={
            200: ParDeTokens,
            401: OpenApiResponse(
                description="Credenciales inválidas; el envelope no distingue la causa."
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


MENSAJE_NO_AUTENTICADO = "Autenticación requerida."


class TokenRefreshEnvelopeView(TokenRefreshView):
    """``POST /api/v1/auth/token/refresh/``: refresh -> ``{access}``."""

    permission_classes: ClassVar[list] = [AllowAny]
    authentication_classes: ClassVar[list] = []

    @extend_schema(
        summary="Renovar el access token",
        request=Refresco,
        responses={
            200: AccessRenovado,
            401: OpenApiResponse(
                description="Refresh inválido, vencido o de una cuenta borrada; "
                "el envelope no distingue la causa."
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """F1 del verify: el usuario borrado lanza DoesNotExist, no AuthenticationFailed."""
        try:
            return super().post(request, *args, **kwargs)
        except get_user_model().DoesNotExist:
            # Cuando la 401 distingue causas se rompe el oracle (S4-5).
            raise AuthenticationFailed() from None
