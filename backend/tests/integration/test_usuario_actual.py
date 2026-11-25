"""Perfil del usuario autenticado: ``GET /api/v1/me/`` (S7, brecha 1 de la matriz).

El front lo pide tras el login para armar el menú por rol. La respuesta es la del
actor de la fila guardada y nada más: ``id``, ``nombre``, ``email``, ``rol`` y
``carrera`` (el id de la FK o ``null``). Nunca la contraseña, las banderas de
privilegio ni los grupos. Sin token, con token inválido o vencido, o con la cuenta
inactiva o borrada tras obtener el token responde el mismo 401 en el envelope de
ADR-0012 (docs/api.md §10.1).
"""

from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.carreras.models import Carrera
from apps.usuarios.models import Usuario

ME = "/api/v1/me/"
TOKEN = "/api/v1/auth/token/"
CLAVE = "Clave-Segura-2026"
CAMPOS = {"id", "nombre", "email", "rol", "carrera"}
PROHIBIDOS = {
    "password", "is_staff", "is_superuser", "is_active", "groups",
    "user_permissions", "last_login",
}
ERROR_401 = {
    "success": False,
    "message": "Autenticación requerida.",
    "data": None,
    "errors": {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
    "meta": {},
}


class UsuarioActualTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.usuarios = {
            rol: Usuario.objects.create_user(
                username=f"u-{rol}",
                nombre=f"Persona {rol}",
                email=f"{rol}@example.com",
                rol=rol,
                carrera=cls.carrera if rol in Usuario.ROLES_CON_CARRERA else None,
                password=CLAVE,
            )
            for rol in Usuario.Rol.values
        }

    def setUp(self):
        # El login tiene tope de intentos sobre la cache: cada test parte de cero.
        cache.clear()
        self.addCleanup(cache.clear)

    def con_token(self, usuario):
        # Seis logins seguidos superan el tope de 5/min: no es lo que se prueba aquí.
        cache.clear()
        respuesta = APIClient().post(
            TOKEN, {"username": usuario.username, "password": CLAVE}, format="json"
        )
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        cliente = APIClient()
        cliente.credentials(
            HTTP_AUTHORIZATION=f"Bearer {respuesta.json()['data']['access']}"
        )
        return cliente

    def forzado(self, usuario):
        cliente = APIClient()
        cliente.force_authenticate(user=usuario)
        return cliente

    def esperado(self, usuario):
        return {
            "id": usuario.pk,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol,
            "carrera": usuario.carrera_id,
        }

    def test_cada_rol_con_token_real_recibe_su_perfil_exacto(self):
        for rol, usuario in self.usuarios.items():
            with self.subTest(rol=rol):
                respuesta = self.con_token(usuario).get(ME)

                self.assertEqual(respuesta.status_code, 200, respuesta.content)
                cuerpo = respuesta.json()
                self.assertEqual(
                    cuerpo,
                    {
                        "success": True,
                        "message": "Operación exitosa.",
                        "data": self.esperado(usuario),
                        "errors": None,
                        "meta": {},
                    },
                )
                self.assertEqual(set(cuerpo["data"]), CAMPOS)
                self.assertFalse(PROHIBIDOS & set(cuerpo["data"]))

    def test_la_carrera_es_el_id_o_null_segun_el_rol(self):
        coordinador = self.forzado(self.usuarios[Usuario.Rol.COORDINADOR]).get(ME)
        estudiante = self.forzado(self.usuarios[Usuario.Rol.ESTUDIANTE]).get(ME)

        self.assertEqual(coordinador.json()["data"]["carrera"], self.carrera.pk)
        self.assertIsNone(estudiante.json()["data"]["carrera"])

    def test_con_force_authenticate_responde_el_mismo_perfil(self):
        usuario = self.usuarios[Usuario.Rol.TUTOR_ACADEMICO]
        respuesta = self.forzado(usuario).get(ME)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["data"], self.esperado(usuario))

    def test_el_perfil_sale_de_la_fila_guardada_y_no_del_objeto_del_llamador(self):
        usuario = Usuario.objects.get(pk=self.usuarios[Usuario.Rol.ESTUDIANTE].pk)
        usuario.nombre = "Nombre no guardado"
        usuario.rol = Usuario.Rol.COORDINADOR

        data = self.forzado(usuario).get(ME).json()["data"]

        self.assertEqual(data["nombre"], "Persona estudiante")
        self.assertEqual(data["rol"], Usuario.Rol.ESTUDIANTE)

    def test_el_staff_no_expone_banderas_de_privilegio(self):
        usuario = self.usuarios[Usuario.Rol.DIRECTOR]
        Usuario.objects.filter(pk=usuario.pk).update(is_staff=True, is_superuser=True)

        data = self.con_token(usuario).get(ME).json()["data"]

        self.assertEqual(set(data), CAMPOS)

    def test_sin_token_responde_401_en_el_envelope(self):
        respuesta = APIClient().get(ME)

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json(), ERROR_401)

    def test_token_invalido_responde_401(self):
        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION="Bearer no-es-un-jwt")

        respuesta = cliente.get(ME)

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json()["errors"]["code"], "no_autenticado")

    def test_una_cuenta_inactiva_responde_401(self):
        usuario = self.usuarios[Usuario.Rol.ESTUDIANTE]
        con_token = self.con_token(usuario)
        Usuario.objects.filter(pk=usuario.pk).update(is_active=False)
        usuario.refresh_from_db()

        for nombre, cliente in (("jwt", con_token), ("forzado", self.forzado(usuario))):
            with self.subTest(cliente=nombre):
                respuesta = cliente.get(ME)
                self.assertEqual(respuesta.status_code, 401)
                self.assertEqual(respuesta.json(), ERROR_401)

    def test_un_access_vencido_responde_el_401_documentado(self):
        usuario = self.usuarios[Usuario.Rol.ESTUDIANTE]
        vigente = APIClient()
        vigente.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(usuario)}")
        self.assertEqual(vigente.get(ME).status_code, 200)
        vencido = AccessToken.for_user(usuario)
        vencido.set_exp(from_time=timezone.now() - timedelta(hours=1))
        self.assertLess(vencido["exp"], timezone.now().timestamp())
        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {vencido}")

        respuesta = cliente.get(ME)

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json(), ERROR_401)

    def test_un_usuario_borrado_tras_obtener_el_token_responde_el_401_documentado(self):
        usuario = Usuario.objects.create_user(
            username="u-borrado", nombre="Persona borrada", email="borrado@example.com",
            rol=Usuario.Rol.ESTUDIANTE, password=CLAVE,
        )
        con_token = self.con_token(usuario)
        self.assertEqual(con_token.get(ME).status_code, 200)
        Usuario.objects.filter(pk=usuario.pk).delete()
        self.assertFalse(Usuario.objects.filter(pk=usuario.pk).exists())

        respuesta = con_token.get(ME)

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json(), ERROR_401)

    def test_post_responde_405(self):
        respuesta = self.forzado(self.usuarios[Usuario.Rol.ESTUDIANTE]).post(
            ME, {}, format="json"
        )

        self.assertEqual(respuesta.status_code, 405)
        self.assertEqual(respuesta.json()["errors"]["code"], "method_not_allowed")
        self.assertEqual(respuesta["Allow"], "GET, HEAD, OPTIONS")
