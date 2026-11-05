"""Tests de HistorialEstado, el diario de estados de solo inserción (T009, T016)."""

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from apps.auditoria.models import HistorialEstado
from apps.practicas.models import Practica
from apps.usuarios.models import Usuario
from tests.unit.test_asignacion_tutor import AsignacionTutorFixturesMixin

MENSAJE_INMUTABLE = "El historial de estados es de solo inserción: no se puede modificar ni borrar un registro."
MENSAJE_INSERCION = "El historial pide inserción fila a fila con full_clean(); bulk_create no se permite."
MENSAJE_ESTADO_ANTERIOR = "El estado anterior solo puede quedar vacío en el registro inicial."
MENSAJE_MOTIVO = "El motivo es obligatorio al suspender, reanudar o cancelar una práctica."

TRANSICIONES = [
    (None, Practica.Estado.ASIGNADA, ""),
    (Practica.Estado.ASIGNADA, Practica.Estado.EN_CURSO, ""),
    (Practica.Estado.EN_CURSO, Practica.Estado.SUSPENDIDA, "Convenio vencido."),
    (Practica.Estado.SUSPENDIDA, Practica.Estado.EN_CURSO, "Se renovó el convenio."),
    (Practica.Estado.EN_CURSO, Practica.Estado.EN_REVISION_FINAL, ""),
    (Practica.Estado.EN_REVISION_FINAL, Practica.Estado.CERRADA, ""),
]


