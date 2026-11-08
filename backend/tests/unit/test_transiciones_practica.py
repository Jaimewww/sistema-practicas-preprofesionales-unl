"""Tests del servicio interno de transiciones de ``Practica`` (T008, T017, RF-10, RF-13).

El bloqueo de filas solo se prueba en PostgreSQL; en SQLite esa prueba se omite.
"""

import threading
import time
from collections.abc import Callable
from typing import Any
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import connections, transaction
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from apps.auditoria.models import MENSAJE_MOTIVO, HistorialEstado
from apps.carreras.models import Carrera
from apps.practicas.models import Practica
from apps.practicas.services import (
    MENSAJE_AUTOR, MENSAJE_COORDINADOR, MENSAJE_ESTADO_INVALIDO, MENSAJE_MOTIVO_TEXTO,
    MENSAJE_TERMINAL, MENSAJE_TRANSICION, cambiar_estado_practica,
)
from apps.usuarios.models import Usuario
from tests.unit.test_historial_estado import HistorialEstadoFixturesMixin

Estado = Practica.Estado
ESTADOS_FINALES = (Estado.CERRADA, Estado.CANCELADA)

# Las siete aristas exactas de specs/001-seguimiento-practicas/data-model.md.
ARISTAS = [
    (Estado.ASIGNADA, Estado.EN_CURSO), (Estado.EN_CURSO, Estado.EN_REVISION_FINAL),
    (Estado.EN_REVISION_FINAL, Estado.EN_CURSO), (Estado.EN_REVISION_FINAL, Estado.CERRADA),
    (Estado.EN_CURSO, Estado.SUSPENDIDA), (Estado.SUSPENDIDA, Estado.EN_CURSO),
    (Estado.SUSPENDIDA, Estado.CANCELADA),
]
# Motivo obligatorio solo al suspender y cancelar (RF-13, spec.md Clarification);
# reanudar no lo exige.
MOTIVOS = {
    (Estado.EN_CURSO, Estado.SUSPENDIDA): "Convenio vencido.",
    (Estado.SUSPENDIDA, Estado.CANCELADA): "Abandono definitivo.",
}
# Aristas que solo produce el coordinador activo de la carrera de la práctica
# (spec.md:336, RF-13, HU-08); las demás son mecanismo interno.
ARISTAS_DE_COORDINADOR = [
    (Estado.EN_CURSO, Estado.SUSPENDIDA), (Estado.SUSPENDIDA, Estado.EN_CURSO),
    (Estado.SUSPENDIDA, Estado.CANCELADA), (Estado.EN_REVISION_FINAL, Estado.CERRADA),
]


class TransicionesFixturesMixin(HistorialEstadoFixturesMixin):
    """Reutiliza práctica, carrera y autor; las aserciones llegan del ``TestCase``."""

    assertEqual: Callable[..., None]
    assertRaises: Callable[..., Any]

    def situar(self, estado, practica=None):
        """Deja la práctica en ``estado`` sin pasar por el servicio (preparación)."""
        objetivo = practica or self.practica
        Practica.objects.filter(pk=objetivo.pk).update(estado=estado)
        objetivo.refresh_from_db()
        return objetivo

    def transitar(self, nuevo=None, motivo: Any = "", practica=None, autor=None):
        return cambiar_estado_practica(
            practica=practica or self.practica, nuevo_estado=nuevo,
            autor=autor or self.autor, motivo=motivo,
        )

    def afirmar_sin_cambios(self, estado, practica=None):
        """El rechazo no toca estado, motivos, filas ni historial."""
        objetivo = practica or self.practica
        objetivo.refresh_from_db()
        self.assertEqual(objetivo.estado, estado)
        self.assertEqual((objetivo.motivo_suspension, objetivo.motivo_cancelacion), ("", ""))
        self.assertEqual(HistorialEstado.objects.filter(practica=objetivo).count(), 0)

    def rechazar(self, nuevo, origen, mensaje, campo="estado", motivo: Any = "", practica=None):
        objetivo = self.situar(origen, practica)
        with self.assertRaises(ValidationError) as error:
            self.transitar(nuevo, motivo=motivo, practica=objetivo)
        self.assertEqual(error.exception.message_dict[campo], [mensaje])
        self.afirmar_sin_cambios(origen, objetivo)


