"""Tests del modelo Alerta (T042, HU-06, CU-03).

Cubren el contrato de datos: práctica obligatoria, exactamente los tres tipos
declarados, fecha automática, ``atendida`` falsa por defecto, destinatarios
derivados del tipo según HU-06 y unicidad condicional de la causa activa en la
base.
"""

from datetime import date
from typing import cast

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.alertas.models import DESTINATARIOS_POR_TIPO, Alerta
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.usuarios.models import Usuario

MENSAJE_ACTIVA_DUPLICADA = (
    "Ya existe una alerta activa de este tipo para la práctica; "
    "no se genera otra hasta que la vigente se marque como atendida."
)
TIPOS_DEL_CONTRATO = {"reporte_no_enviado", "revision_pendiente", "rezago"}
ROLES_ESTUDIANTE_TUTOR_COORDINADOR = (
    Usuario.Rol.ESTUDIANTE,
    Usuario.Rol.TUTOR_ACADEMICO,
    Usuario.Rol.COORDINADOR,
)


class AlertaFixturesMixin:
    """Dos prácticas válidas de la misma carrera, compartidas por las pruebas."""

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
        cls.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            nombre="Ana Torres",
            email="ana@example.com",
            rol=Usuario.Rol.ESTUDIANTE,
            password=None,
        )
        cls.practica = cls.crear_practica()
        cls.otra_practica = cls.crear_practica()

    @classmethod
    def crear_practica(cls):
        practica = Practica(
            estudiante=cls.estudiante,
            carrera=cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
        )
        practica.full_clean()
        practica.save()
        return practica

    def crear(self, practica=None, tipo=Alerta.Tipo.REZAGO, **extra):
        alerta = Alerta(practica=practica or self.practica, tipo=tipo, **extra)
        alerta.full_clean()
        alerta.save()
        return alerta

    def crear_cruda(self, practica=None, tipo=Alerta.Tipo.REZAGO, **extra):
        """Inserta sin full_clean: la regla de la base tiene que bastar."""
        return Alerta.objects.create(
            practica=practica or self.practica, tipo=tipo, **extra
        )


