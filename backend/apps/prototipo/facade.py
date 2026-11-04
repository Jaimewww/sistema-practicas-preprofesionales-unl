"""Public use cases for synthetic practice queries, not production RBAC.

Weekly reports sent through `registrar_reporte` are not stored here: the caller
keeps the returned `envios` (the prototype uses the sender's session) and passes
them back, so every request rebuilds the sample data plus that overlay.
"""

from copy import deepcopy

from . import sample_data as data
from .dto import (
    to_alerta_dto,
    to_anexo_dto,
    to_historial_dto,
    to_practica_dto,
    to_reporte_dto,
)
from .forms import ReporteSemanalForm
from .sample_data import (
    CARRERA,
    ESTADO_REPORTE,
    HOY,
    TUTOR_ACADEMICO,
    TUTOR_ENTIDAD,
    USUARIO,
    _avance,
    _fechas,
)

ROLES = ("estudiante", "tutor_academico", "tutor_entidad", "coordinador")
# Actores incorporados en el #62: solo para las acciones aprobadas (RF-11).
ROLES_HISTORIAL = ("director", "coordinador")
ROLES_LEGALIZACION = ("secretaria",)
# Personas de demostración conocidas por los endpoints nuevos (#62).
ROLES_DEMO = ROLES + tuple(
    rol for rol in ROLES_HISTORIAL + ROLES_LEGALIZACION if rol not in ROLES
)
SESSION_KEY = "prototipo_reportes"
ID_POR_CLAVE = {"laboral": 1, "comunitaria": 2}
YA_ENVIADO = {"en_revision": "ya tiene un reporte en revisión", "validado": "ya está validada"}


class PracticeQueryError(Exception):
    def __init__(self, status, code, message, form=None, **extra):
        super().__init__(message)
        self.status, self.code, self.form, self.extra = status, code, form, extra


def _visible(practica, rol):
    if rol == "estudiante":
        return practica["estudiante"] == USUARIO["nombre"]
    if rol == "tutor_academico":
        return practica["tutor_academico"] == TUTOR_ACADEMICO
    if rol == "tutor_entidad":
        return practica["tipo"] == "laboral" and practica["tutor_entidad"] == TUTOR_ENTIDAD
    return rol == "coordinador" and practica["carrera"] == CARRERA


def _version(reporte):
    """The report as it was before a resend; nested versions stay on the new one."""
    return {key: value for key, value in reporte.items() if key != "versiones"}


def _aplicar(practica, envio):
    reportes = practica["reportes"]
    semana = envio["semana"]
    anterior = next((r for r in reportes if r["semana"] == semana), None)
    versiones = list(anterior.get("versiones", [])) if anterior else []
    if anterior and anterior["estado"] != "sin_reporte":
        versiones.append(_version(anterior))
    desde, hasta = _fechas(semana)
    nuevo = {
        "semana": semana,
        "desde": desde,
        "hasta": hasta,
        "horas": envio["horas"],
        "estado": "en_revision",
        "estado_display": ESTADO_REPORTE["en_revision"],
        "observacion": "",
        "validado_por": "",
        "validado_el": None,
        "confirmado_por_entidad": False if practica["tipo"] == "laboral" else None,
        "enviado_el": HOY,
        "actividades": envio["actividades"],
        "evidencias": envio["evidencias"],
        "versiones": versiones,
    }
    if anterior:
        reportes[reportes.index(anterior)] = nuevo
    else:
        reportes.append(nuevo)
        reportes.sort(key=lambda r: r["semana"])
    return nuevo


def _con_envios(practica, envios):
    """`practica` with the reports of this session applied in their order."""
    for envio in (envios or {}).get(str(practica["id"]), []):
        _aplicar(practica, envio)
    return _avance(practica, practica["reportes"])


def _todas(envios=None, estado=None, decisiones=None):
    # Imported here because validaciones translates errors using this facade.
    from . import coordinador, validaciones

    practicas = data.practicas_todas()
    for practica in practicas:
        validaciones.aplicar_practica(practica, decisiones or {})
        _con_envios(practica, envios)
    return coordinador.aplicar_estado(practicas, estado or {})


def _buscar(practica_id, rol, envios=None, estado=None, decisiones=None):
    practica = next((p for p in _todas(envios, estado, decisiones) if p["id"] == practica_id), None)
    if practica is None:
        raise PracticeQueryError(404, "recurso_inexistente", "No existe la práctica.")
    if not _visible(practica, rol):
        raise PracticeQueryError(403, "fuera_de_rol", "La práctica no corresponde a tu rol.")
    return practica