class TransicionAristasTests(TransicionesFixturesMixin, TestCase):
    """Solo las siete aristas son legales; ``cerrada`` y ``cancelada`` son finales."""

    def test_cada_arista_cambia_el_estado_y_escribe_el_historial(self):
        for origen, destino in ARISTAS:
            with self.subTest(arista=f"{origen}->{destino}"):
                practica = self.situar(origen, self.crear_practica())
                motivo = MOTIVOS.get((origen, destino), "")
                self.transitar(destino, motivo=motivo, practica=practica)
                practica.refresh_from_db()
                registro = HistorialEstado.objects.get(practica=practica)
                self.assertEqual(practica.estado, destino)
                self.assertEqual((registro.estado_anterior, registro.estado_nuevo), (origen, destino))
                self.assertEqual(registro.autor, self.autor)
                self.assertEqual(registro.motivo, motivo)
                self.assertIsNotNone(registro.fecha)

    def test_el_recorrido_asignada_curso_revision_cerrada_escribe_tres_registros(self):
        self.transitar(Estado.EN_CURSO)
        self.transitar(Estado.EN_REVISION_FINAL)
        self.transitar(Estado.CERRADA)
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, Estado.CERRADA)
        self.assertEqual(
            list(HistorialEstado.objects.values_list("estado_anterior", "estado_nuevo")),
            [(Estado.ASIGNADA, Estado.EN_CURSO), (Estado.EN_CURSO, Estado.EN_REVISION_FINAL), (Estado.EN_REVISION_FINAL, Estado.CERRADA)],
        )

    def test_toda_otra_arista_se_rechaza_sin_efectos(self):
        for origen in Estado.values:
            for destino in Estado.values:
                if (origen, destino) in ARISTAS or origen in ESTADOS_FINALES:
                    continue
                with self.subTest(arista=f"{origen}->{destino}"):
                    self.rechazar(
                        destino, origen, MENSAJE_TRANSICION.format(origen=origen, destino=destino),
                        motivo="Motivo válido.",
                    )

    def test_cerrada_y_cancelada_rechazan_cualquier_destino(self):
        for final in ESTADOS_FINALES:
            for destino in Estado.values:
                with self.subTest(final=final, destino=destino):
                    self.rechazar(
                        destino, final, MENSAJE_TERMINAL.format(estado=final),
                        motivo="Motivo válido.",
                    )


