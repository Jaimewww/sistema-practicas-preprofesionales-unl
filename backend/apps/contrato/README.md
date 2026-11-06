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
  `{campo: [textos]}` para validación, `{"detail": texto}` para errores planos.
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

El 500 devuelve `message: "Error interno del servidor."` y
`errors: {"detail": "Ocurrió un error inesperado."}`: ni la traza, ni el mensaje
original de la excepción, ni datos internos salen por el wire, con `DEBUG`
encendido o apagado. La traza queda en el log del proceso.
El handler nunca devuelve `None`, por lo que DRF no re-lanza la excepción.

## Documentación

`/api/v1/schema/` sirve el OpenAPI en YAML y `/api/v1/docs/` el Swagger UI. Las
dos vistas (`drf_spectacular.views`) fijan sus propios renderers, así que **no**
llevan envelope: son herramientas del contrato, no endpoints de negocio.
`SERVE_INCLUDE_SCHEMA=False` evita que el propio schema se auto-documente.

El acceso es abierto: la frontera de autorización de `/api/v1/` es el issue #79.

## Pruebas

`backend/tests/unit/test_envelope_renderer.py` y `test_envelope_exceptions.py`
definen sus `APIView` **dentro** del módulo de test y activan su `urlpatterns`
con `override_settings(ROOT_URLCONF=__name__)`: el contrato se ejercita sin
publicar endpoints de demostración en producción.

Estas suites requieren DRF: se corren con el intérprete que tenga
`djangorestframework` y `drf-spectacular` instalados (verificación de la tarea:
`~/.venvs/s77/bin/python`) y con `DJANGO_SECRET_KEY` exportada.
