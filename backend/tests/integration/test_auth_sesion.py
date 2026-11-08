"""Ciclo de vida de la sesión JWT según el ADR 0011 (#79, L9).

Cubre lo que el ADR fija y la primera versión de #102 dejaba en los valores por defecto
de simplejwt: access de 15 minutos, refresh con rotación y lista de bloqueo, logout que
invalida el refresh (RNF-03), tope de intentos en ``/api/v1/auth/token/``.
"""

from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from apps.usuarios.models import Usuario

TOKEN = "/api/v1/auth/token/"
REFRESCO = "/api/v1/auth/token/refresh/"
LOGOUT = "/api/v1/auth/logout/"
ESQUEMA = "/api/v1/schema/"
DOCS = "/api/v1/docs/"
CLAVE = "Clave-Segura-2026"
CLAVES_ENVELOPE = {"success", "message", "data", "errors", "meta"}


class ConfiguracionSegunAdrTests(SimpleTestCase):
    def test_simple_jwt_sigue_el_adr_0011(self):
        jwt = settings.SIMPLE_JWT

        self.assertEqual(jwt["ACCESS_TOKEN_LIFETIME"], timedelta(minutes=15))
        # RNF-03: 30 minutos sin usar el refresh cierran la sesión (cada uso rota y
        # renueva la ventana).
        self.assertEqual(jwt["REFRESH_TOKEN_LIFETIME"], timedelta(minutes=30))
        self.assertIs(jwt["ROTATE_REFRESH_TOKENS"], True)
        self.assertIs(jwt["BLACKLIST_AFTER_ROTATION"], True)

    def test_la_lista_de_bloqueo_esta_instalada(self):
        self.assertIn("rest_framework_simplejwt.token_blacklist", settings.INSTALLED_APPS)

    def test_el_login_tiene_su_scope_de_tope_de_intentos(self):
        self.assertEqual(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["auth"], "5/min")


class SesionBase:
    def setUp(self):
        # El tope de intentos usa la cache: sin limpiarla un test hereda los intentos
        # del anterior.
        cache.clear()
        self.addCleanup(cache.clear)
        self.cliente = APIClient()
        self.estudiante = self.crear("estudiante1")

    def crear(self, username):
        return Usuario.objects.create_user(
            username=username, nombre=username.title(), email=f"{username}@example.com",
            rol=Usuario.Rol.ESTUDIANTE, password=CLAVE,
        )

    def iniciar_sesion(self, username="estudiante1"):
        respuesta = APIClient().post(
            TOKEN, {"username": username, "password": CLAVE}, format="json"
        )
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        return respuesta.json()["data"]

    def con_access(self, access):
        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        return cliente

    def assertEnvelopeError(self, respuesta, estado):
        self.assertEqual(respuesta.status_code, estado, respuesta.content)
        cuerpo = respuesta.json()
        self.assertEqual(set(cuerpo), CLAVES_ENVELOPE)
        self.assertIs(cuerpo["success"], False)
        return cuerpo


class RotacionDelRefreshTests(SesionBase, TestCase):
    def test_renovar_entrega_un_refresh_nuevo_y_bloquea_el_anterior(self):
        sesion = self.iniciar_sesion()

        renovado = self.cliente.post(REFRESCO, {"refresh": sesion["refresh"]}, format="json")

        self.assertEqual(renovado.status_code, 200)
        datos = renovado.json()["data"]
        self.assertEqual(set(datos), {"access", "refresh"})
        self.assertNotEqual(datos["refresh"], sesion["refresh"])

        reuso = self.cliente.post(REFRESCO, {"refresh": sesion["refresh"]}, format="json")
        cuerpo = self.assertEnvelopeError(reuso, 401)
        self.assertEqual(cuerpo["errors"]["code"], "no_autenticado")

    def test_el_refresh_rotado_sigue_sirviendo_una_vez(self):
        sesion = self.iniciar_sesion()
        primero = self.cliente.post(REFRESCO, {"refresh": sesion["refresh"]}, format="json")

        segundo = self.cliente.post(
            REFRESCO, {"refresh": primero.json()["data"]["refresh"]}, format="json"
        )

        self.assertEqual(segundo.status_code, 200)


