"""Tests del servicio interno que registra la fecha real de inicio (T10, S1/S3).

RF-11: solo el coordinador activo de la carrera de la práctica declara la fecha
real de inicio, y solo mientras la práctica está «en curso». Es una acción
interna de dominio: no hay endpoint, formulario ni tarea programada, y no cambia
el estado ni el ``HistorialEstado``.

El bloqueo de filas solo se prueba en PostgreSQL: en SQLite esa prueba se omite.
La primera escritura también se defiende con la actualización condicional, que sí
se prueba en SQLite.
"""

import contextlib
import threading
import time
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import connections, transaction
from django.db.models.query import QuerySet
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone

from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera
from apps.practicas.models import Practica
from apps.practicas.services import (
    MENSAJE_AUTOR_INICIO,
    MENSAJE_COORDINADOR,
    MENSAJE_COORDINADOR_INICIO,
    MENSAJE_ESTADO_INICIO,
    MENSAJE_FECHA_FUTURA,
    MENSAJE_FECHA_TIPO,
    MENSAJE_FECHA_YA_REGISTRADA,
    MENSAJE_PRACTICA_INICIO,
    cambiar_estado_practica,
    registrar_inicio_practica,
)
from apps.usuarios.models import Usuario
from tests.unit.test_historial_estado import HistorialEstadoFixturesMixin

Estado = Practica.Estado


def hoy() -> date:
    """Fecha local del servidor, leída en cada uso y no al importar el módulo."""
    return timezone.localdate()


def hace(dias: int) -> date:
    """Fecha local desplazada ``dias`` (negativo = futuro)."""
    return hoy() - timedelta(days=dias)


# Distingue «no se pasó la fecha» de «se pasó None explícitamente».
OMITIDO = object()


class InicioFixturesMixin(HistorialEstadoFixturesMixin):
    """Práctica, carrera y usuarios de ``test_historial_estado`` más las fechas."""

    assertEqual: Callable[..., None]
    assertIsNone: Callable[..., None]
    assertNotEqual: Callable[..., None]
    assertRaises: Callable[..., Any]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        cls.coordinador_ajeno = Usuario.objects.create_user(
            username="coordinador2",
            nombre="Rosa Vega",
            email="rosa@example.com",
            rol=Usuario.Rol.COORDINADOR,
            carrera=cls.otra_carrera,
            password=None,
        )
        cls.tutor_entidad = Usuario.objects.create_user(
            username="entidad1",
            nombre="Pedro Maza",
            email="pedro@example.com",
            rol=Usuario.Rol.TUTOR_ENTIDAD,
            password=None,
        )
        cls.director = Usuario.objects.create_user(
            username="director1",
            nombre="Elena Ortiz",
            email="elena@example.com",
            rol=Usuario.Rol.DIRECTOR,
            carrera=cls.carrera,
            password=None,
        )
        cls.secretaria = Usuario.objects.create_user(
            username="secretaria1",
            nombre="Iván Pardo",
            email="ivan@example.com",
            rol=Usuario.Rol.SECRETARIA,
            carrera=cls.carrera,
            password=None,
        )

    def situar(self, estado, practica=None):
        """Deja la práctica en ``estado`` sin pasar por el servicio (preparación)."""
        objetivo = practica or self.practica
        Practica.objects.filter(pk=objetivo.pk).update(estado=estado)
        objetivo.refresh_from_db()
        return objetivo

    def en_curso(self, practica=None):
        return self.situar(Estado.EN_CURSO, practica)

    def guardar_fecha(self, fecha, practica=None):
        """Escribe una fecha previa en la fila, sin pasar por el servicio."""
        objetivo = practica or self.practica
        Practica.objects.filter(pk=objetivo.pk).update(fecha_inicio_real=fecha)
        objetivo.refresh_from_db()
        return objetivo

    def declarar(self, fecha=OMITIDO, practica=None, autor=None, **kwargs):
        """Llama al servicio; con ``OMITIDO`` no se envía el argumento ``fecha``."""
        argumentos = {
            "practica": practica or self.practica,
            "autor": autor or self.autor,
        }
        if fecha is not OMITIDO:
            argumentos["fecha"] = fecha
        argumentos.update(kwargs)
        return registrar_inicio_practica(**argumentos)

    def afirmar_sin_escritura(self, estado, practica=None):
        """El rechazo no cambia estado, fecha real ni historial."""
        objetivo = practica or self.practica
        objetivo.refresh_from_db()
        self.assertEqual(objetivo.estado, estado)
        self.assertIsNone(objetivo.fecha_inicio_real)
        self.assertEqual(HistorialEstado.objects.filter(practica=objetivo).count(), 0)

    def rechazar(
        self, fecha, campo, mensaje, estado=Estado.EN_CURSO, practica=None, autor=None
    ):
        """Rechazo con ese autor: el mensaje es exactamente el del campo indicado."""
        objetivo = self.situar(estado, practica)
        with self.assertRaises(ValidationError) as error:
            self.declarar(fecha, practica=objetivo, autor=autor)
        self.assertEqual(error.exception.message_dict, {campo: [mensaje]})
        self.afirmar_sin_escritura(estado, objetivo)

    def rechazar_fecha(self, valor, mensaje):
        """Rechazo de la fecha (admite ``None`` como valor explícito)."""
        objetivo = self.situar(Estado.EN_CURSO)
        with self.assertRaises(ValidationError) as error:
            self.declarar(valor, practica=objetivo)
        self.assertEqual(error.exception.message_dict, {"fecha": [mensaje]})
        self.afirmar_sin_escritura(Estado.EN_CURSO, objetivo)


