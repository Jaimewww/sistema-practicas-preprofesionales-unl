# Actividades: plan de actividades, validación, confirmación de entidad, informe final e informe del estudiante

Entidades `PlanActividades` (HU-01/RF-01), `Validacion` (RF-03/RF-04),
`ConfirmacionEntidad` e `InformeFinal` (RF-08/HU-07) y `InformeEstudiante`
(RF-16/HU-10), más los servicios internos que las mueven: enviar, devolver y
aprobar el plan, confirmar el reporte y registrar el informe final del tutor de
entidad, y presentar, reenviar, validar y devolver el informe final del
estudiante, con su API REST (S8). No incluye plantillas, reportes semanales (son
de `apps.reportes`) ni evidencias del prototipo.

## Ruta rápida

1. Modelos: `backend/apps/actividades/models.py` (`PlanActividades`, `Validacion`,
   `ConfirmacionEntidad`, `InformeFinal`, `InformeEstudiante`).
2. Servicios: `backend/apps/actividades/services.py` (`enviar_plan`, `devolver_plan`,
   `aprobar_plan`, `confirmar_reporte`, `registrar_informe_externo`,
   `presentar_informe_final`, `reenviar_informe_final`, `validar_informe_estudiante`,
   `devolver_informe_estudiante`).
3. Migraciones: `backend/apps/actividades/migrations/0001_initial.py`,
   `0002_validacion.py`, `0005_confirmacion_entidad_informe_final.py` y
   `0006_informe_estudiante.py`.
4. Pruebas: `backend/tests/unit/test_plan_actividades.py` (modelo),
   `backend/tests/unit/test_actividades_entidad.py` (invariantes de RF-08),
   `backend/tests/unit/test_validacion_informe.py` (restricción «uno de tres»),
   `backend/tests/integration/test_plan_actividades.py` (acciones),
   `backend/tests/integration/test_tutor_entidad.py` (HU-07 por HTTP) y
   `backend/tests/integration/test_informe_final.py` (RF-16 por HTTP).
   `0002_validacion.py` y `0005_confirmacion_entidad_informe_final.py`.
4. API: `backend/apps/actividades/api.py` y `serializers.py` (S8).
5. Pruebas: `backend/tests/unit/test_plan_actividades.py` (modelo),
   `backend/tests/unit/test_actividades_entidad.py` (invariantes de RF-08),
   `backend/tests/integration/test_plan_actividades.py` y `test_plan_api.py`
   (acciones y endpoints), `backend/tests/integration/test_tutor_entidad.py`
   (HU-07 por HTTP).

Fuente: `specs/001-seguimiento-practicas/data-model.md` (apartados `PlanActividades`,
`Validacion`, `ConfirmacionEntidad` e `InformeFinal`), RF-01/RF-03/RF-08 y T021 a T024
más T047 a T049 en `specs/001-seguimiento-practicas/tasks.md`.

## Campos y reglas

| Campo | Tipo | Regla |
| --- | --- | --- |
| `practica` | FK a `practicas.Practica` | Obligatorio; `PROTECT` |
| `version` | entero positivo | Inicial 1; entero positivo; la aporta quien crea la fila |
| `contenido` | texto | Obligatorio |
| `estado` | `en_revision`, `aprobado` o `devuelto` | Inicial `en_revision` |

`__str__` devuelve `Plan v<version> - práctica <id>`. `practica` expone las filas
como `practica.planes_actividades`; es una decisión técnica de esta unidad.

## Versión inicial

El data-model define `version` como «Número de versión del plan. Incremental por
devolución». De ahí sale solo la numeración: la primera fila es la versión **1**
y el campo tiene `default=1`. No se inventa nada más:

- El modelo **no incrementa** la versión al guardar ni renumera filas: crear otra
  fila con `version=2` es una escritura explícita, y la fila anterior se conserva.
- La pareja (`practica`, `version`) es única en la base (`UniqueConstraint`): la
  invariante no depende solo del bloqueo del servicio, así que el admin, el seed o
  un servicio futuro tampoco pueden duplicar una versión. No hay «versión activa».
- La versión siguiente nace cuando el estudiante **reenvía tras una devolución**;
  la devolución no crea versión. El envío, la devolución y la aprobación los decide
  el servicio de abajo; el modelo no incrementa nada por su cuenta.

