"""Conservación de los fieldsets del admin de usuario (T2, RF-07, S1–S3).

``UsuarioAdmin`` compone sus ``fieldsets`` con los del ``UserAdmin`` de Django
más el fieldset propio de la aplicación. El corte de tipado solo cambia la forma
de esa composición (una tupla explícita en lugar de ``+`` sobre un posible
``None``) para que el analizador estático pueda comprobarla: los fieldsets, su
orden y la página de cambio siguen siendo los mismos.
"""

from django.contrib.auth.admin import UserAdmin
from django.test import TestCase
from django.urls import reverse

from apps.usuarios.admin import UsuarioAdmin
from apps.usuarios.models import Usuario

PASSWORD = "clave-de-prueba-2026"
FIELDSET_PROPIO = ("Rol y carrera", {"fields": ("nombre", "rol", "carrera")})


class FieldsetsDelAdminTests(TestCase):
    def setUp(self):
        self.root = Usuario.objects.create_superuser(
            username="root",
            email="root@unl.edu.ec",
            nombre="Root",
            rol="estudiante",
            password=PASSWORD,
        )
        self.client.force_login(self.root)

    def test_conserva_los_fieldsets_de_django_y_agrega_el_fieldset_del_rol(self):
        """Django conserva sus grupos —en orden— y la app añade «Rol y carrera»."""
        self.assertIsInstance(UsuarioAdmin.fieldsets, tuple)
        fieldsets = tuple(UsuarioAdmin.fieldsets or ())
        heredados = tuple(UserAdmin.fieldsets or ())
        self.assertEqual(fieldsets[: len(heredados)], heredados)
        self.assertEqual(fieldsets[len(heredados) :], (FIELDSET_PROPIO,))

        respuesta = self.client.get(
            reverse("admin:usuarios_usuario_change", args=[self.root.pk])
        )
        self.assertEqual(respuesta.status_code, 200)
        # Los campos de los grupos de Django siguen en el formulario…
        for campo in ("username", "is_staff", "groups"):
            self.assertContains(respuesta, f'name="{campo}"')
        # …y el grupo propio de la app también.
        for campo in ("nombre", "rol", "carrera"):
            self.assertContains(respuesta, f'name="{campo}"')
