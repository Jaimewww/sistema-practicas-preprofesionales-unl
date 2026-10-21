# API base v1 — contrato

**Fecha**: 2026-10-21 | **Estado**: contrato adoptado | **Arquitectura**: [docs/arquitectura.md](arquitectura.md) (monolito modular, DTO, Facade)

El API del sistema sirve JSON con `JsonResponse` de Django — el mismo patrón del endpoint `/health/` — **sin Django REST Framework** (decisión de [research.md](../specs/001-seguimiento-practicas/research.md), Tema 1). Los prototipos de pantalla la incorporan progresivamente: cada aporte entrega una funcionalidad nueva con su endpoint, sus tests y su uso en las pantallas.

## 1. Convenciones

| Regla | Detalle |
| --- | --- |
| Base | `/api/v1/` (versionada: los cambios de contrato que rompen clientes van a `/api/v2/`, nunca se muta v1) |
| Formato | `application/json` en solicitud y respuesta (`Content-Type`) |
| Identidad y rol | **Prototipo**: el rol se emula con el header `X-Rol` (`estudiante`, `tutor_academico`, `tutor_entidad`, `coordinador`); sin header → `401`. **Implementación real**: sesión Django (RNF-01); `Authorization: Bearer` queda reservado para integraciones (RNF-11). |
| Aislamiento | La fachada filtra por rol, carrera y practicantes asignados (RF-11); el filtrado se aplica en la consulta, no en la vista |
| Escritura | `POST` crea, `PUT` reemplaza, `PATCH` cambia parcialmente; **no existe `DELETE`** (RF-10: el historial es inalterable; se cancela o devuelve) |
| Idempotencia | `GET`/`PUT` idempotentes; `POST` no |

## 2. Contrato de errores (JSON)

```json
{
  "error": {
    "code": "transicion_invalida",
    "message": "No se puede validar un reporte ya cerrado.",
    "recurso": "/api/v1/reportes/31/"
  }
}
```

| HTTP | `code` | Cuándo |
| --- | --- | --- |
| `400` | `solicitud_malformada` | JSON no parsea; el servidor ni lee el cuerpo |
| `401` | `sin_sesion` | Falta identidad (sin `X-Rol` en prototipo / sin sesión en real) |
| `403` | `fuera_de_rol` | La acción o el recurso no corresponden al rol (RNF-02): nunca se altera nada |
| `404` | `recurso_inexistente` | No existe o está fuera del alcance del actor |
| `409` | `transicion_invalida` | La transición de estado no está en la tabla (RF-09, RF-13); p. ej. validar lo ya cerrado, cerrar sin requisitos |
| `422` | `dato_invalido` | JSON válido que viola una regla: evidencia > 5 MB o no PDF (RNF-05), ayudantía > 10 h (RF-15, Art. 341), devolución sin observación |
| `500` | `error_interno` | Error no previsto; sin detalles internos |

## 3. Recursos y aportes

Cada aporte entrega **una funcionalidad nueva** con: endpoint, tests (test-first) y su incorporación en las pantallas del prototipo (o la creación de las vistas que falten, con el estilo del #48).

| Aporte (orden) | Funcionalidad | Endpoints | Pantallas donde se incorpora |
| --- | --- | --- | --- |
| 1 — **API base + consulta de prácticas** (Jaime) | Consultar prácticas, estado y horas por rol (HU-04, HU-05) en JSON | `GET /api/v1/practicas/` · `GET /api/v1/practicas/<id>/` | Índice `/prototipo/` (nuevo: lista pantallas + API v1) |
| 2 — **Validaciones** (Ivett) | Validar o devolver planes/reportes/informes con observación (RF-03, RF-04) | `PATCH /api/v1/pendientes/<clave>/` | T2 (Revisar): la acción responde JSON; sin observación → `422` |
| 3 — **Alertas y cierre** (Melissa) | Alertas activas del actor (RF-07) y cierre con guard (RF-09) | `GET /api/v1/alertas/` · `POST /api/v1/practicas/<id>/cierre/` | C2 (Alertas): contador del badge; C4 (Cerrar): el guard responde qué falta |
| 4 — **Historial y legalización** (Doménica) | Historial inalterable (RF-10, HU-09) y marcaje de anexos (RF-04) | `GET /api/v1/practicas/<id>/historial/` · `POST /api/v1/anexos/<id>/legalizacion/` | D2 (detalle del director): pestaña de historial; S2 (Secretaría) |

## 4. Estilo de las vistas del API

- Vistas finas: llaman a la **fachada** y traducen el resultado (o su error) al contrato JSON; sin reglas de negocio.
- Los **DTO** definen la forma exacta de cada payload; el dominio interno nunca sale crudo.
- Cada transición pasa por la **tabla de estados**: lo no listado es `409`, lo inválido es `422`, lo ajeno al rol es `403`.
- Tests `test-first`: el test del contrato se escribe antes que la vista y falla primero (RED → GREEN), igual que la suite de pantallas.