Evidencia disponible: el prototipo no guarda un campo `version` en el plan (su
`_plan` en `apps/prototipo/sample_data.py` solo tiene estado, fechas,
observación y actividades), así que no hay un valor de prototipo que copiar. El
vocabulario de estados sí difiere: el prototipo muestra `validado` para el plan
mientras el data-model define `aprobado`. Esta unidad sigue el data-model y no
modifica los consumidores del prototipo.

## Estados y conservación

`estado` inicia en `en_revision`. Aprobar y devolver los mueve el servicio, y el
modelo solo rechaza valores fuera del vocabulario. Las filas de versiones
anteriores no se borran ni se sobrescriben al registrar otra versión, y
`PROTECT` impide eliminar una práctica que tenga planes o validaciones.

## Acciones del plan (T024)

`apps/actividades/services.py` implementa las tres transiciones y falla cerrado
con `ValidationError` en la clave del campo (`autor`, `estado`, `plan`,
`observacion`, `practica`); no hay `PermissionDenied` ni códigos HTTP porque las
vistas son T025.

| Acción | Actor exigido | Efecto |
| --- | --- | --- |
| `enviar_plan(practica=, contenido=, autor=)` | Estudiante activo de la práctica | Crea la versión máxima + 1 (la 1 si no hay plan) `en_revision`; rechaza si la última versión está `en_revision` o `aprobado` |
| `devolver_plan(plan=, autor=, observacion=)` | Tutor académico activo de la práctica | `Validacion` devuelto y la misma fila queda `devuelto`; no crea versión |
| `aprobar_plan(plan=, autor=)` | Tutor académico activo de la práctica | `Validacion` aprobado, fila `aprobado` y práctica a `en_curso` vía T017 |

La versión, el estado y la entidad los decide el servicio: no son parámetros y
pasarlos es `TypeError`. El permiso se resuelve contra la fila guardada del actor
(`pk`), así que un objeto del llamador desactualizado, inactivo, borrado o sin
asignación con `hasta` nulo falla cerrado, y `is_staff`/`is_superuser` no evita la
regla.

- `enviar_plan` comprueba al actor antes del estado de la práctica; una práctica
  `cerrada` o `cancelada` lanza el `MENSAJE_TERMINAL` de T017.
- `enviar_plan` rechaza (clave `estado`, `MENSAJE_REENVIO`) si la última versión
  está `en_revision` o `aprobado`: la versión es «incremental por devolución», así
  que solo tras una devolución nace la siguiente, con el contenido corregido. El
  permiso y el estado final de la práctica se resuelven antes.
- `devolver_plan` exige observación no vacía (la guarda recortada), marca la fila
  `devuelto` y devuelve esa misma fila (HU-01 criterio 2, Art. 336a); el estudiante
  lee la observación en `plan.validaciones`.
- `aprobar_plan` no envuelve el rechazo de T017: si la práctica no recorre la
  arista, el `ValidationError` sube tal cual y la transacción no deja el plan
  aprobado. Una práctica ya `en_curso` es idempotente: no repite historial.
- La versión se calcula como máximo registrado + 1 con la fila de la práctica
  bloqueada (`select_for_update`), y la `UniqueConstraint` de (`practica`,
  `version`) la respalda en la base. Con el rechazo del reenvío no puede haber dos
  versiones `en_revision` a la vez por el servicio.

## Endpoints (S8)

Contrato completo, orden de comprobación y códigos en `docs/api.md` §5.4.

| Ruta | Actor | Respuesta |
| --- | --- | --- |
| `GET /api/v1/practicas/<id>/plan/` | Quien ve la práctica (`practicas_visibles_para`) | `200`, versiones de la más nueva a la más antigua |
| `POST /api/v1/practicas/<id>/plan/` `{contenido}` | Estudiante de la práctica | `201`, la versión creada |
| `POST /api/v1/planes/<id>/aprobar/` | Tutor académico con asignación activa | `200`, plan aprobado y práctica en curso |
| `POST /api/v1/planes/<id>/devolver/` `{observacion}` | Tutor académico con asignación activa | `200`, plan devuelto |

Sin token 401, rol ajeno 403, fuera de alcance el mismo 404 que inexistente, cuerpo
inválido 400 y 409 con `practica_no_admite_plan`, `plan_no_reenviable` o
`plan_no_en_revision`. La vista exige la práctica «asignada» o «en curso» antes de
llamar al servicio: el servicio solo rechaza el envío en un estado final y, al
aprobar, una práctica suspendida daría la clave «autor» del coordinador.

