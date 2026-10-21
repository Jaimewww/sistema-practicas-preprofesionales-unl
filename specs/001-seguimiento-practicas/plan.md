# Implementation Plan: Seguimiento de prácticas preprofesionales

**Branch**: `001-seguimiento-practicas` | **Date**: 2026-10-11 | **Spec**: [spec.md](./spec.md)

**Input**: Especificación funcional en `specs/001-seguimiento-practicas/spec.md`

## Summary

El sistema debe dar seguimiento y trazabilidad a una práctica preprofesional **ya asignada**, desde su inicio hasta su cierre: plan de actividades, reportes semanales con horas y evidencias, validación del tutor académico, alertas de atraso, informe final y cierre. El valor no está en almacenar formularios, sino en responder en todo momento en qué estado está cada práctica, cuántas horas lleva y quién validó cada paso.

Enfoque técnico (ver [research.md](./research.md)): backend **Django con PostgreSQL**, con control de acceso por roles, aislamiento de datos por carrera y por practicantes asignados, historial inalterable de cambios de estado y generación de alertas por tareas programadas. El alcance se limita al MVP del spec: quedan fuera postulación y emparejamiento, convenios, integración con SIAAF, firma electrónica, aplicación móvil, homologación, encuesta de satisfacción y certificado oficial.

## Technical Context

**Language/Version**: Python 3.12 con Django 5.2 LTS

**Primary Dependencies**: Django, `psycopg` (driver de PostgreSQL, con SQLite por defecto en desarrollo), `django-simple-history` (historial inalterable) y las plantillas de Django para el frontend; Django REST Framework queda descartado para el MVP

**Storage**: PostgreSQL

**Testing**: pytest con `pytest-django` (unitarias, de integración y de contrato)

**Target Platform**: servidor Linux; cliente web en cualquier navegador

**Project Type**: aplicación web server-rendered con plantillas de Django (arquitectura: [monolito modular](../../docs/arquitectura.md))

**Performance Goals**: el estudiante conoce sus horas validadas y faltantes en menos de 1 minuto (CE-03); el sistema responde entre 2 y 10 segundos

**Constraints**: horas requeridas, plazos de reporte y de revisión, y umbral de rezago configurables por carrera y modalidad, y copiados a la práctica al asignarla (RF-12); el servicio comunitario funciona sin tutor de entidad receptora; los datos de un estudiante solo los ven él, sus tutores y el coordinador de su carrera; el proyecto se desarrolla dentro de un ciclo académico

**Scale/Scope**: 5 carreras, ~300 estudiantes y ~150 prácticas activas, con pico semanal de reportes (supuesto adoptado el 2026-10-12; ajustable con datos reales)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluado contra la constitución del equipo (versión 1.0, ratificada el 2026-10-12): [docs/constitution.md](../../docs/constitution.md) y su espejo en `.specify/memory/constitution.md`. Verificado de nuevo después del diseño de [data-model.md](./data-model.md).

| Principio | Gate que impone | Cumplimiento en este plan |
| --- | --- | --- |
| I. GitFlow estricto | Todo llega por PR; `main` solo vía `release/*` o `hotfix/*` | Cumple: la integración se hizo por PRs y releases (#1–#9) |
| II. PRs chicos y revisados | Un tema por PR; `main` exige 1 aprobación | Cumple: PRs por tema; los releases pasaron por revisión de un integrante |
| III. Conventional Commits | Mensajes con tipo y scope | Cumple: historial con `docs:`, `chore:` y scopes |
| IV. Fases SDD documentadas | `spec.md` y `plan.md` completos antes de implementar | Cumple: `spec.md`, `plan.md`, `research.md`, `data-model.md` y [tasks.md](./tasks.md) presentes |
| V. Decisiones registradas | Sin temas abiertos al generar `tasks.md` | Cumple: los tres temas de la fase 0 se resolvieron el 2026-10-12 (ver [research.md](./research.md)) |
| VI. Código con tests, docs verificable | Tests/verificación y entorno reproducible desde el README | Pendiente: no hay código todavía; se verifica cuando exista `backend/` |
| VII. Cumplimiento y evidencias | Filas de contribución y evidencias cargadas | En curso: estructura en `docs/`; filas y capturas por confirmar |

Solo el principio VI (código con tests y entorno reproducible) queda pendiente de validación funcional a medida que se desarrolle el producto; el diseño ya documentado no depende de él, y con los temas de la fase 0 cerrados ya se puede generar `tasks.md`.

## Project Structure

### Documentation (this feature)

```text
specs/001-seguimiento-practicas/
├── spec.md              # Especificación funcional (fases specify y clarify)
├── plan.md              # Este archivo (fase plan)
├── research.md          # Fase 0: decisiones técnicas y alternativas descartadas
├── data-model.md        # Fase 1: entidades, reglas de integridad y transiciones
├── quickstart.md        # Reproducción del entorno en 5 minutos
└── tasks.md             # Fase tasks: tareas por historia de usuario
```

`contracts/` no se genera: al no haber API en el MVP (plantillas Django), no hay contrato que congelar.

### Source Code (repository root)

```text
backend/
├── manage.py
├── config/                  # settings, urls, wsgi y asgi
├── apps/
│   ├── usuarios/            # usuario, roles y RBAC
│   ├── carreras/            # carrera y su configuración: horas, plazos y umbral
│   ├── entidades/           # entidad receptora
│   ├── practicas/           # práctica, asignación de tutores y máquina de estados
│   ├── actividades/         # plan, reportes semanales, evidencias y validaciones
│   ├── alertas/             # generación y registro de alertas
│   ├── auditoria/           # historial inalterable de cambios de estado
│   └── reportes/            # consultas consolidadas del coordinador
├── templates/              # plantillas Django del frontend (server-rendered)
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: se elige una **aplicación web server-rendered con plantillas de Django**, sin API REST completa en el MVP (decisión del 2026-10-12, ver [research.md](./research.md)); el detalle de arquitectura y patrones (monolito modular, DTO, Facade) está en [docs/arquitectura.md](../../docs/arquitectura.md). El backend es un proyecto Django único, sin microservicios, organizado en aplicaciones por dominio con fronteras explícitas: una por cada área del spec, más `auditoria` porque la trazabilidad es un requisito propio (RF-10) y no un detalle de otra aplicación. Las plantillas viven en `templates/`; si más adelante el producto pide una SPA, la migración agrega una API con Django REST Framework y un frontend separado.

## Complexity Tracking

Sin violaciones que justificar: el plan no agrega proyectos, capas ni patrones más allá de los que exige el spec.
