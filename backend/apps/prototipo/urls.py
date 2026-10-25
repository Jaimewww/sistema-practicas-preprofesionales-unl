from django.urls import path

from . import (
    views,
    views_coordinador as coordinador,
    views_director_secretaria as director_secretaria,
    views_entidad as entidad,
)

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
    # Catálogo de entidades y convenios (mapa §3.6, issue #55).
    # N1 lista, N1 detalle y N2 convenios: solo consulta, sin POST.
    path("entidad/catalogo/", entidad.catalogo_entidades, name="catalogo_entidades"),
    path("entidad/catalogo/<int:entidad_id>/", entidad.detalle_entidad, name="detalle_entidad"),
    path("entidad/convenios/", entidad.convenios, name="convenios"),
    # Coordinador de la carrera
    path(
        "coordinador/practicas/",
        coordinador.practicas_carrera,
        name="practicas_carrera",
    ),
    path("coordinador/alertas/", coordinador.alertas, name="alertas"),
    path("coordinador/practicas/<int:practica_id>/", coordinador.practica_coordinador, name="practica_coordinador"),
    path("coordinador/practicas/<int:practica_id>/cerrar/", coordinador.cerrar_practica, name="cerrar_practica"),
    path("coordinador/practicas/<int:practica_id>/<slug:accion>/", coordinador.estado_practica, name="estado_practica"),
    path("coordinador/consolidado/", coordinador.consolidado_carrera, name="consolidado_carrera"),
    path("coordinador/configuracion/", coordinador.configuracion_carrera, name="configuracion_carrera"),
    path("coordinador/restablecer/", coordinador.restablecer, name="restablecer_prototipo"),
    path("dvs/consolidado/", coordinador.consolidado_general, name="consolidado_general"),
    # Director de carrera
    path("director/cierres/", director_secretaria.cierres_director, name="cierres_director"),
    path("director/practicas/<int:practica_id>/", director_secretaria.practica_director, name="practica_director"),
    # Secretaría de carrera
    path("secretaria/anexos/", director_secretaria.anexos_secretaria, name="anexos_secretaria"),
    path("secretaria/anexos/<int:anexo_id>/legalizar/", director_secretaria.legalizar_anexo, name="legalizar_anexo"),
]
