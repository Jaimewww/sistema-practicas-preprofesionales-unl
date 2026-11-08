# Contrato de respuesta de la API v1 (#77)

Esta app no tiene vistas ni modelos: es el contrato que comparten todos los
endpoints de `/api/v1/` (issue #78).

## Envelope

Todo `/api/v1/` responde el mismo sobre (S4 de #87):

```json
{"success": true, "message": "Operación exitosa.", "data": {}, "errors": null, "meta": {}}
```

- `success` es `true` solo con estado < 400; desde 400 siempre `false`.
- `message` es un texto corto en español.
- `data` es la carga cruda del endpoint (`{}`, `[]` o `null`).
- `errors` es `null` en el camino exitoso y un diccionario en el de error:
  `{campo: [textos]}` para validación y `{"detail": texto, "code": codigo}`
  para errores planos (ver «Errores y seguridad»).
- `meta` va vacío; la paginación llega con #78.
- Las respuestas `204` van **sin cuerpo**.

## Dónde vive cada pieza

| Pieza | Archivo | Rol |
| --- | --- | --- |
| `SuccessEnvelopeRenderer` | `renderer.py` | envuelve toda respuesta < 400 y vacía el cuerpo de los `204` |
| `envelope_exception_handler` | `exceptions.py` | envuelve validación, 401, 403, 404, 500 y cualquier excepción |
| `REST_FRAMEWORK` / `SPECTACULAR_SETTINGS` | `config/settings.py` | renderer único por defecto, handler y `AutoSchema` |
| rutas de documentación | `config/urls.py` | `/api/v1/schema/` (YAML) y `/api/v1/docs/` (Swagger) |

El renderer es el **único** renderer por defecto: no hay `BrowsableAPIRenderer`
ni un `JSONRenderer` duplicado, así que ninguna respuesta DRF puede salir sin
envolver. Las vistas pueden seguir usando `Response` con datos crudos.

## Errores y seguridad

Los errores que no son de validación llevan `errors = {"detail", "code"}`, donde
`code` es un identificador estable y legible por máquina (el cliente decide con
él, no con el texto):

| Estado | `message` | `detail` | `code` |
| --- | --- | --- | --- |
| 400 validación | `Datos inválidos.` | — (`{campo: [textos]}`, sin `code`) | — |
| 401 | `Autenticación requerida.` | `Se requiere autenticación.` (genérico) | `no_autenticado` |
| 403 | `Permiso denegado.` | el texto del servidor, o el genérico si no escribió uno | `permiso_denegado` |
| 404 | `Recurso no encontrado.` | `No encontrado.` (genérico) | `no_encontrado` |
| 429 | `Demasiadas solicitudes.` | `Demasiados intentos. Intente de nuevo en N segundos.` (con `Retry-After`) | `demasiadas_solicitudes` |
| otra `APIException` | `Solicitud inválida.` | el `detail` del servidor | el de la excepción (`default_code`; un 409 define el suyo, p. ej. `semana_duplicada`) |
| 500 | `Error interno del servidor.` | `Ocurrió un error inesperado.` | `error_interno` |

El 401 y el 404 son genéricos a propósito: no revelan el motivo de la
autenticación ni si el recurso existe. El 403 y las `APIException` conservan el
`detail` porque lo escribe el servidor y no es un dato sensible.

El 500 no filtra la traza, ni el mensaje original de la excepción, ni datos
internos, con `DEBUG` encendido o apagado. La traza queda en el log del proceso.
El handler nunca devuelve `None`, por lo que DRF no re-lanza la excepción.

**Rollback.** Como el handler por defecto de DRF, el nuestro llama a
`rest_framework.views.set_rollback()` antes de responder: si la vista corre dentro
de una transacción (`ATOMIC_REQUESTS` o `transaction.atomic()` con
`set_rollback`), una respuesta de error deshace las escrituras de la petición.

## Documentación

`/api/v1/schema/` sirve el OpenAPI en YAML y `/api/v1/docs/` el Swagger UI. Las
dos vistas (`drf_spectacular.views`) fijan sus propios renderers, así que **no**
llevan envelope: son herramientas del contrato, no endpoints de negocio.
`SERVE_INCLUDE_SCHEMA=False` evita que el propio schema se auto-documente.

El acceso es anónimo solo con `DEBUG` encendido; con `DEBUG` apagado exige un
access token (`apps.seguridad.permissions.AbiertoSoloEnDebug`, #79/#102; RNF-01
exime únicamente el login y `/health/`).

**El esquema está vacío en #100.** Las vistas de `/api/v1/` de este PR son el
prototipo en Django plano (no DRF), así que `drf-spectacular` no tiene `paths` que
documentar. El criterio de Swagger de #77 se completa con #101 (#78), que
introduce los endpoints DRF; por eso este PR referencia #77 (`Refs #77`) y no lo
cierra.

## Pruebas

`backend/tests/unit/test_envelope_renderer.py` y `test_envelope_exceptions.py`
definen sus `APIView` **dentro** del módulo de test y activan su `urlpatterns`
con `override_settings(ROOT_URLCONF=__name__)`: el contrato se ejercita sin
publicar endpoints de demostración en producción.

Estas suites requieren DRF: se corren con el intérprete que tenga
`djangorestframework` y `drf-spectacular` instalados (verificación de la tarea:
`~/.venvs/s77/bin/python`) y con `DJANGO_SECRET_KEY` exportada.
