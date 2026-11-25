"""API del plan de actividades (S8, brecha 2 de la matriz Front–API; HU-01, RF-01, RF-03).

Cuatro operaciones sobre los servicios de T024 con ``APIClient``:

* ``GET /api/v1/practicas/{id}/plan/`` — versiones del plan, de la más nueva a la
  más antigua, para cualquier rol que vea la práctica (``practicas_visibles_para``).
* ``POST /api/v1/practicas/{id}/plan/`` — solo el estudiante de la práctica envía
  el plan o, tras una devolución, la versión siguiente.
* ``POST /api/v1/planes/{id}/aprobar/`` y ``…/devolver/`` — solo el tutor académico
  con asignación activa; devolver exige observación y aprobar pasa la práctica a
  «en curso».

Fuera de alcance responde el mismo 404 que lo inexistente, el permiso va antes que
el estado y ningún rechazo escribe nada (``fotografia()``).
"""

from collections.abc import Callable
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.actividades.api import MENSAJE_CUERPO_DEVOLVER, MENSAJE_CUERPO_PLAN
from apps.actividades.models import MENSAJE_OBSERVACION, PlanActividades, Validacion
from apps.actividades.serializers import (
    MENSAJE_CAMPO_NO_ADMITIDO,
    MENSAJE_CAMPO_NO_ADMITIDO_DEVOLVER,
    MENSAJE_CONTENIDO,
)
from apps.actividades.services import (
    MENSAJE_ESTADO_PLAN,
    MENSAJE_ESTUDIANTE,
    MENSAJE_REENVIO,
    MENSAJE_TUTOR,
    devolver_plan,
    enviar_plan,
)
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.usuarios.models import Usuario

PLAN = "/api/v1/practicas/{}/plan/"
APROBAR = "/api/v1/planes/{}/aprobar/"
DEVOLVER = "/api/v1/planes/{}/devolver/"
CONTENIDO = "Actividades previstas para la práctica."
OBSERVACION = "Detalle las semanas 3 y 4."
CAMPOS_PLAN = {
    "id", "practica_id", "version", "contenido", "estado", "observacion",
    "fecha_validacion",
}
MODELOS = (
    Usuario, Carrera, Periodo, EntidadReceptora, Practica, AsignacionTutor,
    HistorialEstado, PlanActividades, Validacion,
)
ERROR_401 = {"detail": "Se requiere autenticación.", "code": "no_autenticado"}
ERROR_404 = {"detail": "No encontrado.", "code": "no_encontrado"}
MENSAJE_NO_ADMITE = (
    "La práctica está en «{estado}»: el plan de actividades solo se envía, aprueba "
    "o devuelve con la práctica asignada o en curso."
)


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username, nombre=username.title(), email=f"{username}@example.com",
        rol=rol, carrera=carrera, password=None,
    )


