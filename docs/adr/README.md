# Registro de decisiones de arquitectura (ADR)

Cada decisión técnica relevante tiene su propio archivo con **contexto, decisión, alternativas consideradas y consecuencias** (formato MADR en español, plantilla en [template.md](template.md)). Cumple el principio V de la [constitución](../constitution.md).

La **fecha** es la de la decisión original cuando el repositorio la registra (`research.md`, `plan.md`, `arquitectura.md`, `api.md`); las decisiones tomadas en la sumativa 1 llevan 2026-11-03, día en que se redactaron.

| N.º | Título | Estado | Fecha |
| --- | --- | --- | --- |
| [0001](0001-backend-con-django.md) | Backend con Django (Python) | Aceptada | 2026-10-11 |
| [0002](0002-postgresql-como-motor-de-base-de-datos.md) | PostgreSQL como motor de base de datos | Aceptada | 2026-10-11 |
| [0003](0003-historial-inalterable-con-django-simple-history.md) | Historial inalterable con django-simple-history | Aceptada | 2026-10-11 |
| [0004](0004-autorizacion-rbac-y-filtrado-por-consulta.md) | Autorización con RBAC de Django y filtrado obligatorio por consulta | Aceptada | 2026-10-11 |
| [0005](0005-gestion-de-evidencias-pdf-versionadas.md) | Evidencias en PDF, de hasta 5 MB y versionadas | Aceptada | 2026-10-11 |
| [0006](0006-calculo-de-horas-y-deteccion-de-rezago.md) | Cálculo de horas esperadas y detección de rezago | Aceptada | 2026-10-11 |
| [0007](0007-practicas-laboral-y-comunitaria-separadas.md) | Prácticas laboral y comunitaria como registros separados | Aceptada | 2026-10-11 |
| [0008](0008-monolito-modular-con-dto-y-facade.md) | Monolito modular con DTO y Facade | Aceptada | 2026-10-21 |
| [0009](0009-api-del-prototipo-sin-drf-ni-base-de-datos.md) | API del prototipo sin Django REST Framework ni base de datos | Reemplazada por 0010 | 2026-10-21 |
| [0010](0010-adoptar-django-rest-framework-y-postgresql.md) | Adoptar Django REST Framework y PostgreSQL | Propuesta | 2026-11-03 |
| [0011](0011-metodo-de-autenticacion-de-la-api.md) | Método de autenticación de la API | Propuesta | 2026-11-03 |
| [0012](0012-contrato-universal-de-respuesta.md) | Contrato universal de respuesta | Aceptada | 2026-11-03 |
| [0013](0013-contenerizacion-con-docker-compose.md) | Contenerización con Docker Compose | Aceptada | 2026-11-03 |
| [0014](0014-integracion-continua-con-github-actions.md) | Integración continua con GitHub Actions | Aceptada | 2026-11-03 |
| [0015](0015-observabilidad-minima-logging-y-request-id.md) | Observabilidad mínima: logging estructurado y X-Request-ID | Aceptada | 2026-11-03 |
| [0016](0016-analisis-estatico-con-sonarcloud.md) | Análisis estático y quality gate con SonarCloud | Propuesta | 2026-11-04 |

## Cómo agregar o cambiar una decisión

1. Copia [template.md](template.md) como `NNNN-titulo-en-kebab-case.md` con el siguiente número libre.
2. Completa contexto, decisión, alternativas y consecuencias; empieza en «Propuesta».
3. Agrégala a la tabla y pásala a «Aceptada» cuando el equipo la confirme en el PR.
4. Un ADR aceptado no se reescribe: se crea otro que lo reemplaza y el anterior pasa a «Reemplazada por NNNN».

## Relación con otros documentos

- Los ADR 0001 a 0007 convierten los Temas 1 a 7 de [research.md](../../specs/001-seguimiento-practicas/research.md); el 0008 y el 0009 recogen [arquitectura.md](../arquitectura.md) y [api.md](../api.md).
- Los diagramas están en [../arquitectura/](../arquitectura/README.md) y el modelo de amenazas en [../seguridad.md](../seguridad.md).
