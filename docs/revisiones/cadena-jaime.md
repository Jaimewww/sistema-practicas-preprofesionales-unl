# Revisión de la cadena de PRs de Jaime (Sumativa 1)

Este documento registra, PR por PR, cada decisión tomada al revisar y corregir la cadena de Jaime. Cada entrada dice **qué se decidió**, **por qué** (con la fuente: spec, reglamento o ADR) y **dónde quedó el cambio** (archivos y commit). Las correcciones van como commits nuevos encima de la rama, sin reescribir historia.

Convenciones: `spec.md` y `data-model.md` son los de `specs/001-seguimiento-practicas/`; los números de línea son los de la rama tras estos cambios.

## #98 — Cimientos (#76)

Rama `feature/s1-j1-cimientos`. La revisión original (hallazgos bloqueantes, ajustes y alineación con la spec) está en el comentario de revisión de #98; aquí queda el porqué de cada resolución.

### 1. Conflicto con develop: `settings.py` toma ambos lados

- **Decisión**: resolver el conflicto conservando la unión de las dos versiones de `backend/config/settings.py`.
- **Por qué**: develop avanzó 18 commits (logging, `apps.observability`, `RequestIdMiddleware`) y la rama aporta el contrato de entorno de #76 (`DJANGO_*`, `POSTGRES_*`) y seis apps nuevas. Ninguno de los dos lados contradice al otro, así que descartar uno habría perdido trabajo ya mergeado. Los nombres de variables ya coinciden con el compose y el CI ([ADR 0013](../adr/0013-contenerizacion-con-docker-compose.md):17, [ADR 0002](../adr/0002-postgresql-como-motor-de-base-de-datos.md):24).
- **Cambio**: `backend/config/settings.py`; merge `0c8448a`.

### 2. El seed es idempotente (corrección de Jaime)

- **Decisión**: la segunda corrida de `manage.py seed` imprime el aviso y termina con código 0, sin escribir nada.
- **Por qué**: `docker/entrypoint.sh` corre con `set -eu` y ejecuta `seed` en cada arranque; con el volumen `pgdata` persistente, una segunda corrida que abortara dejaría el contenedor en crash-loop ([ADR 0013](../adr/0013-contenerizacion-con-docker-compose.md)). Es la corrección que pidió la revisión y la hizo Jaime.
- **Cambio**: `backend/apps/prototipo/management/commands/seed.py`, `backend/tests/unit/test_seed_command.py`; commit `cdc869e` (nota en el README del prototipo: `b0d38e8`).

### 3. Una versión de plan por práctica, impuesta en la base

- **Decisión**: `UniqueConstraint(["practica", "version"])` en `PlanActividades`.
- **Por qué**: la unicidad dependía solo del bloqueo de `enviar_plan`; el admin, el seed o un servicio futuro podían duplicar versiones. La restricción no cambia el comportamiento y convierte la invariante de [data-model.md](../../specs/001-seguimiento-practicas/data-model.md):115 («incremental por devolución; única por práctica») en una garantía de la base.
- **Cambio**: `backend/apps/actividades/models.py`, migración `actividades/0003_plan_version_unica.py`, `tests/unit/test_plan_actividades.py`; commit `109661f`.

### 4. Reglas de rango como `CheckConstraint`

- **Decisión**: `Periodo.fecha_fin > fecha_inicio`, `horas_requeridas > 0` (en `Practica` y `ConfiguracionCarrera`) y `umbral_rezago <= 100`, también en la base. Queda **fuera** la regla «carrera obligatoria por rol» de `Usuario`.
- **Por qué**: [data-model.md](../../specs/001-seguimiento-practicas/data-model.md):45,48,59 pide fin posterior al inicio, horas definidas por la carrera y un umbral que es un porcentaje; `objects.create()` y `save()` no ejecutan `full_clean()`, así que sin la restricción esas reglas no se cumplían. Horas en cero harían que el cierre del 100 % de las horas ([spec.md](../../specs/001-seguimiento-practicas/spec.md):281, Art. 339) fuera trivial. La regla de `Usuario` queda pendiente: cambiaría el alta de superusuarios y el admin, y merece su propia decisión.
- **Cambio**: `apps/practicas/models.py`, `apps/carreras/models.py`, migraciones `practicas/0005_checks_periodo_practica.py` y `carreras/0002_configuracion_checks.py` y sus tests; commit `109661f`.

