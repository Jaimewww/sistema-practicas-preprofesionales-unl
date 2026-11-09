# Declaración de uso de IA — APE-001

Cada integrante declara cómo usó herramientas de IA en este trabajo. La declaración es individual y va firmada con fecha. Completá la plantilla correspondiente según corresponda; si no usaste IA, indicá "No usé herramientas de IA".

## Guía para completar

- **Herramienta**: nombre y versión, por ejemplo "GitHub Copilot", "ChatGPT", "Pi (asistente de desarrollo)", etc.
- **Actividad**: para qué se usó (redacción de documentos, revisión de código, generación de pruebas, corrección ortográfica, etc.).
- **Alcance**: qué parte del trabajo hizo la herramienta y qué parte revisó y decidió el humano.
- **Revisión**: cómo se verificó el resultado (lectura crítica, revisión por otra persona, ejecución de pruebas).
- **Firma**: nombre, fecha y (si aplica) mail institucional.

---

## Integrante: Alejandro Padilla

**Fecha**: 11/10/2026

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| Claude (Anthropic), mediante un asistente de desarrollo en terminal | Sesión de clarify sobre `spec.md` | La IA detectó las ambigüedades del spec y propuso cinco preguntas con opciones y una recomendación. Elegí la respuesta de cada pregunta; la IA aplicó esas respuestas en las secciones del spec. | Lectura del spec resultante y revisión del equipo en el PR #3. |
| Claude (Anthropic), mediante un asistente de desarrollo en terminal | Borrador de `tasks.md` | La IA redactó el desglose de tareas a partir de `spec.md`, `plan.md`, `data-model.md` y la constitución. Revisé que cada tarea se trace a una historia y a una ruta del plan. | Revisión estructural (IDs, cobertura de historias) y revisión del equipo en el PR #13 antes del merge. |
| Claude (Anthropic), mediante un asistente de desarrollo en terminal | Bibliografía y esta declaración | La IA reunió las fuentes que citan los documentos del repositorio y redactó el borrador; confirmé las fuentes y el texto. | Lectura crítica antes de abrir el PR. |
| Claude (Anthropic), mediante un asistente de desarrollo en terminal | Actualización de `spec.md` con el reglamento y `docs/guia-requisitos.md` (y su PDF) | Aporté el compendio del reglamento; la IA lo comparó con el spec, redactó los requisitos nuevos (RF-14 a RF-19) y la guía con el porqué de cada requisito, y generó el PDF. Revisé y aprobé el resultado. | Lectura del PDF de la guía y del diff del spec antes de abrir el PR. |
| Claude (Anthropic), mediante un asistente de desarrollo en terminal | ACD 2: requisitos no funcionales, revisión de calidad, casos de uso (`spec.md` v0.3.0) y documento de la entrega | La IA redactó los borradores a partir de las decisiones y observaciones del equipo, y capturó la solicitud HTTP real a `/health/`; cada integrante revisa su sección individual. | Revisión del diff del spec y lectura del PDF antes de abrir el PR. |

