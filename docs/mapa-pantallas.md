# Mapa de pantallas

Este mapa conecta las historias de usuario del [spec](../specs/001-seguimiento-practicas/spec.md) con las pantallas del prototipo. Cada pantalla usa uno de los patrones del SIAAF descritos en [referencia-siaaf.md](referencia-siaaf.md): **L** (lista), **D** (detalle) o **F** (formulario). El contexto del producto está en [PRODUCT.md](../PRODUCT.md).

**Estado:** confirmado (2026-10-20).

---

## 1. Decisiones de estructura

| Decisión | Resultado |
| --- | --- |
| Ubicación | Sección «Prácticas ›» del módulo académico del SIAAF, junto a «Tutorías». |
| Vista del estudiante | Una pantalla «Mi práctica» con pestañas (Resumen, Plan, Reportes semanales, Informe final), como el detalle de persona del SIAAF. |
| Entrada del tutor académico | Una bandeja única «Pendientes de revisión» con planes, reportes e informes finales, más «Mis tutorados». |
| Personas con varios roles | Menú combinado: un docente que es tutor y coordinador ve las secciones de ambos roles en el mismo menú. |
| Tutor de la entidad | Mismo marco del SIAAF con un menú reducido a sus practicantes. |
| Alertas | La campana de la barra superior del SIAAF muestra las alertas de cada persona; el coordinador tiene además una lista completa. |
| Navegación | Lista → detalle → formulario. El formulario vuelve al detalle al guardar (`?next=`), y la ubicación muestra la ruta completa (`⌂ Prácticas › Mi práctica › Semana 12`). |

## 2. Menú por rol

Las secciones de cada rol cuelgan de «Prácticas ›». Si una persona tiene varios roles, ve la unión de sus secciones.

| Rol | Secciones del menú |
| --- | --- |
| Estudiante | Mis prácticas |
| Tutor académico | Pendientes de revisión · Mis tutorados |
| Tutor de la entidad | Mis practicantes · Reportes por confirmar |
| Coordinador | Prácticas de la carrera · Alertas · Consolidado · Configuración |
| Rectorado y Decanato | Catálogo de entidades · Convenios y cartas de compromiso (fuera del MVP) |

Todos ven también «← Menú Principal» y «Tablero». El tablero muestra un resumen por cada rol de la persona: el avance de horas del estudiante, el número de pendientes del tutor y las alertas activas del coordinador.

## 3. Pantallas

### Estudiante

| ID | Pantalla | Patrón | Historias | Contenido principal |
| --- | --- | :---: | --- | --- |
| E1 | Mis prácticas | L | HU-04 | Sus prácticas (laboral y comunitaria van por separado). Con una sola práctica, entra directo a E2. |
| E2 | Mi práctica | D | HU-04, HU-02 | Cabecera con estado, tipo y subtipo, entidad, tutores y período, y las horas validadas, en revisión y requeridas. Pestañas: **Resumen** (avance frente a lo esperado a la fecha, y qué está pendiente o devuelto), **Plan**, **Reportes semanales** (lista por semana con su estado) e **Informe final**. |
| E3 | Plan de actividades | F | HU-01 | Registrar o corregir el plan y enviarlo a revisión. |
| E4 | Nuevo reporte semanal | F | HU-02 | Semana, actividades, horas y evidencias (PDF de hasta 5 MB, RNF-05). En una ayudantía, rechaza más de 10 h semanales y cita el Art. 341. |
| E5 | Reporte semanal | D | HU-02, HU-03 | Actividades, horas, evidencias, estado, observación de devolución, quién validó y cuándo, y la confirmación de la entidad. |
| E6 | Informe final de actividades | F | HU-10 | Presentar el informe a revisión. |

### Tutor académico

| ID | Pantalla | Patrón | Historias | Contenido principal |
| --- | --- | :---: | --- | --- |
| T1 | Pendientes de revisión | L | HU-01, HU-03, HU-10 | Planes, reportes e informes finales por revisar, con etiqueta de tipo, fecha de envío y días de espera. Marca lo que está fuera del plazo de revisión. |
| T2 | Revisar | D | HU-03 (CU-01) | Muestra el plan, el reporte o el informe con acciones «Validar» y «Devolver». Devolver exige observación (RF-03). Es la misma pantalla para los tres tipos. |
| T3 | Mis tutorados | L | HU-04 | Prácticas que tutoriza, con estado y horas. |
| T4 | Práctica | D | HU-04, HU-11 | Detalle de la práctica, compartido con el coordinador (ver C3). |
| T5 | Evaluación final | F | HU-11 | Porcentaje de la evaluación; muestra el resultado según la regla (aprobada desde 70 %, RF-17). |

### Tutor de la entidad receptora