class RegistrarInicioExitoTests(InicioFixturesMixin, TestCase):
    """La declaración del coordinador de la carrera guarda solo la fecha real."""

    def test_el_coordinador_de_la_misma_carrera_guarda_la_fecha(self):
        practica = self.en_curso()
        fecha = hace(30)

        resultado = self.declarar(fecha, practica=practica)

        self.assertEqual(resultado.pk, practica.pk)
        self.assertEqual(resultado.fecha_inicio_real, fecha)
        self.assertEqual(Practica.objects.get(pk=practica.pk).fecha_inicio_real, fecha)

    def test_solo_cambia_la_fecha_real_de_inicio(self):
        practica = self.en_curso()
        antes = Practica.objects.filter(pk=practica.pk).values().get()
        fecha = hace(30)

        self.declarar(fecha, practica=practica)

        despues = Practica.objects.filter(pk=practica.pk).values().get()
        sin_fecha = {k: v for k, v in despues.items() if k != "fecha_inicio_real"}
        self.assertEqual(
            sin_fecha, {k: v for k, v in antes.items() if k != "fecha_inicio_real"}
        )
        self.assertEqual(despues["fecha_inicio_real"], fecha)

    def test_no_escribe_estado_ni_historial(self):
        practica = self.en_curso()
        previo = self.registrar(anterior=Estado.ASIGNADA, nuevo=Estado.EN_CURSO)

        self.declarar(hace(30), practica=practica)

        self.assertEqual(Practica.objects.get(pk=practica.pk).estado, Estado.EN_CURSO)
        registros = list(HistorialEstado.objects.filter(practica=practica))
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0].pk, previo.pk)
        self.assertEqual(
            (
                registros[0].estado_anterior,
                registros[0].estado_nuevo,
                registros[0].motivo,
            ),
            (Estado.ASIGNADA, Estado.EN_CURSO, ""),
        )


