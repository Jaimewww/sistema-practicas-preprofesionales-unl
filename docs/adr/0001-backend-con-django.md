# 0001. Backend con Django (Python)

- **Estado**: Aceptada
- **Fecha**: 2026-10-11
- **Decisores**: equipo (fase 0 de la planificación)

## Contexto

El problema exige trazabilidad operativa estricta (quién, qué y cuándo), transiciones de estado controladas y control de acceso riguroso con actores externos a la institución (tutor de la entidad receptora). Además, el proyecto real de la UNL sigue el lineamiento de Python, Django y PostgreSQL por DTI. Origen: [research.md, Tema 1](../../specs/001-seguimiento-practicas/research.md).

## Decisión

Usar **Django (Python)** como framework de backend. Hoy el proyecto es Django 5.2 (`backend/requirements.txt`).

## Alternativas consideradas

| Alternativa | Por qué se descartó |
| --- | --- |
| NestJS (Node.js) | Los Guards cubren el RBAC, pero la gestión de evidencias exige librerías de terceros y la auditoría obliga a escribir interceptores propios. |
| Spring Boot (Java) | Spring Security es robusto, pero el manejo de archivos es más verboso y la auditoría pide configuración adicional (por ejemplo Hibernate Envers). |

## Consecuencias

- **Positivas**: RBAC, ORM con migraciones, `FileField` y el ecosistema de auditoría vienen resueltos; coincide con el stack del proyecto real.
- **Negativas o costos**: el equipo queda atado al ecosistema Python; Django no trae API REST completa (ver [0010](0010-adoptar-django-rest-framework-y-postgresql.md)).

## Referencias

- [research.md, Tema 1](../../specs/001-seguimiento-practicas/research.md)
- [plan.md](../../specs/001-seguimiento-practicas/plan.md)
