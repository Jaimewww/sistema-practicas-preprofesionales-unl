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
    # El rezago compara las horas validadas más las que están en revisión
    # (spec, HU-06 caso 3 y clarify 2026-10-11; data-model, regla 2).
    rezagada = validadas + en_revision < minimo
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
        "incumplimientos": [
            {
                "descripcion": (
                    "No asistió dos días consecutivos a las tutorías de refuerzo "
                    "sin presentar justificativo."
                ),
                "reportado_por": TUTOR_ENTIDAD,
                "reportado_el": date(2026, 5, 18),
            }
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
    "suspendida": "Suspendida",
    "cancelada": "Cancelada",
    "cerrada": "Cerrada",
}

# La práctica cerrada conserva el resultado de la evaluación (Art. 339).
RESULTADO_PRACTICA = {
    "aprobada": "Aprobada",
    "no_aprobada": "No aprobada",
}

# Estados en los que la práctica ya no admite cambios (mapa, sección 4).
ESTADOS_SOLO_LECTURA = ("suspendida", "cancelada", "cerrada")

# Estados en los que la práctica sigue activa: se evalúan para el rezago
# (CU-03, alternativa 1a).
ESTADOS_ACTIVOS = ("en_curso",)

TIPO_REVISION = {
    "plan": "Plan de actividades",
    "reporte": "Reporte semanal",
    "informe": "Informe final",
}


def _clave_badge(practica):
    """Clave de color de la insignia del estado (include estado_badge)."""
    if practica["estado"] == "cerrada":
        return (
            "cerrada_aprobada"
            if practica.get("resultado") == "aprobada"
            else "cerrada_no_aprobada"
        )
    return practica["estado"]


def _historial_inicial(practica):
    """Historial de ejemplo hasta el estado actual de la práctica (RF-10)."""
    autor = practica["tutor_academico"]
    entradas = [
        {
            "estado_anterior": "",
            "estado_nuevo": "asignada",
            "autor": "SISTEMA",
            "fecha": date(2026, 4, 6),
            "motivo": "",
        }
    ]

    def _entrada(anterior, nuevo, fecha, motivo=""):
        return {
            "estado_anterior": anterior,
            "estado_nuevo": nuevo,
            "autor": COORDINADOR if nuevo in ("suspendida", "cancelada", "cerrada") else autor,
            "fecha": fecha,
            "motivo": motivo,
        }

    if practica["estado"] != "asignada":
        entradas.append(_entrada("asignada", "en_curso", date(2026, 4, 10)))
    if practica["estado"] in ("en_revision_final", "cerrada"):
        entradas.append(_entrada("en_curso", "en_revision_final", date(2026, 6, 3)))
    if practica["estado"] in ("suspendida", "cancelada"):
        entradas.append(
            _entrada(
                "en_curso",
                "suspendida",
                date(2026, 5, 20),
                "La entidad receptora informó que la persona practicante "
                "cumplió un período de licencia.",
            )
        )
    if practica["estado"] == "cancelada":
        entradas.append(
            _entrada("suspendida", "cancelada", date(2026, 5, 28), "La práctica se abandonó.")
        )
    if practica["estado"] == "cerrada":
        entradas.append(
            _entrada(
                "en_revision_final",
                "cerrada",
                date(2026, 6, 4),
                "Práctica cerrada con el resultado de la evaluación final.",
            )
        )
    return entradas


def _completar(practica):
    """Defaults que toda práctica necesita: historial, alertas e insignia."""
    practica.setdefault(
        "plan", _plan("validado", ["Actividades de la práctica."], date(2026, 4, 8))
    )
    practica.setdefault("historial", _historial_inicial(practica))
    practica.setdefault("incumplimientos", [])
    practica.setdefault("resultado", "")
    practica.setdefault("resultado_display", "")
    practica["estado_badge"] = _clave_badge(practica)
    return practica


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
    if estado == "cerrada":
        resultado = datos.get("resultado", "aprobada")
        practica["resultado"] = resultado
        practica["resultado_display"] = RESULTADO_PRACTICA[resultado]
        practica["estado_display"] = f"Cerrada ({RESULTADO_PRACTICA[resultado].lower()})"
    return _completar(_avance(practica, reportes))


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


