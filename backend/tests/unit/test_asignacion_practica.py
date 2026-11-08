"""Tests del servicio interno de asignación de ``Practica`` (T010, T018, RF-12).

La configuración se elige por carrera y modalidad con la fecha vigente al día de la
llamada. Las pruebas fijan ese día con ``mock`` en vez de depender del reloj real.
"""

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.practicas.models import AsignacionTutor, Practica
from apps.practicas.services import (
    MENSAJE_AUTOR_ASIGNACION,
    MENSAJE_CONFIGURACION,
    asignar_practica,
)
from apps.usuarios.models import Usuario
from tests.unit.test_historial_estado import HistorialEstadoFixturesMixin

HOY = date(2026, 3, 10)
Modalidad = ConfiguracionCarrera.Modalidad
Estado = Practica.Estado


class AsignacionFixturesMixin(HistorialEstadoFixturesMixin):
    """Reutiliza carrera, período, estudiante y autor; añade la configuración y el alta."""

    assertEqual: Callable[..., None]
    assertIn: Callable[..., None]
    assertRaises: Callable[..., Any]
    subTest: Callable[..., Any]

    def configurar(self, horas, vigente_desde=HOY, modalidad=Modalidad.LABORAL, carrera=None):
        return ConfiguracionCarrera.objects.create(
            carrera=carrera or self.carrera, modalidad=modalidad,
            horas_requeridas=horas, vigente_desde=vigente_desde,
        )

    def asignar_nueva(self, hoy=HOY, **overrides):
        datos = {
            "estudiante": self.estudiante, "carrera": self.carrera,
            "periodo": self.periodo, "tipo": Practica.Tipo.LABORAL,
            "entidad": self.entidad, "subtipo": Practica.Subtipo.PRACTICA,
            "autor": self.autor,
        }
        datos.update(overrides)
        with mock.patch("django.utils.timezone.localdate", return_value=hoy):
            return asignar_practica(**datos)

    def contar(self):
        return (Practica.objects.count(), HistorialEstado.objects.count())

    def rechazar(self, campo, mensaje, **overrides: Any):
        """El rechazo documentado no deja prácticas ni historial nuevos."""
        antes = self.contar()
        with self.assertRaises(ValidationError) as error:
            self.asignar_nueva(**overrides)
        self.assertEqual(error.exception.message_dict[campo], [mensaje])
        self.assertEqual(self.contar(), antes)


class AsignacionConfiguracionTests(AsignacionFixturesMixin, TestCase):
    """Solo cuenta la configuración de la misma carrera y modalidad, vigente hoy."""

    def test_usa_la_configuracion_de_la_misma_carrera_y_modalidad(self):
        otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        self.configurar(100, carrera=otra_carrera)
        self.configurar(500, modalidad=Modalidad.COMUNITARIA)
        self.configurar(240)
        laboral = self.asignar_nueva()
        self.assertEqual((laboral.carrera, laboral.tipo), (self.carrera, Practica.Tipo.LABORAL))
        self.assertEqual(laboral.horas_requeridas, 240)
        comunitaria = self.asignar_nueva(
            tipo=Practica.Tipo.COMUNITARIA, entidad=None, subtipo="",
            proyecto_vinculacion="Vinculación con la comunidad",
        )
        self.assertEqual((comunitaria.carrera, comunitaria.horas_requeridas), (self.carrera, 500))

    def test_el_dia_de_hoy_es_la_frontera_de_la_vigencia(self):
        self.configurar(260, vigente_desde=HOY)
        self.assertEqual(self.asignar_nueva().horas_requeridas, 260)
        self.rechazar(
            "carrera", MENSAJE_CONFIGURACION, hoy=HOY - timedelta(days=1),
        )

    def test_una_configuracion_solo_futura_no_sirve(self):
        self.configurar(260, vigente_desde=HOY + timedelta(days=1))
        self.rechazar("carrera", MENSAJE_CONFIGURACION)

    def test_sin_configuracion_la_asignacion_falla_cerrada(self):
        otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        self.configurar(100, carrera=otra_carrera)
        self.configurar(500, modalidad=Modalidad.COMUNITARIA)
        self.rechazar("carrera", MENSAJE_CONFIGURACION)

    def test_la_vigencia_mas_reciente_gana_y_el_pk_desempata(self):
        self.configurar(200, vigente_desde=HOY - timedelta(days=30))
        self.configurar(220, vigente_desde=HOY - timedelta(days=10))
        self.configurar(250, vigente_desde=HOY - timedelta(days=10))
        self.assertEqual(self.asignar_nueva().horas_requeridas, 250)