| ID | Pantalla | Patrón | Historias | Contenido principal |
| --- | --- | :---: | --- | --- |
| R1 | Mis practicantes | L | HU-07 | Sus practicantes de práctica laboral, con estado y horas. |
| R2 | Reportes por confirmar | L | HU-07 | Reportes semanales de sus practicantes que aún no confirmó. |
| R3 | Confirmar reporte | D | HU-07 | El reporte con la acción «Confirmar». |
| R4 | Informe externo | F | HU-07 | Registrar su informe final. |
| R5 | Reportar incumplimiento | F | HU-12 | Describir el incumplimiento; se avisa al tutor académico (RF-18). |

### Coordinador

| ID | Pantalla | Patrón | Historias | Contenido principal |
| --- | --- | :---: | --- | --- |
| C1 | Prácticas de la carrera | L | HU-05 | Las columnas de RF-06 (estudiante, tipo, estado, horas validadas, en revisión y requeridas, alertas y tutor académico), con filtros por período, tipo, estado y alerta. Debe cargar en menos de 2 s con 150 prácticas (RNF-04). |
| C2 | Alertas | L | HU-06 | Reportes no enviados, revisiones pendientes, horas rezagadas e incumplimientos. |
| C3 | Práctica | D | HU-05, HU-09 | Igual que T4, con la pestaña **Historial** (quién, qué y cuándo) y las acciones «Cerrar», «Suspender», «Reanudar» y «Cancelar», según el estado. |
| C4 | Cerrar práctica | F | HU-08 (CU-02) | Lista de los requisitos de RF-09 con lo que falta; solo permite cerrar si se cumplen todos. |
| C5 | Suspender o cancelar | F | RF-13 | Motivo obligatorio. |
| C6 | Consolidado de la carrera | L | HU-13 | Horas y resultado por estudiante y componente, con exportación a CSV (RNF-10). |
| C7 | Configuración de la carrera | F | RF-12 | Horas requeridas por modalidad, plazos de reporte y de revisión, y umbral de rezago. |

### Analista de prácticas DVS (issue #53)

| ID | Pantalla | Patrón | Contenido principal |
| --- | --- | :---: | --- |
| A1 | Consolidado general | L | El patrón de C6 entre carreras, con filtros por período y componente; solo consulta. |
| A2 | Exportación | Acción | CSV UTF-8 del consolidado filtrado, con fechas ISO 8601 (RNF-10). |

### Entidad receptora y Rectorado/Decanato (§3.6, issue #55) — decisión

Estas pantallas no estaban en el mapa original. Se agregan con el issue #55 (Jaime, orden 4) y, como pide la regla del prototipado, la decisión queda anotada aquí además del PR.

| ID | Pantalla | Patrón | Historias | Contenido principal |
| --- | --- | :---: | --- | --- |
| N1 | Catálogo de entidades | L + D | HU-07 | Lista de entidades receptoras con su instrumento (convenio o carta de compromiso), su vigencia (desde, hasta y estado vigente/vencido) y cuántas prácticas vigentes recibe. El detalle es de solo lectura y muestra las prácticas vigentes de la entidad; si no tiene, muestra el vacío de la §4. |
| N2 | Convenios y cartas de compromiso | L | — (fuera del MVP) | Lista única de convenios y cartas con su vigencia y su estado de aprobación. Cada elemento va etiquetado «Fuera del MVP — proyecto R» y remite a la [§4 del spec](../specs/001-seguimiento-practicas/spec.md#fuera-del-alcance): sin registro ni firma. |

- **Decisión (2026-06-05):** el catálogo sigue a `EntidadReceptora` del [data-model](../specs/001-seguimiento-practicas/data-model.md), que solo exige `nombre` y es **opcional** en la práctica comunitaria; el instrumento y la vigencia son datos de consulta, no campos del MVP. N1 y N2 son **solo consulta** (sin POST, sin edición ni firma) porque la gestión de convenios está fuera del alcance y corresponde al proyecto R.

## 4. Estados que el prototipo debe mostrar

- **Práctica:** `asignada` (sin plan aprobado: E2 invita a registrar el plan), `en curso`, `en revisión final`, `suspendida`, `cancelada` y `cerrada` (aprobada o no aprobada). En `suspendida`, `cancelada` y `cerrada` las pantallas son de solo lectura.
- **Plan, reporte e informe:** en revisión, validado y devuelto con observación. El reporte de una práctica laboral muestra además si la entidad lo confirmó.
- **Horas:** al día y rezagada (por debajo del umbral de la carrera, 80 % por defecto).
- **Vacíos:** sin reportes todavía, sin pendientes de revisión, sin alertas y, en el catálogo de entidades, sin prácticas vigentes.
- **Errores:** evidencia que no es PDF o que pasa de 5 MB, ayudantía con más de 10 h y devolución sin observación.

## 5. Primer prototipo

**E2 Mi práctica** (pestañas Resumen y Reportes semanales) y **E4 Nuevo reporte semanal**. Cubren las historias P1 del estudiante y fijan a la vez los patrones de detalle y de formulario.

## 6. Decisiones abiertas

- Qué actor registra el informe del proyecto de vinculación en la práctica comunitaria (afecta a C4 y a la pestaña de informes).
- Si cada práctica tiene un solo tutor académico activo a la vez (S-02; afecta a la cabecera de E2 y a T3).
