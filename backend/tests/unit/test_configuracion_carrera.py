"""Tests del modelo y del servicio de configuración por carrera (RF-12).

El modelo conserva solo las dos ``CheckConstraint`` (horas positivas, umbral
hasta 100): D3 revisada deja la idempotencia del mismo día en
``guardar_configuracion``, no en una ``UniqueConstraint``, para no romper el
desempate ``-vigente_desde, -pk`` que ya fijan las pruebas de asignación y de
alertas.
"""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.carreras.services import (
    MENSAJE_COORDINADOR_CONFIGURACION,
    guardar_configuracion,
)
from apps.usuarios.models import Usuario

VIGENTE_DESDE = date(2025, 3, 1)


def crear_carrera(codigo="ING-SIS", nombre="Ingeniería de Sistemas"):
    return Carrera.objects.create(codigo=codigo, nombre=nombre)


def crear_usuario(username, carrera, rol=Usuario.Rol.COORDINADOR):
    return Usuario.objects.create_user(
        username=username,
        nombre=username.title(),
        email=f"{username}@example.com",
        rol=rol,
        carrera=carrera,
        password=None,
    )


def crear_configuracion(carrera, **overrides):
    datos = {
        "carrera": carrera,
        "modalidad": ConfiguracionCarrera.Modalidad.LABORAL,
        "horas_requeridas": 240,
        "vigente_desde": VIGENTE_DESDE,
    }
    datos.update(overrides)
    return ConfiguracionCarrera.objects.create(**datos)


class CarreraTests(TestCase):
    """codigo es único y nombre es obligatorio; nada se guarda si el alta falla."""

    def test_codigo_duplicado_es_rechazado_sin_guardar_la_fila_nueva(self):
        crear_carrera()
        duplicada = Carrera(codigo="ING-SIS", nombre="Otra carrera")

        with self.assertRaises(ValidationError) as error:
            duplicada.full_clean()

        self.assertIn("codigo", error.exception.message_dict)
        self.assertEqual(Carrera.objects.count(), 1)

    def test_codigo_duplicado_tambien_es_rechazado_por_la_base_de_datos(self):
        crear_carrera()

        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrera.objects.create(codigo="ING-SIS", nombre="Otra carrera")

        self.assertEqual(Carrera.objects.count(), 1)
        self.assertEqual(Carrera.objects.get().nombre, "Ingeniería de Sistemas")

    def test_nombre_es_obligatorio(self):
        sin_nombre = Carrera(codigo="DER-001")

        with self.assertRaises(ValidationError) as error:
            sin_nombre.full_clean()

        self.assertIn("nombre", error.exception.message_dict)
        self.assertEqual(Carrera.objects.count(), 0)

    def test_codigo_es_obligatorio(self):
        sin_codigo = Carrera(nombre="Carrera sin código")

        with self.assertRaises(ValidationError) as error:
            sin_codigo.full_clean()

        self.assertIn("codigo", error.exception.message_dict)
        self.assertEqual(Carrera.objects.count(), 0)


