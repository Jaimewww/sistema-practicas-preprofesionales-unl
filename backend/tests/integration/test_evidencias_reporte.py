"""Reporte semanal con actividades y evidencias PDF versionadas (C-03, #157).

S2: el alta JSON y sus respuestas legadas no cambian; el alta ``multipart/form-data``
suma ``actividades`` y ``evidencias`` (uno o más PDF). S3: cada PDF tiene hasta
5 MB y el reenvío opcional con PDFs nuevos conserva la versión anterior y la
observación del tutor; un rechazo no deja filas ni archivos parciales. S4: la
descarga es una ruta autenticada con el alcance de filas de la práctica y
ninguna respuesta publica una URL de archivo.

Cada prueba usa su propio ``MEDIA_ROOT`` temporal (D10), así que «no quedó
ningún archivo» se comprueba contra un directorio vacío y no contra lo que dejó
otra prueba.
"""

import os
import shutil
import tempfile
from collections.abc import Callable
from datetime import date
from unittest import mock

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.actividades.models import (
    MAX_INFORME_BYTES,
    MENSAJE_ARCHIVO_PDF,
    MENSAJE_ARCHIVO_TAMANO,
    Validacion,
)
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.reportes.models import EvidenciaReporte, ReporteSemanal
from apps.reportes.serializers import MENSAJE_ACTIVIDADES, MENSAJE_SIN_EVIDENCIAS
from apps.usuarios.models import Usuario

REPORTES = "/api/v1/practicas/{}/reportes/"
DEVOLVER = "/api/v1/reportes/{}/devolver/"
REENVIAR = "/api/v1/reportes/{}/reenviar/"
OBSERVACION = "Adjunte la minuta de la reunión."
ACTIVIDADES = "Levanté requisitos con la entidad.\nPrototipé el formulario."
PDF = b"%PDF-1.4\n% evidencia de la semana\n"
NO_PDF = b"GIF89a" + b"0" * 32
CAMPOS_ALTA = {
    "id",
    "practica_id",
    "semana",
    "horas_reportadas",
    "estado",
    "requiere_revision",
    "fecha_registro",
}
CAMPOS_TARJETA = {"id", "practica_id", "semana", "horas_reportadas", "estado"}


def pdf(nombre="semana-1.pdf", contenido=PDF):
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


def pdf_de(tamano, nombre="grande.pdf"):
    """PDF con firma válida y exactamente ``tamano`` bytes."""
    return pdf(nombre, b"%PDF-" + b"0" * (tamano - 5))


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username,
        nombre=username.title(),
        email=f"{username}@example.com",
        rol=rol,
        carrera=carrera,
        password=None,
    )


