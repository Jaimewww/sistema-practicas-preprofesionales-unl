"""Prototype state for tutor decisions (approve/return), isolated per browser.

No database or production permissions. Decisions are kept in a signed, expiring
cookie shared by the API and screen T2. The shared sample data is never mutated:
each lookup rebuilds it and the overlay is applied on top. Nothing is deleted
(RF-10); a decision only moves a document out of "en_revision".
"""
import json

from django.core import signing
from django.core.serializers.json import DjangoJSONEncoder

from . import sample_data as data
from .dto import DOCUMENT_FIELDS, REPORT_FIELDS
from .facade import PracticeQueryError

COOKIE = "prototipo_validaciones"
SALT = "prototipo.validaciones.v1"
LIMITE_COOKIE = 3500
LIMITE_OBSERVACION = 500
DECISIONES = {"aprobado": "validado", "devuelto": "devuelto"}


def leer_estado(request):
    try:
        return signing.loads(request.COOKIES.get(COOKIE, ""), salt=SALT, max_age=86400)
    except signing.BadSignature:
        return {"decisiones": {}}


def guardar_estado(request, response, estado):
    """Set the cookie; False (and no cookie) when the demo outgrew its limit."""
    value = signing.dumps(estado, salt=SALT, compress=True)
    if len(value) > LIMITE_COOKIE:
        return False
    response.set_cookie(COOKIE, value, max_age=86400, path="/",
                        httponly=True, samesite="Lax", secure=request.is_secure())
    return True


def _documentos():
    """Every plan, sent report and final report of every práctica, whatever its state."""
    for practica in data._practicas():
        plan = practica.get("plan")
        if plan:
            yield "plan", f"plan-{practica['id']}", "Plan de actividades", practica, plan
        for reporte in practica["reportes"]:
            if reporte["estado"] != "sin_reporte":
                clave = f"reporte-{practica['id']}-{reporte['semana']}"
                yield "reporte", clave, f"Semana {reporte['semana']}", practica, reporte
        informe = practica.get("informe_final")
        if informe:
            yield "informe", f"informe-{practica['id']}", "Informe final", practica, informe


def localizar(clave, estado):
    """Find a document among all of them (404), of this tutor (403), still open (409)."""
    encontrado = next((d for d in _documentos() if d[1] == clave), None)
    if encontrado is None:
        raise PracticeQueryError(404, "recurso_inexistente", "No existe el documento.")
    tipo, clave, titulo, practica, documento = encontrado
    if practica["tutor_academico"] != data.TUTOR_ACADEMICO:
        raise PracticeQueryError(403, "fuera_de_rol", "El documento no corresponde a tu rol.")
    if documento["estado"] != "en_revision" or clave in estado.get("decisiones", {}):
        raise PracticeQueryError(409, "transicion_invalida", "El documento ya fue revisado.")
    return data._pendiente(tipo, clave, titulo, practica, documento)


def leer_cuerpo(raw):
    try:
        datos = json.loads(raw)
    except ValueError:
        datos = None
    if not isinstance(datos, dict):
        raise PracticeQueryError(400, "solicitud_malformada", "El cuerpo debe ser un objeto JSON.")
    return datos


def _decision_valida(datos):
    """Return (estado, observacion) or raise 422; the rule of RF-03 lives here."""
    decision = datos.get("decision")
    if not isinstance(decision, str) or decision not in DECISIONES:
        raise PracticeQueryError(422, "dato_invalido", "decision debe ser aprobado o devuelto.")
    if decision == "aprobado":
        return DECISIONES[decision], ""
    observacion = datos.get("observacion")
    if not isinstance(observacion, str) or not observacion.strip():
        raise PracticeQueryError(422, "dato_invalido", "Devolver exige una observación.")
    if len(observacion) > LIMITE_OBSERVACION:
        raise PracticeQueryError(
            422, "dato_invalido", f"La observación admite hasta {LIMITE_OBSERVACION} caracteres."
        )
    return DECISIONES[decision], observacion.strip()


def aplicar(pendiente, estado):
    """Overlay a stored decision on a rebuilt pendiente (who and when are derived)."""
    decision = estado.get("decisiones", {}).get(pendiente["clave"])
    if decision:
        nuevo = decision["estado"]
        pendiente["documento"].update(
            estado=nuevo,
            estado_display=data.ESTADO_REPORTE[nuevo],
            validado_por=data.TUTOR_ACADEMICO,
            validado_el=data.HOY,
            observacion=decision["observacion"],
        )
        pendiente.update(estado=nuevo, estado_display=data.ESTADO_REPORTE[nuevo])
    return pendiente


def registrar(pendiente, estado, datos):
    nuevo, observacion = _decision_valida(datos)
    estado.setdefault("decisiones", {})[pendiente["clave"]] = {
        "estado": nuevo, "observacion": observacion,
    }
    return aplicar(pendiente, estado)


def decidir(clave, estado, datos):
    """Locate and decide in one step (used by screen T2)."""
    return registrar(localizar(clave, estado), estado, datos)


def to_pendiente_dto(pendiente):
    documento = pendiente["documento"]
    campos = REPORT_FIELDS if pendiente["tipo"] == "reporte" else DOCUMENT_FIELDS
    dto = {
        "clave": pendiente["clave"],
        "tipo": pendiente["tipo"],
        "titulo": pendiente["titulo"],
        "practica_id": pendiente["practica"]["id"],
    }
    dto.update({key: documento[key] for key in campos if key in documento})
    return dto


def a_json(payload):
    return json.dumps(payload, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)