### 5. `DATABASES` falla cerrado sin `POSTGRES_*` cuando `DEBUG` está apagado

- **Decisión**: con `DJANGO_DEBUG` distinto de `True` y sin `POSTGRES_HOST` ni `POSTGRES_DB`, `settings.py` lanza `ImproperlyConfigured`; con `DEBUG` encendido sigue el respaldo a SQLite.
- **Por qué**: un despliegue mal configurado arrancaba sobre un archivo SQLite descartable sin avisar, contra [ADR 0002](../adr/0002-postgresql-como-motor-de-base-de-datos.md) (PostgreSQL es el motor; SQLite solo comodidad de desarrollo, igual que dice [plan.md](../../specs/001-seguimiento-practicas/plan.md):19). Es el mismo criterio que ya tenía `DJANGO_SECRET_KEY`. El CI, el compose y el entrypoint ya definen `POSTGRES_*`, así que no cambia nada en esos entornos.
- **Cambio**: `backend/config/settings.py`, probe en `tests/unit/test_settings_env.py` (caso sin variables con `DEBUG` apagado, bordes de `POSTGRES_PORT` solo y `POSTGRES_HOST` vacío); commit `c4ed1ba`.
- **Efecto en `backend/config/tests.py`**: el archivo viene de develop y sus tests recargan `settings` con `DEBUG` apagado y sin `POSTGRES_*`, que ahora es justo el caso que falla cerrado por diseño; solo pasaban donde el entorno ya exportaba `POSTGRES_*` (CI). Se planta `POSTGRES_HOST` en su entorno de prueba sin tocar sus aserciones. Commit `42623cb`.

### 6. Se quita un test que no probaba nada

- **Decisión**: eliminar `test_actualizar_la_configuracion_no_cambia_las_horas_guardadas` de `tests/unit/test_practica.py`.
- **Por qué**: `Practica` no tiene vínculo con `ConfiguracionCarrera` en ese punto, así que el test guardaba las horas y comprobaba que seguían ahí; no podía fallar. La cobertura real de [data-model.md](../../specs/001-seguimiento-practicas/data-model.md):92 («copiadas al asignar; no se recalculan») está en `tests/unit/test_asignacion_practica.py` (`AsignacionCopiaTests`: editar la configuración y crear una posterior).
- **Cambio**: `backend/tests/unit/test_practica.py`; commit `d0dfdbf`. El título del commit original `d89dc4a` («stored hours snapshot») sigue adelantando una copia que llega en `84e5312`; no se reescribe historia, queda anotado aquí.

### 7. Devolver regresa el plan al estudiante; el reenvío crea la versión

- **Decisión**: `devolver_plan` marca la fila `devuelto`, escribe la `Validacion` y devuelve esa misma fila, sin versión nueva. `enviar_plan` rechaza (clave `estado`) si la última versión está `en_revision` o `aprobado`; tras una devolución crea la versión máx+1 con el contenido corregido.
- **Por qué**: la versión es «incremental por devolución» ([data-model.md](../../specs/001-seguimiento-practicas/data-model.md):115,121) y el criterio de aceptación de HU-01 dice que el estudiante ve las observaciones y **puede corregirlo** ([spec.md](../../specs/001-seguimiento-practicas/spec.md):93; el tutor orienta y retroalimenta el plan, Art. 336, [reglamento](../fuentes/reglamento-practicas-unl.md):65-67). Antes, devolver creaba la versión N+1 ya `en_revision` con el mismo contenido: el tutor volvía a recibir lo que acababa de devolver. Rechazar el reenvío con la última versión `en_revision` o `aprobado` evita dos planes pendientes a la vez o pisar uno ya aprobado. Decisión de spec tomada el 2026-11-05.
- **Cambio**: `backend/apps/actividades/services.py` (docstrings incluidos), `backend/tests/integration/test_plan_actividades.py` (reescritos el ciclo de dos devoluciones, el reenvío y la devolución; nuevos rechazos para `en_revision` y `aprobado`); commit `e79a5c6`.

