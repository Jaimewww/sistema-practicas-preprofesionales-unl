"""Public use cases for synthetic practice queries, not production RBAC."""

from .dto import to_practica_dto
from .sample_data import CARRERA, TUTOR_ACADEMICO, TUTOR_ENTIDAD, USUARIO, _practicas

ROLES = ("estudiante", "tutor_academico", "tutor_entidad", "coordinador")


class PracticeQueryError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code = status, code


def _visible(practica, rol):
    if rol == "estudiante":
        return practica["estudiante"] == USUARIO["nombre"]
    if rol == "tutor_academico":
        return practica["tutor_academico"] == TUTOR_ACADEMICO
    if rol == "tutor_entidad":
        return practica["tipo"] == "laboral" and practica["tutor_entidad"] == TUTOR_ENTIDAD
    return rol == "coordinador" and practica["carrera"] == CARRERA


def practicas_de(rol):
    return [to_practica_dto(p, resumido=True) for p in _practicas() if _visible(p, rol)]


def practica_de_id(practica_id, rol):
    practica = next((p for p in _practicas() if p["id"] == practica_id), None)
    if practica is None:
        raise PracticeQueryError(404, "recurso_inexistente", "No existe la práctica.")
    if not _visible(practica, rol):
        raise PracticeQueryError(403, "fuera_de_rol", "La práctica no corresponde a tu rol.")
    return to_practica_dto(practica)
