"""Invariantes de ``ConfirmacionEntidad`` e ``InformeFinal`` en la base (RF-08).

Comprueban la parte que **no** depende del servicio ni de la vista: la
``UniqueConstraint`` de la confirmación, la ``CheckConstraint`` «contenido o
archivo, exactamente uno» y la validación de PDF de ADR 0005. Se usa
``objects.create()`` justamente porque no ejecuta ``full_clean()``: así la
prueba dice si la restricción vive en el esquema y no solo en Python. Los
archivos van a un ``MEDIA_ROOT`` temporal, nunca al árbol de trabajo.
"""

import shutil
import tempfile
from collections.abc import Callable
from datetime import date
from typing import cast

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase, override_settings

from apps.actividades.models import (
    MAX_INFORME_BYTES,
    MENSAJE_ARCHIVO_PDF,
    MENSAJE_ARCHIVO_TAMANO,
    MENSAJE_INFORME_UNO,
    ConfirmacionEntidad,
    InformeFinal,
    ruta_informe_final,
    validar_archivo_informe,
)
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario

PDF = b"%PDF-1.4\n% informe final de prueba\n"


def pdf(nombre="informe.pdf", contenido=PDF):
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


class MediaTemporalMixin:
    """``MEDIA_ROOT`` efímero para las pruebas que sí guardan el archivo.

    Es un mixin, no un ``TestCase``: el ``super()`` de un ``classmethod`` en una
    clase plana no declara ``setUpClass``/``tearDownClass``, así que el ``cast``
    documenta el contrato que aporta la clase de prueba que lo mezcla.
    """

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp(prefix="rf08-modelo-")
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


class EntidadFixturesMixin:
    """Una práctica laboral con su tutor de entidad, un reporte y un informe."""

    assertEqual: Callable[..., None]
    assertTrue: Callable[..., None]
    assertIsNone: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(codigo="ING-SIS", nombre="Sistemas")
        cls.entidad = EntidadReceptora.objects.create(nombre="Junta Parroquial")
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            nombre="Estudiante",
            email="estudiante1@example.com",
            rol=Usuario.Rol.ESTUDIANTE,
            password=None,
        )
        cls.tutor = Usuario.objects.create_user(
            username="externo1",
            nombre="Externo",
            email="externo1@example.com",
            rol=Usuario.Rol.TUTOR_ENTIDAD,
            password=None,
        )
        cls.practica = Practica.objects.create(
            estudiante=cls.estudiante,
            carrera=cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
            tutor_entidad=cls.tutor,
            estado=Practica.Estado.EN_CURSO,
        )
        cls.reporte = ReporteSemanal.objects.create(
            practica=cls.practica, semana=1, horas_reportadas=8
        )

    def informe(self, **campos):
        datos = {"practica": self.practica, "tutor_entidad": self.tutor}
        datos.update(campos)
        return InformeFinal(**datos)


