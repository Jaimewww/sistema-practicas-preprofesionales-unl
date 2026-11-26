"""Paridad de los serializers compartidos con la derivación de ``ModelSerializer``.

``PracticaCardSerializer`` y ``ReporteSemanalSerializer`` son ``Serializer``
explícitos porque el ``Meta`` anidado de ``ModelSerializer`` solo existe en los
stubs de DRF —en ejecución cada serializador aporta el suyo— y el checker lo
trata como un reemplazo incompatible. Estos tests fijan lo que el contrato
observa —campos, validadores, errores, payload y OpenAPI— comparándolo contra un
``ModelSerializer`` de referencia construido con la misma declaración ``Meta``:
si la derivación cambia, la paridad falla.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from unittest import mock

from django.test import SimpleTestCase
from drf_spectacular.generators import SchemaGenerator
from rest_framework import serializers

from apps.practicas.api import PracticaCardSerializer
from apps.practicas.models import Practica
from apps.reportes.models import ReporteSemanal
from apps.reportes.serializers import (
    MENSAJE_CAMPO_NO_ADMITIDO,
    MENSAJE_CUERPO_NO_OBJETO,
    ReporteSemanalSerializer,
)

CAMPOS_TARJETA = (
    "id",
    "estudiante_id",
    "tipo",
    "subtipo",
    "estado",
    "horas_requeridas",
)
CAMPOS_REPORTE = (
    "id",
    "practica_id",
    "semana",
    "horas_reportadas",
    "estado",
    "requiere_revision",
    "fecha_registro",
)
PAYLOAD = {"semana": 3, "horas_reportadas": 8}
INGRESO = datetime(2026, 3, 2, 10, 30, tzinfo=UTC)
MENSAJE_AYUDANTIA_ESPERADO = (
    "Una ayudantía no puede reportar más de 10 horas semanales "
    "(Art. 341 del Reglamento de Régimen Académico)."
)


def _referencia(modelo, campos, solo_lectura, declarados):
    """``ModelSerializer`` con la misma ``Meta``: la derivación que se reemplazó."""
    meta = type(
        "Meta",
        (),
        {"model": modelo, "fields": campos, "read_only_fields": solo_lectura},
    )
    atributos = dict(declarados, Meta=meta)
    return type("Referencia", (serializers.ModelSerializer,), atributos)()


def _tarjeta_de_referencia():
    return _referencia(
        Practica,
        CAMPOS_TARJETA,
        CAMPOS_TARJETA,
        {"estudiante_id": serializers.IntegerField(read_only=True)},
    )


def _reporte_de_referencia():
    return _referencia(
        ReporteSemanal,
        CAMPOS_REPORTE,
        ("id", "practica_id", "estado", "requiere_revision", "fecha_registro"),
        {"practica_id": serializers.IntegerField(read_only=True)},
    )


def _validador(validador):
    """Identidad observable de un validador: su nombre y el límite que declara."""
    return (
        getattr(validador, "__name__", type(validador).__name__),
        repr(getattr(validador, "limit_value", None)),
    )


def _configuracion(campo):
    """Lo que ``ModelSerializer`` derivaba de cada campo, sin detalles internos."""
    return {
        "clase": type(campo).__name__,
        "read_only": campo.read_only,
        "required": campo.required,
        "write_only": campo.write_only,
        "allow_null": campo.allow_null,
        "allow_blank": getattr(campo, "allow_blank", None),
        "default": repr(campo.default),
        "label": campo.label,
        "help_text": campo.help_text,
        "choices": (
            [list(par) for par in dict(campo.choices).items()]
            if isinstance(campo, serializers.ChoiceField)
            else None
        ),
        "min_value": repr(getattr(campo, "min_value", None)),
        "max_value": repr(getattr(campo, "max_value", None)),
        "validadores": [_validador(validador) for validador in campo.validators],
        "mensajes": dict(campo.error_messages),
    }


def _campo(serializer, nombre):
    """El campo declarado, ya estrechado a la clase que el test necesita."""
    return serializer.fields[nombre]


def _choice(serializer, nombre):
    return cast("serializers.ChoiceField", _campo(serializer, nombre))


def _entero(serializer, nombre):
    return cast("serializers.IntegerField", _campo(serializer, nombre))


def _esquema():
    return SchemaGenerator().get_schema(request=None, public=True)


def _componente(esquema, nombre):
    return esquema["components"]["schemas"][nombre]


class PracticaCardSerializerTests(SimpleTestCase):
    """La tarjeta conserva los seis campos, sus enums y el read-only del contrato."""

    def test_declara_los_seis_campos_en_orden(self):
        self.assertEqual(list(PracticaCardSerializer().fields), list(CAMPOS_TARJETA))
        self.assertTrue(
            all(campo.read_only for campo in PracticaCardSerializer().fields.values())
        )

    def test_cada_campo_se_deriva_igual_que_con_model_serializer(self):
        actual = PracticaCardSerializer()
        referencia = _tarjeta_de_referencia()
        self.assertEqual(list(actual.fields), list(referencia.fields))
        for nombre in CAMPOS_TARJETA:
            with self.subTest(campo=nombre):
                self.assertEqual(
                    _configuracion(actual.fields[nombre]),
                    _configuracion(referencia.fields[nombre]),
                )

    def test_los_enums_son_los_del_modelo(self):
        tarjeta = PracticaCardSerializer()
        self.assertEqual(
            dict(_choice(tarjeta, "tipo").choices), dict(Practica.Tipo.choices)
        )
        self.assertEqual(
            dict(_choice(tarjeta, "subtipo").choices), dict(Practica.Subtipo.choices)
        )
        self.assertEqual(
            dict(_choice(tarjeta, "estado").choices), dict(Practica.Estado.choices)
        )

    def test_representa_una_practica_sin_campos_de_mas(self):
        practica = Practica(
            id=7,
            estudiante_id=11,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            estado=Practica.Estado.EN_CURSO,
            horas_requeridas=240,
        )
        self.assertEqual(
            PracticaCardSerializer(practica).data,
            {
                "id": 7,
                "estudiante_id": 11,
                "tipo": "laboral",
                "subtipo": "practica",
                "estado": "en_curso",
                "horas_requeridas": 240,
            },
        )


class ReporteSemanalSerializerTests(SimpleTestCase):
    """El reporte conserva entrada, validadores, errores y payload de respuesta."""

    def _contexto(self, subtipo=Practica.Subtipo.PRACTICA):
        return {"practica": SimpleNamespace(subtipo=subtipo)}

    def test_declara_los_siete_campos_en_orden_con_solo_dos_escribibles(self):
        reporte = ReporteSemanalSerializer()
        self.assertEqual(list(reporte.fields), list(CAMPOS_REPORTE))
        escribibles = [
            nombre for nombre, campo in reporte.fields.items() if not campo.read_only
        ]
        self.assertEqual(escribibles, ["semana", "horas_reportadas"])

    def test_cada_campo_se_deriva_igual_que_con_model_serializer(self):
        actual = ReporteSemanalSerializer()
        referencia = _reporte_de_referencia()
        self.assertEqual(list(actual.fields), list(referencia.fields))
        for nombre in CAMPOS_REPORTE:
            with self.subTest(campo=nombre):
                self.assertEqual(
                    _configuracion(actual.fields[nombre]),
                    _configuracion(referencia.fields[nombre]),
                )

    def test_el_estado_expone_el_enum_del_modelo(self):
        self.assertEqual(
            dict(_choice(ReporteSemanalSerializer(), "estado").choices),
            dict(ReporteSemanal.Estado.choices),
        )

    def test_rechaza_un_cuerpo_que_no_es_objeto(self):
        for cuerpo in ([PAYLOAD], "semana", 3):
            with self.subTest(cuerpo=cuerpo):
                reporte = ReporteSemanalSerializer(
                    data=cuerpo, context=self._contexto()
                )
                self.assertFalse(reporte.is_valid())
                self.assertEqual(
                    reporte.errors, {"non_field_errors": [MENSAJE_CUERPO_NO_OBJETO]}
                )

    def test_rechaza_campos_no_admitidos_y_los_que_fija_el_servidor(self):
        sobrantes = ("contenido", "estado", "requiere_revision", "id", "practica_id")
        for campo in sobrantes:
            with self.subTest(campo=campo):
                reporte = ReporteSemanalSerializer(
                    data={**PAYLOAD, campo: "x"}, context=self._contexto()
                )
                self.assertFalse(reporte.is_valid())
                self.assertEqual(reporte.errors, {campo: [MENSAJE_CAMPO_NO_ADMITIDO]})

    def test_conserva_los_errores_de_rango_de_semana_y_horas(self):
        casos = (
            (
                {"semana": 0, "horas_reportadas": 8},
                "semana",
                "La semana del reporte debe ser un número entero positivo.",
            ),
            (
                {"semana": 3, "horas_reportadas": 0},
                "horas_reportadas",
                "Las horas reportadas deben ser un número entero positivo.",
            ),
            (
                {"semana": 3, "horas_reportadas": 169},
                "horas_reportadas",
                "Una semana tiene 168 horas: no se pueden reportar más.",
            ),
        )
        for payload, campo, mensaje in casos:
            with self.subTest(payload=payload):
                reporte = ReporteSemanalSerializer(
                    data=payload, context=self._contexto()
                )
                self.assertFalse(reporte.is_valid())
                self.assertEqual(reporte.errors[campo][0], mensaje)

    def test_conserva_el_tope_de_ayudantia_del_art_341(self):
        reporte = ReporteSemanalSerializer(
            data={"semana": 3, "horas_reportadas": 11},
            context=self._contexto(Practica.Subtipo.AYUDANTIA_DOCENCIA),
        )
        self.assertFalse(reporte.is_valid())
        self.assertEqual(
            reporte.errors["horas_reportadas"],
            [MENSAJE_AYUDANTIA_ESPERADO],
        )
        limite = ReporteSemanalSerializer(
            data={"semana": 3, "horas_reportadas": 10},
            context=self._contexto(Practica.Subtipo.AYUDANTIA_DOCENCIA),
        )
        self.assertTrue(limite.is_valid())
        self.assertEqual(limite.validated_data, {"semana": 3, "horas_reportadas": 10})

    def test_save_envia_al_create_lo_validado_y_lo_que_fija_la_vista(self):
        contexto = self._contexto()
        reporte = ReporteSemanalSerializer(data=PAYLOAD, context=contexto)
        self.assertTrue(reporte.is_valid())
        with mock.patch.object(ReporteSemanal.objects, "create") as crear:
            reporte.save(practica=contexto["practica"], ingreso_revision_en=INGRESO)
        crear.assert_called_once_with(
            semana=3,
            horas_reportadas=8,
            practica=contexto["practica"],
            ingreso_revision_en=INGRESO,
        )

    def test_la_respuesta_expone_exactamente_los_siete_campos(self):
        fecha = datetime(2026, 3, 9, 8, 0, tzinfo=UTC)
        reporte = ReporteSemanal(
            id=5,
            practica_id=7,
            semana=3,
            horas_reportadas=8,
            estado=ReporteSemanal.Estado.EN_REVISION,
            requiere_revision=False,
            fecha_registro=fecha,
        )
        self.assertEqual(
            ReporteSemanalSerializer(reporte).data,
            {
                "id": 5,
                "practica_id": 7,
                "semana": 3,
                "horas_reportadas": 8,
                "estado": "en_revision",
                "requiere_revision": False,
                "fecha_registro": "2026-03-09T08:00:00Z",
            },
        )


class OpenApiParityTests(SimpleTestCase):
    """Los componentes OpenAPI conservan nombre, enums, read-only, rango y orden."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.esquema = _esquema()

    def test_la_tarjeta_conserva_su_componente_y_los_enums(self):
        tarjeta = _componente(self.esquema, "PracticaCard")
        self.assertEqual(
            tarjeta["description"], (PracticaCardSerializer.__doc__ or "").strip()
        )
        self.assertEqual(sorted(tarjeta["properties"]), sorted(CAMPOS_TARJETA))
        self.assertEqual(sorted(tarjeta["required"]), sorted(CAMPOS_TARJETA))
        self.assertTrue(
            all(
                propiedad.get("readOnly") is True
                for propiedad in tarjeta["properties"].values()
            )
        )
        for campo, componente_enum, opciones in (
            ("tipo", "TipoEnum", Practica.Tipo),
            ("subtipo", "SubtipoEnum", Practica.Subtipo),
            ("estado", "PracticaCardEstadoEnum", Practica.Estado),
        ):
            with self.subTest(campo=campo):
                self.assertEqual(
                    tarjeta["properties"][campo]["allOf"],
                    [{"$ref": f"#/components/schemas/{componente_enum}"}],
                )
                self.assertEqual(
                    _componente(self.esquema, componente_enum)["enum"],
                    [opcion.value for opcion in opciones],
                )

    def test_el_reporte_conserva_su_componente_el_enum_y_el_rango(self):
        reporte = _componente(self.esquema, "ReporteSemanal")
        self.assertEqual(
            reporte["description"], (ReporteSemanalSerializer.__doc__ or "").strip()
        )
        self.assertEqual(sorted(reporte["properties"]), sorted(CAMPOS_REPORTE))
        self.assertEqual(sorted(reporte["required"]), sorted(CAMPOS_REPORTE))
        solo_lectura = set(CAMPOS_REPORTE) - {"semana", "horas_reportadas"}
        self.assertEqual(
            {
                nombre
                for nombre, valor in reporte["properties"].items()
                if valor.get("readOnly")
            },
            solo_lectura,
        )
        self.assertEqual(
            reporte["properties"]["estado"]["allOf"],
            [{"$ref": "#/components/schemas/ReporteSemanalEstadoEnum"}],
        )
        self.assertEqual(
            _componente(self.esquema, "ReporteSemanalEstadoEnum")["enum"],
            [estado.value for estado in ReporteSemanal.Estado],
        )
        referencia = _reporte_de_referencia()
        for campo in ("semana", "horas_reportadas"):
            with self.subTest(campo=campo):
                propiedad = reporte["properties"][campo]
                esperado = _entero(referencia, campo)
                self.assertEqual(propiedad["type"], "integer")
                self.assertEqual(propiedad["minimum"], esperado.min_value)
                self.assertEqual(propiedad["maximum"], esperado.max_value)


