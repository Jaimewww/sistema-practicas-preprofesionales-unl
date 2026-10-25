"""Notification context for the existing synthetic actor screens."""
from django.conf import settings

from . import facade
from .views import contexto_demo


def notificaciones(request):
    match = request.resolver_match
    if not settings.DEBUG or not match or match.namespace != "prototipo":
        return {}
    path = request.path
    if path.startswith("/prototipo/coordinador/"):
        rol = "coordinador"
    elif path.startswith("/prototipo/tutor/"):
        rol = "tutor_academico"
    elif path.startswith("/prototipo/entidad/"):
        rol = "tutor_entidad"
    elif match.url_name in {"mi_practica", "reporte_semanal_nuevo"}:
        rol = "estudiante"
    else:
        return {}
    return {"rol_demo": rol, "notificaciones": facade.alertas_de(rol, **contexto_demo(request))}
