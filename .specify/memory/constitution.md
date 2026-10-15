# Sistema de Prácticas Preprofesionales Constitution

Espejo en formato Spec Kit de `docs/constitution.md`, que es la versión canónica. La herramienta Spec Kit lee este archivo para sus gates; cualquier enmienda se hace primero en `docs/constitution.md` y luego se propaga acá.

## Core Principles

### I. GitFlow Estricto
`main` es producción y solo recibe `release/*` o `hotfix/*`; `develop` es integración y solo recibe `feature/*`, `bugfix/*`, `release/*` o `hotfix/*`. Nadie pushea directo a `main` ni a `develop`: todo llega por Pull Request.

### II. Pull Requests Chicas y Revisadas
Un PR cubre un solo tema y es revisable; si supera ~400 líneas o toca varias áreas, se parte. El merge a `main` exige una aprobación de otra persona; a `develop` alcanza con la revisión del responsable del tema.

### III. Conventional Commits
Cada commit usa tipo (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`) y scope cuando hace falta, con subject claro en español o inglés, consistente dentro del mismo PR.

### IV. Fases SDD Documentadas en el Repositorio
Cada funcionalidad deja sus artefactos en `specs/NNN-nombre/`: `spec.md` (specify/clarify), `plan.md`, `research.md`, `data-model.md` (plan) y `tasks.md` (tasks) antes de implementar. Las herramientas de autoría (Spec Kit en `.specify/` y sus comandos en `.opencode/`) se versionan como apoyo del equipo; el estado machine-local no se versiona (ver `.specify/.gitignore`).

### V. Decisiones Registradas con Justificación
Cada decisión de arquitectura, stack o normativa se documenta en `research.md` con `Decision`, `Rationale` y `Alternatives considered`. Los temas abiertos se marcan con `[NEEDS CLARIFICATION]` y se cierran en una sesión de clarify antes de generar tareas.

### VI. Código con Tests, Documentación Verificable
Cuando el cambio tiene tests aplicables, se escriben primero (RED → GREEN → refactor). Para documentación y configuraciones sin runner, se verifica por estructura y por lo que sí se puede ejecutar. El README debe permitir reproducir el entorno completo desde cero.

### VII. Cumplimiento y Evidencias
Cada integrante deja constancia de su contribución (commits y PRs en `main`) y de su uso de IA en `docs/contribuciones.md` y `docs/declaracion-ia.md`; el repositorio guarda evidencias de ramas, PRs y protección en `evidencias/`, y las entregas finales en `entregables/`.

## Stack Tecnológico

| Área | Definición |
| --- | --- |
| Lenguaje y framework | Python 3.12 con Django 5.2 LTS |
| Base de datos | PostgreSQL (SQLite por defecto en desarrollo local) |
| Driver de base de datos | `psycopg` |
| Frontend | Plantillas de Django server-rendered; Django REST Framework descartado para el MVP |
| Historial inalterable | `django-simple-history` |
| Pruebas | `pytest` con `pytest-django` |
| Plataforma destino | Servidor Linux; cliente web en cualquier navegador |
| Escala del MVP | 5 carreras, ~300 estudiantes y ~150 prácticas activas, con pico semanal de reportes |

El detalle vive en `specs/001-seguimiento-practicas/plan.md` (Technical Context) y `research.md`. Cambiar el lenguaje, el framework, la base de datos o el enfoque de frontend exige enmendar esta constitución (ver Governance).

## Protecciones del Repositorio

`main` está protegida: exige Pull Request con 1 aprobación y no permite force-push ni borrado. `develop` está protegida: sin force-push ni borrado. Al mergear un PR, su rama se borra automáticamente (`delete_branch_on_merge`). La rama por defecto del repositorio es `develop`.

## Flujo de Desarrollo

Las funcionalidades se integran a `develop` por PR. Las versiones salen por `release/*` → `main` con revisión y tag de versión; después del release se hace el merge-back a `develop`. El Constitution Check se evalúa en `plan.md` antes de la fase de diseño y se re-evalúa después.

## Governance

La versión canónica de la constitución es `docs/constitution.md`; este archivo es su espejo para la herramienta Spec Kit. La constitución se modifica por PR a `develop` aprobado por la mayoría del equipo; los cambios en `main` siguen exigiendo PR aprobado. Si un principio entra en conflicto con una decisión de cátedra, gana la decisión de cátedra y la excepción se registra en `docs/constitution.md`.

**Version**: 1.1 | **Ratified**: 2026-10-12 | **Last Amended**: 2026-10-12