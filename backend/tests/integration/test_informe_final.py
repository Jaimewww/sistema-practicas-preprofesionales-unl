"""Informe final del estudiante: presentación y revisión por el tutor (RF-16).

HU-10 por HTTP. El estudiante **dueño** de una práctica «en revisión final»
presenta su informe (un PDF de hasta 5 MB) y el informe nace «en revisión»; su
tutor académico lo ve pendiente en su cola y decide reutilizando C-04: validar
deja autor y fecha en ``Validacion``, devolver exige observación. Un informe
devuelto se corrige reenviando: nace la versión siguiente y la anterior se
conserva; solo la última cuenta como «revisado» para el cierre.

Corte B (plan:103-127) fija lo que estas pruebas comprueban: presentar solo con
la práctica «en revisión final», devolver **no** cambia el estado de la práctica
(la transición a «en curso» espera a P-05) y el cierre no queda habilitado por un
informe devuelto. La práctica ajena y la inexistente responden el mismo 404, otro
tutor no decide y sin token el contrato responde 401 con el envelope universal.
Los archivos de prueba viven en un ``MEDIA_ROOT`` temporal.
"""

import shutil
import tempfile
from collections.abc import Callable
from datetime import date
from typing import cast

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient

from apps.actividades.models import (
    MAX_INFORME_BYTES,
    MENSAJE_ARCHIVO_PDF,
    MENSAJE_OBSERVACION,
    InformeEstudiante,
    Validacion,
)
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.usuarios.models import Usuario
from tests.integration.test_inicio_practica import RespuestaAPI

INFORME = "/api/v1/practicas/{}/informe-final/"
PENDIENTES = "/api/v1/pendientes/"
VALIDAR = "/api/v1/informes-estudiante/{}/validar/"
DEVOLVER = "/api/v1/informes-estudiante/{}/devolver/"
OBSERVACION = "Falta el detalle de la semana 8."
CAMPOS_INFORME = {"id", "practica_id", "version", "estado", "fecha"}
CAMPOS_PENDIENTE = {"clave", "id", "practica_id", "version", "estado"}
CAMPOS_DETALLE = {"id", "version", "estado", "fecha", "devolucion"}
PDF = b"%PDF-1.4\n% informe final del estudiante\n"
NO_PDF = b"GIF89a" + b"0" * 32


def pdf(nombre="informe-estudiante.pdf", contenido=PDF):
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username,
        nombre=username.title(),
        email=f"{username}@example.com",
        rol=rol,
        carrera=carrera,
        password=None,
    )


class MediaTemporalMixin:
    """``MEDIA_ROOT`` efímero: los PDF de prueba nunca caen en el repositorio.

    Es un mixin, no un ``TestCase``: el ``super()`` de un ``classmethod`` en una
    clase plana no declara ``setUpClass``/``tearDownClass``, así que el ``cast``
    documenta el contrato que aporta la clase de prueba que lo mezcla.
    """

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp(prefix="rf16-informe-")
        cls._nombre_override = override_settings(MEDIA_ROOT=cls._media)
        cls._nombre_override.enable()
        cast(type[TestCase], super()).setUpClass()

    @classmethod
    def tearDownClass(cls):
        try:
            cast(type[TestCase], super()).tearDownClass()
        finally:
            cls._nombre_override.disable()
            shutil.rmtree(cls._media, ignore_errors=True)


