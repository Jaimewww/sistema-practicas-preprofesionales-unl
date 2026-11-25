# Alertas: política de rezago, plazo de revisión, modelo y generación por práctica (HU-06, CU-03, T040–T043)

Cinco piezas de RF-07: la regla matemática que decide si una práctica está
rezagada a una fecha (T040), el modelo `Alerta` que persiste el aviso con su
causa activa única (T042), la generación de la alerta de rezago de **una**
práctica con fecha inyectada (T043), la regla pura del plazo de revisión en
días hábiles (T041) y la regla pura del plazo de reporte de una semana completa
(T12). No hay ejecución programada, consulta, notificación ni autorización en
esta unidad. Ver «Alcance» al final.

## Fórmula

```text
días transcurridos = acotar((fecha - fecha_inicio).días + 1, 0, días del período)
horas esperadas    = horas requeridas × (días transcurridos ÷ días del período)
horas mínimas      = horas esperadas × (umbral de rezago ÷ 100)
hay rezago         = horas validadas + horas en revisión < horas mínimas
```

- **Días inclusivos**, la misma convención que `Periodo.dias_totales`: el inicio
  y el fin cuentan, así que el día 56 del período son 56 días transcurridos.
- **Acotado al período**: antes del inicio son 0 días (0 h esperadas) y después
  del fin son todos los días (horas requeridas como esperadas).
- **Comparación estricta y exacta**: se usan `Fraction`, sin redondeo, y el
  rezago exige quedar *por debajo*. Con 96 h mínimas, 95 h es rezago y 96 h no.
- **Ambos saldos suman**: horas validadas + horas en revisión (`CU-03`); un
  reporte devuelto no entra en ninguno de los dos.

## Ejemplo concreto

240 h requeridas en un período de 16 semanas (112 días inclusivos), al cerrar la
semana 8 (día 56):

```text
horas esperadas = 240 × (56 ÷ 112) = 120
horas mínimas   = 120 × 80 %       = 96
```

Con 95 h entre validadas y en revisión hay rezago; con 96 h o más no lo hay.

## Entradas y salida

`apps.alertas.services.evaluar_rezago` es una función pura, todo por palabra
clave:

| Entrada | Significado |
| --- | --- |
| `horas_requeridas` | Horas de la práctica (las que copió la asignación) |
| `horas_validadas` | Suma de reportes validados |
| `horas_en_revision` | Suma de reportes en revisión |
| `fecha_inicio`, `fecha_fin` | Fechas del período, inclusivas |
| `fecha` | Fecha de evaluación inyectada; la función no lee el reloj |
| `umbral_rezago` | Porcentaje configurado; el 80 por defecto vive en `ConfiguracionCarrera.umbral_rezago`, no aquí |

Devuelve `EvaluacionRezago` (`NamedTuple`):

| Campo | Tipo | Significado |
| --- | --- | --- |
| `horas_esperadas` | `Fraction` | Horas esperadas a la fecha |
| `horas_minimas` | `Fraction` | Umbral aplicado a las horas esperadas |
| `en_rezago` | `bool` | Comparación estricta ya resuelta |

Un período con `fecha_fin` no posterior a `fecha_inicio` es inválido y se
rechaza con `ValueError` («La fecha de fin debe ser posterior a la fecha de
inicio.»), la misma regla que impone `Periodo`. No se valida nada más: la
función no toca la base de datos, no la consulta, no escribe y no conoce
configuración, roles ni rutas.

## Modelo `Alerta` (T042)

`apps.alertas.models.Alerta` es la fila que representa un aviso. La migración
`0001_initial` es **aditiva**: crea solo la tabla nueva y no cambia ninguna
tabla existente; la app se registra en `INSTALLED_APPS` para que Django cargue
el modelo.

| Campo | Tipo | Regla |
| --- | --- | --- |
| `practica` | FK a `Practica` | Obligatorio; `on_delete=PROTECT`, como las demás referencias a una práctica en el sistema |
| `tipo` | `CharField(choices)` | Exactamente los tres tipos del data-model |
| `fecha` | `DateField(auto_now_add)` | Django la asigna al crear la fila; un valor manual se ignora |
| `atendida` | `BooleanField(default=False)` | Nace falsa; el flujo de resolución no está en esta unidad |

