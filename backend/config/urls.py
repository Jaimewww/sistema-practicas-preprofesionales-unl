"""URL configuration for config project."""
from apps.practicas.api import PracticaDetalleView, PracticasListaView
from apps.reportes.api import ReportePracticaView
from apps.seguridad.api import TokenObtainEnvelopeView, TokenRefreshEnvelopeView
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.health.urls')),
    path('prototipo/', include('apps.prototipo.urls')),
    # Contrato OpenAPI (#77, S4): schema en /api/v1/schema/ y Swagger en
    # /api/v1/docs/; /health/ queda intacto.
    path(
        'api/v1/schema/',
        SpectacularAPIView.as_view(),
        name='api-v1-spectacular',
    ),
    path(
        'api/v1/docs/',
        SpectacularSwaggerView.as_view(url_name='api-v1-spectacular'),
        name='api-v1-docs',
    ),
    # Autenticación JWT de la API real (#79, D2).
    path(
        'api/v1/auth/token/',
        TokenObtainEnvelopeView.as_view(),
        name='api-v1-auth-token',
    ),
    path(
        'api/v1/auth/token/refresh/',
        TokenRefreshEnvelopeView.as_view(),
        name='api-v1-auth-token-refresh',
    ),
    # Endpoints de negocio de /api/v1/ (#78, S2): las tres rutas de prácticas
    # (lista, detalle y reportes).
    path('api/v1/practicas/', PracticasListaView.as_view(), name='practicas-lista'),
    path(
        'api/v1/practicas/<int:practica_id>/',
        PracticaDetalleView.as_view(),
        name='practicas-detalle',
    ),
    path(
        'api/v1/practicas/<int:practica_id>/reportes/',
        ReportePracticaView.as_view(),
        name='practicas-reportes',
    ),
    # JSON del demo (X-Rol, no autentica): fuera de /api/v1/ para que ninguna ruta
    # de la API real comparta prefijo con un mecanismo sin identidad (#79, ADR 0011).
    path('prototipo/api/v1/', include('apps.prototipo.api_urls')),
]