### 8. El permiso de suspender, reanudar, cancelar y cerrar vive en el servicio

- **Decisión**: `cambiar_estado_practica` exige que esas cuatro aristas (`en_curso→suspendida`, `suspendida→en_curso`, `suspendida→cancelada`, `en_revision_final→cerrada`) las produzca el coordinador **activo** de la carrera de la práctica, leído de la fila guardada de `Usuario`. Orden de rechazos: estado final, destino inválido, arista ilegal, permiso (clave `autor`), motivo. Las demás aristas siguen siendo mecanismo interno.
- **Por qué**: la revisión pedía elegir un criterio, servicio o capa de endpoint (RNF-02). Se eligió el servicio porque no hay endpoints todavía y los servicios del plan ya fallan cerrado contra la fila guardada; así un futuro endpoint hereda la regla. La fuente es [spec.md](../../specs/001-seguimiento-practicas/spec.md):336 («solo el coordinador suspende, reanuda o cancela»), RF-13 (:285) y la precondición «de su carrera» de HU-08; el cierre lo hace el coordinador ([data-model.md](../../specs/001-seguimiento-practicas/data-model.md):231-237). `aprobar_plan` ya exige al tutor, por eso `asignada→en_curso` no se restringe.
- **Consecuencia**: aprobar el plan de una práctica suspendida ya no falla por «motivo» sino por permiso (`autor`), porque reanudar no es del tutor. El seed no cambia: firma esas aristas con el coordinador, que tiene la carrera de las prácticas sembradas.
- **Cambio**: `backend/apps/practicas/services.py`, `tests/unit/test_transiciones_practica.py` (coordinador permitido; estudiante, tutor, tutor de entidad, director, secretaría, coordinador de otra carrera e inactivo rechazados sin tocar estado, motivos ni historial), `tests/integration/test_plan_actividades.py`; commit `804037f`.

### 9. Motivo obligatorio solo al suspender y cancelar

- **Decisión**: reanudar no exige motivo (si se da, se conserva en el historial). Cambian `ARISTAS_CON_MOTIVO`, `HistorialEstado._exige_motivo` y `MENSAJE_MOTIVO`.
- **Por qué**: RF-13 pide «un motivo para suspender y para cancelar» ([spec.md](../../specs/001-seguimiento-practicas/spec.md):285) y la Clarification de :486 lo repite; [data-model.md](../../specs/001-seguimiento-practicas/data-model.md):201 era la línea desactualizada y el código la seguía. Se corrigieron las dos.
- **Cambio**: `backend/apps/auditoria/models.py`, `backend/apps/practicas/services.py`, `tests/unit/test_historial_estado.py`, `tests/unit/test_transiciones_practica.py` (reanudar sin motivo se acepta); `data-model.md`:201 en `97dc341`; commit del código `804037f`.

### 10. `asignar_practica` copia solo las horas

- **Decisión**: se mantiene la copia solo de `horas_requeridas`; se aclara el data-model en lugar de copiar también plazos y umbral.
- **Por qué**: el Tema 7 de [research.md](../../specs/001-seguimiento-practicas/research.md):79-81 y la Clarification de [spec.md](../../specs/001-seguimiento-practicas/spec.md):487 hablan de las **horas** (el motivo de copiarlas: que un cambio posterior no quite ni agregue horas a quien ya cumplía). Los plazos y el umbral se aplican a la alerta del día y RF-07 los toma «de la carrera»; copiarlos congelaría alertas con valores viejos y `Practica` no tiene columnas para ellos. La frase «copian sus valores» de [data-model.md](../../specs/001-seguimiento-practicas/data-model.md):51 era la imprecisa.
- **Cambio**: `specs/001-seguimiento-practicas/data-model.md`:51, `backend/apps/practicas/README.md`, entrada en Clarifications; commit `97dc341`.

### 11. Un abandono se registra suspendiendo y luego cancelando

