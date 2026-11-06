from django.urls import path

from . import api

app_name = "api"

urlpatterns = [
    path("alertas/", api.lista_alertas, name="lista_alertas"),
    path("anexos/<int:anexo_id>/legalizacion/", api.legalizar_anexo, name="legalizar_anexo"),
    path("practicas/<int:practica_id>/cierre/", api.cierre_practica, name="cierre_practica"),
    path("practicas/<int:practica_id>/historial/", api.historial_practica, name="historial_practica"),
    path("pendientes/<slug:clave>/", api.decidir_pendiente, name="decidir_pendiente"),
]
