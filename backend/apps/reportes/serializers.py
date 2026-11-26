"""Serializer del reporte semanal (S2, S4, S5).

El payload tiene exactamente lo que el data-model define para un reporte:
``semana`` y ``horas_reportadas``. La práctica sale del path y ``estado`` y
``fecha_registro`` los pone el servidor, así que son de solo lectura. ``contenido``
no existe en ``ReporteSemanal`` y se rechaza con 400 en su clave en vez de
ignorarse: un campo que el contrato no define nunca crea un recurso.
"""

from collections.abc import Mapping
from typing import cast

from django.db import models
from rest_framework import serializers
from rest_framework.settings import api_settings
from rest_framework.utils.field_mapping import get_field_kwargs

from apps.practicas.models import Practica
from apps.reportes.models import (
    MAX_HORAS_AYUDANTIA,
    MENSAJE_AYUDANTIA,
    ReporteSemanal,
)

SUBTIPOS_AYUDANTIA = frozenset(
    {Practica.Subtipo.AYUDANTIA_DOCENCIA, Practica.Subtipo.AYUDANTIA_INVESTIGACION}
)
MENSAJE_CUERPO_NO_OBJETO = (
    "El cuerpo debe ser un objeto JSON con «semana» y «horas_reportadas»."
)
MENSAJE_CAMPO_NO_ADMITIDO = (
    "Campo no admitido: un reporte semanal solo envía «semana» y «horas_reportadas»."
)


def _campo_entero_positivo(nombre_campo):
    """``IntegerField`` derivado del campo del modelo, igual que ``ModelSerializer``.

    ``ModelSerializer`` traducía a ``min_value``/``max_value`` los validadores de
    rango que Django calcula para el motor de base de datos y sumaba los
    validadores propios del campo. Se reutiliza esa derivación para no fijar en
    el código topes que dependen del motor.
    """
    campo = cast("models.Field", ReporteSemanal._meta.get_field(nombre_campo))
    kwargs = get_field_kwargs(nombre_campo, campo)
    kwargs.pop("model_field", None)
    return serializers.IntegerField(**kwargs)


# Es un ``Serializer`` explícito y no un ``ModelSerializer``: el ``Meta`` anidado
# de ``ModelSerializer`` solo existe en los stubs de DRF —en ejecución cada
# serializador aporta el suyo— y el checker lo trata como un reemplazo
# incompatible. Los campos replican el orden, el tipo y los validadores que
# ``ModelSerializer`` derivaba del modelo; el payload y el OpenAPI no cambian y
# lo comprueba ``test_reportes_serializer_parity``.
class ReporteSemanalSerializer(serializers.Serializer):
    """Entrada ``semana`` + ``horas_reportadas``; salida con el estado y la fecha."""

    # DRF deriva la PK del modelo (``BigAutoField``) como ``BigIntegerField`` con
    # etiqueta «ID»; se declara igual para conservar el campo tal cual.
    id = serializers.BigIntegerField(read_only=True, label="ID")
    practica_id = serializers.IntegerField(read_only=True)
    semana = _campo_entero_positivo("semana")
    horas_reportadas = _campo_entero_positivo("horas_reportadas")
    estado = serializers.ChoiceField(
        choices=ReporteSemanal.Estado.choices, read_only=True
    )
    requiere_revision = serializers.BooleanField(read_only=True)
    fecha_registro = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        """Crea la fila con lo validado y los datos de servidor que envía la vista."""
        return ReporteSemanal.objects.create(**validated_data)

    def to_internal_value(self, data):
        """Solo admite un objeto con los campos que escribe el cliente.

        Un cuerpo que no es objeto (lista, texto, número) es un 400 de validación,
        no un 500; y los campos que fija el servidor (``estado``, ``requiere_revision``)
        se rechazan igual que los desconocidos.
        """
        if not isinstance(data, Mapping):
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: [MENSAJE_CUERPO_NO_OBJETO]}
            )
        escribibles = {n for n, campo in self.fields.items() if not campo.read_only}
        sobrantes = sorted(set(data) - escribibles)
        if sobrantes:
            raise serializers.ValidationError(
                {campo: [MENSAJE_CAMPO_NO_ADMITIDO] for campo in sobrantes}
            )
        return super().to_internal_value(data)

    def validate(self, attrs):
        """Art. 341 en ayudantías (S5); la semana repetida es un 409 de la vista."""
        practica = self.context["practica"]
        horas = attrs["horas_reportadas"]
        if practica.subtipo in SUBTIPOS_AYUDANTIA and horas > MAX_HORAS_AYUDANTIA:
            raise serializers.ValidationError({"horas_reportadas": [MENSAJE_AYUDANTIA]})
        return attrs
