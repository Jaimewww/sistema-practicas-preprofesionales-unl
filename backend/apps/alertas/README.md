# Alertas: política de rezago, plazo de revisión, modelo y generación por práctica (HU-06, CU-03, T040–T043)

Nueve piezas de RF-07: la regla matemática que decide si una práctica está
rezagada a una fecha (T040), el modelo `Alerta` que persiste el aviso con su
causa activa única (T042), la generación de la alerta de rezago de **una**
práctica con fecha inyectada (T043), la regla pura del plazo de revisión en
días hábiles (T041), la regla pura del plazo de reporte de una semana completa
(T12), la generación de la alerta de revisión vencida de **una** práctica a
partir del ingreso persistido (T13), la selección pura de las semanas
completas vencidas y sin reporte (T14) y la reconstrucción conservadora de
suspensiones desde el historial persistido (T15), más la generación de la
alerta de reporte no enviado de **una** práctica con fecha inyectada (T16). No
hay ejecución programada, consulta, notificación ni autorización en esta
unidad. Ver «Alcance» al final.

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

## Generación de la alerta de revisión vencida (T13)

`apps.alertas.services.generar_alerta_revision_vencida(practica, *, fecha)`
evalúa **una** práctica a la fecha inyectada y devuelve la misma tupla
`(alerta, created)` que la generación de rezago:

| Resultado | Significado |
| --- | --- |
| `(None, False)` | No corresponde alertar: fuera de la guarda, sin candidatas o dentro del plazo |
| `(Alerta, True)` | La alerta activa de revisión pendiente se creó ahora |
| `(Alerta, False)` | Ya existía una alerta activa de la misma causa y se devuelve esa |

La evaluación, en orden:

1. **Guarda de estado y período.** Igual que en rezago: solo la práctica
   guardada en `en_curso` (manda la fila de la base) cuyo período incluye la
   fecha, con ambos extremos incluidos. Fuera de la guarda devuelve
   `(None, False)` sin leer configuración ni escribir.
2. **Candidatas.** Solo los reportes de esa práctica en estado `en_revision` con
   `ingreso_revision_en` conocido. Una fila histórica con ese dato en `NULL` no
   es candidata: la fecha no se infiere de `fecha_registro`. Los reportes
   validados o devueltos tampoco son candidatos. Sin candidatas devuelve
   `(None, False)` **antes** de exigir configuración.
3. **Fecha del ingreso.** El instante persistido se convierte a fecha en la zona
   configurada del proyecto (`settings.TIME_ZONE`, hoy UTC), aunque haya una
   zona activa distinta; el resto del plazo se evalúa con esa fecha.
4. **Configuración vigente.** La fila de `ConfiguracionCarrera` de la misma
   carrera y modalidad con `vigente_desde` no posterior a la fecha; la más
   reciente gana y el mayor `pk` desempata. No hay respaldo: sin configuración
   vigente se lanza `ValidationError` («No hay una configuración de carrera
   vigente para esa modalidad: no se puede evaluar el plazo de revisión de la
   práctica.») bajo la clave `carrera`, sin crear filas.
5. **Evaluación.** Se aplica `evaluar_plazo_revision` a cada candidata con el
   `plazo_revision_dias` de la configuración. Basta un reporte vencido para
   alertar.
6. **Causa activa.** `Alerta.objects.get_or_create(practica=…, tipo=
   revision_pendiente, atendida=False)`: una única alerta activa por práctica,
   que **no identifica un reporte particular**. Una fila activa existente se
   devuelve sin reescribir su `fecha`; una atendida no se reactiva, queda como
   historial y no bloquea una nueva. Un `IntegrityError` ajeno a esa unicidad se
   propaga.

La alerta conserva los destinatarios derivados del tipo (solo el rol tutor
académico), pero no se persiste un destinatario concreto ni se envía nada. La
función no exige tutor asignado, no cierra alertas cuando ya no hay candidatas,
no escribe estados ni historial y no lee el reloj.

## Plazo de revisión en días hábiles (T041)

`apps.alertas.services.evaluar_plazo_revision` es la regla pura de HU-06 #2:
«un reporte sin revisar **más allá del plazo de revisión de su carrera**» avisa
al tutor académico. Como el plazo está en días hábiles, se cuenta cuántos días
hábiles pasaron desde el ingreso a revisión hasta la fecha evaluada.

| Entrada | Significado |
| --- | --- |
| `fecha_ingreso` | Fecha explícita de entrada a revisión; se obtiene de `ReporteSemanal.ingreso_revision_en` (T13), no se infiere de `fecha_registro` ni de otra fuente |
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

