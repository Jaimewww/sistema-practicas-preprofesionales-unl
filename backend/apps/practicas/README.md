# Prácticas: catálogos, práctica asignada, tutor académico y transiciones

Dos catálogos y los registros del modelo de datos: entidades receptoras, períodos
académicos, `Practica` (RF-14), `AsignacionTutor` y el servicio interno de
transiciones de estado (T017). Sin endpoints, API, autenticación ni datos de ejemplo.

## Ruta rápida

1. Modelos y servicio: `backend/apps/entidades/models.py` (`EntidadReceptora`), `backend/apps/practicas/models.py` (`Periodo`, `Practica`, `AsignacionTutor`) y `backend/apps/practicas/services.py` (`cambiar_estado_practica`).
2. Migraciones: `backend/apps/entidades/migrations/0001_initial.py`, `backend/apps/practicas/migrations/0001_initial.py` (períodos), `0002_practica.py` y `0003_asignaciontutor.py`.
3. Pruebas: `backend/tests/unit/test_entidad_receptora.py`, `test_periodo.py`, `test_practica.py`, `test_asignacion_tutor.py` y `test_transiciones_practica.py`.

Fuente: `specs/001-seguimiento-practicas/data-model.md` (apartados `Periodo`,
`EntidadReceptora`, `Practica` y `AsignacionTutor`) y T014/T015/T017 en `specs/001-seguimiento-practicas/tasks.md`.

## Campos y reglas

| Modelo | Campos obligatorios | Regla |
| --- | --- | --- |
| `EntidadReceptora` | `nombre` | Sin convenio, contacto ni vigencia; el nombre no es único |
| `Periodo` | `nombre`, `fecha_inicio`, `fecha_fin` | `fecha_fin` estrictamente posterior a `fecha_inicio` |
| `Periodo.dias_totales` | — | Propiedad derivada de solo lectura: `(fecha_fin - fecha_inicio).days + 1` |
| `Practica` | `estudiante`, `carrera`, `periodo`, `tipo`, `horas_requeridas` | Reglas condicionales por tipo; ver la sección siguiente |
| `AsignacionTutor` | `practica`, `tutor_academico`, `desde` | Una sola asignación activa por práctica; ver «Asignación de tutor» |

## Practica asignada

`entidad` es opcional salvo en laboral; `subtipo` es obligatorio en laboral y debe
quedar vacío en comunitaria; `proyecto_vinculacion` (texto de 200) es obligatorio
en comunitaria. Las cuatro claves foráneas usan `PROTECT`.

| Campo | Valores |
| --- | --- |
| `tipo` | `laboral`, `comunitaria` |
| `subtipo` | `practica`, `pasantia`, `ayudantia_docencia`, `ayudantia_investigacion` |
| `estado` | `asignada` (inicial), `en_curso`, `en_revision_final`, `cerrada`, `suspendida`, `cancelada` |
| `motivo_suspension`, `motivo_cancelacion` | Texto opcional, vacío por defecto |

`full_clean()` aplica las reglas condicionales y reporta: «La entidad receptora es
obligatoria para las prácticas laborales.», «El subtipo es obligatorio para las
prácticas laborales.», «El subtipo solo aplica a las prácticas laborales.» y «El
proyecto de vinculación es obligatorio para las prácticas comunitarias.».

`horas_requeridas` no tiene valor por defecto ni FK a la configuración: quien asigna
aporta el valor (p. ej. 240) y queda guardado. Cambiar la configuración después no
modifica la práctica; la copia automática es T018 y no está implementada. Las
transiciones y los motivos obligatorios están en la sección siguiente.

## Servicio interno de transiciones

`backend/apps/practicas/services.py` expone `cambiar_estado_practica(*, practica,
nuevo_estado, autor, motivo="")`: una interfaz **interna para llamadores de
confianza**, sin endpoint, vista ni cierre público, que no sustituye las políticas
superiores de T019/T024/T051/T054. Las aristas son las siete de `data-model.md`:

| Arista | Motivo obligatorio |
| --- | --- |
| `asignada` → `en_curso` | No |
| `en_curso` → `en_revision_final` | No |
| `en_revision_final` → `en_curso` | No |
| `en_revision_final` → `cerrada` | No |
| `en_curso` → `suspendida` | Sí |
| `suspendida` → `en_curso` | Sí (reanudación) |
| `suspendida` → `cancelada` | Sí |

Cualquier otra arista se rechaza con «Transición no permitida: de «origen» a «destino»»;
`cerrada` y `cancelada` son finales («La práctica está en «estado», un estado final sin
transiciones») y un destino fuera del vocabulario, aunque no sea texto, da `ValidationError`
(«El estado destino no pertenece al vocabulario de Practica.Estado.»), nunca `TypeError`.

