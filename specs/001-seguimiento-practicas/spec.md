# Especificación funcional: Seguimiento de prácticas preprofesionales

| Campo | Valor |
| --- | --- |
| **Rama** | `feature/clarify` |
| **Fase SDD** | clarify |
| **Estado** | Borrador para revisión |
| **Entrada** | Ficha 7 del banco de proyectos, guía interna del equipo y contexto del caso UNL (`README.md`) |

> [!NOTE]
> Este documento describe **qué** problema se resuelve y **para quién**. No menciona tecnologías, herramientas ni diseño de interfaz; esas decisiones pertenecen a la fase *plan*.

## Contenido

1. [Problema](#1-problema)
2. [Actores y necesidades](#2-actores-y-necesidades)
3. [Historias de usuario](#3-historias-de-usuario)
4. [Alcance](#4-alcance)
5. [Supuestos](#5-supuestos)
6. [Restricciones](#6-restricciones)
7. [Requisitos funcionales](#7-requisitos-funcionales)
8. [Criterios de éxito](#8-criterios-de-éxito)
9. [Clarifications](#clarifications)

---

## 1. Problema

En la universidad, las prácticas preprofesionales son obligatorias para titularse. Hoy su seguimiento se hace con formularios, correos, mensajes y archivos sueltos que cada carrera maneja a su manera.

| Situación actual | Consecuencia |
| --- | --- |
| El avance de cada práctica está repartido entre estudiantes y tutores. | El coordinador **no sabe en qué estado está cada práctica** sin pedir información. |
| Las horas cumplidas se suman a mano. | **El atraso se descubre tarde**, cuando ya no hay tiempo de corregirlo. |
| Las evidencias circulan sin registro de revisión. | **No se sabe quién validó qué ni cuándo**: no hay trazabilidad. |
| Los documentos de cierre están dispersos. | Cerrar una práctica exige reunirlos y revisarlos uno por uno. |

> [!IMPORTANT]
> **Problema delimitado:** no existe una forma única y confiable de dar seguimiento a una práctica ya asignada, desde su inicio hasta su cierre, que muestre el avance de horas, el estado de las evidencias y quién validó cada paso.
>
> El valor del sistema **no está en almacenar formularios**, sino en el **seguimiento y la trazabilidad** del proceso.

---

## 2. Actores y necesidades

| Actor | Rol en el proceso | Necesidad concreta |
| --- | --- | --- |
| **Estudiante** | Desarrolla la práctica, planifica sus actividades y reporta su avance. | Saber cuántas horas lleva, cuántas le faltan y qué tiene pendiente o devuelto. |
| **Tutor académico** | Docente que orienta, revisa y valida el trabajo del estudiante. | Aprobar o devolver las actividades semanales con observaciones, sin perseguir documentos. |
| **Tutor de la entidad receptora** | Persona de la institución donde el estudiante hace la práctica. Usa el sistema con cuenta propia y solo ve a sus practicantes. | Confirmar las actividades y dejar su informe final registrado sin trámites adicionales. |
| **Coordinador de prácticas** | Docente responsable de las prácticas de la carrera. | Ver el estado de todas las prácticas en un solo lugar y enterarse a tiempo de los atrasos. |

**Actor secundario:** el director de carrera consulta el resultado del cierre para continuar con la acreditación, que queda fuera de este alcance.

---

## 3. Historias de usuario

### Resumen

| ID | Como… | Quiero… | Para… | Prioridad |
| --- | --- | --- | --- | :---: |
| HU-01 | Estudiante | registrar mi plan de actividades | que mi tutor sepa qué voy a hacer y lo apruebe | P1 |
| HU-02 | Estudiante | reportar cada semana mis actividades con horas y evidencias | que mi avance quede registrado | P1 |
| HU-03 | Tutor académico | validar o devolver las actividades semanales | que solo cuenten las horas revisadas | P1 |
| HU-04 | Estudiante | ver mis horas validadas frente a las requeridas | saber cuánto me falta y si voy a tiempo | P1 |
| HU-05 | Coordinador | consultar el estado de todas las prácticas de mi carrera | intervenir sin pedir archivos por correo | P1 |
| HU-06 | Coordinador | recibir una alerta cuando una práctica se atrasa | actuar antes de que el estudiante incumpla | P2 |
| HU-07 | Tutor de la entidad | confirmar actividades y registrar mi informe final | que mi evaluación forme parte del cierre | P2 |
| HU-08 | Coordinador | cerrar la práctica cuando cumple horas e informe final | dejar constancia de que terminó bien | P2 |
| HU-09 | Coordinador | ver el historial de cambios de estado | saber quién hizo qué y cuándo | P3 |

> P1 = imprescindible para el MVP · P2 = importante · P3 = deseable

### Criterios de aceptación

#### HU-01 · Registrar el plan de actividades

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un estudiante con una práctica asignada | registra su plan de actividades | el plan queda «en revisión» y su tutor académico ve que tiene un plan pendiente |
| 2 | un plan en revisión | el tutor académico lo devuelve con observaciones | el estudiante ve las observaciones y puede corregirlo |

#### HU-02 · Reportar actividades semanales

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un plan aprobado | el estudiante reporta la semana con horas y evidencias | el reporte queda con fecha de registro y «en revisión» |
| 2 | un reporte semanal sin validar | se consultan las horas cumplidas | sus horas todavía no se cuentan |

#### HU-03 · Validar actividades semanales

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un reporte en revisión | el tutor académico lo valida | las horas se suman al acumulado y queda registrado quién validó y cuándo |
| 2 | un reporte en revisión | el tutor lo devuelve | debe escribir una observación y el reporte vuelve al estudiante |

#### HU-04 · Consultar las horas acumuladas

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un estudiante con reportes validados | consulta su avance | ve horas validadas, horas pendientes de validación y horas requeridas |

#### HU-05 · Conocer el estado de todas las prácticas

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un conjunto de prácticas en curso | el coordinador consulta el estado general | ve por cada práctica su estado, las horas acumuladas y si tiene pendientes o atrasos |

#### HU-06 · Recibir alertas de atraso

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un estudiante que no reporta su semana dentro del plazo de reporte de su carrera | se cumple ese plazo | el estudiante, su tutor académico y el coordinador reciben una alerta |
| 2 | un reporte sin revisar más allá del plazo de revisión de su carrera | se cumple ese plazo | el tutor académico recibe una alerta |
| 3 | horas validadas más horas en revisión por debajo del umbral de rezago respecto de lo esperado para la fecha | se detecta el rezago | el estudiante, su tutor académico y el coordinador reciben una alerta de atraso |

> **Horas esperadas a una fecha** = horas requeridas × (días transcurridos ÷ días del período). Hay rezago cuando las horas validadas más las horas en revisión quedan por debajo del umbral de rezago (80 % por defecto) de las horas esperadas. Ejemplo: 240 h en un período de 16 semanas; en la semana 8 se esperan 120 h y la alerta se genera por debajo de 96 h.

#### HU-07 · Confirmar actividades e informar desde la entidad receptora

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un estudiante que terminó sus actividades | el tutor de la entidad registra su informe final | el informe queda asociado a la práctica con su autor y fecha |
| 2 | un reporte semanal de uno de sus practicantes | el tutor de la entidad lo confirma | queda registrado quién lo confirmó y cuándo |
| 3 | un tutor de entidad | intenta ver una práctica que no es de uno de sus practicantes | el acceso se rechaza |

> El tutor de la entidad receptora usa el sistema directamente, con cuenta propia y un rol limitado a sus practicantes (ver Clarifications).

#### HU-08 · Cerrar la práctica con informe final

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | una práctica con las horas requeridas validadas y con informe final | el coordinador la cierra | pasa a «cerrada» y ya no admite cambios |
| 2 | una práctica sin las horas requeridas o sin informe final | se intenta cerrar | el cierre se rechaza indicando qué falta |

#### HU-09 · Consultar el historial de la práctica

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | una práctica con movimientos | se consulta su historial | cada cambio muestra estado anterior, estado nuevo, quién lo hizo y la fecha |
| 2 | un registro del historial | alguien intenta modificarlo o borrarlo | la acción no se permite |

### Casos límite

| Caso | Qué debe garantizarse |
| --- | --- |
| El tutor académico deja de ejercer durante la práctica | Se asigna otro tutor sin perder lo ya validado. |
| El estudiante reporta más horas de lo razonable en una semana | El reporte se identifica para revisión. |
| Una evidencia se devuelve varias veces | Se conserva cada versión y cada observación. |
| El estudiante completa las horas antes de la fecha de fin | Puede pasar a revisión final sin esperar al fin del período. |
| La práctica se suspende o se abandona | Queda registrado el motivo y el estado en que quedó; una suspensión puede reanudarse y un abandono se registra como cancelación. |

---

## 4. Alcance

### Dentro del alcance (MVP)

La práctica **ya asignada**, desde su inicio hasta su cierre:

| Área | Qué incluye |
| --- | --- |
| Planificación | Plan de actividades del estudiante y su aprobación. |
| Registro | Actividades semanales con horas y evidencias. |
| Validación | Aprobación o devolución con observaciones por el tutor académico. |
| Horas | Acumulado de horas validadas frente a las requeridas. |
| Alertas | Reportes no enviados, revisiones pendientes y horas rezagadas. |
| Cierre | Informe final y cierre de la práctica. |
| Trazabilidad | Historial de cambios de estado de la práctica. |
| Acceso | Cada actor ve y hace solo lo que le corresponde. |

### Fuera del alcance

| Elemento | Motivo |
| --- | --- |
| Postulación y emparejamiento con empresas | La práctica llega ya asignada. |
| Gestión de convenios y cartas de compromiso | Corresponde a otro proyecto del banco (proyecto R). |
| Integración con el sistema académico institucional (SIAAF) | Depende de acuerdos externos fuera del ciclo. |
| Firma electrónica | Requiere validez legal y certificación externa. |
| Aplicación móvil nativa | No es necesaria para resolver el problema de seguimiento. |
| Homologación y convalidación | Flujos paralelos con reglas propias; fase posterior. |
| Encuesta de satisfacción y certificado oficial | Ocurren después del cierre; fase posterior. |
| Notas académicas y gestión financiera | No forman parte del seguimiento de la práctica. |

---

## 5. Supuestos

| ID | Supuesto | Estado |
| --- | --- | --- |
| S-01 | La práctica ya viene asignada: estudiante, entidad, tutor académico, período y horas requeridas se conocen al iniciar. | Confirmado por la guía |
| S-02 | Cada práctica tiene un solo tutor académico activo a la vez. | Por confirmar |
| S-03 | El reporte de actividades es semanal; los plazos de reporte y de revisión los define cada carrera. | Confirmado en clarify |
| S-04 | Solo cuentan como cumplidas las horas validadas por el tutor académico. | Por confirmar |
| S-05 | Los usuarios tienen conexión a internet para registrar y revisar actividades. | Por confirmar |

---

## 6. Restricciones

| Tipo | Restricción |
| --- | --- |
| Normativa | El reglamento define las horas mínimas. El estudio del caso UNL cita 240 h laborales y 120 h comunitarias en modalidad presencial, con excepciones por carrera; por eso se configuran por carrera y modalidad, y el sistema no fija ningún valor. Las horas de cada práctica se copian de esa configuración al asignarla. |
| Servicio comunitario | No siempre tiene tutor de entidad receptora; el proceso debe funcionar sin él. |
| Tiempo | El proyecto se desarrolla dentro de un ciclo académico; el alcance se limita al MVP. |
| Información | Los procesos se basan en un instructivo que estaba en construcción y aún no se validaron con usuarios reales. |
| Privacidad | Los datos de un estudiante solo los ven él, sus tutores y el coordinador de su carrera. |

---

## 7. Requisitos funcionales

| ID | El sistema debe… | Historia |
| --- | --- | :---: |
| RF-01 | Permitir al estudiante registrar su plan de actividades y enviarlo a revisión. | HU-01 |
| RF-02 | Permitir al estudiante registrar actividades semanales con horas y adjuntar evidencias. | HU-02 |
| RF-03 | Permitir al tutor académico validar o devolver planes y reportes; la devolución exige observación. | HU-01, HU-03 |
| RF-04 | Registrar en cada validación quién la realizó y en qué fecha. | HU-03 |
| RF-05 | Calcular las horas validadas de cada práctica y compararlas con las requeridas. | HU-04 |
| RF-06 | Mostrar al coordinador el estado de todas las prácticas de su carrera. | HU-05 |
| RF-07 | Generar alertas por reportes no enviados, revisiones pendientes y horas rezagadas, según los plazos y el umbral de rezago de la carrera. | HU-06 |
| RF-08 | Permitir al tutor de la entidad receptora, con cuenta propia, confirmar los reportes semanales de sus practicantes y registrar su informe final. | HU-07 |
| RF-09 | Permitir el cierre solo si la práctica cumple horas e informe final. | HU-08 |
| RF-10 | Guardar un historial inalterable de los cambios de estado de cada práctica. | HU-09 |
| RF-11 | Restringir lo que cada actor puede ver y hacer según su rol. | Todas |
| RF-12 | Permitir configurar por carrera las horas requeridas de cada modalidad, los plazos de reporte y de revisión, y el umbral de rezago. | HU-04, HU-06 |
| RF-13 | Permitir al coordinador suspender, reanudar y cancelar una práctica, exigiendo un motivo para suspender y para cancelar. | HU-09 |

### Estados de la práctica

```text
asignada ──► en curso ──► en revisión final ──► cerrada
                ▲ │
                │ ▼
             suspendida ──► cancelada
```

| Estado | Significado | Pasa a |
| --- | --- | --- |
| `asignada` | La práctica existe, pero el estudiante aún no tiene plan aprobado. | `en curso` |
| `en curso` | Plan aprobado; el estudiante reporta actividades semanales. | `en revisión final`, `suspendida` |
| `en revisión final` | Horas cumplidas; se espera el informe final. | `cerrada`, `en curso` |
| `cerrada` | Práctica terminada; no admite cambios. | — |
| `suspendida` | Práctica detenida por el coordinador, con motivo; conserva las horas validadas. | `en curso`, `cancelada` |
| `cancelada` | Práctica abandonada; el coordinador registra el motivo. No admite cambios. | — |

> Solo el coordinador suspende, reanuda o cancela una práctica (ver Clarifications).

### Conceptos clave

| Concepto | Definición |
| --- | --- |
| Práctica | Relación entre un estudiante, una entidad receptora y un tutor académico durante un período, de un tipo (`laboral` o `comunitaria`) y con horas requeridas copiadas de la configuración de su carrera al asignarla. Las prácticas laboral y comunitaria de un estudiante son prácticas separadas. |
| Configuración de carrera | Horas requeridas por modalidad, plazos de reporte y de revisión, y umbral de rezago de una carrera. |
| Plan de actividades | Lo que el estudiante se compromete a hacer. |
| Reporte semanal | Actividades realizadas en una semana, con horas y evidencias. |
| Evidencia | Respaldo de una actividad, con autor, fecha y estado de revisión. |
| Validación | Decisión del tutor (aprobado o devuelto), con observación, autor y fecha. |
| Alerta | Aviso generado por un atraso o un pendiente. |
| Informe final | Valoración de cierre del tutor de la entidad receptora. |
| Historial | Registro de cada cambio de estado de la práctica. |

---

## 8. Criterios de éxito

| ID | Criterio | Cómo se verifica |
| --- | --- | --- |
| CE-01 | El coordinador consulta el estado de todas las prácticas de su carrera **sin pedir archivos por correo**. | Prueba con el coordinador: obtiene el estado de cada práctica sin solicitar nada a terceros. |
| CE-02 | El **100 %** de las evidencias validadas queda con **fecha y nombre de quien la validó**. | Revisión de todas las evidencias validadas: ninguna sin autor o fecha. |
| CE-03 | Un estudiante conoce sus horas validadas y faltantes **en menos de 1 minuto**. | Prueba cronometrada con estudiantes. |
| CE-04 | Toda práctica atrasada genera una alerta **antes** de la fecha de fin del período. | Caso de prueba con una práctica rezagada. |
| CE-05 | **Ninguna** práctica se cierra sin las horas requeridas y sin informe final. | Intento de cierre de una práctica incompleta: se rechaza. |
| CE-06 | Para cualquier práctica se reconstruye el historial completo: quién, qué y cuándo. | Consulta del historial de una práctica cerrada. |

---

## Clarifications

### Session 2026-10-11

- Q: ¿El tutor de la entidad receptora usa el sistema directamente? → A: Sí, con cuenta propia y un rol limitado: solo ve a sus practicantes, confirma sus reportes semanales y registra el informe final.
- Q: ¿Cada cuánto se reporta y con qué plazos? → A: Reporte semanal; los plazos de reporte y de revisión se configuran por carrera (por defecto 3 días tras cerrar la semana y 5 días hábiles).
- Q: ¿Quién suspende una práctica y puede retomarse? → A: Solo el coordinador, con motivo obligatorio; puede reanudarla a `en curso` conservando las horas validadas o pasarla a `cancelada` (final, con motivo).
- Q: ¿Cómo se relacionan las prácticas laboral y comunitaria? → A: Son prácticas separadas, cada una con su tipo, tutor, plan y cierre; las horas requeridas se copian de la configuración de carrera y modalidad al asignarla.
- Q: ¿Cuándo se considera atrasada una práctica? → A: Cuando las horas validadas más las en revisión quedan por debajo del umbral de rezago (80 % por defecto, configurable por carrera) de las horas esperadas linealmente a la fecha.
