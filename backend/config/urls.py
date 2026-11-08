"""URL configuration for config project."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.health.urls')),
    path('prototipo/', include('apps.prototipo.urls')),
    # Contrato OpenAPI (#77, S4): schema en /api/v1/schema/ y Swagger en
    # /api/v1/docs/. Son las ÚNICAS rutas nuevas; los endpoints de negocio de
    # /api/v1/ llegan con #78 y /health/ queda intacto.
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
    path('api/v1/', include('apps.prototipo.api_urls')),
]
