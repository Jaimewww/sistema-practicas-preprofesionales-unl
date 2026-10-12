from django.urls import path

from apps.health import views

app_name = "health"

urlpatterns = [
    path("health/", views.health, name="health"),
]