class ConfiguracionCarreraPorDefectoTests(TestCase):
    """plazo_reporte_dias=3, plazo_revision_dias=5 y umbral_rezago=80 (RF-12)."""

    def setUp(self):
        self.carrera = crear_carrera()

    def test_valores_por_defecto_de_plazos_y_umbral(self):
        configuracion = crear_configuracion(self.carrera)
        configuracion.refresh_from_db()

        self.assertEqual(configuracion.plazo_reporte_dias, 3)
        self.assertEqual(configuracion.plazo_revision_dias, 5)
        self.assertEqual(configuracion.umbral_rezago, 80)

    def test_horas_requeridas_no_tiene_valor_por_defecto(self):
        sin_horas = ConfiguracionCarrera(
            carrera=self.carrera,
            modalidad=ConfiguracionCarrera.Modalidad.LABORAL,
            vigente_desde=VIGENTE_DESDE,
        )

        self.assertIsNone(sin_horas.horas_requeridas)

        with self.assertRaises(ValidationError) as error:
            sin_horas.full_clean()

        self.assertIn("horas_requeridas", error.exception.message_dict)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_horas_requeridas_ausentes_son_rechazadas_por_la_base_de_datos(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConfiguracionCarrera.objects.create(
                carrera=self.carrera,
                modalidad=ConfiguracionCarrera.Modalidad.LABORAL,
                vigente_desde=VIGENTE_DESDE,
            )

        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_horas_definidas_por_la_carrera_se_guardan(self):
        configuracion = crear_configuracion(self.carrera, horas_requeridas=480)
        configuracion.refresh_from_db()

        self.assertEqual(configuracion.horas_requeridas, 480)


class ConfiguracionCarreraValidacionTests(TestCase):
    """carrera, modalidad y vigente_desde obligatorios; modalidad laboral/comunitaria."""

    def setUp(self):
        self.carrera = crear_carrera()

    def test_carrera_es_obligatoria(self):
        sin_carrera = ConfiguracionCarrera(
            modalidad=ConfiguracionCarrera.Modalidad.LABORAL,
            horas_requeridas=240,
            vigente_desde=VIGENTE_DESDE,
        )

        with self.assertRaises(ValidationError) as error:
            sin_carrera.full_clean()

        self.assertIn("carrera", error.exception.message_dict)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_carrera_ausente_es_rechazada_por_la_base_de_datos(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConfiguracionCarrera.objects.create(
                modalidad=ConfiguracionCarrera.Modalidad.LABORAL,
                horas_requeridas=240,
                vigente_desde=VIGENTE_DESDE,
            )

        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_modalidad_es_obligatoria(self):
        sin_modalidad = ConfiguracionCarrera(
            carrera=self.carrera,
            horas_requeridas=240,
            vigente_desde=VIGENTE_DESDE,
        )

        with self.assertRaises(ValidationError) as error:
            sin_modalidad.full_clean()

        self.assertIn("modalidad", error.exception.message_dict)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_modalidad_fuera_de_laboral_o_comunitaria_es_rechazada(self):
        invalida = ConfiguracionCarrera(
            carrera=self.carrera,
            modalidad="virtual",
            horas_requeridas=240,
            vigente_desde=VIGENTE_DESDE,
        )

        with self.assertRaises(ValidationError) as error:
            invalida.full_clean()

        self.assertIn("modalidad", error.exception.message_dict)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_ambas_modalidades_son_aceptadas(self):
        laboral = crear_configuracion(self.carrera)
        comunitaria = crear_configuracion(
            self.carrera, modalidad=ConfiguracionCarrera.Modalidad.COMUNITARIA
        )

        self.assertEqual(laboral.modalidad, "laboral")
        self.assertEqual(comunitaria.modalidad, "comunitaria")
        self.assertEqual(ConfiguracionCarrera.objects.count(), 2)

    def test_vigente_desde_es_obligatoria(self):
        sin_vigencia = ConfiguracionCarrera(
            carrera=self.carrera,
            modalidad=ConfiguracionCarrera.Modalidad.LABORAL,
            horas_requeridas=240,
        )

        with self.assertRaises(ValidationError) as error:
            sin_vigencia.full_clean()

        self.assertIn("vigente_desde", error.exception.message_dict)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_vigente_desde_ausente_es_rechazada_por_la_base_de_datos(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConfiguracionCarrera.objects.create(
                carrera=self.carrera,
                modalidad=ConfiguracionCarrera.Modalidad.LABORAL,
                horas_requeridas=240,
            )

        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)


class ConfiguracionCarreraHistorialTests(TestCase):
    """Se permiten varias configuraciones históricas de la misma carrera y modalidad."""

    def test_se_guardan_varias_configuraciones_de_la_misma_carrera(self):
        carrera = crear_carrera()
        primera = crear_configuracion(carrera, vigente_desde=date(2024, 3, 1))
        segunda = crear_configuracion(carrera, vigente_desde=VIGENTE_DESDE)

        self.assertNotEqual(primera.pk, segunda.pk)
        self.assertEqual(primera.modalidad, segunda.modalidad)
        self.assertEqual(
            ConfiguracionCarrera.objects.filter(carrera=carrera).count(), 2
        )

    def test_dos_modalidades_el_mismo_dia_son_filas_distintas(self):
        carrera = crear_carrera()
        laboral = crear_configuracion(carrera)
        comunitaria = crear_configuracion(
            carrera, modalidad=ConfiguracionCarrera.Modalidad.COMUNITARIA
        )

        self.assertNotEqual(laboral.pk, comunitaria.pk)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 2)


class GuardarConfiguracionTests(TestCase):
    """D3 revisada: la idempotencia del mismo día la da el servicio, no la base."""

    def setUp(self):
        self.carrera = crear_carrera()
        self.otra_carrera = crear_carrera("DER-001", "Derecho")
        self.coordinador = crear_usuario("coordinador1", self.carrera)
        self.coordinador_par = crear_usuario("coordinador2", self.otra_carrera)

    def datos(self, **overrides):
        base = {
            "modalidad": ConfiguracionCarrera.Modalidad.LABORAL,
            "horas_requeridas": 300,
            "plazo_reporte_dias": 4,
            "plazo_revision_dias": 6,
            "umbral_rezago": 75,
            "vigente_desde": VIGENTE_DESDE,
        }
        base.update(overrides)
        return base

    def guardar(self, autor=None, **overrides):
        return guardar_configuracion(
            carrera=self.carrera,
            autor=self.coordinador if autor is None else autor,
            datos=self.datos(**overrides),
        )

    def test_repetir_la_misma_fecha_actualiza_la_fila_sin_duplicar(self):
        primera = self.guardar()

        segunda = self.guardar(horas_requeridas=480, umbral_rezago=100)

        self.assertEqual(segunda.pk, primera.pk)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 1)
        guardada = ConfiguracionCarrera.objects.get()
        self.assertEqual(
            (guardada.horas_requeridas, guardada.umbral_rezago), (480, 100)
        )

    def test_otra_fecha_de_vigencia_agrega_una_fila_historica(self):
        primera = self.guardar()

        segunda = self.guardar(vigente_desde=date(2025, 4, 1), horas_requeridas=480)

        self.assertNotEqual(segunda.pk, primera.pk)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 2)
        self.assertEqual(
            ConfiguracionCarrera.objects.get(pk=primera.pk).horas_requeridas, 300
        )

    def test_cada_modalidad_se_guarda_en_su_propia_fila(self):
        laboral = self.guardar()
        comunitaria = self.guardar(modalidad=ConfiguracionCarrera.Modalidad.COMUNITARIA)

        self.assertNotEqual(comunitaria.pk, laboral.pk)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 2)

    def test_el_coordinador_de_otra_carrera_no_escribe(self):
        with self.assertRaises(ValidationError) as error:
            self.guardar(autor=self.coordinador_par)

        self.assertEqual(
            error.exception.message_dict["autor"],
            [MENSAJE_COORDINADOR_CONFIGURACION],
        )
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_un_rol_ajeno_al_coordinador_no_escribe(self):
        for rol in (
            Usuario.Rol.ESTUDIANTE,
            Usuario.Rol.TUTOR_ACADEMICO,
            Usuario.Rol.TUTOR_ENTIDAD,
            Usuario.Rol.DIRECTOR,
            Usuario.Rol.SECRETARIA,
        ):
            with self.subTest(rol=rol):
                ajeno = crear_usuario(f"ajeno-{rol}", self.carrera, rol=rol)

                with self.assertRaises(ValidationError) as error:
                    self.guardar(autor=ajeno)

                self.assertEqual(
                    error.exception.message_dict["autor"],
                    [MENSAJE_COORDINADOR_CONFIGURACION],
                )
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_un_valor_fuera_de_rango_del_modelo_no_escribe(self):
        """La ``CheckConstraint`` del umbral es la última defensa: no escribe.

        El 400 por campo lo da el serializer (``umbral_rezago`` entre 0 y 100);
        acá se fija que el modelo, si se lo salta, rechaza bajo ``__all__`` y sin
        dejar filas.
        """
        with self.assertRaises(ValidationError) as error:
            self.guardar(umbral_rezago=101)

        self.assertEqual(
            error.exception.message_dict["__all__"],
            ["El umbral de rezago es un porcentaje: máximo 100."],
        )
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)


