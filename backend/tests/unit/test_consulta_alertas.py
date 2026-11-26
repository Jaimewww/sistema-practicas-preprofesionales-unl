"""Consulta de alertas activas visibles para un destinatario (T17, T045, HU-06).

``apps.alertas.consultas.alertas_visibles_para`` es la base de solo lectura de la
vista de T045. Cruza dos reglas ya existentes: el alcance de filas
``practicas_visibles_para`` (T019: prácticas propias del estudiante, asignación
vigente del tutor, carrera del coordinador) y el mapeo de destinatarios por tipo
de ``DESTINATARIOS_POR_TIPO`` (HU-06). El rol y el estado de la cuenta se releen
de la fila guardada, así que un objeto del llamador con datos viejos no decide.

La consulta no escribe, no resuelve historial atendido, no notifica y no conoce
la petición HTTP: devuelve un ``QuerySet`` de ``Alerta`` activas ordenadas de la
más reciente a la más antigua (``-fecha`` y, para el empate, ``-pk``).
"""

from datetime import date

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.db.models import QuerySet
from django.test import TestCase

from apps.alertas.consultas import alertas_visibles_para
from apps.alertas.models import Alerta
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import practicas_visibles_para

Tipo = Alerta.Tipo
Rol = Usuario.Rol
DESDE = date(2026, 3, 1)