# --- Coordinator scenarios (C1-C7) --------------------------------------------
# These three practices show the states the coordinator acts on. They have
# another academic tutor on purpose, so the tutor screens of PR #56 keep
# showing exactly the same practices.

COORDINADOR = "MENDOZA ARÉVALO CARLOS ANDRÉS"
ANALISTA_DVS = "PACHECO LOORO VERÓNICA ELENA"

TUTOR_CARRERA = "CAÑAR MERCHÁN WASHINGTON EDUARDO"
ENTIDAD_NORTE = "Agroindustrias del Norte Cía. Ltda."


def _pasantia_lista_para_cerrar():
    """C4: everything is ready, so the coordinator can close it (CE-05)."""
    return _practica(
        7,
        "ZAMBRANO ORTIZ ANDREA PAOLA",
        "laboral",
        "en_revision_final",
        [_validado(semana, 20, confirmado_por_entidad=True) for semana in range(1, 9)],
        subtipo="pasantia",
        subtipo_display="Pasantía",
        entidad=ENTIDAD_NORTE,
        tutor_academico=TUTOR_CARRERA,
        tutor_entidad="VIVANCO LEÓN PABLO ESTEBAN",
        plan=_plan(
            "validado",
            ["Desarrollo del módulo de inventario de la empresa."],
            date(2026, 4, 8),
        ),
        informe_final=_informe_final(
            "validado",
            date(2026, 6, 1),
            "informe-final-zambrano.pdf",
            validado_por=TUTOR_CARRERA,
            validado_el=date(2026, 6, 3),
        ),
        informe_externo={
            "registrado_por": "VIVANCO LEÓN PABLO ESTEBAN",
            "registrado_el": date(2026, 6, 2),
            "valoracion": "Cumplió con el plan y presentó el informe de la empresa.",
            "archivo": "informe-entidad-zambrano.pdf",
        },
        evaluacion={
            "porcentaje": 88,
            "resultado": "aprobada",
            "resultado_display": "Aprobada",
            "registrado_por": TUTOR_CARRERA,
            "registrado_el": date(2026, 6, 3),
        },
    )


