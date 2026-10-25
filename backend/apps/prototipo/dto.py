"""Explicit projections for the practice API; domain dictionaries stay private."""

PRACTICE_FIELDS = (
    "id", "estudiante", "tipo", "tipo_display", "subtipo_display", "estado",
    "estado_display", "entidad", "tutor_academico", "tutor_entidad", "periodo",
    "carrera", "horas_requeridas", "horas_validadas", "horas_en_revision",
    "resultado", "resultado_display",
)
DOCUMENT_FIELDS = (
    "estado", "estado_display", "enviado_el", "validado_por", "validado_el",
    "observacion", "actividades", "resumen", "archivo", "registrado_por",
    "registrado_el", "valoracion",
)
REPORT_FIELDS = DOCUMENT_FIELDS + (
    "semana", "desde", "hasta", "horas", "confirmado_por_entidad", "evidencias",
)


def to_reporte_dto(report):
    """A weekly report; `versiones` lists what a resend replaced (RF-10)."""
    dto = {key: report[key] for key in REPORT_FIELDS if key in report}
    if "versiones" in report:
        dto["versiones"] = [
            {key: version[key] for key in REPORT_FIELDS if key in version}
            for version in report["versiones"]
        ]
    return dto


def to_alerta_dto(alerta, rol):
    """Never expose alerta.practica.alertas (a circular domain reference)."""
    practica = alerta["practica"]
    practica_id = practica["id"]
    if rol == "coordinador":
        pantalla = f"/prototipo/coordinador/practicas/{practica_id}/"
    elif rol == "tutor_academico":
        pantalla = f"/prototipo/tutor/practicas/{practica_id}/"
    else:
        pantalla = "/prototipo/mi-practica/?practica=" + practica["tipo"]
    return {
        **{key: alerta[key] for key in ("tipo", "tipo_display", "estado_badge", "detalle", "fecha")},
        "practica": {
            **{key: practica[key] for key in ("id", "estudiante", "tipo", "tipo_display", "carrera")},
            "url": f"/api/v1/practicas/{practica_id}/",
            "detalle_url": pantalla,
        },
    }


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
        dto["reportes"] = [to_reporte_dto(report) for report in practica["reportes"]]
    return dto
