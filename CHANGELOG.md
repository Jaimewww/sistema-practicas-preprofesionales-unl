# Changelog

Todos los cambios relevantes de este proyecto, en orden inverso. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es [semántico](https://semver.org/lang/es/).

## [0.2.0] - 2026-10-12

Segunda entrega: estructura de gobernanza y cumplimiento de la APE-001, y entrada del entorno Spec Kit al repositorio.

### Agregado

- Constitución del equipo en `docs/constitution.md` con 7 principios (GitFlow estricto, PRs chicos y revisados, Conventional Commits, fases SDD documentadas, decisiones registradas, documentación verificable, cumplimiento y evidencias).
- Plantilla de Pull Request en `.github/PULL_REQUEST_TEMPLATE.md`.
- Estructura de cumplimiento en `docs/`: `contribuciones.md` (una fila por integrante, pre-cargada desde el historial) y `declaracion-ia.md` (declaración individual de uso de IA).
- Carpetas de evidencia con instructivo: `evidencias/` (capturas de ramas, PRs y protección) y `entregables/` (PDFs finales).
- Entorno Spec Kit versionado: `.specify/` y `.opencode/` como herramientas de apoyo del equipo (inicialización de Melissa).

### Cambiado

- `.specify/` y `.opencode/` ahora se versionan en el repositorio; solo el estado machine-local queda fuera (`.specify/.gitignore`). La nota de la v0.1.0 que decía lo contrario quedó obsoleta con este cambio.

## [0.1.0] - 2026-10-11

Primera entrega del proyecto: la documentación base y las tres primeras fases de Spec Kit. Todavía no hay código, así que esta versión no incluye nada ejecutable.

### Agregado

- Contexto del proyecto en `README.md`: situación investigada, actores, proceso, alcance preliminar, restricciones y criterios de éxito.
- Guía de contribución en `CONTRIBUTING.md` con el modelo GitFlow, los comandos de `git flow` y la convención de commits.
- Especificación funcional del seguimiento de prácticas preprofesionales en `specs/001-seguimiento-practicas/spec.md`: problema, actores, historias de usuario con criterios de aceptación, alcance, supuestos, restricciones, requisitos funcionales, estados de la práctica y criterios de éxito.
- Plan de implementación en `specs/001-seguimiento-practicas/plan.md`: contexto técnico, gates derivados del spec y estructura del repositorio.
- Decisiones técnicas de la fase 0 en `specs/001-seguimiento-practicas/research.md`, con justificación y alternativas descartadas para cada tema.
- Modelo de datos en `specs/001-seguimiento-practicas/data-model.md`: entidades con sus campos y relaciones, reglas de integridad y transiciones de estado.

### Notas

- Las decisiones de la fase 0 fijan Django con PostgreSQL como stack del backend.
- `.specify/` y `.opencode/` no se versionan: son herramientas locales de desarrollo, no parte del producto.
- `tasks.md` queda pendiente hasta cerrar los temas abiertos de `research.md`: stack del frontend, mecanismo de generación de alertas y escala esperada del MVP.
