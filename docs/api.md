# API base v1 — contrato

**Fecha**: 2026-10-21 | **Estado**: contrato adoptado | **Arquitectura**: [docs/arquitectura.md](arquitectura.md) (monolito modular, DTO, Facade)

**Alcance actual: demostración con datos sintéticos, solo con `DEBUG=True`.** `X-Rol` selecciona una persona de ejemplo y no autentica usuarios. No hay base de datos ni RBAC de producción en este incremento: los reportes enviados viven solo en la sesión del navegador o cliente que los envía (§5) y las decisiones de validación en una cookie firmada del mismo navegador (§6). Con `DEBUG=False` los endpoints devuelven `404`, incluso con ese header.

El API del prototipo sirve JSON con `JsonResponse` de Django — el mismo patrón del endpoint `/health/` — **sin Django REST Framework** (decisión de [research.md](../specs/001-seguimiento-practicas/research.md), Tema 1). Los prototipos de pantalla la incorporan progresivamente: cada aporte entrega una funcionalidad nueva con su endpoint, sus tests y su uso en las pantallas.

## 1. Convenciones

| Regla | Detalle |
| --- | --- |
| Base | `/api/v1/` (versionada: los cambios de contrato que rompen clientes van a `/api/v2/`, nunca se muta v1) |
| Formato | Respuestas de las vistas API: `application/json`. Una URL sin ruta coincidente (p. ej. ID `abc` o negativo) y el bloqueo con `DEBUG=False` usan el `404` HTML de Django. |
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
| `400` | `solicitud_malformada` | El cuerpo leído no es JSON válido ni un objeto JSON |
| `401` | `sin_sesion` | Falta identidad (sin `X-Rol` en prototipo / sin sesión en real) |
| `403` | `fuera_de_rol` | La acción o el recurso no corresponden al rol (RNF-02): nunca se altera nada |
| `404` | `recurso_inexistente` | El recurso no existe; el prototipo devuelve `403` para una práctica existente ajena al rol |
| `405` | `metodo_no_permitido` | Cada endpoint admite un solo método (`GET` en las consultas de prácticas, `POST` en reportes y `PATCH` en `/pendientes/<clave>/`); los demás, incluidos `HEAD`/`OPTIONS`, se rechazan con `Allow` indicando el permitido. `HEAD` no lleva cuerpo. |
| `409` | `transicion_invalida` | La transición de estado no está en la tabla (RF-09, RF-13); p. ej. validar lo ya cerrado, cerrar sin requisitos |
| `422` | `dato_invalido` | JSON válido que viola una regla: evidencia > 5 MB o no PDF (RNF-05), ayudantía > 10 h (RF-15, Art. 341), devolución sin observación |
| `500` | `error_interno` | Error no previsto; sin detalles internos |

## 3. Recursos y aportes