Actualización 03/11/2026 — Sumativa 1 (issues #81 a #86, plan #87):

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| Claude Code (Anthropic) y Pi (asistente de desarrollo en terminal, con el perfil «el Gentleman») | Docker y compose con PostgreSQL (#81, PR #88) y CI en GitHub Actions (#82, PR #89) | La IA redactó el `Dockerfile`, el compose, el entrypoint, el workflow, la configuración de `ruff` y la sección del README, y eliminó dos pruebas duplicadas que se tapaban entre sí (F811). Yo definí el contrato de variables de entorno y los pasos del workflow. | `docker compose up` con `/health/` en 200, entrypoint con espera de base y `migrate`, 231 pruebas en el contenedor como usuario 1000, `ruff` sin errores y cobertura local de 98 %. |
| Claude Code (Anthropic) y Pi (el Gentleman); subagentes de escritura | Modelado BPMN (#83, PR #90) | La IA redactó el análisis de los siete elementos y el diagrama BPMN 2.0.2 con su disposición gráfica, y lo exportó a SVG y PNG. Yo fijé el proceso a modelar y la convención de nombres. | Validación del XML (bien formado, referencias y elementos de diagrama completos), 28 tareas con verbo en infinitivo y render con puppeteer en Docker. |
| Claude Code (Anthropic) y Pi (el Gentleman); subagentes de escritura | C4, ADR y modelo de amenazas (#84, PR #91, #92 y #93) | La IA redactó el DSL de Structurizr, el UML de código, los 15 ADR y el análisis STRIDE y OWASP Top 10, a partir del código y los documentos del repositorio. Yo decidí qué elementos son reales y cuáles se marcan como planificados. | Validación del DSL con la imagen `structurizr/structurizr`, render de los SVG y contraste de las clases con `backend/apps/prototipo`. La imagen `structurizr/cli` está deprecada y no valida nada, por eso no se usó. |
| Claude Code (Anthropic) y Pi (el Gentleman); subagente de escritura | Portal Quarto, matriz de trazabilidad, `tasks.md` y workflow de GitHub Pages (#85) | La IA escribió `_quarto.yml`, las páginas del portal, la matriz RF → código → prueba y `docs.yml`, y dejó `tasks.md` con solo T001 y T005 marcadas, porque el resto no existe en código. Yo definí los criterios (no afirmar DRF, PostgreSQL ni autenticación como hechos) y las superficies de edición. | Comprobación de que cada nombre de prueba de la matriz existe en el código y `quarto render` en Docker. La publicación en Pages la habilita Jaime. |
| Claude Code (Anthropic) y Pi (el Gentleman) | Observabilidad mínima (#86) | La IA escribió el middleware, el logging, la comprobación de base en `/health/` y sus pruebas. Yo definí el contrato (`X-Request-ID`, errores 500 sin datos sensibles y 503 si la base no responde). | Suite completa en verde y `ruff`. El PR aún no se abrió. |

La versión del modelo no la declaran las herramientas en este registro, así que no se infiere. Los PRs #88 a #93 están en borrador: la revisión humana de Jaime y la prueba cruzada siguen pendientes, y esta nota no declara que ya ocurrieron.

Actualización 08/11/2026 — APE 002 (refinamiento de `spec.md` a v0.4.0): Pi (asistente de desarrollo en terminal, con el perfil «el Gentleman», sobre Claude de Anthropic) auditó el `spec.md` v0.3.0 contra la guía de la APE 002 y redactó los cambios: objetivo del incremento de la Unidad 1, necesidades N-01 a N-06, HU-14, HU-15 y RF-20, criterios de error y validación, RNF-01, RNF-02 y RNF-09 reescritos, contratos preliminares C-01 a C-19 a partir de las operaciones existentes en `docs/api.md` y `docs/trazabilidad.md`, matriz de trazabilidad y preguntas pendientes P-01 a P-08. La sesión de clarificación del 2026-11-08 registra decisiones del equipo que aún deben validarse con el docente; no declara que el docente ya las aprobó. Revisión humana: lectura del diff del spec antes de abrir el PR. La versión del modelo no se infiere.

**Firma**: Alejandro Padilla

---

## Integrante: Jaime Landázuri

**Fecha**: 12/10/2026

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| Pi (asistente de desarrollo en terminal) | Coordinación de la integración GitFlow: PRs, releases v0.1.0–v0.4.0, tags y merge-backs | La IA ejecutó merges, resolvió conflictos (incluido el del PR #15) y mantuvo la secuencia de releases; yo definí el plan de integración y autoricé cada paso. | Verificación post-merge: árboles `main` == `develop`, tags presentes y ramas limpias. |
| Pi (asistente de desarrollo en terminal) | Conversión de `plan.md`/`research.md`/`data-model.md` al formato Spec Kit y redacción de la constitución v1.0 | La IA redactó los documentos siguiendo las plantillas de Spec Kit; yo revisé el contenido y el equipo lo validó en los PRs #7 y #10. | Revisión estructural (paridad con las plantillas) y revisión del equipo antes del merge. |
| Pi (asistente de desarrollo en terminal) | Esqueleto del backend (Django) con endpoint `/health`, README de instalación/ejecución y `quickstart.md` | La IA escribió el código y los tests en modo test-first (404 → 200); yo corrí la suite y la prueba cruzada desde cero. | `manage.py test` del backend y corrida desde cero con `curl /health/`. |
| Pi (asistente de desarrollo en terminal) | Cierre de los tres temas abiertos de la fase 0 (frontend, alertas y escala) | La IA propuso las opciones con recomendaciones; yo decidí junto con el equipo las tres soluciones y la IA documentó las decisiones en `research.md` y `plan.md`. | Revisión del diff del PR #16 y cero `[NEEDS CLARIFICATION]` restantes. |
| NotebookLM | Análisis de los actores con el reglamento de la UNL (ACD 2, semana 2) | Cargué el reglamento como fuente y consulté las funciones de cada actor; el equipo discutió cada actor y decidió los cambios en los requisitos. | Contraste de cada respuesta con el artículo citado del reglamento. |

Actualización 24/10/2026 — issues #63 (API base, PR #65) e #55 (prototipo N1/N2): Pi (asistente de desarrollo en terminal) implementó ambos aportes bajo mi dirección: el contrato del API v1, DTO y fachada con consultas de práctica/horas por persona sintética (PR #65, mergeado) y las pantallas del catálogo de entidades y convenios (PR de #55). El alcance y las decisiones (monolito modular, DTO, Facade, demo solo en DEBUG sin autenticación) los definí yo y corresponden a `docs/arquitectura.md` y `docs/api.md`. Verificación: suites Django completas y verificación técnica independiente de seguridad; la prueba visual en navegador no se ejecutó por falta de runner. Prueba cruzada humana: pendiente.

Actualización 12/11/2026 — Sumativa 1 (incremento del backend, issues #76 a #80, PRs apilados #98/#100/#101/#102/#103 mergeados = los 5 en Cecil de orden):

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| Pi (asistente de desarrollo en terminal, perfil «el Gentleman», suba en modelo de la sesión; la versión no la declaran las herramientas) y subagentes (writer/verify especializados) | Incremento del backend: modelos y servicios T016/T022/T024/T017/T019, contrato universal + OpenAPI (#77), flujo de reportes (#78), JWT y permisos por rol/objeto (#79), pytest+cobertura (#80) | La IA dirigió el desarrollo con lectura primero de las especificaciones; cada unidad se implementó RED-first con suites verdes (459 → 462 tests, pérdida de cobertura ~98 %), sondeos de seguridad de un verificador independiente y correcciones que la IA no tomó por sí (opciones presentadas al humano). Yo definí el alcance de cada issue, tomé las decisiones de producto (vínculo del tutor de entidad, retiro del demo sombreado, JWT real con el demo X-Rol provisional pendiente del ADR #84) y revisé/elegí las opciones de desbloqueo. | Suite completa de pytest en verde por cada unidad, makemigrations/check limpios, evaluación independiente de seguridad por unidad (4 verificados; un bloqueador F1 real — refresh con usuario borrado — corregido y pinado), `ruff` y makemigrations en superficies propias. Merges y revisión final por el compañero AlejandroTatum. |
Registro de integración — issue #62: por solicitud de Jaime, Pi implementó el API de historial y legalización asignado al orden 4, incluida la ampliación explícitamente autorizada de permisos para Director y Secretaría. Un subagente escribió el código, tests y documentación; otro realizó la verificación técnica independiente de seguridad, y el asistente de integración revisó el diff y corrigió dos afirmaciones de documentación. La implementación base está en `0a729dc`. Se verificaron 37 tests focalizados y 231 tests completos, además de `manage.py check`; no hubo prueba visual ni prueba cruzada humana. La evaluación nativa no estuvo disponible por falta del binario y el diagnóstico LSP fue parcial. Este registro no atribuye a Doménica esta implementación ni una revisión, aprobación o firma personal.

**Firma**: Jaime Landázuri

---

## Integrante: Melissa Contento

**Fecha**: 10/10/2026

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| OpenCode (asistente de desarrollo en terminal) | Inicialización del entorno Spec Kit (`.specify/`, `.opencode/` y la carpeta `specs/`) | La IA generó el scaffolding del entorno y probó los comandos de Spec Kit; yo revisé la estructura, validé los documentos de la especificación y decidí qué quedaba versionado en el repositorio. | Revisión de la estructura del repositorio y del contenido de los documentos en el PR #2 antes del merge. |

Actualización 21/10/2026 — issue #53: Codex completó el prototipo de Coordinador/DVS a partir del avance local, corrigió datos y navegación, agregó pruebas y documentación y ejecutó verificaciones Django/Chrome. Se guardaron capturas en `evidencias/`. La revisión humana y aprobación del PR están pendientes; esta nota no declara una revisión realizada por la integrante.

Actualización 24/10/2026 — issue #61: la integrante aprobó el plan de implementación y autorizó publicar un comentario con el trabajo pendiente para otro issue. Codex escribió primero la especificación y los tests de contrato, verificó RED (rutas 404 y estado de pantallas sin actualizar), implementó la fachada común, DTO de alertas, cierre con guard, cookie compatible e integración C2/C4/campana. Ejecutó las pruebas Django y el recorrido del navegador con capturas en `evidencias/api-alertas-cierre/`. Los resultados finales se registran en `evidencias/api-alertas-cierre-verificacion.md`. La revisión humana, prueba cruzada y aprobación del PR siguen pendientes; esta nota no declara que ya ocurrieron.

**Firma**: Melissa Contento

---

## Integrante: Ivett Zaragocín

**Fecha**: 11/10/2026

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| Claude (Anthropic), mediante un asistente de desarrollo en terminal | Redacción de `spec.md` | El contenido de la especificación (problema, actores, historias de usuario, alcance y criterios de éxito) lo definí yo; la IA solo me ayudó a mejorar la redacción y la claridad de algunos textos. | Lectura crítica de cada cambio sugerido y revisión del equipo en el PR #1. |

Actualización 24/10/2026 — issue #60 / PR #69: según los commits y el código del PR #69, Claude Code (Anthropic), como asistente de desarrollo en terminal, implementó el `PATCH /api/v1/pendientes/<clave>/` de esta entrega: el módulo `validaciones.py` con la cookie firmada de 24 h por navegador, el decorador de escritura del API, la integración con las pantallas T2 y T1, 31 tests nuevos y la actualización de `docs/api.md`. La versión del modelo no se declara en el PR, así que no se infiere. El resumen del PR #69, según el contexto de integración, menciona además una revisión automática de cuatro lentes; no consta una revisión humana del cambio. La verificación del 24/10/2026 la ejecutó el asistente de integración —no la integrante— sobre la rama del PR: `manage.py test` completo (153 tests, OK) y `manage.py check` sin observaciones, además de corregir dos expectativas de alcance del coordinador que ya fallaban en `develop` desde el PR #66. `mypy` no está disponible en el entorno y no hubo prueba cruzada humana. Esta nota no declara revisión humana, aprobación del PR ni firma de la integrante.

Actualización 09/11/2026 — issue #110: la actualización de mi fila en `docs/contribuciones.md` y de esta sección la redactó un asistente de desarrollo en terminal a partir del historial del repositorio y del issue #110; yo revisé que los PRs y commits citados existan y que la reflexión refleje mi aporte. Declaro además que puedo explicar técnicamente lo declarado en mi fila.

**Firma**: Ivett Zaragocín

---

## Integrante: Doménica Rojas

**Fecha**: 11/10/2026

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| Gemini | Mejora de redacción de los documentos técnicos | Yo estructuré el modelo de datos, la matriz comparativa y definí el papel del backend en los archivos `research.md`, `plan.md` y `data-model.md`. La IA **únicamente** se utilizó para mejorar la redacción del texto, dándole un tono más formal, claro y académico. | Lectura crítica de los textos devueltos para verificar que conservaran intactas mis ideas y decisiones originales antes de enviarlas al PR #4. |
| Pi (asistente de desarrollo en terminal) | Implementación del prototipo D1–D2 / S1–S2 para Director de carrera y Secretaría de carrera | Yo definí el alcance (solo consulta para el director, legalización de anexos para la secretaría, persistencia por cookie) y revisé cada pantalla. Pi escribió las vistas, templates, helpers de `sample_data.py`, módulo de estado `secretaria.py`, tests, menús y rutas; también resolvió el problema de configuración del reviewer y aplicó la corrección defensiva con `deepcopy` que el review de confiabilidad solicitó. | Ejecución de `manage.py test apps.prototipo.tests_director_secretaria` (10/10 OK), revisión manual de las URLs de prototipo en navegador y aprobación del native review de Gentle AI. |

**Firma**: Doménica Rojas
