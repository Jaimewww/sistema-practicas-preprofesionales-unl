"""Autenticación JWT real y permisos por rol/objeto (#79, S4).

Cubre los cinco criterios de aceptación con una prueba por caso: 401 sin
credenciales o con token inválido, 403 cuando el rol no tiene permiso, 403/404
al tocar una práctica ajena, y que la contraseña y los tokens no salen en las
respuestas ni en los logs.

La API real es *auth-first*: sin credenciales todo responde 401 con el envelope
de #77, incluso una ruta que sin autenticación habría dado 404.
"""

import logging
from collections.abc import Callable
from contextlib import contextmanager
from datetime import date, timedelta

import yaml
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.practicas.services import asignar_practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario

RUTA_OBTENCION = "/api/v1/auth/token/"
RUTA_RENOVACION = "/api/v1/auth/token/refresh/"
LISTA = "/api/v1/practicas/"
DETALLE = "/api/v1/practicas/{}/"
REPORTES = "/api/v1/practicas/{}/reportes/"
PAYLOAD = {"semana": 1, "horas_reportadas": 8}
CLAVE = "Clave-Segura-2026"
CLAVES_ENVELOPE = {"success", "message", "data", "errors", "meta"}
MENSAJE_401 = "Autenticación requerida."
MENSAJE_403 = "Permiso denegado."