### Conexión con la persistencia (T13)

`generar_alerta_revision_vencida` ya cablea esta regla sobre
`ReporteSemanal.ingreso_revision_en`: lee los reportes en revisión de la
práctica, convierte el instante a fecha en la zona configurada (no en la zona
activa) y usa el `plazo_revision_dias` de la configuración vigente. No hay
campos nuevos,
migraciones, reloj, notificaciones ni endpoints, y no cambia ninguna otra
alerta.

Falta lo que las tareas siguientes resuelven: la ejecución diaria y la consulta
de alertas (T044-T045 / T7), el vencimiento de pendientes que no son reportes
semanales (plan, informe final) y la agrupación por reporte concreto —la
unicidad actual es por práctica/tipo—. El calendario de reportes no enviados
(T14) se conecta en T16.

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
`reporte_no_enviado` es T16.

## Selección de semanas sin reporte (T14)

`apps.alertas.plazos_reporte.semanas_sin_reporte_vencidas` compone la regla del
plazo con entradas explícitas y devuelve una tupla de `SemanaSinReporte`
(`numero_semana`, `fecha_inicio`, `fecha_cierre`, `ultimo_dia_oportuno`) con
**solo** las semanas completas y vencidas que siguen sin reporte, en orden
ascendente. Entradas: `fecha_inicio_real` (ancla `practice_start`), `fecha`
(evaluación inyectada), `plazo_reporte_dias` (días naturales),
`semanas_reportadas` (números ya enviados; `devuelto` cuenta como enviado, L28,
pero leer los estados es del llamador), `suspensiones` (intervalos inclusivos
`(inicio, fin)` confirmados) y `fecha_fin_real` (fin real **conocido**, opcional).

- **Solo semanas completas**: se examina una semana cuando su cierre no es
  posterior a `fecha` ni a `fecha_fin_real`; la primera que cierre después de
  cualquiera de esos límites detiene el recorrido. Sin `fecha_fin_real` no se
  supone un fin: el fin administrativo del período no se usa como fin real.
- **Vencimiento estricto y sin renumerar**: reutiliza
  `evaluar_plazo_reporte_semanal`, así que el último día oportuno no vence y el
  día siguiente sí; si la semana 3 se omite, la siguiente sigue siendo la 4.
- **Suspensión con bordes**: la semana se omite si su intervalo inclusivo toca
  algún intervalo de suspensión, aunque el contacto sea solo su primer o último
  día (días de transición, L29).
- **Validación conservadora**: un intervalo invertido (`fin < inicio`) se rechaza
  con `ValueError` («La fecha de fin de una suspensión no puede ser anterior a su
  fecha de inicio.») y un `fecha_fin_real` anterior al inicio también («La fecha
  de fin real no puede ser anterior a la fecha de inicio real.»), sin importar la
  fecha evaluada. Números reportados fuera del calendario se ignoran.

La zona y el historial ambiguo los resuelve T15; la generación de la alerta de
reporte no enviado es T16.

## Generación de la alerta de reporte no enviado (T16)

`apps.alertas.services.generar_alerta_reporte_no_enviado(practica, *, fecha)`
evalúa **una** práctica a la fecha inyectada y devuelve la misma tupla
`(alerta, created)` que las otras generaciones:

| Resultado | Significado |
| --- | --- |
| `(None, False)` | No corresponde alertar: fuera de la guarda, sin inicio real, sin historial certificado, sin semanas posibles o sin semanas elegibles |
| `(Alerta, True)` | La alerta activa `reporte_no_enviado` se creó ahora |
| `(Alerta, False)` | Ya existía una alerta activa de la misma causa y se devuelve esa |

La evaluación, en orden:

1. **Guarda de estado y período.** Solo la práctica guardada en `en_curso`
   (manda la fila de la base, no el objeto del llamador) cuyo período incluye la
   fecha, con ambos extremos incluidos. Fuera de la guarda devuelve
   `(None, False)` sin leer configuración ni escribir.
2. **Inicio real.** Sin `fecha_inicio_real` no hay calendario y **no hay
   alerta**: no se sustituye por el inicio del período ni por otra fecha. Una
   fecha anterior al inicio real tampoco alerta ni exige configuración.
3. **Historial certificado.** `reconstruir_suspensiones` debe devolver
   `conocida=True`. Un historial vacío, incompleto o incoherente **no** se lee
   como «no hubo suspensiones»: devuelve `(None, False)` sin alerta y sin leer
   configuración. Las fechas de las suspensiones se convierten en la zona
   configurada del proyecto, no en la zona activa (T15).
