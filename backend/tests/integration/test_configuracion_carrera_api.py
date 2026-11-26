"""``PUT /api/v1/carreras/{codigo}/configuracion/`` (RF-12, C-17, D1-D5).

Adaptador HTTP fino de ``guardar_configuracion``: el rol ``coordinador`` se
comprueba en ``initial()`` —antes de la carrera y del cuerpo—, la carrera se
busca por ``codigo`` (404 si no existe), el cuerpo es estricto (una modalidad por
llamada, sin claves ajenas) y el alcance de carrera lo decide el servicio contra
la fila **guardada** del actor: otro coordinador recibe 403.

D1: una sola modalidad por llamada. D2: editar con otra ``vigente_desde`` crea
una fila histórica nueva. D3: repetir con la misma fecha **actualiza** esa fila
(una sola por día). D4: el endpoint nunca toca ``Practica.horas_requeridas`` —
las prácticas existentes conservan lo copiado y solo las asignaciones nuevas
leen la configuración nueva (S6/S7).
"""

from collections.abc import Callable
from datetime import date
from typing import Any, Protocol, cast

from django.test import TestCase
from django.utils import timezone

from apps.carreras.api import MENSAJE_COORDINADOR_CONFIGURACION
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.carreras.serializers import (
    MENSAJE_CAMPO_NO_ADMITIDO_CONFIGURACION,
    MENSAJE_CUERPO_CONFIGURACION,
    MENSAJE_HORAS_REQUERIDAS,
    MENSAJE_PLAZOS,
    MENSAJE_UMBRAL_REZAGO,
)
from apps.practicas.models import Practica
from apps.usuarios.models import Usuario
from tests.integration.test_reportes_flujo import FlujoFixturesMixin, crear_usuario

CONFIGURACION = "/api/v1/carreras/{}/configuracion/"
CAMPOS_RESPUESTA = {
    "id",
    "carrera",
    "modalidad",
    "horas_requeridas",
    "plazo_reporte_dias",
    "plazo_revision_dias",
    "umbral_rezago",
    "vigente_desde",
}
CUERPO = {
    "modalidad": "laboral",
    "horas_requeridas": 300,
    "plazo_reporte_dias": 4,
    "plazo_revision_dias": 6,
    "umbral_rezago": 75,
}


def cuerpo_configuracion(**overrides: Any) -> dict[str, Any]:
    """Cuerpo válido del ``PUT``, vigente desde hoy, con los cambios pedidos."""
    return {**CUERPO, "vigente_desde": iso(hoy()), **overrides}


def hoy() -> date:
    """Fecha local del servidor, leída en cada uso y no al importar el módulo."""
    return timezone.localdate()


def iso(fecha: date) -> str:
    return fecha.strftime("%Y-%m-%d")


class RespuestaAPI(Protocol):
    """Lo que estas pruebas leen de la respuesta HTTP de la API.

    El cliente de pruebas de DRF devuelve un ``HttpResponse`` al que Django le
    agrega ``.json()`` en tiempo de ejecución; ni Django ni DRF declaran ese
    método, así que el contrato que usa la prueba se declara acá.
    """

    status_code: int
    content: bytes

    def json(self) -> Any: ...


class ConfiguracionFixturesMixin(FlujoFixturesMixin):
    """Reutiliza el flujo de reportes: dos carreras con configuración y seis roles."""

    carrera: Carrera
    otra_carrera: Carrera
    practica: Practica
    coordinador: Usuario
    coordinador_par: Usuario
    estudiante: Usuario
    par: Usuario
    director: Usuario
    secretaria: Usuario
    externo: Usuario
    tutor: Usuario

    assertEqual: Callable[..., None]
    assertIn: Callable[..., None]
    assertNotIn: Callable[..., None]
    assertTrue: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.director = crear_usuario("director1", Usuario.Rol.DIRECTOR, cls.carrera)
        cls.secretaria = crear_usuario(
            "secretaria1", Usuario.Rol.SECRETARIA, cls.carrera
        )

    def configurar(self, usuario, cuerpo=None, codigo=None) -> RespuestaAPI:
        """``PUT`` de la ruta con el cuerpo JSON pedido (por defecto, uno válido)."""
        destino = self.carrera.codigo if codigo is None else codigo
        datos = cuerpo_configuracion() if cuerpo is None else cuerpo
        respuesta = self.cliente(usuario).put(
            CONFIGURACION.format(destino), datos, format="json"
        )
        # El cliente de pruebas de DRF no declara el tipo de su respuesta.
        return cast(RespuestaAPI, respuesta)

    def assertExito(self, respuesta, estado=200):
        self.assertEqual(respuesta.status_code, estado)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["success"], True)
        self.assertEqual(cuerpo["message"], "Operación exitosa.")
        self.assertEqual(cuerpo["errors"], None)
        self.assertEqual(cuerpo["meta"], {})
        return cuerpo["data"]

    def assertRechazo(self, respuesta, estado, mensaje, errores):
        self.assertEqual(respuesta.status_code, estado)
        self.assertEqual(
            respuesta.json(),
            {
                "success": False,
                "message": mensaje,
                "data": None,
                "errors": errores,
                "meta": {},
            },
        )

    def filas_de_hoy(self, modalidad="laboral", carrera=None):
        return ConfiguracionCarrera.objects.filter(
            carrera=carrera or self.carrera,
            modalidad=modalidad,
            vigente_desde=hoy(),
        )

    def fotografia_practicas(self):
        """Horas y estado de cada práctica: el endpoint no las toca (D4)."""
        return tuple(
            Practica.objects.order_by("pk").values_list(
                "pk", "horas_requeridas", "estado"
            )
        )


