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

## Integrante: Melissa Contento

**Fecha**: 10/10/2026

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| OpenCode (asistente de desarrollo en terminal) | Inicialización del entorno Spec Kit (`.specify/`, `.opencode/` y la carpeta `specs/`) | La IA generó el scaffolding del entorno y probó los comandos de Spec Kit; yo revisé la estructura, validé los documentos de la especificación y decidí qué quedaba versionado en el repositorio. | Revisión de la estructura del repositorio y del contenido de los documentos en el PR #2 antes del merge. |

**Firma**: Melissa Contento

---

## Integrante: Ivett Zaragocín

**Fecha**: 11/10/2026

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| Claude (Anthropic), mediante un asistente de desarrollo en terminal | Redacción de `spec.md` | El contenido de la especificación (problema, actores, historias de usuario, alcance y criterios de éxito) lo definí yo; la IA solo me ayudó a mejorar la redacción y la claridad de algunos textos. | Lectura crítica de cada cambio sugerido y revisión del equipo en el PR #1. |

**Firma**: Ivett Zaragocín

---

## Integrante: Doménica Rojas

**Fecha**: 11/10/2026

| Herramienta | Actividad | Alcance (qué hizo la IA / qué revisó el humano) | Revisión |
| --- | --- | --- | --- |
| Gemini | Mejora de redacción de los documentos técnicos | Yo estructuré el modelo de datos, la matriz comparativa y definí el papel del backend en los archivos `research.md`, `plan.md` y `data-model.md`. La IA **únicamente** se utilizó para mejorar la redacción del texto, dándole un tono más formal, claro y académico. | Lectura crítica de los textos devueltos para verificar que conservaran intactas mis ideas y decisiones originales antes de enviarlas al PR #4. |

**Firma**: Doménica Rojas