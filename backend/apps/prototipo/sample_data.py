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
TUTOR_ENTIDAD = "CELI ARMIJOS MARTHA CECILIA"
PLAZO_REVISION_DIAS = 5  # business days, default per career (RF-12)

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
        "enviado_el": None if estado == "sin_reporte" else hasta + timedelta(days=1),
        "actividades": [],
        "evidencias": [],
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
        _reporte(
            8,
            8,
            "en_revision",
            confirmado_por_entidad=False,
            actividades=[
                "Calificación de los talleres 7 y 8 de Programación.",
                "Dos tutorías de refuerzo a estudiantes de primer ciclo.",
            ],
            evidencias=["talleres-semana-8.pdf", "asistencia-tutorias.pdf"],
        ),
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
        "tutor_entidad": TUTOR_ENTIDAD,
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


# Tutors (T1-T5, R1-R5). More made-up practices so their lists have content.
# Ids are stable: 1 and 2 are the student's practices above.

TUTOR_ENTIDAD_SUR = "VIVANCO LEÓN PABLO ESTEBAN"
ENTIDAD_SUR = "Soluciones Informáticas del Sur Cía. Ltda."

ESTADO_PRACTICA = {
    "asignada": "Asignada",
    "en_curso": "En curso",
    "en_revision_final": "En revisión final",
}

TIPO_REVISION = {
    "plan": "Plan de actividades",
    "reporte": "Reporte semanal",
    "informe": "Informe final",
}


def _practica(practica_id, estudiante, tipo, estado, reportes, **datos):
    practica = {
        "id": practica_id,
        "clave": str(practica_id),
        "estudiante": estudiante,
        "estado": estado,
        "estado_display": ESTADO_PRACTICA[estado],
        "tipo": tipo,
        "tipo_display": tipo.capitalize(),
        "subtipo": "",
        "subtipo_display": "",
        "es_ayudantia": False,
        "entidad": "",
        "tutor_academico": TUTOR_ACADEMICO,
        "tutor_entidad": "",
        "proyecto_vinculacion": "",
        "periodo": PERIODO,
        "carrera": CARRERA,
        "horas_requeridas": 160,
        "semana_actual": 9,
        "semanas_para_reportar": [],
        "informe_final": None,
        "informe_externo": None,
        "evaluacion": None,
    }
    practica.update(datos)
    return _avance(practica, reportes)


def _plan(estado, actividades, fecha):
    """A plan sent on `fecha`; once decided, `fecha` is also the decision date."""
    decidido = estado != "en_revision"
    return {
        "estado": estado,
        "estado_display": ESTADO_REPORTE[estado],
        "enviado_el": fecha,
        "validado_por": TUTOR_ACADEMICO if decidido else "",
        "validado_el": fecha if decidido else None,
        "observacion": "",
        "actividades": actividades,
    }


def _ayudantia_investigacion():
    reportes = [
        _validado(semana, horas, confirmado_por_entidad=True)
        for semana, horas in zip(range(1, 7), (8, 8, 10, 8, 6, 8))
    ]
    reportes += [
        _reporte(
            7,
            8,
            "en_revision",
            confirmado_por_entidad=False,
            actividades=[
                "Limpieza del conjunto de datos de matrícula 2020-2025.",
                "Reunión de avance con el grupo de investigación.",
            ],
            evidencias=["limpieza-datos-semana-7.pdf"],
        ),
        _reporte(
            8,
            10,
            "en_revision",
            confirmado_por_entidad=True,
            actividades=["Primer modelo de predicción de deserción y su informe."],
            evidencias=["modelo-desercion-v1.pdf"],
        ),
        _reporte(9, 0, "sin_reporte"),
    ]
    return _practica(
        3,
        "JIMÉNEZ CASTILLO DIEGO ALEJANDRO",
        "laboral",
        "en_curso",
        reportes,
        subtipo="ayudantia_investigacion",
        subtipo_display="Ayudantía de investigación",
        es_ayudantia=True,
        entidad="Universidad Nacional de Loja - Carrera de Computación",
        tutor_entidad=TUTOR_ENTIDAD,
        plan=_plan(
            "validado",
            ["Preparación de datos y modelos para el proyecto de deserción estudiantil."],
            date(2026, 4, 9),
        ),
    )


def _comunitaria_asignada():
    return _practica(
        4,
        "QUIZHPE GUAMÁN ANDREA SOFÍA",
        "comunitaria",
        "asignada",
        [],
        entidad="GAD Parroquial de Vilcabamba",
        proyecto_vinculacion="Sitio web informativo para el GAD parroquial de Vilcabamba",
        horas_requeridas=96,
        plan=_plan(
            "en_revision",
            [
                "Levantamiento de la información que publicará el GAD.",
                "Diseño y publicación del sitio web.",
                "Capacitación al personal que lo actualizará.",
            ],
            date(2026, 5, 29),
        ),
    )