class RegistrarInicioAutorizacionTests(InicioFixturesMixin, TestCase):
    """Sin rol, sin carrera, otra carrera o cuenta inactiva: rechazo sin escritura."""

    def test_los_demas_roles_son_rechazados(self):
        autores = {
            "estudiante": self.estudiante,
            "tutor_academico": self.tutor,
            "tutor_entidad": self.tutor_entidad,
            "director": self.director,
            "secretaria": self.secretaria,
        }
        for rol, autor in autores.items():
            with self.subTest(rol=rol):
                self.rechazar(
                    hace(30), "autor", MENSAJE_COORDINADOR_INICIO, autor=autor
                )

    def test_el_coordinador_de_otra_carrera_es_rechazado(self):
        self.rechazar(
            hace(30), "autor", MENSAJE_COORDINADOR_INICIO, autor=self.coordinador_ajeno
        )

    def test_el_coordinador_inactivo_es_rechazado(self):
        Usuario.objects.filter(pk=self.autor.pk).update(is_active=False)

        self.rechazar(hace(30), "autor", MENSAJE_COORDINADOR_INICIO)

    def test_el_coordinador_sin_carrera_es_rechazado(self):
        Usuario.objects.filter(pk=self.autor.pk).update(carrera=None)

        self.rechazar(hace(30), "autor", MENSAJE_COORDINADOR_INICIO)

    def test_un_autor_sin_guardar_es_rechazado(self):
        sin_guardar = Usuario(
            username="nuevo",
            nombre="Sin Guardar",
            email="nuevo@example.com",
            rol=Usuario.Rol.COORDINADOR,
            carrera=self.carrera,
        )

        self.rechazar(hace(30), "autor", MENSAJE_AUTOR_INICIO, autor=sin_guardar)

    def test_una_practica_sin_guardar_es_rechazada(self):
        practicas = Practica.objects.count()

        with self.assertRaises(ValidationError) as error:
            self.declarar(hace(30), practica=Practica())

        self.assertEqual(
            error.exception.message_dict, {"practica": [MENSAJE_PRACTICA_INICIO]}
        )
        self.assertEqual(Practica.objects.count(), practicas)

    def test_el_rechazo_de_autor_no_revela_el_estado_ni_la_fecha(self):
        sin_permiso = self.tutor

        with self.subTest(caso="estado fuera de en curso"):
            self.rechazar(
                hace(30),
                "autor",
                MENSAJE_COORDINADOR_INICIO,
                estado=Estado.ASIGNADA,
                autor=sin_permiso,
            )

        practica = self.en_curso()
        guardada = hace(40)
        self.guardar_fecha(guardada, practica)
        with (
            self.subTest(caso="fecha ya registrada distinta"),
            self.assertRaises(ValidationError) as error,
        ):
            self.declarar(hace(30), practica=practica, autor=sin_permiso)
        self.assertEqual(
            error.exception.message_dict, {"autor": [MENSAJE_COORDINADOR_INICIO]}
        )
        self.assertEqual(
            Practica.objects.get(pk=practica.pk).fecha_inicio_real, guardada
        )


class RegistrarInicioFechaTests(InicioFixturesMixin, TestCase):
    """La fecha es un argumento explícito ``date`` no futuro; no se infiere nada."""

    def test_rechaza_un_datetime_aunque_herede_de_date(self):
        self.rechazar(
            datetime.combine(hace(30), datetime.min.time()), "fecha", MENSAJE_FECHA_TIPO
        )

    def test_rechaza_los_valores_que_no_son_fecha(self):
        for valor in (None, "2026-04-06", 20260406, 3.5):
            with self.subTest(valor=valor):
                self.rechazar_fecha(valor, MENSAJE_FECHA_TIPO)

    def test_rechaza_una_fecha_futura(self):
        self.rechazar(hace(-1), "fecha", MENSAJE_FECHA_FUTURA)

    def test_la_fecha_local_de_hoy_es_el_limite(self):
        practica = self.en_curso()

        self.declarar(hoy(), practica=practica)

        self.assertEqual(Practica.objects.get(pk=practica.pk).fecha_inicio_real, hoy())

    def test_no_valida_ni_infiere_el_periodo(self):
        practica = self.en_curso()
        fuera_del_periodo = hace(1)
        self.assertNotEqual(fuera_del_periodo, self.periodo.fecha_inicio)
        self.assertTrue(self.periodo.fecha_fin < fuera_del_periodo)

        self.declarar(fuera_del_periodo, practica=practica)

        guardada = Practica.objects.get(pk=practica.pk)
        self.assertEqual(guardada.fecha_inicio_real, fuera_del_periodo)
        self.assertNotEqual(guardada.fecha_inicio_real, self.periodo.fecha_inicio)

    def test_la_fecha_es_un_argumento_obligatorio(self):
        practica = self.en_curso()

        with self.assertRaises(TypeError):
            self.declarar(practica=practica)

        self.afirmar_sin_escritura(Estado.EN_CURSO, practica)


