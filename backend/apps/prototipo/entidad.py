"""Catálogo consultivo de entidades receptoras y convenios (N1-N2, issue #55).

N1 y N2 son pantallas nuevas que el mapa de pantallas no define (§3.6): solo
consulta, sin edición ni firma. La entidad sigue al `EntidadReceptora` del
data-model, que **solo exige `nombre`** y es **opcional** en la práctica
comunitaria; el instrumento y la vigencia son datos de ejemplo, no campos del
MVP. Toda institución, documento y persona es inventada.
"""
from datetime import date

from . import sample_data as data

HOY = data.HOY

# Rectorado y Decanato aprueban y revisan convenios (README §3; Art. 342).
USUARIO = "SALINAS ORDÓÑEZ RODRIGO XAVIER"

INSTRUMENTOS = {
    "convenio": "Convenio",
    "carta": "Carta de compromiso",
}

ESTADO_APROBACION = {
    "aprobado": "Aprobado",
    "pendiente": "Pendiente de aprobación",
}

# Una práctica sigue vigente mientras no se haya cerrado ni cancelado.
ESTADOS_VIGENTES = ("asignada", "en_curso", "en_revision_final", "suspendida")

# Las entidades reutilizan los nombres de sample_data; los ids siguen el orden
# de esta tabla (N1 y N2 comparten la misma lista).
_ENTIDADES = (
    {
        "id": 1,
        "nombre": "Universidad Nacional de Loja - Carrera de Computación",
        "instrumento": "convenio",
        "referencia": "CONV-2025-014",
        "vigencia_desde": date(2025, 1, 15),
        "vigencia_hasta": date(2027, 12, 31),
        "estado_aprobacion": "aprobado",
    },
    {
        "id": 2,
        "nombre": "Junta Parroquial de San Lucas",
        "instrumento": "carta",
        "referencia": "CC-2026-003",
        "vigencia_desde": date(2026, 1, 12),
        "vigencia_hasta": date(2026, 12, 31),
        "estado_aprobacion": "aprobado",
    },
    {
        "id": 3,
        "nombre": "Soluciones Informáticas del Sur Cía. Ltda.",
        "instrumento": "convenio",
        "referencia": "CONV-2026-002",
        "vigencia_desde": date(2026, 2, 1),
        "vigencia_hasta": date(2028, 1, 31),
        "estado_aprobacion": "aprobado",
    },
    {
        # Venció el 31/03/2026 y sus prácticas siguen en curso: la consulta deja
        # ver el desfase sin habilitar ninguna acción.
        "id": 4,
        "nombre": "Agroindustrias del Norte Cía. Ltda.",
        "instrumento": "convenio",
        "referencia": "CONV-2025-031",
        "vigencia_desde": date(2025, 4, 1),
        "vigencia_hasta": date(2026, 3, 31),
        "estado_aprobacion": "aprobado",
    },
    {
        "id": 5,
        "nombre": "GAD Parroquial de Vilcabamba",
        "instrumento": "carta",
        "referencia": "CC-2026-011",
        "vigencia_desde": date(2026, 1, 20),
        "vigencia_hasta": date(2027, 1, 19),
        "estado_aprobacion": "pendiente",
    },
    {
        # Solo tuvo una práctica comunitaria, ya cerrada: N1 muestra el vacío.
        "id": 6,
        "nombre": "GAD Municipal de Catamayo",
        "instrumento": "convenio",
        "referencia": "CONV-2024-019",
        "vigencia_desde": date(2024, 7, 1),
        "vigencia_hasta": date(2026, 6, 30),
        "estado_aprobacion": "aprobado",
    },
)


def _ficha(datos):
    """Una entidad con su instrumento, la vigencia resuelta contra HOY y la aprobación."""
    ficha = dict(datos)
    ficha["instrumento_display"] = INSTRUMENTOS[ficha["instrumento"]]
    ficha["estado_aprobacion_display"] = ESTADO_APROBACION[ficha["estado_aprobacion"]]
    ficha["vigente"] = ficha["vigencia_desde"] <= HOY <= ficha["vigencia_hasta"]
    ficha["estado_vigencia"] = "vigente" if ficha["vigente"] else "vencido"
    ficha["estado_vigencia_display"] = "Vigente" if ficha["vigente"] else "Vencido"
    return ficha


def entidades():
    """N1: el catálogo, reconstruido en cada llamada para no compartir estado."""
    return [_ficha(datos) for datos in _ENTIDADES]


def get_entidad(entidad_id):
    """N1 detalle: una entidad del catálogo, o None si no existe."""
    return next((e for e in entidades() if e["id"] == entidad_id), None)


def convenios():
    """N2: el instrumento de cada entidad con su vigencia y su aprobación."""
    return entidades()


def practicas_vigentes_de_la_entidad(nombre):
    """N1 detalle (HU-07): prácticas aún vigentes de la entidad, sin mutar los datos."""
    return [
        p
        for p in data.practicas_de_la_carrera()
        if p["entidad"] == nombre and p["estado"] in ESTADOS_VIGENTES
    ]
