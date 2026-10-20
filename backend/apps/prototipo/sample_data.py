"""Sample context for the prototype views.

Keys are named after the domain data (spec, "Conceptos clave") so the real views
can feed the same templates from the models. Every person and entity is made up.
"""
from datetime import date, timedelta

TOTAL_SEMANAS = 16
UMBRAL_REZAGO = 80  # percent, default per career (RF-12)
PRIMERA_SEMANA = date(2026, 4, 6)
HOY = date(2026, 6, 5)

PERIODO = "MAR.26-AGO.26 GRADO"
CARRERA = "FEIRNNR - COMPUTACIÓN - PRESENCIAL - Régimen 2019 - CICLO 4A"

USUARIO = {"nombre": "MENDIETA SARANGO LUCIANA BELÉN"}
TUTOR_ACADEMICO = "PAREDES JARAMILLO ROBERTO ANDRÉS"

ESTADO_REPORTE = {
    "validado": "Validado",
    "en_revision": "En revisión",
    "devuelto": "Devuelto con observación",
    "sin_reporte": "Sin reporte",
}


def _fechas(semana):
    desde = PRIMERA_SEMANA + timedelta(weeks=semana - 1)
    return desde, desde + timedelta(days=6)


def _reporte(semana, horas, estado, **extra):
    desde, hasta = _fechas(semana)
    reporte = {
        "semana": semana,
        "desde": desde,
        "hasta": hasta,
        "horas": horas,
        "estado": estado,
        "estado_display": ESTADO_REPORTE[estado],
        "observacion": "",
        "validado_por": "",
        "validado_el": None,
        "confirmado_por_entidad": None,
    }
    if estado in ("validado", "devuelto"):
        reporte["validado_por"] = TUTOR_ACADEMICO
        reporte["validado_el"] = hasta + timedelta(days=3)
    reporte.update(extra)
    return reporte


def _validado(semana, horas, **extra):
    return _reporte(semana, horas, "validado", **extra)


def _avance(practica, reportes):
    validadas = sum(r["horas"] for r in reportes if r["estado"] == "validado")
    en_revision = sum(r["horas"] for r in reportes if r["estado"] == "en_revision")
    requeridas = practica["horas_requeridas"]
    esperadas = round(requeridas * practica["semana_actual"] / TOTAL_SEMANAS)
    minimo = round(esperadas * UMBRAL_REZAGO / 100)
    rezagada = validadas < minimo
    practica.update(
        horas_validadas=validadas,
        horas_en_revision=en_revision,
        horas_esperadas=esperadas,
        horas_minimas=minimo,
        horas_faltantes=requeridas - validadas,
        umbral_rezago=UMBRAL_REZAGO,
        total_semanas=TOTAL_SEMANAS,
        rezagada=rezagada,
        horas_estado="rezagada" if rezagada else "al_dia",
        horas_estado_display="Rezagada" if rezagada else "Al día",
        pct_validadas=round(validadas / requeridas * 100),
        pct_en_revision=round(en_revision / requeridas * 100),
        pct_esperadas=round(esperadas / requeridas * 100),
        pct_cumplimiento=round(validadas / esperadas * 100),
    )
    practica["reportes"] = reportes
    practica["pendientes"] = [
        r for r in reportes if r["estado"] in ("devuelto", "sin_reporte")
    ]
    practica["en_revision"] = [r for r in reportes if r["estado"] == "en_revision"]
    return practica


def _laboral():
    reportes = [
        _validado(1, 8, confirmado_por_entidad=True),
        _validado(2, 8, confirmado_por_entidad=True),
        _validado(3, 6, confirmado_por_entidad=True),
        _validado(4, 8, confirmado_por_entidad=True),
        _reporte(
            5,
            6,
            "devuelto",
            confirmado_por_entidad=True,
            observacion=(
                "Falta detallar qué talleres calificó. Agregue el nombre de "
                "cada taller y vuelva a enviar el reporte con la lista firmada."
            ),
        ),
        _validado(6, 4, confirmado_por_entidad=True),
        _validado(7, 8, confirmado_por_entidad=False),
        _reporte(8, 8, "en_revision", confirmado_por_entidad=False),
        _reporte(9, 0, "sin_reporte"),
    ]
    practica = {
        "clave": "laboral",
        "estudiante": USUARIO["nombre"],
        "estado": "en_curso",
        "estado_display": "En curso",
        "tipo": "laboral",
        "tipo_display": "Laboral",
        "subtipo": "ayudantia_docencia",
        "subtipo_display": "Ayudantía de docencia",
        "es_ayudantia": True,
        "entidad": "Universidad Nacional de Loja - Carrera de Computación",
        "tutor_academico": TUTOR_ACADEMICO,
        "tutor_entidad": "CELI ARMIJOS MARTHA CECILIA",
        "proyecto_vinculacion": "",
        "periodo": PERIODO,
        "carrera": CARRERA,
        "horas_requeridas": 160,
        "semana_actual": 9,
        "plan": {
            "estado": "validado",
            "estado_display": "Validado",
            "validado_por": TUTOR_ACADEMICO,
            "validado_el": date(2026, 4, 10),
            "actividades": [
                "Apoyo en la calificación de talleres de Programación.",
                "Tutorías de refuerzo a estudiantes de primer ciclo.",
                "Preparación de material para laboratorios.",
            ],
        },
        "semanas_para_reportar": [
            ("9", "Semana 9 (01/06/2026 - 07/06/2026)"),
        ],
    }
    return _avance(practica, reportes)


def _comunitaria():
    reportes = [_validado(s, h) for s, h in zip(range(1, 9), (6, 6, 8, 6, 6, 8, 6, 6))]
    reportes += [
        _reporte(9, 6, "en_revision"),
        _reporte(10, 0, "sin_reporte"),
    ]
    practica = {
        "clave": "comunitaria",
        "estudiante": USUARIO["nombre"],
        "estado": "en_curso",
        "estado_display": "En curso",
        "tipo": "comunitaria",
        "tipo_display": "Comunitaria",
        "subtipo": "",
        "subtipo_display": "",
        "es_ayudantia": False,
        "entidad": "Junta Parroquial de San Lucas",
        "tutor_academico": "ORDOÑEZ BRAVO CARLOS EDUARDO",
        "tutor_entidad": "",
        "proyecto_vinculacion": "Alfabetización digital para adultos mayores del cantón Loja",
        "periodo": PERIODO,
        "carrera": CARRERA,
        "horas_requeridas": 96,
        "semana_actual": 10,
        "plan": {
            "estado": "validado",
            "estado_display": "Validado",
            "validado_por": "ORDOÑEZ BRAVO CARLOS EDUARDO",
            "validado_el": date(2026, 4, 9),
            "actividades": [
                "Talleres semanales de uso básico del teléfono y del correo.",
                "Elaboración de guías impresas para los participantes.",
            ],
        },
        "semanas_para_reportar": [
            ("10", "Semana 10 (08/06/2026 - 14/06/2026)"),
        ],
    }
    practica = _avance(practica, reportes)
    for reporte in practica["reportes"]:
        if reporte["estado"] == "validado":
            reporte["validado_por"] = practica["tutor_academico"]
    return practica


SEMANAS_PARA_REPORTAR = _laboral()["semanas_para_reportar"]


def get_practica(clave):
    """Return the sample práctica for `clave` ("laboral" by default)."""
    return _comunitaria() if clave == "comunitaria" else _laboral()
