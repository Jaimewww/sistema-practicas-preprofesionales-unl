# Data Model: Seguimiento de prácticas preprofesionales

**Input**: [spec.md](./spec.md) · **Decisiones técnicas**: [research.md](./research.md)

Modelo conceptual de la fase 1: entidades, campos, relaciones, reglas de validación tomadas de los requisitos y transiciones de estado. Los nombres de campos están en `snake_case`; las entidades en PascalCase.

## Resumen de entidades

| Entidad | Qué representa | Origen |
| --- | --- | --- |
| `Carrera` | Programa de estudios al que pertenece una práctica. | Aislamiento por carrera |
| `ConfiguracionCarrera` | Horas, plazos y umbral de rezago de una carrera y modalidad. | RF-12 |
| `Periodo` | Ventana académica de la práctica; fija los días del período. | HU-06 |
| `Usuario` | Persona que entra al sistema, con un rol. | RF-11 |
| `EntidadReceptora` | Institución donde el estudiante hace la práctica. | HU-07 |
| `Practica` | Entidad central: estudiante, entidad, tutores, período y estado. | Todo el MVP |
| `AsignacionTutor` | Vigencia del tutor académico de una práctica. | Caso límite: reemplazo de tutor |
| `PlanActividades` | Lo que el estudiante se compromete a hacer. | HU-01, RF-01 |
| `ReporteSemanal` | Actividades, horas y evidencias de una semana. | HU-02, RF-02 |
| `Evidencia` | Archivo de respaldo de un reporte, versionado. | HU-02, caso límite de devoluciones |
| `Validacion` | Decisión del tutor académico sobre un plan o un reporte. | HU-03, RF-03, RF-04 |
| `ConfirmacionEntidad` | Confirmación del tutor de entidad sobre un reporte. | HU-07 caso 2, RF-08 |
| `InformeFinal` | Valoración de cierre del tutor de la entidad receptora. | HU-07, HU-08, RF-09 |
| `Alerta` | Aviso generado por un atraso o un pendiente. | RF-07 |
| `HistorialEstado` | Registro inalterable de cada cambio de estado de una práctica. | RF-10, HU-09, CE-06 |

## Entidades

### Carrera

| Campo | Descripción | Regla |
| --- | --- | --- |
| `id` | Identificador. | — |
| `codigo` | Código de la carrera. | Único |
| `nombre` | Nombre de la carrera. | Obligatorio |

**Relaciones**: una carrera tiene muchas `ConfiguracionCarrera`, muchas `Practica` y muchos `Usuario` coordinadores.

### ConfiguracionCarrera

| Campo | Descripción | Regla |
| --- | --- | --- |
| `carrera_id` | Carrera a la que aplica. | Obligatorio |
| `modalidad` | `laboral` o `comunitaria`. | Obligatorio |
| `horas_requeridas` | Horas exigidas para esa modalidad. | Obligatorio. El sistema **no** fija ningún valor: lo define cada carrera |
| `plazo_reporte_dias` | Días para reportar después de cerrar la semana. | Por defecto 3 |
| `plazo_revision_dias` | Días hábiles para que el tutor revise. | Por defecto 5 |
| `umbral_rezago` | Porcentaje de horas esperadas bajo el cual hay rezago. | Por defecto 80 % |
| `vigente_desde` | Inicio de vigencia de la configuración. | Obligatorio |

**Relaciones**: pertenece a una `Carrera`. Las `Practica` copian sus valores al asignarse (ver Tema 7 en [research.md](./research.md)).

### Periodo

| Campo | Descripción | Regla |
| --- | --- | --- |
| `nombre` | Nombre del período académico. | Obligatorio |
| `fecha_inicio` | Inicio. | Obligatorio |
| `fecha_fin` | Fin. | Debe ser posterior al inicio |
| `dias_totales` | Días del período, usados para calcular las horas esperadas. | Derivado de las fechas |

### Usuario

| Campo | Descripción | Regla |
| --- | --- | --- |
| `id` | Identificador. | — |
| `nombre` | Nombre completo. | Obligatorio |
| `email` | Correo de acceso. | Único |
| `rol` | `estudiante`, `tutor_academico`, `tutor_entidad` o `coordinador`. | Obligatorio, un rol por cuenta en el MVP |
| `carrera_id` | Carrera del usuario. | Obligatorio para coordinadores y tutores académicos |

**Relaciones**: un estudiante puede tener varias `Practica`; un tutor académico participa en varias prácticas a través de `AsignacionTutor`; un coordinador ve todas las prácticas de su carrera.

### EntidadReceptora