class HistorialEstadoFixturesMixin(AsignacionTutorFixturesMixin):
    """Reutiliza la práctica, carrera y usuarios de ``test_asignacion_tutor``."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.autor = Usuario.objects.create_user(
            username="coordinador1", nombre="Luis Paredes", email="coordinador@example.com",
            rol=Usuario.Rol.COORDINADOR, carrera=cls.carrera, password=None,
        )

    def registrar(self, anterior=None, nuevo=Practica.Estado.ASIGNADA, motivo=""):
        registro = HistorialEstado(
            practica=self.practica, estado_anterior=anterior,
            estado_nuevo=nuevo, motivo=motivo, autor=self.autor,
        )
        registro.full_clean()
        registro.save()
        return registro


class HistorialEstadoInsercionTests(HistorialEstadoFixturesMixin, TestCase):
    """Cada transición inserta un registro con anterior, nuevo, autor y fecha."""

    def test_cada_transicion_inserta_un_registro(self):
        for anterior, nuevo, motivo in TRANSICIONES:
            self.registrar(anterior=anterior, nuevo=nuevo, motivo=motivo)
        registros = list(HistorialEstado.objects.order_by("pk"))
        self.assertEqual(len(registros), len(TRANSICIONES))
        self.assertEqual([(r.estado_anterior, r.estado_nuevo, r.motivo) for r in registros], TRANSICIONES)
        self.assertTrue(all(r.fecha and r.autor_id == self.autor.pk for r in registros))

    def test_el_registro_inicial_no_tiene_estado_anterior(self):
        registro = self.registrar()
        registro.refresh_from_db()
        self.assertIsNone(registro.estado_anterior)
        self.assertEqual(registro.estado_nuevo, Practica.Estado.ASIGNADA)
        self.assertIsNotNone(registro.fecha)
        self.assertEqual(HistorialEstado.objects.count(), 1)

    def test_estado_nuevo_fuera_del_vocabulario_se_rechaza_sin_guardar(self):
        invalido = HistorialEstado(practica=self.practica, estado_nuevo="archivada", autor=self.autor)
        with self.assertRaises(ValidationError) as error:
            invalido.full_clean()
        self.assertIn("estado_nuevo", error.exception.message_dict)
        self.assertEqual(HistorialEstado.objects.count(), 0)

    def test_estado_con_tipo_invalido_da_validation_error_y_no_type_error(self):
        for valor in (["suspendida"], {"estado": "suspendida"}, 42):
            with self.subTest(valor=valor):
                invalido = HistorialEstado(practica=self.practica, estado_nuevo=valor, autor=self.autor)
                with self.assertRaises(ValidationError) as error:
                    invalido.full_clean()
                self.assertIn("estado_nuevo", error.exception.message_dict)
        self.assertEqual(HistorialEstado.objects.count(), 0)

    def test_estado_anterior_nulo_solo_en_el_registro_inicial(self):
        self.registrar(anterior=Practica.Estado.EN_CURSO, nuevo=Practica.Estado.EN_REVISION_FINAL)
        segundo = HistorialEstado(
            practica=self.practica, estado_anterior=None,
            estado_nuevo=Practica.Estado.CERRADA, autor=self.autor,
        )
        with self.assertRaises(ValidationError) as error:
            segundo.full_clean()
        self.assertEqual(error.exception.message_dict["estado_anterior"], [MENSAJE_ESTADO_ANTERIOR])
        self.assertEqual(HistorialEstado.objects.count(), 1)


class HistorialEstadoMotivoTests(HistorialEstadoFixturesMixin, TestCase):
    """El motivo es obligatorio en suspensión, cancelación y reanudación."""

    def test_motivo_obligatorio_al_suspender_cancelar_y_reanudar(self):
        casos = [
            (Practica.Estado.EN_CURSO, Practica.Estado.SUSPENDIDA),
            (Practica.Estado.SUSPENDIDA, Practica.Estado.CANCELADA),
            (Practica.Estado.SUSPENDIDA, Practica.Estado.EN_CURSO),
        ]
        for anterior, nuevo in casos:
            with self.subTest(nuevo=nuevo):
                sin_motivo = HistorialEstado(
                    practica=self.practica, estado_anterior=anterior,
                    estado_nuevo=nuevo, motivo="   ", autor=self.autor,
                )
                with self.assertRaises(ValidationError) as error:
                    sin_motivo.full_clean()
                self.assertEqual(error.exception.message_dict["motivo"], [MENSAJE_MOTIVO])
        self.assertEqual(HistorialEstado.objects.count(), 0)


class HistorialEstadoInmutableTests(HistorialEstadoFixturesMixin, TestCase):
    """Modificar o borrar un registro se rechaza y no toca la fila guardada."""

    def setUp(self):
        self.registro = self.registrar(Practica.Estado.ASIGNADA, Practica.Estado.EN_CURSO)
        self.registro.refresh_from_db()

    def assert_sin_cambios(self):
        filas = list(HistorialEstado.objects.order_by("pk"))
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0].pk, self.registro.pk)
        self.assertEqual(filas[0].practica_id, self.practica.pk)
        self.assertEqual(filas[0].autor_id, self.autor.pk)
        self.assertEqual(filas[0].fecha, self.registro.fecha)
        self.assertEqual(filas[0].estado_anterior, Practica.Estado.ASIGNADA)
        self.assertEqual(filas[0].estado_nuevo, Practica.Estado.EN_CURSO)
        self.assertEqual(filas[0].motivo, "")

    def rechazar(self, escritura):
        with self.assertRaises(ValidationError) as error:
            escritura()
        self.assertEqual(error.exception.messages, [MENSAJE_INMUTABLE])
        self.assert_sin_cambios()

    def test_modificar_un_registro_guardado_se_rechaza(self):
        for nombre, kwargs in {
            "save": {},
            "save con update_fields": {"update_fields": ["estado_nuevo"]},
            "save con force_update": {"force_update": True},
        }.items():
            with self.subTest(escritura=nombre):
                fila = HistorialEstado.objects.get(pk=self.registro.pk)
                fila.estado_nuevo = Practica.Estado.CERRADA
                self.assertRaises(ValidationError, fila.save, **kwargs)
                self.assert_sin_cambios()

    def test_guardar_con_pk_existente_se_rechaza(self):
        self.rechazar(lambda: HistorialEstado(
            pk=self.registro.pk, practica=self.practica,
            estado_anterior=Practica.Estado.ASIGNADA, estado_nuevo=Practica.Estado.CANCELADA,
            motivo="Cancelación indebida.", autor=self.autor,
        ).save())

    def test_reasignar_por_el_gestor_inverso_se_rechaza(self):
        otra = self.crear_practica()
        for nombre, escritura in {
            "add()": lambda: otra.historial_estados.add(self.registro),
            "set()": lambda: otra.historial_estados.set([self.registro]),
        }.items():
            with self.subTest(escritura=nombre):
                self.rechazar(escritura)

    def test_actualizacion_y_borrado_masivos_se_rechazan(self):
        obsoleta = HistorialEstado.objects.get(pk=self.registro.pk)
        obsoleta.estado_nuevo = Practica.Estado.CERRADA
        casos = {
            "filter().update()": lambda: HistorialEstado.objects.filter(pk=self.registro.pk).update(
                estado_nuevo=Practica.Estado.CERRADA
            ),
            "all().update()": lambda: HistorialEstado.objects.all().update(motivo="otro"),
            "filter().delete()": lambda: HistorialEstado.objects.filter(pk=self.registro.pk).delete(),
            "all().delete()": lambda: HistorialEstado.objects.all().delete(),
            "Model.delete()": self.registro.delete,
            "bulk_update()": lambda: HistorialEstado.objects.bulk_update([obsoleta], ["estado_nuevo"]),
            "update_or_create()": lambda: HistorialEstado.objects.update_or_create(
                pk=self.registro.pk, defaults={"estado_nuevo": Practica.Estado.CERRADA}
            ),
        }
        for nombre, escritura in casos.items():
            with self.subTest(escritura=nombre):
                self.rechazar(escritura)

    def test_bulk_create_se_rechaza_porque_no_valida_cada_fila(self):
        nueva = HistorialEstado(
            practica=self.practica, estado_anterior=Practica.Estado.EN_CURSO,
            estado_nuevo=Practica.Estado.SUSPENDIDA, autor=self.autor,
        )
        casos = {
            "bulk_create()": lambda: HistorialEstado.objects.bulk_create([nueva]),
            "bulk_create(update_conflicts=True)": lambda: HistorialEstado.objects.bulk_create(
                [nueva], update_conflicts=True, update_fields=["motivo"]
            ),
        }
        for nombre, escritura in casos.items():
            with self.subTest(escritura=nombre):
                with self.assertRaises(ValidationError) as error:
                    escritura()
                self.assertEqual(error.exception.messages, [MENSAJE_INSERCION])
                self.assert_sin_cambios()

    def test_borrar_la_practica_o_su_historial_por_el_gestor_inverso_se_rechaza(self):
        with self.assertRaises(ProtectedError):
            self.practica.delete()
        self.assert_sin_cambios()
        self.rechazar(self.practica.historial_estados.all().delete)