def _pasantia(practica_id, estudiante, informe_final, informe_externo):
    """A pasantía that already completed its 160 h and waits for the closing reports."""
    reportes = [_validado(semana, 20, confirmado_por_entidad=True) for semana in range(1, 9)]
    return _practica(
        practica_id,
        estudiante,
        "laboral",
        "en_revision_final",
        reportes,
        subtipo="pasantia",
        subtipo_display="Pasantía",
        entidad=ENTIDAD_SUR,
        tutor_entidad=TUTOR_ENTIDAD_SUR,
        plan=_plan(
            "validado",
            ["Desarrollo del módulo de inventario del sistema de la empresa."],
            date(2026, 4, 8),
        ),
        informe_final=informe_final,
        informe_externo=informe_externo,
    )


def _informe_final(estado, enviado_el, archivo, **extra):
    informe = {
        "estado": estado,
        "estado_display": ESTADO_REPORTE[estado],
        "enviado_el": enviado_el,
        "validado_por": "",
        "validado_el": None,
        "observacion": "",
        "resumen": (
            "Resumen de las actividades cumplidas, los resultados obtenidos y las "
            "horas acreditadas en la pasantía."
        ),
        "archivo": archivo,
    }
    informe.update(extra)
    return informe


def _pasantia_lista_para_evaluar():
    return _pasantia(
        5,
        "TORRES VIVANCO MATEO JOSÉ",
        _informe_final(
            "validado",
            date(2026, 6, 1),
            "informe-final-torres.pdf",
            validado_por=TUTOR_ACADEMICO,
            validado_el=date(2026, 6, 3),
        ),
        {
            "registrado_por": TUTOR_ENTIDAD_SUR,
            "registrado_el": date(2026, 6, 2),
            "valoracion": "Cumplió las actividades del plan con autonomía y puntualidad.",
            "archivo": "informe-entidad-torres.pdf",
        },
    )


def _pasantia_con_informe_en_revision():
    return _pasantia(
        6,
        "CUENCA ROJAS VALERIA ISABEL",
        _informe_final("en_revision", date(2026, 6, 2), "informe-final-cuenca.pdf"),
        None,
    )


def _practicas():
    """Every sample práctica, rebuilt on each call so a request never leaks state."""
    laboral, comunitaria = _laboral(), _comunitaria()
    for practica_id, practica in ((1, laboral), (2, comunitaria)):
        practica.update(
            id=practica_id, informe_final=None, informe_externo=None, evaluacion=None
        )
    return [
        laboral,
        comunitaria,
        _ayudantia_investigacion(),
        _comunitaria_asignada(),
        _pasantia_lista_para_evaluar(),
        _pasantia_con_informe_en_revision(),
    ]


def _dias_habiles(desde, hasta):
    """Business days after `desde` up to `hasta` (the review deadline counts them)."""
    dias = (desde + timedelta(days=n) for n in range(1, (hasta - desde).days + 1))
    return sum(1 for dia in dias if dia.weekday() < 5)


def practicas_del_tutor(tutor=TUTOR_ACADEMICO):
    """T3: practices whose single active academic tutor is `tutor` (S-02)."""
    return [p for p in _practicas() if p["tutor_academico"] == tutor]


def get_practica_del_tutor(practica_id, tutor=TUTOR_ACADEMICO):
    return next((p for p in practicas_del_tutor(tutor) if p["id"] == practica_id), None)


def _pendiente(tipo, clave, titulo, practica, documento):
    dias = _dias_habiles(documento["enviado_el"], HOY)
    return {
        "clave": clave,
        "tipo": tipo,
        "tipo_display": TIPO_REVISION[tipo],
        "titulo": titulo,
        "practica": practica,
        "documento": documento,
        "enviado_el": documento["enviado_el"],
        "dias_espera": dias,
        "plazo_revision": PLAZO_REVISION_DIAS,
        "fuera_de_plazo": dias > PLAZO_REVISION_DIAS,
        "estado": documento["estado"],
        "estado_display": ESTADO_REPORTE[documento["estado"]],
    }


def pendientes_de_revision(tutor=TUTOR_ACADEMICO):
    """T1: plans, weekly reports and final reports in review, oldest first."""
    items = []
    for p in practicas_del_tutor(tutor):
        if p["plan"]["estado"] == "en_revision":
            items.append(
                _pendiente("plan", f"plan-{p['id']}", "Plan de actividades", p, p["plan"])
            )
        for r in p["en_revision"]:
            clave = f"reporte-{p['id']}-{r['semana']}"
            items.append(_pendiente("reporte", clave, f"Semana {r['semana']}", p, r))
        informe = p["informe_final"]
        if informe and informe["estado"] == "en_revision":
            items.append(
                _pendiente("informe", f"informe-{p['id']}", "Informe final", p, informe)
            )
    return sorted(items, key=lambda item: item["enviado_el"])


def get_pendiente(clave, tutor=TUTOR_ACADEMICO):
    return next((i for i in pendientes_de_revision(tutor) if i["clave"] == clave), None)


def requisitos_evaluacion(practica):
    """What HU-11 still needs before the final evaluation can be recorded."""
    faltan = []
    informe = practica["informe_final"]
    if not informe or informe["estado"] != "validado":
        faltan.append("el informe final del estudiante revisado")
    if not practica["informe_externo"]:
        faltan.append("el informe externo")
    return faltan