- **Decisión**: la cancelación sigue permitida solo desde `suspendida`; la spec lo dice explícitamente.
- **Por qué**: así lo implementa la tabla de transiciones ([data-model.md](../../specs/001-seguimiento-practicas/data-model.md):231-237) y evita abrir una arista nueva `en_curso→cancelada` sin decisión de producto. La fila de casos límite ([spec.md](../../specs/001-seguimiento-practicas/spec.md):195) decía «un abandono se registra como cancelación» sin aclarar la ruta.
- **Cambio**: `specs/001-seguimiento-practicas/spec.md`:195 y Clarifications (:503-510); commit `97dc341`.

### 12. S-02: la fuente de la confirmación queda pendiente de Jaime

- **Decisión**: no se inventa quién confirmó S-02. Se conserva el estado que escribió el commit `54c0bfb`, se marca «fuente por enlazar» y se abre una entrada en Clarifications que pide a Jaime el enlace (mensaje, issue o acta).
- **Por qué**: el commit pasó S-02 de «Por confirmar» a «Confirmado para el MVP por la persona dueña» sin enlazar la confirmación, y nadie del equipo de revisión puede reconstruirla. La regla no se retira porque el modelo (índice único parcial de `AsignacionTutor`) y el data-model la implementan; lo que falta es la trazabilidad.
- **Cambio**: `specs/001-seguimiento-practicas/spec.md`:245 y :503-504; commit `97dc341`.

### Pendiente en #98

