# API base v1 — contrato

**Fecha**: 2026-10-21 | **Estado**: contrato adoptado | **Arquitectura**: [docs/arquitectura.md](arquitectura.md) (monolito modular, DTO, Facade)

**Alcance actual: demostración con datos sintéticos, solo con `DEBUG=True`.** `X-Rol` selecciona una persona de ejemplo y no autentica usuarios. No hay base de datos ni RBAC de producción en este incremento: los reportes del demo (E4, formulario del prototipo) viven solo en la sesión del navegador que los envía —el endpoint real de reportes de §5 sí persiste en la base—, las decisiones de validación en una cookie firmada del mismo navegador (§6), los cambios del coordinador en otra (§8) y las legalizaciones de la Secretaría en una tercera (§9). Con `DEBUG=False` los endpoints devuelven `404`, incluso con ese header.

El API del prototipo sirve JSON con `JsonResponse` de Django — el mismo patrón del endpoint `/health/` — **sin Django REST Framework** (decisión de [research.md](../specs/001-seguimiento-practicas/research.md), Tema 1). Los prototipos de pantalla la incorporan progresivamente: cada aporte entrega una funcionalidad nueva con su endpoint, sus tests y su uso en las pantallas.

## 1. Convenciones

| Regla | Detalle |
| --- | --- |
| Base | `/api/v1/` (versionada: los cambios de contrato que rompen clientes van a `/api/v2/`, nunca se muta v1) |
| Formato | Respuestas de las vistas API: `application/json`. Una URL sin ruta coincidente (p. ej. ID `abc` o negativo) y el bloqueo con `DEBUG=False` usan el `404` HTML de Django. |
| Identidad y rol | **Prototipo**: el rol se emula con el header `X-Rol` (`estudiante`, `tutor_academico`, `tutor_entidad`, `coordinador`); sin header → `401`. El historial (§9.1) acepta además `director` y la legalización (§9.2) `secretaria`, solo en esas rutas: en las anteriores esos dos valores siguen respondiendo `401`. **Implementación real**: sesión Django (RNF-01); `Authorization: Bearer` queda reservado para integraciones (RNF-11). |
| Aislamiento | La fachada filtra por rol, carrera y practicantes asignados (RF-11); el filtrado se aplica en la consulta, no en la vista |
| Escritura | `POST` crea, `PUT` reemplaza, `PATCH` cambia parcialmente; **no existe `DELETE`** (RF-10: el historial es inalterable; se cancela o devuelve) |
| Idempotencia | `GET`/`PUT` idempotentes; `POST` no |

## 2. Contrato de errores (JSON)

Todo error de la API DRF (`/api/v1/`, [ADR 0012](adr/0012-contrato-universal-de-respuesta.md)) usa el envelope universal; el código de máquina vive en `errors.code`:

```json
{
  "success": false,
  "message": "Solicitud inválida.",
  "data": null,
  "errors": {
    "detail": "No se puede validar un reporte ya cerrado.",
    "code": "transicion_invalida"
  },
  "meta": {}
}
```

- `errors.code` es un identificador estable y legible por máquina: el cliente decide con él, no con el texto de `detail`.
- La validación por campos es la excepción: `400` con `errors = {campo: [textos]}` y `message: "Datos inválidos."`, sin `code`.
- `401` y `404` son genéricos a propósito (no revelan el motivo de la autenticación ni si el recurso existe). `403` y el resto de `APIException` conservan el `detail` que escribió el servidor.
- El `500` nunca expone trazas ni datos internos (`detail` genérico, `code: error_interno`).
- El handler marca la transacción para rollback (`set_rollback`) en toda respuesta de error.

