# Decisiones de arquitectura (ADR)

Registro numerado de las decisiones de arquitectura y de patrones del sistema, con contexto, alternativas registradas, consecuencias y fuentes locales. Es el índice estable que cita la [descripción de arquitectura](../arquitectura.md). No reemplaza a las fuentes originales: cada decisión sigue viviendo en `research.md`, `plan.md`, `docs/api.md` o el código que la aplica.

## Registro

| ADR | Decisión | Estado | Implementación |
| --- | --- | --- | --- |
| [0001](0001-monolito-modular.md) | Monolito modular por dominio | aceptada | parcial |
| [0002](0002-django-plantillas-jsonresponse.md) | Django 5.2 con plantillas y `JsonResponse`; sin DRF ni SPA | aceptada | parcial |
| [0003](0003-dto-fachada-transiciones.md) | DTO, fachada, capa de servicios y tabla de transiciones | aceptada | parcial |
| [0004](0004-postgresql-objetivo.md) | PostgreSQL como motor objetivo; SQLite en desarrollo | aceptada | planificada |
| [0005](0005-autenticacion-rbac.md) | Sesión Django, RBAC y aislamiento por consulta | aceptada | planificada |
| [0006](0006-estado-demo-cookies.md) | Estado de la demo en cookies firmadas del navegador | aceptada (solo demostración) | actual |
| [0007](0007-alertas-comando-cron.md) | Alertas por comando de gestión programado (cron) | aceptada | planificada |
| [0008](0008-contrato-api-v1.md) | API v1 con `JsonResponse`, error anidado y sin `DELETE` | aceptada | parcial |
| [0009](0009-configuracion-carrera.md) | Configuración por carrera con horas copiadas a la práctica | aceptada | parcial |

## Cómo leer el estado

- **Estado** dice si la decisión fue adoptada: `aceptada`, `propuesta` o `reemplazada`. Se toma solo de una fuente que la adopte explícitamente (constitución, research resuelto, arquitectura o contrato).
- **Implementación** es independiente del estado: `actual`, `parcial` o `planificada`. Una decisión aceptada puede no estar implementada, y una implementación de demostración no acepta la decisión para producción.
- **Procedencia**: los ADR se documentaron retrospectivamente. Cada uno indica su fecha de registro y no inventa una fecha histórica de adopción, aprobación humana ni infraestructura futura.

## Fuera de este registro

- Evidencias con `FileField` (solo PDF, máximo 5 MB, versionadas) y escala del MVP (5 carreras, ~300 estudiantes, ~150 prácticas activas): siguen en [research.md](../../specs/001-seguimiento-practicas/research.md), Temas 5 y escala resuelta.
- Requisitos, matriz de permisos y transiciones: [spec.md](../../specs/001-seguimiento-practicas/spec.md) y [data-model.md](../../specs/001-seguimiento-practicas/data-model.md).
- Contrato HTTP vigente y su alcance de demostración: [docs/api.md](../api.md).