def _practica_cerrada(practica_id, estudiante, porcentaje, resultado, tipo="laboral"):
    """C6: a closed practice, with the result of its final evaluation (Art. 339)."""
    horas = 160 if tipo == "laboral" else 96
    return _practica(
        practica_id,
        estudiante,
        tipo,
        "cerrada",
        [_validado(semana, horas // 8, confirmado_por_entidad=True) for semana in range(1, 9)],
        subtipo="pasantia" if tipo == "laboral" else "",
        subtipo_display="Pasantía" if tipo == "laboral" else "",
        entidad=ENTIDAD_NORTE if tipo == "laboral" else "GAD Municipal de Catamayo",
        tutor_academico=TUTOR_CARRERA,
        tutor_entidad="VIVANCO LEÓN PABLO ESTEBAN" if tipo == "laboral" else "",
        proyecto_vinculacion=(
            "" if tipo == "laboral" else "Alfabetización digital en el GAD de Catamayo"
        ),
        plan=_plan(
            "validado",
            ["Actividades del plan aprobado por el tutor académico."],
            date(2026, 4, 8),
        ),
        informe_final=_informe_final(
            "validado",
            date(2026, 6, 3),
            f"informe-final-cerrada-{practica_id}.pdf",
            validado_por=TUTOR_CARRERA,
            validado_el=date(2026, 6, 3),
        ),
        informe_externo={
            "registrado_por": "VIVANCO LEÓN PABLO ESTEBAN" if tipo == "laboral" else "PROYECTO DE VINCULACIÓN",
            "registrado_el": date(2026, 6, 3),
            "valoracion": "Cumplimiento satisfactorio del plan de actividades.",
            "archivo": f"informe-externo-cerrada-{practica_id}.pdf",
        },
        evaluacion={
            "porcentaje": porcentaje,
            "resultado": resultado,
            "resultado_display": RESULTADO_PRACTICA[resultado],
            "registrado_por": TUTOR_CARRERA,
            "registrado_el": date(2026, 6, 3),
        },
        resultado=resultado,
        horas_requeridas=horas,
        semana_actual=TOTAL_SEMANAS,
    )


def _pasantia_no_aprobada():
    practica = _pasantia_lista_para_cerrar()
    practica.update(id=10, clave="10", estudiante="SALAZAR VEGA MARÍA JOSÉ")
    practica["evaluacion"].update(porcentaje=64, resultado="no_aprobada", resultado_display="No aprobada")
    return practica


def _practicas():
    """Every sample práctica, rebuilt on each call so a request never leaks state."""
    laboral, comunitaria = _laboral(), _comunitaria()
    for practica_id, practica in ((1, laboral), (2, comunitaria)):
        practica.update(
            id=practica_id, informe_final=None, informe_externo=None, evaluacion=None
        )
    practicas = [
        _completar(laboral),
        _completar(comunitaria),
        _ayudantia_investigacion(),
        _comunitaria_asignada(),
        _pasantia_lista_para_evaluar(),
        _pasantia_con_informe_en_revision(),
        _pasantia_lista_para_cerrar(),
        _practica_cerrada(8, "CORDOVA VAZQUEZ JOSE LUIS", 92, "aprobada"),
        _practica_cerrada(
            9,
            "AYOVI CANDO MARIA FERNANDA",
            64,
            "no_aprobada",
            tipo="comunitaria",
        ),
        _pasantia_no_aprobada(),
    ]
    return practicas


def _dias_habiles(desde, hasta):
    """Business days after `desde` up to `hasta` (the review deadline counts them)."""
    dias = (desde + timedelta(days=n) for n in range(1, (hasta - desde).days + 1))
    return sum(1 for dia in dias if dia.weekday() < 5)


def practicas_del_tutor(tutor=TUTOR_ACADEMICO):
    """T3: practices whose single active academic tutor is `tutor` (S-02)."""
    return [p for p in _practicas() if p["tutor_academico"] == tutor]


def get_practica_del_tutor(practica_id, tutor=TUTOR_ACADEMICO):
    return next((p for p in practicas_del_tutor(tutor) if p["id"] == practica_id), None)


# --- Coordinador (C1-C7) y Analista DVS (A1-A2) ------------------------------
#
# El coordinador solo ve las prácticas de su carrera (RF-11, aislamiento): el
# ejemplo incluye carreras ajenas que no pueden aparecer en sus pantallas.

CARRERA_COORDINADOR = CARRERA
CARRERAS_OTRAS = (
    "FEIRNNR - ELECTRÓNICA - PRESENCIAL - Régimen 2019 - CICLO 4A",
    "FEIRNNR - AGROFORESTAL - PRESENCIAL - Régimen 2019 - CICLO 4A",
)
PERIODO_ANTERIOR = "SEP.25-ENE.26 GRADO"

# RNF-04: el panel del coordinador se mide con 150 prácticas de su carrera.
CANTIDAD_PRACTICAS_CARRERA = 150

# Plazo de reporte: 3 días tras cerrar la semana (clarify, sesión 2026-10-11).
PLAZO_REPORTE_DIAS = 3

CONFIGURACION_CARRERA = {
    "carrera": CARRERA_COORDINADOR,
    "horas_laboral": 160,
    "horas_comunitaria": 96,
    "horas_laboral_distancia": 256,
    "horas_comunitaria_distancia": 144,
    "plazo_reporte_dias": PLAZO_REPORTE_DIAS,
    "plazo_revision_dias": PLAZO_REVISION_DIAS,
    "umbral_rezago": UMBRAL_REZAGO,
}

TIPOS_ALERTA = {
    "reporte_no_enviado": "No reportó en plazo",
    "revision_pendiente": "Revisión vencida",
    "rezago": "Horas rezagadas",
    "incumplimiento": "Incumplimiento reportado",
}

# Color de la insignia de cada tipo de alerta (include estado_badge).
INSIGNIA_ALERTA = {
    "reporte_no_enviado": "fuera_de_plazo",
    "revision_pendiente": "por_confirmar",
    "rezago": "rezagada",
    "incumplimiento": "fuera_de_plazo",
}

_APELLIDOS = (
    "AGUILAR",
    "BENÍTEZ",
    "CÁRDENAS",
    "DÍAZ",
    "ESPINOZA",
    "FRANCO",
    "GARCÍA",
    "HERRERA",
    "JARAMILLO",
    "LOAIZA",
    "MERCHÁN",
    "NARVÁEZ",
    "ORDOÑEZ",
    "PÁEZ",
    "QUISHPE",
)
_APELLIDOS_SEGUNDOS = (
    "ACOSTA",
    "BOADA",
    "CARVAJAL",
    "DOMÍNGUEZ",
    "ESTRELLA",
    "FONSECA",
    "GUZMÁN",
    "HURTADO",
    "IBARRA",
    "JUMBO",
)
_NOMBRES = (
    "ANA LUCÍA",
    "BRAYAN ANDRÉS",
    "CAMILA SOFÍA",
    "DIEGO FERNANDO",
    "ELENA VERÓNICA",
    "FABIO ANDRÉS",
    "GABRIELA ELENA",
    "HUMBERTO JOSÉ",
    "ISABEL MARGARITA",
    "JORGE LUIS",
    "KATHERINE SOFÍA",
    "LENIN ANTONIO",
    "MARCELA BEATRIZ",
    "NELSON IVÁN",
    "OFELIA DEL CARMEN",
)
_TUTORES_CARRERA = (
    TUTOR_CARRERA,
    "CORDOVA PINTO MARIA ELENA",
    "ENRIQUEZ VARGAS JORGE LUIS",
    "LOAIZA TORRES SANDRA VERONICA",
    "ROSALES VILLALTA PEDRO PABLO",
    "SOLIS REYES ANA CECILIA",
)
_ENTIDADES = (
    "Soluciones Informáticas del Sur Cía. Ltda.",
    "Agroindustrias del Norte Cía. Ltda.",
    "Cooperativa de Cafetaleros de Loja",
    "Museo Provincial de Loja",
    "Fundación Provincial de Alfabetización",
)
_TUTORES_ENTIDAD = (
    "ALVARADO GUERRERO NORMAN EDUARDO",
    "CHIMBORAZO LOBO MARITZA SOFIA",
    "TORRES CAÑAVERA HENRY ALBERTO",
)
_PROYECTOS = (
    "Alfabetización digital para adultos mayores del cantón Loja",
    "Sitio web informativo para el GAD parroquial de Vilcabamba",
    "Capacitación en herramientas digitales para productores",
    "Recuperación de áreas verdes en el barrio Lapapaya",
)

# Estados repartidos entre las prácticas de ejemplo, para que los filtros de
# C1 y las alertas tengan contenido de cada estado.
_ESTADOS_SINTETICOS = (
    "en_curso",
    "en_curso",
    "en_revision_final",
    "asignada",
    "suspendida",
    "en_curso",
    "en_revision_final",
    "cancelada",
    "en_curso",
    "cerrada",
)


def _estudiantes(cantidad):
    """Nombres de ejemplo, todos distintos entre sí."""
    return [
        f"{_APELLIDOS[i % len(_APELLIDOS)]} "
        f"{_APELLIDOS_SEGUNDOS[i % len(_APELLIDOS_SEGUNDOS)]} "
        f"{_NOMBRES[(i // len(_APELLIDOS_SEGUNDOS)) % len(_NOMBRES)]}"
        for i in range(cantidad)
    ]


def _componentes(cantidad):
    """(estudiante, tipo) por práctica: los dos componentes del título.

    Los primeros estudiantes tienen práctica laboral y comunitaria, como el
    título que exige la carrera (Art. 334); el resto, un solo componente.
    """
    componentes = []
    indice = 0
    while len(componentes) < cantidad:
        estudiante = _estudiantes(indice + 1)[indice]
        if indice < 54:
            tipos = ("laboral", "comunitaria")
        else:
            tipos = ("laboral",) if indice % 2 == 0 else ("comunitaria",)
        for tipo in tipos:
            if len(componentes) >= cantidad:
                break
            componentes.append((estudiante, tipo))
        indice += 1
    return componentes


def _semana_de(estado, indice):
    if estado in ("cerrada", "en_revision_final"):
        return 8
    if estado == "asignada":
        return 1 + indice % 4
    return 2 + indice % 7


def _reportes_sinteticos(estado, horas_semana, semana_actual, indice):
    """Reportes semanales de una práctica de ejemplo, según su estado."""
    if estado == "asignada":
        return []
    if estado == "cerrada":
        return [
            _validado(semana, horas_semana, confirmado_por_entidad=True)
            for semana in range(1, 9)
        ]
    ultima_sin_reporte = (
        estado in ("en_curso", "suspendida", "cancelada") and indice % 3 == 0
    )
    ultima_en_revision = estado in ("en_curso", "en_revision_final") and indice % 3 == 1
    reportes = []
    for semana in range(1, semana_actual + 1):
        if semana == semana_actual:
            if ultima_sin_reporte:
                reportes.append(_reporte(semana, 0, "sin_reporte"))
                continue
            if ultima_en_revision:
                reportes.append(_reporte(semana, horas_semana, "en_revision"))
                continue
        reportes.append(_validado(semana, horas_semana, confirmado_por_entidad=True))
    return reportes


def _practica_sintetica(indice, estudiante, tipo, carrera, periodo, id_base):
    """Una práctica de ejemplo, con los datos que la lista de C1 muestra."""
    estado = _ESTADOS_SINTETICOS[indice % len(_ESTADOS_SINTETICOS)]
    clave_horas = "horas_laboral" if tipo == "laboral" else "horas_comunitaria"
    horas_requeridas = CONFIGURACION_CARRERA[clave_horas]
    horas_semana = horas_requeridas // (8 if estado in ("cerrada", "en_revision_final") else TOTAL_SEMANAS)
    semana_actual = _semana_de(estado, indice)
    reportes = _reportes_sinteticos(estado, horas_semana, semana_actual, indice)
    datos = {
        "carrera": carrera,
        "periodo": periodo,
        "tutor_academico": _TUTORES_CARRERA[indice % len(_TUTORES_CARRERA)],
        "semana_actual": semana_actual,
        "horas_requeridas": horas_requeridas,
        "subtipo": "pasantia" if tipo == "laboral" else "",
        "subtipo_display": "Pasantía" if tipo == "laboral" else "",
        "entidad": _ENTIDADES[indice % len(_ENTIDADES)] if tipo == "laboral" else "",
        "tutor_entidad": (
            _TUTORES_ENTIDAD[indice % len(_TUTORES_ENTIDAD)] if tipo == "laboral" else ""
        ),
        "proyecto_vinculacion": (
            "" if tipo == "laboral" else _PROYECTOS[indice % len(_PROYECTOS)]
        ),
        "plan": _plan(
            "en_revision" if estado == "asignada" else "validado",
            [f"Actividad {n} del plan de {tipo}." for n in range(1, 4)],
            date(2026, 4, 9),
        ),
    }
    if estado == "en_revision_final":
        datos["informe_final"] = _informe_final(
            "validado",
            date(2026, 6, 1),
            f"informe-final-{id_base + indice}.pdf",
            validado_por=datos["tutor_academico"],
            validado_el=date(2026, 6, 3),
        )
        if tipo == "laboral":
            datos["informe_externo"] = {
                "registrado_por": datos["tutor_entidad"],
                "registrado_el": date(2026, 6, 2),
                "valoracion": "Cumplió las actividades del plan de la práctica.",
                "archivo": f"informe-entidad-{id_base + indice}.pdf",
            }
    if estado == "cerrada":
        datos["informe_final"] = _informe_final(
            "validado",
            date(2026, 6, 3),
            f"informe-final-{id_base + indice}.pdf",
            validado_por=datos["tutor_academico"],
            validado_el=date(2026, 6, 3),
        )
        datos["informe_externo"] = {
            "registrado_por": datos["tutor_entidad"] or "PROYECTO DE VINCULACIÓN",
            "registrado_el": date(2026, 6, 3),
            "valoracion": "Cumplimiento satisfactorio del plan de actividades.",
            "archivo": f"informe-externo-{id_base + indice}.pdf",
        }
        resultado = "no_aprobada" if indice % 4 == 3 else "aprobada"
        datos["evaluacion"] = {
            "porcentaje": 64 if resultado == "no_aprobada" else 88,
            "resultado": resultado,
            "resultado_display": RESULTADO_PRACTICA[resultado],
            "registrado_por": datos["tutor_academico"],
            "registrado_el": date(2026, 6, 3),
        }
        datos["resultado"] = resultado
    return _practica(id_base + indice, estudiante, tipo, estado, reportes, **datos)


def _practicas_sinteticas(carrera, periodo, componentes, id_base):
    return [
        _practica_sintetica(indice, estudiante, tipo, carrera, periodo, id_base)
        for indice, (estudiante, tipo) in enumerate(componentes)
    ]


def _documentos_en_revision(practica):
    """Documentos de la práctica que esperan revisión, con su etiqueta."""
    documentos = []
    plan = practica.get("plan") or {}
    if plan.get("estado") == "en_revision":
        documentos.append(("Plan de actividades", plan))
    for reporte in practica["reportes"]:
        if reporte["estado"] == "en_revision":
            documentos.append((f"Semana {reporte['semana']}", reporte))
    informe = practica.get("informe_final")
    if informe and informe["estado"] == "en_revision":
        documentos.append(("Informe final", informe))
    return documentos


def sumar_dias_habiles(desde, cantidad):
    while cantidad:
        desde += timedelta(days=1)
        if desde.weekday() < 5:
            cantidad -= 1
    return desde


def alertas_de(practica, configuracion=None):
    """Alertas activas de una práctica (RF-07, CU-03)."""
    if practica["estado"] in ESTADOS_SOLO_LECTURA:
        return []
    configuracion = configuracion or CONFIGURACION_CARRERA
    plazo_reporte = configuracion["plazo_reporte_dias"]
    plazo_revision = configuracion["plazo_revision_dias"]
    alertas = []

    def _alerta(tipo, detalle, fecha):
        return {
            "tipo": tipo,
            "tipo_display": TIPOS_ALERTA[tipo],
            "estado_badge": INSIGNIA_ALERTA[tipo],
            "detalle": detalle,
            "fecha": fecha,
            "practica": practica,
        }

    for reporte in practica["reportes"]:
        if reporte["estado"] != "sin_reporte":
            continue
        fecha = reporte["hasta"] + timedelta(days=plazo_reporte)
        if HOY > fecha:
            alertas.append(
                _alerta(
                    "reporte_no_enviado",
                    f"La semana {reporte['semana']} se cerró sin reporte.",
                    fecha,
                )
            )
    for etiqueta, documento in _documentos_en_revision(practica):
        dias = _dias_habiles(documento["enviado_el"], HOY)
        if dias > plazo_revision:
            alertas.append(
                _alerta(
                    "revision_pendiente",
                    f"{etiqueta}: {dias} días hábiles de espera "
                    f"(el plazo es de {plazo_revision}).",
                    sumar_dias_habiles(documento["enviado_el"], plazo_revision),
                )
            )
    if practica["estado"] in ESTADOS_ACTIVOS and practica["rezagada"]:
        alertas.append(
            _alerta(
                "rezago",
                f"{practica['horas_validadas'] + practica['horas_en_revision']} h de las "
                f"{practica['horas_minimas']} h mínimas del {practica['umbral_rezago']} %.",
                HOY,
            )
        )
    for incumplimiento in practica.get("incumplimientos", []):
        alertas.append(
            _alerta(
                "incumplimiento",
                incumplimiento["descripcion"],
                incumplimiento["reportado_el"],
            )
        )
    return alertas


def _con_alertas(practicas):
    for practica in practicas:
        practica["alertas"] = alertas_de(practica)
    return practicas


def practicas_de_la_carrera(carrera=CARRERA_COORDINADOR):
    """C1: todas las prácticas de la carrera del coordinador (RF-11)."""
    propias = [p for p in _practicas() if p["carrera"] == carrera]
    faltan = CANTIDAD_PRACTICAS_CARRERA - len(propias)
    componentes = _componentes(faltan)
    return _con_alertas(propias + _practicas_sinteticas(carrera, PERIODO, componentes, 100))


def practicas_de_otras_carreras():
    """Prácticas de carreras ajenas: el coordinador no puede verlas (RF-11)."""
    practicas = []
    id_base = 1000
    for indice, carrera in enumerate(CARRERAS_OTRAS):
        periodo = PERIODO if indice == 0 else PERIODO_ANTERIOR
        componentes = _componentes(20)
        practicas += _practicas_sinteticas(carrera, periodo, componentes, id_base)
        id_base += 20
    return _con_alertas(practicas)


def practicas_todas():
    """Todas las prácticas de ejemplo, de todas las carreras (A1)."""
    return practicas_de_la_carrera() + practicas_de_otras_carreras()


def get_practica_de_la_carrera(practica_id, carrera=CARRERA_COORDINADOR):
    return next(
        (p for p in practicas_de_la_carrera(carrera) if p["id"] == practica_id), None
    )


def alertas_de_la_carrera(carrera=CARRERA_COORDINADOR):
    """C2: las alertas de la carrera del coordinador, de la más reciente a la más vieja."""
    alertas = [
        alerta for p in practicas_de_la_carrera(carrera) for alerta in p["alertas"]
    ]
    return sorted(
        alertas, key=lambda alerta: (alerta["fecha"], alerta["practica"]["id"]), reverse=True
    )


def alertas_todas():
    """A1: las alertas de todas las carreras."""
    alertas = [alerta for p in practicas_todas() for alerta in p["alertas"]]
    return sorted(
        alertas, key=lambda alerta: (alerta["fecha"], alerta["practica"]["id"]), reverse=True
    )


def requisitos_cierre(practica):
    """Los requisitos de RF-09/COR-02 y si cada uno se cumple."""
    informe = practica.get("informe_final")
    externo = practica.get("informe_externo")
    evaluacion = practica.get("evaluacion")
    es_laboral = practica["tipo"] == "laboral"
    return [
        {
            "clave": "horas",
            "requisito": "El 100 % de las horas requeridas validadas",
            "cumplido": practica["horas_validadas"] >= practica["horas_requeridas"],
            "detalle": (
                f"{practica['horas_validadas']} h validadas de "
                f"{practica['horas_requeridas']} h requeridas"
            ),
        },
        {
            "clave": "informe_final",
            "requisito": "El informe final del estudiante revisado",
            "cumplido": bool(informe) and informe["estado"] == "validado",
            "detalle": (
                f"{informe['archivo']}, revisado el "
                f"{informe['validado_el'].strftime('%d/%m/%Y')}"
                if informe and informe["estado"] == "validado"
                else "sin informe final revisado"
            ),
        },
        {
            "clave": "informe_externo",
            "requisito": (
                "El informe externo del tutor de la entidad"
                if es_laboral
                else "El informe del proyecto de vinculación"
            ),
            "cumplido": bool(externo),
            "detalle": (
                f"registrado por {externo['registrado_por']} el "
                f"{externo['registrado_el'].strftime('%d/%m/%Y')}"
                if externo
                else "sin informe externo registrado"
            ),
            "nota": (
                ""
                if es_laboral
                else "El actor que registra este informe está por definir (spec, sección 6)."
            ),
        },
        {
            "clave": "evaluacion",
            "requisito": "La evaluación final registrada",
            "cumplido": bool(evaluacion),
            "detalle": (
                f"{evaluacion['porcentaje']} % — {evaluacion['resultado_display']}"
                if evaluacion
                else "sin evaluación final registrada"
            ),
        },
    ]


def faltantes_cierre(practica):
    """Lo que le falta a la práctica para poder cerrarse (CE-05)."""
    return [r["requisito"] for r in requisitos_cierre(practica) if not r["cumplido"]]


def fecha_cierre(practica):
    """Fecha del último cambio de estado a «cerrada», si la práctica se cerró."""
    for entrada in reversed(practica.get("historial", [])):
        if entrada["estado_nuevo"] == "cerrada":
            return entrada["fecha"]
    return None


def _fila_consolidado(practica):
    return {
        "estudiante": practica["estudiante"],
        "carrera": practica["carrera"],
        "periodo": practica["periodo"],
        "componente": "Laboral" if practica["tipo"] == "laboral" else "Comunitaria",
        "tipo": practica["tipo"],
        "horas_requeridas": practica["horas_requeridas"],
        "horas_validadas": practica["horas_validadas"],
        "horas_en_revision": practica["horas_en_revision"],
        "porcentaje": practica["pct_validadas"],
        "estado": practica["estado"],
        "estado_display": practica["estado_display"],
        "resultado": practica.get("resultado", ""),
        "resultado_display": practica.get("resultado_display", ""),
        "fecha_cierre": fecha_cierre(practica),
    }


def _filtrar_consolidado(filas, periodo, componente):
    if periodo:
        filas = [f for f in filas if f["periodo"] == periodo]
    if componente:
        filas = [f for f in filas if f["tipo"] == componente]
    return sorted(filas, key=lambda f: (f["estudiante"], f["tipo"]))


def consolidado_de_la_carrera(carrera=CARRERA_COORDINADOR, periodo=None, componente=None):
    """C6: horas y resultado por estudiante y componente (HU-13)."""
    filas = [_fila_consolidado(p) for p in practicas_de_la_carrera(carrera) if p["estado"] == "cerrada"]
    return _filtrar_consolidado(filas, periodo, componente)


def consolidado_general(periodo=None, componente=None):
    """A1: el mismo consolidado, entre carreras."""
    filas = [_fila_consolidado(p) for p in practicas_todas() if p["estado"] == "cerrada"]
    return _filtrar_consolidado(filas, periodo, componente)


def filtrar_practicas(
    practicas, periodo=None, tipo=None, estado=None, alerta=None, busqueda=None
):
    """Filtros de C1: período, tipo, estado, alerta y búsqueda por estudiante."""
    if periodo:
        practicas = [p for p in practicas if p["periodo"] == periodo]
    if tipo:
        practicas = [p for p in practicas if p["tipo"] == tipo]
    if estado:
        practicas = [p for p in practicas if p["estado"] == estado]
    if alerta:
        practicas = [p for p in practicas if any(a["tipo"] == alerta for a in p["alertas"])]
    if busqueda:
        texto = busqueda.strip().upper()
        practicas = [p for p in practicas if texto in p["estudiante"].upper()]
    return practicas


def periodos_de(practicas):
    """Períodos presentes en las prácticas, para los desplegables de filtro."""
    return sorted({p["periodo"] for p in practicas}, reverse=True)


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


def practicas_de_la_entidad(tutor=TUTOR_ENTIDAD):
    """R1: the tutor's interns. Only a práctica laboral has one (Art. 337, COR-03)."""
    return [
        p for p in _practicas() if p["tipo"] == "laboral" and p["tutor_entidad"] == tutor
    ]


def get_practica_de_la_entidad(practica_id, tutor=TUTOR_ENTIDAD):
    return next(
        (p for p in practicas_de_la_entidad(tutor) if p["id"] == practica_id), None
    )


def reportes_por_confirmar(tutor=TUTOR_ENTIDAD):
    """R2: sent weekly reports of the tutor's interns that are not confirmed yet."""
    return [
        {"practica": p, "reporte": r}
        for p in practicas_de_la_entidad(tutor)
        for r in p["reportes"]
        if r["estado"] != "sin_reporte" and not r["confirmado_por_entidad"]
    ]


def get_reporte_de_practicante(practica_id, semana, tutor=TUTOR_ENTIDAD):
    """R3: (práctica, reporte) only for the tutor's own interns (HU-07 case 3)."""
    practica = get_practica_de_la_entidad(practica_id, tutor)
    if practica is None:
        return None
    reporte = next(
        (
            r
            for r in practica["reportes"]
            if r["semana"] == semana and r["estado"] != "sin_reporte"
        ),
        None,
    )
    return (practica, reporte) if reporte else None