def practicas_para_pantalla(rol, envios=None, estado=None, decisiones=None):
    """Rebuilt practices for the existing templates, scoped by the same API policy."""
    return [p for p in _todas(envios, estado, decisiones) if _visible(p, rol)]


def practicas_de(rol, envios=None, estado=None, decisiones=None):
    return [to_practica_dto(p, resumido=True) for p in practicas_para_pantalla(rol, envios, estado, decisiones)]


def practica_de_id(practica_id, rol, envios=None, estado=None, decisiones=None):
    return to_practica_dto(_buscar(practica_id, rol, envios, estado, decisiones))


def practica_para_pantalla(practica_id, rol, envios=None, estado=None, decisiones=None):
    return _buscar(practica_id, rol, envios, estado, decisiones)


def alertas_de(rol, tipo="", envios=None, estado=None, decisiones=None):
    destinatarios = {
        "estudiante": {"reporte_no_enviado", "rezago"},
        "tutor_academico": set(data.TIPOS_ALERTA),
        "coordinador": set(data.TIPOS_ALERTA),
        "tutor_entidad": set(),
    }
    alertas = [a for p in practicas_para_pantalla(rol, envios, estado, decisiones)
               for a in p["alertas"] if a["tipo"] in destinatarios.get(rol, set())]
    alertas.sort(key=lambda a: (a["fecha"], a["practica"]["id"]), reverse=True)
    return {"count": len(alertas), "alertas": [to_alerta_dto(a, rol) for a in alertas if not tipo or a["tipo"] == tipo]}


def cerrar_practica(practica_id, rol, envios=None, estado=None, decisiones=None):
    """RF-09: return the closed DTO and a new state; rejection has no side effects."""
    from . import coordinador

    if rol != "coordinador":
        raise PracticeQueryError(403, "fuera_de_rol", "Solo el coordinador puede cerrar la práctica.")
    practica = _buscar(practica_id, rol, envios, estado, decisiones)
    origenes, destino, _ = coordinador.TRANSICIONES["cerrar"]
    faltante = data.faltantes_cierre(practica)
    if practica["estado"] not in origenes or faltante:
        message = "No se puede cerrar: falta " + "; ".join(faltante) + "." if faltante else "La práctica no permite el cierre en su estado actual."
        raise PracticeQueryError(409, "transicion_invalida", message, faltante=faltante)
    nuevo = deepcopy(estado or {"cambios": {}, "configuracion": {}})
    coordinador.registrar_cambio(nuevo, practica, destino, "Cierre con el resultado de la evaluación final.")
    cerrada = _buscar(practica_id, rol, envios, nuevo, decisiones)
    return to_practica_dto(cerrada), nuevo


def historial_de(practica_id, rol, envios=None, estado=None, decisiones=None):
    """RF-10: read-only state changes of a practice of this career (RF-11).

    The coordinator keeps the career-wide access of #61; the director reads the
    history of the same career and nothing else.
    """
    if rol not in ROLES_HISTORIAL:
        raise PracticeQueryError(
            403, "fuera_de_rol", "Solo el coordinador y el director consultan el historial."
        )
    practica = next((p for p in _todas(envios, estado, decisiones) if p["id"] == practica_id), None)
    if practica is None:
        raise PracticeQueryError(404, "recurso_inexistente", "No existe la práctica.")
    if practica["carrera"] != CARRERA:
        raise PracticeQueryError(403, "fuera_de_rol", "La práctica no corresponde a tu carrera.")
    return [to_historial_dto(entrada) for entrada in practica["historial"]]


def legalizar_anexo(anexo_id, rol, estado=None):
    """RF-04: the secretary legalizes one annex; author and date are derived.

    Returns the anexo DTO and a new state. A rejection (foreign career, already
    legalized) leaves the state untouched and never mutates the sample data.
    """
    from . import secretaria

    if rol not in ROLES_LEGALIZACION:
        raise PracticeQueryError(403, "fuera_de_rol", "Solo la Secretaría legaliza anexos.")
    nuevo = deepcopy(estado or {"legalizaciones": {}})
    practicas = secretaria.aplicar_legalizaciones(data.practicas_todas(), nuevo)
    encontrado = next(
        ((anexo, practica) for practica in practicas for anexo in practica.get("anexos", [])
         if anexo["id"] == anexo_id),
        None,
    )
    if encontrado is None:
        raise PracticeQueryError(404, "recurso_inexistente", "No existe el anexo.")
    anexo, practica = encontrado
    if practica["carrera"] != CARRERA:
        raise PracticeQueryError(403, "fuera_de_rol", "El anexo no corresponde a tu carrera.")
    if anexo["estado"] == "legalizado":
        raise PracticeQueryError(409, "transicion_invalida", "El anexo ya fue legalizado.")
    secretaria.legalizar_anexo(nuevo, anexo_id, data.SECRETARIA)
    secretaria.aplicar_legalizaciones([practica], nuevo)
    return to_anexo_dto(anexo), nuevo