class InformeFinalFixturesMixin:
    """Una práctica en revisión final asignada al tutor, otra ajena y un par."""

    assertEqual: Callable[..., None]
    assertFalse: Callable[..., None]
    assertIn: Callable[..., None]
    assertIs: Callable[..., None]
    assertIsNone: Callable[..., None]
    assertTrue: Callable[..., None]

    practica: Practica
    ajena: Practica
    estudiante: Usuario
    par: Usuario
    tutor: Usuario
    otro_tutor: Usuario
    coordinador: Usuario

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.entidad = EntidadReceptora.objects.create(
            nombre="Junta Parroquial de San Lucas"
        )
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.par = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario(
            "academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.otro_tutor = crear_usuario(
            "academico2", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.coordinador = crear_usuario(
            "coordinador1", Usuario.Rol.COORDINADOR, cls.carrera
        )
        cls.practica = cls.crear_practica(
            cls.estudiante, Practica.Estado.EN_REVISION_FINAL
        )
        cls.ajena = cls.crear_practica(cls.par, Practica.Estado.EN_REVISION_FINAL)
        AsignacionTutor.objects.create(
            practica=cls.practica, tutor_academico=cls.tutor, desde=date(2026, 1, 1)
        )

    @classmethod
    def crear_practica(cls, estudiante, estado):
        practica = Practica(
            estudiante=estudiante,
            carrera=cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
        )
        practica.full_clean()
        practica.save()
        Practica.objects.filter(pk=practica.pk).update(estado=estado)
        practica.refresh_from_db()
        return practica

    def cliente(self, usuario=None):
        cliente = APIClient()
        if usuario is not None:
            cliente.force_authenticate(user=usuario)
        return cliente

    def presentar(
        self, usuario, practica=None, archivo=None, nombre_campo="archivo"
    ) -> RespuestaAPI:
        """``POST`` multipart del informe; sin archivo, el cuerpo va vacío."""
        objetivo = self.practica if practica is None else practica
        datos = {}
        if archivo is not None:
            datos[nombre_campo] = archivo
        return cast(
            RespuestaAPI,
            self.cliente(usuario).post(
                INFORME.format(getattr(objetivo, "pk", objetivo)),
                datos,
                format="multipart",
            ),
        )

    def detalle(self, usuario, practica=None) -> RespuestaAPI:
        objetivo = self.practica if practica is None else practica
        return cast(
            RespuestaAPI,
            self.cliente(usuario).get(
                INFORME.format(getattr(objetivo, "pk", objetivo))
            ),
        )

    def decidir(self, ruta, usuario, informe, datos=None) -> RespuestaAPI:
        return cast(
            RespuestaAPI,
            self.cliente(usuario).post(
                ruta.format(getattr(informe, "pk", informe)),
                datos or {},
                format="json",
            ),
        )

    def presentar_ok(self, usuario=None, practica=None) -> InformeEstudiante:
        respuesta = self.presentar(usuario or self.estudiante, practica, archivo=pdf())
        self.assertEqual(respuesta.status_code, 201)
        return InformeEstudiante.objects.get(pk=respuesta.json()["data"]["id"])

    def devolver_ok(self, informe) -> None:
        respuesta = self.decidir(
            DEVOLVER, self.tutor, informe, {"observacion": OBSERVACION}
        )
        self.assertEqual(respuesta.status_code, 200)

    def fotografia(self):
        return (
            InformeEstudiante.objects.count(),
            Validacion.objects.count(),
            HistorialEstado.objects.count(),
            tuple(
                InformeEstudiante.objects.order_by("pk").values_list(
                    "pk", "version", "estado"
                )
            ),
            tuple(
                Practica.objects.order_by("pk").values_list("pk", "estado")
            ),
        )

    def assertExito(self, respuesta, estado=200):
        self.assertEqual(respuesta.status_code, estado)
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], True)
        self.assertEqual(cuerpo["errors"], None)
        self.assertEqual(cuerpo["meta"], {})
        self.assertEqual(
            cuerpo["message"],
            "Recurso creado." if estado == 201 else "Operación exitosa.",
        )
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

    def assertSinEscrituras(self, antes):
        self.assertEqual(self.fotografia(), antes)