class TransicionMotivosYRechazosTests(TransicionesFixturesMixin, TestCase):
    """Motivos obligatorios, destino malformado, autor no persistente, obsoleto y rollback."""

    def test_motivo_obligatorio_solo_al_suspender_y_cancelar(self):
        for origen, destino in MOTIVOS:
            with self.subTest(arista=f"{origen}->{destino}"):
                for vacio in ("", "   ", None):
                    self.rechazar(
                        destino, origen, MENSAJE_MOTIVO, campo="motivo", motivo=vacio,
                        practica=self.crear_practica(),
                    )
                self.rechazar(
                    destino, origen, MENSAJE_MOTIVO_TEXTO, campo="motivo",
                    motivo=["Convenio vencido."], practica=self.crear_practica(),
                )

    def test_los_motivos_de_la_practica_se_registran_y_se_conservan(self):
        self.transitar(Estado.EN_CURSO)
        self.transitar(Estado.SUSPENDIDA, motivo="Convenio vencido.")
        self.transitar(Estado.EN_CURSO)
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, Estado.EN_CURSO)
        self.assertEqual(self.practica.motivo_suspension, "Convenio vencido.")
        self.assertEqual(self.practica.motivo_cancelacion, "")
        self.transitar(Estado.SUSPENDIDA, motivo="Nuevo convenio vencido.")
        self.transitar(Estado.CANCELADA, motivo="Abandono definitivo.")
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, Estado.CANCELADA)
        self.assertEqual(self.practica.motivo_suspension, "Nuevo convenio vencido.")
        self.assertEqual(self.practica.motivo_cancelacion, "Abandono definitivo.")
        self.assertEqual(HistorialEstado.objects.count(), 5)


    def test_reanudar_sin_motivo_se_acepta_y_con_motivo_se_guarda_en_el_historial(self):
        for vacio, esperado in (("", ""), ("   ", ""), (None, ""), ("Se renovó el convenio.", "Se renovó el convenio.")):
            with self.subTest(motivo=vacio):
                practica = self.situar(Estado.SUSPENDIDA, self.crear_practica())

                reanudada = self.transitar(Estado.EN_CURSO, motivo=vacio, practica=practica)

                self.assertEqual(reanudada.estado, Estado.EN_CURSO)
                registro = HistorialEstado.objects.get(practica=practica)
                self.assertEqual(
                    (registro.estado_anterior, registro.estado_nuevo, registro.motivo),
                    (Estado.SUSPENDIDA, Estado.EN_CURSO, esperado),
                )
                self.assertEqual(reanudada.motivo_suspension, "")

    def test_destino_malformado_se_rechaza_sin_typeerror(self):
        for valor in ("archivada", ["en_curso"], {"estado": "en_curso"}, 42, None):
            with self.subTest(valor=valor):
                with self.assertRaises(ValidationError) as error:
                    self.transitar(valor)
                self.assertEqual(error.exception.message_dict["estado"], [MENSAJE_ESTADO_INVALIDO])
                self.afirmar_sin_cambios(Estado.ASIGNADA)

    def test_autor_sin_guardar_se_rechaza_sin_escribir(self):
        sin_pk = Usuario(
            username="sin-guardar", nombre="Sin Guardar", email="sin@example.com",
            rol=Usuario.Rol.COORDINADOR, carrera=self.carrera,
        )
        with self.assertRaises(ValidationError) as error:
            cambiar_estado_practica(practica=self.practica, nuevo_estado=Estado.EN_CURSO, autor=sin_pk)
        self.assertEqual(error.exception.message_dict["autor"], [MENSAJE_AUTOR])
        self.afirmar_sin_cambios(Estado.ASIGNADA)

    def test_el_estado_obsoleto_del_llamador_no_se_usa(self):
        obsoleta = Practica.objects.get(pk=self.practica.pk)
        self.transitar(Estado.EN_CURSO)
        self.assertEqual(obsoleta.estado, Estado.ASIGNADA)
        with self.assertRaises(ValidationError) as error:
            self.transitar(Estado.EN_CURSO, practica=obsoleta)
        self.assertEqual(
            error.exception.message_dict["estado"],
            [MENSAJE_TRANSICION.format(origen=Estado.EN_CURSO, destino=Estado.EN_CURSO)],
        )
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, Estado.EN_CURSO)
        self.assertEqual(HistorialEstado.objects.count(), 1)

    def test_si_falla_el_historial_no_queda_el_estado_nuevo(self):
        self.situar(Estado.EN_CURSO)
        rechazo = ValidationError("El historial rechazó la fila.")
        with mock.patch.object(HistorialEstado, "full_clean", side_effect=rechazo), \
                self.assertRaises(ValidationError):
            self.transitar(Estado.EN_REVISION_FINAL)
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, Estado.EN_CURSO)
        self.assertEqual(HistorialEstado.objects.count(), 0)