4. **Semanas completas posibles.** La primera semana cierra el día
   `inicio_real + 6`, sin depender del plazo. Si aún no cerró ninguna, ninguna
   configuración produce alerta y no se exige.
5. **Configuración vigente.** La fila de `ConfiguracionCarrera` de la misma
   carrera y modalidad con `vigente_desde` no posterior a la fecha; la más
   reciente gana y el mayor `pk` desempata. Sin respaldo: sin configuración
   vigente se lanza `ValidationError` («No hay una configuración de carrera
   vigente para esa modalidad: no se puede evaluar el plazo de reporte de la
   práctica.») bajo la clave `carrera`, sin crear filas.
6. **Semanas elegibles.** `semanas_sin_reporte_vencidas` recibe el inicio real,
   la fecha, el `plazo_reporte_dias` configurado en **días naturales**, el
   conjunto de semanas ya reportadas —de cualquier estado: un `devuelto` ya se
   envió (L28)— y los períodos certificados de suspensión. No se pasa fin real:
   no está persistido y el fin administrativo del período no lo sustituye.
7. **Causa activa.** Cualquier semana elegida produce **una única** alerta
   activa `reporte_no_enviado` por práctica, con
   `Alerta.objects.get_or_create(practica=…, tipo=reporte_no_enviado,
   atendida=False)`. Una fila activa existente se devuelve sin reescribir su
   `fecha`; una atendida no se reactiva ni se reabre, queda como historial y no
   bloquea una nueva. Un `IntegrityError` ajeno a esa unicidad se propaga: no se
   confunde con un duplicado.

La función no identifica un reporte particular, no cierra alertas cuando ya no
falta ninguna semana, no notifica, no escribe estados ni historial y no lee el
reloj. La alerta conserva los destinatarios derivados del tipo (estudiante,
tutor académico y coordinador).

## Reconstrucción de suspensiones desde el historial (T15)

`apps.alertas.suspensiones.reconstruir_suspensiones(practica)` es un adaptador
**de solo lectura** para una práctica persistida «en curso». Lee su
`HistorialEstado` completo en orden de `pk` —el orden canónico de las
transiciones, no el de la fecha— y devuelve `SuspensionesReconstruidas`:

| Campo | Significado |
| --- | --- |
| `conocida` | `True` solo si el historial certifica el resultado |
| `periodos` | Tupla de pares inclusivos `(inicio, fin)`; vacía si no hubo suspensiones |

Solo la arista `en_curso → suspendida` abre un período y solo
`suspendida → en_curso` lo cierra. Ambas fechas se convierten con
`timezone.get_default_timezone()` (`settings.TIME_ZONE`), no con la zona activa.
Las transiciones de revisión (`en_curso → en_revision_final` y su regreso) son
válidas y **no** son suspensiones.

El resultado es conservador:

- **Conocido y vacío** (`conocida=True`, `periodos=()`) cuando la cadena es
  canónica, termina en `en_curso` y no tiene suspensiones.
- **Desconocido** (`conocida=False`, `periodos=()`) cuando la práctica no está
  guardada, no existe, no está `en_curso`, el historial está vacío o le falta el
  alta inicial, la cadena es discontinua, aparece una arista imposible, una
  suspensión queda sin reanudar, el fin es anterior al inicio o el último estado
  del historial no coincide con la fila persistida.

`conocida=False` **no** significa «no hubo suspensiones»: el llamador no debe
usar el vacío como prueba de ausencia. La función no escribe, no repara ni
completa filas, no lee el reloj y no genera ni cierra alertas.

## Alcance

La app queda registrada en `INSTALLED_APPS` y su migración inicial es aditiva.
Esta unidad genera las alertas de rezago (T043), de revisión vencida (T13) y de
reporte no enviado (T16) de una práctica, aporta las reglas puras del plazo de
revisión (T041), del plazo de reporte de una semana completa (T12) y de la
selección de semanas vencidas sin reporte (T14), y reconstruye suspensiones
desde el historial persistido (T15). No las ejecuta en lote, no notifica, no
consulta, no autoriza, no expone endpoints ni comandos y no modifica código ni
tablas.

No entregado aquí, y que las tareas siguientes (T044-T045) deben resolver:

- ejecución diaria y comando con fecha de prueba;
- vista/consulta de alertas y su estado general;
- anclaje de alertas a reportes concretos, resolución/cierre y permisos de
  lectura por destinatario;