- Descripción del PR: la sección «Impacto cruzado» quedó desactualizada (#81 y #82 ya están en develop y este PR aporta el `seed`). Se actualiza al publicar la rama.
- Enlace de la confirmación de S-02 (Jaime).
- `README.md` de la raíz (:216) todavía dice que Django usa SQLite dentro del contenedor y el `Makefile` (`make run`/`make test`) no exporta `DJANGO_SECRET_KEY` ni `DJANGO_DEBUG` para `migrate`/`test`; quedan fuera de las superficies de esta revisión.

---

## #100 — Contrato de respuesta y OpenAPI (#77)

Rama `feature/s1-j2-contrato-openapi`. Entrega el envelope universal (renderer + exception handler) y el OpenAPI de `drf-spectacular` de [ADR 0012](../adr/0012-contrato-universal-de-respuesta.md).

### 1. Se integra la base corregida con un merge, no con un rebase

- **Decisión**: traer a la rama el estado corregido de #98 con un merge (`0f55227`).
- **Por qué**: la rama de #100 está apilada sobre #98 y ya tiene commits de Jaime publicados. Un rebase reescribiría esa historia y obligaría a un force-push; el merge conserva los commits y los hashes, y la revisión sigue siendo legible.
- **Cambio**: merge `0f55227` (sin conflictos).

### 2. Los errores llevan `code` legible por máquina

- **Decisión**: todo error que no es de validación devuelve `errors = {"detail": texto, "code": codigo}`: `no_autenticado`, `permiso_denegado`, `no_encontrado`, `error_interno` o el `default_code` de la `APIException` (un `409` define el suyo, p. ej. `semana_duplicada`). La validación sigue siendo `{campo: [textos]}`.
- **Por qué**: [ADR 0012](../adr/0012-contrato-universal-de-respuesta.md) dejó pendiente en #77 cómo se conservan los códigos de dominio del contrato anterior (`docs/api.md` §2). Sin `code`, el cliente tendría que decidir comparando el texto de `detail`, que es para personas y puede cambiar. Es el criterio S4 de la revisión: «errores con `code` legible por máquina».
- **Cambio**: `backend/apps/contrato/exceptions.py`, `backend/tests/unit/test_envelope_exceptions.py` (envelope exacto por estado, 409 con código propio, validación sin `code`); commit `214c014`. Documentado en `backend/apps/contrato/README.md` (`5af7657`), `docs/api.md` §2 y ADR 0012 (`f07debd`; el estado del ADR no cambia).

### 3. 403 y `APIException` conservan el `detail`; 401 y 404 son genéricos

- **Decisión**: el `detail` que escribió el servidor se conserva en el `403` y en las demás `APIException`; el `401` y el `404` devuelven siempre el mismo texto genérico. Un `403` sin texto propio usa el genérico en español, no el inglés de fábrica de DRF.
- **Por qué**: el texto de un `403` o de un `409` es parte del contrato con el cliente y no revela datos sensibles. En cambio, un `404` distinto según el motivo delataría si un recurso existe, y un `401` detallado revelaría por qué falló la autenticación (token vencido, usuario inexistente…). Es el mismo criterio de no filtrar existencia que se aplica a los `404` de #101.
- **Cambio**: `backend/apps/contrato/exceptions.py` y sus tests (403 de DRF con y sin texto propio); commit `214c014`.

### 4. El handler llama a `set_rollback()`

- **Decisión**: toda respuesta de error marca la transacción de la petición para rollback, incluido el `500`.
- **Por qué**: el handler por defecto de DRF lo hace; al reemplazarlo sin llamarlo, con `ATOMIC_REQUESTS` o una vista dentro de `transaction.atomic()` un error ya envuelto como respuesta dejaría escrituras a medias, porque la excepción no llega a la transacción. Cerrado por defecto: ante un error, no se guarda nada.
- **Cambio**: `backend/apps/contrato/exceptions.py`; tests con `set_rollback` simulado para cada estado manejado y para el `500`; commit `214c014`.

### 5. El esquema OpenAPI está vacío en este PR y #77 se completa con #101

- **Decisión**: se documenta que `/api/v1/schema/` no lista `paths` todavía, y el PR pasa a referenciar el issue con `Refs #77` en lugar de cerrarlo (la descripción se actualiza al publicar).
- **Por qué**: las vistas de `/api/v1/` de este PR son el prototipo en Django plano, no DRF, así que `drf-spectacular` no tiene nada que describir. El criterio de Swagger de #77 solo se cumple cuando #101 (#78) introduce los endpoints DRF; cerrar #77 aquí sería declarar un cumplimiento falso.
- **Cambio**: `backend/apps/contrato/README.md`; el texto del PR se corrige en la publicación (T6 de la revisión).

### 6. Schema y Swagger siguen abiertos (`AllowAny`) hasta #102

- **Decisión**: no se restringe el acceso a `/api/v1/schema/` y `/api/v1/docs/` en este PR.
- **Por qué**: la frontera de autorización de `/api/v1/` es #79/#102; añadir una regla aquí duplicaría esa decisión sin autenticación real que la respalde. El esquema hoy no expone endpoints, así que el riesgo es nulo; queda registrado para #102.
- **Cambio**: sin cambio de código; nota en `backend/apps/contrato/README.md`.

### 7. Tamaño del PR: 651 líneas, aceptado

- **Decisión**: no se divide el PR.
- **Por qué**: 369 de las 651 líneas son tests, y el envelope, su handler, su renderer y el OpenAPI forman un solo contrato; dividirlo reescribiría una cadena ya apilada y revisada (#101-#103 dependen de esta rama). Los cambios de esta revisión suman unas 240 líneas más (la mayoría tests y documentación).
- **Cambio**: ninguno; queda como excepción documentada.

### 8. El test de `/health/` se alinea con develop

- **Decisión**: el test que protege que `/health/` no se envuelve declara `databases = {"default"}` y espera el cuerpo actual (`{"status": "ok", "checks": {"database": "ok"}}`).
- **Por qué**: al integrar la base corregida (que ya incluye develop), `/health/` hace una consulta a la base y devuelve `checks`; el test, escrito antes, usaba `SimpleTestCase` (que prohíbe consultas) y comparaba el cuerpo viejo, y fallaba la suite completa. Lo que se protege no cambia: que la ruta no DRF salga sin envelope.
- **Cambio**: `backend/tests/unit/test_envelope_renderer.py`; commit `183e640`.

### Pendiente en #100

- Descripción del PR: cambiar el cierre de #77 por `Refs #77` y anotar que el esquema está vacío hasta #101.
- Frontera de acceso a schema/docs: #102.

## #101 — Flujo de reportes (#78)

Rama `feature/s1-j3-flujo-reportes`. Hallazgos de la revisión: fuga de existencia (404 frente a 400), actor ajeno con 400 en vez de 403, `to_internal_value` con 500 ante un cuerpo lista, lectura de la práctica fuera de la transacción, `except IntegrityError` demasiado ancho, horas sin tope, RNF-05 y plan aprobado sin imponer, Swagger parcial y el orden de claves de `dto.py`. Las referencias a la spec son `specs/001-seguimiento-practicas/spec.md`; el issue es #78 (alcance y criterios de aceptación).

### 1. Se integra #100 corregido con un merge y se fusionan las migraciones 0003

- **Decisión**: la rama recibió el merge de `feature/s1-j2-contrato-openapi` ya corregida (`4b8883a`, que arrastra #98 y el `errors.code` de #100) y se añadió la migración de fusión `actividades/0004_merge_0003_plan_version_unica_0003_validacion_reporte`.
- **Por qué**: #98 corregido creó `actividades/0003_plan_version_unica` y #101 ya tenía `0003_validacion_reporte`: dos hojas en el grafo de migraciones y `manage.py test` ni arrancaba («Conflicting migrations detected»). Renombrar la 0003 de Jaime habría reescrito una migración publicada; fusionar conserva ambas y no toca historia. Lo demás de #98 (devolver/reenvío del plan, permisos solo del coordinador, motivo solo al suspender y cancelar, CHECK) no rompió ningún test ni código de #101.
- **Cambio**: `backend/apps/actividades/migrations/0004_merge_*.py`; commit `28b40f9`.

### 2. 401 sin actor, 403 si no es estudiante, 404 idéntico si la práctica no es suya

- **Decisión**: el POST de reportes responde `401 no_autenticado` sin actor guardado y activo, `403 permiso_denegado` si el actor no es estudiante y `404 no_encontrado` si la práctica no existe **o** no pertenece al estudiante. Las dos causas del 404 devuelven el mismo cuerpo. Antes eran `400` en la clave `actor` (o `404` solo si la práctica no existía).
- **Por qué**: con `404` para la inexistente y `400` para la ajena, cualquiera podía averiguar qué ids de práctica existen: fuga de existencia. Un `400` tampoco es un permiso: un tutor no «envía datos inválidos», no tiene derecho a esta acción (RNF-02, spec.md:369 y el contrato de #100: 401/404 genéricos, 403 con `detail`). La búsqueda filtra por `estudiante_id` del actor guardado, así el 404 es el mismo por construcción.
- **Cambio**: `backend/apps/reportes/api.py` (`actor_estudiante`, `post`); tests en `backend/tests/integration/test_reportes_flujo.py` (estado, envelope exacto con `errors.code` y conteos sin cambio); commit `aaa1367`.

### 3. La práctica se busca dentro de `transaction.atomic()` con `select_for_update`

- **Decisión**: la lectura de la práctica, la comprobación de estado y la inserción del reporte ocurren en una misma transacción y la fila de la práctica queda bloqueada.
- **Por qué**: antes se leía fuera de la transacción: entre la lectura y el `INSERT` otro proceso podía suspender o cerrar la práctica y el reporte entraba igual (carrera de estado). El bloqueo de la fila serializa los envíos de una práctica y la decisión «¿admite reportes?» se toma sobre el estado real. Un test espía `select_for_update` y comprueba que corre con una savepoint más que el test (SQLite no bloquea de verdad; el bloqueo real es de PostgreSQL).
- **Cambio**: `backend/apps/reportes/api.py`; commit `aaa1367`.

### 4. Solo una práctica «en curso» acepta reportes (409 `practica_no_en_curso`)

- **Decisión**: cualquier estado distinto de `en_curso` (asignada, suspendida, en revisión final, cerrada, cancelada) responde `409` con `errors.code = practica_no_en_curso`; antes solo se rechazaban los estados finales con un `400`.
- **Por qué**: spec.md:99 (HU-02, escenario 1) parte de «un plan aprobado» y spec.md:330 define `en curso` como «plan aprobado; el estudiante reporta actividades semanales», mientras que `asignada` es «aún sin plan aprobado» (spec.md:329). Exigir `en_curso` impone el plan aprobado sin consultar el plan aparte, y excluye por la misma regla la suspendida (detenida por el coordinador) y la de revisión final. Es un conflicto con el estado del recurso, no un error de campo, por eso 409 con código propio (L7 de #100: «409 con `code` propio»).
- **Cambio**: `backend/apps/reportes/api.py` (`PracticaNoEnCurso`); commit `aaa1367`.

### 5. Solo la restricción de semana única se traduce; la semana repetida es 409 `semana_duplicada`

- **Decisión**: el `except IntegrityError` ya no atrapa todo: solo el error de la restricción `reportes_reporte_semana_unica` (nombre en PostgreSQL, columnas en SQLite) se convierte en `409 semana_duplicada`; cualquier otro `IntegrityError` se relanza y sale como `500 error_interno` genérico. La comprobación previa de semana repetida pasa también a `409 semana_duplicada` (antes era `400` en `semana`).
- **Por qué**: atrapar todo convertía, p. ej., una FK rota o un NOT NULL en «semana duplicada»: un bug real quedaba disfrazado de error del usuario. Y dejar la misma condición con `400` en un camino y `409` en otro obligaba al cliente a manejar dos respuestas para un solo hecho; la semana repetida es un conflicto con un recurso existente. Tests: mock de ambos mensajes (SQLite y PostgreSQL), mock de otro `IntegrityError` (500 y sin filas) y un caso real con la comprobación previa desactivada que llega al `INSERT`.
- **Cambio**: `backend/apps/reportes/api.py` (`es_semana_unica`, `semana_ya_reportada`), `backend/apps/reportes/serializers.py` (el `validate` ya no consulta la base); commit `aaa1367`. Es una desviación deliberada de la letra de L8 (que solo mencionaba el `IntegrityError`) para mantener un único contrato.

### 6. Un cuerpo que no es objeto es 400, no 500

- **Decisión**: `to_internal_value` rechaza lo que no sea un `Mapping` con `400 Datos inválidos.` y `errors = {"non_field_errors": [texto]}`; además rechaza los campos que fija el servidor (`estado`, `requiere_revision`) igual que los desconocidos.
- **Por qué**: `set(data)` con una lista de objetos lanzaba `TypeError` (500) y con un texto producía claves absurdas (un carácter por clave). Una entrada del cliente nunca debe producir un 500. Tests con lista, texto y número.
- **Cambio**: `backend/apps/reportes/serializers.py`; commit `aaa1367`.

### 7. Tope físico de 168 horas por semana y marca `requiere_revision` (> 40 h)

- **Decisión**: `horas_reportadas` admite de 1 a 168 (más es `400` en `horas_reportadas`); el modelo gana `requiere_revision` (booleano no editable) que `save()` calcula como «horas > 40», con la migración `reportes/0002` (que además marca los reportes previos de más de 40 h). La ayudantía de hasta 10 h sigue aceptándose sin marca; la de más de 10 h sigue rechazada con el Art. 341.
- **Por qué**: una semana tiene 168 horas: sin tope se aceptaba cualquier entero. spec.md:102 (HU-02, escenario 4) pide que, para laboral no ayudantía o comunitaria con más de 40 h, el reporte se registre «en revisión» y «quede identificado para que el tutor lo revise»; spec.md:192 y spec.md:500 lo repiten. La versión original aceptaba el reporte pero no guardaba ninguna marca, así que el escenario no se cumplía. El valor se deriva en el servidor para que ningún cliente lo escriba (por eso se rechaza en el cuerpo). Por la misma regla (spec.md:287, RF-15) la ayudantía nunca llega a 40 h.
- **Cambio**: `backend/apps/reportes/models.py`, `backend/apps/reportes/serializers.py`, `backend/apps/reportes/migrations/0002_requiere_revision_y_tope_semanal.py`; tests en `backend/tests/unit/test_reportes.py` y el flujo; commits `e1d5f9b` y `aaa1367`.

### 8. Swagger completo: cuerpo real, 401/403/404/409 y el path de detalle

- **Decisión**: el POST documenta `request=ReporteSemanalSerializer` (ya no el serializer en línea de dos campos) y las respuestas 201, 400, 401, 403, 404 y 409; el detalle de prácticas documenta 200 y 404. Hay un test del path `/api/v1/practicas/{practica_id}/` y otro que comprueba que solo `semana` y `horas_reportadas` son escribibles y que `requiere_revision` aparece como campo de salida.
- **Por qué**: el criterio del issue #78 es «el endpoint aparece en Swagger con sus errores»; el serializer en línea podía divergir del real y los errores 401/403/409 no estaban documentados.
- **Cambio**: `backend/apps/reportes/api.py`, `backend/apps/practicas/api.py`; commit `aaa1367`.

### 9. `dto.py`: `url` vuelve a su posición original

- **Decisión**: en `to_practica_dto`, `url` se asigna justo después de los campos de la práctica, donde estaba en develop, y se quita un comentario que solo explicaba el cambio.
- **Por qué**: #101 movió `url` al final del diccionario; el orden de claves es parte del payload que ven las pantallas y los diffs de snapshot, y un cambio de orden sin motivo ensucia la revisión. Un test fija la posición.
- **Cambio**: `backend/apps/prototipo/dto.py`; commit `aaa1367`.

### 10. Nits: wrapper y comentarios obsoletos

- **Decisión**: se quita `practicas_del_actor` (llamaba directamente a `practicas_visibles_para`) y se corrigen los comentarios de `config/urls.py` y de `prototipo/views.py` que decían que el demo todavía declara las rutas de prácticas y que su POST es «el mismo caso de uso» del endpoint real.
- **Por qué**: un wrapper de una línea oculta qué función aplica el alcance de filas; y los comentarios mentían tras retirar las rutas del demo.
- **Cambio**: `backend/apps/practicas/api.py`, `backend/config/urls.py`, `backend/apps/prototipo/views.py`; commit `aaa1367`.

### 11. docs/api.md y README de reportes reflejan lo que el PR hace

- **Decisión**: §2 (tabla de códigos con `practica_no_en_curso`, `semana_duplicada`, 401/404 del endpoint real y la nota de que 422 es solo del prototipo), §3, §4 y §5 describen los endpoints reales y las **rutas retiradas del demo** (`GET /api/v1/practicas/`, `GET /api/v1/practicas/<id>/` y `POST …/reportes/` con `multipart`, que dejaron de ser vistas de Django plano con `X-Rol`).
- **Por qué**: la documentación seguía describiendo el demo (multipart, evidencias, `422`) que ya no existe y habría llevado a un cliente a llamar a un contrato inexistente.
- **Cambio**: `docs/api.md` (commit `c480207`), `backend/apps/reportes/README.md` (commit `8c5dc00`).

### 12. Tamaño del PR: excepción documentada (no se divide)

- **Decisión**: no se divide #101. Con estas correcciones el PR suma unas 1 640 líneas añadidas y 527 quitadas en 29 archivos respecto de #100, y se acepta como excepción al máximo de ~400 líneas del issue #78 («Tamaño»).
- **Por qué**: dividirlo obligaría a reescribir la cadena ya apilada y revisada (#102 y #103 cuelgan de esta rama). La mayor parte son tests (el flujo y las pruebas de reglas del issue, criterio 4 de la rúbrica) y el retiro de rutas del demo; el código de producción nuevo es pequeño. Las correcciones de esta revisión se entregan en commits separados por unidad (migración, modelo, endpoint, documentación) para que se puedan revisar de a uno.
- **Cambio**: ninguno; documentado aquí.

### Pendiente en #101

- **RNF-05 (evidencias PDF ≤ 5 MB)** queda **fuera de #78 y pendiente de forma explícita**. spec.md:369 lo define («solo PDF, hasta 5 MB; un PDF de 5 MB se acepta y uno de 5,1 MB o un JPG/PNG se rechazan») y RF-02 (spec.md:274) lo delega ahí, pero el modelo de datos de #101 no tiene entidad de evidencia ni almacenamiento: el endpoint registra solo `semana` y `horas_reportadas`. No se inventa una subida de archivos en este PR; necesita su propio issue (almacenamiento, validación de formato/tamaño y permisos).
- Los textos de actividades y las versiones del reporte (devolución con versión nueva) siguen sin modelo; llegan con la validación del tutor (HU-03).
- Descripción del PR: dejar `Refs #77` en #100 y anotar aquí el tamaño y el RNF-05 pendiente (T6 de la revisión).

---

Las secciones de #102 y #103 se agregan a medida que se revisa cada PR.
