# Actividades: plan de actividades (HU-01)

Entidad `PlanActividades` del seguimiento de prácticas: la práctica, la versión
del plan, el contenido que el estudiante se compromete a cumplir y su estado.
Solo modelo y migración; no incluye servicios de transición, vistas, endpoints
ni los modelos de reportes, evidencias o validaciones.

## Ruta rápida

1. Modelo: `backend/apps/actividades/models.py` (`PlanActividades`).
2. Migración: `backend/apps/actividades/migrations/0001_initial.py`.
3. Pruebas: `backend/tests/unit/test_plan_actividades.py`.

Fuente: `specs/001-seguimiento-practicas/data-model.md` (apartado
`PlanActividades`) y T022 en `specs/001-seguimiento-practicas/tasks.md`.

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
- No hay `UniqueConstraint` por práctica ni «versión activa»: el data-model no
  define esa restricción y agregarla inventaría una regla de producto.
- La devolución que genera una versión nueva, el reenvío y la aprobación son el
  servicio de T024 y no están implementados aquí.

Evidencia disponible: el prototipo no guarda un campo `version` en el plan (su
`_plan` en `apps/prototipo/sample_data.py` solo tiene estado, fechas,
observación y actividades), así que no hay un valor de prototipo que copiar. El
vocabulario de estados sí difiere: el prototipo muestra `validado` para el plan
mientras el data-model define `aprobado`. Esta unidad sigue el data-model y no
modifica los consumidores del prototipo.

## Estados y conservación

`estado` inicia en `en_revision`. Aprobar y devolver son transiciones de T024;
el modelo solo rechaza valores fuera del vocabulario. Las filas de versiones
anteriores no se borran ni se sobrescriben al registrar otra versión, y
`PROTECT` impide eliminar una práctica que tenga planes.

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
`version` con «La versión del plan debe ser un número entero positivo.». No hay
reglas replicadas en la base en esta unidad; las pruebas corren sobre SQLite en
memoria y no son verificación de PostgreSQL.

## Fuera de esta unidad

T021 (pruebas de integración), T023 (`Validacion`), T024 (enviar, devolver y
aprobar con el servicio de transiciones de T017), T025 (vistas y plantillas),
reportes, evidencias, informe final y endpoints. Que la tabla conserve filas no
significa que exista el servicio que las crea: T024 sigue pendiente.

## Checklist

- [ ] `apps.actividades` figura en `INSTALLED_APPS`.
- [ ] El plan nace en `en_revision` con versión 1 y su contenido.
- [ ] `full_clean()` rechaza campos obligatorios ausentes, estados fuera del
      vocabulario y versiones no positivas.
- [ ] Una versión no numérica produce un `ValidationError` en `version` y no un
      `TypeError`.
- [ ] Dos versiones explícitas conviven como filas separadas y la anterior no cambia.
- [ ] Eliminar la práctica con planes lanza `ProtectedError`.

## Siguiente paso

T024: implementar enviar, devolver y aprobar sobre el servicio de transiciones
de T017, incluida la nueva versión por devolución.
