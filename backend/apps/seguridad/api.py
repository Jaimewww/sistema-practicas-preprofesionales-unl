"""Rutas de sesión de la API real (#79, D2; ADR 0011): obtener, renovar y cerrar.

Obtener y renovar heredan de ``simplejwt`` —el flujo lo resuelve la librería— y solo
agregan la documentación de ``drf-spectacular``. El cuerpo lo envuelve el renderer
del contrato (#77): ``data`` es ``{access, refresh}`` al obtener y, como el refresh
rota (``ROTATE_REFRESH_TOKENS``), también al renovar; el refresh anterior queda en la
lista de bloqueo. El cierre de sesión (RNF-03) bloquea el refresh que se le entrega.

Obtener y renovar son las únicas rutas públicas de la API real (RNF-01 exime el
login): sin credenciales no hay a dónde pedir el token, así que llevan ``AllowAny``
explícito. Obtener además tiene tope de intentos (scope ``auth``). El logout exige un
access vigente: nadie cierra sesiones sin haber iniciado una.
"""

from collections.abc import Callable
from typing import cast

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

MENSAJE_REFRESH_INVALIDO = "El token de refresco no es válido o ya fue revocado."
MENSAJE_REFRESH_OBLIGATORIO = "Este campo es obligatorio."

# Frontera tipada con ``simplejwt``: ``Token.__init__`` está anotado como si
# recibiera otro ``Token``, pero su propio cuerpo trata el argumento como el JWT
# codificado (lo decodifica con el backend) y es lo que la librería entrega. El
# constructor real acepta el string, así que el contrato se declara una vez acá
# y el resto del módulo usa el nombre tipado: sin ``Any`` ni supresiones, y la
# invocación y las validaciones del token quedan intactas.
CrearRefreshToken: Callable[[str], RefreshToken] = cast(
    Callable[[str], RefreshToken], RefreshToken
)

ParDeTokens = inline_serializer(
    name="ParDeTokens",
    fields={
        "access": serializers.CharField(read_only=True),
        "refresh": serializers.CharField(read_only=True),
    },
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

    # DRF recorre estas secuencias al construir autenticadores y throttles, así
    # que una tupla cumple el mismo contrato que una lista: es el tipo inmutable
    # que declaran los stubs de DRF (``Sequence``).
    authentication_classes = ()
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def get_permissions(self) -> list[BasePermission]:
        """``AllowAny`` explícito: pedir el token no puede exigir credenciales.

        ``simplejwt`` anuncia ``permission_classes = ()`` y el analizador infiere
        de ahí una tupla vacía, así que reasignar otra tupla en la subclase no
        compila. El permiso se declara en el punto que DRF consulta
        (``get_permissions``), sin reescribir el atributo heredado.
        """
        return [AllowAny()]

    @extend_schema(
        summary="Obtener el par de tokens JWT",
        request=Credenciales,
        responses={
            200: ParDeTokens,
            401: OpenApiResponse(
                description="Credenciales inválidas; el envelope no distingue la causa."
            ),
            429: OpenApiResponse(
                description=(
                    "Más de 5 intentos por minuto desde el mismo origen "
                    "(`demasiadas_solicitudes`); `Retry-After` indica la espera."
                )
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshEnvelopeView(TokenRefreshView):
    """``POST /api/v1/auth/token/refresh/``: refresh -> ``{access, refresh}`` rotado."""

    authentication_classes = ()

    def get_permissions(self) -> list[BasePermission]:
        """``AllowAny`` explícito, igual que en el login: sin access no se renueva."""
        return [AllowAny()]

    @extend_schema(
        summary="Renovar el access token (rota el refresh)",
        request=Refresco,
        responses={
            200: ParDeTokens,
            401: OpenApiResponse(
                description="Refresh inválido, vencido, ya usado, revocado o de una "
                "cuenta borrada; el envelope no distingue la causa."
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


class LogoutView(APIView):
    """``POST /api/v1/auth/logout/``: bloquea el refresh de la sesión que se cierra."""

    @extend_schema(
        summary="Cerrar la sesión (revoca el refresh)",
        request=Refresco,
        responses={
            200: OpenApiResponse(
                description="Refresh revocado; el cuerpo no lleva datos."
            ),
            400: OpenApiResponse(
                description="Refresh ausente, inválido, ya revocado o de otra cuenta."
            ),
            401: OpenApiResponse(description="Sin access vigente (`no_autenticado`)."),
        },
    )
    def post(self, request):
        crudo = request.data.get("refresh") if hasattr(request.data, "get") else None
        if not crudo or not isinstance(crudo, str):
            raise ValidationError({"refresh": [MENSAJE_REFRESH_OBLIGATORIO]})
        try:
            token = CrearRefreshToken(crudo)
        except TokenError:
            raise ValidationError({"refresh": [MENSAJE_REFRESH_INVALIDO]}) from None
        # Un refresh ajeno no se bloquea y se responde igual que uno inválido: el
        # cliente no aprende si el token existe ni de quién es.
        if str(token.payload.get("user_id")) != str(request.user.pk):
            raise ValidationError({"refresh": [MENSAJE_REFRESH_INVALIDO]})
        token.blacklist()
        return Response(None)
