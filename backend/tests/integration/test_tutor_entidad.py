"""Confirmación de entidad e informe final externo (RF-08, HU-07, S3-S7).

``POST /api/v1/reportes/{id}/confirmacion/`` registra **quién** confirmó el
reporte semanal de su practicante y **cuándo** (HU-07 caso 2), y ``POST
/api/v1/practicas/{id}/informe-externo/`` registra el informe final del tutor de
la entidad con su autor y su fecha (HU-07 caso 1). El alcance es el de la fila
guardada: solo el ``tutor_entidad`` **persistido** de esa práctica laboral
confirma y registra; cualquier otro tutor de entidad, un rol ajeno, un
estudiante o una práctica comunitaria —que no tiene tutor de entidad— se
rechazan (HU-07 caso 3), y un reporte o una práctica inexistente responde 404.

Ninguna de las dos acciones cambia el estado del reporte, el de la práctica ni
el historial (S9): el cierre es de otra unidad y aquí solo se escribe la fila de
la confirmación o del informe. Un rechazo no escribe nada y los ``archivo`` de
prueba viven en un ``MEDIA_ROOT`` temporal, no en el árbol de trabajo.
"""

import shutil
import tempfile
from collections.abc import Callable
from typing import cast

import yaml
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils.dateparse import parse_datetime

from apps.actividades.models import (
    MAX_INFORME_BYTES,
    MENSAJE_ARCHIVO_PDF,
    MENSAJE_ARCHIVO_TAMANO,
    MENSAJE_INFORME_UNO,
    ConfirmacionEntidad,
    InformeFinal,
)
from apps.actividades.services import (
    MENSAJE_CONFIRMACION_DUPLICADA,
    MENSAJE_INFORME_DUPLICADO,
    MENSAJE_TUTOR_ENTIDAD_CONFIRMACION,
    MENSAJE_TUTOR_ENTIDAD_INFORME,
)
from apps.auditoria.models import HistorialEstado
from apps.practicas.models import Practica
from apps.practicas.services import asignar_practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario
from tests.integration.test_inicio_practica import RespuestaAPI
from tests.integration.test_reportes_flujo import FlujoFixturesMixin, crear_usuario

CONFIRMACION = "/api/v1/reportes/{}/confirmacion/"
INFORME = "/api/v1/practicas/{}/informe-externo/"
RUTA_SCHEMA_CONFIRMACION = "/api/v1/reportes/{reporte_id}/confirmacion/"
RUTA_SCHEMA_INFORME = "/api/v1/practicas/{practica_id}/informe-externo/"

CAMPOS_CONFIRMACION = {"id", "reporte_id", "tutor_entidad_id", "fecha"}
CAMPOS_INFORME = {
    "id",
    "practica_id",
    "tutor_entidad_id",
    "contenido",
    "archivo",
    "fecha",
}

PDF = b"%PDF-1.4\n% informe final de prueba\n"
PDF_GRANDE = b"%PDF-" + b"0" * MAX_INFORME_BYTES


def pdf(nombre="informe.pdf", contenido=PDF):
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


class MediaTemporalMixin:
    """``MEDIA_ROOT`` efímero: los archivos de prueba nunca caen en el repo.

    Es un mixin, no un ``TestCase``: el ``super()`` de un ``classmethod`` en una
    clase plana no declara ``setUpClass``/``tearDownClass``, así que el ``cast``
    documenta el contrato que aporta la clase de prueba que lo mezcla.
    """

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp(prefix="rf08-informes-")
        cls._override_media = override_settings(MEDIA_ROOT=cls._media)
        cls._override_media.enable()
        cast(type[TestCase], super()).setUpClass()

    @classmethod
    def tearDownClass(cls):
        try:
            cast(type[TestCase], super()).tearDownClass()
        finally:
            cls._override_media.disable()
            shutil.rmtree(cls._media, ignore_errors=True)