class ConfiguracionGuardarTests(ConfiguracionFixturesMixin, TestCase):
    """El coordinador de la carrera guarda la configuración y la ve devuelta."""

    def test_guarda_la_configuracion_y_devuelve_la_fila_guardada(self):
        data = self.assertExito(self.configurar(self.coordinador))

        self.assertEqual(set(data), CAMPOS_RESPUESTA)
        self.assertEqual(data["carrera"], self.carrera.codigo)
        self.assertEqual(data["modalidad"], "laboral")
        self.assertEqual(data["horas_requeridas"], 300)
        self.assertEqual(data["plazo_reporte_dias"], 4)
        self.assertEqual(data["plazo_revision_dias"], 6)
        self.assertEqual(data["umbral_rezago"], 75)
        self.assertEqual(data["vigente_desde"], iso(hoy()))
        guardada = ConfiguracionCarrera.objects.get(pk=data["id"])
        self.assertEqual(guardada.carrera, self.carrera)
        self.assertEqual(guardada.horas_requeridas, 300)
        self.assertEqual(guardada.umbral_rezago, 75)

    def test_cada_modalidad_se_guarda_por_separado(self):
        self.assertExito(self.configurar(self.coordinador))
        data = self.assertExito(
            self.configurar(
                self.coordinador, cuerpo_configuracion(modalidad="comunitaria")
            )
        )

        self.assertEqual(data["modalidad"], "comunitaria")
        self.assertEqual(self.filas_de_hoy("laboral").count(), 1)
        self.assertEqual(self.filas_de_hoy("comunitaria").count(), 1)

    def test_los_plazos_y_el_umbral_se_guardan_en_la_fila_de_la_modalidad(self):
        """S6: plazos y umbral no se copian a la práctica; viven en la fila."""
        self.assertExito(
            self.configurar(
                self.coordinador,
                cuerpo_configuracion(
                    plazo_reporte_dias=2,
                    plazo_revision_dias=7,
                    umbral_rezago=100,
                ),
            )
        )

        guardada = self.filas_de_hoy().get()
        self.assertEqual(
            (
                guardada.plazo_reporte_dias,
                guardada.plazo_revision_dias,
                guardada.umbral_rezago,
            ),
            (2, 7, 100),
        )


class ConfiguracionPracticasNuevasTests(ConfiguracionFixturesMixin, TestCase):
    """S6/S7 y D4: solo las asignaciones nuevas leen las horas nuevas."""

    def test_una_practica_asignada_despues_copia_las_horas_nuevas(self):
        self.assertExito(
            self.configurar(
                self.coordinador, cuerpo_configuracion(horas_requeridas=480)
            )
        )

        nueva = self.crear(self.par)

        self.assertEqual(nueva.horas_requeridas, 480)
        self.assertEqual(Practica.objects.get(pk=nueva.pk).horas_requeridas, 480)

    def test_una_practica_existente_conserva_las_horas_ya_copiadas(self):
        """La garantía central de S7: editar la configuración no reescribe la práctica."""
        antes = Practica.objects.get(pk=self.practica.pk).horas_requeridas
        self.assertEqual(antes, 240)

        self.assertExito(
            self.configurar(
                self.coordinador, cuerpo_configuracion(horas_requeridas=480)
            )
        )

        despues = Practica.objects.get(pk=self.practica.pk).horas_requeridas
        self.assertEqual(despues, antes)

    def test_el_endpoint_no_escribe_ninguna_practica(self):
        antes = self.fotografia_practicas()

        self.assertExito(
            self.configurar(
                self.coordinador, cuerpo_configuracion(horas_requeridas=999)
            )
        )

        self.assertEqual(self.fotografia_practicas(), antes)