def practicas_para_director(envios=None, estado=None, decisiones=None):
    """D1: closed practices of the director's career, with this browser's state."""
    return [p for p in _todas(envios, estado, decisiones)
            if p["carrera"] == CARRERA and p["estado"] == "cerrada"]


def practica_para_director(practica_id, envios=None, estado=None, decisiones=None):
    """D2: one closed practice of the director's career (404 for anything else)."""
    for practica in practicas_para_director(envios, estado, decisiones):
        if practica["id"] == practica_id:
            return practica
    raise PracticeQueryError(404, "recurso_inexistente", "No existe la práctica cerrada.")


def practica_del_estudiante(clave, envios=None, estado=None, decisiones=None):
    """Sample práctica of the E2/E4 screens ("laboral" by default) with the overlay."""
    return _buscar(ID_POR_CLAVE.get(clave, 1), "estudiante", envios, estado, decisiones)


def semanas_para_reportar(practica):
    """Weeks the student may send: returned ones first, then the pending ones."""
    por_semana = {r["semana"]: r for r in practica["reportes"]}
    devueltas = [r["semana"] for r in practica["reportes"] if r["estado"] == "devuelto"]
    pendientes = [
        int(valor)
        for valor, _ in practica["semanas_para_reportar"]
        if por_semana.get(int(valor), {}).get("estado", "sin_reporte") == "sin_reporte"
    ]
    opciones = []
    for semana in devueltas + pendientes:
        desde, hasta = _fechas(semana)
        etiqueta = f"Semana {semana} ({desde:%d/%m/%Y} - {hasta:%d/%m/%Y})"
        if semana in devueltas:
            etiqueta += ", devuelta"
        opciones.append((str(semana), etiqueta))
    return opciones


def formulario_reporte(practica, data=None, files=None):
    return ReporteSemanalForm(
        data,
        files,
        es_ayudantia=practica["es_ayudantia"],
        semanas=semanas_para_reportar(practica),
    )


def _semana_enviada(practica, valor):
    try:
        semana = int(valor)
    except (TypeError, ValueError):
        return None
    reporte = next((r for r in practica["reportes"] if r["semana"] == semana), None)
    if reporte and reporte["estado"] in YA_ENVIADO:
        return f"La semana {semana} {YA_ENVIADO[reporte['estado']]}."
    return None


def registrar_reporte(practica_id, rol, data, files, envios=None, estado=None, decisiones=None):
    """Validate a weekly report (RF-03, RF-15, RNF-05) and return (dto, envios).

    A rejection raises PracticeQueryError and leaves `envios` untouched.
    """
    if rol != "estudiante":
        raise PracticeQueryError(
            403, "fuera_de_rol", "Solo el estudiante envía reportes semanales."
        )
    practica = _buscar(practica_id, rol, envios, estado, decisiones)
    if practica["estado"] != "en_curso":
        raise PracticeQueryError(409, "transicion_invalida", "La práctica no admite nuevos reportes en su estado actual.")
    if (practica.get("plan") or {}).get("estado") != "validado":
        raise PracticeQueryError(
            409, "transicion_invalida", "La práctica no tiene un plan de actividades aprobado."
        )
    form = formulario_reporte(practica, data, files)
    conflicto = _semana_enviada(practica, data.get("semana"))
    if conflicto:
        form.is_valid()
        form.add_error(None, conflicto)
        raise PracticeQueryError(409, "transicion_invalida", conflicto, form=form)
    if not form.is_valid():
        campos = {name: [str(e) for e in errors] for name, errors in form.errors.items()}
        raise PracticeQueryError(
            422,
            "dato_invalido",
            "El reporte no cumple las reglas; revise los campos.",
            form=form,
            campos=campos,
        )
    envio = {
        "semana": int(form.cleaned_data["semana"]),
        "horas": form.cleaned_data["horas"],
        "actividades": [
            line.strip() for line in form.cleaned_data["actividades"].splitlines() if line.strip()
        ],
        "evidencias": [file.name for file in form.cleaned_data["evidencias"]],
    }
    nuevos = {key: list(value) for key, value in (envios or {}).items()}
    nuevos.setdefault(str(practica_id), []).append(envio)
    reporte = _aplicar(practica, envio)
    return to_reporte_dto(reporte), nuevos