class RegistrarInicioEstadoTests(InicioFixturesMixin, TestCase):
    """Solo una práctica «en curso» admite la declaración."""

    def test_solo_en_curso_admite_el_registro(self):
        for estado in (
            Estado.ASIGNADA,
            Estado.EN_REVISION_FINAL,
            Estado.CERRADA,
            Estado.SUSPENDIDA,
            Estado.CANCELADA,
        ):
            with self.subTest(estado=estado):
                mensaje = MENSAJE_ESTADO_INICIO.format(estado=estado)
                self.rechazar(hace(30), "estado", mensaje, estado=estado)


class RegistrarInicioSinReemplazoTests(InicioFixturesMixin, TestCase):
    """Una fecha ya declarada no se reemplaza; repetir el mismo valor no escribe."""

    def test_una_fecha_distinta_no_reemplaza_la_existente(self):
        practica = self.en_curso()
        guardada = hace(40)
        self.guardar_fecha(guardada, practica)

        with self.assertRaises(ValidationError) as error:
            self.declarar(hace(30), practica=practica)

        self.assertEqual(
            error.exception.message_dict, {"fecha": [MENSAJE_FECHA_YA_REGISTRADA]}
        )
        self.assertEqual(
            Practica.objects.get(pk=practica.pk).fecha_inicio_real, guardada
        )

    def test_repetir_la_misma_fecha_devuelve_sin_escribir(self):
        practica = self.en_curso()
        guardada = hace(30)
        self.guardar_fecha(guardada, practica)

        with mock.patch.object(QuerySet, "update") as update:
            resultado = self.declarar(guardada, practica=practica)

        update.assert_not_called()
        self.assertEqual(resultado.fecha_inicio_real, guardada)
        self.assertEqual(
            Practica.objects.get(pk=practica.pk).fecha_inicio_real, guardada
        )

    def test_la_repeticion_no_toca_el_estado_ni_el_historial(self):
        practica = self.en_curso()
        guardada = hace(30)
        self.guardar_fecha(guardada, practica)

        self.declarar(guardada, practica=practica)

        self.assertEqual(Practica.objects.get(pk=practica.pk).estado, Estado.EN_CURSO)
        self.assertEqual(HistorialEstado.objects.filter(practica=practica).count(), 0)