class RecolectorDeLogs(logging.Handler):
    """Handler propio: recoge los registros existentes sin exigir que haya alguno."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.mensajes = []

    def emit(self, record):
        self.mensajes.append(record.getMessage())


@contextmanager
def captura_de_logs():
    """Recoge todos los registros del proceso y restaura el estado global al salir."""
    recolector = RecolectorDeLogs()
    raiz = logging.getLogger()
    nivel, deshabilitado = raiz.level, logging.root.manager.disable
    raiz.setLevel(logging.DEBUG)
    logging.disable(logging.NOTSET)
    raiz.addHandler(recolector)
    try:
        yield recolector
    finally:
        raiz.removeHandler(recolector)
        raiz.setLevel(nivel)
        logging.disable(deshabilitado)


class AuthFixturesMixin:
    """Dos carreras, seis roles con clave real y una práctica propia y otra ajena."""

    assertEqual: Callable[..., None]
    assertIs: Callable[..., None]
    assertIsInstance: Callable[..., None]
    assertIsNone: Callable[..., None]
    assertNotIn: Callable[..., None]
    assertTrue: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        for carrera in (cls.carrera, cls.otra_carrera):
            ConfiguracionCarrera.objects.create(
                carrera=carrera, modalidad="laboral", horas_requeridas=240,
                vigente_desde=date(2020, 1, 1),
            )
        cls.entidad = EntidadReceptora.objects.create(
            nombre="Junta Parroquial de San Lucas"
        )
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = cls.usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.par = cls.usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor_academico = cls.usuario(
            "academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.tutor_entidad = cls.usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.coordinador = cls.usuario("coordinador1", Usuario.Rol.COORDINADOR, cls.carrera)
        cls.coordinador_par = cls.usuario(
            "coordinador2", Usuario.Rol.COORDINADOR, cls.otra_carrera
        )
        cls.practica = asignar_practica(
            estudiante=cls.estudiante, carrera=cls.carrera, periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL, subtipo=str(Practica.Subtipo.PRACTICA),
            autor=cls.coordinador, entidad=cls.entidad,
            tutor_entidad=cls.tutor_entidad,
        )
        AsignacionTutor.objects.create(
            practica=cls.practica, tutor_academico=cls.tutor_academico,
            desde=date(2026, 1, 1),
        )
        cls.ajena = asignar_practica(
            estudiante=cls.par, carrera=cls.otra_carrera, periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL, subtipo=str(Practica.Subtipo.PRACTICA),
            autor=cls.coordinador_par, entidad=cls.entidad,
        )

    @classmethod
    def usuario(cls, username, rol, carrera=None):
        return Usuario.objects.create_user(
            username=username, nombre=username.title(),
            email=f"{username}@example.com", rol=rol, carrera=carrera, password=CLAVE,
        )

    def setUp(self):
        self.client = APIClient()

    def tokens(self, usuario):
        respuesta = self.client.post(
            RUTA_OBTENCION, {"username": usuario.username, "password": CLAVE}, format="json"
        )
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        return respuesta.json()["data"]

    def acceso(self, usuario):
        return self.tokens(usuario)["access"]

    def cliente_con(self, usuario):
        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {self.acceso(usuario)}")
        return cliente

    def token_vencido(self, usuario):
        token = AccessToken.for_user(usuario)
        token.set_exp(
            from_time=timezone.now() - timedelta(hours=1), lifetime=timedelta(minutes=5)
        )
        return str(token)

    def assert_envelope_error(self, respuesta, estado):
        self.assertEqual(respuesta.status_code, estado)
        cuerpo = respuesta.json()
        self.assertEqual(set(cuerpo), CLAVES_ENVELOPE)
        self.assertIs(cuerpo["success"], False)
        self.assertIsNone(cuerpo["data"])
        self.assertIsInstance(cuerpo["errors"], dict)
        return cuerpo


class SinCredencialesTests(AuthFixturesMixin, TestCase):
    """S4: 401 sin credenciales, con envelope, también donde sin auth habría 404."""

    def test_sin_credenciales_toda_la_api_real_responde_401(self):
        for metodo, url in (
            ("get", LISTA),
            ("get", DETALLE.format(self.practica.pk)),
            ("get", DETALLE.format(999_999)),
            ("post", REPORTES.format(self.practica.pk)),
        ):
            with self.subTest(metodo=metodo, url=url):
                respuesta = getattr(self.client, metodo)(url)

                cuerpo = self.assert_envelope_error(respuesta, 401)
                self.assertEqual(cuerpo["message"], MENSAJE_401)
                self.assertEqual(
                    cuerpo["errors"], {"detail": "Se requiere autenticación."}
                )
                self.assertTrue(respuesta["WWW-Authenticate"].startswith("Bearer"))
        self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_token_basura_alterado_o_vencido_responde_401(self):
        access = self.acceso(self.estudiante)
        casos = {
            "basura": "no-es-un-jwt",
            "firma_alterada": access[:-4] + "AAAA",
            "vencido": self.token_vencido(self.estudiante),
        }
        for caso, token in casos.items():
            with self.subTest(caso=caso):
                cliente = APIClient()
                cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
                respuesta = cliente.get(LISTA)

                cuerpo = self.assert_envelope_error(respuesta, 401)
                self.assertEqual(cuerpo["message"], MENSAJE_401)
                # Sin señal distinta para cada causa: no se aprende nada del token.
                self.assertEqual(
                    cuerpo["errors"], {"detail": "Se requiere autenticación."}
                )
                self.assertNotIn(token, respuesta.content.decode())

    def test_un_token_de_usuario_inactivo_o_borrado_responde_401(self):
        inactivo = Usuario.objects.create_user(
            username="inactivo1", nombre="Inactivo", email="inactivo1@example.com",
            rol=Usuario.Rol.ESTUDIANTE, password=CLAVE,
        )
        access_inactivo = self.acceso(inactivo)
        inactivo.is_active = False
        inactivo.save(update_fields=["is_active"])
        efimero = Usuario.objects.create_user(
            username="efimero1", nombre="Efimero", email="efimero1@example.com",
            rol=Usuario.Rol.ESTUDIANTE, password=CLAVE,
        )
        access_borrado = self.acceso(efimero)
        efimero.delete()

        for access in (access_inactivo, access_borrado):
            with self.subTest():
                cliente = APIClient()
                cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
                self.assert_envelope_error(cliente.get(LISTA), 401)


class ObtencionDeTokenTests(AuthFixturesMixin, TestCase):
    """D2: /auth/token/ y /auth/token/refresh/ responden con el envelope de #77."""

    def test_las_credenciales_correctas_devuelven_el_par_en_el_envelope(self):
        respuesta = self.client.post(
            RUTA_OBTENCION, {"username": self.estudiante.username, "password": CLAVE},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertEqual(set(cuerpo), CLAVES_ENVELOPE)
        self.assertIs(cuerpo["success"], True)
        self.assertEqual(set(cuerpo["data"]), {"access", "refresh"})
        self.assertIsNone(cuerpo["errors"])
        self.assertTrue(cuerpo["data"]["access"])
        self.assertTrue(cuerpo["data"]["refresh"])

    def test_el_access_emitido_abre_la_api_real_con_el_alcance_de_t019(self):
        respuesta = self.cliente_con(self.estudiante).get(LISTA)

        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], True)
        self.assertEqual({fila["id"] for fila in cuerpo["data"]}, {self.practica.pk})

    def test_un_refresh_de_cuenta_borrada_no_es_500(self):
        """F1 del verify: DoesNotExist del usuario no puede dejar un 500."""
        efimero = Usuario.objects.create_user(
            username="efimero2", nombre="Efimero", email="efimero2@example.com",
            rol=Usuario.Rol.ESTUDIANTE, password=CLAVE,
        )
        refresh = self.tokens(efimero)["refresh"]
        efimero.delete()

        cuerpo = self.assert_envelope_error(
            self.client.post(RUTA_RENOVACION, {"refresh": refresh}, format="json"), 401
        )

        self.assertEqual(cuerpo["message"], MENSAJE_401)
        self.assertNotIn(refresh, cuerpo["errors"]["detail"])
        self.assertIsNone(cuerpo["data"])

    def test_credenciales_incorrectas_responde_401_sin_eco_de_la_clave(self):
        for datos in (
            {"username": self.estudiante.username, "password": "clave-equivocada"},
            {"username": "no-existe", "password": CLAVE},
        ):
            with self.subTest(datos=datos):
                respuesta = self.client.post(RUTA_OBTENCION, datos, format="json")

                cuerpo = self.assert_envelope_error(respuesta, 401)
                self.assertEqual(cuerpo["message"], MENSAJE_401)
                self.assertNotIn("password", respuesta.content.decode())
                self.assertNotIn(CLAVE, respuesta.content.decode())
                self.assertIsNone(cuerpo["data"])

    def test_un_cuerpo_sin_credenciales_es_400_de_validacion(self):
        """El nombre del campo «password» sí viaja (es el contrato); su valor no."""
        for ruta in (RUTA_OBTENCION, RUTA_RENOVACION):
            with self.subTest(ruta=ruta):
                respuesta = self.client.post(ruta, {}, format="json")

                cuerpo = self.assert_envelope_error(respuesta, 400)
                self.assertEqual(cuerpo["message"], "Datos inválidos.")
                texto = respuesta.content.decode()
                for fuga in (CLAVE, "pbkdf2_sha256", "argon2"):
                    self.assertNotIn(fuga, texto)

    def test_el_refresh_renueva_el_access(self):
        refresh = self.tokens(self.estudiante)["refresh"]

        respuesta = self.client.post(RUTA_RENOVACION, {"refresh": refresh}, format="json")

        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], True)
        self.assertEqual(set(cuerpo["data"]), {"access"})
        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {cuerpo['data']['access']}")
        self.assertEqual(cliente.get(LISTA).status_code, 200)

    def test_las_dos_rutas_de_token_aparecen_en_el_esquema(self):
        documento = yaml.safe_load(self.client.get("/api/v1/schema/").content)

        for ruta in (RUTA_OBTENCION, RUTA_RENOVACION):
            with self.subTest(ruta=ruta):
                self.assertIn("post", documento["paths"][ruta])
                self.assertIn("200", documento["paths"][ruta]["post"]["responses"])

    def test_un_refresh_no_abre_la_api_ni_un_refresh_basura_devuelve_tokens(self):
        refresh = self.tokens(self.estudiante)["refresh"]
        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh}")
        self.assert_envelope_error(cliente.get(LISTA), 401)

        for datos in ({"refresh": "no-es-un-jwt"},):
            with self.subTest(datos=datos):
                respuesta = self.client.post(RUTA_RENOVACION, datos, format="json")
                cuerpo = self.assert_envelope_error(respuesta, 401)
                self.assertIsNone(cuerpo["data"])