Orden de bloqueo: el envío bloquea solo la fila de la práctica (`select_for_update`)
y lee los planes sin bloquearlos, así que nunca espera por una fila de plan;
aprobar y devolver bloquean el plan y después la práctica (vista y servicio, en
ese orden). Las decisiones son las únicas que esperan con una fila tomada, y el
envío no espera por planes: no hay ciclo de espera.

## Validación (T023, adelantado)

`Validacion` guarda `practica`, el `plan`, el `reporte` semanal **o** el
`informe_estudiante` al que se refiere, `decision` (`aprobado` o `devuelto`),
`observacion`, `autor` y `fecha` automática. El data-model pide «exactamente uno de
los dos» entre `plan_id` y `reporte_id`; RF-16 lo extiende a «exactamente uno de
tres» —plan, reporte o informe final del estudiante— porque la decisión de C-04 es
la misma para los tres documentos (Corte B, plan:103-127). La `CheckConstraint`
`actividades_validacion_plan_reporte_o_informe` lo impone en la base y `clean()` lo
repite dentro de `full_clean()`, así que `objects.create()` con dos referencias o
con ninguna falla con `IntegrityError` y `full_clean()` con `ValidationError` en
`reporte`. `observacion` es obligatoria cuando la decisión es `devuelto` (se valida
en `clean()` dentro de `full_clean()`) y aprobar puede ir sin observación. `autor`
lo escribe el servicio que valida y `fecha` la pone la base al insertar (RF-04). El
servicio de aprobación de planes (T024) sigue escribiendo la validación con `plan`
y sin `reporte`; el de reportes (`apps.reportes.services`) con `reporte` y sin
`plan`; el del informe del estudiante con `informe_estudiante` y sin los otros dos.

### Migración `0006_informe_estudiante`

Es **una sola migración** con una sola recreación de la restricción: `RemoveConstraint`
de `actividades_validacion_plan_o_reporte` y `AddConstraint` de
`actividades_validacion_plan_reporte_o_informe`, más la tabla nueva y la columna
opcional `validacion.informe_estudiante_id`. Las filas existentes ya cumplían
«exactamente uno de plan o reporte», que es uno de los tres casos de la regla
nueva, así que **no hay reescritura de datos**: la columna nueva entra en `NULL` y
cada fila anterior satisface el primer o el segundo disyunto. No hay `RunSQL` ni
`RunPython`.

## Límite de validación

Las reglas se validan con `full_clean()`. Este modelo no llama a
`full_clean()` desde `save()` ni desde `objects.create()`, así que esas dos
rutas no ejecutan las validaciones de esta entidad (la afirmación es sobre este
modelo, no sobre cualquier subclase de Django).

La versión la comprueba el validador de campo `validar_version_positiva`, que
Django ejecuta dentro de `Field.clean()` **después** de convertir el valor. Un
valor no numérico falla como `ValidationError` de campo en `version` y nunca
llega al validador, así que `full_clean()` agrega el error en lugar de lanzar
un `TypeError`. Una versión numérica menor que 1 se reporta en el campo
`version` con «La versión del plan debe ser un número entero positivo.». La única
regla replicada en la base es la unicidad de (`practica`, `version`); las pruebas
corren sobre SQLite en memoria y no son verificación de PostgreSQL.

## Fuera de esta unidad

Plantillas de T025, reportes semanales (son de `apps.reportes`), evidencias del
prototipo. La confirmación de entidad y el informe externo sí están aquí: sus dos
vistas HTTP viven en `apps.reportes.api` y `apps.practicas.api`, y el adaptador
es fino. `reporte_id` de `Validacion` llega con el reporte; editar el contenido
de un plan por servicio tampoco está aquí (el contenido entra en `enviar_plan`).

El cierre de la práctica (RF-09) **no** está aquí: registrar el informe final no
cambia `Practica.estado` ni escribe `HistorialEstado`.

## Checklist

- [ ] `apps.actividades` figura en `INSTALLED_APPS`.
- [ ] El plan nace en `en_revision` con versión 1 y su contenido.
- [ ] `full_clean()` rechaza campos obligatorios ausentes, estados fuera del
      vocabulario y versiones no positivas.
- [ ] Una versión no numérica produce un `ValidationError` en `version` y no un
      `TypeError`.
- [ ] Dos versiones explícitas conviven como filas separadas y la anterior no cambia.
- [ ] Repetir la versión de una práctica lanza `IntegrityError`.
- [ ] Eliminar la práctica con planes lanza `ProtectedError`.
- [ ] Enviar deja el plan `en_revision` y el tutor activo lo ve pendiente.
- [ ] Devolver sin observación se rechaza sin escribir nada; con observación deja
      la fila `devuelto` y la `Validacion`, sin versión nueva.