class PlanApiFixturesMixin:
    """Práctica asignada con tutor activo, una de otro estudiante y una sin tutor."""

    assertEqual: Callable[..., None]
    assertIs: Callable[..., None]
    assertIsNone: Callable[..., None]
    assertIsNotNone: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(codigo="ING-SIS", nombre="Ingeniería de Sistemas")
        cls.otra_carrera = Carrera.objects.create(codigo="ING-CIV", nombre="Ingeniería Civil")
        cls.entidad = EntidadReceptora.objects.create(nombre="Junta Parroquial de San Lucas")
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.par = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario("academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.otro_tutor = crear_usuario("academico2", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.coordinador = crear_usuario("coordinador1", Usuario.Rol.COORDINADOR, cls.carrera)
        cls.coordinador_ajeno = crear_usuario(
            "coordinador2", Usuario.Rol.COORDINADOR, cls.otra_carrera
        )
        cls.director = crear_usuario("director1", Usuario.Rol.DIRECTOR, cls.carrera)
        cls.secretaria = crear_usuario("secretaria1", Usuario.Rol.SECRETARIA, cls.carrera)
        cls.externo = crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.practica = cls.crear_practica(cls.estudiante)
        cls.otra_practica = cls.crear_practica(cls.par)
        cls.sin_tutor = cls.crear_practica(cls.estudiante)
        for practica in (cls.practica, cls.otra_practica):
            AsignacionTutor.objects.create(
                practica=practica, tutor_academico=cls.tutor, desde=date(2026, 1, 1)
            )

    @classmethod
    def crear_practica(cls, estudiante):
        practica = Practica(
            estudiante=estudiante, carrera=cls.carrera, entidad=cls.entidad,
            periodo=cls.periodo, tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA, horas_requeridas=240,
            estado=Practica.Estado.ASIGNADA,
        )
        practica.full_clean()
        practica.save()
        return practica

    def crear_plan(self, practica=None, version=1, estado=PlanActividades.Estado.EN_REVISION):
        return PlanActividades.objects.create(
            practica=practica or self.practica, version=version,
            contenido=f"{CONTENIDO} v{version}", estado=estado,
        )

    def poner_estado(self, practica, estado):
        Practica.objects.filter(pk=practica.pk).update(estado=estado)

    def cliente(self, usuario=None):
        cliente = APIClient()
        if usuario is not None:
            cliente.force_authenticate(user=usuario)
        return cliente

    def publicar(self, ruta, usuario, datos=None):
        return self.cliente(usuario).post(
            ruta, datos if datos is not None else {}, format="json"
        )

    def fotografia(self):
        """Filas por modelo y estados de planes y prácticas: un rechazo no cambia nada."""
        foto = {modelo.__name__: modelo.objects.count() for modelo in MODELOS}
        foto["planes"] = list(
            PlanActividades.objects.order_by("pk").values_list("pk", "version", "estado")
        )
        foto["practicas"] = list(Practica.objects.order_by("pk").values_list("pk", "estado"))
        return foto

    def assertRechazo(self, respuesta, estado, mensaje, errores):
        """Estado y envelope exacto (mensaje y ``errors`` con ``code``) sin datos."""
        self.assertEqual(respuesta.status_code, estado, respuesta.content)
        self.assertEqual(
            respuesta.json(),
            {"success": False, "message": mensaje, "data": None, "errors": errores, "meta": {}},
        )

    def assert401(self, respuesta):
        self.assertRechazo(respuesta, 401, "Autenticación requerida.", ERROR_401)

    def assert404(self, respuesta):
        self.assertRechazo(respuesta, 404, "Recurso no encontrado.", ERROR_404)

    def assert403(self, respuesta, detalle):
        self.assertRechazo(
            respuesta, 403, "Permiso denegado.", {"detail": detalle, "code": "permiso_denegado"}
        )

    def assert409(self, respuesta, detalle, codigo):
        self.assertRechazo(
            respuesta, 409, "Solicitud inválida.", {"detail": detalle, "code": codigo}
        )

    def assert400(self, respuesta, errores):
        self.assertRechazo(respuesta, 400, "Datos inválidos.", errores)

    def assertExito(self, respuesta, estado=200):
        self.assertEqual(respuesta.status_code, estado, respuesta.content)
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], True)
        self.assertEqual(cuerpo["errors"], None)
        self.assertEqual(cuerpo["meta"], {})
        self.assertEqual(
            cuerpo["message"], "Recurso creado." if estado == 201 else "Operación exitosa."
        )
        return cuerpo["data"]


