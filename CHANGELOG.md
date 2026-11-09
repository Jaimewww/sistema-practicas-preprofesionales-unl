# Changelog

Todos los cambios relevantes de este proyecto, en orden inverso. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es [semántico](https://semver.org/lang/es/).

## [Sumativa 1] - 2026-11-12

Cierre del incremento backend de la Sumativa 1: dos cadenas de PRs mergeadas (Jaime en `backend/` y `requirements`; Alejandro en la raíz, `docs/` y `specs/`) y los fixes de seguridad aplicados después del merge.

### Agregado

- **Dominio con persistencia real:** modelos y servicios de usuario, carrera y configuración, entidad receptora, período, práctica, asignación de tutor, plan de actividades, validación, reporte semanal e historial de estados (#98). Las transiciones de la práctica son atómicas y escriben un historial de solo inserción (`backend/apps/auditoria/`).
- **Contrato universal de respuesta y OpenAPI:** envelope en `backend/apps/contrato/` y `drf-spectacular` con esquema en `/api/v1/schema/` y Swagger en `/api/v1/docs/` (#100, [ADR 0012](docs/adr/0012-contrato-universal-de-respuesta.md)).
- **Flujo E2E de reportes:** `GET /api/v1/practicas/`, `GET /api/v1/practicas/<id>/` y `POST /api/v1/practicas/<id>/reportes/` sobre PostgreSQL, con permisos de rol y de objeto y el tope del Art. 341 en ayudantías (#101).
- **Autenticación y permisos:** JWT con simplejwt (access de 15 min, refresh de 30 con rotación y lista de bloqueo), rutas `auth/token/`, `auth/token/refresh/` y `auth/logout/`, y el demo `X-Rol` reubicado en `/prototipo/api/v1/` (#102, [ADR 0011](docs/adr/0011-metodo-de-autenticacion-de-la-api.md)).
- **Suite en pytest-django con cobertura:** `backend/pytest.ini`, `backend/.coveragerc` y `coverage.xml` para Sonar; al cierre, 555 pruebas pasadas con 1 omitida en local y cobertura informada de 97 % sobre `apps/` (#103).
- **`manage.py seed` idempotente** para cargar los datos de demo, sin que ningún endpoint lea `sample_data.py` (#98).
- **Configuración que falla cerrada:** `DJANGO_SECRET_KEY` y `POSTGRES_*` obligatorias con `DEBUG` apagado (#98).
- **Docker y PostgreSQL** con `docker compose`, entrypoint con espera de base y el servicio `db` sin puertos publicados (#88).
- **Integración continua** con `ruff`, `bandit`, `pip-audit`, pytest con cobertura sobre `postgres:17`, SonarCloud y build de la imagen (#89 y #107).
- **Modelado y arquitectura:** BPMN 2.0.2 del reporte semanal (#90), C4 con C1, C2, C3 y despliegue (#91), 16 ADR (#92) y modelo de amenazas STRIDE con OWASP Top 10 (#93).
- **Portal Quarto** con la documentación técnica, la matriz de trazabilidad, la bitácora, las contribuciones y la declaración de uso de IA (#85).
- **Observabilidad mínima:** logging estructurado, `X-Request-ID` en cada respuesta y `/health/` que consulta la base y responde `503` si falla (#95).

### Corregido

- Después del merge: DRF 3.18.2, simplejwt 5.5.1 y pytest 9.0.3 por advisories de `pip-audit`; el tope de intentos del login ya no se evade con `X-Rol`; el esquema OpenAPI queda cerrado con `DEBUG` apagado.

### Cambiado

- La suite pasa a pytest-django como runner de la integración continua y del README, manteniendo el runner clásico de Django como válida de comparación del mismo total.

## [Unreleased]

### Cambiado

- `spec.md` asigna los 20 RF al incremento de la Unidad 1 (RF-14 incluido; RF-01, RF-08, RF-13 y RF-16 a RF-19 pospuestos) y registra la segunda validación del docente del 2026-11-04 (sin observaciones).
- `spec.md` registra la validación del docente en la exposición de avances del 2026-10-26 (v0.3.0, sin observaciones).
- `spec.md` pasa a v0.4.0 (APE 002): objetivo y alcance del incremento de la Unidad 1, necesidades identificadas (N-01 a N-06) con director y Secretaría como actores secundarios, HU-14 y HU-15 con RF-20 (legalización de anexos separada de RF-04), criterios de error y validación en HU-01, HU-04, HU-05, HU-12 y HU-13, RNF-01, RNF-02 y RNF-09 sin detalles de implementación y verificables, contratos preliminares C-01 a C-19, matriz de trazabilidad necesidad → historia → requisito → criterio → operación, sesión de clarificación del 2026-11-08 y preguntas pendientes P-01 a P-08 marcadas con `[NEEDS CLARIFICATION]`.
- `spec.md` pasa a v0.3.0 para la semana 2: requisitos no funcionales RNF-01 a RNF-11, revisión de calidad de los 19 RF con registro de correcciones, matriz de permisos de RF-11, casos de uso CU-01 a CU-03 y restricción de integración con el sistema académico. RF-15 pasa a rechazar los reportes de ayudantías con más de 10 h semanales.
- `spec.md` pasa a v0.2.0 alineada con el Reglamento de Régimen Académico de la UNL: aprobación con 100 % de horas y al menos 70 % de evaluación (Art. 339), informe final del estudiante, informe del proyecto de vinculación en el servicio comunitario, subtipos laborales (pasantía y ayudantías) con tope de 10 h semanales, reporte de incumplimientos e informe consolidado (RF-14 a RF-19, HU-10 a HU-13, CE-07).

### Agregado

- `entregables/acd2-requisitos-http.pdf` (ACD 2) con su fuente y generador en `entregables/fuentes/`, y la captura HTTP real `evidencias/http-health-curl.txt`.
- `docs/fuentes/reglamento-practicas-unl.md` con el compendio del reglamento sobre prácticas preprofesionales.
- `docs/guia-requisitos.md` y su versión `docs/guia-requisitos.pdf`: guía requisito por requisito con su porqué, base normativa, prueba y matriz de trazabilidad.

## [0.5.0] - 2026-10-12

Quinta entrega: cierre de las contribuciones individuales, la prueba cruzada y los primeros entregables en PDF.

### Agregado

- `tasks.md` final: marcadores `[R1]/[R2]/[R3]` resueltos contra las decisiones de la fase 0.
- Filas de `docs/contribuciones.md` **confirmadas por los 5 integrantes** (incluye apellidos pendientes) y declaraciones de uso de IA de Melissa, Ivett, Doménica y Jaime en `docs/declaracion-ia.md`.
- **Prueba cruzada registrada**: captura en `evidencias/prueba-cruzada.png` y fila en el registro de `quickstart.md`.
- Primeros entregables en `entregables/`: síntesis de la ACD 1 e informe de la AA 1, en PDF.
- `plan.md`: el gate IV y el árbol de documentación referencian `tasks.md`.

## [0.4.0] - 2026-10-12

Cuarta entrega: primer código del proyecto y el desglose de tareas del MVP.

### Agregado

- Esqueleto del backend **Django 5.2** en `backend/`, con endpoint `GET /health/` → `{"status": "ok"}`, suite de tests (test-first: 404 → 200), `Makefile` (`make install/run/test`), `requirements*.txt`, `.env.example` y configuración de analizadores.
- Sección "Ambiente de desarrollo" en el README (requisitos, instalación, ejecución con un solo comando, verificación) y `quickstart.md` para reproducir el entorno en 5 minutos, con registro de prueba cruzada.
- Desglose de tareas por historia de usuario en `specs/001-seguimiento-practicas/tasks.md` (Setup, Base, HU-01 a HU-09 + RF-13, Cierre).
- Cierre de los tres temas abiertos de la fase 0: **frontend con plantillas de Django**, **alertas por comando de gestión + cron** y **escala asumida de 5 carreras / ~300 estudiantes / ~150 prácticas activas**.
- `docs/bibliografia.md` con las fuentes del equipo y la fila confirmada de Alejandro en `docs/contribuciones.md`, junto con su declaración de uso de IA.

## [0.3.0] - 2026-10-12

Tercera entrega: ratificación y propagación de la constitución del equipo.

### Cambiado

- La constitución queda **ratificada** como v1.0 por el equipo: `docs/constitution.md` deja de estar «pendiente de revisión», `.specify/memory/constitution.md` deja de ser la plantilla vacía (ahora es el espejo en formato Spec Kit con los 7 principios, las protecciones del repositorio, el flujo de desarrollo y la gobernanza) y el Constitution Check de `plan.md` se evalúa contra la versión ratificada.

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