class PermisosPorRolYObjetoTests(AuthFixturesMixin, TestCase):
    """S4: 403 por rol sin permiso y 403/404 al tocar una práctica ajena."""

    def test_un_rol_sin_permiso_en_la_ruta_responde_403(self):
        for usuario in (self.tutor_academico, self.tutor_entidad, self.coordinador):
            with self.subTest(usuario=usuario.username):
                respuesta = self.cliente_con(usuario).post(
                    REPORTES.format(self.practica.pk), PAYLOAD, format="json"
                )

                cuerpo = self.assert_envelope_error(respuesta, 403)
                self.assertEqual(cuerpo["message"], MENSAJE_403)
        self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_la_practica_ajena_en_el_detalle_responde_404(self):
        """Decisión: el detalle usa el row-scope de T019, así que lo ajeno no existe."""
        for usuario in (self.par, self.coordinador_par):
            with self.subTest(usuario=usuario.username):
                respuesta = self.cliente_con(usuario).get(
                    DETALLE.format(self.practica.pk)
                )

                respuesta_404 = self.assert_envelope_error(respuesta, 404)
                self.assertEqual(respuesta_404["message"], "Recurso no encontrado.")

    def test_la_practica_ajena_en_el_post_responde_403_sin_escribir(self):
        respuesta = self.cliente_con(self.par).post(
            REPORTES.format(self.practica.pk), PAYLOAD, format="json"
        )

        cuerpo = self.assert_envelope_error(respuesta, 403)
        self.assertEqual(cuerpo["message"], MENSAJE_403)
        self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_un_actor_autenticado_sin_fila_no_entra(self):
        cliente = APIClient()
        cliente.force_authenticate(user=Usuario(username="fantasma"))

        self.assert_envelope_error(cliente.get(LISTA), 403)
        self.assert_envelope_error(
            cliente.post(REPORTES.format(self.practica.pk), PAYLOAD, format="json"), 403
        )

    def test_el_dueno_conserva_el_flujo_de_78(self):
        """PRESERVE: con credenciales y rol, el comportamiento de #78 no cambia."""
        cliente = self.cliente_con(self.estudiante)

        self.assertEqual(cliente.get(LISTA).status_code, 200)
        self.assertEqual(cliente.get(DETALLE.format(self.practica.pk)).status_code, 200)
        respuesta = cliente.post(
            REPORTES.format(self.practica.pk), PAYLOAD, format="json"
        )
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(ReporteSemanal.objects.count(), 1)
        self.assertEqual(cliente.get("/api/v1/schema/").status_code, 200)