El servicio bloquea y relee la fila (`select_for_update()`) dentro de la transacción: decide
con el estado guardado y no con el objeto —posiblemente obsoleto— del llamador, y devuelve esa
instancia. El estado nuevo y el `HistorialEstado` (anterior, nuevo, autor persistente, fecha y
motivo, con `full_clean()`) se escriben en la misma transacción: si uno falla no queda ninguno.
El motivo queda en el historial y, al suspender o cancelar, en `motivo_suspension` o
`motivo_cancelacion`, conservando lo anterior.

El bloqueo solo se prueba en PostgreSQL: la prueba con dos conexiones se omite en SQLite, que no soporta
`SELECT ... FOR UPDATE`. **Cerrar aquí no valida RF-09** (100 % de horas validadas, informe final revisado,
informe externo y evaluación final; el 70 % es calificación, no cierre): esas políticas son T019/T024/T051/T054.

## Asignación de tutor

`AsignacionTutor` une `practica` (`PROTECT`) con `tutor_academico` (`PROTECT`, usuario
del sistema) desde `desde` (obligatorio, sin valor por defecto) hasta `hasta`
(opcional). Una asignación está **activa** cuando `hasta` es nulo: no hay campo
booleano ni comparación con la fecha actual.

La práctica tiene a lo sumo una asignación activa. Para cambiar de tutor se cierra la
anterior guardando `hasta` y se crea otra; la fila cerrada se conserva como historial
y se admiten varias cerradas. Un mismo tutor académico puede atender varias prácticas.

El límite lo impone la base, no solo una comprobación previa: la `UniqueConstraint`
condicional `practicas_asignacion_tutor_activa_unica` (`practica` única donde
`hasta IS NULL`) rechaza una segunda activa aunque se escriba con `objects.create()` o
`save()`. El mensaje es «Ya existe una asignación activa para esta práctica; cierre la
asignación vigente antes de crear otra.» y se reporta en el error no asociado a un
campo (`NON_FIELD_ERRORS`).

`full_clean()` también valida el intervalo: «La fecha de fin no puede ser anterior a
la fecha de inicio.» en el campo `hasta`. El mismo día es válido y una `desde`
ausente se reporta como campo obligatorio, no como intervalo.

Estas tres decisiones —`related_name`, `PROTECT` y el intervalo `hasta >= desde`— son
opciones técnicas de esta unidad. El filtro por rol o carrera del tutor, el servicio de
reasignación y cualquier histórico inmutable son T019 y posteriores: no están aquí.

## Conteo inclusivo de días

Del 1 al 7 de enero son 7 días, no 6:

```python
>>> from datetime import date
>>> from apps.practicas.models import Periodo
>>> periodo = Periodo(
...     nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 1, 7)
... )
>>> periodo.dias_totales
7
```

Dos fechas adyacentes (1 y 2 de marzo) dan 2 días. Un período de un solo día o
con las fechas invertidas es inválido.

## Límite de validación

Estos modelos se validan con `full_clean()`: `save()` y `objects.create()` no la
ejecutan, como en cualquier modelo de Django. Por eso los tests llaman a
`full_clean()` antes de guardar y una fila creada sin validar queda tal cual en
la base. El error de fechas se reporta en el campo `fecha_fin` con el mensaje
«La fecha de fin debe ser posterior a la fecha de inicio.».

La única regla que la base impone por sí sola es la asignación activa única: una
escritura que la duplique falla con `IntegrityError` y no deja filas nuevas, aunque
salte `full_clean()`. La prueba corre sobre SQLite en memoria; no es verificación de
PostgreSQL, que queda para la integración de #76. El resto de las reglas son
validaciones de modelo y no están replicadas en la base.

`dias_totales` no se almacena: se calcula desde las fechas y no devuelve 0 días
cuando las fechas están incompletas o son inválidas.

## Checklist

- [ ] `apps.entidades` y `apps.practicas` figuran en `INSTALLED_APPS`.
- [ ] `full_clean()` rechaza un nombre vacío y fechas no posteriores al inicio.
- [ ] `full_clean()` rechaza una laboral sin entidad o sin subtipo y una comunitaria sin proyecto.
- [ ] Las horas guardadas no cambian al actualizar la configuración de la carrera.
- [ ] `full_clean()` rechaza una segunda asignación activa y, sin `full_clean()`, la base la rechaza con `IntegrityError`.
- [ ] Cerrar la asignación anterior y abrir otra conserva la fila cerrada.
- [ ] `cambiar_estado_practica` acepta las siete aristas y rechaza el resto sin escribir nada.
- [ ] El rechazo deja iguales estado, motivos, filas e historial, y un fallo del historial deshace el estado nuevo.
- [ ] La concurrencia se prueba en PostgreSQL; en SQLite esa prueba se omite, no se simula.

## Siguiente paso

La copia automática de T018, la reasignación y el filtro de tutores de T019, las
acciones de plan de T024, las políticas de cierre y devolución de T051, las de
suspensión de T054 y el admin de T020 quedan fuera de esta unidad.