Tipos declarados: `reporte_no_enviado`, `revision_pendiente` y `rezago`.
RF-18 (incumplimiento reportado por el tutor de entidad) **no** es una causa de
alerta aquí, y el campo no admite otros valores en `full_clean()`.

### Causa activa única (CU-03, 4b)

La causa de una alerta es el par **práctica/tipo**. Una `UniqueConstraint`
condicional sobre `(practica, tipo)` con `atendida=False` impone en la base que
exista **a lo sumo una alerta activa por causa**. La regla vale también para
`objects.create()` y `save()`, que no ejecutan `full_clean()`: la inserción
falla con `IntegrityError` y la fila original queda intacta. El mensaje de esa
excepción lo da el motor. Si se usa `full_clean()`, la validación de la
restricción presenta «Ya existe una alerta activa de este tipo para la práctica;
no se genera otra hasta que la vigente se marque como atendida.»

Lo que la restricción **sí** permite:

- causas distintas (tipos distintos) activas a la vez en la misma práctica;
- la misma causa activa en prácticas distintas;
- filas atendidas de la misma causa, incluso varias, que quedan como historial;
- una alerta atendida seguida de una nueva activa de la misma causa: el
  historial no bloquea el aviso vigente.

Lo que **no** permite es una segunda fila no atendida del mismo par. Por eso la
detección (T043) usa `get_or_create` con el mismo par: Django busca primero y,
si no la encuentra, intenta insertar; si dos evaluaciones compiten, la
restricción rechaza la segunda inserción y `get_or_create` devuelve la fila ya
existente en lugar de propagar el conflicto (si la fila rival todavía no es
visible, el error se propaga). Solo ese conflicto de unicidad se interpreta como
«ya hay una alerta activa»; cualquier otro `IntegrityError` se propaga.

### Destinatarios derivados del tipo

Los destinatarios **no se persisten**: no hay tabla, columna ni identidades
concretas de destinatarios. `Alerta.destinatarios` devuelve los **roles** que
corresponden a su tipo, según HU-06:

