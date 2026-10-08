# Sistema de gestión de prácticas preprofesionales (caso UNL)

Contexto del proyecto para el equipo. Resume cómo gestiona la Universidad Nacional de Loja (UNL) sus prácticas preprofesionales y qué debe resolver el sistema a construir.

**Fuente principal:** Trabajo de Integración Curricular de Guamán y Novillo (UNL, enero 2025), que desarrolló un módulo de prácticas para el SIAAF. Se apoya en el Reglamento de Régimen Académico de la UNL, en el instructivo de prácticas (en construcción en ese momento) y en entrevistas con la Dirección de Vinculación con la Sociedad (DVS).

## Contenido

1. [Situación investigada](#1-situación-investigada)
2. [Problema principal](#2-problema-principal)
3. [Actores](#3-actores)
4. [Necesidades por actor](#4-necesidades-por-actor)
5. [Proceso](#5-proceso)
6. [Alcance preliminar](#6-alcance-preliminar)
7. [Restricciones conocidas](#7-restricciones-conocidas)
8. [Criterios iniciales de éxito](#8-criterios-iniciales-de-éxito)
9. [Papel del backend](#9-papel-del-backend)
10. [Nota sobre trabajos previos](#nota-sobre-trabajos-previos)

---

## 1. Situación investigada

En la UNL las prácticas son obligatorias para titularse y tienen dos componentes:

- **Laborales:** pasantías o ayudantías de cátedra e investigación.
- **Servicio comunitario.**

Según el estudio citado, **no están centralizadas:** cada carrera usa sus propios repositorios, formatos y procesos. La DVS, que supervisa el tema, no tiene una base única de convenios y cartas de compromiso. Para pedir informes finales debe insistir a cada carrera por oficios, correos y mensajes, y recibe respuestas tardías o incompletas.

## 2. Problema principal

La gestión de las prácticas está **fragmentada y sin trazabilidad**. No hay una vista única del avance de cada estudiante, de los convenios vigentes ni del cumplimiento de horas. Además, la documentación (cartas, planes, asistencia, informes, evaluaciones) circula en formatos distintos y se legaliza a mano.

El sistema debe **dar seguimiento y trazabilidad a un proceso con varias etapas**, no solo guardar formularios.

## 3. Actores

| Actor | Rol en el proceso |
| --- | --- |
| Estudiante | Se postula o es asignado, planifica actividades, registra asistencia, sube evidencias y responde la encuesta. |
| Docente responsable de prácticas (por carrera) | Gestiona convenios y cartas, arma el programa, asigna estudiantes y emite el informe de cumplimiento. |
| Tutor académico | Orienta el plan de actividades, hace seguimiento, retroalimenta, evalúa y legaliza documentos. |
| Tutor institucional (entidad receptora) | Monitorea al estudiante y emite el informe final. No aplica en servicio comunitario. |
| Director de carrera | Aprueba el programa, aprueba homologaciones y convalidaciones, emite el certificado final. |
| Secretaría de carrera | Revisa y legaliza la documentación. |
| Analista de prácticas (DVS) | Crea escenarios y encuestas, consolida datos y genera reportes. |
| Entidad receptora | Recibe estudiantes mediante convenio o carta de compromiso. |
| Rectorado, Procuraduría, Decanato | Aprueban y revisan convenios y firman cartas. |

## 4. Necesidades por actor

- **Estudiante:** saber en qué etapa está, cuántas horas lleva y qué documentos le faltan, y descargar su certificado.
- **Responsable y tutores:** centralizar los planes y las asistencias, revisar y aprobar o rechazar con observaciones, y reasignar tutor si el docente cesa funciones.
- **Director y secretaría:** aprobar y legalizar sin papel físico, con evidencia clara de quién hizo qué y cuándo.
- **DVS y analista:** tener todos los convenios y escenarios en un solo lugar, obtener reportes consolidados sin pedirlos a cada carrera y medir la satisfacción para decidir renovaciones.
- **Entidad receptora:** que su informe final y su evaluación se registren sin burocracia.

## 5. Proceso

Momentos que el sistema debe diferenciar:

1. **Gestión de escenarios:** convenio o carta de compromiso vigente → se registra, aprueba y habilita el escenario.
2. **Planificación y asignación:** se designa responsable y tutores, se elabora el programa, el director lo aprueba y se asigna a los estudiantes.
3. **Desarrollo:** el estudiante registra su plan de actividades y la asistencia con las horas.
4. **Seguimiento:** el tutor revisa, el institucional informa y el responsable elabora el informe de cumplimiento.
5. **Evaluación y acreditación:** se evalúa, se legalizan los anexos, se emite el certificado y se aplica la encuesta de satisfacción.
6. **Flujos paralelos:** homologación (horas ya cumplidas en otra institución, con máximo 10 años de antigüedad) y convalidación (actividades extracurriculares reconocidas como prácticas).

### Respuestas a las preguntas iniciales

- **Asignación o aprobación:** el responsable arma el programa, el director lo aprueba y luego se asigna a los estudiantes. El escenario debe tener convenio o carta vigente.
- **Actores:** los de la tabla anterior, desde el escenario hasta el certificado.
- **Evidencias:** plan de actividades, registro de asistencia con horas, informe del tutor institucional, informe de actividades, evaluación y encuesta de satisfacción.
- **Control del avance:** horas cumplidas frente a horas requeridas, y estado de cada documento (pendiente, en revisión, legalizado, devuelto).
- **Alertas útiles:** convenio por vencer, horas rezagadas, documento pendiente de revisión o legalización, informe no entregado, tutor sin asignar o reemplazado, y encuesta pendiente.

## 6. Alcance preliminar

### Incluye (MVP)

- Autenticación con roles.
- Catálogo de entidades y escenarios con convenios y cartas, y su vigencia.
- Programas de prácticas y asignación de estudiantes.
- Portafolio del estudiante con plan, asistencia y evidencias.
- Flujo de revisión y aprobación con estados.
- Evaluación y certificado de cumplimiento.
- Alertas y reportes básicos.

### Fase posterior

- Homologación y convalidación.
- Encuesta de satisfacción y analítica.
- Integración con el sistema académico.

### Fuera de alcance

- Cálculo de notas académicas.
- Gestión financiera.
- Firma electrónica avanzada.

## 7. Restricciones conocidas

- **Normativas:** el Reglamento CES y el reglamento UNL fijan las horas. El estudio cita 240 h laborales y 120 h comunitarias en modalidad presencial. Derecho, Odontología y Laboratorio Clínico exigen 480 h laborales. La modalidad a distancia es 256 h y 144 h. Estos valores deben ser **configurables por carrera** y verificarse con la normativa vigente.
- **Variabilidad:** las carreras de Salud usan internado rotativo y externado. El servicio comunitario no requiere tutor institucional. Solo Rectorado aprueba convenios.
- **Tecnológicas (en el proyecto real):** autenticación centralizada (SAC), Python/Django/PostgreSQL por lineamiento de DTI, mismo diseño visual que el SIAAF, respuesta de 2 a 10 segundos y compatibilidad con cualquier navegador. En el proyecto académico la elección del stack puede ser libre.
- **De información:** el instructivo estaba en construcción, así que los procesos pueden haber cambiado. Falta validar con usuarios reales.

## 8. Criterios iniciales de éxito

- Un solo repositorio de convenios, cartas y escenarios, con estado de vigencia.
- Cada práctica con trazabilidad completa: quién, qué, cuándo y en qué estado.
- Consultar el avance de horas por estudiante y por carrera sin pedir informes por oficio.
- Certificado generado una vez legalizados todos los anexos.
- Reportes consolidados para la DVS en minutos.
- Alertas que se disparan antes de que ocurra el incumplimiento.
- Control de acceso: cada rol ve y hace solo lo que le corresponde.

## 9. Papel del backend

El backend es el que hace que el sistema sea más que un almacén de formularios:

- **Máquina de estados:** define las etapas de la práctica y los documentos, y sus transiciones válidas (por ejemplo, no se puede certificar sin anexos legalizados).
- **Reglas de negocio:** valida que el convenio esté vigente, acumula horas, compara contra las requeridas por carrera y modalidad, y controla la asignación y el reemplazo de tutores.
- **Autenticación y autorización por roles (RBAC),** con aislamiento de datos por carrera.
- **Auditoría:** historial inmutable de cambios y aprobaciones, que es la base de la trazabilidad.
- **Gestión de evidencias:** almacenamiento seguro de archivos con metadatos y versionado.
- **Tareas programadas y notificaciones:** generan las alertas por vencimientos, retrasos y pendientes.
- **Generación de documentos y reportes:** certificados, informes y matrices consolidadas exportables.
- **API para integraciones,** por ejemplo con el sistema académico o la entidad receptora.

**Entidades núcleo sugeridas:** Usuario/Rol, Carrera, Entidad receptora, Convenio/Carta, Escenario, Programa, Asignación (estudiante–práctica–tutor), Plan de actividades, Registro de asistencia, Evidencia/Documento, Evaluación, Certificado, Alerta, Bitácora de auditoría.

## Nota sobre trabajos previos

Ya existe un módulo hecho dentro del SIAAF de la UNL, así que este proyecto es una propuesta distinta para el banco académico y conviene usar ese trabajo como referencia, no como algo a copiar.

## Cómo trabajar en este repositorio

El repo usa **GitFlow**. Antes de tocar código, leé [`CONTRIBUTING.md`](CONTRIBUTING.md): ahí están el modelo de ramas, los comandos de `git flow` y la convención de commits.
