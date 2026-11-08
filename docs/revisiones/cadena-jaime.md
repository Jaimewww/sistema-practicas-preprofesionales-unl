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

---

Las secciones de #101 a #103 se agregan a medida que se revisa cada PR.