class ConsultaAlertasFixturesMixin:
    """Dos carreras, todos los roles y una práctica con alertas de cada tipo."""

    carrera: Carrera
    otra_carrera: Carrera
    entidad: EntidadReceptora
    periodo: Periodo
    estudiante: Usuario
    otro_estudiante: Usuario
    tutor: Usuario
    otro_tutor: Usuario
    coordinador: Usuario
    coordinador_ajeno: Usuario
    director: Usuario
    secretaria: Usuario
    tutor_entidad: Usuario
    practica: Practica
    practica_ajena: Practica
    practica_otra_carrera: Practica
    alerta_reporte: Alerta
    alerta_revision: Alerta
    alerta_rezago: Alerta
    alerta_ajena: Alerta
    alerta_otra_carrera: Alerta

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        cls.entidad = EntidadReceptora.objects.create(
            nombre="Junta Parroquial de San Lucas"
        )
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )

        cls.estudiante = cls.crear_usuario("estudiante1", Rol.ESTUDIANTE)
        cls.otro_estudiante = cls.crear_usuario("estudiante2", Rol.ESTUDIANTE)
        cls.tutor = cls.crear_usuario("tutor1", Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.otro_tutor = cls.crear_usuario("tutor2", Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.coordinador = cls.crear_usuario(
            "coordinador1", Rol.COORDINADOR, cls.carrera
        )
        cls.coordinador_ajeno = cls.crear_usuario(
            "coordinador2", Rol.COORDINADOR, cls.otra_carrera
        )
        cls.director = cls.crear_usuario("director1", Rol.DIRECTOR, cls.carrera)
        cls.secretaria = cls.crear_usuario("secretaria1", Rol.SECRETARIA, cls.carrera)
        cls.tutor_entidad = cls.crear_usuario("externo1", Rol.TUTOR_ENTIDAD)

        cls.practica = cls.crear_practica(
            cls.estudiante, tutor_entidad=cls.tutor_entidad
        )
        cls.practica_ajena = cls.crear_practica(cls.otro_estudiante)
        cls.practica_otra_carrera = cls.crear_practica(
            cls.otro_estudiante, carrera=cls.otra_carrera
        )

        # El tutor tiene la asignación vigente de ``practica``; su par la de
        # ``practica_ajena``. Nadie más tiene asignaciones activas.
        cls.asignacion = AsignacionTutor.objects.create(
            practica=cls.practica, tutor_academico=cls.tutor, desde=DESDE
        )
        AsignacionTutor.objects.create(
            practica=cls.practica_ajena, tutor_academico=cls.otro_tutor, desde=DESDE
        )

        cls.alerta_reporte = cls.crear_alerta(cls.practica, Tipo.REPORTE_NO_ENVIADO)
        cls.alerta_revision = cls.crear_alerta(cls.practica, Tipo.REVISION_PENDIENTE)
        cls.alerta_rezago = cls.crear_alerta(cls.practica, Tipo.REZAGO)
        cls.alerta_ajena = cls.crear_alerta(cls.practica_ajena, Tipo.REZAGO)
        cls.alerta_otra_carrera = cls.crear_alerta(
            cls.practica_otra_carrera, Tipo.REPORTE_NO_ENVIADO
        )

    @classmethod
    def crear_usuario(cls, username, rol, carrera=None, **extra):
        return Usuario.objects.create_user(
            username=username,
            nombre=username.title(),
            email=f"{username}@example.com",
            rol=rol,
            carrera=carrera,
            password=None,
            **extra,
        )

    @classmethod
    def crear_practica(cls, estudiante, carrera=None, tutor_entidad=None):
        practica = Practica(
            estudiante=estudiante,
            carrera=carrera or cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
            tutor_entidad=tutor_entidad,
        )
        practica.full_clean()
        practica.save()
        return practica

    @classmethod
    def crear_alerta(cls, practica, tipo):
        return Alerta.objects.create(practica=practica, tipo=tipo)

    def pks(self, usuario):
        return set(alertas_visibles_para(usuario).values_list("pk", flat=True))

    def pks_ordenados(self, usuario):
        return list(alertas_visibles_para(usuario).values_list("pk", flat=True))


class AutoridadConsultaAlertasTests(ConsultaAlertasFixturesMixin, TestCase):
    def test_un_cambio_de_rol_no_mezcla_tipo_y_alcance(self):
        # A tutor is assigned only to practica; as a student the same account
        # would instead own practica_ajena, but cannot see its review alerts.
        Practica.objects.filter(pk=self.practica_ajena.pk).update(
            estudiante_id=self.tutor.pk
        )
        ajena = self.crear_alerta(self.practica_ajena, Tipo.REVISION_PENDIENTE)
        usuario_reads = 0

        def change_role_before_second_read(execute, sql, params, many, context):
            nonlocal usuario_reads
            if (
                sql.lstrip().upper().startswith("SELECT")
                and 'FROM "usuarios_usuario"' in sql
            ):
                usuario_reads += 1
                if usuario_reads == 2:
                    Usuario.objects.filter(pk=self.tutor.pk).update(rol=Rol.ESTUDIANTE)
            return execute(sql, params, many, context)

        with connection.execute_wrapper(change_role_before_second_read):
            obtenidas = self.pks(self.tutor)

        self.assertNotIn(ajena.pk, obtenidas)
        self.assertEqual(
            obtenidas,
            {self.alerta_reporte.pk, self.alerta_revision.pk, self.alerta_rezago.pk},
        )


class AlcancePorRolYDestinatarioTests(ConsultaAlertasFixturesMixin, TestCase):
    """Solo las alertas de los tipos cuyo destinatario es el rol guardado."""

    def test_estudiante_solo_ve_sus_alertas_de_sus_tipos(self):
        self.assertEqual(
            self.pks(self.estudiante),
            {self.alerta_reporte.pk, self.alerta_rezago.pk},
        )
        self.assertNotIn(self.alerta_revision.pk, self.pks(self.estudiante))

    def test_tutor_academico_ve_los_tres_tipos_de_su_asignacion_vigente(self):
        self.assertEqual(
            self.pks(self.tutor),
            {self.alerta_reporte.pk, self.alerta_revision.pk, self.alerta_rezago.pk},
        )
        self.assertNotIn(self.alerta_ajena.pk, self.pks(self.tutor))

    def test_coordinador_ve_su_carrera_sin_revision_pendiente(self):
        self.assertEqual(
            self.pks(self.coordinador),
            {self.alerta_reporte.pk, self.alerta_rezago.pk, self.alerta_ajena.pk},
        )
        self.assertNotIn(self.alerta_revision.pk, self.pks(self.coordinador))
        self.assertNotIn(self.alerta_otra_carrera.pk, self.pks(self.coordinador))

    def test_coordinador_de_otra_carrera_solo_ve_las_alertas_de_la_suya(self):
        self.assertEqual(
            self.pks(self.coordinador_ajeno), {self.alerta_otra_carrera.pk}
        )

    def test_roles_sin_destinatario_no_ven_nada_aunque_el_alcance_los_incluya(self):
        alcances = {
            self.director: practicas_visibles_para(self.director),
            self.secretaria: practicas_visibles_para(self.secretaria),
            self.tutor_entidad: practicas_visibles_para(self.tutor_entidad),
        }
        for usuario, alcance in alcances.items():
            with self.subTest(rol=usuario.rol):
                self.assertTrue(
                    alcance.filter(pk=self.practica.pk).exists(),
                    "el alcance de filas sí incluye la práctica",
                )
                self.assertEqual(self.pks(usuario), set())

    def test_la_alerta_atendida_no_aparece_y_sigue_guardada(self):
        atendida = Alerta.objects.create(
            practica=self.practica_otra_carrera,
            tipo=Tipo.REZAGO,
            atendida=True,
        )

        self.assertEqual(
            self.pks(self.coordinador_ajeno), {self.alerta_otra_carrera.pk}
        )
        self.assertTrue(Alerta.objects.filter(pk=atendida.pk, atendida=True).exists())

    def test_el_tutor_anterior_no_conserva_acceso_tras_el_reasignado(self):
        self.asignacion.hasta = date(2026, 4, 1)
        self.asignacion.save()
        nuevo = AsignacionTutor.objects.create(
            practica=self.practica,
            tutor_academico=self.otro_tutor,
            desde=date(2026, 4, 1),
        )

        self.assertEqual(self.pks(self.tutor), set())
        self.assertEqual(
            self.pks(self.otro_tutor),
            {
                self.alerta_reporte.pk,
                self.alerta_revision.pk,
                self.alerta_rezago.pk,
                self.alerta_ajena.pk,
            },
        )
        self.assertIsNotNone(nuevo.pk)


class FalloCerradoTests(ConsultaAlertasFixturesMixin, TestCase):
    """Anónimo, sin guardar, borrado, inactivo o con rol ajeno no ve nada."""

    def test_usuario_ausente_no_guardado_borrado_o_inactivo_no_ve_nada(self):
        sin_guardar = Usuario(
            username="fantasma",
            nombre="Fantasma",
            email="fantasma@example.com",
            rol=Rol.COORDINADOR,
            carrera=self.carrera,
        )
        borrado = self.crear_usuario("coordinador3", Rol.COORDINADOR, self.carrera)
        Usuario.objects.filter(pk=borrado.pk).delete()
        inactivo = self.crear_usuario("coordinador4", Rol.COORDINADOR, self.carrera)
        Usuario.objects.filter(pk=inactivo.pk).update(is_active=False)

        for usuario in (
            None,
            AnonymousUser(),
            sin_guardar,
            Usuario(username="inventado", email="inventado@example.com"),
            borrado,
            inactivo,
        ):
            with self.subTest(usuario=usuario):
                self.assertEqual(self.pks(usuario), set())

    def test_prevalecen_el_rol_y_el_estado_guardados_sobre_el_objeto_del_llamador(
        self,
    ):
        self.estudiante.rol = Rol.COORDINADOR
        self.estudiante.carrera = self.carrera
        self.assertEqual(
            self.pks(self.estudiante),
            {self.alerta_reporte.pk, self.alerta_rezago.pk},
        )

        Usuario.objects.filter(pk=self.coordinador.pk).update(rol=Rol.DIRECTOR)
        self.coordinador.rol = Rol.COORDINADOR
        self.assertEqual(self.pks(self.coordinador), set())

    def test_el_staff_o_superusuario_no_abre_el_alcance(self):
        Usuario.objects.filter(pk=self.estudiante.pk).update(
            is_staff=True, is_superuser=True
        )
        self.estudiante.refresh_from_db()

        self.assertEqual(
            self.pks(self.estudiante),
            {self.alerta_reporte.pk, self.alerta_rezago.pk},
        )


class ConsultaSoloLecturaYOrdenTests(ConsultaAlertasFixturesMixin, TestCase):
    """QuerySet ordenado de la base, sin escrituras ni caché adelantado."""

    def test_devuelve_un_queryset_filtrado_en_la_base(self):
        consulta = alertas_visibles_para(self.coordinador)

        self.assertIsInstance(consulta, QuerySet)
        self.assertIsNone(consulta._result_cache)
        sql = str(consulta.query)
        self.assertIn('"alertas_alerta"."atendida"', sql)
        self.assertIn('"alertas_alerta"."tipo"', sql)
        self.assertIn('"alertas_alerta"."practica_id"', sql)
        self.assertTrue(consulta.ordered)

    def test_la_consulta_no_crea_ni_modifica_alertas(self):
        antes = list(
            Alerta.objects.order_by("pk").values_list("pk", "tipo", "atendida")
        )
        for usuario in (
            self.estudiante,
            self.tutor,
            self.coordinador,
            self.coordinador_ajeno,
            None,
        ):
            self.pks(usuario)

        self.assertEqual(
            list(Alerta.objects.order_by("pk").values_list("pk", "tipo", "atendida")),
            antes,
        )

    def test_el_orden_es_el_mas_reciente_primero_con_pk_como_desempate(self):
        Alerta.objects.filter(pk=self.alerta_reporte.pk).update(fecha=date(2026, 2, 1))
        Alerta.objects.filter(pk=self.alerta_revision.pk).update(fecha=date(2026, 3, 1))
        Alerta.objects.filter(pk=self.alerta_rezago.pk).update(fecha=date(2026, 3, 1))
        self.assertGreater(self.alerta_rezago.pk, self.alerta_revision.pk)

        esperado = [
            self.alerta_rezago.pk,
            self.alerta_revision.pk,
            self.alerta_reporte.pk,
        ]
        self.assertEqual(self.pks_ordenados(self.tutor), esperado)
        self.assertEqual(self.pks_ordenados(self.tutor), esperado)