class CierreDeSesionTests(SesionBase, TestCase):
    def test_el_logout_invalida_el_refresh(self):
        sesion = self.iniciar_sesion()

        salida = self.con_access(sesion["access"]).post(
            LOGOUT, {"refresh": sesion["refresh"]}, format="json"
        )

        self.assertEqual(salida.status_code, 200)
        self.assertIs(salida.json()["success"], True)
        self.assertIsNone(salida.json()["data"])
        intento = self.cliente.post(REFRESCO, {"refresh": sesion["refresh"]}, format="json")
        self.assertEnvelopeError(intento, 401)

    def test_el_logout_exige_estar_autenticado(self):
        sesion = self.iniciar_sesion()

        respuesta = self.cliente.post(LOGOUT, {"refresh": sesion["refresh"]}, format="json")

        self.assertEnvelopeError(respuesta, 401)
        # El refresh sigue vivo: un anónimo no puede cerrar sesiones ajenas.
        self.assertEqual(
            self.cliente.post(REFRESCO, {"refresh": sesion["refresh"]}, format="json").status_code,
            200,
        )

    def test_el_logout_no_revoca_el_refresh_de_otra_cuenta(self):
        self.crear("estudiante2")
        propia = self.iniciar_sesion("estudiante1")
        ajena = self.iniciar_sesion("estudiante2")

        respuesta = self.con_access(propia["access"]).post(
            LOGOUT, {"refresh": ajena["refresh"]}, format="json"
        )

        self.assertEnvelopeError(respuesta, 400)
        self.assertEqual(
            self.cliente.post(REFRESCO, {"refresh": ajena["refresh"]}, format="json").status_code,
            200,
        )

    def test_el_logout_rechaza_un_refresh_invalido_o_repetido_con_400(self):
        sesion = self.iniciar_sesion()
        cliente = self.con_access(sesion["access"])
        cliente.post(LOGOUT, {"refresh": sesion["refresh"]}, format="json")

        for datos in ({"refresh": "no-es-un-jwt"}, {"refresh": sesion["refresh"]}, {}):
            with self.subTest(datos=datos):
                cuerpo = self.assertEnvelopeError(
                    cliente.post(LOGOUT, datos, format="json"), 400
                )
                self.assertIn("refresh", cuerpo["errors"])

    def test_el_logout_no_cierra_las_otras_sesiones_de_la_cuenta(self):
        una = self.iniciar_sesion()
        otra = self.iniciar_sesion()

        self.con_access(una["access"]).post(LOGOUT, {"refresh": una["refresh"]}, format="json")

        self.assertEqual(
            self.cliente.post(REFRESCO, {"refresh": otra["refresh"]}, format="json").status_code,
            200,
        )

    def test_un_access_no_sirve_como_refresh(self):
        sesion = self.iniciar_sesion()

        respuesta = self.cliente.post(REFRESCO, {"refresh": sesion["access"]}, format="json")

        self.assertEnvelopeError(respuesta, 401)


class TopeDeIntentosTests(SesionBase, TestCase):
    def pedir(self, clave=CLAVE):
        return self.cliente.post(
            TOKEN, {"username": "estudiante1", "password": clave}, format="json"
        )

    def test_el_sexto_intento_en_un_minuto_responde_429_con_envelope(self):
        for _ in range(5):
            self.assertEqual(self.pedir("equivocada").status_code, 401)

        respuesta = self.pedir("equivocada")

        cuerpo = self.assertEnvelopeError(respuesta, 429)
        self.assertEqual(cuerpo["errors"]["code"], "demasiadas_solicitudes")
        self.assertIn("segundos", cuerpo["errors"]["detail"])
        self.assertTrue(int(respuesta["Retry-After"]) > 0)

    def test_las_credenciales_correctas_tambien_cuentan(self):
        for _ in range(5):
            self.assertEqual(self.pedir().status_code, 200)

        self.assertEnvelopeError(self.pedir(), 429)

    def test_el_tope_no_alcanza_al_refresh_ni_a_la_api(self):
        sesion = self.iniciar_sesion()
        for _ in range(4):
            self.pedir("equivocada")

        for _ in range(8):
            ronda = self.cliente.post(REFRESCO, {"refresh": sesion["refresh"]}, format="json")
            sesion = {**sesion, **ronda.json()["data"]}
            self.assertEqual(ronda.status_code, 200)
        self.assertEqual(self.con_access(sesion["access"]).get("/api/v1/practicas/").status_code, 200)

    def test_la_cache_limpia_reinicia_el_conteo(self):
        for _ in range(5):
            self.pedir("equivocada")
        cache.clear()

        self.assertEqual(self.pedir("equivocada").status_code, 401)