class ListarPlanTests(PlanApiFixturesMixin, TestCase):
    """``GET /api/v1/practicas/{id}/plan/``: versiones de la más nueva a la más antigua."""

    def test_el_estudiante_ve_sus_versiones_con_la_observacion_de_la_devolucion(self):
        v1 = enviar_plan(practica=self.practica, contenido="Primera", autor=self.estudiante)
        devolver_plan(plan=v1, autor=self.tutor, observacion=OBSERVACION)
        v2 = enviar_plan(practica=self.practica, contenido="Segunda", autor=self.estudiante)
        validacion = Validacion.objects.get(plan=v1)

        data = self.assertExito(self.cliente(self.estudiante).get(PLAN.format(self.practica.pk)))

        self.assertEqual(len(data), 2)
        self.assertEqual(
            data[0],
            {
                "id": v2.pk, "practica_id": self.practica.pk, "version": 2,
                "contenido": "Segunda", "estado": "en_revision",
                "observacion": None, "fecha_validacion": None,
            },
        )
        self.assertEqual(
            {clave: data[1][clave] for clave in CAMPOS_PLAN - {"fecha_validacion"}},
            {
                "id": v1.pk, "practica_id": self.practica.pk, "version": 1,
                "contenido": "Primera", "estado": "devuelto", "observacion": OBSERVACION,
            },
        )
        self.assertEqual(
            data[1]["fecha_validacion"],
            validacion.fecha.isoformat().replace("+00:00", "Z"),
        )
        for fila in data:
            self.assertEqual(set(fila), CAMPOS_PLAN)

    def test_sin_plan_responde_una_lista_vacia(self):
        self.assertEqual(
            self.assertExito(self.cliente(self.estudiante).get(PLAN.format(self.practica.pk))),
            [],
        )

    def test_los_roles_que_ven_la_practica_leen_el_plan(self):
        plan = self.crear_plan()
        for actor in (self.tutor, self.coordinador, self.director, self.secretaria):
            with self.subTest(rol=actor.rol):
                data = self.assertExito(self.cliente(actor).get(PLAN.format(self.practica.pk)))
                self.assertEqual([fila["id"] for fila in data], [plan.pk])

    def test_fuera_de_alcance_responde_el_mismo_404_que_inexistente(self):
        self.crear_plan()
        inexistente = self.cliente(self.estudiante).get(PLAN.format(999_999))
        self.assert404(inexistente)
        for actor in (self.par, self.otro_tutor, self.coordinador_ajeno, self.externo):
            with self.subTest(rol=actor.username):
                fuera = self.cliente(actor).get(PLAN.format(self.practica.pk))
                self.assertEqual(fuera.status_code, 404)
                self.assertEqual(fuera.json(), inexistente.json())

    def test_sin_token_o_con_cuenta_inactiva_responde_401(self):
        self.assert401(self.cliente().get(PLAN.format(self.practica.pk)))
        Usuario.objects.filter(pk=self.estudiante.pk).update(is_active=False)
        self.estudiante.refresh_from_db()
        self.assert401(self.cliente(self.estudiante).get(PLAN.format(self.practica.pk)))