- [ ] Reenviar con la última versión `en_revision` o `aprobado` se rechaza; tras una
      devolución, el reenvío crea la versión siguiente con el contenido nuevo.
- [ ] Aprobar deja el plan `aprobado` y la práctica `en_curso` con su historial.
- [ ] Un actor sin permiso (rol ajeno, inactivo, asignación cerrada, staff) recibe
      `ValidationError` en `autor` y no cambia ninguna fila.
- [ ] El mismo reporte no se confirma dos veces: la base responde `IntegrityError` y
      el servicio `ValidationError` en `confirmacion`, sin escribir nada.
- [ ] `InformeFinal` rechaza en la base —y en `full_clean()`— ni contenido ni archivo
      y ambos a la vez; acepta cada uno por separado.
- [ ] El archivo del informe solo admite PDF (extensión y firma `%PDF-`) de hasta
      5 MB, y se guarda completo en una ruta única por archivo.
- [ ] Solo el `tutor_entidad` guardado de esa práctica laboral confirma y registra;
      otro tutor de entidad, un rol ajeno y una práctica comunitaria se rechazan.
- [ ] `Validacion` admite exactamente uno de plan, reporte o informe del estudiante;
      con dos referencias falla en la base y en `full_clean()`, sin filas huérfanas.
- [ ] El estudiante dueño presenta su informe solo con la práctica «en revisión final»;
      el informe nace «en revisión», su tutor lo ve pendiente y validar deja autor y fecha.
- [ ] Devolver el informe sin observación se rechaza sin escribir; devolverlo no cambia el
      estado de la práctica ni escribe historial.
- [ ] Un informe devuelto y reenviado deja dos versiones y solo la última cuenta como pendiente.

## Confirmación de entidad e informe final (RF-08, HU-07)

Dos entidades nuevas en `models.py` (migración aditiva
`0005_confirmacion_entidad_informe_final`) y dos servicios en `services.py`. El
data-model (S6) fija los campos y una sola regla de alcance: «el tutor de entidad
solo puede confirmar reportes de **sus** practicantes; cualquier otro acceso se
rechaza (HU-07 caso 3)».

| Entidad | Campos | Regla en la base |
| --- | --- | --- |
| `ConfirmacionEntidad` | `reporte` (PROTECT), `tutor_entidad` (PROTECT, rol `tutor_entidad`), `fecha` automática | `UniqueConstraint` de `reporte`: un reporte se confirma una vez |
| `InformeFinal` | `practica` (PROTECT), `tutor_entidad` (PROTECT, rol `tutor_entidad`), `contenido`, `archivo`, `fecha` automática | `CheckConstraint` «contenido o archivo, exactamente uno» |

`Validacion` no se reutiliza para la confirmación ni para el informe del tutor de
entidad: su `CheckConstraint` es «uno de plan, reporte o informe del estudiante» y
la confirmación de la entidad es otra escritura. `InformeFinal` replica
la forma «exactamente uno» de `Validacion`: la `CheckConstraint`
`actividades_informe_final_contenido_o_archivo` la impone en la base —así
`objects.create()` también falla con `IntegrityError`— y `clean()` la repite
dentro de `full_clean()` con las dos claves, `contenido` y `archivo`.

El vacío de `archivo` es la cadena vacía y no `NULL` (la recomendación de Django
para `FileField`), porque Django evalúa la `CheckConstraint` también en Python
dentro de `full_clean()` y ahí un `FieldFile` vacío nunca es `None`: con `NULL` la
restricción se leería al revés en las dos direcciones. La ruta en disco la decide
`ruta_informe_final` (`informes_finales/practica-<id>/<uuid>.pdf`): el nombre que
envía el cliente no se usa como nombre en disco.

`archivo` se valida como PDF de hasta 5 MB con `validar_archivo_informe`
(ADR 0005, S8): extensión `.pdf`, firma `%PDF-` en los primeros cinco bytes y tope
`MAX_INFORME_BYTES`. La regla se repite —no se importa— respecto de
`apps/prototipo/forms.py`, que valida lo mismo pero nunca guarda el archivo; el
validador rebobina el archivo antes y después de leer la firma para que se guarde
el PDF completo. Como es un validador de campo, `full_clean()` lo ejecuta en
`clean_fields()`, así que la vista no repite el chequeo.

### Servicios