class TutorEntidadFixturesMixin(FlujoFixturesMixin):
    """El flujo de reportes, más un segundo tutor de entidad y una comunitaria."""

    practica: Practica
    cerrada: Practica
    comunitaria: Practica
    reporte: ReporteSemanal
    externo: Usuario
    otro_externo: Usuario
    estudiante: Usuario
    tutor: Usuario

    assertEqual: Callable[..., None]
    assertTrue: Callable[..., None]
    assertIsNone: Callable[..., None]
    assertIn: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.otro_externo = crear_usuario("externo2", Usuario.Rol.TUTOR_ENTIDAD)
        cls.comunitaria = asignar_practica(
            estudiante=cls.estudiante,
            carrera=cls.carrera,
            periodo=cls.periodo,
            tipo=Practica.Tipo.COMUNITARIA,
            autor=cls.coordinador,
            proyecto_vinculacion="Vinculación con la comunidad",
        )
        Practica.objects.filter(pk=cls.comunitaria.pk).update(
            estado=Practica.Estado.EN_CURSO
        )
        cls.comunitaria.refresh_from_db()
        cls.reporte = ReporteSemanal.objects.create(
            practica=cls.practica, semana=1, horas_reportadas=8
        )

    def confirmar(self, actor, reporte=None) -> RespuestaAPI:
        objetivo = self.reporte if reporte is None else reporte
        return cast(
            RespuestaAPI,
            self.cliente(actor).post(
                CONFIRMACION.format(getattr(objetivo, "pk", objetivo))
            ),
        )

    def registrar_informe(self, actor, practica=None, datos=None) -> RespuestaAPI:
        objetivo = self.practica if practica is None else practica
        return cast(
            RespuestaAPI,
            self.cliente(actor).post(
                INFORME.format(getattr(objetivo, "pk", objetivo)),
                datos or {},
                format="multipart",
            ),
        )

    def fotografia_completa(self):
        """Conteos, reportes, prácticas e historial: un rechazo no cambia nada."""
        return (
            super().fotografia(),
            ConfirmacionEntidad.objects.count(),
            InformeFinal.objects.count(),
            tuple(
                ReporteSemanal.objects.order_by("pk").values_list(
                    "pk", "practica_id", "semana", "estado"
                )
            ),
            tuple(
                Practica.objects.order_by("pk").values_list(
                    "pk", "estado", "motivo_suspension", "motivo_cancelacion"
                )
            ),
            tuple(
                HistorialEstado.objects.order_by("pk").values_list(
                    "pk", "practica_id", "estado_anterior", "estado_nuevo", "motivo"
                )
            ),
        )

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

    def assertSinEscrituras(self, antes):
        self.assertEqual(self.fotografia_completa(), antes)


class ConfirmacionEntidadTests(TutorEntidadFixturesMixin, TestCase):
    """HU-07 caso 2: queda registrado quién confirmó el reporte y cuándo."""

    def test_el_tutor_de_entidad_confirma_el_reporte_de_su_practicante(self):
        data = self.assertExito(self.confirmar(self.externo))

        self.assertEqual(set(data), CAMPOS_CONFIRMACION)
        self.assertEqual(data["reporte_id"], self.reporte.pk)
        self.assertEqual(data["tutor_entidad_id"], self.externo.pk)
        guardada = ConfirmacionEntidad.objects.get(reporte_id=self.reporte.pk)
        self.assertEqual(guardada.pk, data["id"])
        self.assertEqual(guardada.tutor_entidad_id, self.externo.pk)
        self.assertEqual(parse_datetime(data["fecha"]), guardada.fecha)

    def test_la_confirmacion_no_cambia_el_estado_ni_escribe_historial(self):
        antes = self.reporte.estado
        historial_antes = tuple(HistorialEstado.objects.values_list("pk", flat=True))

        self.assertExito(self.confirmar(self.externo))

        self.assertEqual(ReporteSemanal.objects.get(pk=self.reporte.pk).estado, antes)
        self.assertEqual(
            tuple(HistorialEstado.objects.values_list("pk", flat=True)),
            historial_antes,
        )
        self.assertEqual(
            Practica.objects.get(pk=self.practica.pk).estado,
            Practica.Estado.EN_CURSO,
        )

    def test_confirmar_dos_veces_responde_409_sin_escribir(self):
        self.assertExito(self.confirmar(self.externo))
        antes = self.fotografia_completa()

        self.assertRechazo(
            self.confirmar(self.externo),
            409,
            "Solicitud inválida.",
            {
                "detail": MENSAJE_CONFIRMACION_DUPLICADA,
                "code": "confirmacion_duplicada",
            },
        )
        self.assertSinEscrituras(antes)
        self.assertEqual(ConfirmacionEntidad.objects.count(), 1)