class EnviarPlanTests(PlanApiFixturesMixin, TestCase):
    """``POST /api/v1/practicas/{id}/plan/``: solo el estudiante; 201 con la versión."""

    def test_el_estudiante_envia_la_version_uno_en_revision(self):
        data = self.assertExito(
            self.publicar(PLAN.format(self.practica.pk), self.estudiante, {"contenido": CONTENIDO}),
            201,
        )

        plan = PlanActividades.objects.get()
        self.assertEqual(
            data,
            {
                "id": plan.pk, "practica_id": self.practica.pk, "version": 1,
                "contenido": CONTENIDO, "estado": "en_revision",
                "observacion": None, "fecha_validacion": None,
            },
        )
        self.assertEqual((plan.version, plan.estado), (1, "en_revision"))
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, Practica.Estado.ASIGNADA)

    def test_tras_una_devolucion_el_reenvio_crea_la_version_siguiente(self):
        self.crear_plan(estado=PlanActividades.Estado.DEVUELTO)

        data = self.assertExito(
            self.publicar(PLAN.format(self.practica.pk), self.estudiante, {"contenido": "Corregido"}),
            201,
        )

        self.assertEqual((data["version"], data["contenido"]), (2, "Corregido"))
        self.assertEqual(
            list(PlanActividades.objects.order_by("version").values_list("version", "estado")),
            [(1, "devuelto"), (2, "en_revision")],
        )

    def test_con_la_ultima_version_en_revision_o_aprobada_responde_409(self):
        for estado in (PlanActividades.Estado.EN_REVISION, PlanActividades.Estado.APROBADO):
            with self.subTest(estado=estado):
                PlanActividades.objects.all().delete()
                self.crear_plan(estado=estado)
                antes = self.fotografia()
                respuesta = self.publicar(
                    PLAN.format(self.practica.pk), self.estudiante, {"contenido": CONTENIDO}
                )
                self.assert409(
                    respuesta, MENSAJE_REENVIO.format(estado=estado), "plan_no_reenviable"
                )
                self.assertEqual(self.fotografia(), antes)

    def test_una_practica_que_no_esta_asignada_ni_en_curso_responde_409(self):
        for estado in (
            Practica.Estado.SUSPENDIDA, Practica.Estado.EN_REVISION_FINAL,
            Practica.Estado.CERRADA, Practica.Estado.CANCELADA,
        ):
            with self.subTest(estado=estado):
                self.poner_estado(self.practica, estado)
                antes = self.fotografia()
                respuesta = self.publicar(
                    PLAN.format(self.practica.pk), self.estudiante, {"contenido": CONTENIDO}
                )
                self.assert409(
                    respuesta, MENSAJE_NO_ADMITE.format(estado=estado), "practica_no_admite_plan"
                )
                self.assertEqual(self.fotografia(), antes)

    def test_solo_el_estudiante_puede_enviar(self):
        antes = self.fotografia()
        for actor in (self.tutor, self.coordinador, self.director, self.secretaria, self.externo):
            with self.subTest(rol=actor.rol):
                respuesta = self.publicar(
                    PLAN.format(self.practica.pk), actor, {"contenido": CONTENIDO}
                )
                self.assert403(respuesta, MENSAJE_ESTUDIANTE)
        self.assertEqual(self.fotografia(), antes)

    def test_la_practica_de_otro_estudiante_da_el_mismo_404_que_una_inexistente(self):
        antes = self.fotografia()
        inexistente = self.publicar(PLAN.format(999_999), self.estudiante, {"contenido": CONTENIDO})
        ajena = self.publicar(PLAN.format(self.otra_practica.pk), self.estudiante, {"contenido": CONTENIDO})
        self.assert404(inexistente)
        self.assertEqual(ajena.status_code, 404)
        self.assertEqual(ajena.json(), inexistente.json())
        self.assertEqual(self.fotografia(), antes)

    def test_sin_token_responde_401_sin_escribir(self):
        antes = self.fotografia()
        self.assert401(self.publicar(PLAN.format(self.practica.pk), None, {"contenido": CONTENIDO}))
        self.assertEqual(self.fotografia(), antes)

    def test_un_cuerpo_invalido_responde_400_sin_escribir(self):
        antes = self.fotografia()
        casos = {
            "sin_contenido": ({}, {"contenido": [MENSAJE_CONTENIDO]}),
            "vacio": ({"contenido": "   "}, {"contenido": [MENSAJE_CONTENIDO]}),
            "nulo": ({"contenido": None}, {"contenido": [MENSAJE_CONTENIDO]}),
            "campo_extra": (
                {"contenido": CONTENIDO, "estado": "aprobado"},
                {"estado": [MENSAJE_CAMPO_NO_ADMITIDO]},
            ),
            "lista": ([1], {"non_field_errors": [MENSAJE_CUERPO_PLAN]}),
            "texto": ("x", {"non_field_errors": [MENSAJE_CUERPO_PLAN]}),
        }
        for caso, (datos, errores) in casos.items():
            with self.subTest(caso=caso):
                respuesta = self.publicar(PLAN.format(self.practica.pk), self.estudiante, datos)
                self.assert400(respuesta, errores)
        self.assertEqual(self.fotografia(), antes)