class RegistrarInicioPrimeraEscrituraTests(InicioFixturesMixin, TestCase):
    """Sin bloqueo de fila (SQLite) la actualización condicional no pisa al rival."""

    def adelantar_rival(self, practica, fecha, obsoleta):
        """Simula otra conexión ya confirmada entre nuestra lectura y la escritura.

        La transacción del servicio se reemplaza por un contexto vacío porque, con
        ella abierta, el rechazo revertiría también la escritura rival simulada:
        lo que se prueba es justamente que en SQLite no hay bloqueo que la impida
        ni transacción que la deshaga.
        """

        def leer_y_adelantar_rival(*args, **kwargs):
            Practica.objects.filter(pk=practica.pk).update(fecha_inicio_real=fecha)
            return mock.Mock(get=lambda **_: obsoleta)

        return mock.patch.object(
            Practica.objects, "select_for_update", side_effect=leer_y_adelantar_rival
        )

    @staticmethod
    def sin_transaccion():
        return mock.patch(
            "apps.practicas.services.transaction.atomic", contextlib.nullcontext
        )

    def test_una_escritura_rival_posterior_a_la_lectura_no_se_reemplaza(self):
        practica = self.en_curso()
        obsoleta = Practica.objects.get(pk=practica.pk)
        rival = hace(40)
        nuestra = hace(30)

        with (
            self.sin_transaccion(),
            self.adelantar_rival(practica, rival, obsoleta),
            self.assertRaises(ValidationError) as error,
        ):
            self.declarar(nuestra, practica=obsoleta)

        self.assertEqual(
            error.exception.message_dict, {"fecha": [MENSAJE_FECHA_YA_REGISTRADA]}
        )
        self.assertEqual(Practica.objects.get(pk=practica.pk).fecha_inicio_real, rival)

    def test_si_la_escritura_rival_coincide_no_hay_error_ni_segunda_escritura(self):
        practica = self.en_curso()
        obsoleta = Practica.objects.get(pk=practica.pk)
        nuestra = hace(30)

        with self.sin_transaccion(), self.adelantar_rival(practica, nuestra, obsoleta):
            resultado = self.declarar(nuestra, practica=obsoleta)

        self.assertEqual(resultado.fecha_inicio_real, nuestra)
        self.assertEqual(
            Practica.objects.get(pk=practica.pk).fecha_inicio_real, nuestra
        )


class RegistrarInicioConcurrenteTests(InicioFixturesMixin, TransactionTestCase):
    """Serialización real de la fila: solo PostgreSQL soporta el bloqueo."""

    def setUp(self):
        self.setUpTestData()

    @skipUnlessDBFeature("has_select_for_update")
    def test_dos_registros_simultaneos_conservan_la_primera_fecha(self):
        # El servicio exige la práctica «en curso»; la fila ya está confirmada
        # aquí (TransactionTestCase), así que ambos hilos pasan la guarda de
        # estado y compiten solo por la serialización de la fecha.
        self.en_curso()
        primera, segunda = hace(40), hace(30)
        retenida, intento, rival = threading.Event(), threading.Event(), {}

        def retener_y_registrar():
            try:
                with transaction.atomic():
                    bloqueada = Practica.objects.select_for_update().get(
                        pk=self.practica.pk
                    )
                    retenida.set()
                    intento.wait(10)
                    time.sleep(0.5)  # la otra conexión ya pidió la fila y espera
                    self.declarar(primera, practica=bloqueada)
            finally:
                connections.close_all()

        def competir():
            retenida.wait(10)
            intento.set()
            try:
                self.declarar(segunda)
            except ValidationError as error:
                rival["error"] = error.message_dict
            finally:
                connections.close_all()

        hilos = [
            threading.Thread(target=retener_y_registrar),
            threading.Thread(target=competir),
        ]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(20)
        self.assertFalse(
            any(hilo.is_alive() for hilo in hilos), "un hilo quedó bloqueado"
        )
        self.assertEqual(rival["error"]["fecha"], [MENSAJE_FECHA_YA_REGISTRADA])
        self.assertEqual(
            Practica.objects.get(pk=self.practica.pk).fecha_inicio_real, primera
        )


class TransicionesPreservadasTests(InicioFixturesMixin, TestCase):
    """El mensaje del coordinador en las transiciones existentes no cambia."""

    def test_el_rechazo_de_autor_en_las_transiciones_conserva_su_mensaje(self):
        practica = self.situar(Estado.EN_CURSO)

        with self.assertRaises(ValidationError) as error:
            cambiar_estado_practica(
                practica=practica,
                nuevo_estado=Estado.SUSPENDIDA,
                autor=self.tutor,
                motivo="Convenio vencido.",
            )

        self.assertEqual(error.exception.message_dict, {"autor": [MENSAJE_COORDINADOR]})
        self.afirmar_sin_escritura(Estado.EN_CURSO, practica)
