"""Tests del usuario personalizado, su creación pública y su admin (T012, RF-11)."""

import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.carreras.models import Carrera
from apps.usuarios.models import Usuario

PASSWORD = "clave-de-prueba-2026"
ROLES = ("estudiante", "tutor_academico", "tutor_entidad", "coordinador", "director", "secretaria")
CON_CARRERA = ("coordinador", "tutor_academico", "director", "secretaria")
SIN_CARRERA = ("estudiante", "tutor_entidad")
ENV = {
    "DJANGO_SUPERUSER_USERNAME": "root",
    "DJANGO_SUPERUSER_EMAIL": "root@unl.edu.ec",
    "DJANGO_SUPERUSER_PASSWORD": PASSWORD,
}


def carrera(codigo="ING-SIS"):
    return Carrera.objects.create(codigo=codigo, nombre="Ingeniería de Sistemas")


def datos(**campos):
    base = {"username": "lucia", "nombre": "Lucía Pérez", "email": "lucia@unl.edu.ec", "rol": "estudiante"}
    base.update(campos)
    return base


def instancia(**campos):
    usuario = Usuario(**datos(**campos))
    usuario.set_password(PASSWORD)
    return usuario


def crear(**campos):
    usuario = instancia(**campos)
    usuario.full_clean()
    usuario.save()
    return usuario


def rechazar(caso, campo, **campos):
    with caso.assertRaises(ValidationError) as error:
        instancia(**campos).full_clean()
    caso.assertIn(campo, error.exception.message_dict)


def crear_superusuario_cli(**env):
    with patch.dict(os.environ, {**ENV, **env}):
        call_command("createsuperuser", interactive=False, verbosity=0)


class CamposObligatoriosTests(TestCase):
    def test_nombre_email_y_rol_son_obligatorios(self):
        for campo in ("nombre", "email", "rol"):
            with self.subTest(campo=campo):
                rechazar(self, campo, **{campo: ""})
        self.assertEqual(Usuario.objects.count(), 0)

    def test_rol_fuera_de_los_seis_slugs_es_rechazado(self):
        rechazar(self, "rol", rol="administrador")
        self.assertEqual(Usuario.objects.count(), 0)


class RolesTests(TestCase):
    def test_los_seis_slugs_se_guardan_sin_privilegios(self):
        self.assertEqual(tuple(Usuario.Rol.values), ROLES)
        for i, slug in enumerate(ROLES):
            with self.subTest(rol=slug):
                c = carrera(f"CAR-{i}") if slug in CON_CARRERA else None
                u = Usuario.objects.get(pk=crear(username=f"p{i}", email=f"p{i}@unl.edu.ec", rol=slug, carrera=c).pk)
                self.assertEqual((u.rol, u.carrera_id, u.is_staff, u.is_superuser), (slug, c.pk if c else None, False, False))


class CarreraTests(TestCase):
    def test_la_carrera_es_obligatoria_solo_en_los_cuatro_roles_con_alcance(self):
        for slug in CON_CARRERA:
            with self.subTest(rol=slug):
                rechazar(self, "carrera", rol=slug)
        for slug in SIN_CARRERA:
            with self.subTest(rol=slug):
                self.assertIsNone(crear(username=f"u-{slug}", email=f"{slug}@unl.edu.ec", rol=slug).carrera)
        self.assertEqual(Usuario.objects.count(), 2)

    def test_la_carrera_con_usuarios_no_se_elimina(self):
        c = carrera()
        crear(rol="coordinador", carrera=c)
        with self.assertRaises(ProtectedError), transaction.atomic():
            c.delete()
        self.assertEqual((Carrera.objects.filter(pk=c.pk).count(), Usuario.objects.count()), (1, 1))


class EmailUnicoTests(TestCase):
    def test_email_duplicado_se_rechaza_en_validacion_y_en_la_base(self):
        crear()
        rechazar(self, "email", username="otra")
        duplicado = Usuario(**datos(username="otra"))
        duplicado.set_password(PASSWORD)
        with self.assertRaises(IntegrityError), transaction.atomic():
            duplicado.save()
        self.assertEqual(Usuario.objects.count(), 1)