| Campo | Descripción | Regla |
| --- | --- | --- |
| `id` | Identificador. | — |
| `nombre` | Nombre de la institución. | Obligatorio |

**Relaciones**: una entidad receptora recibe muchas `Practica`. Es **opcional** en prácticas comunitarias: el proceso debe funcionar sin ella.

### Practica

| Campo | Descripción | Regla |
| --- | --- | --- |
| `estudiante_id` | Estudiante que la realiza. | Obligatorio |
| `carrera_id` | Carrera. | Obligatorio |
| `entidad_id` | Entidad receptora. | Opcional en modalidad comunitaria |
| `periodo_id` | Período académico. | Obligatorio |
| `tipo` | `laboral` o `comunitaria`. | Obligatorio |
| `horas_requeridas` | Horas exigidas de esta práctica. | **Copiadas** de `ConfiguracionCarrera` al asignar; no se recalculan después |
| `estado` | Estado actual. | Ver transiciones |
| `motivo_suspension` | Motivo de la suspensión. | Obligatorio al pasar a `suspendida` |
| `motivo_cancelacion` | Motivo de la cancelación. | Obligatorio al pasar a `cancelada` |

**Relaciones**: una práctica tiene un `PlanActividades`, muchos `ReporteSemanal`, a lo sumo un `InformeFinal`, muchas `Alerta` y muchos `HistorialEstado`. Las prácticas laboral y comunitaria de un mismo estudiante son **registros separados**.

### AsignacionTutor

| Campo | Descripción | Regla |
| --- | --- | --- |
| `practica_id` | Práctica. | Obligatorio |
| `tutor_academico_id` | Tutor académico. | Obligatorio |
| `desde` | Inicio de la asignación. | Obligatorio |
| `hasta` | Fin de la asignación. | Nulo mientras está activa |

**Regla**: una práctica tiene **un solo tutor académico activo** a la vez. Al reemplazar al tutor se cierra la asignación anterior y se abre una nueva: las horas y validaciones ya registradas se conservan.

### PlanActividades

| Campo | Descripción | Regla |
| --- | --- | --- |
| `practica_id` | Práctica. | Obligatorio |
| `version` | Número de versión del plan. | Incremental por devolución |
| `contenido` | Descripción de las actividades previstas. | Obligatorio |
| `estado` | `en_revision`, `aprobado` o `devuelto`. | Inicia en `en_revision` |

**Regla**: el estudiante no puede registrar reportes semanales hasta que exista un plan **aprobado** (es la transición de `asignada` a `en curso`).

### ReporteSemanal

| Campo | Descripción | Regla |
| --- | --- | --- |
| `practica_id` | Práctica. | Obligatorio |
| `semana` | Semana del período a la que corresponde. | Obligatorio; una sola versión activa por semana |
| `horas_reportadas` | Horas declaradas. | Positivas |
| `fecha_registro` | Fecha en que el estudiante lo envió. | Automática |
| `estado` | `en_revision`, `validado` o `devuelto`. | Inicia en `en_revision` |

**Regla**: las horas de un reporte **no cuentan** para el acumulado hasta que el tutor académico las valida. Sí cuentan, en cambio, para el cálculo de rezago (ver Tema 6 en [research.md](./research.md)). Un reporte con horas marcadamente altas para la semana se señala para revisión.

### Evidencia

| Campo | Descripción | Regla |
| --- | --- | --- |
| `reporte_id` | Reporte al que respalda. | Obligatorio |
| `archivo` | Archivo subido. | Solo PDF, máximo 5 MB |
| `version` | Versión del archivo. | Incremental; las anteriores no se borran |
| `autor_id` | Quién la subió. | Automático |
| `fecha` | Fecha de carga. | Automática |
| `estado_revision` | Estado de revisión de la evidencia. | Se conserva por versión |

**Regla**: al devolverse una evidencia se conservan todas las versiones y todas las observaciones anteriores.

### Validacion

| Campo | Descripción | Regla |
| --- | --- | --- |
| `practica_id` | Práctica. | Obligatorio |
| `plan_id` o `reporte_id` | Objeto validado. | Exactamente uno de los dos |
| `decision` | `aprobado` o `devuelto`. | Obligatorio |
| `observacion` | Comentario del tutor. | **Obligatoria** cuando la decisión es `devuelto` |
| `autor_id` | Tutor que valida. | Automático |
| `fecha` | Fecha de la validación. | Automática |

**Regla**: RF-04 exige registrar autor y fecha en cada validación. Ninguna evidencia validada puede quedar sin autor ni fecha (CE-02).

