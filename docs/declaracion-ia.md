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

**Firma**: Jaime Landázuri

---

## Integrante: [Nombre y apellido]

**Fecha**: [DD/MM/AAAA]

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
|  |  |  |  |

**Firma**: [Nombre]

---

## Integrante: [Nombre y apellido]

**Fecha**: [DD/MM/AAAA]

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
|  |  |  |  |

**Firma**: [Nombre]