Cada aporte entrega **una funcionalidad nueva** con: endpoint, tests (test-first) y su incorporación en las pantallas del prototipo (o la creación de las vistas que falten, con el estilo del #48).

| Aporte (orden) | Funcionalidad | Endpoints | Pantallas donde se incorpora |
| --- | --- | --- | --- |
| 1 — **API base + consulta de prácticas** (Jaime) | Consultar prácticas, estado y horas por rol (HU-04, HU-05) en JSON | `GET /api/v1/practicas/` · `GET /api/v1/practicas/<id>/` | Índice `/prototipo/` (nuevo: lista pantallas + API v1) |
| 2 — **Validaciones** (Ivett) | Validar o devolver planes/reportes/informes con observación (RF-03, RF-04) | `PATCH /api/v1/pendientes/<clave>/` | T2 (Revisar): muestra bajo el formulario el JSON de la respuesta; sin observación → `422` · **implementado (#60)**, ver §6 |
| 3 — **Alertas y cierre** (Melissa) | Alertas activas del actor (RF-07) y cierre con guard (RF-09) | `GET /api/v1/alertas/` · `POST /api/v1/practicas/<id>/cierre/` | C2 (Alertas): contador del badge; C4 (Cerrar): el guard responde qué falta |
| 4 — **Historial y legalización** (Doménica) | Historial inalterable (RF-10, HU-09) y marcaje de anexos (RF-04) | `GET /api/v1/practicas/<id>/historial/` · `POST /api/v1/anexos/<id>/legalizacion/` | D2 (detalle del director): pestaña de historial; S2 (Secretaría) |
| 5 — **Reportes semanales** (Alejandro, #64) | Enviar actividades, horas y evidencias; conservar versiones (RF-03, RF-15, RNF-05) | `POST /api/v1/practicas/<id>/reportes/` | E4 (Nuevo reporte semanal) |

## 4. Consulta implementada (Jaime, #63)

```bash
make run
curl -H 'X-Rol: estudiante' http://127.0.0.1:8000/api/v1/practicas/
curl -H 'X-Rol: estudiante' http://127.0.0.1:8000/api/v1/practicas/1/
```

El listado responde `{"practicas": [...]}`; el detalle contiene el DTO de una práctica, con plan y reportes explícitamente proyectados, fechas ISO y horas numéricas. La persona sintética se fija por cada rol, no por un usuario enviado por el cliente. `/prototipo/` permite consultar esta lista con el selector de rol. La consulta incluye los reportes que la misma sesión envió (§5). El endpoint del orden 2 está implementado (§6); los de los órdenes 3 y 4 son **planificados**, no implementados todavía. Códigos actuales: `200`, `401`, `403`, `404` y `405`.

## 5. Envío de reportes semanales implementado (Alejandro, #64)

`POST /api/v1/practicas/<id>/reportes/` recibe `multipart/form-data` con `semana`, `actividades` (una por línea), `horas` y uno o más `evidencias`. Usa el mismo caso de uso de la fachada (`registrar_reporte`) que el formulario E4, así que las reglas son las mismas en ambos.

| Respuesta | Cuándo |
| --- | --- |
| `201` + `{"reporte": {...}}` y `Location: /api/v1/practicas/<id>/` | Reporte válido: queda `en_revision`, enviado el día de la demo, y suma a `horas_en_revision` |
| `401 sin_sesion` | Sin `X-Rol` o con un rol desconocido |
| `403 fuera_de_rol` | Un rol distinto de `estudiante`, o una práctica de otro estudiante |
| `404 recurso_inexistente` | La práctica no existe |
| `405 metodo_no_permitido` | Cualquier método distinto de `POST`; `Allow: POST` |
| `409 transicion_invalida` | La semana ya tiene un reporte en revisión o validado, o el plan no está aprobado |
| `422 dato_invalido` | Falta un campo, la semana no está disponible, horas < 1, ayudantía > 10 h (Art. 341), un archivo que no es PDF o pesa más de 5 MB (RNF-05). `error.campos` lista los mensajes por campo |

- **Rechazo sin efectos**: ante cualquier error no cambia nada, ni el reporte ni los contadores de horas.
- **Reenvío**: solo una semana `devuelto` se puede volver a enviar. El reporte nuevo trae en `versiones` la versión anterior con su observación, quién la devolvió y cuándo; nada se borra (RF-10).
- **Alcance del estado simulado**: lo enviado se guarda solo en la sesión Django de ese cliente. No hay escrituras compartidas: otro navegador ve los datos de ejemplo. Las evidencias no se almacenan, solo se registra su nombre. El estado se reinicia con el botón «Reiniciar demo» de E2 (`POST /prototipo/reiniciar-demo/`), al borrar la cookie o al terminar la sesión. `make run` aplica `migrate` porque las sesiones viven en la base local. La bandeja de revisión del tutor (T1) sigue mostrando los datos de ejemplo: un reporte enviado por este endpoint o por E4 no aparece allí ni se puede decidir con este API.
- **CSRF**: como el estado depende de la cookie de sesión, el `POST` exige el token CSRF de Django.

```bash
make run
curl -s -c jar http://127.0.0.1:8000/prototipo/reporte-semanal/nuevo/ -o /dev/null
TOKEN=$(awk '$6=="csrftoken"{print $7}' jar)
curl -b jar -c jar -H 'X-Rol: estudiante' -H "X-CSRFToken: $TOKEN" \
  -F semana=9 -F horas=10 -F 'actividades=Calificación de talleres' -F evidencias=@evidencia.pdf \
  http://127.0.0.1:8000/api/v1/practicas/1/reportes/
curl -b jar -H 'X-Rol: estudiante' http://127.0.0.1:8000/api/v1/practicas/1/
```

## 6. Validaciones implementadas (Ivett, #60)

```bash
curl -X PATCH -H 'X-Rol: tutor_academico' -H 'Content-Type: application/json' \
  -d '{"decision": "devuelto", "observacion": "Falta la firma"}' \
  http://127.0.0.1:8000/api/v1/pendientes/reporte-1-8/
```

`PATCH /api/v1/pendientes/<clave>/` — solo el rol `tutor_academico` y solo sobre documentos de sus prácticas. La `<clave>` es la de T2: `plan-<id>`, `reporte-<id>-<semana>` o `informe-<id>`.

| Campo del cuerpo | Regla |
| --- | --- |
| `decision` | Obligatorio: `aprobado` (el documento pasa a `validado`) o `devuelto` (pasa a `devuelto`) |
| `observacion` | Obligatoria solo con `devuelto`: texto no vacío de hasta 500 caracteres; con `aprobado` se ignora |

`200` devuelve el documento decidido (`clave`, `tipo`, `titulo`, `practica_id`, `estado`, `validado_por`, `validado_el`, `observacion`, …). Orden de las comprobaciones, la primera que falla responde: `404` (sin `DEBUG`) → `405` (`Allow: PATCH`) → `401` → `403` (otro rol) → `404` (clave inexistente) → `403` (documento de otro tutor) → `409` (ya no está en revisión o ya se decidió; incluye `recurso`) → `400` → `422`. Una petición rechazada nunca altera el estado.

**Persistencia de la demo.** La decisión se guarda en la cookie firmada `prototipo_validaciones` (24 h, `Path=/`, sin base de datos), compartida por el API y la pantalla T2: una decisión tomada en uno se ve en el otro, y repetirla responde `409`. No se muta el ejemplo compartido y nunca se elimina nada (RF-10). Si la cookie alcanza su límite, el API responde `500` `error_interno`. T1 oculta los pendientes ya decididos.

**Límites de la demo.** Este `PATCH` está marcado `csrf_exempt` y limitado a datos sintéticos con `DEBUG=True`; no ofrece autenticación ni protección CSRF de producción. La exención solo cubre este endpoint y las demás vistas conservan su protección. El overlay de decisiones afecta T1/T2 y este API en el mismo navegador, no actualiza las horas de `GET /api/v1/practicas/<id>/` ni comunica decisiones a otro navegador. La cookie firmada tampoco reemplaza una identidad autenticada; no usar este diseño con datos reales.

## 7. Estilo de las vistas del API

- Vistas finas: llaman a la **fachada** y traducen el resultado (o su error) al contrato JSON; sin reglas de negocio.
- Los **DTO** definen la forma exacta de cada payload; el dominio interno nunca sale crudo.
- Cada transición pasa por la **tabla de estados**: lo no listado es `409`, lo inválido es `422`, lo ajeno al rol es `403`.
- Tests `test-first`: el test del contrato se escribe antes que la vista y falla primero (RED → GREEN), igual que la suite de pantallas.