class TransicionPermisoTests(TransicionesFixturesMixin, TestCase):
    """Suspender, reanudar, cancelar y cerrar: solo el coordinador activo de la carrera.

    El rol se lee de la fila guardada y el permiso va después de la arista y antes
    del motivo; un rechazo no cambia estado, motivos ni historial.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.otra_carrera = Carrera.objects.create(codigo="ADM", nombre="Administración")
        cls.coordinador_ajeno = cls.crear_usuario(
            "coordinador2", Usuario.Rol.COORDINADOR, cls.otra_carrera
        )
        cls.coordinador_inactivo = cls.crear_usuario(
            "coordinador3", Usuario.Rol.COORDINADOR, cls.carrera, is_active=False
        )
        cls.sin_permiso = {
            "estudiante": cls.estudiante,
            "tutor académico": cls.tutor,
            "tutor de entidad": cls.crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD),
            "director": cls.crear_usuario("director1", Usuario.Rol.DIRECTOR, cls.carrera),
            "secretaría": cls.crear_usuario("secretaria1", Usuario.Rol.SECRETARIA, cls.carrera),
            "coordinador de otra carrera": cls.coordinador_ajeno,
            "coordinador inactivo": cls.coordinador_inactivo,
        }

    @staticmethod
    def crear_usuario(username, rol, carrera=None, **extra):
        return Usuario.objects.create_user(
            username=username, nombre=username.title(), email=f"{username}@example.com",
            rol=rol, carrera=carrera, password=None, **extra,
        )

    def motivo_de(self, origen, destino):
        return MOTIVOS.get((origen, destino), "")

    def test_el_coordinador_activo_de_la_carrera_recorre_las_cuatro_aristas(self):
        for origen, destino in ARISTAS_DE_COORDINADOR:
            with self.subTest(arista=f"{origen}->{destino}"):
                practica = self.situar(origen, self.crear_practica())
                self.transitar(
                    destino, motivo=self.motivo_de(origen, destino), practica=practica,
                    autor=self.autor,
                )
                practica.refresh_from_db()
                self.assertEqual(practica.estado, destino)
                self.assertEqual(HistorialEstado.objects.get(practica=practica).autor, self.autor)

    def test_los_demas_roles_no_pueden_producir_esas_aristas(self):
        for rol, autor in self.sin_permiso.items():
            for origen, destino in ARISTAS_DE_COORDINADOR:
                with self.subTest(rol=rol, arista=f"{origen}->{destino}"):
                    practica = self.situar(origen, self.crear_practica())
                    with self.assertRaises(ValidationError) as error:
                        self.transitar(
                            destino, motivo=self.motivo_de(origen, destino) or "Motivo válido.",
                            practica=practica, autor=autor,
                        )
                    self.assertEqual(error.exception.message_dict["autor"], [MENSAJE_COORDINADOR])
                    self.afirmar_sin_cambios(origen, practica)

    def test_el_rol_se_lee_de_la_fila_guardada_y_no_del_objeto_del_llamador(self):
        obsoleto = Usuario.objects.get(pk=self.autor.pk)
        Usuario.objects.filter(pk=self.autor.pk).update(rol=Usuario.Rol.ESTUDIANTE, carrera=None)
        self.assertEqual(obsoleto.rol, Usuario.Rol.COORDINADOR)
        self.situar(Estado.EN_CURSO)

        with self.assertRaises(ValidationError) as error:
            self.transitar(Estado.SUSPENDIDA, motivo="Convenio vencido.", autor=obsoleto)

        self.assertEqual(error.exception.message_dict["autor"], [MENSAJE_COORDINADOR])
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, Estado.EN_CURSO)
        self.assertEqual(HistorialEstado.objects.count(), 0)

    def test_el_staff_o_superusuario_no_evita_el_permiso(self):
        Usuario.objects.filter(pk=self.coordinador_ajeno.pk).update(is_staff=True, is_superuser=True)
        self.situar(Estado.EN_CURSO)

        with self.assertRaises(ValidationError) as error:
            self.transitar(
                Estado.SUSPENDIDA, motivo="Convenio vencido.", autor=self.coordinador_ajeno
            )

        self.assertEqual(error.exception.message_dict["autor"], [MENSAJE_COORDINADOR])

    def test_el_permiso_se_resuelve_antes_que_el_motivo(self):
        self.rechazar_como(self.tutor, Estado.SUSPENDIDA, Estado.EN_CURSO, "autor", MENSAJE_COORDINADOR)

    def test_la_arista_ilegal_y_el_estado_final_se_resuelven_antes_que_el_permiso(self):
        self.rechazar_como(
            self.estudiante, Estado.CERRADA, Estado.EN_CURSO, "estado",
            MENSAJE_TRANSICION.format(origen=Estado.EN_CURSO, destino=Estado.CERRADA),
        )
        self.rechazar_como(
            self.estudiante, Estado.EN_CURSO, Estado.CANCELADA, "estado",
            MENSAJE_TERMINAL.format(estado=Estado.CANCELADA),
        )

    def test_las_aristas_internas_no_exigen_ser_coordinador(self):
        casos = (
            (Estado.ASIGNADA, Estado.EN_CURSO, self.tutor),
            (Estado.EN_CURSO, Estado.EN_REVISION_FINAL, self.estudiante),
            (Estado.EN_REVISION_FINAL, Estado.EN_CURSO, self.tutor),
        )
        for origen, destino, autor in casos:
            with self.subTest(arista=f"{origen}->{destino}", rol=autor.rol):
                practica = self.situar(origen, self.crear_practica())
                self.transitar(destino, practica=practica, autor=autor)
                practica.refresh_from_db()
                self.assertEqual(practica.estado, destino)

    def rechazar_como(self, autor, destino, origen, campo, mensaje):
        """Rechazo con ese autor y sin motivo ni permiso válido: manda el primero que falla."""
        practica = self.situar(origen, self.crear_practica())
        with self.assertRaises(ValidationError) as error:
            self.transitar(destino, motivo="", practica=practica, autor=autor)
        self.assertEqual(error.exception.message_dict[campo], [mensaje])
        self.afirmar_sin_cambios(origen, practica)


class TransicionConcurrenteTests(TransicionesFixturesMixin, TransactionTestCase):
    """Serialización real de la fila: solo PostgreSQL soporta el bloqueo."""

    def setUp(self):
        self.setUpTestData()

    @skipUnlessDBFeature("has_select_for_update")
    def test_dos_transiciones_simultaneas_se_serializan(self):
        retenida, intento, rival = threading.Event(), threading.Event(), {}

        def retener_y_transitar():
            try:
                with transaction.atomic():
                    bloqueada = Practica.objects.select_for_update().get(pk=self.practica.pk)
                    retenida.set()
                    intento.wait(10)
                    time.sleep(0.5)  # la otra conexión ya pidió la fila y espera
                    cambiar_estado_practica(
                        practica=bloqueada, nuevo_estado=Estado.EN_CURSO, autor=self.autor
                    )
            finally:
                connections.close_all()

        def competir():
            retenida.wait(10)
            intento.set()
            inicio = time.monotonic()
            try:
                cambiar_estado_practica(
                    practica=self.practica, nuevo_estado=Estado.EN_CURSO, autor=self.autor
                )
            except ValidationError as error:
                rival["error"] = error.message_dict
            finally:
                rival["espera"] = time.monotonic() - inicio
                connections.close_all()

        hilos = [threading.Thread(target=retener_y_transitar), threading.Thread(target=competir)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(20)
        self.assertFalse(any(hilo.is_alive() for hilo in hilos), "un hilo quedó bloqueado")
        self.assertGreaterEqual(rival.get("espera", 0), 0.3)
        self.assertEqual(
            rival["error"]["estado"],
            [MENSAJE_TRANSICION.format(origen=Estado.EN_CURSO, destino=Estado.EN_CURSO)],
        )
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, Estado.EN_CURSO)
        self.assertEqual(HistorialEstado.objects.count(), 1)
