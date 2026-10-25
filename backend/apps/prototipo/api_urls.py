from django.urls import path

from . import api

app_name = "api"

urlpatterns = [
    path("alertas/", api.lista_alertas, name="lista_alertas"),
    path("practicas/<int:practica_id>/cierre/", api.cierre_practica, name="cierre_practica"),
    path("practicas/", api.lista_practicas, name="lista_practicas"),
    path("practicas/<int:practica_id>/", api.detalle_practica, name="detalle_practica"),
    path(
        "practicas/<int:practica_id>/reportes/",
        api.reportes_practica,
        name="reportes_practica",
    ),
    path("pendientes/<slug:clave>/", api.decidir_pendiente, name="decidir_pendiente"),
]