| Acción | Actor exigido | Efecto |
| --- | --- | --- |
| `confirmar_reporte(reporte=, autor=)` | `tutor_entidad` guardado y activo **y** `Practica.tutor_entidad` de la práctica del reporte, que debe ser laboral | Crea la `ConfirmacionEntidad`; un segundo intento es `ValidationError` en `confirmacion` |
| `registrar_informe_externo(practica=, autor=, contenido=, archivo=)` | El mismo permiso, sobre la práctica | Crea el `InformeFinal`; un segundo intento es `ValidationError` en `informe` |

El permiso sale de la fila guardada de la práctica: una práctica comunitaria no
tiene tutor de entidad (`Practica.clean` lo prohíbe), así que la misma comparación
la rechaza sin una rama propia. Los dos servicios leen la fila bloqueada
(`select_for_update`) y no tocan `Practica.estado` ni `HistorialEstado` (S9).

### Endpoints

| Ruta | Vista | Éxito | Rechazos |
| --- | --- | --- | --- |
| `POST /api/v1/reportes/<id>/confirmacion/` | `ConfirmarReporteEntidadView` (`apps/reportes/api.py`) | `200` con `{id, reporte_id, tutor_entidad_id, fecha}` | `401`, `403` (rol ajeno o tutor ajeno), `404` reporte inexistente, `409 confirmacion_duplicada` |
| `POST /api/v1/practicas/<id>/informe-externo/` | `InformeExternoView` (`apps/practicas/api.py`) | `200` con `{id, practica_id, tutor_entidad_id, contenido, archivo, fecha}` | `400` (`contenido`/`archivo`), `401`, `403` (rol ajeno o tutor ajeno; la comunitaria cae aquí), `404`, `409 informe_duplicado` |

Las dos vistas comprueban el rol en `initial()` —antes de la fila y del cuerpo— y
buscan la fila por `pk` sin acotar al alcance de lectura: el contrato de HU-07 caso
3 distingue la práctica **ajena** (`403`, decidida por el servicio contra el
`tutor_entidad` guardado) de la **inexistente** (`404`). Del informe se devuelve la
ruta guardada del archivo y no una URL, porque los settings no definen `MEDIA_URL`.

### Pruebas

`backend/tests/unit/test_actividades_entidad.py` cubre las invariantes de la base
(unicidad, «exactamente uno», PDF y ruta única) y
`backend/tests/integration/test_tutor_entidad.py` las recorre por HTTP: la
confirmación registra quién y cuándo, el informe queda con autor y fecha, y la
práctica ajena, la comunitaria, el duplicado, el PDF inválido o mayor a 5 MB, las
dos ausencias y las dos presencias se rechazan sin escribir. Sin token, `401` con
el envelope universal.

## Informe final del estudiante (RF-16, HU-10, C-10)

El estudiante presenta su informe final de actividades y su tutor académico lo
revisa o lo devuelve con observación (spec.md:177-180, 328 y 341).

### Nombre: `InformeFinal` es la entidad, `InformeEstudiante` el estudiante

El `InformeFinal` que ya existía (RF-08, HU-07) es el informe del **tutor de
entidad** sobre la práctica: se registra una sola vez, sin estado ni versiones, y
lleva `tutor_entidad`. El informe que presenta el **estudiante** al cerrar
(RF-16) es otro documento: tiene autor `estudiante`, nace «en revisión», se
devuelve con observación y se reenvía en versiones. Reutilizar la tabla habría
mezclado dos autores, dos ciclos de vida y dos reglas de unicidad, así que la
entidad nueva se llama `InformeEstudiante` —`InformeFinal` se queda como estaba,
sin renombrar ni migrar— y el nombre de este README lo deja por escrito.

### Campos y reglas

| Campo | Tipo | Regla |
| --- | --- | --- |
| `practica` | FK a `practicas.Practica` | Obligatorio; `PROTECT`; `practica.informes_estudiante` |
| `estudiante` | FK a `settings.AUTH_USER_MODEL` | Obligatorio; `PROTECT`; sin `limit_choices_to`: el rol lo exige el servicio contra `practica.estudiante_id` |
| `version` | entero positivo | Inicial 1; máximo + 1 bajo el bloqueo de la práctica; único por `(practica, version)` (`actividades_informe_estudiante_version_unica`) |
| `estado` | `en_revision`, `validado` o `devuelto` | Inicia `en_revision` |
| `fecha` | fecha y hora | Automática al insertar (`auto_now_add`) |
| `archivo` | PDF de hasta 5 MB | Obligatorio; ruta única `informes_estudiante/practica-<id>/<uuid>.pdf`; reutiliza `validar_archivo_informe` de RF-08 |