class EvidenciasFixturesMixin:
    """Práctica en curso del estudiante con su tutor, otra de un par y el coordinador."""

    assertEqual: Callable[..., None]
    assertFalse: Callable[..., None]
    assertIs: Callable[..., None]
    assertTrue: Callable[..., None]
    addCleanup: Callable[..., None]

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
        cls.coordinador = crear_usuario(
            "coordinador1", Usuario.Rol.COORDINADOR, cls.carrera
        )
        cls.practica = cls.crear_practica(cls.estudiante)
        cls.ajena = cls.crear_practica(cls.par)
        for practica in (cls.practica, cls.ajena):
            AsignacionTutor.objects.create(
                practica=practica, tutor_academico=cls.tutor, desde=date(2026, 1, 1)
            )

    @classmethod
    def crear_practica(cls, estudiante):
        practica = Practica(
            estudiante=estudiante,
            carrera=cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
            estado=Practica.Estado.EN_CURSO,
        )
        practica.full_clean()
        practica.save()
        return practica

    def setUp(self):
        """``MEDIA_ROOT`` vacío por prueba; se borra al terminar (D10)."""
        media = tempfile.mkdtemp(prefix="c03-evidencias-")
        ajuste = override_settings(MEDIA_ROOT=media)
        ajuste.enable()
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        self.addCleanup(ajuste.disable)

    def cliente(self, usuario=None):
        cliente = APIClient()
        if usuario is not None:
            cliente.force_authenticate(user=usuario)
        return cliente

    def archivos_en_media(self):
        """Rutas relativas de todo archivo guardado bajo el ``MEDIA_ROOT`` temporal."""
        raiz = settings.MEDIA_ROOT
        return sorted(
            os.path.relpath(os.path.join(carpeta, nombre), raiz)
            for carpeta, _, nombres in os.walk(raiz)
            for nombre in nombres
        )

    def alta_multipart(self, datos=None, usuario=None, practica=None):
        cuerpo = {
            "semana": 1,
            "horas_reportadas": 8,
            "actividades": ACTIVIDADES,
            "evidencias": [pdf()],
        }
        cuerpo.update(datos or {})
        cuerpo = {clave: valor for clave, valor in cuerpo.items() if valor is not None}
        return self.cliente(usuario or self.estudiante).post(
            REPORTES.format((practica or self.practica).pk), cuerpo, format="multipart"
        )

    def assertRechazo400(self, respuesta, errores):
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            respuesta.json(),
            {
                "success": False,
                "message": "Datos inválidos.",
                "data": None,
                "errors": errores,
                "meta": {},
            },
        )

    def assertSinEscrituras(self):
        """Ni filas de reporte o evidencia ni archivos bajo ``MEDIA_ROOT``."""
        self.assertEqual(ReporteSemanal.objects.count(), 0)
        self.assertEqual(EvidenciaReporte.objects.count(), 0)
        self.assertEqual(self.archivos_en_media(), [])