class ConfirmacionEntidadModeloTests(EntidadFixturesMixin, TestCase):
    """Un reporte se confirma una sola vez, y la fila no se borra por arrastre."""

    def test_el_mismo_reporte_no_se_confirma_dos_veces_en_la_base(self):
        ConfirmacionEntidad.objects.create(
            reporte=self.reporte, tutor_entidad=self.tutor
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConfirmacionEntidad.objects.create(
                reporte=self.reporte, tutor_entidad=self.tutor
            )
        self.assertEqual(ConfirmacionEntidad.objects.count(), 1)

    def test_la_fecha_la_pone_la_base_y_el_autor_es_el_tutor_guardado(self):
        confirmacion = ConfirmacionEntidad.objects.create(
            reporte=self.reporte, tutor_entidad=self.tutor
        )
        guardada = ConfirmacionEntidad.objects.get(pk=confirmacion.pk)
        self.assertEqual(guardada.tutor_entidad_id, self.tutor.pk)
        self.assertEqual(guardada.reporte_id, self.reporte.pk)
        self.assertIsNotNone(guardada.fecha)

    def test_borrar_el_reporte_confirmado_esta_protegido(self):
        ConfirmacionEntidad.objects.create(
            reporte=self.reporte, tutor_entidad=self.tutor
        )
        with self.assertRaises(ProtectedError):
            self.reporte.delete()


class InformeFinalModeloTests(MediaTemporalMixin, EntidadFixturesMixin, TestCase):
    """«Contenido o archivo»: exactamente uno, en la base y en ``full_clean()``."""

    def test_sin_contenido_ni_archivo_la_base_lo_rechaza(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InformeFinal.objects.create(
                practica=self.practica, tutor_entidad=self.tutor
            )
        self.assertEqual(InformeFinal.objects.count(), 0)

    def test_con_contenido_y_archivo_la_base_lo_rechaza(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InformeFinal.objects.create(
                practica=self.practica,
                tutor_entidad=self.tutor,
                contenido="Cierre.",
                archivo=pdf(),
            )
        self.assertEqual(InformeFinal.objects.count(), 0)

    def test_solo_contenido_y_solo_archivo_pasan_full_clean(self):
        solo_texto = self.informe(contenido="Cierre.")
        solo_texto.full_clean()

        solo_pdf = self.informe(archivo=pdf())
        solo_pdf.full_clean()

        self.assertIsNone(solo_texto.archivo.name or None)
        self.assertIsNone(solo_pdf.contenido)

    def test_full_clean_rechaza_las_dos_ausencias_y_las_dos_presencias(self):
        for campos in ({}, {"contenido": "Cierre.", "archivo": pdf()}):
            with self.subTest(campos=sorted(campos)):
                with self.assertRaises(ValidationError) as error:
                    self.informe(**campos).full_clean()
                mensajes = error.exception.message_dict
                self.assertEqual(set(mensajes), {"contenido", "archivo"})
                self.assertEqual(mensajes["contenido"], [MENSAJE_INFORME_UNO])

    def test_un_contenido_en_blanco_no_cuenta_como_contenido(self):
        with self.assertRaises(ValidationError) as error:
            self.informe(contenido="   ").full_clean()
        self.assertEqual(set(error.exception.message_dict), {"contenido", "archivo"})


class ArchivoDelInformeTests(MediaTemporalMixin, EntidadFixturesMixin, TestCase):
    """ADR 0005: PDF por extensión y firma, hasta 5 MB, y ruta única en disco."""

    def test_solo_pdf_por_extension_y_por_firma(self):
        casos = {
            "informe.docx": (b"%PDF-1.4\n", MENSAJE_ARCHIVO_PDF),
            "informe.pdf": (b"no soy un pdf", MENSAJE_ARCHIVO_PDF),
        }
        for nombre, (contenido, mensaje) in casos.items():
            with self.subTest(nombre=nombre):
                with self.assertRaises(ValidationError) as error:
                    validar_archivo_informe(pdf(nombre, contenido))
                self.assertEqual(
                    error.exception.messages, [mensaje.format(nombre=nombre)]
                )

    def test_mas_de_5_mb_se_rechaza_por_tamano(self):
        grande = pdf(contenido=b"%PDF-" + b"0" * MAX_INFORME_BYTES)
        with self.assertRaises(ValidationError) as error:
            validar_archivo_informe(grande)
        self.assertEqual(
            error.exception.messages,
            [MENSAJE_ARCHIVO_TAMANO.format(nombre="informe.pdf")],
        )

    def test_un_pdf_valido_queda_con_el_archivo_completo(self):
        """La firma se lee sin consumir el archivo: se guarda entero, no la cola."""
        informe = self.informe(archivo=pdf())
        informe.full_clean()
        informe.save()

        guardado = InformeFinal.objects.get(pk=informe.pk)
        self.assertEqual(guardado.archivo.size, len(PDF))
        self.assertTrue(guardado.archivo.name.endswith(".pdf"))

    def test_la_ruta_en_disco_es_unica_por_archivo(self):
        primera = ruta_informe_final(self.informe(), "informe.pdf")
        segunda = ruta_informe_final(self.informe(), "informe.pdf")

        self.assertNotEqual(primera, segunda)
        self.assertTrue(
            primera.startswith(f"informes_finales/practica-{self.practica.pk}/")
        )
        self.assertTrue(primera.endswith(".pdf"))

    def test_sin_archivo_la_ruta_no_se_usa(self):
        self.assertIsNone(self.informe(contenido="Cierre.").archivo.name or None)