class AsignacionCopiaTests(AsignacionFixturesMixin, TestCase):
    """Copia las horas y crea la práctica asignada con su registro inicial."""

    def test_copia_las_horas_y_el_estado_inicial_es_asignada(self):
        self.configurar(300)
        practica = self.asignar_nueva()
        practica.refresh_from_db()
        self.assertEqual((practica.horas_requeridas, practica.estado), (300, Estado.ASIGNADA))
        self.assertEqual(
            (practica.estudiante, practica.periodo, practica.entidad, practica.subtipo),
            (self.estudiante, self.periodo, self.entidad, Practica.Subtipo.PRACTICA),
        )
        self.assertEqual(AsignacionTutor.objects.count(), 0)

    def test_el_registro_inicial_guarda_el_autor_persistente(self):
        self.configurar(300)
        practica = self.asignar_nueva()
        registro = HistorialEstado.objects.get(practica=practica)
        self.assertEqual(
            (registro.estado_anterior, registro.estado_nuevo, registro.motivo),
            (None, Estado.ASIGNADA, ""),
        )
        self.assertEqual(registro.autor, self.autor)
        self.assertIsNotNone(registro.fecha)
        self.assertEqual(HistorialEstado.objects.count(), 1)

    def test_el_llamador_no_puede_imponer_horas_ni_estado(self):
        self.configurar(300)
        antes = self.contar()
        with self.assertRaisesRegex(TypeError, "unexpected keyword argument 'horas_requeridas'"):
            self.asignar_nueva(horas_requeridas=1)
        self.assertEqual(self.contar(), antes)
        with self.assertRaisesRegex(TypeError, "unexpected keyword argument 'estado'"):
            self.asignar_nueva(estado=Estado.CERRADA)
        self.assertEqual(self.contar(), antes)

    def test_las_horas_no_cambian_al_editar_la_configuracion(self):
        configuracion = self.configurar(300)
        practica = self.asignar_nueva()
        configuracion.horas_requeridas = 120
        configuracion.save()
        practica.refresh_from_db()
        self.assertEqual(practica.horas_requeridas, 300)

    def test_una_configuracion_nueva_posterior_no_altera_la_practica_asignada(self):
        self.configurar(300)
        practica = self.asignar_nueva()
        self.configurar(400, vigente_desde=HOY + timedelta(days=1))
        practica.refresh_from_db()
        self.assertEqual(practica.horas_requeridas, 300)
        self.assertEqual(self.asignar_nueva(hoy=HOY + timedelta(days=1)).horas_requeridas, 400)


class AsignacionRechazosTests(AsignacionFixturesMixin, TestCase):
    """El modelo, el autor y el diario rechazan sin dejar filas nuevas."""

    def test_practica_invalida_se_rechaza_sin_escribir(self):
        self.configurar(300)
        antes = self.contar()
        with self.assertRaises(ValidationError) as error:
            self.asignar_nueva(subtipo="")
        self.assertIn("subtipo", error.exception.message_dict)
        self.assertEqual(self.contar(), antes)

    def test_autor_sin_guardar_se_rechaza_sin_escribir(self):
        sin_pk = Usuario(
            username="sin-guardar", nombre="Sin Guardar", email="sin@example.com",
            rol=Usuario.Rol.COORDINADOR, carrera=self.carrera,
        )
        self.rechazar("autor", MENSAJE_AUTOR_ASIGNACION, autor=sin_pk)

    def test_si_falla_el_historial_no_queda_la_practica(self):
        self.configurar(300)
        antes = self.contar()
        rechazo = ValidationError("El diario rechazó la fila.")
        with mock.patch.object(HistorialEstado, "full_clean", side_effect=rechazo), \
                self.assertRaises(ValidationError):
            self.asignar_nueva()
        self.assertEqual(self.contar(), antes)