| Tipo | Roles destinatarios |
| --- | --- |
| `reporte_no_enviado` | estudiante, tutor académico y coordinador (HU-06 #1) |
| `revision_pendiente` | solo el tutor académico (HU-06 #2, CU-03 1b) |
| `rezago` | estudiante, tutor académico y coordinador (HU-06 #3) |

Es un mapeo de rol, no una autorización: esta unidad no decide quién puede leer
ni resolver la alerta, ni notifica a nadie. El tutor académico concreto sale de
`AsignacionTutor` y el coordinador de la carrera de la práctica; resolverlos es
trabajo de la vista de T045.

### Deduplicación a nivel de reporte: cuándo haría falta

Hoy la unicidad es por práctica/tipo, así que **varias semanas sin reporte de la
misma práctica producen una sola alerta activa** de `reporte_no_enviado`, y
varios documentos pendientes del mismo tutor una sola de `revision_pendiente`.
Eso es lo que CU-03 4b pide: no duplicar la causa. Si el producto quiere una
alerta por **reporte concreto** (por ejemplo, para mostrar «semana 3 sin
reporte» y cerrarla cuando se envía) habrá que anclar la alerta al reporte y
mover la unicidad a `(practica, tipo, reporte)`/`(reporte, tipo)`; con la
restricción actual esas alertas por reporte chocarían entre sí. Esa decisión no
se toma en T042: el anclaje a reportes y la resolución quedan para las tareas
siguientes.

## Generación de la alerta de rezago (T043)

`apps.alertas.services.generar_alerta_rezago(practica, *, fecha)` evalúa **una**
práctica a la fecha inyectada y devuelve una tupla `(alerta, created)`:

| Resultado | Significado |
| --- | --- |
| `(None, False)` | No corresponde alertar: fuera de la guarda o sin rezago |
| `(Alerta, True)` | La alerta activa de rezago se creó ahora |
| `(Alerta, False)` | Ya existía una alerta activa de la misma causa y se devuelve esa |

La evaluación, en orden:

1. **Guarda de estado y período.** Solo se evalúa la práctica guardada en
   `en_curso` (manda la fila de la base, no el objeto del llamador) cuyo período
   incluye la fecha: `fecha_inicio <= fecha <= fecha_fin`, ambos extremos
   incluidos. Fuera de la guarda devuelve `(None, False)` sin leer
   configuración, sin escribir y sin error; una práctica sin guardar también.
2. **Configuración vigente.** La fila de `ConfiguracionCarrera` de la misma
   carrera y modalidad (`practica.tipo`) con `vigente_desde` no posterior a la
   fecha; la más reciente gana y el mayor `pk` desempata, igual que en
   `practicas.services`. No hay respaldo a otra carrera, otra modalidad ni a una
   fila futura: sin configuración vigente se lanza `ValidationError` («No hay una
   configuración de carrera vigente para esa modalidad: no se puede evaluar el
   rezago de la práctica.») bajo la clave `carrera`, sin crear filas.
3. **Evaluación.** `horas_practica` aporta los dos saldos y las horas requeridas
   de la práctica; `umbral_rezago` sale de la configuración vigente, no del 80
   por defecto de este módulo. `evaluar_rezago` decide con la misma comparación
   estricta de la sección anterior.
4. **Causa activa.** Si hay rezago,
   `Alerta.objects.get_or_create(practica=…, tipo=rezago, atendida=False)`. La
   búsqueda no filtra por fecha, así que una alerta activa de otro día se devuelve
   tal cual, con su `fecha` y su `pk` originales. Una fila atendida no bloquea:
   queda como historial y se crea una nueva activa. Un `IntegrityError` que no sea
   la unicidad de la causa activa se propaga; no se confunde con un duplicado.

`fecha` es solo la fecha de evaluación: `Alerta.fecha` sigue siendo la fecha real
de creación que asigna Django y reevaluar nunca la reescribe. La función no
resuelve ni cierra alertas cuando el rezago desaparece, no notifica, no lee el
reloj y no resuelve destinatarios concretos.

## Plazo de revisión en días hábiles (T041)

`apps.alertas.services.evaluar_plazo_revision` es la regla pura de HU-06 #2:
«un reporte sin revisar **más allá del plazo de revisión de su carrera**» avisa
al tutor académico. Como el plazo está en días hábiles, se cuenta cuántos días
hábiles pasaron desde el ingreso a revisión hasta la fecha evaluada.

| Entrada | Significado |
| --- | --- |
| `fecha_ingreso` | Fecha explícita de entrada a revisión; no se infiere de `fecha_registro` ni de otra fuente y todavía no está anclada en persistencia |
| `fecha` | Fecha de evaluación inyectada; la función no lee el reloj |
| `plazo_revision_dias` | Límite configurado (`ConfiguracionCarrera.plazo_revision_dias`, 5 por defecto) |

Devuelve `EvaluacionPlazoRevision` (`NamedTuple`) con `dias_habiles` (`int`, los
contados) y `vencido` (`bool`, la comparación ya resuelta).

```text
días hábiles = fechas de lunes a viernes en (fecha_ingreso, fecha]
vencido      = días hábiles > plazo_revision_dias
```

- **Calendario «lunes a viernes, como en el demo»** (decisión `weekdays_only`):
  sábado y domingo no cuentan; un **feriado entre semana cuenta** como día
  hábil, porque el demo solo excluye el fin de semana.
- **Intervalo `(ingreso, fecha]`** como en el demo: el día de ingreso no cuenta
  y la fecha evaluada sí. Una fecha anterior o igual al ingreso cuenta 0 días y
  no vence.
- **«Más allá» es estricto**: vence cuando se cuentan *más* días hábiles que el
  límite configurado. Con 5, el quinto día hábil no vence y el sexto sí.
- **Aritmética entera sobre fechas**: semanas completas de cinco días hábiles
  más los días sobrantes (a lo sumo seis), sin recorrer rangos largos.

Ejemplo de borde con un ingreso el lunes 2 de marzo de 2026:

```text
lun 2 → (mar 3, mié 4, jue 5, vie 6, lun 9) = 5 días hábiles → no vence
lun 9 → sexto día hábil el mar 10                   → vence
```

### No conectado todavía

Esta unidad **no cablea** la regla: no hay campos nuevos, migraciones, ORM,
reloj, notificaciones, comandos ni endpoints, y no cambia ninguna otra alerta.
Falta lo que las tareas siguientes (T044-T045) resuelven: de dónde sale la fecha
concreta de ingreso a revisión de cada pendiente (plan, reporte o informe
final), cómo se agrupa por reporte concreto —la unicidad actual es por
práctica/tipo, ver arriba—, el cruce con `plazo_revision_dias` de la
configuración vigente, la ejecución diaria y la consulta de alertas.

## Plazo de reporte de una semana completa (T12)

`apps.alertas.plazos_reporte.evaluar_plazo_reporte_semanal` es la regla pura de
HU-06 #1 («una semana se cerró sin reporte») para **una semana completa**
anclada en la fecha real de inicio de la práctica (decisión `practice_start`,
no el inicio del período ni el primer lunes).

| Entrada | Significado |
| --- | --- |
| `fecha_inicio_real` | Fecha real de inicio de la práctica (`Practica.fecha_inicio_real`), explícita; no se infiere de fechas, estados ni historial |
| `numero_semana` | Semana desde 1, la numeración que aporta quien reporta |
| `fecha` | Fecha de evaluación inyectada; la función no lee el reloj |
| `plazo_reporte_dias` | Plazo configurado (`ConfiguracionCarrera.plazo_reporte_dias`, 3 por defecto) en **días naturales** |

Devuelve `EvaluacionPlazoReporte` (`NamedTuple`) con `fecha_cierre` (`date`),
`ultimo_dia_oportuno` (`date`) y `vencido` (`bool`, la comparación ya resuelta).

```text
cierre              = fecha_inicio_real + (7 × numero_semana − 1) días
último día oportuno = cierre + plazo_reporte_dias
vencido             = fecha > último día oportuno
```

- **Anclaje en el inicio real**: la semana 1 empieza el día del inicio real y
  cierra seis días después. Si el inicio es el jueves 9 de abril de 2026, la
  semana 1 cierra el miércoles 15, no el domingo.
- **Semana *n* en el día 7n − 1**: un inicio en lunes hace que la semana 8
  cierre en el día 56, como en la convención inclusiva de `Periodo`.
- **Días naturales**: el plazo no descuenta sábados, domingos ni feriados,
  igual que `hoy > cierre + plazo_reporte_dias` en el demo.
- **Vence estrictamente después**: el último día oportuno no vence y el día
  siguiente sí. Con plazo 0 el reporte vence el día posterior al cierre.

Ejemplo con el plazo por defecto de 3 días y un inicio el lunes 6 de abril de
2026:

```text
semana 1: cierre dom 12 abr → último día oportuno mié 15 abr
          mié 15 abr no vence · jue 16 abr sí vence
```

La semana es un número entero positivo: `0` o `-1` se rechazan con `ValueError`
(«La semana del reporte debe ser un número entero positivo.», el mismo mensaje
de `ReporteSemanal.semana`). Como en `evaluar_plazo_revision`, la función no
valida la configuración: recibe el plazo y lo aplica tal cual. No consulta la
base de datos, no arma el calendario de semanas esperadas de una práctica, no
opina sobre semanas parciales, suspensión o fin de práctica, y no crea, cierra
ni notifica alertas; el cableado con la configuración vigente y las alertas de
`reporte_no_enviado` queda para la ejecución diaria (T044-T045).

### No conectado todavía

No hay campos nuevos, migraciones, ORM, reloj, comando ni endpoint: falta
decidir el conjunto de semanas completas esperadas de cada práctica y cruzar
esta regla con `plazo_reporte_dias` de la configuración vigente cuando se
ejecute la detección.

## Alcance

La app queda registrada en `INSTALLED_APPS` y su migración inicial es aditiva.
Esta unidad genera la alerta de rezago de una práctica (T043) y aporta las
reglas puras del plazo de revisión (T041) y del plazo de reporte de una semana
completa (T12), pero no las ejecuta en lote, no notifica, no consulta, no
autoriza, no expone endpoints ni comandos y no modifica código ni tablas
existentes.

No entregado aquí, y que las tareas siguientes (T044-T045) deben resolver:

- alertas por plazos: el anclaje de la fecha de ingreso a revisión de cada
  pendiente, el cruce del plazo de revisión y del plazo de reporte con la
  configuración vigente, y la alerta de reporte no enviado (la regla pura del
  plazo de reporte existe, pero no está cableada);
- ejecución diaria y comando con fecha de prueba;
- vista/consulta de alertas y su estado general;
- anclaje de alertas a reportes concretos, resolución/cierre y permisos de
  lectura por destinatario;
- calendario de semanas esperadas de cada práctica y anclaje semana/fecha (el
  cierre de una semana completa ya se calcula, pero no el conjunto esperado), y
  la noción de «antes de la fecha de fin del período» como disparo.

## Pruebas

`backend/tests/unit/test_regla_rezago.py` (`SimpleTestCase`, sin base de datos):
ejemplo canónico con 95/96 h y ambos saldos, umbral configurado distinto de 80,
acotado en el inicio y en el fin, primer día inclusivo, límite con horas mínimas
fraccionarias (sin redondeo) y período inválido.

`backend/tests/unit/test_alerta_modelo.py` (`TestCase`, SQLite): tipos exactos,
campos obligatorios, fecha automática, `atendida` falsa, mapeo exacto de roles
por tipo, y la unicidad de la causa activa mediante inserciones reales
(duplicado rechazado sin perder el original, causas y prácticas distintas,
historial atendido que no bloquea la siguiente activa).

`backend/tests/unit/test_alertas_rezago.py` (`TestCase`, SQLite, reportes
reales): ejemplo canónico con 95/96 h sumando validadas y en revisión y
excluyendo la devuelta, horas requeridas tomadas de la práctica, guarda de estado
(persistido) y de extremos inclusivos del período sin configuración requerida
fuera, configuración por carrera/modalidad con corte `vigente_desde` y desempate
por `pk`, rechazo estable sin configuración sin escribir, reejecución que conserva
`pk` y `fecha`, historial atendido que no bloquea la nueva activa, ausencia de
resolución automática y propagación de un `IntegrityError` ajeno a la unicidad.

`backend/tests/unit/test_alertas_plazos.py` (`SimpleTestCase`, sin base de
datos): borde exacto del límite configurado en 5 (quinto día hábil no vence y
sexto sí), fin de semana en el borde (domingo no suma, lunes siguiente sí,
ingreso en sábado), fecha anterior o igual al ingreso con límite 0, límites
distintos (3 y 0), feriados de Semana Santa contados como días hábiles por la
decisión `weekdays_only` y un rango de un año que el conteo resuelve por
semanas completas.

`backend/tests/unit/test_plazo_reporte_semanal.py` (`SimpleTestCase`, sin base
de datos): cierre de la semana 1 a seis días del inicio en lunes y en jueves
(ejemplo de L24), semana 8 en el día 56, cierre independiente de la fecha
evaluada, borde del último día oportuno en días naturales (con plazo 0, 3 y 10),
fecha anterior al inicio y día intermedio sin vencer, fin de semana que cuenta
en el plazo, semana que cruza el año y el 29 de febrero, y rechazo de la semana
0 y negativa con el mensaje de `ReporteSemanal`.

Fuente: `specs/001-seguimiento-practicas/spec.md:146` (HU-06 #3), HU-06 #2,
CU-03, T040-T043 en `specs/001-seguimiento-practicas/tasks.md`.