class AprobarPlanTests(PlanApiFixturesMixin, TestCase):
    """``POST /api/v1/planes/{id}/aprobar/``: el plan queda aprobado y la práctica en curso."""

    def test_el_tutor_aprueba_y_la_practica_pasa_a_en_curso(self):
        plan = self.crear_plan()

        data = self.assertExito(self.publicar(APROBAR.format(plan.pk), self.tutor))

        validacion = Validacion.objects.get()
        self.assertEqual(
            data,
            {
                "id": plan.pk, "practica_id": self.practica.pk, "version": 1,
                "contenido": plan.contenido, "estado": "aprobado", "observacion": "",
                "fecha_validacion": validacion.fecha.isoformat().replace("+00:00", "Z"),
            },
        )
        plan.refresh_from_db()
        self.practica.refresh_from_db()
        self.assertEqual(plan.estado, PlanActividades.Estado.APROBADO)
        self.assertEqual(self.practica.estado, Practica.Estado.EN_CURSO)
        self.assertEqual(
            (validacion.decision, validacion.plan_id, validacion.autor_id),
            ("aprobado", plan.pk, self.tutor.pk),
        )
        historial = HistorialEstado.objects.get()
        self.assertEqual(
            (historial.estado_anterior, historial.estado_nuevo, historial.autor_id),
            ("asignada", "en_curso", self.tutor.pk),
        )

    def test_un_plan_que_no_esta_en_revision_responde_409(self):
        for estado in (PlanActividades.Estado.APROBADO, PlanActividades.Estado.DEVUELTO):
            with self.subTest(estado=estado):
                plan = self.crear_plan(version=2 if estado == "devuelto" else 1, estado=estado)
                antes = self.fotografia()
                respuesta = self.publicar(APROBAR.format(plan.pk), self.tutor)
                self.assert409(
                    respuesta, MENSAJE_ESTADO_PLAN.format(estado=estado), "plan_no_en_revision"
                )
                self.assertEqual(self.fotografia(), antes)

    def test_una_practica_suspendida_o_en_revision_final_responde_409(self):
        plan = self.crear_plan()
        for estado in (
            Practica.Estado.SUSPENDIDA, Practica.Estado.EN_REVISION_FINAL,
            Practica.Estado.CANCELADA,
        ):
            with self.subTest(estado=estado):
                self.poner_estado(self.practica, estado)
                antes = self.fotografia()
                respuesta = self.publicar(APROBAR.format(plan.pk), self.tutor)
                self.assert409(
                    respuesta, MENSAJE_NO_ADMITE.format(estado=estado), "practica_no_admite_plan"
                )
                self.assertEqual(self.fotografia(), antes)

    def test_solo_el_tutor_academico_puede_aprobar(self):
        plan = self.crear_plan()
        antes = self.fotografia()
        for actor in (self.estudiante, self.coordinador, self.director, self.externo):
            with self.subTest(rol=actor.rol):
                self.assert403(self.publicar(APROBAR.format(plan.pk), actor), MENSAJE_TUTOR)
        self.assertEqual(self.fotografia(), antes)

    def test_un_tutor_no_asignado_recibe_el_mismo_404_que_un_plan_inexistente(self):
        plan = self.crear_plan()
        sin_tutor = self.crear_plan(practica=self.sin_tutor)
        antes = self.fotografia()
        inexistente = self.publicar(APROBAR.format(999_999), self.tutor)
        self.assert404(inexistente)
        for actor, objetivo in ((self.otro_tutor, plan), (self.tutor, sin_tutor)):
            with self.subTest(actor=actor.username):
                fuera = self.publicar(APROBAR.format(objetivo.pk), actor)
                self.assertEqual(fuera.status_code, 404)
                self.assertEqual(fuera.json(), inexistente.json())
        self.assertEqual(self.fotografia(), antes)

    def test_una_asignacion_cerrada_responde_404(self):
        plan = self.crear_plan()
        AsignacionTutor.objects.filter(practica=self.practica).update(hasta=date(2026, 6, 1))
        antes = self.fotografia()
        self.assert404(self.publicar(APROBAR.format(plan.pk), self.tutor))
        self.assertEqual(self.fotografia(), antes)

    def test_sin_token_o_tutor_inactivo_responde_401(self):
        plan = self.crear_plan()
        antes = self.fotografia()
        self.assert401(self.publicar(APROBAR.format(plan.pk), None))
        Usuario.objects.filter(pk=self.tutor.pk).update(is_active=False)
        self.tutor.refresh_from_db()
        self.assert401(self.publicar(APROBAR.format(plan.pk), self.tutor))
        self.assertEqual(
            {k: v for k, v in self.fotografia().items() if k != "Usuario"},
            {k: v for k, v in antes.items() if k != "Usuario"},
        )


