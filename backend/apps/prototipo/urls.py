from django.urls import path

from . import views

app_name = "prototipo"

urlpatterns = [
    path("mi-practica/", views.mi_practica, name="mi_practica"),
    path(
        "reporte-semanal/nuevo/",
        views.reporte_semanal_nuevo,
        name="reporte_semanal_nuevo",
    ),
    # Tutor académico
    path("tutor/pendientes/", views.pendientes_revision, name="pendientes_revision"),
    path("tutor/pendientes/<slug:clave>/", views.revisar, name="revisar"),
    path("tutor/tutorados/", views.mis_tutorados, name="mis_tutorados"),
    path(
        "tutor/practicas/<int:practica_id>/",
        views.practica_tutor,
        name="practica_tutor",
    ),
    path(
        "tutor/practicas/<int:practica_id>/evaluacion/",
        views.evaluacion_final,
        name="evaluacion_final",
    ),
]
