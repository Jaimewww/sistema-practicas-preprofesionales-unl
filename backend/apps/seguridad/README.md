# Seguridad: JWT real y permisos por rol y por objeto (#79)

Autenticación de la API real con `djangorestframework-simplejwt` (ADR 0011, aceptada),
sesión con rotación, lista de bloqueo y logout, tope de intentos en el login y las
clases DRF de permiso por rol y por objeto. No incluye el flujo de login del cliente.

## Ruta rápida

1. Permisos: `backend/apps/seguridad/permissions.py` (`rol_requerido`,
   `PermitirPracticaVisible`, `rol_guardado`).
2. Rutas de sesión: `backend/apps/seguridad/api.py`
   (`TokenObtainEnvelopeView`, `TokenRefreshEnvelopeView`, `LogoutView`).
3. Wiring: `backend/config/settings.py` (`INSTALLED_APPS`, `REST_FRAMEWORK`, `SIMPLE_JWT`,
   `SPECTACULAR_SETTINGS`) y `backend/config/urls.py`.
4. Vistas protegidas: `backend/apps/practicas/api.py` y `backend/apps/reportes/api.py`.
5. Pruebas: `backend/tests/unit/test_seguridad.py` (permisos),
   `backend/tests/integration/test_auth_seguridad.py` (S4 de punta a punta),
   `test_auth_sesion.py` (rotación, logout, tope de intentos, schema) y
   `test_demo_xrol_aislado.py` (`X-Rol` ignorado con `DEBUG` encendido y apagado).

Fuente: issue #79 (S3/S4), `docs/adr/0011-metodo-de-autenticacion-de-la-api.md` y el
alcance de filas de T019 (`apps/usuarios/permissions.py`).

## Flujo de autenticación

| Método y ruta | Cuerpo | Respuesta |
| --- | --- | --- |
| `POST /api/v1/auth/token/` | `{username, password}` | 200, `data`: `{access, refresh}`; 429 al sexto intento por minuto |
| `POST /api/v1/auth/token/refresh/` | `{refresh}` | 200, `data`: `{access, refresh}`; el refresh enviado queda bloqueado |
| `POST /api/v1/auth/logout/` | `{refresh}` + access | 200, `data`: `null`; el refresh queda revocado |

Valores (ADR 0011): access de 15 minutos; refresh de 30 con rotación y lista de
bloqueo, de modo que 30 minutos sin renovar cierran la sesión (RNF-03). El tope del
login es `ScopedRateThrottle` con scope `auth` (5/min) sobre la cache por defecto.

El cliente manda `Authorization: Bearer <access>` en el resto de la API real. Obtener y
renovar son públicas (`AllowAny`; RNF-01 exime el login) y el logout exige un access.
Todo lo demás es **auth-first**: `DEFAULT_AUTHENTICATION_CLASSES` es `JWTAuthentication`,
`DEFAULT_PERMISSION_CLASSES` es `IsAuthenticated` y el 401 sale con el envelope de #77
(`errors.detail` = «Se requiere autenticación.», `code` = `no_autenticado`). La
autenticación corre antes del despacho, así que una ruta inexistente o un `id` que no
existe también responde 401 sin credenciales; el 404 aparece recién autenticado.
`X-Rol` se ignora: no abre nada.

El schema y Swagger (`/api/v1/schema/`, `/api/v1/docs/`) son anónimos solo con `DEBUG`
encendido (`AbiertoSoloEnDebug`, decidido por petición); con `DEBUG` apagado exigen un
access.

El envelope no distingue *por qué* falló el token (basura, firma alterada, vencido,
revocado, cuenta inactiva o borrada): todas dan 401 con el mismo cuerpo, así que el
cliente no aprende nada del token recibido. Con credenciales pero sin permiso el estado
es 403 (`errors.detail` = «No tiene permiso para esta operación.» o el texto de la
vista), también con el envelope. Una cuenta sin fila guardada y activa no tiene
credenciales vigentes: `SinFilaEs401` convierte el rechazo en 401, no en 403.

**CSRF**: las rutas DRF con JWT no usan `csrf_exempt` ni cookies de sesión, así que no
hay exención que agregar ni lógica CSRF nueva en esta unidad. El `csrf_exempt` del
`PATCH` de decisiones del demo (`/prototipo/api/v1/pendientes/`) es una excepción del
prototipo y no se extiende.

## Modelo de permisos

