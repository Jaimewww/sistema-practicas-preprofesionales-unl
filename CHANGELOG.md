# Changelog

Todos los cambios relevantes de este proyecto, en orden inverso. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es [semántico](https://semver.org/lang/es/).

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
