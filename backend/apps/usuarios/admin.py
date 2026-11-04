"""Admin del usuario personalizado (T012, RF-11)."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Conserva los fieldsets, permisos y contraseña de Django."""

    fieldsets = UserAdmin.fieldsets + (
        ("Rol y carrera", {"fields": ("nombre", "rol", "carrera")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Datos del actor",
            {"classes": ("wide",), "fields": ("nombre", "email", "rol", "carrera")},
        ),
    )
