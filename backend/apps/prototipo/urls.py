from django.urls import path

from . import views

app_name = "prototipo"

urlpatterns = [
    path("", views.indice, name="indice"),
    path("mi-practica/", views.mi_practica, name="mi_practica"),
    path(
        "reporte-semanal/nuevo/",
        views.reporte_semanal_nuevo,
        name="reporte_semanal_nuevo",
    ),
    path("reiniciar-demo/", views.reiniciar_demo, name="reiniciar_demo"),
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
    # Tutor de la entidad receptora
    path("entidad/practicantes/", views.mis_practicantes, name="mis_practicantes"),
    path(
        "entidad/reportes/",
        views.reportes_por_confirmar_lista,
        name="reportes_por_confirmar",
    ),
    path(
        "entidad/practicas/<int:practica_id>/reportes/<int:semana>/",
        views.confirmar_reporte,
        name="confirmar_reporte",
    ),
    path(
        "entidad/practicas/<int:practica_id>/informe/",
        views.informe_externo,
        name="informe_externo",
    ),
    path(
        "entidad/practicas/<int:practica_id>/incumplimiento/",
        views.reportar_incumplimiento,
        name="reportar_incumplimiento",
    ),
]
