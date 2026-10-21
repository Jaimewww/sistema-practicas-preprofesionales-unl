"""Explicit projections for the practice API; domain dictionaries stay private."""

PRACTICE_FIELDS = (
    "id", "estudiante", "tipo", "tipo_display", "subtipo_display", "estado",
    "estado_display", "entidad", "tutor_academico", "tutor_entidad", "periodo",
    "carrera", "horas_requeridas", "horas_validadas", "horas_en_revision",
)
DOCUMENT_FIELDS = (
    "estado", "estado_display", "enviado_el", "validado_por", "validado_el",
    "observacion", "actividades", "resumen", "archivo", "registrado_por",
    "registrado_el", "valoracion",
)
REPORT_FIELDS = DOCUMENT_FIELDS + (
    "semana", "desde", "hasta", "horas", "confirmado_por_entidad", "evidencias",
)


def to_practica_dto(practica, resumido=False):
    """JSON-compatible shape; DjangoJSONEncoder renders dates as ISO strings."""
    dto = {key: practica[key] for key in PRACTICE_FIELDS}
    dto["url"] = f"/api/v1/practicas/{practica['id']}/"
    if not resumido:
        for name in ("plan", "informe_final", "informe_externo", "evaluacion"):
            document = practica.get(name)
            dto[name] = (
                {key: document[key] for key in DOCUMENT_FIELDS if key in document}
                if document is not None else None
            )
        dto["reportes"] = [
            {key: report[key] for key in REPORT_FIELDS if key in report}
            for report in practica["reportes"]
        ]
    return dto