class PresentarInformeFinalTests(
    MediaTemporalMixin, InformeFinalFixturesMixin, TestCase
):
    """HU-10 caso 1: el estudiante presenta y el tutor ve el pendiente."""

    def test_el_estudiante_presenta_y_el_tutor_academico_ve_el_pendiente(self):
        data = self.assertExito(
            self.presentar(self.estudiante, archivo=pdf()), estado=201
        )

        self.assertEqual(set(data), CAMPOS_INFORME)
        self.assertEqual(data["practica_id"], self.practica.pk)
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["estado"], InformeEstudiante.Estado.EN_REVISION)
        informe = InformeEstudiante.objects.get(pk=data["id"])
        self.assertEqual(informe.estudiante_id, self.estudiante.pk)
        self.assertEqual(parse_datetime(data["fecha"]), informe.fecha)
        self.assertTrue(str(informe.archivo.name or "").endswith(".pdf"))

        pendientes = self.assertExito(self.cliente(self.tutor).get(PENDIENTES))
        self.assertEqual(len(pendientes), 1)
        pendiente = pendientes[0]
        self.assertEqual(set(pendiente), CAMPOS_PENDIENTE)
        self.assertEqual(pendiente["clave"], f"informe-{informe.pk}")
        self.assertEqual(pendiente["id"], informe.pk)
        self.assertEqual(pendiente["practica_id"], self.practica.pk)
        self.assertEqual(pendiente["version"], 1)
        self.assertEqual(pendiente["estado"], InformeEstudiante.Estado.EN_REVISION)

    def test_la_practica_en_curso_responde_409_sin_escribir(self):
        en_curso = self.crear_practica(self.estudiante, Practica.Estado.EN_CURSO)
        antes = self.fotografia()

        self.assertRechazo(
            self.presentar(self.estudiante, en_curso, archivo=pdf()),
            409,
            "Solicitud inválida.",
            {
                "detail": (
                    "Transición no permitida: la práctica está en «en_curso» y solo "
                    "se presenta el informe final con la práctica «en_revision_final»."
                ),
                "code": "practica_no_en_revision_final",
            },
        )
        self.assertSinEscrituras(antes)

    def test_un_archivo_que_no_es_pdf_se_rechaza_sin_escribir(self):
        antes = self.fotografia()

        self.assertRechazo(
            self.presentar(
                self.estudiante,
                archivo=SimpleUploadedFile(
                    "informe.pdf", NO_PDF, content_type="application/pdf"
                ),
            ),
            400,
            "Datos inválidos.",
            {
                "archivo": [
                    MENSAJE_ARCHIVO_PDF.format(nombre="informe.pdf"),
                ]
            },
        )
        self.assertSinEscrituras(antes)

    def test_un_archivo_mayor_a_cinco_mb_se_rechaza_sin_escribir(self):
        grande = pdf(
            "informe-grande.pdf",
            b"%PDF-" + b"0" * MAX_INFORME_BYTES,
        )
        antes = self.fotografia()

        respuesta = self.presentar(self.estudiante, archivo=grande)

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["message"], "Datos inválidos.")
        self.assertIn("supera el máximo de 5 MB", str(respuesta.json()["errors"]))
        self.assertSinEscrituras(antes)

    def test_sin_archivo_se_rechaza_sin_escribir(self):
        antes = self.fotografia()

        respuesta = self.presentar(self.estudiante)

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["message"], "Datos inválidos.")
        self.assertIn("archivo", respuesta.json()["errors"])
        self.assertSinEscrituras(antes)

    def test_presentar_dos_veces_responde_409_sin_escribir(self):
        informe = self.presentar_ok()
        antes = self.fotografia()

        self.assertRechazo(
            self.presentar(self.estudiante, archivo=pdf()),
            409,
            "Solicitud inválida.",
            {
                "detail": (
                    "No se puede presentar el informe final: la última versión está "
                    "«en_revision»; solo se reenvía después de una devolución."
                ),
                "code": "informe_pendiente",
            },
        )
        self.assertSinEscrituras(antes)
        self.assertEqual(InformeEstudiante.objects.get().pk, informe.pk)

    def test_otro_estudiante_y_una_practica_inexistente_responden_el_mismo_404(self):
        antes = self.fotografia()

        for objetivo in (self.ajena, 999_999):
            with self.subTest(practica=getattr(objetivo, "pk", objetivo)):
                self.assertRechazo(
                    self.presentar(self.estudiante, objetivo),
                    404,
                    "Recurso no encontrado.",
                    {"detail": "No encontrado.", "code": "no_encontrado"},
                )
        self.assertSinEscrituras(antes)

    def test_los_demas_roles_no_presentan_el_informe(self):
        antes = self.fotografia()

        for actor in (self.tutor, self.coordinador, self.otro_tutor):
            with self.subTest(actor=actor.username):
                self.assertRechazo(
                    self.presentar(actor),
                    403,
                    "Permiso denegado.",
                    {
                        "detail": (
                            "Solo el estudiante de la práctica puede presentar su "
                            "informe final."
                        ),
                        "code": "permiso_denegado",
                    },
                )
        self.assertSinEscrituras(antes)

    def test_sin_token_responde_401_con_el_envelope(self):
        antes = self.fotografia()

        for actor in (None, Usuario(username="fantasma")):
            with self.subTest(actor=getattr(actor, "username", "anonimo")):
                self.assertRechazo(
                    self.presentar(actor),
                    401,
                    "Autenticación requerida.",
                    {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
                )
                self.assertRechazo(
                    self.detalle(actor),
                    401,
                    "Autenticación requerida.",
                    {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
                )
        self.assertSinEscrituras(antes)


class ReenvioInformeFinalTests(MediaTemporalMixin, InformeFinalFixturesMixin, TestCase):
    """Corte B: un informe devuelto y reenviado deja dos versiones."""

    def test_el_reenvio_del_dueno_crea_la_version_2_en_revision(self):
        primera = self.presentar_ok()
        self.devolver_ok(primera)

        data = self.assertExito(
            self.presentar(self.estudiante, archivo=pdf()), estado=201
        )

        self.assertEqual(data["version"], 2)
        self.assertEqual(data["estado"], InformeEstudiante.Estado.EN_REVISION)
        primera.refresh_from_db()
        self.assertEqual(primera.estado, InformeEstudiante.Estado.DEVUELTO)
        self.assertEqual(InformeEstudiante.objects.count(), 2)
        self.assertEqual(
            list(
                InformeEstudiante.objects.order_by("version").values_list(
                    "version", "estado"
                )
            ),
            [(1, "devuelto"), (2, "en_revision")],
        )

    def test_solo_la_ultima_version_cuenta_como_pendiente(self):
        primera = self.presentar_ok()
        self.devolver_ok(primera)
        segunda = InformeEstudiante.objects.get(
            pk=self.assertExito(
                self.presentar(self.estudiante, archivo=pdf()), estado=201
            )["id"]
        )

        pendientes = self.assertExito(self.cliente(self.tutor).get(PENDIENTES))

        self.assertEqual(
            [fila["clave"] for fila in pendientes], [f"informe-{segunda.pk}"]
        )


class RevisionInformeFinalTests(MediaTemporalMixin, InformeFinalFixturesMixin, TestCase):
    """HU-10 caso 2 y C-04: el tutor valida o devuelve con observación."""

    def test_validar_deja_autor_y_fecha(self):
        informe = self.presentar_ok()

        data = self.assertExito(self.decidir(VALIDAR, self.tutor, informe))

        self.assertEqual(set(data), CAMPOS_PENDIENTE)
        self.assertEqual(data["clave"], f"informe-{informe.pk}")
        self.assertEqual(data["estado"], InformeEstudiante.Estado.VALIDADO)
        informe.refresh_from_db()
        self.assertEqual(informe.estado, InformeEstudiante.Estado.VALIDADO)
        validacion = Validacion.objects.get(informe_estudiante=informe)
        self.assertEqual(validacion.decision, Validacion.Decision.APROBADO)
        self.assertEqual(validacion.autor_id, self.tutor.pk)
        self.assertIsNotNone(validacion.fecha)
        self.assertEqual(validacion.observacion, "")

    def test_devolver_sin_observacion_se_rechaza_sin_escribir(self):
        informe = self.presentar_ok()
        antes = self.fotografia()

        for datos in ({}, {"observacion": ""}, {"observacion": "   "}):
            with self.subTest(datos=datos):
                self.assertRechazo(
                    self.decidir(DEVOLVER, self.tutor, informe, datos),
                    400,
                    "Datos inválidos.",
                    {"observacion": [MENSAJE_OBSERVACION]},
                )
        self.assertSinEscrituras(antes)
        informe.refresh_from_db()
        self.assertEqual(informe.estado, InformeEstudiante.Estado.EN_REVISION)

    def test_devolver_con_observacion_no_habilita_el_cierre(self):
        informe = self.presentar_ok()
        historial_antes = tuple(HistorialEstado.objects.values_list("pk", flat=True))

        data = self.assertExito(
            self.decidir(DEVOLVER, self.tutor, informe, {"observacion": OBSERVACION})
        )

        self.assertEqual(data["estado"], InformeEstudiante.Estado.DEVUELTO)
        informe.refresh_from_db()
        self.assertEqual(informe.estado, InformeEstudiante.Estado.DEVUELTO)
        validacion = Validacion.objects.get(informe_estudiante=informe)
        self.assertEqual(validacion.decision, Validacion.Decision.DEVUELTO)
        self.assertEqual(validacion.observacion, OBSERVACION)
        self.assertEqual(validacion.autor_id, self.tutor.pk)
        self.assertEqual(
            Practica.objects.get(pk=self.practica.pk).estado,
            Practica.Estado.EN_REVISION_FINAL,
        )
        self.assertEqual(
            tuple(HistorialEstado.objects.values_list("pk", flat=True)),
            historial_antes,
        )

    def test_otro_tutor_no_puede_decidir(self):
        informe = self.presentar_ok()
        antes = self.fotografia()

        self.assertRechazo(
            self.decidir(VALIDAR, self.otro_tutor, informe),
            403,
            "Permiso denegado.",
            {
                "detail": (
                    "Solo el tutor académico activo de la práctica puede validar su "
                    "informe final del estudiante."
                ),
                "code": "permiso_denegado",
            },
        )
        self.assertSinEscrituras(antes)

    def test_el_estudiante_no_decide_sobre_su_propio_informe(self):
        informe = self.presentar_ok()
        antes = self.fotografia()

        self.assertRechazo(
            self.decidir(VALIDAR, self.estudiante, informe),
            403,
            "Permiso denegado.",
            {
                "detail": (
                    "Solo el tutor académico puede revisar los informes finales de "
                    "sus practicantes."
                ),
                "code": "permiso_denegado",
            },
        )
        self.assertSinEscrituras(antes)

    def test_una_decision_sobre_un_informe_inexistente_responde_404(self):
        antes = self.fotografia()

        self.assertRechazo(
            self.decidir(VALIDAR, self.tutor, 999_999),
            404,
            "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertSinEscrituras(antes)

    def test_una_segunda_decision_responde_409_sin_escribir(self):
        informe = self.presentar_ok()
        self.assertExito(self.decidir(VALIDAR, self.tutor, informe))
        antes = self.fotografia()

        self.assertRechazo(
            self.decidir(DEVOLVER, self.tutor, informe, {"observacion": OBSERVACION}),
            409,
            "Solicitud inválida.",
            {
                "detail": (
                    "Transición no permitida: el informe está en «validado» y solo se "
                    "decide uno «en_revision»."
                ),
                "code": "informe_no_en_revision",
            },
        )
        self.assertSinEscrituras(antes)

    def test_sin_token_responde_401_con_el_envelope(self):
        informe = self.presentar_ok()
        antes = self.fotografia()

        self.assertRechazo(
            self.decidir(VALIDAR, None, informe),
            401,
            "Autenticación requerida.",
            {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
        )
        self.assertSinEscrituras(antes)


class DetalleInformeFinalTests(MediaTemporalMixin, InformeFinalFixturesMixin, TestCase):
    """El estudiante recupera la observación de la devolución con la lectura."""

    def test_el_estudiante_lee_su_informe_devuelto_con_la_observacion(self):
        informe = self.presentar_ok()
        self.devolver_ok(informe)
        validacion = Validacion.objects.get(informe_estudiante=informe)

        data = self.assertExito(self.detalle(self.estudiante))

        self.assertEqual(set(data), CAMPOS_DETALLE)
        self.assertEqual(data["id"], informe.pk)
        self.assertEqual(data["estado"], InformeEstudiante.Estado.DEVUELTO)
        self.assertEqual(parse_datetime(data["fecha"]), informe.fecha)
        self.assertEqual(set(data["devolucion"]), {"observacion", "autor_id", "fecha"})
        self.assertEqual(data["devolucion"]["observacion"], OBSERVACION)
        self.assertEqual(data["devolucion"]["autor_id"], self.tutor.pk)
        self.assertEqual(
            parse_datetime(data["devolucion"]["fecha"]), validacion.fecha
        )

    def test_el_tutor_lee_el_informe_de_su_practicante(self):
        self.presentar_ok()

        data = self.assertExito(self.detalle(self.tutor))

        self.assertEqual(data["version"], 1)

    def test_un_informe_en_revision_o_validado_no_expone_observacion(self):
        informe = self.presentar_ok()
        self.assertIsNone(self.assertExito(self.detalle(self.estudiante))["devolucion"])
        self.assertExito(self.decidir(VALIDAR, self.tutor, informe))

        self.assertIsNone(self.assertExito(self.detalle(self.estudiante))["devolucion"])

    def test_devuelto_y_reenviado_deja_de_exponer_la_observacion_anterior(self):
        primera = self.presentar_ok()
        self.devolver_ok(primera)
        self.presentar_ok()

        data = self.assertExito(self.detalle(self.estudiante))

        self.assertEqual(data["version"], 2)
        self.assertIsNone(data["devolucion"])

    def test_sin_informe_responde_el_mismo_404_que_una_practica_ajena(self):
        antes = self.fotografia()

        for objetivo in (self.practica, self.ajena, 999_999):
            with self.subTest(practica=getattr(objetivo, "pk", objetivo)):
                self.assertRechazo(
                    self.detalle(self.estudiante, objetivo),
                    404,
                    "Recurso no encontrado.",
                    {"detail": "No encontrado.", "code": "no_encontrado"},
                )
        self.assertSinEscrituras(antes)
