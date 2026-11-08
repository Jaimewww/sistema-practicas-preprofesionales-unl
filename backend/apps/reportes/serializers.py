"""Serializer del reporte semanal (S2, S4, S5).

El payload tiene exactamente lo que el data-model define para un reporte:
``semana`` y ``horas_reportadas``. La práctica sale del path y ``estado`` y
``fecha_registro`` los pone el servidor, así que son de solo lectura. ``contenido``
no existe en ``ReporteSemanal`` y se rechaza con 400 en su clave en vez de
ignorarse: un campo que el contrato no define nunca crea un recurso.
"""

from collections.abc import Mapping

from rest_framework import serializers
from rest_framework.settings import api_settings

from apps.practicas.models import Practica
from apps.reportes.models import (
    MAX_HORAS_AYUDANTIA,
    MENSAJE_AYUDANTIA,
    ReporteSemanal,
)

SUBTIPOS_AYUDANTIA = frozenset(
    {Practica.Subtipo.AYUDANTIA_DOCENCIA, Practica.Subtipo.AYUDANTIA_INVESTIGACION}
)
MENSAJE_CUERPO_NO_OBJETO = "El cuerpo debe ser un objeto JSON con «semana» y «horas_reportadas»."
MENSAJE_CAMPO_NO_ADMITIDO = (
    "Campo no admitido: un reporte semanal solo envía «semana» y «horas_reportadas»."
)


class ReporteSemanalSerializer(serializers.ModelSerializer):
    """Entrada ``semana`` + ``horas_reportadas``; salida con el estado y la fecha."""

    practica_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ReporteSemanal
        fields = (
            "id", "practica_id", "semana", "horas_reportadas", "estado",
            "requiere_revision", "fecha_registro",
        )
        read_only_fields = (
            "id", "practica_id", "estado", "requiere_revision", "fecha_registro",
        )

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