| HTTP | `errors.code` | `message` | Cuándo |
| --- | --- | --- | --- |
| `400` | — (`{campo: [textos]}`) | `Datos inválidos.` | Validación por campo |
| `400` | `parse_error` (antes `solicitud_malformada`) | `Solicitud inválida.` | El cuerpo leído no es JSON válido ni un objeto JSON |
| `401` | `no_autenticado` (antes `sin_sesion`) | `Autenticación requerida.` | Falta identidad (sin sesión/token) o el usuario está inactivo o no guardado; detalle genérico |
| `403` | `permiso_denegado` (antes `fuera_de_rol`) | `Permiso denegado.` | La acción o el recurso no corresponden al rol (RNF-02): nunca se altera nada |
| `404` | `no_encontrado` (antes `recurso_inexistente`) | `Recurso no encontrado.` | El recurso no existe o no es visible para el actor; detalle genérico. En `POST …/reportes/` la práctica inexistente y la de otro estudiante responden idéntico |
| `405` | `method_not_allowed` (antes `metodo_no_permitido`) | `Solicitud inválida.` | Método no admitido; `Allow` indica el permitido. `HEAD` no lleva cuerpo |
| `409` | `transicion_invalida` (u otro código propio) | `Solicitud inválida.` | La transición de estado no está en la tabla (RF-09, RF-13); p. ej. validar lo ya cerrado, cerrar sin requisitos |
| `409` | `practica_no_en_curso` | `Solicitud inválida.` | `POST …/reportes/` sobre una práctica que no está «en curso» (asignada, suspendida, en revisión final, cerrada o cancelada) |
| `409` | `semana_duplicada` | `Solicitud inválida.` | `POST …/reportes/` de una semana que ya tiene reporte |
| `422` | `dato_invalido` | `Solicitud inválida.` | Solo en las rutas del prototipo: JSON válido que viola una regla de negocio (evidencia > 5 MB o no PDF, RNF-05; devolución sin observación). En la API DRF la ayudantía > 10 h (RF-15, Art. 341) es `400` por campo |
| `500` | `error_interno` | `Error interno del servidor.` | Error no previsto; sin detalles internos |

Los códigos de dominio (`transicion_invalida`, `dato_invalido`, …) son el `default_code` de la `APIException` correspondiente y se conservan tal cual en `errors.code`.

> **Rutas del prototipo.** #101 (#78) sustituyó por vistas DRF con el envelope las tres rutas de práctica: `GET /api/v1/practicas/`, `GET /api/v1/practicas/<id>/` y `POST /api/v1/practicas/<id>/reportes/` (§4 y §5). Las **rutas retiradas del demo** son esas tres: ya no existen como vistas de Django plano ni aceptan `X-Rol`. Las demás rutas de `/api/v1/` (alertas y cierre §8, historial y legalización §9, y `PATCH …/pendientes/<clave>/` §6) siguen siendo vistas de Django plano con `X-Rol` y responden la forma anterior `{"error": {"code", "message", "recurso"}}` con los códigos antiguos (`sin_sesion`, `fuera_de_rol`, `recurso_inexistente`, `solicitud_malformada`, `metodo_no_permitido`, `transicion_invalida`, `dato_invalido`, `error_interno`) hasta que se migren. Los ejemplos y tablas de §6–§9 describen ese prototipo; las tres rutas reales viven en §4 y §5.

## 3. Recursos y aportes