class DevolverPlanTests(PlanApiFixturesMixin, TestCase):
    """``POST /api/v1/planes/{id}/devolver/``: observación obligatoria; sin versión nueva."""

    def test_el_tutor_devuelve_con_observacion_y_la_practica_no_cambia(self):
        plan = self.crear_plan()

        data = self.assertExito(
            self.publicar(DEVOLVER.format(plan.pk), self.tutor, {"observacion": f"  {OBSERVACION} "})
        )

        validacion = Validacion.objects.get()
        self.assertEqual(
            (data["id"], data["estado"], data["observacion"], data["version"]),
            (plan.pk, "devuelto", OBSERVACION, 1),
        )
        self.assertIsNotNone(data["fecha_validacion"])
        plan.refresh_from_db()
        self.practica.refresh_from_db()
        self.assertEqual(plan.estado, PlanActividades.Estado.DEVUELTO)
        self.assertEqual(PlanActividades.objects.count(), 1)
        self.assertEqual(self.practica.estado, Practica.Estado.ASIGNADA)
        self.assertEqual(
            (validacion.decision, validacion.observacion, validacion.autor_id),
            ("devuelto", OBSERVACION, self.tutor.pk),
        )
        self.assertEqual(HistorialEstado.objects.count(), 0)

    def test_sin_observacion_responde_400_sin_escribir(self):
        plan = self.crear_plan()
        antes = self.fotografia()
        for datos in ({}, {"observacion": ""}, {"observacion": "   "}, {"observacion": 7}):
            with self.subTest(datos=datos):
                self.assert400(
                    self.publicar(DEVOLVER.format(plan.pk), self.tutor, datos),
                    {"observacion": [MENSAJE_OBSERVACION]},
                )
        self.assertEqual(self.fotografia(), antes)

    def test_un_cuerpo_que_no_es_objeto_responde_400_sin_escribir(self):
        plan = self.crear_plan()
        antes = self.fotografia()
        for datos in ([1], "x", 7):
            with self.subTest(datos=datos):
                self.assert400(
                    self.publicar(DEVOLVER.format(plan.pk), self.tutor, datos),
                    {"non_field_errors": [MENSAJE_CUERPO_DEVOLVER]},
                )
        self.assertEqual(self.fotografia(), antes)

    def test_un_campo_no_admitido_responde_400_sin_escribir(self):
        plan = self.crear_plan()
        antes = self.fotografia()
        casos = {
            "con_observacion": (
                {"observacion": OBSERVACION, "estado": "aprobado"},
                {"estado": [MENSAJE_CAMPO_NO_ADMITIDO_DEVOLVER]},
            ),
            "sin_observacion": (
                {"version": 2, "decision": "devuelto"},
                {
                    "decision": [MENSAJE_CAMPO_NO_ADMITIDO_DEVOLVER],
                    "version": [MENSAJE_CAMPO_NO_ADMITIDO_DEVOLVER],
                },
            ),
        }
        for caso, (datos, errores) in casos.items():
            with self.subTest(caso=caso):
                self.assert400(
                    self.publicar(DEVOLVER.format(plan.pk), self.tutor, datos), errores
                )
        self.assertEqual(self.fotografia(), antes)

    def test_un_plan_ya_decidido_responde_409(self):
        plan = self.crear_plan(estado=PlanActividades.Estado.APROBADO)
        antes = self.fotografia()
        self.assert409(
            self.publicar(DEVOLVER.format(plan.pk), self.tutor, {"observacion": OBSERVACION}),
            MENSAJE_ESTADO_PLAN.format(estado="aprobado"),
            "plan_no_en_revision",
        )
        self.assertEqual(self.fotografia(), antes)

    def test_una_practica_suspendida_responde_409(self):
        plan = self.crear_plan()
        self.poner_estado(self.practica, Practica.Estado.SUSPENDIDA)
        antes = self.fotografia()
        self.assert409(
            self.publicar(DEVOLVER.format(plan.pk), self.tutor, {"observacion": OBSERVACION}),
            MENSAJE_NO_ADMITE.format(estado="suspendida"),
            "practica_no_admite_plan",
        )
        self.assertEqual(self.fotografia(), antes)

    def test_solo_el_tutor_academico_puede_devolver(self):
        plan = self.crear_plan()
        antes = self.fotografia()
        for actor in (self.estudiante, self.coordinador, self.secretaria, self.externo):
            with self.subTest(rol=actor.rol):
                self.assert403(
                    self.publicar(DEVOLVER.format(plan.pk), actor, {"observacion": OBSERVACION}),
                    MENSAJE_TUTOR,
                )
        self.assertEqual(self.fotografia(), antes)

    def test_fuera_de_alcance_da_el_mismo_404_que_inexistente(self):
        plan = self.crear_plan()
        antes = self.fotografia()
        inexistente = self.publicar(DEVOLVER.format(999_999), self.tutor, {"observacion": OBSERVACION})
        fuera = self.publicar(DEVOLVER.format(plan.pk), self.otro_tutor, {"observacion": OBSERVACION})
        self.assert404(inexistente)
        self.assertEqual(fuera.status_code, 404)
        self.assertEqual(fuera.json(), inexistente.json())
        self.assertEqual(self.fotografia(), antes)

    def test_sin_token_responde_401_sin_escribir(self):
        plan = self.crear_plan()
        antes = self.fotografia()
        self.assert401(self.publicar(DEVOLVER.format(plan.pk), None, {"observacion": OBSERVACION}))
        self.assertEqual(self.fotografia(), antes)