class AlertaCamposTests(AlertaFixturesMixin, TestCase):
    """Práctica obligatoria, tres tipos exactos, fecha automática y no atendida."""

    def test_declara_exactamente_los_tres_tipos_del_contrato(self):
        self.assertEqual(set(Alerta.Tipo.values), TIPOS_DEL_CONTRATO)
        self.assertEqual(len(Alerta.Tipo.choices), 3)

    def test_practica_y_tipo_son_obligatorios_y_no_guardan_nada(self):
        for campo in ("practica", "tipo"):
            with self.subTest(campo=campo):
                incompleta = Alerta(practica=self.practica, tipo=Alerta.Tipo.REZAGO)
                setattr(incompleta, campo, None)
                with self.assertRaises(ValidationError) as error:
                    incompleta.full_clean()
                self.assertIn(campo, error.exception.message_dict)
                self.assertEqual(Alerta.objects.count(), 0)

    def test_la_base_rechaza_una_alerta_sin_practica(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Alerta(practica_id=None, tipo=Alerta.Tipo.REZAGO).save()

        self.assertEqual(Alerta.objects.count(), 0)

    def test_tipo_fuera_del_contrato_se_rechaza(self):
        for tipo in ("incumplimiento", "", "reporte_enviado"):
            with self.subTest(tipo=tipo):
                invalida = Alerta(practica=self.practica, tipo=tipo)
                with self.assertRaises(ValidationError) as error:
                    invalida.full_clean()
                self.assertIn("tipo", error.exception.message_dict)
                self.assertEqual(Alerta.objects.count(), 0)

    def test_fecha_se_asigna_automaticamente_e_ignora_la_manual(self):
        alerta = self.crear(fecha=date(2000, 1, 1))
        alerta.refresh_from_db()

        self.assertEqual(alerta.fecha, date.today())

    def test_atendida_es_falsa_por_defecto(self):
        alerta = self.crear()
        alerta.refresh_from_db()

        self.assertFalse(alerta.atendida)
        self.assertEqual(Alerta.objects.filter(atendida=False).count(), 1)


class AlertaDestinatariosTests(AlertaFixturesMixin, TestCase):
    """Los destinatarios son roles derivados del tipo, no identidades guardadas."""

    def test_mapeo_exacto_de_roles_por_tipo_segun_hu06(self):
        self.assertEqual(
            DESTINATARIOS_POR_TIPO,
            {
                Alerta.Tipo.REPORTE_NO_ENVIADO: ROLES_ESTUDIANTE_TUTOR_COORDINADOR,
                Alerta.Tipo.REVISION_PENDIENTE: (Usuario.Rol.TUTOR_ACADEMICO,),
                Alerta.Tipo.REZAGO: ROLES_ESTUDIANTE_TUTOR_COORDINADOR,
            },
        )

    def test_cada_alerta_expone_los_roles_de_su_tipo(self):
        casos = {
            Alerta.Tipo.REPORTE_NO_ENVIADO: ROLES_ESTUDIANTE_TUTOR_COORDINADOR,
            Alerta.Tipo.REVISION_PENDIENTE: (Usuario.Rol.TUTOR_ACADEMICO,),
            Alerta.Tipo.REZAGO: ROLES_ESTUDIANTE_TUTOR_COORDINADOR,
        }
        for tipo, esperados in casos.items():
            with self.subTest(tipo=tipo):
                alerta = self.crear(tipo=tipo)
                alerta.refresh_from_db()
                self.assertEqual(alerta.destinatarios, esperados)

    def test_no_hay_columna_de_destinatarios_ni_de_usuarios(self):
        campos = {campo.name for campo in Alerta._meta.concrete_fields}

        self.assertNotIn("destinatarios", campos)
        self.assertNotIn("usuario", campos)
        self.assertEqual(campos, {"id", "practica", "tipo", "fecha", "atendida"})


class AlertaCausaActivaUnicaTests(AlertaFixturesMixin, TestCase):
    """Una sola causa activa por práctica y tipo; el historial se conserva."""

    def test_duplicado_activo_lo_rechaza_la_base_y_conserva_el_original(self):
        original = self.crear_cruda()
        pk_original = original.pk
        casos = {
            "objects.create": lambda: self.crear_cruda(),
            "save": lambda: Alerta(
                practica=self.practica, tipo=Alerta.Tipo.REZAGO
            ).save(),
        }

        for nombre, escritura in casos.items():
            with self.subTest(escritura=nombre):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    escritura()
                filas = list(Alerta.objects.order_by("pk"))
                self.assertEqual(len(filas), 1)
                self.assertEqual(filas[0].pk, pk_original)
                self.assertEqual(filas[0].tipo, Alerta.Tipo.REZAGO)
                self.assertFalse(filas[0].atendida)

    def test_causas_distintas_conviven_activas_en_la_misma_practica(self):
        # ``Tipo.values`` son los valores crudos; el campo guarda el ``str``.
        for tipo in Alerta.Tipo.values:
            self.crear_cruda(tipo=cast(Alerta.Tipo, tipo))

        self.assertEqual(
            Alerta.objects.filter(practica=self.practica, atendida=False).count(), 3
        )

    def test_practicas_distintas_admiten_la_misma_causa_activa(self):
        self.crear_cruda()
        self.crear_cruda(practica=self.otra_practica)

        self.assertEqual(
            Alerta.objects.filter(tipo=Alerta.Tipo.REZAGO, atendida=False).count(), 2
        )

    def test_una_resuelta_no_bloquea_la_siguiente_activa(self):
        resuelta = self.crear_cruda()
        resuelta.atendida = True
        resuelta.save()
        nueva = self.crear_cruda()
        resuelta.refresh_from_db()

        self.assertTrue(resuelta.atendida)
        self.assertFalse(nueva.atendida)
        self.assertEqual(
            Alerta.objects.filter(
                practica=self.practica, tipo=Alerta.Tipo.REZAGO
            ).count(),
            2,
        )

    def test_varias_resueltas_de_la_misma_causa_conviven(self):
        for _ in range(2):
            resuelta = self.crear_cruda()
            resuelta.atendida = True
            resuelta.save()

        self.assertEqual(
            Alerta.objects.filter(
                practica=self.practica,
                tipo=Alerta.Tipo.REZAGO,
                atendida=True,
            ).count(),
            2,
        )
