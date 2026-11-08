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
- **Actualización (merge de develop con la spec v0.4.0, APE 002)**: develop dejó S-02 «Por confirmar» con la pregunta abierta P-02 al docente. En el merge se toma esa versión: es la posición vigente del equipo y reemplaza la marca «fuente por enlazar». El código mantiene un solo tutor activo, que es lo que P-02 indica mientras se resuelve; la pregunta a Jaime por la fuente deja de hacer falta.

### 13. DRF sube a la línea 3.18 (vulnerabilidades de 3.16)

- **Decisión**: `djangorestframework>=3.18.2,<3.19` en lugar de `>=3.16,<3.17`.
- **Por qué**: el job «Security scan» de CI (`pip-audit`) falló en este PR: DRF 3.16.1 tiene cinco avisos conocidos (PYSEC-2026-3827, PYSEC-2026-3828, GHSA-33wh-fxxf-88vv, GHSA-3547-9m27-7rxg, GHSA-xw6w-gcfp-cf8m), corregidos en 3.18.2. La 3.18 declara soporte para Django 5.2, así que Django no cambia. Se verificó con `pip-audit` local (sin hallazgos) y con la suite completa de toda la cadena.
- **Cambio**: `backend/requirements.txt`.

### Pendiente en #98

- Descripción del PR: la sección «Impacto cruzado» quedó desactualizada (#81 y #82 ya están en develop y este PR aporta el `seed`). Se actualiza al publicar la rama.
- S-02 / P-02: confirmar con el docente si una práctica puede tener más de un tutor académico activo.
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
- **Por qué**: con `404` para la inexistente y `400` para la ajena, cualquiera podía averiguar qué ids de práctica existen: fuga de existencia. Un `400` tampoco es un permiso: un tutor no «envía datos inválidos», no tiene derecho a esta acción (RNF-02, spec.md:366: «responder 403 a cualquier acción fuera del rol del actor y no modificar ningún dato»; y el contrato de #100: 401/404 genéricos, 403 con `detail`). La búsqueda filtra por `estudiante_id` del actor guardado, así el 404 es el mismo por construcción.
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

## #102 — Autenticación y permisos (#79)

Rama `feature/s1-j4-auth-permisos`. Hallazgos de la revisión: el demo `X-Rol` seguía montado en `/api/v1/` y solo lo separaba `DEBUG`; `SIMPLE_JWT` con los valores por defecto de la librería (no los del ADR 0011) y el ADR aún «Propuesta»; el POST de reporte ajeno daba 403 mientras el detalle daba 404 (fuga de existencia); `/auth/token/` sin tope de intentos; schema y Swagger con `AllowAny`; sin prueba de que `X-Rol` se ignora. Las referencias a la spec son `specs/001-seguimiento-practicas/spec.md`; el issue es #79 y el método de autenticación, el [ADR 0011](../adr/0011-metodo-de-autenticacion-de-la-api.md).

### 1. Se integra #101 corregido con un merge y los cuatro conflictos se resuelven sumando los dos lados

- **Decisión**: la rama recibió el merge de `feature/s1-j3-flujo-reportes` ya corregida (`ae11a59`, «merge: integrar #78 corregido en #79»). Los cuatro archivos en conflicto se resolvieron conservando la autenticación real de #102 **y** todas las correcciones de #101:
  - `apps/reportes/api.py`: se queda el flujo de #101 completo (`actor_estudiante` con 401/403, búsqueda dentro de `transaction.atomic()` con `select_for_update` filtrada por `estudiante_id`, 404 idéntico, solo «en curso» → 409 `practica_no_en_curso`, `IntegrityError` acotado a `semana_duplicada`, `requiere_revision`) y se conservan las `permission_classes` de #102 (`rol_requerido(estudiante)` y el permiso de práctica visible), con `check_object_permissions` justo después de la búsqueda. Se descartan los chequeos de #102 que #101 reemplaza (`actor_guardado` con 400, `ESTADOS_FINALES`, 403 por objeto ajeno).
  - `config/urls.py`: se suman las rutas de token de #102 a las tres rutas de prácticas de #101; los comentarios que hablaban del demo compartiendo prefijo se actualizan (el demo se mueve en la decisión 2).
  - `tests/integration/test_reportes_flujo.py`: se toma el archivo de #101 (más completo) y se adapta a la autenticación: la lista anónima y la cuenta sin fila pasan de «200 vacío» a 401.
  - `tests/unit/test_envelope_exceptions.py`: se unen los imports de ambos lados y las sondas nuevas de #101 (409, 403 de DRF, rollback) usan el cliente autenticado de #102.
- **Por qué**: son dos ramas que cambian la misma vista por razones distintas: #101 corrige las reglas de negocio (RNF-02, escenario 1 de HU-02) y #102 añade la frontera de identidad (RNF-01). Descartar cualquiera deshace una revisión ya hecha. Donde #102 afirmaba 403 para el POST de una práctica ajena, gana la decisión de #101 (404 idéntico): el 403 por objeto confirmaba que el id existe.
- **Un ajuste de semántica que salió del merge**: una cuenta inactiva, borrada o sin guardar responde 401, no 403. #101 ya lo exigía en el POST (spec.md:366 pide 403 solo para «acciones fuera del rol del actor»; sin credenciales vigentes no hay actor) y #102 daba 403 en la lista. Se unifica con el mixin `SinFilaEs401`, que solo cambia cómo la vista traduce el rechazo; los permisos siguen devolviendo `False`, así que las pruebas unitarias de #102 no cambian.
- **Cambio**: `ae11a59`; `apps/seguridad/permissions.py` (`SinFilaEs401`, `rol_requerido(..., mensaje=)`), `apps/practicas/api.py`, `apps/reportes/api.py`, `config/urls.py` y los tests citados. En el mismo commit se retira `MENSAJE_NO_AUTENTICADO`, que ya no tenía usos. Suite tras el merge: 522 pruebas, OK.

### 2. El demo `X-Rol` sale de `/api/v1/` y pasa a `/prototipo/api/v1/`

- **Decisión**: las rutas JSON del demo (alertas, cierre, historial, legalización, pendientes) se montan en `prototipo/api/v1/`. Una ruta de negocio de `/api/v1/` con `X-Rol` y sin token responde 401 con el envelope, con `DEBUG` encendido y apagado; las rutas viejas del demo responden 404. El JS y las plantillas toman la URL de `{% url %}`, así que solo cambió el texto fijo de `indice.html`; los tests del demo siguen la ruta nueva.
- **Por qué**: con el demo y la API real bajo el mismo prefijo, la única barrera entre un header sin identidad y datos reales era `DEBUG`. RNF-01 (spec.md:365) exige inicio de sesión en todas las rutas protegidas, y una frontera que depende de una bandera de entorno es una configuración errónea lejos de abrir el sistema. Separar los prefijos hace que `/api/v1/*` no tenga ningún camino que lea `X-Rol`. La prueba cubre ambos modos de `DEBUG` y todos los roles del demo, incluidos director y Secretaría.
- **Cambio**: `076e236`; `config/urls.py`, `templates/practicas/indice.html`, tests del prototipo y `tests/integration/test_demo_xrol_aislado.py`. Los `url` de `dto.py` (`/api/v1/practicas/<id>/`) apuntan a la API real y no cambian.

### 3. `SIMPLE_JWT` según el ADR 0011, con rotación, lista de bloqueo y logout

- **Decisión**: `ACCESS_TOKEN_LIFETIME` 15 minutos, `ROTATE_REFRESH_TOKENS` y `BLACKLIST_AFTER_ROTATION` activos, `rest_framework_simplejwt.token_blacklist` en `INSTALLED_APPS`. Se elige además `REFRESH_TOKEN_LIFETIME` de 30 minutos. Nuevo `POST /api/v1/auth/logout/`: exige un access vigente y bloquea el refresh que recibe; un refresh ausente, inválido, ya revocado o **de otra cuenta** responde 400 y no revoca nada. Renovar ahora devuelve `{access, refresh}` y el refresh usado deja de servir (401).
- **Por qué**: el ADR 0011 recomendaba exactamente esto (access corto, refresh con rotación y `token_blacklist`) y #102 lo ignoró dejando los valores por defecto de la librería (5 minutos y 1 día, sin revocación): sin blacklist no hay forma de cerrar una sesión robada. RNF-03 (spec.md:367) pide cerrar la sesión tras 30 minutos de inactividad; el ADR no fijó la vida del refresh, así que se deriva de ese requisito: con rotación, cada renovación abre otra ventana de 30 minutos y 30 minutos sin renovar la cierran, mientras un cliente activo renueva cada ≤ 15 minutos. El refresh ajeno se trata como inválido (400 igual) para que el logout no sea un oráculo de qué tokens existen ni permita cerrar sesiones de otros.
- **Cambio**: `9dfe7c6`; `config/settings.py`, `apps/seguridad/api.py` (`LogoutView`), `config/urls.py` y `tests/integration/test_auth_sesion.py` (rotado y revocado rechazados con 401, otro usuario no se revoca, otras sesiones de la cuenta siguen).

### 4. Tope de intentos en `/api/v1/auth/token/` (`ScopedRateThrottle`, scope «auth», 5/min)

- **Decisión**: `throttle_scope = "auth"` con `DEFAULT_THROTTLE_RATES = {"auth": "5/min"}`; el sexto intento en un minuto responde 429 con el envelope, `code: demasiadas_solicitudes` y `Retry-After`. Cuentan los intentos correctos y los fallidos; renovar y la API de negocio no se limitan. El handler del contrato traduce `Throttled` a un texto en español.
- **Por qué**: sin tope, el login admite fuerza bruta de contraseñas, y RNF-03 (spec.md:367) protege las credenciales. El tope va solo donde se comprueban contraseñas; limitar el refresh o la API castigaría a clientes legítimos. Las pruebas que piden tokens limpian la cache en `setUp`: el contador vive en la cache y, sin limpiarla, una prueba heredaría los intentos de la anterior.
- **Cambio**: `9dfe7c6`; `config/settings.py`, `apps/seguridad/api.py`, `apps/contrato/exceptions.py` (+ README del contrato) y `test_auth_sesion.py`. Límite conocido: la cache por defecto es local al proceso, así que con varios procesos el tope es por proceso; hoy el contenedor corre uno solo (ADR 0011, «Límites conocidos»).

### 5. Schema y Swagger: anónimos solo con `DEBUG`; con `DEBUG` apagado exigen JWT

- **Decisión**: `SERVE_PERMISSIONS` pasa de `AllowAny` a `AbiertoSoloEnDebug`, que decide por petición: `DEBUG` encendido → abierto; si no, exige una cuenta guardada y activa (401 sin token). El login y `/health/` siguen abiertos.
- **Por qué**: RNF-01 (spec.md:365) exime únicamente «la ruta de inicio de sesión y el endpoint de salud»; un schema público en producción describe todas las rutas, campos y errores a quien aún no se ha autenticado. Decidirlo por petición (no al importar) hace que apagar `DEBUG` cierre el acceso sin reiniciar. Efecto práctico: Swagger UI no es navegable en producción (el navegador no envía `Authorization` al abrir la página); el schema sí se obtiene con el access, y en desarrollo todo sigue abierto.
- **Cambio**: `4c9c53e`; `apps/seguridad/permissions.py`, `config/settings.py`, `test_auth_sesion.py` y los tests que leen el schema anónimo, que ahora declaran `DEBUG` (el runner de Django lo apaga).

### 6. El POST de reporte ajeno sigue en 404 idéntico tras las permission classes

- **Decisión**: se verifica y se fija con prueba: un estudiante que envía a la práctica de otro y a un id inexistente recibe el mismo 404 (cuerpo idéntico) y no se escribe nada. La prueba de #102 que esperaba 403 se reescribe.
- **Por qué**: es la decisión 2 de #101 y la razón de fondo es la misma (no filtrar existencia). El permiso de objeto no la contradice porque la búsqueda ya acota a las prácticas del estudiante: el permiso nunca ve una práctica ajena.
- **Cambio**: `ae11a59`; `tests/integration/test_auth_seguridad.py`. README de seguridad actualizado.

### 7. Nits

- **Decisión**: (a) `MENSAJE_NO_AUTENTICADO` eliminado (sin usos; se retiró en el merge, `ae11a59`); (b) `PermitirObjetoAlDueno` → `PermitirPracticaVisible`; (c) la matriz HTTP 403 de reportes incluye director y Secretaría; (d) una sola fuente de mensajes de permiso.
- **Por qué**: (b) el permiso no pregunta por el dueño sino por el alcance de T019, que incluye tutores, coordinador, director y Secretaría: el nombre engañaba al lector. (c) spec.md:295 define la matriz con seis actores y RNF-02 (spec.md:366) pide probar «cada combinación rol × acción no permitida»: la prueba omitía dos. (d) el texto del 403 estaba escrito en dos sitios (la vista y el permiso); ahora es `MENSAJE_ACTOR`, que `rol_requerido(..., mensaje=)` recibe, y las pruebas importan las constantes del contrato en vez de copiar textos.
- **Cambio**: `0c86025`.

### 8. Documentación y ADR

- **Decisión**: el ADR 0011 pasa a «Aceptada» con los valores efectivos (15/30 minutos, rotación, blacklist, logout, tope) y los límites conocidos; `docs/api.md` gana la sección 10 (token, refresh, logout, códigos 401/429) y todas las rutas del demo apuntan a `/prototipo/api/v1/`; el README de seguridad deja de decir que la blacklist no estaba habilitada y anota que el permiso de las transiciones de estado vive en el servicio `cambiar_estado_practica` (#98), no en clases DRF de vista.
- **Por qué**: el ADR estaba «Propuesta» con un pendiente que este PR cierra; documentar un contrato que no es el implementado es peor que no documentarlo. Duplicar el permiso de transiciones en la vista habría creado dos fuentes para la misma regla (RF-13).
- **Cambio**: commits `docs(adr)`, `docs(api)`, `docs(seguridad)` y `docs(contrato)` de esta rama.

### 9. El tope de intentos no se evade cambiando `X-Forwarded-For`

- **Decisión**: `REST_FRAMEWORK['NUM_PROXIES'] = 0`, así el tope de `/api/v1/auth/token/` identifica al cliente por `REMOTE_ADDR`. Prueba: cinco intentos fallidos con una `X-Forwarded-For` distinta cada vez y el sexto responde 429.
- **Por qué**: la verificación independiente de seguridad encontró que, sin `NUM_PROXIES`, DRF usa la cabecera `X-Forwarded-For` completa como identidad del cliente (`rest_framework/throttling.py`, `get_ident`). Esa cabecera la escribe el cliente cuando no hay proxy delante, así que cambiarla en cada intento daba intentos de contraseña ilimitados y anulaba el tope de 5 por minuto del ADR 0011. Hoy no hay proxy delante (compose expone `runserver` directo); si se despliega detrás de uno, el valor pasa a ser la cantidad de proxies de confianza.
- **Cambio**: `config/settings.py` (`REST_FRAMEWORK`), `tests/integration/test_auth_sesion.py` (`test_cambiar_x_forwarded_for_no_reinicia_el_conteo`, rojo observado antes del cambio).

### 10. simplejwt sube a 5.5.1 (PYSEC-2026-1305)

- **Decisión**: `djangorestframework-simplejwt>=5.5.1,<5.6` en lugar de `>=5.4,<5.5`.
- **Por qué**: `pip-audit` (el mismo chequeo del job «Security scan» de CI) marca PYSEC-2026-1305 en simplejwt 5.4.0, corregido en 5.5.1. La 5.5.1 declara soporte para Django 5.2 y DRF ≥ 3.14, así que convive con DRF 3.18 (decisión 13 de #98). Suite completa y `pip-audit` sin hallazgos tras el cambio.
- **Cambio**: `backend/requirements.txt`.

### Pendiente en #102

- La cache del tope de intentos es local al proceso; con varios procesos hay que pasar a una cache compartida.
- La limpieza de tokens vencidos de la lista de bloqueo (`manage.py flushexpiredtokens`) no está programada.
- Otros documentos fuera de esta revisión mencionan las rutas viejas del demo (`README.md`, `CONTRIBUTING.md`, `docs/trazabilidad.md`, `docs/bpmn/`, `docs/portal/`, `specs/002-api-alertas-cierre/`) y deben actualizarse a `/prototipo/api/v1/`. **Cerrado en #103**, decisión 8.
- `docs/seguridad.md` (R-03, `csrf_exempt` del PATCH) no se tocó; sigue describiendo el demo.
- La descripción del PR #102 debe citar `Closes #79` y la excepción de tamaño si aplica (T6 de la revisión).

---

## #103 — pytest y cobertura (#80)

Rama `feature/s1-j5-pytest`. Hallazgos de la revisión: `[coverage:*]` en `pytest.ini` se ignoraba (pytest-cov no lo lee); el comando documentado no generaba `coverage.xml` (Sonar lo espera en `backend/coverage.xml`) ni medía `config/`; el marcador `security` no cubría `test_seguridad.py`; PostgreSQL no estaba verificado; y `test_pytest_config.py` (funciones sueltas de pytest) no corría con `manage.py test`. Los recuentos de cada runner se toman con `DJANGO_DEBUG=True` desde `backend/`.

### 1. Se integra #102 corregido con un merge y se corrige el desfase que dejó

- **Decisión**: la rama recibió el merge de `feature/s1-j4-auth-permisos` ya corregida (`e7131a7`, «merge: integrar #79 corregido en #80»), sin conflictos. Se corrió la suite completa con los dos runners **antes** de tocar nada: `manage.py test` 545 pruebas OK (1 omitida) y `pytest` 547 pasadas + 1 omitida = 548. Las 3 de diferencia eran las funciones de `test_pytest_config.py`, que Django no descubre (decisión 5). Las pruebas añadidas en #98–#102 sí se recolectaron, pero el conftest no las clasificaba (decisión 4) y el README prometía correr pytest sin variables aunque, desde #98, los settings fallan cerrado sin `POSTGRES_*` y con `DEBUG` apagado.
- **Por qué**: un merge limpio no prueba que las piezas de #103 sigan describiendo la suite: #103 se escribió contra 459 pruebas y hoy son 551, y el fallo cerrado de #98 invalidó una afirmación de su README. Medir primero evita corregir de memoria.
- **Cambio**: `e7131a7` (merge); `277ac73` y `0af42c4` (correcciones). El comentario de `pytest.ini` con «459» deja de citar cifras: dice que ambos runners deben reportar el mismo total.

### 2. La cobertura vive en `backend/.coveragerc` y mide `apps` y `config`

- **Decisión**: `[coverage:*]` sale de `pytest.ini` y pasa a `.coveragerc`: `source = apps, config`, `show_missing`, `skip_empty`, y `omit` de migraciones y de los archivos de test (`tests.py`, `tests_*.py`, `test_*.py`, `tests/`). Se verificó que `cd backend && python -m pytest --cov --cov-report=xml:coverage.xml --cov-report=term-missing` escribe `backend/coverage.xml` con las dos fuentes (`apps/` y `config/`), sin tests ni conftest: 97 % sobre 2601 sentencias en SQLite. Una sonda (`test_cov_documentado_mide_apps_y_config_y_escribe_xml`) lo fija en la suite.
- **Por qué**: pytest-cov delega en coverage.py, que solo lee `.coveragerc`, `setup.cfg`, `tox.ini` o `pyproject.toml`; las secciones `[coverage:*]` de `pytest.ini` eran letra muerta, y `--cov` sin valor medía además los tests y el conftest (comprobado antes del cambio), lo que infla el porcentaje. El comando lleva `--cov` **sin valor** a propósito: `--cov=apps` pisaría `source` y dejaría `config/` sin medir. Se omiten los archivos de test porque medir las pruebas contra sí mismas no informa de la calidad del código. Sonar lee `backend/coverage.xml`, de ahí `--cov-report=xml:coverage.xml`.
- **Cambio**: `277ac73`; `backend/.coveragerc`, `backend/pytest.ini`. Efecto colateral aceptado: CI corre `coverage run --source=apps,config` desde `backend/`, así que también lee `.coveragerc` y su porcentaje deja de contar migraciones y archivos de test; es la medición que se quiere y no cambia el comando de CI.

### 3. Comando CI-compatible documentado en el README del backend

- **Decisión**: `backend/README.md` documenta `cd backend && python -m pytest --cov --cov-report=xml:coverage.xml --cov-report=term-missing` como el comando para CI; aclara que `coverage.xml` y `.coverage` son artefactos que no se commitean y que `DJANGO_DEBUG=True` es lo que habilita el SQLite local (`make test` ya lo exporta). Se corrige el comentario duplicado del ejemplo (`# 11 tests de la unidad   # archivo o caso puntual`) y se quita la afirmación de que PostgreSQL no se corría en local.
- **Por qué**: un comando que no se puede copiar y pegar a CI no sirve de contrato; y el README de #103 prometía que pytest corre sin variables, lo que dejó de ser cierto con el fallo cerrado de #98.
- **Cambio**: `0af42c4`; `backend/README.md`.

### 4. El marcador `security` cubre «seguridad» y los `test_auth_*`; los `test_envelope_*` llevan `api`

- **Decisión**: el conftest asigna `security` a todo módulo con «seguridad» en el nombre (`test_seguridad.py`, `test_auth_seguridad.py`) o con prefijo `test_auth_` (`test_auth_sesion.py`), y `api` a `test_envelope_*`. `pytest -m security` pasa de 19 a 48 pruebas y `-m api` de 54 a 78; dos sondas lo fijan listando los módulos que cada marcador recolecta.
- **Por qué**: el mapa buscaba la subcadena `auth_seguridad`, que no aparece en `test_seguridad.py` ni en `test_auth_sesion.py` (#102), así que `pytest -m security` omitía las pruebas de autenticación más importantes. El envelope (#100) es la superficie HTTP de la API y debe entrar en `-m api`. No se añadieron `test_demo_xrol_aislado.py` ni `test_aislamiento_roles.py`: la decisión pedía seguridad y auth, y ampliar el criterio corresponde a quien defina la política de marcadores.
- **Cambio**: `277ac73`; `backend/conftest.py` (tabla y docstring), `backend/pytest.ini` (descripción del marcador).

### 5. `test_pytest_config.py` pasa a `SimpleTestCase` y el probe de marcadores no fija el exit code

- **Decisión**: las funciones sueltas pasan a una clase `SimpleTestCase`, así `manage.py test` también las corre (6 pruebas, con las 3 sondas nuevas). El probe de `--strict-markers` ya no exige el exit code 3: exige que falle (código distinto de 0) y que la salida nombre un marcador no registrado.
- **Por qué**: una suite con pruebas que solo un runner ejecuta describe dos suites distintas (545 frente a 548). Fijar el exit code 3 acopla la prueba a cómo pytest reporta el caso (INTERNALERROR hoy; error de uso en otras versiones), y lo que importa es que un marcador no registrado nunca pase en silencio.
- **Cambio**: `277ac73`; `backend/tests/unit/test_pytest_config.py`. Las sondas usan `COVERAGE_FILE` en un directorio temporal para no ensuciar `backend/`.

### 6. CI sigue con `manage.py test` + `coverage` en esta cadena

- **Decisión**: `.github/workflows/ci.yml` no se toca. El job `test` mantiene `coverage run --source=apps,config manage.py test`, `coverage report` y `coverage xml`. El cambio a `pytest --cov` va en un PR propio de Alejandro después del merge de la cadena.
- **Por qué**: el job actual funciona, mide lo mismo (comparte `.coveragerc`) y sube el mismo `coverage.xml`; cambiarlo mezcla la migración de la suite con la zona y el riesgo de entrega de CI, que tiene otro dueño y otro ciclo de revisión. El comando de pytest ya queda probado y documentado para que ese PR sea un cambio de una línea.
- **Cambio**: ninguno en el workflow; el README del backend y el portal (`ejecucion-pruebas.qmd`) dicen que CI usa `manage.py test` hoy.

### 7. PostgreSQL 16: 551 pruebas OK con los dos runners

- **Decisión**: se corrió la suite contra `postgres:16` en un contenedor temporal (`docker run -d --rm -p 127.0.0.1::5432`, puerto efímero, contraseña de un solo uso), con el entorno de CI (`DJANGO_DEBUG=False`, `POSTGRES_*`, clave de prueba): `pytest` 551 pasadas, 0 omitidas, y `manage.py test` 551 OK. El contenedor se detuvo al terminar. En SQLite ambos runners dan 551 con 1 omitida.
- **Por qué**: bajo SQLite se omite el test que necesita `select_for_update` (`has_select_for_update`), así que la carrera de estado de #101 solo se verifica de verdad en PostgreSQL; allí corre completo (por eso 0 omitidas). CI levanta `postgres:17-alpine`: la 17 solo la ejerce CI.
- **Cambio**: sin cambios de código; el resultado queda aquí y en `backend/README.md`.

### 8. Cierre de «Pendiente en #102»: las rutas del demo en la documentación

- **Decisión**: alertas, cierre, historial, legalización y pendientes pasan de `/api/v1/` a `/prototipo/api/v1/` en `README.md`, `CONTRIBUTING.md`, `docs/trazabilidad.md`, `docs/bpmn/` (análisis y `.bpmn`), `docs/portal/` y `specs/002-api-alertas-cierre/plan.md`. Se verificó contra `config/urls.py` y `apps/prototipo/api_urls.py`: siguen en `/api/v1/` solo `practicas/`, `practicas/<id>/`, `practicas/<id>/reportes/`, `auth/token/`, `auth/token/refresh/`, `auth/logout/`, `schema/` y `docs/`, y esas no se tocaron. Dos cambios adicionales porque la misma edición los exigía: `api-openapi.qmd` separa la API real del demo (y deja de decir que Swagger no existe), y la matriz de trazabilidad actualiza las líneas de `api.py` y reapunta RF-02, RF-05 y RF-06 a las vistas reales y a sus pruebas, porque las rutas de demo de prácticas y reportes y las pruebas que citaban se retiraron en #101. No se tocaron los archivos de evidencia históricos (`evidencias/`).
- **Por qué**: la documentación seguía diciendo que el demo `X-Rol` vive en `/api/v1/`, justo lo que #102 corrigió; un lector podría llamar a una ruta que ahora responde 401 o 404 y concluir que la API está rota. Las evidencias históricas describen lo que se midió en su fecha y reescribirlas falsearía el registro.
- **Cambio**: `b0afc8e` (sustitución de rutas y matriz) y `c39a835` (portal: `api-openapi.qmd`, `instalacion.qmd`, `ejecucion-pruebas.qmd`).

### Pendiente en #103

- Cambiar CI a `pytest --cov` (PR propio de Alejandro, decisión 6).
- `backend/coverage.xml` y `backend/.coverage` no están en `.gitignore` (archivo fuera de esta revisión): quedan como untracked tras correr el comando documentado.
- Los módulos legados de `apps/prototipo/tests*.py` siguen sin marcadores por diseño de #80.

---

### pytest sube a 9.0.3 (PYSEC-2026-1845)

- **Decisión**: `pytest>=9.0.3,<10` en `backend/requirements-dev.txt`, en lugar de `>=8,<9`.
- **Por qué**: el job «Security scan» de CI corre `pip-audit -r backend/requirements-dev.txt`, que marca PYSEC-2026-1845 en pytest 8.4.2 (corregido en 9.0.3). pytest-django 4.14 y pytest-cov 6.3 funcionan con la línea 9: con `manage.py test` 556 OK y con `pytest` 555 pasadas + 1 omitida, y el comando de cobertura sigue escribiendo `coverage.xml`.
- **Cambio**: `backend/requirements-dev.txt`.

## Pendientes

Lista consolidada de lo que sigue abierto tras la cadena. Cada punto remite a la sección donde se decidió.

1. **RNF-05 (evidencias PDF ≤ 5 MB)** en la API real: sin modelo ni almacenamiento; necesita su propio issue (#101, pendiente).
2. **Carrera obligatoria por rol** de `Usuario`: queda sin restricción en la base (#98, decisión 4).
3. **S-02 / P-02**: develop (spec v0.4.0) la dejó como pregunta abierta al docente; el código implementa un solo tutor activo mientras se resuelve (#98, decisión 12).
4. **Actividades y versiones del reporte** sin modelo; llegan con la validación del tutor, HU-03 (#101).
5. **`manage.py flushexpiredtokens`**: sin tarea programada que limpie la lista de bloqueo de tokens (#102).
6. **Tope de intentos por proceso**: la cache local no se comparte entre procesos; pasar a una cache compartida si hay más de uno (#102, decisión 4).
7. **`docs/seguridad.md`** (R-03, `csrf_exempt` del PATCH) sigue describiendo el demo (#102).
8. **CI a pytest**: `ci.yml` sigue con `manage.py test` + `coverage`; PR propio de Alejandro tras el merge (#103, decisión 6).
9. **`.gitignore`** sin `coverage.xml` ni `.coverage` (#103).
10. **Preguntas abiertas de la spec v0.4.0 que el código ya responde de forma provisional**: P-06 (semana repetida: #101 la rechaza con 409 `semana_duplicada`) y P-08 (identificación ante la API: #102 implementa JWT y deja el ADR 0011 «Aceptada»). Si el docente responde distinto, se ajusta el código y no al revés.
11. **Swagger UI con `DEBUG` apagado** no es navegable en un navegador (no envía `Authorization`); el schema sí se obtiene con el access (#102, decisión 5).
12. **PostgreSQL 17**: solo la ejerce CI; en local se verificó la 16 (#103, decisión 7).