### Servicios

| Acción | Actor exigido | Efecto |
| --- | --- | --- |
| `presentar_informe_final(practica=, autor=, archivo=)` | Estudiante guardado de la práctica, con la práctica «en revisión final» | Crea la versión 1; si la última quedó `devuelto`, delega en el reenvío; con la última `en_revision` o `validado` rechaza en `informe` |
| `reenviar_informe_final(practica=, autor=, archivo=)` | El mismo actor, solo si la última versión está `devuelto` | Crea la versión siguiente `en_revision`; la anterior se conserva `devuelto` |
| `validar_informe_estudiante(informe=, autor=)` | Tutor académico activo de la práctica (`AsignacionTutor` con `hasta` nulo) | `Validacion` aprobada con autor y fecha, fila `validado` |
| `devolver_informe_estudiante(informe=, autor=, observacion=)` | El mismo tutor, con observación no vacía | `Validacion` devuelta con la observación recortada, fila `devuelto` |

Orden de los rechazos: práctica/informe guardados (`practica`, `informe`),
permiso (`autor`), estado (`estado`) y entrada (`observacion`, `archivo`). Las
cuatro acciones pueden correr en una transacción: leen la práctica o el informe
con `select_for_update`. **Ninguna** cambia `Practica.estado` ni escribe
`HistorialEstado`: la transición `en revisión final` → `en curso` sigue sin
implementarse hasta que P-05 se decida, y devolver el informe no habilita el
cierre (RF-09 es otra unidad).

### Endpoints

| Ruta | Vista | Éxito | Rechazos |
| --- | --- | --- | --- |
| `POST /api/v1/practicas/{id}/informe-final/` | `InformeFinalEstudianteView.post` (`apps/practicas/api.py`) | `201` con `{id, practica_id, version, estado, fecha}` | `400` (falta el archivo, no es PDF o supera 5 MB), `401`, `403` (rol ajeno), `404` (práctica ajena o inexistente), `409 practica_no_en_revision_final` / `informe_pendiente` |
| `GET /api/v1/practicas/{id}/informe-final/` | `InformeFinalEstudianteView.get` | `200` con `{id, version, estado, fecha, devolucion}` | `401`, `404` (ajena, inexistente o sin informe; el mismo para los tres) |
| `POST /api/v1/informes-estudiante/{id}/validar/` | `ValidarInformeEstudianteView` (`apps/reportes/api.py`) | `200` con la tarjeta `{clave, id, practica_id, version, estado}` | `401`, `403` (rol ajeno o tutor que no es el de la práctica), `404` (informe inexistente), `409 informe_no_en_revision` |
| `POST /api/v1/informes-estudiante/{id}/devolver/` | `DevolverInformeEstudianteView` | `200` con la misma tarjeta | `400` (observación obligatoria), `401`, `403`, `404`, `409` |

El `GET` es multirrol y se decide por el alcance de filas de T019
(`practicas_visibles_para`): el estudiante dueño, su tutor académico y los roles
con carrera alcanzan el informe. La `devolucion` (`observacion`, `autor_id`,
`fecha`) sale solo con `estado = devuelto`, de la última `Validacion` devuelta del
informe; en `en_revision` y en `validado` es `null`.

### Clave del pendiente: `informe-<id>`

La decisión del tutor reutiliza C-04 y la cola de `GET /api/v1/pendientes/` suma
los informes del estudiante a los reportes semanales. El esquema de claves no
cambia para lo que ya existía —las tarjetas de reporte conservan sus cinco campos
`id`, `practica_id`, `semana`, `horas_reportadas`, `estado`, y el demo sigue
usando `plan-<id>` y `reporte-<id>-<semana>`—; la clave nueva del informe es
`informe-<id>`, la misma forma que el demo ya usaba para este pendiente. Las
versiones no cambian la clave: el pendiente es el informe, y la versión que manda
es la última, que es la única «en revisión» o «devuelto» a la vez.

### Cierre

Un informe `validado` deja la práctica «en revisión final» y no habilita nada por
sí solo: el cierre (RF-09: horas validadas, evaluación e informe de la entidad)
es otra unidad, y hasta que P-05 se decida devolver el informe tampoco devuelve la
práctica a «en curso». Solo la última versión cuenta como «revisado».

## Siguiente paso

Sumar los planes en revisión a la cola `GET /api/v1/pendientes/` del tutor
(brecha 5 de `docs/matriz-front-api.md`).