Cada aporte entrega **una funcionalidad nueva** con: endpoint, tests (test-first) y su incorporación en las pantallas del prototipo (o la creación de las vistas que falten, con el estilo del #48).

| Aporte (orden) | Funcionalidad | Endpoints | Pantallas donde se incorpora |
| --- | --- | --- | --- |
| 1 — **API base + consulta de prácticas** (Jaime) | Consultar prácticas, estado y horas por rol (HU-04, HU-05) en JSON | `GET /api/v1/practicas/` · `GET /api/v1/practicas/<id>/` | Índice `/prototipo/` (nuevo: lista pantallas + API v1) · **real desde #101 (#78), ver §4** |
| 2 — **Validaciones** (Ivett) | Validar o devolver planes/reportes/informes con observación (RF-03, RF-04) | `PATCH /api/v1/pendientes/<clave>/` | T2 (Revisar): muestra bajo el formulario el JSON de la respuesta; sin observación → `422` · **implementado (#60)**, ver §6 |
| 3 — **Alertas y cierre** (Melissa) | Alertas activas del actor (RF-07) y cierre con guard (RF-09) | `GET /api/v1/alertas/` · `POST /api/v1/practicas/<id>/cierre/` | C2 (Alertas): contador del badge; C4 (Cerrar): el guard responde qué falta |
| 4 — **Historial y legalización** (Doménica) | Historial inalterable (RF-10, HU-09) y marcaje de anexos (RF-04) | `GET /api/v1/practicas/<id>/historial/` · `POST /api/v1/anexos/<id>/legalizacion/` | D2 (detalle del director): pestaña de historial; S2 (Secretaría) · **implementado (#62), ver §9** |
| 5 — **Reportes semanales** (Alejandro, #64) | Registrar horas por semana (RF-02, RF-15). Evidencias PDF (RNF-05) y versiones: **pendientes**. **Real desde #101 (#78), ver §5**; el demo con evidencias (#67) se retiró | `POST /api/v1/practicas/<id>/reportes/` | E4 (Nuevo reporte semanal) |

## 4. Consulta de prácticas (#101, #78)

`GET /api/v1/practicas/` y `GET /api/v1/practicas/<id>/` son vistas DRF reales (ya no el demo con `X-Rol`): leen la base y devuelven el envelope de §2. Cada actor ve solo las filas de su alcance (RF-11, `practicas_visibles_para`): el estudiante sus prácticas, el tutor académico las que tiene asignadas, el tutor de la entidad las laborales vinculadas, y coordinador, director y secretaría las de su carrera. Un actor anónimo, inactivo o no guardado no ve ninguna fila.

| Respuesta | Cuándo |
| --- | --- |
| `200` + `data` con la lista de tarjetas | Lista; vacía si el actor no ve ninguna |
| `200` + `data` con una tarjeta (`id`, `estudiante_id`, `tipo`, `subtipo`, `estado`, `horas_requeridas`) | Detalle de una práctica visible |
| `404 no_encontrado` | El detalle no existe **o** está fuera del alcance del actor; las dos respuestas son idénticas |

El contrato queda en `/api/v1/schema/` y `/api/v1/docs/` (Swagger), con 200 y 404 documentados para el detalle. Las rutas de demo equivalentes (lista y detalle con `{"practicas": [...]}`) **se retiraron**.

## 5. Registro de reportes semanales (#101, #78)

`POST /api/v1/practicas/<id>/reportes/` registra el reporte de una semana con `Content-Type: application/json` y exactamente dos campos: `semana` (entero ≥ 1) y `horas_reportadas` (entero de 1 a 168). Cualquier otro campo —incluidos los que fija el servidor, `estado` y `requiere_revision`— se rechaza con `400` en su clave. La ruta de demo con `multipart/form-data`, `actividades`, `horas` y `evidencias` **se retiró**.

El servidor decide en este orden y no escribe nada hasta el final; la práctica se busca dentro de una transacción con `select_for_update` para que dos envíos simultáneos no se crucen:

| Respuesta | `errors.code` | Cuándo |
| --- | --- | --- |
| `201` + el reporte | — | Reporte válido: nace `en_revision`, con `requiere_revision` |
| `401` | `no_autenticado` | Sin actor autenticado, o actor inactivo o no guardado |
| `403` | `permiso_denegado` | El actor no es estudiante (tutor, coordinador, etc.) |
| `404` | `no_encontrado` | La práctica no existe **o** es de otro estudiante: respuesta idéntica, sin revelar existencia |
| `409` | `practica_no_en_curso` | La práctica no está «en curso» (asignada, suspendida, en revisión final, cerrada o cancelada); «en curso» implica plan aprobado |
| `400` | — (`{campo: [textos]}`) | Cuerpo que no es objeto (`non_field_errors`), campo no admitido, `semana` u `horas_reportadas` < 1, horas > 168, ayudantía > 10 h (Art. 341) |
| `409` | `semana_duplicada` | La semana ya tiene un reporte (también cuando la restricción única de la base atrapa una carrera entre dos envíos) |

- **`requiere_revision`**: `true` cuando `horas_reportadas` > 40 (se identifica para revisión del tutor, spec escenario S5); la ayudantía ≤ 10 h nunca lo activa. Se calcula en el servidor.
- **Respuesta `201`**: `data` = `{id, practica_id, semana, horas_reportadas, estado, requiere_revision, fecha_registro}`.
- **Rechazo sin efectos**: ningún error cambia filas ni contadores.
- **Pendiente (RNF-05)**: la subida de evidencias PDF (≤ 5 MB), los textos de actividades y las versiones del reporte no existen aún en este endpoint; quedan como pendiente explícito (ver [docs/revisiones/cadena-jaime.md](revisiones/cadena-jaime.md), «#101»).

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"semana": 3, "horas_reportadas": 12}' \
  http://127.0.0.1:8000/api/v1/practicas/1/reportes/   # sin autenticación -> 401
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

**Límites de la demo.** Este `PATCH` está marcado `csrf_exempt` y limitado a datos sintéticos con `DEBUG=True`; no ofrece autenticación ni protección CSRF de producción. La exención solo cubre este endpoint y las demás vistas conservan su protección. El overlay de decisiones afecta T1/T2, las horas de consulta API/E2, las pantallas del coordinador, las alertas y el cierre en el mismo navegador; no comunica decisiones a otro navegador. Se aplica a los documentos originales antes de los reenvíos de sesión, para no decidir automáticamente una versión nueva. La cookie firmada tampoco reemplaza una identidad autenticada; no usar este diseño con datos reales.

## 7. Estilo de las vistas del API

- Vistas finas: llaman a la **fachada** y traducen el resultado (o su error) al contrato JSON; sin reglas de negocio.
- Los **DTO** definen la forma exacta de cada payload; el dominio interno nunca sale crudo.
- Cada transición pasa por la **tabla de estados**: lo no listado es `409`, lo inválido es `422`, lo ajeno al rol es `403`.
- Tests `test-first`: el test del contrato se escribe antes que la vista y falla primero (RED → GREEN), igual que la suite de pantallas.

## 8. Alertas y cierre implementados (Melissa, #61)

`GET /api/v1/alertas/` devuelve `{"count": N, "alertas": [...]}`. El filtro opcional `?tipo=rezago` limita la lista; `count` conserva el total activo del actor. Un tipo desconocido devuelve una lista vacía. Cada alerta proyecta `tipo`, `tipo_display`, `estado_badge`, `detalle`, `fecha` ISO y `practica` (`id`, `estudiante`, `tipo`, `tipo_display`, `carrera`, `url` API y `detalle_url` de pantalla). Nunca se serializa la referencia circular del dominio.

| Persona sintética | Alertas recibidas |
| --- | --- |
| Estudiante | Reportes vencidos y rezago de sus prácticas |
| Tutor académico | Reportes vencidos, revisión vencida, rezago e incumplimientos de sus tutorados |
| Coordinador | Todas las alertas de su carrera, incluidas las prácticas sintéticas adicionales |
| Tutor de entidad | Lista vacía: estos requisitos no le asignan notificaciones |

Se reutilizan los plazos configurables: reporte vencido después de 3 días naturales por defecto; revisión después de 5 días hábiles; rezago si horas validadas + en revisión quedan por debajo del mínimo configurado (80 % de las horas esperadas). Las fechas son las de la demo (`HOY`), no las del reloj real. Suspendidas, canceladas y cerradas no generan alertas. Las decisiones del tutor eliminan revisiones vencidas y actualizan horas antes de generar alertas.

`POST /api/v1/practicas/<id>/cierre/` no requiere cuerpo. Solo el coordinador de la carrera cierra desde `en_revision_final`, con el 100 % de horas **validadas**, informe del estudiante validado, informe externo y evaluación. Para comunitaria se exige el informe del proyecto de vinculación. La respuesta `200` es el DTO de la práctica cerrada y conserva el resultado de evaluación: 69 % es «no aprobada»; 70 % es «aprobada». El historial añade autor, fecha y motivo una sola vez.

```json
{
  "error": {
    "code": "transicion_invalida",
    "message": "No se puede cerrar: falta La evaluación final registrada.",
    "recurso": "/api/v1/practicas/7/cierre/",
    "faltante": ["La evaluación final registrada"]
  }
}
```

Un requisito pendiente, estado incorrecto o cierre repetido devuelve `409` sin cambios. `faltante` es una lista vacía cuando solo falla el estado de origen. El contrato anidado de §2 prevalece sobre el ejemplo abreviado del issue. Sin rol o rol desconocido → `401`; otro actor o carrera → `403`; inexistente → `404`; método incorrecto → `405` con `Allow: GET` o `POST`. Con `DEBUG=False` las rutas están bloqueadas.

**CSRF y estado.** El cierre exige token CSRF, igual que el envío de reportes; un rechazo del middleware CSRF usa la respuesta HTML `403` de Django. La cookie firmada `prototipo_coordinador_v2` dura 24 h y usa `Path=/`, `HttpOnly`, `SameSite=Lax` y `Secure` con HTTPS. Las pantallas migran la cookie anterior al recibirla; «Restablecer» elimina la nueva y la anterior en sus respectivos paths. Cookies vencidas o inválidas se ignoran. Si el estado excede 3500 caracteres firmados, el cierre devuelve `500 error_interno` sin publicar cookie ni éxito.

C2 consume JSON para su lista y mantiene el total en el badge y la campana. C4 presenta `error.faltante` y abre el historial tras un cierre exitoso. Las alternativas HTML usan los mismos casos de uso sin llamadas HTTP internas; un error de carga conserva la última consulta y muestra un aviso. El formulario HTML exige confirmar el cierre y mantiene los estados HTTP anteriores de las pantallas.

**Pendiente para otro issue:** persistencia compartida entre usuarios/navegadores, identidad autenticada y almacenamiento de reportes, validaciones y decisiones para el flujo estudiante → tutor → coordinador. Un reporte enviado en un navegador no aparece para un tutor en otro. También queda integrar los envíos nuevos en el catálogo revisable de T1/PATCH (los reportes reales de §5 aún no alimentan ese catálogo); este aporte solo proyecta las decisiones existentes sobre los documentos originales.

Especificación y decisiones: [specs/002-api-alertas-cierre](../specs/002-api-alertas-cierre/plan.md). Verificación: [evidencias](../evidencias/api-alertas-cierre-verificacion.md).

## 9. Historial y legalización implementados (Doménica, #62)

El director de carrera obtiene su historial de solo lectura y la Secretaría legaliza los anexos de cierre. Los dos endpoints reutilizan la fachada, los DTO y el estado firmado de las pantallas; D1/D2 y S1/S2 usan los mismos casos de uso, sin llamadas HTTP internas. Ninguno de los dos amplía el acceso del director ni de la Secretaría a las rutas anteriores (§1, RF-11).

### 9.1 Historial de la práctica (RF-10, HU-09)

```bash
curl -H 'X-Rol: director' http://127.0.0.1:8000/api/v1/practicas/8/historial/
```

`GET /api/v1/practicas/<id>/historial/` responde `{"historial": [...]}`. Cada cambio de estado proyecta `estado_anterior`, `estado_anterior_display`, `estado_nuevo`, `estado_nuevo_display`, `autor`, `fecha` ISO y `motivo`; el orden es el del registro y la última entrada es el estado actual. La primera entrada no tiene estado anterior.

| Respuesta | Cuándo |
| --- | --- |
| `200` | El director o el coordinador consultan una práctica de la carrera |
| `401 sin_sesion` | Sin `X-Rol` o con una persona desconocida |
| `403 fuera_de_rol` | Otro rol (estudiante, tutores, secretaría) o una práctica de otra carrera |
| `404 recurso_inexistente` | La práctica no existe; con `DEBUG=False` también |
| `405 metodo_no_permitido` | Cualquier método distinto de `GET`; `Allow: GET` |

- **Solo lectura**: no existe ruta de escritura; el historial es inalterable (RF-10) y ni un `POST` ni un `DELETE` lo modifican.
- **Estado del navegador**: suma el historial de ejemplo y los cambios del coordinador guardados en la cookie `prototipo_coordinador_v2` (§8) del mismo cliente, así que un cierre o una suspensión hechos aquí aparecen en el historial. Otro navegador ve el historial original.
- **Pantallas**: D2 muestra la pestaña Historial con la misma proyección que el JSON y D1/D2 reconstruyen los cierres de la carrera con ese estado, de modo que un cierre hecho por el coordinador en ese navegador también aparece en sus pantallas. El director no ve la pestaña de acciones ni escribe nada.
- **Alcance**: el director consulta el historial de las prácticas de su carrera; la Secretaría no consulta historial y el coordinador conserva el acceso del #61.

### 9.2 Legalización de anexos (RF-04, HU-09)

```bash
make run
curl -s -c jar http://127.0.0.1:8000/prototipo/secretaria/anexos/802/legalizar/ -o /dev/null
TOKEN=$(awk '$6=="csrftoken"{print $7}' jar)
curl -b jar -c jar -X POST -H 'X-Rol: secretaria' -H "X-CSRFToken: $TOKEN" \
  http://127.0.0.1:8000/api/v1/anexos/802/legalizacion/
```

`POST /api/v1/anexos/<id>/legalizacion/` no requiere cuerpo y responde `200` con el DTO del anexo: `id`, `nombre`, `tipo`, `archivo`, `estado` (`legalizado`), `estado_display`, `legalizado_por` y `legalizado_el`.

| Respuesta | Cuándo |
| --- | --- |
| `200` | Anexo de la carrera legalizado: autor y fecha son los de la demo |
| `401 sin_sesion` | Sin `X-Rol` o con una persona desconocida |
| `403 fuera_de_rol` | Un rol distinto de `secretaria`, o un anexo de otra carrera |
| `404 recurso_inexistente` | El anexo no existe; con `DEBUG=False` también |
| `405 metodo_no_permitido` | Cualquier método distinto de `POST`; `Allow: POST` |
| `409 transicion_invalida` | El anexo ya está legalizado; incluye `recurso` |
| `500 error_interno` | El estado firmado supera 3500 caracteres |

- **Autor fijo**: el autor y la fecha se derivan de la persona sintética de la Secretaría y del día de la demo. El cuerpo de la petición se ignora: el cliente no puede atribuirse la legalización.
- **Rechazo sin efectos**: ningún error cambia el estado guardado, los contadores ni los datos de ejemplo, y tampoco publica cookie.
- **CSRF**: Django exige el token, igual que en el envío de reportes y el cierre; la exención del `PATCH` de §6 sigue siendo solo de ese endpoint. Con `Client(enforce_csrf_checks=True)` un `POST` sin token responde el `403` HTML del middleware, que se ejecuta antes de la vista; por eso, con `DEBUG=False` y sin token la respuesta es `403` y no `404`.
- **Estado simulado**: la cookie firmada `prototipo_secretaria_v2` dura 24 h y usa `Path=/`, `HttpOnly`, `SameSite=Lax` y `Secure` con HTTPS, para que el API y las pantallas compartan lo legalizado. La cookie anterior `prototipo_secretaria` (`Path=/prototipo/`) se sigue leyendo y las pantallas la migran a la nueva al recibirla: las legalizaciones previas no se descartan. Cookies vencidas o inválidas se ignoran. Si el estado excede 3500 caracteres firmados, el API responde `500 error_interno` sin publicar la cookie.
- **Pantallas**: S2 consume el mismo caso de uso; si el anexo ya está legalizado muestra el `409` con su mensaje, y S1 deja de listarlo. Un rechazo deja la lista igual. La legalización de anexos es distinta de la validación del tutor (RF-03, RF-16): aquella decide si un documento cumple, esta solo deja constancia de quién revisó el anexo de cierre y cuándo (§RF-11 de la especificación).

**Pendiente para otro issue:** persistencia compartida entre usuarios y navegadores, identidad autenticada y almacenamiento de las legalizaciones. Este aporte no agrega un botón para restablecer la cookie de la Secretaría; borrar la cookie del navegador vuelve a los datos de ejemplo.