- persistir el fin real de la práctica y la noción de «antes de la fecha de fin
  del período» como disparo;
- garantía de foto consistente entre semanas, historial y configuración en
  evaluaciones concurrentes, y reconstrucción retroactiva de alertas.

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

`backend/tests/unit/test_alertas_revision.py` (`TestCase`, SQLite, reportes
reales): quinto día hábil sin alerta y sexto con alerta `revision_pendiente`,
plazo configurado mayor y menor que el valor por defecto, conversión del
ingreso a la zona configurada (UTC frente a `America/Guayaquil`), guarda de
estado (persistido) y de extremos inclusivos del período sin configuración
requerida fuera, ingreso desconocido y otros estados que no son candidatos sin
inferir fecha, reportes de otra práctica excluidos, configuración por
carrera/modalidad con corte `vigente_desde`, fila futura ignorada, desempate
por `pk` y rechazo estable sin configuración, una sola alerta activa para varios
reportes vencidos, reejecución que conserva `pk` y `fecha`, historial atendido
que no se reactiva, ausencia de cierre automático, ninguna escritura de estado
ni historial y propagación de un `IntegrityError` ajeno a la unicidad.

`backend/tests/unit/test_plazo_reporte_semanal.py` (`SimpleTestCase`, sin base
de datos): cierre de la semana 1 a seis días del inicio en lunes y en jueves
(ejemplo de L24), semana 8 en el día 56, cierre independiente de la fecha
evaluada, borde del último día oportuno en días naturales (con plazo 0, 3 y 10),
fecha anterior al inicio y día intermedio sin vencer, fin de semana que cuenta
en el plazo, semana que cruza el año y el 29 de febrero, y rechazo de la semana
0 y negativa con el mensaje de `ReporteSemanal`.

`backend/tests/unit/test_semanas_sin_reporte.py` (`SimpleTestCase`, sin base de
datos): selección ascendente anclada en el inicio real (lunes y jueves),
vencimiento estricto en el último día oportuno y con plazos 0/10, semana que
cierra después de la fecha evaluada que no se examina, ausencia de fin inferido,
fin real conocido que acota (a mitad de semana y antes del primer cierre),
semanas reportadas omitidas sin renumerar, suspensión que toca la semana por su
inicio, por su cierre o a través de dos semanas, intervalos invertidos rechazados
incluso sin efecto, y pureza.

`backend/tests/unit/test_suspensiones_alertas.py` (`TestCase`, SQLite,
historial real): resultado conocido y vacío con transiciones de revisión, un
período inclusivo y varios en orden, suspensión y reanudación el mismo día,
lectura por `pk` aunque las fechas no sean monótonas, conversión en la zona
configurada frente a una zona activa distinta, y resultados desconocidos por
práctica sin guardar o inexistente, historial vacío, práctica que no está en
curso, alta inicial ausente, cadena discontinua, arista imposible, estado actual
que no coincide, suspensión sin reanudar y par con fechas invertidas; el último
caso comprueba además que no se escribe ni se repara el historial.

`backend/tests/unit/test_alertas_reporte_no_enviado.py` (`TestCase`, SQLite,
historial real): una semana vencida sin reporte crea una sola alerta activa con
los roles derivados del tipo, el último día oportuno no alerta y el siguiente
sí, varias semanas faltantes siguen produciendo una sola alerta, reejecución
que conserva `pk` y `fecha`, historial atendido que no se reactiva, ausencia de
cierre automático cuando ya no falta ninguna semana, un reporte `devuelto`
—como `validado` o `en_revision`— ya enviado, otra semana reportada que no
oculta la faltante, ninguna escritura de estado ni historial y propagación de
un `IntegrityError` ajeno; sin `fecha_inicio_real` ni con fecha anterior al
inicio real no hay alerta ni se exige configuración, guarda de estado
(persistido) y de extremos inclusivos del período, práctica sin guardar,
primera semana aún incompleta, historial vacío o incoherente que no se lee como
«sin suspensiones», semana que toca una suspensión y suspensión que cubre todas
las semanas, decisión de la suspensión en la zona configurada frente a una zona
activa distinta, plazo mayor y plazo 0 en días naturales, configuración futura
ignorada, desempate por `pk`, otra carrera/modalidad que no sirve de
configuración y rechazo estable sin configuración sin escribir.

Fuente: `specs/001-seguimiento-practicas/spec.md:146` (HU-06 #3), HU-06 #2,
CU-03, T040-T043 en `specs/001-seguimiento-practicas/tasks.md`.
