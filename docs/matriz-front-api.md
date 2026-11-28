# Matriz Front–API

Cruce de cada pantalla de [`mapa-pantallas.md`](mapa-pantallas.md) con el endpoint de la API que la sirve. Estado al 2026-11-25 sobre `develop`, con la cadena de reportes (#123, #125, #127) ya mergeada.

**Estado:** **D** existe en `develop` · **PR #129** en revisión · **FALTA** no hay endpoint real (los de `/prototipo/api/v1/` son demo con `X-Rol` y no cuentan).

## Transversal

| Aspecto | Situación |
|---|---|
| Autenticación (ADR-0011) | JWT con `Authorization: Bearer`; access 15 min, refresh 30 min con rotación y blacklist. `POST /api/v1/auth/token/`, `/auth/token/refresh/`, `/auth/logout/`: **D** |
| Usuario actual | `GET /api/v1/me/` (rol, nombre, carrera) para el menú por rol: **PR #129** |
| Sobre de respuesta (ADR-0012) | `{success, message, data, errors, meta}`; el código de máquina va en `errors.code`: **D** |
| OpenAPI | Generado en `/api/v1/schema/` y `/api/v1/docs/`; no hay esquema versionado en el repo |
| CORS | No configurado. Solo hace falta si el front se sirve desde otro origen |

## Por pantalla

| Pantalla | Necesidad | Endpoint | Estado |
|---|---|---|---|
| E1 | Lista de mis prácticas | `GET /api/v1/practicas/` | D |
| E2 cabecera | Estado, tipo, subtipo, horas requeridas | `GET /api/v1/practicas/<id>/` | D |
| E2 cabecera | Entidad, tutores, período | (no está en la respuesta del detalle) | FALTA |
| E2 Resumen | Horas validadas, en revisión, requeridas | `GET /api/v1/practicas/<id>/horas/` | D (#127) |
| E2 Reportes | Reportes por semana | `GET /api/v1/practicas/<id>/reportes/` (detalle ampliado de cada reporte, por semana, sin paginar; alcance de filas, 404 fuera de él) | PR #157 |
| E2 Plan, E3 | Ver y enviar el plan | `GET/POST /api/v1/practicas/<id>/plan/` | PR #129 |
| E2 Informe, E6 | Ver y enviar el informe final | `…/informe-final/` | FALTA |
| E4 | Crear reporte semanal | `POST /api/v1/practicas/<id>/reportes/` | D (JSON legado); PR #157 suma `multipart/form-data` con `actividades` y `evidencias` (uno o más PDF ≤ 5 MB, RNF-05) |
| E5 | Detalle del reporte con observación | `GET /api/v1/reportes/<id>/` | PR #157 (`devolucion` legada más `actividades`, `version`, `evidencias` con su ruta `descarga` y el historial `devoluciones`) |
| E5 | Descargar evidencia PDF | `GET /api/v1/reportes/<id>/evidencias/<evidencia_id>/` (`application/pdf` adjunto; sin URL pública; fuera de alcance o archivo ausente, el mismo 404) | PR #157 |
| E5 | Reenviar reporte devuelto | `POST /api/v1/reportes/<id>/reenviar/` | D (#125, sin cuerpo); PR #157 suma `multipart/form-data` con `evidencias` como la versión siguiente |
| T1 | Cola de pendientes | `GET /api/v1/pendientes/` | D (#123, solo reportes de prácticas en curso) |
| T2 | Validar / devolver reporte | `POST /api/v1/reportes/<id>/validar/`, `/devolver/` | D (#123) |
| T2 | Aprobar / devolver plan | `POST /api/v1/planes/<id>/aprobar/`, `/devolver/` | PR #129 |
| T2 | Validar / devolver informe | (sin modelo) | FALTA |
| T3 | Mis tutorados | `GET /api/v1/practicas/` (filtrado por tutor) | D |
| T4, C3 | Detalle de práctica | `GET /api/v1/practicas/<id>/` | D |
| T5 | Evaluación final | (sin modelo) | FALTA |
| R1 | Mis practicantes | `GET /api/v1/practicas/` (tutor de entidad) | D |
| R2, R3 | Reportes por confirmar, confirmar | — | FALTA |
| R4, R5 | Informe externo, incumplimiento | (sin modelo) | FALTA |
| C1 | Prácticas de la carrera con filtros | `GET /api/v1/practicas/` | D (sin filtros RF-06) |
| C2 | Alertas | solo prototipo | FALTA |
| C3 | Historial de estados | solo prototipo (`HistorialEstado` existe) | FALTA |
| C3, C5 | Suspender, reanudar, cancelar | servicio `cambiar_estado_practica` sin vista | FALTA |
| C4 | Cerrar práctica | solo prototipo | FALTA |
| C6, A1, A2 | Consolidado y CSV | — | FALTA |
| C7 | Configuración de carrera | modelo `ConfiguracionCarrera` sin API | FALTA |
| N1, N2 | Entidades y convenios | modelo `EntidadReceptora` sin API | FALTA |
| — | Asignar práctica y tutor | servicio `asignar_practica` sin vista | FALTA |

## Brechas, por lo que desbloquean

1. **`GET /api/v1/me/`** (`usuarios`): lo necesita cualquier front para saber el rol tras el login.
2. **Plan de actividades** (`actividades`): los servicios `enviar_plan`, `devolver_plan` y `aprobar_plan` ya existen. La aprobación del plan pone la práctica en curso; sin ella E4 responde 409 `practica_no_en_curso`.
3. **Lecturas de E2**: detalle con entidad, tutores y período; lista de reportes; detalle de reporte.
4. **Estado de la práctica** (C3, C4): servicios ya existentes sin vista.
5. **Ampliar `/pendientes/`** con planes e informes.
6. **Sin modelo ni servicio todavía**: informes, evaluación final, confirmación de la entidad, incumplimientos, alertas, consolidado, configuración de carrera, catálogo de entidades.
