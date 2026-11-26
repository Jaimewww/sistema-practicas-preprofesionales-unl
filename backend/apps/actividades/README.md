# Actividades: plan de actividades, validación, confirmación de entidad e informe final

Entidades `PlanActividades` (HU-01/RF-01), `Validacion` (RF-03/RF-04),
`ConfirmacionEntidad` e `InformeFinal` (RF-08/HU-07), más los servicios internos
que las mueven: enviar, devolver y aprobar el plan, y confirmar el reporte y
registrar el informe final del tutor de entidad, con su API REST (S8). No
incluye plantillas, reportes semanales (son de `apps.reportes`) ni evidencias
del prototipo.

## Ruta rápida

1. Modelos: `backend/apps/actividades/models.py` (`PlanActividades`, `Validacion`,
   `ConfirmacionEntidad`, `InformeFinal`).
2. Servicios: `backend/apps/actividades/services.py` (`enviar_plan`, `devolver_plan`,
   `aprobar_plan`, `confirmar_reporte`, `registrar_informe_externo`).
3. Migraciones: `backend/apps/actividades/migrations/0001_initial.py`,
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

`Validacion` guarda `practica`, el `plan` **o** el `reporte` semanal al que se refiere,
`decision` (`aprobado` o `devuelto`), `observacion`, `autor` y `fecha` automática. El
data-model pide «exactamente uno de los dos» entre `plan_id` y `reporte_id`: la
`CheckConstraint` `actividades_validacion_plan_o_reporte` (migración
`0003_validacion_reporte`) lo impone en la base y `clean()` lo repite dentro de
`full_clean()`, así que `objects.create()` con los dos lados o con ninguno falla con
`IntegrityError` y `full_clean()` con `ValidationError` en `reporte`. `observacion` es
obligatoria cuando la decisión es `devuelto` (se valida en `clean()` dentro de
`full_clean()`) y aprobar puede ir sin observación. `autor` lo escribe el servicio que
valida y `fecha` la pone la base al insertar (RF-04). El servicio de aprobación de
planes (T024) sigue escribiendo la validación con `plan` y sin `reporte`.

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

`Validacion` no se reutiliza ni se modifica: su `CheckConstraint` es «plan o
reporte» y la confirmación de la entidad es otra escritura. `InformeFinal` replica
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

## Siguiente paso

Sumar los planes en revisión a la cola `GET /api/v1/pendientes/` del tutor
(brecha 5 de `docs/matriz-front-api.md`).