### ConfirmacionEntidad

| Campo | Descripción | Regla |
| --- | --- | --- |
| `reporte_id` | Reporte confirmado. | Obligatorio |
| `tutor_entidad_id` | Tutor de la entidad. | Obligatorio |
| `fecha` | Fecha de la confirmación. | Automática |

**Regla**: el tutor de entidad solo puede confirmar reportes de **sus** practicantes; cualquier otro acceso se rechaza (HU-07 caso 3).

### InformeFinal

| Campo | Descripción | Regla |
| --- | --- | --- |
| `practica_id` | Práctica. | Obligatorio |
| `tutor_entidad_id` | Tutor de la entidad. | Obligatorio |
| `contenido` o `archivo` | Valoración de cierre. | Obligatorio uno de los dos |
| `fecha` | Fecha de registro. | Automática |

**Regla**: es requisito para cerrar la práctica. En modalidad comunitaria puede no existir tutor de entidad, caso en el que el cierre no depende de este registro (ver transiciones).

### Alerta

| Campo | Descripción | Regla |
| --- | --- | --- |
| `practica_id` | Práctica afectada. | Obligatorio |
| `tipo` | `reporte_no_enviado`, `revision_pendiente` o `rezago`. | Obligatorio |
| `destinatarios` | A quién se notifica. | Estudiante, tutor académico y coordinador según el tipo |
| `fecha` | Fecha de generación. | Automática |
| `atendida` | Si el pendiente ya se resolvió. | Por defecto falso |

### HistorialEstado

| Campo | Descripción | Regla |
| --- | --- | --- |
| `practica_id` | Práctica. | Obligatorio |
| `estado_anterior` | Estado de origen. | Nulo solo en el registro inicial |
| `estado_nuevo` | Estado de destino. | Obligatorio |
| `autor_id` | Quién produjo el cambio. | Obligatorio |
| `fecha` | Fecha del cambio. | Automática |
| `motivo` | Motivo del cambio. | Obligatorio en suspensión, reanudación y cancelación |

**Regla**: tabla de **solo inserción**. El sistema rechaza cualquier intento de modificar o borrar un registro del historial (RF-10, HU-09 caso 2).

## Reglas de integridad y aislamiento

Estas reglas cruzan entidades y se aplican en la capa de datos, no en las vistas.

| # | Regla | Fuente |
| --- | --- | --- |
| 1 | Cada usuario ve solo su información; el coordinador solo la de su carrera; el tutor de entidad solo la de sus practicantes. El filtrado se aplica en la consulta. | RF-11, restricción de privacidad, HU-07 caso 3 |
| 2 | Solo las horas validadas cuentan para el acumulado; las horas en revisión cuentan solo para el cálculo de rezago. | S-04, Tema 6 de research.md |
| 3 | La práctica se cierra solo con las horas requeridas validadas y con el informe final registrado. | RF-09, CE-05 |
| 4 | Suspender y cancelar exigen motivo; el motivo queda en el historial. | RF-13, clarify |
| 5 | Una práctica tiene un solo tutor académico activo; el reemplazo conserva las horas y validaciones previas. | S-02, caso límite |
| 6 | Las horas requeridas se copian al asignar la práctica y no cambian después. | Clarify, Tema 7 de research.md |
| 7 | Las evidencias son PDF de hasta 5 MB y se conservan todas las versiones y observaciones. | Caso límite de devoluciones, Tema 5 de research.md |
| 8 | El historial de estados es inalterable: solo inserción. | RF-10, CE-06 |

## Transiciones de estado

```text
asignada ──► en curso ──► en revisión final ──► cerrada
                ▲ │
                │ ▼
             suspendida ──► cancelada
```

| Transición | Quién la produce | Condición |
| --- | --- | --- |
| `asignada` → `en curso` | Tutor académico | Aprueba el plan de actividades |
| `en curso` → `en revisión final` | Estudiante | Completó las horas requeridas; puede adelantarse al fin del período |
| `en revisión final` → `en curso` | Coordinador o tutor académico | El informe final se devuelve y hay que retomar actividades |
| `en revisión final` → `cerrada` | Coordinador | Horas requeridas validadas **e** informe final registrado |
| `en curso` → `suspendida` | Coordinador | Con motivo obligatorio; conserva las horas validadas |
| `suspendida` → `en curso` | Coordinador | Reanudación; conserva las horas validadas |
| `suspendida` → `cancelada` | Coordinador | Con motivo obligatorio; es final |

`cerrada` y `cancelada` no admiten cambios. Toda transición escribe un registro en `HistorialEstado`.