class AltaMultipartTests(EvidenciasFixturesMixin, TestCase):
    """S2/S3: alta con actividades y PDFs; todo rechazo es atómico (D4)."""

    def test_el_alta_multipart_guarda_actividades_y_evidencias_privadas(self):
        respuesta = self.alta_multipart(
            {"evidencias": [pdf("uno.pdf"), pdf("dos.pdf", PDF + b"2")]}
        )

        self.assertEqual(respuesta.status_code, 201)
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], True)
        # La respuesta del alta es la legada: sin rutas de archivo ni campos nuevos.
        self.assertEqual(set(cuerpo["data"]), CAMPOS_ALTA)
        self.assertEqual(cuerpo["data"]["estado"], ReporteSemanal.Estado.EN_REVISION)
        reporte = ReporteSemanal.objects.get(practica=self.practica)
        self.assertEqual(reporte.actividades, ACTIVIDADES)
        evidencias = list(reporte.evidencias.order_by("pk"))
        self.assertEqual(
            [(e.version, e.nombre, e.tamano_bytes) for e in evidencias],
            [(1, "uno.pdf", len(PDF)), (1, "dos.pdf", len(PDF) + 1)],
        )
        prefijo = f"reportes_evidencias/practica-{self.practica.pk}/"
        for evidencia, contenido in zip(evidencias, (PDF, PDF + b"2"), strict=True):
            self.assertTrue(evidencia.archivo.name.startswith(prefijo))
            with evidencia.archivo.open("rb") as archivo:
                self.assertEqual(archivo.read(), contenido)
        self.assertEqual(len(self.archivos_en_media()), 2)

    def test_un_pdf_de_exactamente_5_mb_se_acepta(self):
        respuesta = self.alta_multipart({"evidencias": [pdf_de(MAX_INFORME_BYTES)]})

        self.assertEqual(respuesta.status_code, 201)
        evidencia = EvidenciaReporte.objects.get()
        self.assertEqual(evidencia.tamano_bytes, 5 * 1024 * 1024)
        self.assertEqual(len(self.archivos_en_media()), 1)

    def test_un_pdf_de_5_mb_mas_un_byte_se_rechaza_sin_escribir(self):
        respuesta = self.alta_multipart(
            {"evidencias": [pdf_de(MAX_INFORME_BYTES + 1, "pesado.pdf")]}
        )

        self.assertRechazo400(
            respuesta,
            {"evidencias": [MENSAJE_ARCHIVO_TAMANO.format(nombre="pesado.pdf")]},
        )
        self.assertSinEscrituras()

    def test_un_archivo_que_no_es_pdf_se_rechaza_por_extension_o_firma(self):
        for archivo in (
            pdf("notas.txt", PDF),  # firma válida, extensión ajena
            pdf("falso.pdf", NO_PDF),  # extensión válida, firma ajena
        ):
            with self.subTest(nombre=archivo.name):
                respuesta = self.alta_multipart({"evidencias": [archivo]})
                self.assertRechazo400(
                    respuesta,
                    {"evidencias": [MENSAJE_ARCHIVO_PDF.format(nombre=archivo.name)]},
                )
                self.assertSinEscrituras()

    def test_un_pdf_invalido_junto_a_uno_valido_no_guarda_ninguno(self):
        respuesta = self.alta_multipart(
            {"evidencias": [pdf("bueno.pdf"), pdf("falso.pdf", NO_PDF)]}
        )

        self.assertRechazo400(
            respuesta,
            {"evidencias": [MENSAJE_ARCHIVO_PDF.format(nombre="falso.pdf")]},
        )
        self.assertSinEscrituras()

    def test_sin_evidencias_el_alta_multipart_se_rechaza(self):
        respuesta = self.alta_multipart({"evidencias": None})

        self.assertRechazo400(respuesta, {"evidencias": [MENSAJE_SIN_EVIDENCIAS]})
        self.assertSinEscrituras()

    def test_sin_actividades_o_en_blanco_el_alta_multipart_se_rechaza(self):
        for actividades in (None, "", "   "):
            with self.subTest(actividades=actividades):
                respuesta = self.alta_multipart({"actividades": actividades})
                self.assertRechazo400(
                    respuesta, {"actividades": [MENSAJE_ACTIVIDADES]}
                )
                self.assertSinEscrituras()

    def test_la_semana_duplicada_multipart_es_409_sin_archivos(self):
        ReporteSemanal.objects.create(
            practica=self.practica, semana=1, horas_reportadas=8
        )

        respuesta = self.alta_multipart()

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.json()["errors"]["code"], "semana_duplicada")
        self.assertEqual(ReporteSemanal.objects.count(), 1)
        self.assertEqual(EvidenciaReporte.objects.count(), 0)
        self.assertEqual(self.archivos_en_media(), [])

    def test_un_fallo_al_guardar_el_segundo_pdf_borra_el_primero(self):
        """D4: si una escritura posterior falla, el PDF ya guardado se elimina."""
        guardar = FileSystemStorage._save
        llamadas = []

        def falla_en_el_segundo(storage, nombre, contenido):
            llamadas.append(nombre)
            if len(llamadas) == 2:
                raise OSError("disco lleno")
            return guardar(storage, nombre, contenido)

        with (
            mock.patch.object(
                FileSystemStorage,
                "_save",
                autospec=True,
                side_effect=falla_en_el_segundo,
            ),
            self.assertLogs("apps.contrato.exceptions", "ERROR"),
        ):
            respuesta = self.alta_multipart(
                {"evidencias": [pdf("uno.pdf"), pdf("dos.pdf")]}
            )

        self.assertEqual(respuesta.status_code, 500)
        self.assertEqual(respuesta.json()["errors"]["code"], "error_interno")
        self.assertEqual(len(llamadas), 2)
        self.assertSinEscrituras()

    def test_un_pdf_escrito_a_medias_se_borra(self):
        """S3: un fallo a mitad de la escritura no deja el archivo parcial."""

        def escribe_a_medias(storage, nombre, contenido):
            ruta = storage.path(nombre)
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta, "wb") as parcial:
                parcial.write(PDF[:5])
            raise OSError("disco lleno")

        with (
            mock.patch.object(
                FileSystemStorage,
                "_save",
                autospec=True,
                side_effect=escribe_a_medias,
            ),
            self.assertLogs("apps.contrato.exceptions", "ERROR"),
        ):
            respuesta = self.alta_multipart()

        self.assertEqual(respuesta.status_code, 500)
        self.assertEqual(respuesta.json()["errors"]["code"], "error_interno")
        self.assertSinEscrituras()

    def test_la_practica_no_en_curso_multipart_es_409_sin_archivos(self):
        Practica.objects.filter(pk=self.practica.pk).update(
            estado=Practica.Estado.CERRADA
        )

        respuesta = self.alta_multipart()

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.json()["errors"]["code"], "practica_no_en_curso")
        self.assertSinEscrituras()

    def test_el_alta_json_legada_no_cambia(self):
        respuesta = self.cliente(self.estudiante).post(
            REPORTES.format(self.practica.pk),
            {"semana": 1, "horas_reportadas": 8},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(set(respuesta.json()["data"]), CAMPOS_ALTA)
        reporte = ReporteSemanal.objects.get()
        self.assertEqual(reporte.actividades, "")
        self.assertEqual(EvidenciaReporte.objects.count(), 0)
        self.assertEqual(self.archivos_en_media(), [])

    def test_la_practica_ajena_responde_404_sin_escribir(self):
        respuesta = self.alta_multipart(practica=self.ajena)

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json()["errors"]["code"], "no_encontrado")
        self.assertSinEscrituras()