class CreacionSuperusuarioTests(TestCase):
    def test_cli_con_los_campos_nuevos_crea_un_superusuario_valido(self):
        crear_superusuario_cli(DJANGO_SUPERUSER_NOMBRE="Root", DJANGO_SUPERUSER_ROL="estudiante")
        root = Usuario.objects.get(username="root")
        root.full_clean()
        self.assertEqual((root.nombre, root.rol, root.is_staff, root.is_superuser), ("Root", "estudiante", True, True))

    def test_cli_rechaza_entrada_incompleta_o_invalida_sin_escribir(self):
        casos = (
            ({}, "--nombre"),
            ({"DJANGO_SUPERUSER_NOMBRE": "Root", "DJANGO_SUPERUSER_ROL": "administrador"}, "not a valid choice"),
            ({"DJANGO_SUPERUSER_NOMBRE": "Root", "DJANGO_SUPERUSER_ROL": "coordinador"}, "La carrera es obligatoria para este rol."),
        )
        for env, mensaje in casos:
            with self.subTest(mensaje=mensaje):
                with self.assertRaises(CommandError) as error:
                    crear_superusuario_cli(**env)
                self.assertIn(mensaje, str(error.exception))
                self.assertEqual(Usuario.objects.count(), 0)

    def test_create_user_y_create_superuser_validan_antes_de_escribir(self):
        for creador, rol in ((Usuario.objects.create_user, "administrador"), (Usuario.objects.create_superuser, "coordinador")):
            with self.subTest(creador=creador.__name__):
                with self.assertRaises(ValidationError):
                    creador(password=PASSWORD, **datos(rol=rol))
                self.assertEqual(Usuario.objects.count(), 0)


class CreacionAsincronaTests(TestCase):
    async def test_acreate_user_conserva_la_creacion_y_valida(self):
        valido = await Usuario.objects.acreate_user(**datos(), password=PASSWORD)
        self.assertTrue(valido.check_password(PASSWORD))
        self.assertEqual((valido.is_staff, valido.is_superuser), (False, False))
        raiz = await Usuario.objects.acreate_superuser(username="raiz", email="raiz@unl.edu.ec", nombre="Raíz", rol="estudiante", password=PASSWORD)
        self.assertEqual((raiz.is_staff, raiz.is_superuser), (True, True))
        with self.assertRaises(ValidationError):
            await Usuario.objects.acreate_user(**datos(username="malo", email="malo@unl.edu.ec", rol="administrador"), password=PASSWORD)
        self.assertEqual(await Usuario.objects.acount(), 2)


class AdminTests(TestCase):
    def setUp(self):
        self.carrera = carrera("DER-001")
        self.root = Usuario.objects.create_superuser(password=PASSWORD, **datos(username="root", email="root@unl.edu.ec", nombre="Root"))
        self.client.force_login(self.root)

    def post_add(self, **cambios):
        base = {
            **datos(username="coord", nombre="Coordinadora", email="coord@unl.edu.ec"),
            "rol": "coordinador",
            "carrera": self.carrera.pk,
            "usable_password": "true",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        return self.client.post(reverse("admin:usuarios_usuario_add"), {**base, **cambios})

    def test_admin_publica_el_gestionador_de_usuarios(self):
        self.assertContains(self.client.get(reverse("admin:index")), reverse("admin:usuarios_usuario_changelist"))
        self.assertEqual(self.client.get(reverse("admin:usuarios_usuario_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:usuarios_usuario_add")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:usuarios_usuario_change", args=[self.root.pk])).status_code, 200)

    def test_admin_agrega_un_actor_valido_y_rechaza_rol_sin_carrera(self):
        self.assertEqual(self.post_add().status_code, 302)
        coord = Usuario.objects.get(username="coord")
        coord.full_clean()
        self.assertEqual((coord.rol, coord.is_staff, coord.is_superuser), ("coordinador", False, False))
        respuesta = self.post_add(username="coord2", email="coord2@unl.edu.ec", carrera="")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("carrera", respuesta.context["adminform"].form.errors)
        self.assertFalse(Usuario.objects.filter(username="coord2").exists())


class AutenticacionHeredadaTests(TestCase):
    def test_conserva_autenticacion_y_sesion(self):
        usuario = Usuario.objects.create_user(password=PASSWORD, **datos())
        self.assertIs(get_user_model(), Usuario)
        self.assertEqual((usuario.get_username(), usuario.check_password(PASSWORD)), ("lucia", True))
        self.assertEqual((usuario.has_usable_password(), usuario.is_active), (True, True))
        self.assertEqual((usuario.is_staff, usuario.is_superuser), (False, False))
        self.assertTrue(self.client.login(username="lucia", password=PASSWORD))
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)
