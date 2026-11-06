"""Serializer del reporte semanal (S2, S4, S5).

El payload tiene exactamente lo que el data-model define para un reporte:
``semana`` y ``horas_reportadas``. La práctica sale del path y ``estado`` y
``fecha_registro`` los pone el servidor, así que son de solo lectura. ``contenido``
no existe en ``ReporteSemanal`` y se rechaza con 400 en su clave en vez de
ignorarse: un campo que el contrato no define nunca crea un recurso.
"""

from rest_framework import serializers

from apps.practicas.models import Practica
from apps.reportes.models import (
    MAX_HORAS_AYUDANTIA,
    MENSAJE_AYUDANTIA,
    MENSAJE_SEMANA_DUPLICADA,
    ReporteSemanal,
)

SUBTIPOS_AYUDANTIA = frozenset(
    {Practica.Subtipo.AYUDANTIA_DOCENCIA, Practica.Subtipo.AYUDANTIA_INVESTIGACION}
)
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
            "fecha_registro",
        )
        read_only_fields = ("id", "practica_id", "estado", "fecha_registro")

    def to_internal_value(self, data):
        """Rechaza campos fuera del data-model antes de validar los conocidos."""
        sobrantes = sorted(set(data) - set(self.fields))
        if sobrantes:
            raise serializers.ValidationError(
                {campo: [MENSAJE_CAMPO_NO_ADMITIDO] for campo in sobrantes}
            )
        return super().to_internal_value(data)

    def validate(self, attrs):
        """Art. 341 en ayudantías y una sola versión activa por semana (S4, S5)."""
        practica = self.context["practica"]
        horas = attrs["horas_reportadas"]
        if practica.subtipo in SUBTIPOS_AYUDANTIA and horas > MAX_HORAS_AYUDANTIA:
            raise serializers.ValidationError({"horas_reportadas": [MENSAJE_AYUDANTIA]})
        if ReporteSemanal.objects.filter(
            practica=practica, semana=attrs["semana"]
        ).exists():
            raise serializers.ValidationError({"semana": [MENSAJE_SEMANA_DUPLICADA]})
        return attrs
