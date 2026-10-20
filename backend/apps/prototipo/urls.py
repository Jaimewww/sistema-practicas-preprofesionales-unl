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
]