class ReenvioConEvidenciasTests(EvidenciasFixturesMixin, TestCase):
    """S3 (D5): reenvío opcional con PDFs nuevos; la versión anterior se conserva."""

    def reporte_devuelto(self):
        """Alta multipart (versión 1) y devolución del tutor, ambas por la API."""
        self.assertEqual(
            self.alta_multipart({"evidencias": [pdf("v1.pdf")]}).status_code, 201
        )
        reporte = ReporteSemanal.objects.get()
        respuesta = self.cliente(self.tutor).post(
            DEVOLVER.format(reporte.pk), {"observacion": OBSERVACION}, format="json"
        )
        self.assertEqual(respuesta.status_code, 200)
        return reporte

    def reenviar(self, reporte, datos=None, usuario=None, formato="multipart"):
        return self.cliente(usuario or self.estudiante).post(
            REENVIAR.format(reporte.pk), datos or {}, format=formato
        )

    def estado_guardado(self):
        """Fila del reporte, sus evidencias, sus validaciones y los archivos."""
        return (
            tuple(ReporteSemanal.objects.values_list("pk", "estado")),
            tuple(
                EvidenciaReporte.objects.order_by("pk").values_list(
                    "pk", "version", "nombre", "archivo"
                )
            ),
            tuple(
                Validacion.objects.order_by("pk").values_list(
                    "pk", "decision", "observacion", "autor_id", "fecha"
                )
            ),
            self.archivos_en_media(),
        )

    def test_el_reenvio_con_pdfs_nuevos_conserva_ambas_versiones_y_la_observacion(
        self,
    ):
        reporte = self.reporte_devuelto()
        anterior = EvidenciaReporte.objects.get()
        devolucion = Validacion.objects.get()

        respuesta = self.reenviar(
            reporte, {"evidencias": [pdf("v2.pdf", PDF + b"v2")]}
        )

        self.assertEqual(respuesta.status_code, 200)
        data = respuesta.json()["data"]
        self.assertEqual(set(data), CAMPOS_TARJETA)
        self.assertEqual(data["estado"], ReporteSemanal.Estado.EN_REVISION)
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, ReporteSemanal.Estado.EN_REVISION)
        evidencias = list(reporte.evidencias.order_by("pk"))
        self.assertEqual(
            [(e.version, e.nombre) for e in evidencias], [(1, "v1.pdf"), (2, "v2.pdf")]
        )
        self.assertEqual(
            evidencias[0].archivo.name, anterior.archivo.name
        )  # la versión 1 queda intacta
        for evidencia, contenido in zip(evidencias, (PDF, PDF + b"v2"), strict=True):
            with evidencia.archivo.open("rb") as archivo:
                self.assertEqual(archivo.read(), contenido)
        self.assertEqual(len(self.archivos_en_media()), 2)
        self.assertEqual(
            list(Validacion.objects.values_list("pk", "observacion", "fecha")),
            [(devolucion.pk, OBSERVACION, devolucion.fecha)],
        )

    def test_el_reenvio_legado_sin_cuerpo_no_cambia(self):
        reporte = self.reporte_devuelto()
        archivos = self.archivos_en_media()

        respuesta = self.reenviar(reporte, formato="json")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(set(respuesta.json()["data"]), CAMPOS_TARJETA)
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, ReporteSemanal.Estado.EN_REVISION)
        self.assertEqual(
            list(EvidenciaReporte.objects.values_list("version", flat=True)), [1]
        )
        self.assertEqual(self.archivos_en_media(), archivos)
        self.assertEqual(Validacion.objects.count(), 1)

    def test_un_pdf_invalido_en_el_reenvio_no_escribe_nada(self):
        reporte = self.reporte_devuelto()
        antes = self.estado_guardado()
        casos = (
            (
                pdf_de(MAX_INFORME_BYTES + 1, "pesado.pdf"),
                MENSAJE_ARCHIVO_TAMANO.format(nombre="pesado.pdf"),
            ),
            (pdf("falso.pdf", NO_PDF), MENSAJE_ARCHIVO_PDF.format(nombre="falso.pdf")),
        )
        for archivo, mensaje in casos:
            with self.subTest(nombre=archivo.name):
                respuesta = self.reenviar(
                    reporte, {"evidencias": [pdf("bueno.pdf"), archivo]}
                )
                self.assertRechazo400(respuesta, {"evidencias": [mensaje]})
                self.assertEqual(self.estado_guardado(), antes)

    def test_el_reenvio_multipart_sin_evidencias_se_rechaza(self):
        reporte = self.reporte_devuelto()
        antes = self.estado_guardado()

        respuesta = self.reenviar(reporte, {"actividades": "otra cosa"})

        self.assertRechazo400(respuesta, {"evidencias": [MENSAJE_SIN_EVIDENCIAS]})
        self.assertEqual(self.estado_guardado(), antes)

    def test_el_reenvio_con_pdfs_de_un_reporte_no_devuelto_es_409_sin_archivos(self):
        self.assertEqual(self.alta_multipart().status_code, 201)
        reporte = ReporteSemanal.objects.get()
        antes = self.estado_guardado()

        respuesta = self.reenviar(reporte, {"evidencias": [pdf("v2.pdf")]})

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.json()["errors"]["code"], "reporte_no_devuelto")
        self.assertEqual(self.estado_guardado(), antes)

    def test_otro_estudiante_recibe_404_sin_archivos(self):
        reporte = self.reporte_devuelto()
        antes = self.estado_guardado()

        respuesta = self.reenviar(
            reporte, {"evidencias": [pdf("v2.pdf")]}, usuario=self.par
        )

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json()["errors"]["code"], "no_encontrado")
        self.assertEqual(self.estado_guardado(), antes)

    def test_el_reenvio_con_pdfs_de_un_alta_json_guarda_la_version_2(self):
        """D1': sin evidencias la versión vigente es 1, así que la entrega nueva es 2."""
        reporte = ReporteSemanal.objects.create(
            practica=self.practica,
            semana=1,
            horas_reportadas=8,
            estado=ReporteSemanal.Estado.DEVUELTO,
        )

        respuesta = self.reenviar(reporte, {"evidencias": [pdf("v2.pdf")]})

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            list(reporte.evidencias.values_list("version", "nombre")), [(2, "v2.pdf")]
        )
        self.assertEqual(len(self.archivos_en_media()), 1)