class SinFugasDeSecretosTests(AuthFixturesMixin, TestCase):
    """S4: ni la contraseña ni los tokens aparecen en respuestas ni en logs."""

    def test_las_respuestas_de_token_no_repiten_la_clave(self):
        obtencion = self.client.post(
            RUTA_OBTENCION, {"username": self.estudiante.username, "password": CLAVE},
            format="json",
        )
        datos = obtencion.json()["data"]
        refresco = self.client.post(
            RUTA_RENOVACION, {"refresh": datos["refresh"]}, format="json"
        )

        for respuesta in (obtencion, refresco):
            texto = respuesta.content.decode()
            self.assertNotIn("password", texto)
            self.assertNotIn(CLAVE, texto)
            self.assertNotIn("hasher", texto)

    def test_los_logs_de_las_rutas_de_token_no_cargan_clave_ni_tokens(self):
        with captura_de_logs() as registro:
            datos = self.client.post(
                RUTA_OBTENCION, {"username": self.estudiante.username, "password": CLAVE},
                format="json",
            ).json()["data"]
            self.client.post(
                RUTA_RENOVACION, {"refresh": datos["refresh"]}, format="json"
            )
            self.client.post(
                RUTA_OBTENCION,
                {"username": self.estudiante.username, "password": "equivocada"},
                format="json",
            )
            self.client.post(RUTA_RENOVACION, {"refresh": "basura"}, format="json")

        texto = "\n".join(registro.mensajes)
        for secreto in (CLAVE, "equivocada", datos["access"], datos["refresh"]):
            with self.subTest():
                self.assertNotIn(secreto, texto)

    def test_el_401_por_token_invalido_no_repite_el_token_recibido(self):
        inventado = "token-inventado-que-no-sirve"
        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {inventado}")

        with captura_de_logs() as registro:
            respuesta = cliente.get(LISTA)

        self.assert_envelope_error(respuesta, 401)
        self.assertNotIn(inventado, respuesta.content.decode())
        self.assertNotIn(inventado, "\n".join(registro.mensajes))
