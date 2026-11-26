# Prácticas: catálogos, práctica asignada, tutor académico, asignación y transiciones

Dos catálogos y los registros del modelo de datos: entidades receptoras, períodos
académicos, `Practica` (RF-14), `AsignacionTutor`, los servicios internos de asignación
(T018), transiciones de estado (T017) y registro de la fecha real de inicio (T10), y su
acción autenticada `POST /api/v1/practicas/<id>/inicio/` (T11). Sin datos de ejemplo.

## Ruta rápida

1. Modelos y servicios: `backend/apps/entidades/models.py` (`EntidadReceptora`), `backend/apps/practicas/models.py` (`Periodo`, `Practica`, `AsignacionTutor`) y `backend/apps/practicas/services.py` (`asignar_practica`, `cambiar_estado_practica`, `registrar_inicio_practica`).
2. API: `backend/apps/practicas/api.py` (`PracticasListaView`, `PracticaDetalleView` e `InicioPracticaView`) y la ruta en `backend/config/urls.py`.
3. Migraciones: `backend/apps/entidades/migrations/0001_initial.py`, `backend/apps/practicas/migrations/0001_initial.py` (períodos), `0002_practica.py` y `0003_asignaciontutor.py`.
4. Pruebas: `backend/tests/unit/test_entidad_receptora.py`, `test_periodo.py`, `test_practica.py`, `test_asignacion_tutor.py`, `test_asignacion_practica.py`, `test_transiciones_practica.py`, `test_practica_fecha_inicio_real.py` y `test_registrar_inicio_practica.py`; HTTP, `backend/tests/integration/test_inicio_practica.py`.

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

## Fecha real de inicio (T9, S3)

`Practica.fecha_inicio_real` es un `DateField` **opcional** (`null=True`,
`blank=True`) y **propiedad del servidor** (`editable=False`): no aparece en
`ModelForm` ni en los formularios genéricos del admin. No tiene valor por
defecto ni se rellena en filas históricas, así que las prácticas anteriores
quedan con `NULL`; borrar o cambiar fechas no la toca. Tampoco se deriva del
período, de `fecha_registro`, del historial de estados ni de la aprobación del
plan: el paso `asignada → en_curso` registra *cuándo se aprobó el plan*, no
cuándo arrancaron las actividades, y reanudar o volver de revisión final nunca
reinicia el calendario. Solo la escribe el servicio interno de la sección
siguiente o, fuera de él, una escritura explícita en la fila.

| Dato | Estado |
| --- | --- |
| Persistencia nullable, sin valor por defecto ni relleno | T9 |
| Declaración inicial por el coordinador de la carrera (servicio interno) | T10 |
| Acción HTTP autenticada de captura | T11, este corte |
| Validar que la fecha caiga dentro del período | Diferido: falta decidir la regla |
| Anclaje del calendario de reportes y de las alertas de RF-07 | T12 |

Este corte no cambia `save()`, `asignar_practica`, `cambiar_estado_practica`,
`aprobar_plan`, la tarjeta de la API (`PracticaCardSerializer`) ni las rutas `GET`
del esquema OpenAPI: la captura HTTP va en su propia sección y el calendario de
reportes sigue diferido.

## Servicio interno de registro de la fecha real de inicio (T10, S3)

`registrar_inicio_practica(*, practica, fecha, autor)` es la **declaración
inicial** del dato: no tiene validaciones de negocio propias de la API y su única
superficie HTTP es la acción autenticada de T11 (sección siguiente), que no
añade reglas. La matriz de permisos de RF-11
(`specs/001-seguimiento-practicas/spec.md`, «Matriz de permisos») le da esta
escritura solo al coordinador, sobre las prácticas de su carrera.

| Decisión | Regla |
| --- | --- |
| Autor | Usuario guardado, **activo**, rol `coordinador` y carrera igual a la de la práctica; rol, carrera e `is_active` se leen de la fila guardada del autor |
| Orden de rechazos | práctica sin guardar → autor sin guardar → permiso de autor → tipo y rango de la fecha → estado → fecha ya registrada distinta |
| Estado | Solo `en_curso`; en cualquier otro estado se rechaza en `estado` |
| Fecha | Argumento `date` obligatorio y explícito; un `datetime` (que hereda de `date`), `None`, texto o número se rechazan en `fecha` |
| Rango | No puede ser posterior a `timezone.localdate()`, la única lectura del reloj; hoy se acepta |
| Inferencia | Ninguna: no se deriva del período, de `fecha_registro`, del historial ni de la aprobación del plan, y no se valida que caiga dentro del período |
| Primera escritura | Si ya hay una fecha distinta se rechaza en `fecha` y no se escribe; repetir exactamente la misma devuelve la instancia sin escribir |
| Efectos | Solo `fecha_inicio_real`: no cambia estado, motivos ni `HistorialEstado` |

