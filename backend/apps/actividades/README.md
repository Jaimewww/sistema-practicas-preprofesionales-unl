# Actividades: plan de actividades y validación (HU-01, HU-03)

Entidades `PlanActividades` (HU-01/RF-01) y `Validacion` (RF-03/RF-04), más los
servicios internos que mueven el plan: enviar, devolver y aprobar. No incluye
vistas, endpoints, plantillas, reportes, evidencias ni confirmaciones de entidad.

## Ruta rápida

1. Modelos: `backend/apps/actividades/models.py` (`PlanActividades`, `Validacion`).
2. Servicios: `backend/apps/actividades/services.py` (`enviar_plan`, `devolver_plan`,
   `aprobar_plan`).
3. Migraciones: `backend/apps/actividades/migrations/0001_initial.py` y
   `0002_validacion.py`.
4. Pruebas: `backend/tests/unit/test_plan_actividades.py` (modelo) y
   `backend/tests/integration/test_plan_actividades.py` (acciones).

Fuente: `specs/001-seguimiento-practicas/data-model.md` (apartados `PlanActividades`
y `Validacion`), RF-01/RF-03 y T021 a T024 en
`specs/001-seguimiento-practicas/tasks.md`.

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

## Validación (T023, adelantado)

`Validacion` guarda `practica`, `plan`, `decision` (`aprobado` o `devuelto`),
`observacion`, `autor` y `fecha` automática. `observacion` es obligatoria cuando
la decisión es `devuelto` (se valida en `clean()` dentro de `full_clean()`) y
aprobar puede ir sin observación. El data-model pide «exactamente uno de los dos»
entre `plan_id` y `reporte_id`, pero `ReporteSemanal` todavía no existe: hoy
`plan` es obligatorio en la base, de modo que una validación sin plan no se puede
insertar. Cuando llegue el reporte, `plan` pasará a opcional junto a `reporte` con
una `CheckConstraint` «exactamente uno»; escribirla ahora sobre una columna
inexistente inventaría esquema. `autor` lo escribe el servicio que valida y
`fecha` la pone la base al insertar (RF-04).

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

T025 (vistas y plantillas), reportes semanales, evidencias, confirmación de
entidad, informe final y endpoints. `reporte_id` de `Validacion` llega con el
reporte; editar el contenido de un plan por servicio tampoco está aquí (el
contenido entra en `enviar_plan`).

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

## Siguiente paso

T025: vistas y plantillas que llamen a estos servicios con los permisos de RF-11.