class ConfiguracionUpsertEHistorialTests(ConfiguracionFixturesMixin, TestCase):
    """D2/D3: misma fecha actualiza la fila; otra fecha agrega una histórica."""

    def test_repetir_el_put_el_mismo_dia_actualiza_la_misma_fila(self):
        primero = self.assertExito(self.configurar(self.coordinador))

        segundo = self.assertExito(
            self.configurar(
                self.coordinador, cuerpo_configuracion(horas_requeridas=360)
            )
        )

        self.assertEqual(segundo["id"], primero["id"])
        self.assertEqual(segundo["horas_requeridas"], 360)
        self.assertEqual(self.filas_de_hoy().count(), 1)
        self.assertEqual(self.filas_de_hoy().get().horas_requeridas, 360)

    def test_otra_fecha_de_vigencia_crea_una_fila_historica(self):
        primero = self.assertExito(
            self.configurar(
                self.coordinador, cuerpo_configuracion(vigente_desde="2026-01-05")
            )
        )
        segundo = self.assertExito(
            self.configurar(
                self.coordinador, cuerpo_configuracion(vigente_desde="2026-02-05")
            )
        )

        self.assertNotEqual(segundo["id"], primero["id"])
        historicas = ConfiguracionCarrera.objects.filter(
            carrera=self.carrera, modalidad="laboral"
        )
        self.assertEqual(
            list(
                historicas.order_by("vigente_desde").values_list(
                    "vigente_desde", flat=True
                )
            ),
            [date(2020, 1, 1), date(2026, 1, 5), date(2026, 2, 5)],
        )
        self.assertEqual(historicas.get(pk=primero["id"]).horas_requeridas, 300)

    def test_el_historial_conserva_la_configuracion_anterior_intacta(self):
        anterior = self.assertExito(
            self.configurar(
                self.coordinador, cuerpo_configuracion(vigente_desde="2026-01-05")
            )
        )
        self.assertExito(
            self.configurar(
                self.coordinador, cuerpo_configuracion(vigente_desde="2026-02-05")
            )
        )

        self.assertEqual(
            ConfiguracionCarrera.objects.get(pk=anterior["id"]).horas_requeridas, 300
        )


