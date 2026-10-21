"""URL configuration for config project."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.health.urls')),
    path('prototipo/', include('apps.prototipo.urls')),
    path('api/v1/', include('apps.prototipo.api_urls')),
]
