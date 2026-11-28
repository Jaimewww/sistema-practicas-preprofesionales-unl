# pyright: reportMissingImports=false
"""URL configuration for config project."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.actividades.api import (
    AprobarPlanView,
    DevolverPlanView,
    PlanPracticaView,
)
from apps.alertas.api import AlertasView
from apps.carreras.api import ConfiguracionCarreraView
from apps.practicas.api import (
    InformeExternoView,
    InformeFinalEstudianteView,
    InicioPracticaView,
    PracticaDetalleView,
    PracticasListaView,
)
from apps.reportes.api import (
    ConfirmarReporteEntidadView,
    DescargaEvidenciaView,
    DevolverInformeEstudianteView,
    DevolverReporteView,
    HorasPracticaView,
    PendientesView,
    ReenviarReporteView,
    ReporteDetalleView,
    ReportePracticaView,
    ValidarInformeEstudianteView,
    ValidarReporteView,
)
from apps.seguridad.api import (
    LogoutView,
    TokenObtainEnvelopeView,
    TokenRefreshEnvelopeView,
)
from apps.usuarios.api import UsuarioActualView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.health.urls")),
    path("prototipo/", include("apps.prototipo.urls")),
    # Contrato OpenAPI (#77, S4): schema en /api/v1/schema/ y Swagger en
    # /api/v1/docs/; /health/ queda intacto.
    path(
        "api/v1/schema/",
        SpectacularAPIView.as_view(),
        name="api-v1-spectacular",
    ),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="api-v1-spectacular"),
        name="api-v1-docs",
    ),
    path(
        "api/v1/alertas/",
        AlertasView.as_view(),
        name="alertas-lista",
    ),
    # Configuración de la carrera por modalidad (RF-12, C-17): PUT con el rol
    # coordinador y el alcance de su propia carrera.
    path(
        "api/v1/carreras/<str:codigo>/configuracion/",
        ConfiguracionCarreraView.as_view(),
        name="api-v1-carrera-configuracion",
    ),
    # Autenticación JWT de la API real (#79, D2).
    path(
        "api/v1/auth/token/",
        TokenObtainEnvelopeView.as_view(),
        name="api-v1-auth-token",
    ),
    path(
        "api/v1/auth/token/refresh/",
        TokenRefreshEnvelopeView.as_view(),
        name="api-v1-auth-token-refresh",
    ),
    path("api/v1/auth/logout/", LogoutView.as_view(), name="api-v1-auth-logout"),
    # Perfil del usuario autenticado para el menú por rol (S7).
    path("api/v1/me/", UsuarioActualView.as_view(), name="api-v1-me"),
    # Endpoints de negocio de /api/v1/ (#78, S2): las tres rutas de prácticas
    # (lista, detalle y reportes).
    path("api/v1/practicas/", PracticasListaView.as_view(), name="practicas-lista"),
    path(
        "api/v1/practicas/<int:practica_id>/",
        PracticaDetalleView.as_view(),
        name="practicas-detalle",
    ),
    path(
        "api/v1/practicas/<int:practica_id>/reportes/",
        ReportePracticaView.as_view(),
        name="practicas-reportes",
    ),
    # Horas acumuladas de la práctica (HU-04, #126): lectura multirrol con el
    # alcance de filas de T019.
    path(
        "api/v1/practicas/<int:practica_id>/horas/",
        HorasPracticaView.as_view(),
        name="practicas-horas",
    ),
    # Fecha real de inicio declarada por el coordinador de la carrera (T11,
    # RF-11): escritura autenticada del grupo de prácticas, antes de las demás
    # rutas de negocio y del demo del prototipo.
    path(
        "api/v1/practicas/<int:practica_id>/inicio/",
        InicioPracticaView.as_view(),
        name="practicas-inicio",
    ),
    # Informe final del tutor de entidad sobre la práctica (RF-08, HU-07).
    path(
        "api/v1/practicas/<int:practica_id>/informe-externo/",
        InformeExternoView.as_view(),
        name="practicas-informe-externo",
    ),
    # Informe final del estudiante (RF-16, HU-10, C-10): el dueño lo presenta —la
    # corrección tras una devolución crea la versión siguiente— y todo actor con
    # alcance de filas lee la última versión con su devolución.
    path(
        "api/v1/practicas/<int:practica_id>/informe-final/",
        InformeFinalEstudianteView.as_view(),
        name="practicas-informe-final",
    ),
    # Decisión del tutor académico sobre el informe del estudiante: reutiliza C-04
    # con la clave `informe-<id>` que la cola de pendientes publica.
    path(
        "api/v1/informes-estudiante/<int:informe_id>/validar/",
        ValidarInformeEstudianteView.as_view(),
        name="api-v1-informe-estudiante-validar",
    ),
    path(
        "api/v1/informes-estudiante/<int:informe_id>/devolver/",
        DevolverInformeEstudianteView.as_view(),
        name="api-v1-informe-estudiante-devolver",
    ),
    # Plan de actividades (S8, HU-01): versiones y envío del estudiante, y la
    # decisión del tutor académico activo.
    path(
        "api/v1/practicas/<int:practica_id>/plan/",
        PlanPracticaView.as_view(),
        name="practicas-plan",
    ),
    path(
        "api/v1/planes/<int:plan_id>/aprobar/",
        AprobarPlanView.as_view(),
        name="api-v1-plan-aprobar",
    ),
    path(
        "api/v1/planes/<int:plan_id>/devolver/",
        DevolverPlanView.as_view(),
        name="api-v1-plan-devolver",
    ),
    # Endpoints del tutor para validar/devolver reportes (RF-03, #122)
    path(
        "api/v1/pendientes/",
        PendientesView.as_view(),
        name="api-v1-pendientes",
    ),
    # Lectura del reporte individual con la observación de su devolución
    # (RF-03, S6): el estudiante recupera la observación y cierra la corrección.
    path(
        "api/v1/reportes/<int:reporte_id>/",
        ReporteDetalleView.as_view(),
        name="api-v1-reporte-detalle",
    ),
    # Descarga autenticada de las evidencias PDF del reporte (C-03, #157): única
    # salida del archivo, con el alcance de filas de T019; no hay URL pública.
    path(
        "api/v1/reportes/<int:reporte_id>/evidencias/<int:evidencia_id>/",
        DescargaEvidenciaView.as_view(),
        name="api-v1-reporte-evidencia",
    ),
    path(
        "api/v1/reportes/<int:reporte_id>/validar/",
        ValidarReporteView.as_view(),
        name="api-v1-reporte-validar",
    ),
    path(
        "api/v1/reportes/<int:reporte_id>/devolver/",
        DevolverReporteView.as_view(),
        name="api-v1-reporte-devolver",
    ),
    # Reenvío del estudiante sobre el reporte devuelto (#124)
    path(
        "api/v1/reportes/<int:reporte_id>/reenviar/",
        ReenviarReporteView.as_view(),
        name="api-v1-reporte-reenviar",
    ),
    # Confirmación del tutor de entidad sobre el reporte de su practicante
    # (RF-08, HU-07): registra quién confirmó y cuándo.
    path(
        "api/v1/reportes/<int:reporte_id>/confirmacion/",
        ConfirmarReporteEntidadView.as_view(),
        name="api-v1-reporte-confirmacion",
    ),
    # JSON del demo (X-Rol, no autentica): fuera de /api/v1/ para que ninguna ruta
    # de la API real comparta prefijo con un mecanismo sin identidad (#79, ADR 0011).
    path("prototipo/api/v1/", include("apps.prototipo.api_urls")),
]