El rechazo de autor es el **primero** de los que dependen de la práctica, de modo que
un usuario sin permiso no averigua el estado ni si ya hay una fecha guardada. Los
mensajes son: «Solo el coordinador activo de la carrera de la práctica puede registrar
su fecha real de inicio.» en `autor`; «Solo una práctica «en curso» admite registrar su
fecha real de inicio; está en «estado».» en `estado`; «La fecha real de inicio debe ser
una fecha sin hora.», «La fecha real de inicio no puede ser posterior a hoy.» y «La
práctica ya tiene otra fecha real de inicio registrada: no se reemplaza.» en `fecha`.

La primera escritura se protege en dos capas: la fila se bloquea con
`select_for_update()` dentro de la transacción —igual que en
`cambiar_estado_practica`— y la escritura es una actualización condicional
(`fecha_inicio_real IS NULL`). PostgreSQL soporta el bloqueo; **SQLite no lo soporta**
(no agrega `FOR UPDATE`) y allí solo la condición de la actualización impide pisar una
fecha rival: si la actualización no afecta filas, el servicio relee y, si el valor no
coincide, rechaza. La prueba del bloqueo corre solo en PostgreSQL y se omite en SQLite;
la de la actualización condicional sí corre en SQLite simulando una escritura rival ya
confirmada.

Reglas de negocio **diferidas**, sin implementar acá: si la fecha debe caer dentro del
período, si se admite corregirla después de declarada y si una práctica suspendida puede
declarar su fecha real (hoy se exige `en_curso`). La acción HTTP autenticada es la
sección siguiente (T11) y T12 usa la fecha en el calendario de reportes y en las
alertas de RF-07.

## Acción autenticada de captura (T11, S3)

`POST /api/v1/practicas/<id>/inicio/` es el **adaptador HTTP fino** del servicio
anterior: no añade reglas de negocio, solo lee el cuerpo, acota la práctica al
alcance del actor y traduce el `ValidationError` del dominio **por claves**
(`fecha` → 400 de campo; `estado` → 409). Vista: `InicioPracticaView` en
`backend/apps/practicas/api.py`; ruta en `backend/config/urls.py`, dentro del
grupo de prácticas y antes de las rutas del demo.

| Decisión | Regla |
| --- | --- |
| Actor | Usuario autenticado del servidor (JWT); el cuerpo no puede fijar autor, práctica ni estado |
| Orden | `401` sin identidad → `403` rol distinto de coordinador → `404` práctica inexistente o de otra carrera → cuerpo → `409`/`400` del dominio |
| Permisos | `rol_requerido(coordinador)` y `PermitirPracticaVisible`; la práctica se busca con `practicas_visibles_para`, no con `get_object` |
| Cuerpo | Objeto JSON con exactamente una clave, `fecha` (`AAAA-MM-DD`, sin hora); claves extra y cuerpos que no son objeto dan `400` en su clave o en `non_field_errors` |
| Respuesta | `200` con `{id, fecha_inicio_real}`, también cuando repite la misma fecha (no reescribe) |
| Sin reemplazo | Una segunda fecha distinta se rechaza en `fecha` con el mensaje del dominio, que no incluye la fecha guardada |
| Estado | Solo `en_curso`; en cualquier otro estado `409 practica_no_en_curso` |
| Fallo cerrado | Una clave de dominio no prevista (`practica`, `autor` o una nueva) responde `500 error_interno` sin publicar el mensaje del dominio |
| Efectos | Solo `fecha_inicio_real`: no cambia `estado`, motivos, `fecha_registro` ni `HistorialEstado` |

