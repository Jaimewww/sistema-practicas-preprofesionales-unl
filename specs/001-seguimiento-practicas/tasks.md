# Tasks: Seguimiento de prácticas preprofesionales

**Input**: documentos de diseño en `specs/001-seguimiento-practicas/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md)

**Tests**: la constitución (principio VI) exige escribir los tests primero cuando el cambio tiene tests aplicables. Cada historia empieza por sus tests, que deben **fallar** antes de implementar.

**Organization**: las tareas se agrupan por historia de usuario (HU-01 a HU-09 del spec) para que cada una se implemente y se pruebe de forma independiente.

> [!NOTE]
> Generado con los temas de la fase 0 cerrados (sesión 2026-10-12 de [research.md](./research.md)): interfaz con **plantillas de Django**, alertas con un **comando de gestión ejecutado por cron** y escala supuesta de **5 carreras, ~300 estudiantes y ~150 prácticas activas**. Cumple el principio V de la constitución.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede hacerse en paralelo (archivos distintos, sin dependencias pendientes).
- **[HU-NN]**: historia de usuario del spec a la que pertenece la tarea. `[RF-13]` marca la fase de suspensión y cancelación.
- **[x]**: tarea ya hecha; se indica el PR que la cubrió.

## Path Conventions

Aplicación web según [plan.md](./plan.md): proyecto Django en `backend/`, con aplicaciones por dominio en `backend/apps/<app>/`, plantillas en `backend/templates/<app>/` y tests en `backend/tests/unit/` y `backend/tests/integration/`. No hay API en el MVP.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: proyecto Django que arranca con un solo comando y responde `/health`. Coincide con el esqueleto del backend de la guía del equipo.

- [x] T001 Crear el proyecto Django en `backend/` con `manage.py` y `backend/config/` (settings, urls, wsgi, asgi) — PR #14
- [ ] T002 [P] Agregar a `backend/requirements.txt` `psycopg` y `django-simple-history`, y a `backend/requirements-dev.txt` `pytest` y `pytest-django` (Django 5.2 ya está desde el PR #14)
- [ ] T003 [P] Hacer configurable PostgreSQL por variables de entorno en `backend/config/settings.py`, manteniendo SQLite por defecto en desarrollo, y documentarlas en `backend/.env.example`
- [ ] T004 [P] Configurar `pytest-django` en `backend/pytest.ini` con las carpetas `backend/tests/unit/` y `backend/tests/integration/`, y apuntar `make test` a pytest sin perder los tests de `/health`
- [x] T005 Endpoint `/health/` con sus tests en `backend/apps/health/` — PR #14
- [ ] T006 [P] Crear las aplicaciones vacías `usuarios`, `carreras`, `entidades`, `practicas`, `actividades`, `alertas`, `auditoria` y `reportes` en `backend/apps/`, la carpeta `backend/templates/` con una plantilla base, y registrarlas en `INSTALLED_APPS`

**Checkpoint**: `pytest` corre en verde con `test_health.py` y el README permite levantar el entorno desde cero.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modelos base, máquina de estados, historial inalterable y aislamiento por rol. Todas las historias dependen de esta fase.

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

### Tests for Foundational

- [ ] T007 [P] Test unitario de `ConfiguracionCarrera`: valores por defecto 3 días, 5 días hábiles y 80 %; `horas_requeridas` obligatorio y sin valor por defecto en `backend/tests/unit/test_configuracion_carrera.py`
- [ ] T008 [P] Test unitario de transiciones: cada transición permitida de la tabla de `data-model.md`, rechazo de cualquier otra, `cerrada` y `cancelada` sin cambios, motivo obligatorio al suspender y cancelar en `backend/tests/unit/test_transiciones_practica.py`
- [ ] T009 [P] Test unitario de `HistorialEstado`: cada transición inserta un registro; modificar o borrar un registro se rechaza en `backend/tests/unit/test_historial_estado.py`
- [ ] T010 [P] Test unitario de asignación: las horas requeridas se copian de la configuración vigente y no cambian si después se edita la configuración en `backend/tests/unit/test_asignacion_practica.py`
- [ ] T011 [P] Test de integración de aislamiento: el estudiante ve solo lo suyo, el coordinador solo su carrera y el tutor de entidad solo a sus practicantes en `backend/tests/integration/test_aislamiento_roles.py`

### Implementation for Foundational

- [ ] T012 Crear el modelo `Usuario` personalizado con `rol` y `carrera` en `backend/apps/usuarios/models.py` (antes de la primera migración: Django no permite cambiar el modelo de usuario después)
- [ ] T013 [P] Crear `Carrera` y `ConfiguracionCarrera` en `backend/apps/carreras/models.py`
- [ ] T014 [P] Crear `EntidadReceptora` en `backend/apps/entidades/models.py`
- [ ] T015 Crear `Periodo`, `Practica` y `AsignacionTutor` en `backend/apps/practicas/models.py`, con `entidad` opcional solo en modalidad comunitaria (depende de T012–T014)
- [ ] T016 Crear `HistorialEstado` de solo inserción en `backend/apps/auditoria/models.py`
- [ ] T017 Implementar el servicio de transiciones en `backend/apps/practicas/services.py`: valida la tabla de transiciones, exige motivo y escribe `HistorialEstado` en la misma transacción (depende de T015, T016)
- [ ] T018 Implementar el servicio de asignación que copia `horas_requeridas` desde `ConfiguracionCarrera` en `backend/apps/practicas/services.py`
- [ ] T019 Implementar el filtrado por rol en la consulta (regla 1 de `data-model.md`) en `backend/apps/usuarios/permissions.py`
- [ ] T020 [P] Registrar carreras, configuraciones, períodos, entidades, usuarios y prácticas asignadas en el admin de Django (`backend/apps/*/admin.py`): la práctica llega ya asignada (S-01)

**Checkpoint**: T007–T011 en verde; ya se pueden cargar prácticas asignadas desde el admin.

---

## Phase 3: HU-01 · Registrar el plan de actividades (Priority: P1) 🎯 MVP

**Goal**: el estudiante envía su plan y el tutor académico lo aprueba o lo devuelve.

**Independent Test**: con una práctica `asignada`, el estudiante envía su plan; el tutor lo devuelve con observación, el estudiante lo corrige y el tutor lo aprueba; la práctica pasa a `en curso`.

### Tests for HU-01

- [ ] T021 [P] [HU-01] Test de integración: plan enviado queda `en_revision` y el tutor lo ve pendiente; devolución sin observación se rechaza; devolución con observación genera una nueva versión; aprobación pasa la práctica a `en curso` en `backend/tests/integration/test_plan_actividades.py`

### Implementation for HU-01

- [ ] T022 [P] [HU-01] Crear `PlanActividades` en `backend/apps/actividades/models.py`
- [ ] T023 [P] [HU-01] Crear `Validacion` (exactamente un plan o un reporte; observación obligatoria si se devuelve) en `backend/apps/actividades/models.py`
- [ ] T024 [HU-01] Implementar enviar, devolver y aprobar el plan en `backend/apps/actividades/services.py`, usando el servicio de transiciones de T017
- [ ] T025 [HU-01] Vistas y plantillas para que el estudiante registre su plan y el tutor académico vea su bandeja de planes pendientes en `backend/apps/actividades/views.py` y `backend/templates/actividades/`

**Checkpoint**: HU-01 funciona de punta a punta.

---

## Phase 4: HU-02 · Reportar actividades semanales (Priority: P1)

**Goal**: el estudiante reporta cada semana sus horas y evidencias.

**Independent Test**: con un plan aprobado, el estudiante reporta una semana con una evidencia PDF; el reporte queda `en_revision` con fecha y sus horas no cuentan todavía.

### Tests for HU-02

- [ ] T026 [P] [HU-02] Test de integración: sin plan aprobado no se puede reportar; el reporte queda `en_revision` con fecha de registro; una sola versión activa por semana; las horas no validadas no suman al acumulado en `backend/tests/integration/test_reporte_semanal.py`
- [ ] T027 [P] [HU-02] Test unitario de evidencias: solo PDF, máximo 5 MB, versiones anteriores conservadas; reporte con horas marcadamente altas queda señalado en `backend/tests/unit/test_evidencias.py`

### Implementation for HU-02

- [ ] T028 [P] [HU-02] Crear `ReporteSemanal` y `Evidencia` en `backend/apps/actividades/models.py`
- [ ] T029 [HU-02] Implementar el registro de reportes y la carga versionada de evidencias en `backend/apps/actividades/services.py`
- [ ] T030 [HU-02] Vista y plantilla del reporte semanal con carga de evidencias en `backend/apps/actividades/views.py` y `backend/templates/actividades/`

**Checkpoint**: HU-01 y HU-02 funcionan juntas.

---

## Phase 5: HU-03 · Validar actividades semanales (Priority: P1)

**Goal**: el tutor académico valida o devuelve los reportes, y solo cuentan las horas validadas.

**Independent Test**: el tutor valida un reporte y sus horas se suman con autor y fecha; devuelve otro con observación y vuelve al estudiante.

### Tests for HU-03

- [ ] T031 [P] [HU-03] Test de integración: validar suma las horas y registra autor y fecha (CE-02); devolver sin observación se rechaza; las observaciones anteriores se conservan en `backend/tests/integration/test_validacion_reporte.py`

### Implementation for HU-03

- [ ] T032 [HU-03] Implementar validar y devolver reportes en `backend/apps/actividades/services.py`
- [ ] T033 [HU-03] Vista y plantilla de la bandeja de reportes pendientes del tutor académico en `backend/apps/actividades/views.py` y `backend/templates/actividades/`

---

## Phase 6: HU-04 · Consultar las horas acumuladas (Priority: P1)

**Goal**: el estudiante ve horas validadas, pendientes de validación y requeridas.

**Independent Test**: con reportes validados y en revisión, el avance muestra los tres valores correctos.

### Tests for HU-04

- [ ] T034 [P] [HU-04] Test unitario del cálculo de avance: validadas, en revisión y requeridas; las devueltas no cuentan en `backend/tests/unit/test_avance_horas.py`

### Implementation for HU-04

- [ ] T035 [HU-04] Implementar el cálculo de avance de una práctica en `backend/apps/practicas/services.py`
- [ ] T036 [HU-04] Vista y plantilla del avance de horas del estudiante, visible al entrar (CE-03: menos de 1 minuto) en `backend/apps/practicas/views.py` y `backend/templates/practicas/`

---

## Phase 7: HU-05 · Conocer el estado de todas las prácticas (Priority: P1)

**Goal**: el coordinador ve en un solo lugar el estado de todas las prácticas de su carrera.

**Independent Test**: un coordinador ve las prácticas de su carrera con estado, horas, pendientes y atrasos, y no ve las de otra carrera.

### Tests for HU-05

- [ ] T037 [P] [HU-05] Test de integración del tablero del coordinador: estado, horas acumuladas, pendientes y atrasos por práctica; ninguna práctica de otra carrera en `backend/tests/integration/test_estado_general.py`

### Implementation for HU-05

- [ ] T038 [HU-05] Implementar la consulta consolidada en `backend/apps/reportes/services.py`
- [ ] T039 [HU-05] Vista y plantilla del tablero del coordinador (CE-01) en `backend/apps/reportes/views.py` y `backend/templates/reportes/`

**Checkpoint**: MVP P1 completo (HU-01 a HU-05).

---

## Phase 8: HU-06 · Recibir alertas de atraso (Priority: P2)

**Goal**: el sistema avisa a tiempo de reportes no enviados, revisiones pendientes y horas rezagadas.

**Independent Test**: con una práctica rezagada y una fecha dada, la detección genera las alertas esperadas y sus destinatarios.

### Tests for HU-06

- [ ] T040 [P] [HU-06] Test unitario de rezago con el ejemplo del spec: 240 h en 16 semanas; en la semana 8 se esperan 120 h y hay alerta con menos de 96 h (validadas más en revisión) y no la hay con 96 h o más en `backend/tests/unit/test_regla_rezago.py`
- [ ] T041 [P] [HU-06] Test unitario de plazos: alerta de reporte no enviado al vencer el plazo de reporte de la carrera y de revisión pendiente al vencer el plazo de revisión en días hábiles; destinatarios según el tipo en `backend/tests/unit/test_alertas_plazos.py`

### Implementation for HU-06

- [ ] T042 [P] [HU-06] Crear `Alerta` en `backend/apps/alertas/models.py`
- [ ] T043 [HU-06] Implementar la detección como función que recibe la fecha de evaluación, sin depender del reloj ni del mecanismo de disparo, en `backend/apps/alertas/services.py`
- [ ] T044 [HU-06] Comando de gestión `generar_alertas` (con opción `--fecha` para pruebas) en `backend/apps/alertas/management/commands/generar_alertas.py`, con un test que lo invoca en `backend/tests/integration/test_comando_alertas.py`, y la entrada de cron diaria documentada en `quickstart.md`
- [ ] T045 [HU-06] Vista y plantilla de alertas para cada destinatario (CE-04) en `backend/apps/alertas/views.py` y `backend/templates/alertas/`

---

## Phase 9: HU-07 · Confirmar actividades e informar desde la entidad receptora (Priority: P2)

**Goal**: el tutor de entidad, con cuenta propia, confirma reportes de sus practicantes y registra el informe final.

**Independent Test**: el tutor de entidad confirma un reporte de su practicante y registra el informe final; el acceso a una práctica ajena se rechaza.

### Tests for HU-07

- [ ] T046 [P] [HU-07] Test de integración: la confirmación registra autor y fecha; el informe final queda asociado con autor y fecha; acceder a la práctica de otro practicante se rechaza en `backend/tests/integration/test_tutor_entidad.py`

### Implementation for HU-07

- [ ] T047 [P] [HU-07] Crear `ConfirmacionEntidad` e `InformeFinal` en `backend/apps/actividades/models.py`
- [ ] T048 [HU-07] Implementar confirmar reportes y registrar el informe final en `backend/apps/actividades/services.py`
- [ ] T049 [HU-07] Vistas y plantillas del tutor de entidad (sus practicantes, sus reportes y el registro del informe final) en `backend/apps/actividades/views.py` y `backend/templates/actividades/`

---

## Phase 10: HU-08 · Cerrar la práctica con informe final (Priority: P2)

**Goal**: el coordinador cierra solo las prácticas que cumplen horas e informe final.

**Independent Test**: una práctica completa se cierra; una incompleta se rechaza indicando qué falta.

### Tests for HU-08

- [ ] T050 [P] [HU-08] Test de integración: el estudiante pasa a `en revisión final` al completar las horas, aun antes del fin del período; el cierre con horas e informe pasa a `cerrada`; sin horas o sin informe se rechaza indicando qué falta (CE-05); en modalidad comunitaria sin tutor de entidad el cierre no exige informe; `cerrada` no admite cambios en `backend/tests/integration/test_cierre_practica.py`

### Implementation for HU-08

- [ ] T051 [HU-08] Implementar el paso a revisión final, la devolución a `en curso` y el cierre en `backend/apps/practicas/services.py`
- [ ] T052 [HU-08] Vista y plantilla del cierre con el detalle de lo que falta en `backend/apps/practicas/views.py` y `backend/templates/practicas/`

---

## Phase 11: RF-13 · Suspensión y cancelación (Priority: P2)

**Goal**: el coordinador suspende, reanuda y cancela prácticas con motivo, sin perder las horas validadas.

**Independent Test**: una práctica suspendida se reanuda con sus horas intactas; otra se cancela y queda final.

### Tests for RF-13

- [ ] T053 [P] [RF-13] Test de integración: solo el coordinador suspende, reanuda y cancela; motivo obligatorio al suspender y cancelar; la reanudación conserva las horas validadas; `cancelada` no admite cambios en `backend/tests/integration/test_suspension_cancelacion.py`

### Implementation for RF-13

- [ ] T054 [RF-13] Implementar suspender, reanudar y cancelar sobre el servicio de transiciones de T017 en `backend/apps/practicas/services.py`
- [ ] T055 [RF-13] Vistas y plantillas de suspensión, reanudación y cancelación para el coordinador en `backend/apps/practicas/views.py` y `backend/templates/practicas/`

---

## Phase 12: HU-09 · Consultar el historial de la práctica (Priority: P3)

**Goal**: cualquier práctica muestra su historial completo e inalterable.

**Independent Test**: el historial de una práctica cerrada muestra cada cambio con estado anterior, estado nuevo, autor y fecha.

### Tests for HU-09

- [ ] T056 [P] [HU-09] Test de integración: el historial de una práctica cerrada reconstruye quién, qué y cuándo (CE-06) en `backend/tests/integration/test_historial_practica.py`

### Implementation for HU-09

- [ ] T057 [HU-09] Implementar la consulta del historial en `backend/apps/auditoria/services.py`
- [ ] T058 [HU-09] Vista y plantilla del historial de la práctica en `backend/apps/auditoria/views.py` y `backend/templates/auditoria/`

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: casos límite y verificaciones que cruzan historias.

- [ ] T059 [P] Test e implementación del reemplazo de tutor académico: se cierra la asignación anterior y se conservan horas y validaciones (caso límite, regla 5) en `backend/tests/unit/test_reemplazo_tutor.py` y `backend/apps/practicas/services.py`
- [ ] T060 [P] Actualizar el README con lo que cambió en el entorno y repetir la prueba cruzada
- [ ] T061 Verificar CE-01 a CE-06 contra la implementación y registrar el resultado
- [ ] T062 Comando `cargar_datos_demo` con datos a la escala supuesta (5 carreras, ~300 estudiantes, ~150 prácticas activas) en `backend/apps/reportes/management/commands/cargar_datos_demo.py`; con esos datos, revisar índices del tablero (T038) y del avance (T035) y comprobar CE-03

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias; coincide con el esqueleto del backend.
- **Foundational (Phase 2)**: depende de Setup y **bloquea todas las historias**.
- **HU-01 (Phase 3)**: depende de Foundational.
- **HU-02 (Phase 4)**: depende de HU-01 (sin plan aprobado no hay reportes).
- **HU-03 y HU-04 (Phases 5–6)**: dependen de HU-02.
- **HU-05 (Phase 7)**: depende de HU-04 (usa el cálculo de avance).
- **HU-06 (Phase 8)**: depende de HU-02 y HU-04.
- **HU-07 (Phase 9)**: depende de HU-02.
- **HU-08 (Phase 10)**: depende de HU-03 y HU-07.
- **RF-13 (Phase 11)** y **HU-09 (Phase 12)**: dependen solo de Foundational.
- **Polish (Phase 13)**: al final.

### Within Each Phase

- Los tests se escriben primero y deben fallar.
- Modelos antes que servicios; servicios antes que la interfaz.
- Las vistas y plantillas van al final de cada historia, sobre servicios ya probados.

### Parallel Opportunities

- En Phase 2, los tests T007–T011 y los modelos T013–T014 se hacen en paralelo.
- Terminada Phase 2, RF-13 y HU-09 avanzan en paralelo con la cadena HU-01 → HU-05.
- Terminada HU-02, HU-03, HU-04 y HU-07 avanzan en paralelo.

---

## Implementation Strategy

### MVP First

1. Setup y Foundational.
2. HU-01 a HU-05 (todas P1).
3. **Validar**: CE-01, CE-02 y CE-03 se pueden comprobar con este alcance.

### Incremental Delivery

1. MVP P1 (HU-01 a HU-05).
2. P2: HU-06, HU-07, HU-08 y RF-13.
3. P3: HU-09 (el historial ya se escribe desde Foundational; esta fase solo lo consulta).

## Notes

- Las reglas de dominio viven en los servicios y en la capa de datos, no en las vistas: si más adelante se pasa a una SPA con API (ver research.md), los servicios y sus tests no cambian.
- Hacer commit por tarea o por grupo lógico, con Conventional Commits.