class ConfiguracionAlcanceTests(ConfiguracionFixturesMixin, TestCase):
    """D5: solo el coordinador de esa carrera; rol ajeno 403 y carrera 404."""

    def test_otro_coordinador_recibe_403_sin_escribir(self):
        antes = ConfiguracionCarrera.objects.count()

        self.assertRechazo(
            self.configurar(self.coordinador_par),
            403,
            "Permiso denegado.",
            {
                "detail": MENSAJE_COORDINADOR_CONFIGURACION,
                "code": "permiso_denegado",
            },
        )
        self.assertEqual(ConfiguracionCarrera.objects.count(), antes)
        self.assertEqual(self.filas_de_hoy().count(), 0)

    def test_los_demas_roles_reciben_403_sin_escribir(self):
        antes = ConfiguracionCarrera.objects.count()
        actores = {
            "estudiante": self.estudiante,
            "tutor_academico": self.tutor,
            "tutor_entidad": self.externo,
            "director": self.director,
            "secretaria": self.secretaria,
        }
        for rol, actor in actores.items():
            with self.subTest(rol=rol):
                self.assertRechazo(
                    self.configurar(actor),
                    403,
                    "Permiso denegado.",
                    {
                        "detail": MENSAJE_COORDINADOR_CONFIGURACION,
                        "code": "permiso_denegado",
                    },
                )
        self.assertEqual(ConfiguracionCarrera.objects.count(), antes)

    def test_el_rol_se_comprueba_antes_que_la_carrera_y_el_cuerpo(self):
        """Un rol ajeno recibe 403 aunque el código no exista ni el cuerpo valga."""
        respuesta = self.configurar(self.estudiante, {}, codigo="NO-EXISTE")

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(respuesta.json()["errors"]["code"], "permiso_denegado")

    def test_un_codigo_de_carrera_inexistente_responde_404_sin_escribir(self):
        antes = ConfiguracionCarrera.objects.count()

        self.assertRechazo(
            self.configurar(self.coordinador, codigo="NO-EXISTE"),
            404,
            "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertEqual(ConfiguracionCarrera.objects.count(), antes)

    def test_sin_token_responde_401_con_el_envelope(self):
        antes = ConfiguracionCarrera.objects.count()

        self.assertRechazo(
            self.configurar(None),
            401,
            "Autenticación requerida.",
            {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
        )
        self.assertEqual(ConfiguracionCarrera.objects.count(), antes)

    def test_una_cuenta_inactiva_responde_401_sin_escribir(self):
        inactivo = crear_usuario("coordinador3", Usuario.Rol.COORDINADOR, self.carrera)
        Usuario.objects.filter(pk=inactivo.pk).update(is_active=False)
        antes = ConfiguracionCarrera.objects.count()

        self.assertRechazo(
            self.configurar(inactivo),
            401,
            "Autenticación requerida.",
            {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
        )
        self.assertEqual(ConfiguracionCarrera.objects.count(), antes)


class ConfiguracionValidacionTests(ConfiguracionFixturesMixin, TestCase):
    """D5: valores fuera de rango y claves ajenas responden 400 en su campo."""

    def rechazar_campo(self, campo, mensaje, cuerpo):
        antes = ConfiguracionCarrera.objects.count()
        antes_practicas = self.fotografia_practicas()

        self.assertRechazo(
            self.configurar(self.coordinador, cuerpo),
            400,
            "Datos inválidos.",
            {campo: [mensaje]},
        )

        self.assertEqual(ConfiguracionCarrera.objects.count(), antes)
        self.assertEqual(self.fotografia_practicas(), antes_practicas)

    def test_cero_horas_requeridas_se_rechaza_en_su_campo(self):
        self.rechazar_campo(
            "horas_requeridas",
            MENSAJE_HORAS_REQUERIDAS,
            {**CUERPO, "horas_requeridas": 0, "vigente_desde": iso(hoy())},
        )

    def test_umbral_rezago_sobre_100_se_rechaza_en_su_campo(self):
        self.rechazar_campo(
            "umbral_rezago",
            MENSAJE_UMBRAL_REZAGO,
            {**CUERPO, "umbral_rezago": 101, "vigente_desde": iso(hoy())},
        )

    def test_plazos_negativos_se_rechazan_en_su_campo(self):
        for campo in ("plazo_reporte_dias", "plazo_revision_dias"):
            with self.subTest(campo=campo):
                self.rechazar_campo(
                    campo,
                    MENSAJE_PLAZOS,
                    {**CUERPO, campo: -1, "vigente_desde": iso(hoy())},
                )

    def test_una_clave_ajena_se_rechaza_sin_escribir(self):
        for campo in ("autor", "id", "carrera", "estado"):
            with self.subTest(campo=campo):
                self.rechazar_campo(
                    campo,
                    MENSAJE_CAMPO_NO_ADMITIDO_CONFIGURACION,
                    {**CUERPO, campo: "x", "vigente_desde": iso(hoy())},
                )

    def test_un_cuerpo_que_no_es_objeto_responde_400(self):
        for cuerpo in ([{"modalidad": "laboral"}], ["modalidad"], "laboral", 7):
            with self.subTest(cuerpo=cuerpo):
                self.rechazar_campo(
                    "non_field_errors", MENSAJE_CUERPO_CONFIGURACION, cuerpo
                )

    def test_los_campos_obligatorios_faltantes_se_rechazan(self):
        antes = ConfiguracionCarrera.objects.count()
        respuesta = self.configurar(self.coordinador, {"modalidad": "laboral"})

        self.assertEqual(respuesta.status_code, 400)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["message"], "Datos inválidos.")
        self.assertEqual(
            set(cuerpo["errors"]),
            {
                "horas_requeridas",
                "plazo_reporte_dias",
                "plazo_revision_dias",
                "umbral_rezago",
                "vigente_desde",
            },
        )
        self.assertEqual(ConfiguracionCarrera.objects.count(), antes)

    def test_una_modalidad_fuera_de_laboral_o_comunitaria_se_rechaza(self):
        antes = ConfiguracionCarrera.objects.count()

        respuesta = self.configurar(
            self.coordinador, cuerpo_configuracion(modalidad="virtual")
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(list(respuesta.json()["errors"]), ["modalidad"])
        self.assertEqual(ConfiguracionCarrera.objects.count(), antes)