class ConfirmacionEntidadAlcanceTests(TutorEntidadFixturesMixin, TestCase):
    """HU-07 caso 3: un tutor de entidad ajeno no alcanza la práctica (403)."""

    def test_otro_tutor_de_entidad_recibe_403_sin_escribir(self):
        antes = self.fotografia_completa()
        self.assertRechazo(
            self.confirmar(self.otro_externo),
            403,
            "Permiso denegado.",
            {"detail": MENSAJE_TUTOR_ENTIDAD_CONFIRMACION, "code": "permiso_denegado"},
        )
        self.assertSinEscrituras(antes)

    def test_una_practica_sin_tutor_de_entidad_no_la_confirma_nadie(self):
        """El ``tutor_entidad`` de la práctica es la única fuente del permiso."""
        reporte = self.crear_reporte(self.cerrada, semana=2)
        antes = self.fotografia_completa()
        for actor in (self.externo, self.otro_externo):
            with self.subTest(actor=actor.username):
                self.assertRechazo(
                    self.confirmar(actor, reporte),
                    403,
                    "Permiso denegado.",
                    {
                        "detail": MENSAJE_TUTOR_ENTIDAD_CONFIRMACION,
                        "code": "permiso_denegado",
                    },
                )
        self.assertSinEscrituras(antes)

    def test_la_practica_comunitaria_se_rechaza_sin_escribir(self):
        """P-01 sigue abierta: la comunitaria no tiene tutor de entidad."""
        reporte = self.crear_reporte(self.comunitaria, semana=3)
        antes = self.fotografia_completa()
        self.assertRechazo(
            self.confirmar(self.externo, reporte),
            403,
            "Permiso denegado.",
            {"detail": MENSAJE_TUTOR_ENTIDAD_CONFIRMACION, "code": "permiso_denegado"},
        )
        self.assertSinEscrituras(antes)

    def test_un_reporte_inexistente_responde_404_sin_escribir(self):
        antes = self.fotografia_completa()
        self.assertRechazo(
            self.confirmar(self.externo, 999_999),
            404,
            "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertSinEscrituras(antes)

    def test_los_demas_roles_reciben_403_antes_que_la_existencia(self):
        antes = self.fotografia_completa()
        actores = {
            "estudiante": self.estudiante,
            "tutor_academico": self.tutor,
            "coordinador": self.coordinador,
        }
        for rol, actor in actores.items():
            with self.subTest(rol=rol):
                self.assertRechazo(
                    self.confirmar(actor),
                    403,
                    "Permiso denegado.",
                    {
                        "detail": MENSAJE_TUTOR_ENTIDAD_CONFIRMACION,
                        "code": "permiso_denegado",
                    },
                )
        # El rol se resuelve antes que la fila: el 403 no depende del reporte.
        self.assertEqual(self.confirmar(self.estudiante, 999_999).status_code, 403)
        self.assertSinEscrituras(antes)

    def test_sin_token_o_con_cuenta_inactiva_recibe_401_sin_escribir(self):
        inactivo = crear_usuario("inactivo1", Usuario.Rol.TUTOR_ENTIDAD)
        Usuario.objects.filter(pk=inactivo.pk).update(is_active=False)
        antes = self.fotografia_completa()

        for actor in (None, inactivo, Usuario(username="fantasma")):
            with self.subTest(actor=getattr(actor, "username", "anonimo")):
                self.assertRechazo(
                    self.confirmar(actor),
                    401,
                    "Autenticación requerida.",
                    {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
                )
        self.assertSinEscrituras(antes)

    def test_un_token_jwt_real_sin_credenciales_recibe_401(self):
        """Sin token, el contrato responde 401 con el envelope universal."""
        respuesta = self.client.post(CONFIRMACION.format(self.reporte.pk))
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json()["errors"]["code"], "no_autenticado")
        self.assertFalse(respuesta.json()["success"])


class InformeFinalExternoTests(MediaTemporalMixin, TutorEntidadFixturesMixin, TestCase):
    """HU-07 caso 1: el informe queda asociado a la práctica con autor y fecha."""

    def test_el_informe_con_contenido_queda_con_autor_y_fecha(self):
        data = self.assertExito(
            self.registrar_informe(
                self.externo, datos={"contenido": "Cumplió el plan satisfactoriamente."}
            )
        )

        self.assertEqual(set(data), CAMPOS_INFORME)
        self.assertEqual(data["practica_id"], self.practica.pk)
        self.assertEqual(data["tutor_entidad_id"], self.externo.pk)
        self.assertEqual(data["contenido"], "Cumplió el plan satisfactoriamente.")
        self.assertIsNone(data["archivo"])
        informe = InformeFinal.objects.get(practica_id=self.practica.pk)
        self.assertEqual(informe.pk, data["id"])
        self.assertEqual(informe.tutor_entidad_id, self.externo.pk)
        self.assertEqual(parse_datetime(data["fecha"]), informe.fecha)
        self.assertIsNone(informe.archivo.name or None)

    def test_el_informe_con_archivo_pdf_guarda_el_archivo(self):
        data = self.assertExito(
            self.registrar_informe(self.externo, datos={"archivo": pdf()})
        )

        self.assertIsNone(data["contenido"])
        self.assertTrue(data["archivo"].endswith(".pdf"))
        informe = InformeFinal.objects.get(practica_id=self.practica.pk)
        self.assertIsNone(informe.contenido)
        # ``FileField.name`` es ``str | None``: con el archivo guardado siempre es ruta.
        self.assertTrue(cast(str, informe.archivo.name).endswith(".pdf"))
        self.assertEqual(informe.archivo.size, len(PDF))

    def test_el_informe_no_cambia_el_estado_de_la_practica_ni_el_historial(self):
        historial_antes = tuple(
            HistorialEstado.objects.order_by("pk").values_list("pk", flat=True)
        )

        self.assertExito(
            self.registrar_informe(self.externo, datos={"contenido": "Cierre."})
        )

        self.assertEqual(
            Practica.objects.get(pk=self.practica.pk).estado,
            Practica.Estado.EN_CURSO,
        )
        self.assertEqual(
            tuple(HistorialEstado.objects.order_by("pk").values_list("pk", flat=True)),
            historial_antes,
        )

    def test_registrar_dos_informes_responde_409_sin_escribir(self):
        self.assertExito(
            self.registrar_informe(self.externo, datos={"contenido": "Cierre."})
        )
        antes = self.fotografia_completa()

        self.assertRechazo(
            self.registrar_informe(self.externo, datos={"contenido": "Otra vez."}),
            409,
            "Solicitud inválida.",
            {"detail": MENSAJE_INFORME_DUPLICADO, "code": "informe_duplicado"},
        )
        self.assertSinEscrituras(antes)
        self.assertEqual(InformeFinal.objects.count(), 1)


class InformeFinalValidacionTests(
    MediaTemporalMixin, TutorEntidadFixturesMixin, TestCase
):
    """S8/ADR 0005: PDF de hasta 5 MB, y «contenido o archivo», nunca los dos."""

    def test_ni_contenido_ni_archivo_responde_400_sin_escribir(self):
        antes = self.fotografia_completa()
        respuesta = self.registrar_informe(self.externo)
        self.assertEqual(respuesta.status_code, 400)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["message"], "Datos inválidos.")
        self.assertEqual(set(cuerpo["errors"]), {"contenido", "archivo"})
        self.assertEqual(cuerpo["errors"]["contenido"], [MENSAJE_INFORME_UNO])
        self.assertIsNone(cuerpo["data"])
        self.assertSinEscrituras(antes)

    def test_contenido_y_archivo_juntos_responde_400_sin_escribir(self):
        antes = self.fotografia_completa()
        respuesta = self.registrar_informe(
            self.externo, datos={"contenido": "Cierre.", "archivo": pdf()}
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(set(respuesta.json()["errors"]), {"contenido", "archivo"})
        self.assertSinEscrituras(antes)

    def test_un_archivo_que_no_es_pdf_responde_400_en_su_campo(self):
        antes = self.fotografia_completa()
        casos = {
            "informe.docx": pdf("informe.docx"),
            "informe.pdf": pdf(contenido=b"no soy un pdf"),
        }
        for nombre, archivo in casos.items():
            with self.subTest(nombre=nombre):
                respuesta = self.registrar_informe(
                    self.externo, datos={"archivo": archivo}
                )
                self.assertRechazo(
                    respuesta,
                    400,
                    "Datos inválidos.",
                    {"archivo": [MENSAJE_ARCHIVO_PDF.format(nombre=nombre)]},
                )
        self.assertSinEscrituras(antes)

    def test_un_archivo_mayor_a_5_mb_responde_400_en_su_campo(self):
        antes = self.fotografia_completa()
        self.assertRechazo(
            self.registrar_informe(
                self.externo, datos={"archivo": pdf(contenido=PDF_GRANDE)}
            ),
            400,
            "Datos inválidos.",
            {"archivo": [MENSAJE_ARCHIVO_TAMANO.format(nombre="informe.pdf")]},
        )
        self.assertSinEscrituras(antes)


class InformeFinalAlcanceTests(MediaTemporalMixin, TutorEntidadFixturesMixin, TestCase):
    """HU-07 caso 3 sobre la práctica: solo el tutor de entidad persistido."""

    def test_otro_tutor_de_entidad_recibe_403_sin_escribir(self):
        antes = self.fotografia_completa()
        self.assertRechazo(
            self.registrar_informe(
                self.otro_externo, datos={"contenido": "Informe ajeno."}
            ),
            403,
            "Permiso denegado.",
            {"detail": MENSAJE_TUTOR_ENTIDAD_INFORME, "code": "permiso_denegado"},
        )
        self.assertSinEscrituras(antes)

    def test_la_practica_comunitaria_se_rechaza_sin_escribir(self):
        antes = self.fotografia_completa()
        self.assertRechazo(
            self.registrar_informe(
                self.externo, self.comunitaria, datos={"contenido": "Cierre."}
            ),
            403,
            "Permiso denegado.",
            {"detail": MENSAJE_TUTOR_ENTIDAD_INFORME, "code": "permiso_denegado"},
        )
        self.assertSinEscrituras(antes)

    def test_una_practica_inexistente_responde_404_sin_escribir(self):
        antes = self.fotografia_completa()
        self.assertRechazo(
            self.registrar_informe(self.externo, 999_999, datos={"contenido": "X."}),
            404,
            "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertSinEscrituras(antes)

    def test_los_demas_roles_reciben_403_antes_que_la_existencia(self):
        antes = self.fotografia_completa()
        for rol, actor in (
            ("estudiante", self.estudiante),
            ("tutor_academico", self.tutor),
            ("coordinador", self.coordinador),
        ):
            with self.subTest(rol=rol):
                self.assertRechazo(
                    self.registrar_informe(actor, datos={"contenido": "X."}),
                    403,
                    "Permiso denegado.",
                    {
                        "detail": MENSAJE_TUTOR_ENTIDAD_INFORME,
                        "code": "permiso_denegado",
                    },
                )
        self.assertEqual(
            self.registrar_informe(
                self.estudiante, 999_999, datos={"contenido": "X."}
            ).status_code,
            403,
        )
        self.assertSinEscrituras(antes)

    def test_sin_token_recibe_401_sin_escribir(self):
        antes = self.fotografia_completa()
        respuesta = self.client.post(INFORME.format(self.practica.pk), {})
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json()["errors"]["code"], "no_autenticado")
        self.assertSinEscrituras(antes)


class TutorEntidadSchemaTests(TutorEntidadFixturesMixin, TestCase):
    """El contrato OpenAPI publica las dos rutas con sus respuestas y el JWT."""

    @override_settings(DEBUG=True)
    def test_las_dos_rutas_aparecen_con_sus_respuestas_y_security(self):
        documento = yaml.safe_load(self.client.get("/api/v1/schema/").content)
        esperadas = {
            RUTA_SCHEMA_CONFIRMACION: {"200", "401", "403", "404", "409"},
            RUTA_SCHEMA_INFORME: {"200", "400", "401", "403", "404", "409"},
        }
        for ruta, estados in esperadas.items():
            with self.subTest(ruta=ruta):
                operacion = documento["paths"][ruta]["post"]
                self.assertLessEqual(estados, set(operacion["responses"]))
                self.assertEqual(operacion["security"], [{"jwtAuth": []}])

    @override_settings(DEBUG=True)
    def test_el_informe_declara_cuerpo_multipart_y_su_respuesta(self):
        documento = yaml.safe_load(self.client.get("/api/v1/schema/").content)
        operacion = documento["paths"][RUTA_SCHEMA_INFORME]["post"]

        self.assertIn("multipart/form-data", operacion["requestBody"]["content"])
        componentes = documento["components"]["schemas"]
        self.assertEqual(set(componentes["InformeFinal"]["properties"]), CAMPOS_INFORME)
        self.assertEqual(
            set(componentes["ConfirmacionEntidad"]["properties"]),
            CAMPOS_CONFIRMACION,
        )
        self.assertIn(
            "reportes", documento["paths"][RUTA_SCHEMA_CONFIRMACION]["post"]["tags"]
        )