class ConfiguracionCarreraRestriccionesEnBaseTests(TestCase):
    """Horas positivas y umbral de rezago como porcentaje, impuestos en la base."""

    def test_cero_horas_es_rechazado_por_la_base(self):
        carrera = crear_carrera()

        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_configuracion(carrera, horas_requeridas=0)

        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_umbral_sobre_100_es_rechazado_por_la_base_y_por_full_clean(self):
        carrera = crear_carrera()

        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_configuracion(carrera, umbral_rezago=101)
        with self.assertRaises(ValidationError):
            ConfiguracionCarrera(
                carrera=carrera,
                modalidad="laboral",
                horas_requeridas=240,
                umbral_rezago=101,
                vigente_desde=VIGENTE_DESDE,
            ).full_clean()

        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_umbral_de_100_se_guarda(self):
        crear_configuracion(crear_carrera(), umbral_rezago=100)

        self.assertEqual(ConfiguracionCarrera.objects.get().umbral_rezago, 100)


class ConfiguracionCarreraProteccionTests(TestCase):
    """La configuración vigente se conserva: no se elimina en cascada con la carrera."""

    def test_eliminar_una_carrera_con_configuracion_es_rechazado(self):
        carrera = crear_carrera()
        configuracion = crear_configuracion(carrera)

        with self.assertRaises(ProtectedError), transaction.atomic():
            carrera.delete()

        self.assertTrue(Carrera.objects.filter(pk=carrera.pk).exists())
        self.assertTrue(
            ConfiguracionCarrera.objects.filter(pk=configuracion.pk).exists()
        )
