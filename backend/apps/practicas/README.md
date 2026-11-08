# Prácticas: catálogos, práctica asignada, tutor académico, asignación y transiciones

Dos catálogos y los registros del modelo de datos: entidades receptoras, períodos
académicos, `Practica` (RF-14), `AsignacionTutor` y los servicios internos de asignación
(T018) y transiciones de estado (T017). Sin endpoints, API, autenticación ni datos de ejemplo.

## Ruta rápida

1. Modelos y servicios: `backend/apps/entidades/models.py` (`EntidadReceptora`), `backend/apps/practicas/models.py` (`Periodo`, `Practica`, `AsignacionTutor`) y `backend/apps/practicas/services.py` (`asignar_practica`, `cambiar_estado_practica`).
2. Migraciones: `backend/apps/entidades/migrations/0001_initial.py`, `backend/apps/practicas/migrations/0001_initial.py` (períodos), `0002_practica.py` y `0003_asignaciontutor.py`.
3. Pruebas: `backend/tests/unit/test_entidad_receptora.py`, `test_periodo.py`, `test_practica.py`, `test_asignacion_tutor.py`, `test_asignacion_practica.py` y `test_transiciones_practica.py`.

Fuente: `specs/001-seguimiento-practicas/data-model.md` (apartados `Periodo`,
`EntidadReceptora`, `Practica` y `AsignacionTutor`) y T014/T015/T017/T018 en
`specs/001-seguimiento-practicas/tasks.md`.

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

`horas_requeridas` no tiene valor por defecto ni FK a la configuración: el servicio de
asignación las copia de la configuración vigente y las guarda en la práctica nueva.
Cambiar la configuración después no modifica la práctica. Solo las horas se copian: los
plazos de reporte y de revisión y el umbral de rezago se leen de la configuración vigente
de la carrera (RF-07), no se guardan en la práctica. Las transiciones y los motivos
obligatorios están en la sección siguiente.

## Servicio interno de asignación

`asignar_practica(*, estudiante, carrera, periodo, tipo, autor, entidad=None,
subtipo="", proyecto_vinculacion="")` crea la `Practica` y su registro inicial de
historial. Es otra interfaz **interna para llamadores de confianza**: no hay endpoint,
vista ni formulario, y el filtro por rol o carrera es T019.

| Decisión | Regla |
| --- | --- |
| Día de selección | `timezone.localdate()` se lee en cada llamada; no hay parámetro para cambiar la fecha de selección ni un campo nuevo de fecha de asignación |
| Configuración | `carrera` y `modalidad = tipo`, con `vigente_desde <= hoy`; se ordena `-vigente_desde, -pk` |
| Desempates | Gana la vigencia más reciente; el `pk` más alto resuelve el mismo día |
| Horas | Se copian de la configuración elegida; no son parámetro del servicio |
| Estado inicial | Siempre `asignada`; el llamador no puede fijarlo |
| Diario | Un `HistorialEstado` inicial (`estado_anterior` nulo → `asignada`) con el `autor` persistente, `full_clean()` y la práctica en la misma transacción |

Sin configuración vigente no hay respaldo a otra carrera, otra modalidad, una fila futura
ni horas del sistema: «No hay una configuración de carrera vigente para esa modalidad: no
se puede asignar la práctica.» en `carrera`, sin filas nuevas. Un `autor` sin guardar da
«El autor de la asignación debe ser un usuario guardado.» en `autor`. La práctica se valida
con `full_clean()`, así que una laboral sin entidad o subtipo se rechaza igual que en el
modelo. Si el diario rechaza la fila, la transacción deshace la práctica. El servicio no
crea ni reasigna `AsignacionTutor`, y la copia es un valor guardado: editar la
configuración o añadir una fila posterior no cambia las horas ya asignadas.

## Servicio interno de transiciones

`backend/apps/practicas/services.py` expone `cambiar_estado_practica(*, practica,
nuevo_estado, autor, motivo="")`: una interfaz **interna para llamadores de
confianza**, sin endpoint, vista ni cierre público, que no sustituye las políticas
superiores de T019/T024/T051/T054. Las aristas son las siete de `data-model.md`:

| Arista | Motivo obligatorio | Solo el coordinador de la carrera |
| --- | --- | --- |
| `asignada` → `en_curso` | No | No |
| `en_curso` → `en_revision_final` | No | No |
| `en_revision_final` → `en_curso` | No | No |
| `en_revision_final` → `cerrada` | No | Sí |
| `en_curso` → `suspendida` | Sí | Sí |
| `suspendida` → `en_curso` | No (reanudación) | Sí |
| `suspendida` → `cancelada` | Sí | Sí |

El motivo es obligatorio solo al suspender y cancelar (RF-13, Clarification de
`spec.md`). El permiso vive en el servicio, no en una capa de endpoint que aún no existe
(RNF-02): suspender, reanudar, cancelar y cerrar solo los produce un usuario **activo** de
rol `coordinador` cuya carrera es la de la práctica; el rol, la carrera y `is_active` se
leen de la fila guardada del autor, no del objeto del llamador. El rechazo es
`ValidationError` en la clave `autor` y el orden de los rechazos es: estado final, destino
inválido, arista ilegal, permiso y, por último, motivo. Las demás aristas siguen siendo
mecanismo interno (`aprobar_plan` ya exige al tutor académico).

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
- [ ] `asignar_practica` copia las horas de la configuración de la misma carrera y modalidad vigente, no de otra ni futura.
- [ ] Sin configuración vigente, o si falla el diario, no queda ninguna práctica ni historial nuevos.
- [ ] `full_clean()` rechaza una segunda asignación activa y, sin `full_clean()`, la base la rechaza con `IntegrityError`.
- [ ] Cerrar la asignación anterior y abrir otra conserva la fila cerrada.
- [ ] `cambiar_estado_practica` acepta las siete aristas y rechaza el resto sin escribir nada.
- [ ] El rechazo deja iguales estado, motivos, filas e historial, y un fallo del historial deshace el estado nuevo.
- [ ] La concurrencia se prueba en PostgreSQL; en SQLite esa prueba se omite, no se simula.

## Siguiente paso

La reasignación y el filtro de tutores de T019, las acciones de plan de T024, las
políticas de cierre y devolución de T051, las de suspensión de T054 y el admin de T020
quedan fuera de esta unidad.

## Tutor de entidad externo (T019, S3)

`Practica.tutor_entidad` es una FK opcional a `Usuario` con rol `tutor_entidad`
(`PROTECT`; un solo tutor vigente por práctica y reemplazarlo reemplaza el vínculo,
sin historial de vigencias). Una práctica comunitaria no tiene tutor de entidad y
`full_clean()` lo rechaza; el rol del vinculado también se valida en `full_clean()`.
`asignar_practica` acepta `tutor_entidad=None` opcional sin cambiar sus otros contratos.