La vista no calcula permisos propios: el rol sale de `apps.seguridad` y el alcance
de `practicas_visibles_para` (T019). Por eso una práctica de otra carrera y una
inexistente responden el mismo `404` genérico **incluso con un cuerpo malformado**,
y un rol ajeno recibe `403` antes de que se lea el cuerpo o se compruebe la
existencia. El contrato queda en `/api/v1/schema/` y `/api/v1/docs/` con `jwtAuth`
y las respuestas `200`, `400`, `401`, `403`, `404` y `409`; las rutas `GET` de
prácticas conservan su esquema.

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
- [ ] `fecha_inicio_real` se guarda solo cuando se escribe explícitamente; omitirla deja `NULL`, no aparece en `ModelForm` y ninguna transición ni la aprobación del plan la inventa.
- [ ] `registrar_inicio_practica` solo acepta al coordinador activo de la misma carrera y solo en `en_curso`; el rechazo de autor no revela estado ni fecha y no escribe nada.
- [ ] Una fecha `datetime`, de otro tipo o futura se rechaza; el registro no valida el período ni infiere la fecha.
- [ ] Una fecha distinta ya declarada no se reemplaza y repetir la misma no escribe; el estado y el historial quedan intactos.
- [ ] `POST /api/v1/practicas/<id>/inicio/` comprueba rol y alcance de carrera antes del cuerpo: rol ajeno `403`, práctica ajena o inexistente `404` idéntico aunque el cuerpo venga malformado.
- [ ] El cuerpo del POST acepta solo `fecha` (`AAAA-MM-DD`, no futura); claves extra, cuerpos que no son objeto y fechas malformadas dan `400` sin escribir.
- [ ] Repetir la misma fecha da `200` sin escribir; una segunda fecha distinta da `400` sin revelar la guardada; una práctica que no está en curso da `409 practica_no_en_curso`.
- [ ] El POST no cambia estado, motivos ni historial, y el OpenAPI publica sus respuestas con `jwtAuth`.
- [ ] `POST /api/v1/practicas/<id>/informe-externo/` solo lo usa el `tutor_entidad` guardado de esa práctica laboral: rol ajeno y tutor ajeno `403`, práctica inexistente `404`, comunitaria `403`, y ninguno escribe.
- [ ] El informe exige `contenido` **o** `archivo` (exactamente uno) y el archivo es un PDF de hasta 5 MB: los rechazos responden `400` en `contenido`/`archivo`, y el duplicado `409 informe_duplicado`.
- [ ] Cerrar la asignación anterior y abrir otra conserva la fila cerrada.
- [ ] `cambiar_estado_practica` acepta las siete aristas y rechaza el resto sin escribir nada.
- [ ] El rechazo deja iguales estado, motivos, filas e historial, y un fallo del historial deshace el estado nuevo.
- [ ] La concurrencia se prueba en PostgreSQL; en SQLite esa prueba se omite, no se simula.

## Siguiente paso

La reasignación y el filtro de tutores de T019, las acciones de plan de T024, las
políticas de cierre y devolución de T051, las de suspensión de T054, el admin de T020,
la validación de negocio de la fecha (¿dentro del período?) y el calendario de reportes
que la usa (T12) quedan fuera de esta unidad.

## Tutor de entidad externo (T019, S3)

`Practica.tutor_entidad` es una FK opcional a `Usuario` con rol `tutor_entidad`
(`PROTECT`; un solo tutor vigente por práctica y reemplazarlo reemplaza el vínculo,
sin historial de vigencias). Una práctica comunitaria no tiene tutor de entidad y
`full_clean()` lo rechaza; el rol del vinculado también se valida en `full_clean()`.
`asignar_practica` acepta `tutor_entidad=None` opcional sin cambiar sus otros contratos.

## Informe final del tutor de entidad (RF-08, HU-07)

`POST /api/v1/practicas/<id>/informe-externo/` es el adaptador HTTP del servicio
`registrar_informe_externo` (`backend/apps/actividades/services.py`), que escribe
`InformeFinal`: la práctica, el `tutor_entidad` guardado, `contenido` o `archivo`
—exactamente uno— y la `fecha` automática. Vista: `InformeExternoView` en
`backend/apps/practicas/api.py`; ruta en `backend/config/urls.py`, junto a las
demás rutas de prácticas. La confirmación del reporte (el otro endpoint de RF-08)
vive en `apps/reportes/api.py` y su documentación está en
`backend/apps/actividades/README.md`.

| Decisión | Regla |
| --- | --- |
| Actor | `tutor_entidad` guardado y activo (`rol_requerido`) **y** el `tutor_entidad` de esa práctica laboral |
| Orden | `401` sin identidad → `403` rol ajeno → `404` práctica inexistente → cuerpo → `403` tutor ajeno → `409` duplicado → `400` de campo |
| Cuerpo | `multipart/form-data` con `contenido` (texto) **o** `archivo` (PDF de hasta 5 MB), nunca los dos ni ninguno |
| Respuesta | `200` con `{id, practica_id, tutor_entidad_id, contenido, archivo, fecha}`; `archivo` es la ruta guardada, no una URL (no hay `MEDIA_URL` en los settings) |
| Duplicado | La segunda vez responde `409 informe_duplicado` y no escribe |
| Comunitaria | Se rechaza con `403`: una comunitaria no tiene tutor de entidad (`Practica.clean`), así que la regla de alcance la cubre sin rama propia mientras P-01 siga abierta |
| Fallo cerrado | Una clave de dominio no prevista responde `500 error_interno` sin publicar el mensaje del dominio |
| Efectos | No cambia `estado`, motivos ni `HistorialEstado`: el cierre es de RF-09 (S9) |

La vista **no** acota la práctica con `practicas_visibles_para`: ese alcance
(T019) devuelve vacío para una práctica ajena **y** para una comunitaria, y el
contrato de HU-07 caso 3 distingue el permiso denegado (`403`) del recurso
inexistente (`404`). El desconocido se resuelve en el servicio contra la columna
`tutor_entidad` de la fila guardada, que es la única fuente del permiso. Por eso
un rol ajeno recibe `403` antes de que se lea la fila o el cuerpo, y una práctica
ajena responde `403` en lugar del `404` que daría el alcance de lectura.
