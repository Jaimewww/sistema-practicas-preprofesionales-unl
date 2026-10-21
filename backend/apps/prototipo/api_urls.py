from django.urls import path

from . import api

app_name = "api"

urlpatterns = [
    path("practicas/", api.lista_practicas, name="lista_practicas"),
    path("practicas/<int:practica_id>/", api.detalle_practica, name="detalle_practica"),
]