class OpenApiRutasTests(SimpleTestCase):
    """Las rutas que sirven estos serializers conservan sus esquemas de entrada."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.esquema = _esquema()

    def test_la_ruta_del_reporte_y_las_de_practicas_responden_lo_mismo(self):
        rutas = self.esquema["paths"]
        self.assertEqual(
            rutas["/api/v1/practicas/"]["get"]["responses"]["200"]["content"][
                "application/json"
            ]["schema"],
            {"type": "array", "items": {"$ref": "#/components/schemas/PracticaCard"}},
        )
        self.assertIn(
            "#/components/schemas/PracticaCard",
            str(rutas["/api/v1/practicas/{practica_id}/"]["get"]["responses"]),
        )
        reporte = rutas["/api/v1/practicas/{practica_id}/reportes/"]["post"]
        self.assertEqual(
            reporte["requestBody"]["content"]["application/json"]["schema"],
            {"$ref": "#/components/schemas/ReporteSemanal"},
        )
        self.assertEqual(
            reporte["responses"]["201"]["content"]["application/json"]["schema"],
            {"$ref": "#/components/schemas/ReporteSemanal"},
        )


class EnvelopeDeValidacionTests(SimpleTestCase):
    """El 400 por cuerpo no admitido sigue siendo un error de validación de DRF."""

    def test_el_campo_no_admitido_es_un_validation_error_por_clave(self):
        reporte = ReporteSemanalSerializer(
            data={"contenido": "x"},
            context={"practica": SimpleNamespace(subtipo=Practica.Subtipo.PRACTICA)},
        )
        with self.assertRaises(serializers.ValidationError) as error:
            reporte.to_internal_value({"contenido": "x"})
        detalle = cast("dict[str, list]", error.exception.detail)
        self.assertEqual(detalle["contenido"][0], MENSAJE_CAMPO_NO_ADMITIDO)
