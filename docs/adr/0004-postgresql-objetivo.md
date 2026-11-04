# ADR 0004 — PostgreSQL como motor objetivo; SQLite en desarrollo

- **Estado**: aceptada
- **Implementación**: planificada — la configuración actual usa SQLite y el motor objetivo no está conectado
- **Registro**: 2026-11-03, retrospectivo

## Contexto

El sistema debe aislar información por carrera, sostener restricciones de integridad y conservar un historial inalterable. El proyecto real tiene PostgreSQL por lineamiento de DTI.

## Decisión

- PostgreSQL como motor del sistema; SQLite solo como base local de desarrollo.
- `psycopg` como driver de PostgreSQL.
- Historial inalterable de cambios de estado con `django-simple-history` y una tabla de solo inserción.

## Alternativas registradas

- **SQLite como motor del sistema**: descartado; no reproduce concurrencia, tipos ni integridad de PostgreSQL.
- **MySQL o MariaDB**: descartado; no aporta frente a PostgreSQL y diverge del lineamiento del proyecto real.
- **Triggers de PostgreSQL para el historial**: descartado; saca la regla del código de la aplicación y complica revisión y pruebas.
- **Tabla de auditoría escrita a mano con señales**: descartado; más código propio y más casos que olvidar.

## Consecuencias

- `backend/config/settings.py` apunta a SQLite y `backend/requirements.txt` no incluye `psycopg`.
- `django-simple-history` está declarado en la constitución y en el research, pero no instalado: el historial persistente no existe todavía.
- La paridad entre desarrollo y producción no está ejercida; el paso a PostgreSQL exige configuración, migración de datos y pruebas.
- El dominio de demostración se reconstruye con datos en memoria y overlays de cookies o sesión; la sesión Django sí usa la base local (ver [ADR 0006](0006-estado-demo-cookies.md)).

**Fuentes**: [constitución](../constitution.md) (stack) · [research](../../specs/001-seguimiento-practicas/research.md) Temas 2 y 3 · [data-model](../../specs/001-seguimiento-practicas/data-model.md) (HistorialEstado) · [settings.py](../../backend/config/settings.py) · [requirements.txt](../../backend/requirements.txt).