- `rol_requerido(*roles, mensaje=None)` fabrica la clase de permiso que exige alguno de
  esos roles (por ejemplo `rol_requerido(Usuario.Rol.ESTUDIANTE)`). `mensaje` es el texto
  del 403 cuando la vista tiene uno propio; el texto vive en una sola constante, la de
  la vista, y sin él sale el genérico del contrato. Un rol desconocido o una lista
  vacía es un error de programa: la fábrica falla en vez de dejar pasar a nadie.
- `PermitirPracticaVisible` (antes `PermitirObjetoAlDueno`): la entrada exige una cuenta
  guardada y activa; el objeto se decide con `practicas_visibles_para` (T019) acotado al `pk` pedido. No reimplementa el
  alcance de filas: pregunta si el objeto está dentro del alcance, con la misma
  semántica (estudiante = sus prácticas, tutor académico = las asignadas, tutor de
  entidad = las laborales vinculadas, coordinador/director/secretaría = su carrera).
- El rol se relee siempre de la fila guardada por `pk`: el objeto del llamador no decide
  e `is_staff`/`is_superuser` no abren nada.

| Vista | Permisos | Efecto |
| --- | --- | --- |
| `GET /api/v1/practicas/` | `PermitirPracticaVisible` | 200 con las filas de T019; 401 anónimo o sin fila |
| `GET /api/v1/practicas/{id}/` | `PermitirPracticaVisible` | 200 si está en el alcance; 404 fuera de alcance (lo ajeno no existe) |
| `POST /api/v1/practicas/{id}/reportes/` | `rol_requerido(estudiante)` + `PermitirPracticaVisible` | 201 del dueño; 403 si el rol no es estudiante (tutor, coordinador, director, Secretaría); 404 idéntico si la práctica no existe o es ajena (#101) |

En el POST del reporte la práctica se busca solo entre las del estudiante autenticado
(dentro de la transacción), así que la ajena y la inexistente dan el mismo 404 y el
permiso de objeto nunca la ve: el 403 por objeto ajeno que daba la primera versión de
#102 filtraba la existencia y se retiró. El chequeo explícito de actor y de dueño queda
como segunda barrera.

**Permiso de las transiciones de estado.** No vive en estas clases DRF: está en el
servicio `cambiar_estado_practica` (#98), que decide con la fila bloqueada y exige al
coordinador activo de la carrera para suspender, reanudar, cancelar y cerrar. Los
endpoints que lo usen heredan esa regla; no la duplican con un permiso de vista.

## El X-Rol del demo

El demo server-rendered del prototipo sigue seleccionando personas sintéticas con
`X-Rol` y **no autentica** a nadie. Su JSON vive en `/prototipo/api/v1/` (antes
compartía el prefijo `/api/v1/` con la API real y solo `DEBUG` lo separaba). La API real
no lo obedece: `test_demo_xrol_aislado.py` comprueba que una ruta de negocio con `X-Rol`
y sin token responde 401 con `DEBUG` encendido y apagado.

## Límites

- El tope de intentos usa la cache local del proceso: con varios procesos es por proceso.
- Las filas vencidas de la lista de bloqueo se limpian con
  `manage.py flushexpiredtokens`, que no está programado.
- El logout revoca el refresh, no el access ya emitido (vale hasta 15 minutos).
- Las pruebas corren sobre SQLite en memoria; el runner apaga `DEBUG`, así que las que
  leen el schema anónimo lo declaran con `override_settings`.

## Checklist

- [ ] `apps.seguridad` y `token_blacklist` figuran en `INSTALLED_APPS` y la API real
      exige JWT por defecto.
- [ ] `POST /api/v1/auth/token/` devuelve `{access, refresh}` envuelto; el refresh rota y
      el anterior ya no sirve; el logout lo revoca.
- [ ] Sin credenciales, toda la API real responde 401 con envelope (también con `X-Rol`).
- [ ] Token basura, alterado, vencido, revocado o de cuenta inactiva responde 401 con el
      mismo cuerpo.
- [ ] Un rol sin permiso recibe 403 (incluidos director y Secretaría) y una práctica
      ajena 404 en el detalle y en el POST.
- [ ] El sexto intento de login en un minuto responde 429.
- [ ] Schema y Swagger responden 401 sin token con `DEBUG` apagado.
- [ ] Ni la contraseña ni los tokens aparecen en respuestas ni en logs.
