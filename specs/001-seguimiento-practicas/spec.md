# Especificación funcional: Seguimiento de prácticas preprofesionales

| Campo | Valor |
| --- | --- |
| **Rama** | `001-seguimiento-practicas` (ramas `feature/spec` y `feature/clarify` integradas en `develop`) |
| **Fase SDD** | specify y clarify (completadas; actualizada con el reglamento el 2026-10-18; actualizada para la semana 2 el 2026-10-18) |
| **Estado** | Vigente para planificación (v0.3.0) |
| **Entrada** | Ficha 7 del banco de proyectos, guía interna del equipo, contexto del caso UNL (`README.md`) y Reglamento de Régimen Académico de la UNL (compendio en [`docs/fuentes/reglamento-practicas-unl.md`](../../docs/fuentes/reglamento-practicas-unl.md); texto oficial en [`docs/fuentes/reglamento-regimen-academico-unl-ocs-27-01-2021.pdf`](../../docs/fuentes/reglamento-regimen-academico-unl-ocs-27-01-2021.pdf)) |

> [!NOTE]
> Este documento describe **qué** problema se resuelve y **para quién**. No menciona tecnologías, herramientas ni diseño de interfaz; esas decisiones pertenecen a la fase *plan*.
>
> Las referencias «Art. N» remiten al Reglamento de Régimen Académico de la UNL. La explicación de cada requisito, con su porqué, está en la [guía de requisitos](../../docs/guia-requisitos.md).

## Contenido

1. [Problema](#1-problema)
2. [Actores y necesidades](#2-actores-y-necesidades)
3. [Historias de usuario](#3-historias-de-usuario)
4. [Alcance](#4-alcance)
5. [Supuestos](#5-supuestos)
6. [Restricciones](#6-restricciones)
7. [Requisitos funcionales](#7-requisitos-funcionales)
8. [Requisitos no funcionales](#8-requisitos-no-funcionales)
9. [Revisión de calidad de los requisitos](#9-revisión-de-calidad-de-los-requisitos)
10. [Casos de uso](#10-casos-de-uso)
11. [Criterios de éxito](#11-criterios-de-éxito)
12. [Clarifications](#clarifications)

---

## 1. Problema

En la universidad, las prácticas preprofesionales son obligatorias para titularse: el certificado de horas cumplidas es requisito para la declaratoria de aptitud legal previa a la sustentación o al examen complexivo (Art. 235). Hoy su seguimiento se hace con formularios, correos, mensajes y archivos sueltos que cada carrera maneja a su manera.

| Situación actual | Consecuencia |
| --- | --- |
| El avance de cada práctica está repartido entre estudiantes y tutores. | El coordinador **no sabe en qué estado está cada práctica** sin pedir información. |
| Las horas cumplidas se suman a mano. | **El atraso se descubre tarde**, cuando ya no hay tiempo de corregirlo. |
| Las evidencias circulan sin registro de revisión. | **No se sabe quién validó qué ni cuándo**: no hay trazabilidad. |
| Los documentos de cierre están dispersos. | Cerrar una práctica exige reunirlos y revisarlos uno por uno. |
| La evaluación final y su resultado no quedan en un registro común. | No se puede demostrar que la práctica se aprobó con el **100 % de las horas y al menos 70 %** de desempeño (Art. 339). |

> [!IMPORTANT]
> **Problema delimitado:** no existe una forma única y confiable de dar seguimiento a una práctica ya asignada, desde su inicio hasta su cierre, que muestre el avance de horas, el estado de las evidencias, la evaluación final y quién validó cada paso.
>
> El valor del sistema **no está en almacenar formularios**, sino en el **seguimiento y la trazabilidad** del proceso.

---

## 2. Actores y necesidades

| Actor | Nombre en el reglamento | Rol en el proceso | Necesidad concreta |
| --- | --- | --- | --- |
| **Estudiante** | Estudiante | Desarrolla la práctica, planifica sus actividades, reporta su avance y presenta su informe final de actividades. | Saber cuántas horas lleva, cuántas le faltan y qué tiene pendiente o devuelto. |
| **Tutor académico** | Tutor académico (Art. 336) | Docente que orienta el plan, da seguimiento, revisa el informe final del estudiante y evalúa la práctica. | Aprobar o devolver las actividades semanales con observaciones y registrar la evaluación final, sin perseguir documentos. |
| **Tutor de la entidad receptora** | Tutor institucional (Art. 337) | Persona nombrada por la entidad donde se hace una práctica **laboral**. Usa el sistema con cuenta propia y solo ve a sus practicantes. No existe en el servicio comunitario. | Confirmar las actividades, reportar incumplimientos y dejar su informe final registrado sin trámites adicionales. |
| **Coordinador de prácticas** | Docente responsable de prácticas de la carrera (Art. 335) | Docente designado en cada carrera para gestionar las prácticas y presentar el informe consolidado de cumplimiento. | Ver el estado de todas las prácticas en un solo lugar, enterarse a tiempo de los atrasos y obtener el consolidado para la dirección. |

**Actor secundario:** el director de carrera recibe el informe consolidado y emite la certificación de horas por componente (Art. 340), que queda fuera de este alcance.

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
| HU-07 | Tutor de la entidad | confirmar actividades y registrar mi informe final | que mi informe forme parte de la evaluación | P2 |
| HU-08 | Coordinador | cerrar la práctica cuando cumple todos los requisitos de acreditación | dejar constancia de su resultado | P2 |
| HU-09 | Coordinador | ver el historial de cambios de estado | saber quién hizo qué y cuándo | P3 |
| HU-10 | Estudiante | presentar mi informe final de actividades | que mi tutor académico lo revise antes del cierre | P2 |
| HU-11 | Tutor académico | registrar la evaluación final de la práctica | que el resultado se decida con la regla del reglamento | P2 |
| HU-12 | Tutor de la entidad | reportar un incumplimiento del practicante | que el tutor académico actúe a tiempo | P2 |
| HU-13 | Coordinador | obtener el informe consolidado de cumplimiento de mi carrera | presentarlo al director de carrera | P3 |

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
| 3 | una práctica de subtipo ayudantía | el estudiante intenta reportar más de 10 horas en una semana | el reporte se rechaza y el mensaje indica el máximo de 10 horas semanales (Art. 341); un reporte de 10 horas se acepta |
| 4 | una práctica laboral que no es ayudantía, o una comunitaria | el estudiante reporta más de 40 horas en una semana | el reporte se registra «en revisión» y queda identificado para que el tutor lo revise |

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
| 1 | un estudiante de práctica laboral que terminó sus actividades | el tutor de la entidad registra su informe final | el informe queda asociado a la práctica con su autor y fecha |
| 2 | un reporte semanal de uno de sus practicantes | el tutor de la entidad lo confirma | queda registrado quién lo confirmó y cuándo |
| 3 | un tutor de entidad | intenta ver una práctica que no es de uno de sus practicantes | el acceso se rechaza |

> El tutor de la entidad receptora usa el sistema directamente, con cuenta propia y un rol limitado a sus practicantes (ver Clarifications). Las prácticas de servicio comunitario no tienen tutor de entidad (Art. 337).

#### HU-08 · Cerrar la práctica

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | una práctica con el 100 % de las horas requeridas validadas, informe final del estudiante revisado, informe externo registrado y evaluación final | el coordinador la cierra | pasa a «cerrada» con el resultado de la evaluación y ya no admite cambios |
| 2 | una práctica a la que le falta cualquiera de esos elementos | se intenta cerrar | el cierre se rechaza indicando qué falta |
| 3 | una práctica cerrada con resultado «no aprobada» | el estudiante necesita acreditar ese componente | debe cumplir una nueva práctica; las horas de la anterior no se trasladan (Art. 339) |

> **Informe externo:** en la práctica laboral es el informe final del tutor de la entidad; en la de servicio comunitario es el informe del proyecto de vinculación (Art. 339).

#### HU-09 · Consultar el historial de la práctica

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | una práctica con movimientos | se consulta su historial | cada cambio muestra estado anterior, estado nuevo, quién lo hizo y la fecha |
| 2 | un registro del historial | alguien intenta modificarlo o borrarlo | la acción no se permite |

#### HU-10 · Presentar el informe final de actividades

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | una práctica en revisión final | el estudiante presenta su informe final de actividades | el informe queda «en revisión» y su tutor académico ve que tiene un informe pendiente |
| 2 | un informe final en revisión | el tutor académico lo devuelve con observaciones | el estudiante ve las observaciones y puede corregirlo |

#### HU-11 · Registrar la evaluación final

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | una práctica con informe final del estudiante revisado e informe externo registrado | el tutor académico registra un desempeño de 70 % o más | la evaluación queda con resultado «aprobada», autor y fecha |
| 2 | la misma práctica | el tutor registra un desempeño menor a 70 % | la evaluación queda con resultado «no aprobada», autor y fecha |
| 3 | una práctica sin informe externo registrado | el tutor intenta evaluarla | la evaluación se rechaza indicando que falta el informe |

#### HU-12 · Reportar un incumplimiento

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | una práctica laboral en curso | el tutor de la entidad reporta un incumplimiento con su descripción | el tutor académico recibe una alerta y el reporte queda en la práctica con autor y fecha |

#### HU-13 · Obtener el informe consolidado

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | prácticas cerradas de la carrera en un período | el coordinador solicita el consolidado | ve, por estudiante, las horas cumplidas y el resultado de cada componente (laboral y comunitario) |

### Casos límite

| Caso | Qué debe garantizarse |
| --- | --- |
| El tutor académico deja de ejercer durante la práctica | Se asigna otro tutor sin perder lo ya validado. |
| El estudiante reporta más horas de lo razonable en una semana | En práctica laboral o comunitaria, más de 40 h en una semana se identifica para revisión del tutor; en ayudantías, más de 10 h se rechaza (Art. 341). |
| Una evidencia se devuelve varias veces | Se conserva cada versión y cada observación. |
| El estudiante completa las horas antes de la fecha de fin | Puede pasar a revisión final sin esperar al fin del período. |
| La práctica se suspende o se abandona | Queda registrado el motivo y el estado en que quedó; una suspensión puede reanudarse y un abandono se registra como cancelación. |
| La evaluación final es menor a 70 % | La práctica se cierra como «no aprobada»; el estudiante repite el componente en una práctica nueva (Art. 339). |
| Una práctica comunitaria no tiene proyecto de vinculación | No puede registrarse: el servicio comunitario se realiza siempre dentro de un proyecto aprobado (Art. 338, 347). |
| El estudiante cumple menos del 100 % de las horas | La práctica no puede cerrarse; las fracciones de horas no se acreditan (Art. 339, 343). |

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
| Alertas | Reportes no enviados, revisiones pendientes, horas rezagadas e incumplimientos reportados. |
| Evaluación | Informe final del estudiante, informe externo y evaluación final con resultado. |
| Cierre | Cierre de la práctica con su resultado y consolidado de cumplimiento por carrera. |
| Trazabilidad | Historial de cambios de estado de la práctica. |
| Acceso | Cada actor ve y hace solo lo que le corresponde. |

### Fuera del alcance

| Elemento | Motivo |
| --- | --- |
| Postulación y emparejamiento con empresas | La práctica llega ya asignada. |
| Selección de ayudantes de docencia e investigación | Los requisitos de nota y promedio (Art. 341) se verifican al asignar, antes del seguimiento. |
| Programa de prácticas del período | Lo elabora el docente responsable al inicio del período (Art. 335); es planificación institucional. |
| Gestión de convenios y cartas de compromiso | Corresponde a otro proyecto del banco (proyecto R); los firman Rector y Decanos (Art. 342). |
| Compensación y afiliación al IESS de pasantes | Es obligación de la entidad receptora (Art. 333), no del seguimiento académico. |
| Integración con el sistema académico institucional (SIAAF) | Depende de acuerdos externos fuera del ciclo. |
| Firma electrónica | Requiere validez legal y certificación externa. |
| Aplicación móvil nativa | No es necesaria para resolver el problema de seguimiento. |
| Homologación y convalidación | Flujos paralelos con reglas propias (Art. 343, 344); fase posterior. |
| Internados rotativos y prácticas de Derecho | Enfermería y Medicina tienen rotaciones con reparto asistencial/docente (Art. 580, 581); Derecho depende de normativa externa (Art. 334). |
| Prácticas de posgrado | Se rigen por las Unidades Asistenciales Docentes (Art. 345, 610). |
| Encuesta de satisfacción y certificado oficial | Ocurren después del cierre; el certificado lo emite el director de carrera (Art. 340). |
| Notas académicas y gestión financiera | No forman parte del seguimiento de la práctica. |

---

## 5. Supuestos

| ID | Supuesto | Estado |
| --- | --- | --- |
| S-01 | La práctica ya viene asignada: estudiante, entidad, tutor académico, período, tipo, subtipo y horas requeridas se conocen al iniciar. | Confirmado por la guía |
| S-02 | Cada práctica tiene un solo tutor académico activo a la vez. | Por confirmar |
| S-03 | El reporte de actividades es semanal; los plazos de reporte y de revisión los define cada carrera. | Confirmado en clarify |
| S-04 | Solo cuentan como cumplidas las horas validadas por el tutor académico. | Por confirmar |
| S-05 | Los usuarios tienen conexión a internet para registrar y revisar actividades. | Por confirmar |
| S-06 | Una práctica puede ejecutarse en un período ordinario, extraordinario o vacacional; el sistema no restringe el tipo de período. | Confirmado por el reglamento (Art. 21, 338, 395) |
| S-07 | La práctica comunitaria pertenece siempre a un proyecto de vinculación aprobado. | Confirmado por el reglamento (Art. 338, 347) |

---

## 6. Restricciones

| Tipo | Restricción |
| --- | --- |
| Normativa | El reglamento define las horas por carrera y modalidad (Art. 334): 240 h laborales y 120 h comunitarias en carreras presenciales, 256 h y 144 h a distancia, y 480 h y 120 h en Odontología y Laboratorio Clínico. Por eso se configuran por carrera y modalidad, y el sistema no fija ningún valor. Las horas de cada práctica se copian de esa configuración al asignarla. |
| Acreditación | Una práctica se aprueba solo con el 100 % de las horas programadas y al menos 70 % en la evaluación; si no, se repite (Art. 339). |
| Servicio comunitario | No tiene tutor de entidad receptora (Art. 337); el proceso debe funcionar sin él y usar el informe del proyecto de vinculación. |
| Relación laboral | La práctica no crea vínculo laboral con la entidad (Art. 332); el sistema no registra datos de contratación. |
| Tiempo | El proyecto se desarrolla dentro de un ciclo académico; el alcance se limita al MVP. |
| Información | Los procesos se basan en el reglamento y en un instructivo que estaba en construcción; aún no se validaron con usuarios reales. |
| Privacidad | Los datos de un estudiante solo los ven él, sus tutores y el coordinador de su carrera. |
| Integración institucional | El sistema se concibe como un módulo del sistema académico existente de la UNL. Durante el prototipado, su diseño (navegación, terminología y datos de estudiantes) se contrasta con ese sistema. La integración técnica con SIAAF sigue fuera del alcance. |

---

## 7. Requisitos funcionales

| ID | El sistema debe… | Historia | Norma |
| --- | --- | :---: | :---: |
| RF-01 | Permitir al estudiante registrar su plan de actividades y enviarlo a revisión. | HU-01 | Art. 336 |
| RF-02 | Permitir al estudiante registrar actividades semanales con horas y adjuntar evidencias en los formatos y con el tamaño máximo definidos en RNF-05. | HU-02 | Art. 11 |
| RF-03 | Permitir al tutor académico validar o devolver planes y reportes; la devolución exige observación. | HU-01, HU-03 | Art. 336 |
| RF-04 | Registrar en cada validación quién la realizó y en qué fecha. | HU-03 | — |
| RF-05 | Calcular las horas validadas de cada práctica y compararlas con las requeridas. | HU-04 | Art. 334, 339 |
| RF-06 | Mostrar al coordinador, por cada práctica de su carrera: estudiante, tipo, estado, horas validadas, horas en revisión, horas requeridas, alertas activas y tutor académico. | HU-05 | Art. 331, 335 |
| RF-07 | Generar alertas por reportes no enviados, revisiones pendientes, horas rezagadas e incumplimientos reportados, según los plazos y el umbral de rezago de la carrera. | HU-06, HU-12 | Art. 336 |
| RF-08 | Permitir al tutor de la entidad receptora, con cuenta propia, confirmar los reportes semanales de sus practicantes de una práctica laboral y registrar su informe final. | HU-07 | Art. 337 |
| RF-09 | Permitir el cierre solo si la práctica tiene el 100 % de las horas requeridas validadas, el informe final del estudiante revisado, el informe externo registrado y la evaluación final; el cierre conserva el resultado. | HU-08 | Art. 339 |
| RF-10 | Guardar un historial inalterable de los cambios de estado de cada práctica. | HU-09 | Art. 340 |
| RF-11 | Permitir a cada actor solo las acciones que le asigna la matriz de permisos siguiente (rol × acción) y rechazar cualquier otra. | Todas | Art. 335–337 |
| RF-12 | Permitir configurar por carrera las horas requeridas de cada modalidad, los plazos de reporte y de revisión, y el umbral de rezago. | HU-04, HU-06 | Art. 334 |
| RF-13 | Permitir al coordinador suspender, reanudar y cancelar una práctica, exigiendo un motivo para suspender y para cancelar. | HU-09 | — |
| RF-14 | Registrar el tipo de cada práctica (`laboral` o `comunitaria`), el subtipo de la laboral (práctica, pasantía, ayudantía de docencia o ayudantía de investigación) y, en la comunitaria, su proyecto de vinculación obligatorio. | HU-02, HU-08 | Art. 332, 338, 341, 347 |
| RF-15 | Rechazar los reportes de ayudantías que superen 10 horas semanales, indicando el límite del Art. 341. | HU-02 | Art. 341 |
| RF-16 | Permitir al estudiante presentar su informe final de actividades y al tutor académico revisarlo o devolverlo con observación. | HU-10 | Art. 336 |
| RF-17 | Permitir al tutor académico registrar la evaluación final en porcentaje; asignar «aprobada» desde 70 % y «no aprobada» por debajo. | HU-11 | Art. 339 |
| RF-18 | Permitir al tutor de la entidad reportar un incumplimiento del practicante al tutor académico. | HU-12 | Art. 337 |
| RF-19 | Generar para el coordinador el informe consolidado de cumplimiento de la carrera, con horas y resultado por estudiante y componente. | HU-13 | Art. 335, 340 |

### Matriz de permisos (RF-11)

✔ = permitido sobre las prácticas que le corresponden al actor; — = no permitido (responde 403, RNF-02). En todos los casos, cada actor ve solo los datos de las prácticas que le corresponden (ver Restricciones, Privacidad). El estudiante opera solo sobre su práctica, el tutor académico sobre las prácticas que tutoriza, el tutor de la entidad sobre sus practicantes y el coordinador sobre las prácticas de su carrera.

| Acción | Estudiante | Tutor académico | Tutor de la entidad | Coordinador |
| --- | :---: | :---: | :---: | :---: |
| Registrar el plan de actividades | ✔ | — | — | — |
| Registrar el reporte semanal | ✔ | — | — | — |
| Validar o devolver (plan, reporte, informe final del estudiante) | — | ✔ | — | — |
| Confirmar el reporte semanal | — | — | ✔ | — |
| Presentar el informe final del estudiante | ✔ | — | — | — |
| Registrar el informe externo | — | — | ✔ | — |
| Reportar un incumplimiento | — | — | ✔ | — |
| Registrar la evaluación final | — | ✔ | — | — |
| Cerrar la práctica | — | — | — | ✔ |
| Suspender, reanudar o cancelar la práctica | — | — | — | ✔ |
| Generar el consolidado | — | — | — | ✔ |
| Configurar la carrera | — | — | — | ✔ |
| Ver el historial de la práctica | — | — | — | ✔ |

> El informe externo de la práctica comunitaria (informe del proyecto de vinculación) aún no tiene un actor que lo registre, porque ese servicio no tiene tutor de entidad (Art. 337). Queda por definir en la fase *plan*.

### Estados de la práctica

```text
asignada ──► en curso ──► en revisión final ──► cerrada (aprobada | no aprobada)
                ▲ │
                │ ▼
             suspendida ──► cancelada
```

| Estado | Significado | Pasa a |
| --- | --- | --- |
| `asignada` | La práctica existe, pero el estudiante aún no tiene plan aprobado. | `en curso` |
| `en curso` | Plan aprobado; el estudiante reporta actividades semanales. | `en revisión final`, `suspendida` |
| `en revisión final` | Horas cumplidas; se esperan el informe final del estudiante, el informe externo y la evaluación. | `cerrada`, `en curso` |
| `cerrada` | Práctica terminada con resultado `aprobada` o `no aprobada`; no admite cambios. | — |
| `suspendida` | Práctica detenida por el coordinador, con motivo; conserva las horas validadas. | `en curso`, `cancelada` |
| `cancelada` | Práctica abandonada; el coordinador registra el motivo. No admite cambios. | — |

> Solo el coordinador suspende, reanuda o cancela una práctica (ver Clarifications).

### Conceptos clave

| Concepto | Definición |
| --- | --- |
| Práctica | Relación entre un estudiante, una entidad receptora y un tutor académico durante un período, de un tipo (`laboral` o `comunitaria`) y con horas requeridas copiadas de la configuración de su carrera al asignarla. Las prácticas laboral y comunitaria de un estudiante son prácticas separadas. |
| Subtipo laboral | Forma de cumplir la práctica laboral: práctica, pasantía, ayudantía de docencia o ayudantía de investigación (Art. 332, 341). |
| Proyecto de vinculación | Proyecto aprobado dentro del cual se realiza toda práctica comunitaria (Art. 338, 347). |
| Configuración de carrera | Horas requeridas por modalidad, plazos de reporte y de revisión, y umbral de rezago de una carrera. |
| Plan de actividades | Lo que el estudiante se compromete a hacer. |
| Reporte semanal | Actividades realizadas en una semana, con horas y evidencias. |
| Evidencia | Respaldo de una actividad, con autor, fecha y estado de revisión. |
| Validación | Decisión del tutor (aprobado o devuelto), con observación, autor y fecha. |
| Alerta | Aviso generado por un atraso, un pendiente o un incumplimiento reportado. |
| Informe final de actividades | Informe del estudiante sobre su práctica, revisado por el tutor académico (Art. 336). |
| Informe externo | Informe final del tutor de la entidad (laboral) o del proyecto de vinculación (comunitaria) (Art. 337, 339). |
| Evaluación final | Desempeño en porcentaje registrado por el tutor académico; define el resultado (Art. 339). |
| Informe consolidado | Resumen por carrera de horas y resultados por estudiante y componente (Art. 335). |
| Historial | Registro de cada cambio de estado de la práctica. |

---

## 8. Requisitos no funcionales

Cada requisito tiene un valor numérico o una comprobación objetiva. Los valores son propuestas del equipo y pueden ajustarse en la fase *plan*.

| ID | Categoría | El sistema debe… | Se verifica con |
| --- | --- | --- | --- |
| RNF-01 | Seguridad | Exigir inicio de sesión en todas las páginas, excepto el inicio de sesión y `/health/`. | Prueba automatizada que solicita cada página sin sesión: todas redirigen al inicio de sesión, salvo las dos excepciones. |
| RNF-02 | Seguridad | Responder 403 a cualquier acción fuera del rol del actor y no modificar ningún dato. | Prueba por cada combinación rol × acción no permitida de la matriz de RF-11: responde 403 y los datos quedan iguales. |
| RNF-03 | Seguridad | Guardar las contraseñas con hash y cerrar la sesión tras 30 minutos de inactividad. | Revisión de la base de datos de prueba (ninguna contraseña legible) y prueba con una sesión inactiva por 31 minutos: pide iniciar sesión de nuevo. |
| RNF-04 | Rendimiento | Cargar el panel del coordinador en menos de 2 s con 150 prácticas activas. | Medición con 150 prácticas de prueba: 10 cargas consecutivas, todas por debajo de 2 s. |
| RNF-05 | Rendimiento | Aceptar evidencias en PDF, JPG y PNG de hasta 10 MB, y rechazar cualquier otro formato o tamaño. | Prueba de carga: un PDF, un JPG y un PNG de 10 MB se aceptan; un archivo de 10,1 MB y uno de otro formato se rechazan con mensaje. |
| RNF-06 | Disponibilidad | Estar disponible el 99 % del tiempo durante el período académico y respaldar los datos cada día. | Registro de disponibilidad del período (consulta periódica de `/health/`) igual o superior a 99 %, y restauración exitosa de la última copia diaria. |
| RNF-07 | Usabilidad | Permitir que un estudiante nuevo registre su primer reporte semanal sin ayuda en menos de 5 minutos. | Prueba cronometrada con estudiantes que no conocen el sistema: todos lo logran sin asistencia en menos de 5 minutos. |
| RNF-08 | Accesibilidad | Cumplir WCAG 2.1 nivel AA en contraste, uso con teclado y etiquetas de formulario. | Auditoría con herramienta automática sin errores de nivel A o AA, y recorrido de los flujos principales solo con teclado. |
| RNF-09 | Mantenibilidad | Cubrir con pruebas al menos el 80 % de las reglas de negocio y pasar el linter sin errores. | Informe de cobertura de las reglas de negocio igual o superior a 80 % y ejecución del linter con cero errores. |
| RNF-10 | Interoperabilidad | Exportar el informe consolidado a CSV en UTF-8 con fechas en formato ISO 8601. | Exportación de un consolidado de prueba: el archivo es UTF-8, las tildes se leen bien y todas las fechas tienen la forma AAAA-MM-DD. |
| RNF-11 | Interoperabilidad | Identificar a las personas y carreras con los identificadores de la institución (cédula y código de carrera), de modo que una integración futura con el sistema académico no exija migrar datos. | Carga de datos de prueba con cédulas y códigos de carrera institucionales, sin transformarlos ni crear identificadores propios. |

> RNF-11 nace de la observación de Ivett Zaragocín: el sistema es un módulo del sistema académico de la UNL (ver Restricciones y Clarifications).

---

## 9. Revisión de calidad de los requisitos

Cada requisito funcional de la v0.2.0 se evaluó con cinco criterios: **claro** (se entiende de una sola manera), **específico** (dice qué, quién y con qué datos), **pertinente** (responde al problema o a la norma), **verificable** (se puede comprobar con una prueba) y **consistente con el alcance** (no contradice lo que está dentro o fuera del MVP). La columna Corrección remite al registro de correcciones que sigue.

| RF | Claro | Específico | Pertinente | Verificable | Consistente con el alcance | Corrección |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| RF-01 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-02 | ✔ | ✘ | ✔ | ✘ | ✔ | COR-06 |
| RF-03 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-04 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-05 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-06 | ✔ | ✘ | ✔ | ✘ | ✔ | COR-05 |
| RF-07 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-08 | ✔ | ✔ | ✔ | ✔ | ✔ | COR-03 (v0.2.0) |
| RF-09 | ✔ | ✔ | ✔ | ✔ | ✔ | COR-02 (v0.2.0) |
| RF-10 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-11 | ✘ | ✘ | ✔ | ✘ | ✔ | COR-04 |
| RF-12 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-13 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-14 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-15 | ✔ | ✔ | ✘ | ✔ | ✔ | COR-08 |
| RF-16 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-17 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-18 | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| RF-19 | ✔ | ✔ | ✔ | ✔ | ✔ | — |

> RF-08 y RF-09 ya se corrigieron en la v0.2.0 al incorporar el reglamento; por eso figuran sin ✘ y se registran abajo. RF-15 fallaba en pertinencia: marcar un reporte que supera el máximo del Art. 341 deja pasar horas que el reglamento no permite.

### Registro de correcciones

| ID | Antes | Después | Motivo | Origen |
| --- | --- | --- | --- | --- |
| COR-01 | Los actores se describían en una frase, sin el nombre que les da el reglamento. | Tabla de actores con nombre en el reglamento, rol en el proceso y necesidad concreta; el tutor de la entidad se limita a la práctica laboral (Art. 335–337). | Cada actor debía quedar definido y alineado con el reglamento. | O1 (Alejandro y Jaime), O2 (Melissa) |
| COR-02 | RF-09: «Permitir el cierre solo si la práctica cumple horas e informe final.» | RF-09: cierre solo con el 100 % de las horas validadas, informe final del estudiante revisado, informe externo y evaluación final; el cierre conserva el resultado. | El Art. 339 exige el 100 % de las horas, los informes y al menos 70 % en la evaluación. | O2 (reglamento, Melissa) |
| COR-03 | RF-08 sin norma; HU-07 se aplicaba a cualquier práctica. | RF-08 con Art. 337 y limitado a la práctica laboral; HU-07 solo para práctica laboral, y el servicio comunitario funciona sin tutor de entidad. | El tutor de la entidad existe solo en la práctica laboral. | O2 (reglamento, Melissa) |
| COR-04 | RF-11: «Restringir lo que cada actor puede ver y hacer según su rol.» | RF-11: matriz rol × acción con 4 actores y 13 acciones. | La frase no decía qué actor hace qué y no se podía probar. | Revisión de calidad |
| COR-05 | RF-06: «Mostrar al coordinador el estado de todas las prácticas de su carrera.» | RF-06: por práctica muestra estudiante, tipo, estado, horas validadas, horas en revisión, horas requeridas, alertas activas y tutor académico. | «Estado» no decía qué datos mostrar, así que no había forma de comprobarlo. | Revisión de calidad |
| COR-06 | RF-02: adjuntar evidencias, sin formato ni tamaño. | RF-02: evidencias en los formatos y el tamaño máximo de RNF-05. | Sin formatos ni tamaño no se podía comprobar qué archivos se aceptan. | Revisión de calidad |
| COR-07 | Caso límite: «El reporte se identifica para revisión» cuando hay «más horas de lo razonable». | Más de 40 h semanales en práctica laboral o comunitaria se identifica para revisión; en ayudantías, más de 10 h se rechaza. | «Razonable» no se podía medir; hacía falta un número. | Revisión de calidad, O3 (Doménica) |
| COR-08 | RF-15: el sistema solo señalaba para revisión los reportes de ayudantías de más de 10 horas semanales. | RF-15: «Rechazar los reportes de ayudantías que superen 10 horas semanales, indicando el límite del Art. 341.» HU-02 (criterio 3) y el caso límite siguen el mismo criterio. | 10 h es un máximo del reglamento, no una sospecha: aceptar el reporte dejaba pasar horas no permitidas. | O3 (tope de 10 h, Doménica) |
| COR-09 | Sin requisito de interoperabilidad; el sistema académico solo aparecía como fuera del alcance. | RNF-11 (identificadores institucionales) y restricción «Integración institucional». | El sistema se concibe como un módulo del sistema académico de la UNL. | O4 (módulo del sistema académico, Ivett) |

---

## 10. Casos de uso

Tres flujos representativos del sistema. Cada uno remite a los requisitos que lo sustentan.

### CU-01 · Validar un reporte semanal

| Elemento | Descripción |
| --- | --- |
| **Actor principal** | Tutor académico |
| **Precondiciones** | El tutor tiene sesión iniciada. La práctica está `en curso` y es de uno de sus estudiantes. El estudiante envió un reporte semanal que está «en revisión». |
| **Flujo principal** | 1. El tutor abre la lista de reportes pendientes de revisión.<br>2. Selecciona un reporte.<br>3. El sistema muestra las actividades, las horas y las evidencias.<br>4. El tutor revisa el contenido y elige «validar».<br>5. El sistema registra quién validó y en qué fecha.<br>6. El sistema suma las horas del reporte al acumulado de horas validadas.<br>7. El sistema muestra el acumulado actualizado frente a las horas requeridas. |
| **Flujos alternativos** | **4a. Devolver.** El tutor elige «devolver» y escribe una observación; el sistema devuelve el reporte al estudiante con la observación. Si no escribe observación, el sistema rechaza la devolución.<br>**2a. Reporte ajeno.** Si el reporte pertenece a un estudiante de otro tutor, el sistema responde 403 y no cambia nada.<br>**2b. Práctica no activa.** Si la práctica está suspendida, cancelada o cerrada, el sistema no permite validar. |
| **Postcondiciones** | Validado: las horas cuentan para el acumulado y el reporte guarda autor y fecha de la validación. Devuelto: las horas no cuentan y el estudiante ve la observación. |
| **Requisitos relacionados** | RF-03, RF-04, RF-05, RF-11; HU-03, HU-04; RNF-02 |

### CU-02 · Cerrar la práctica

| Elemento | Descripción |
| --- | --- |
| **Actor principal** | Coordinador de prácticas |
| **Precondiciones** | El coordinador tiene sesión iniciada. La práctica es de su carrera y está `en revisión final`. |
| **Flujo principal** | 1. El coordinador abre la práctica.<br>2. El sistema muestra el estado de los requisitos de cierre: horas validadas, informe final del estudiante, informe externo y evaluación final.<br>3. El coordinador solicita el cierre.<br>4. El sistema verifica que tiene el 100 % de las horas requeridas validadas, el informe final del estudiante revisado, el informe externo registrado y la evaluación final.<br>5. El sistema pasa la práctica a `cerrada` con el resultado de la evaluación («aprobada» desde 70 %).<br>6. El sistema registra el cambio de estado en el historial, con autor y fecha.<br>7. La práctica ya no admite cambios. |
| **Flujos alternativos** | **4a. Falta algún requisito.** El sistema rechaza el cierre e indica qué falta; la práctica sigue `en revisión final`.<br>**5a. Evaluación menor a 70 %.** El sistema cierra la práctica como «no aprobada»; el estudiante debe cumplir una práctica nueva y las horas no se trasladan (Art. 339).<br>**1a. Otro rol.** Si quien intenta cerrar no es el coordinador de la carrera, el sistema responde 403.<br>**1b. Práctica ya cerrada.** El sistema rechaza la acción porque la práctica no admite cambios. |
| **Postcondiciones** | La práctica queda `cerrada` con su resultado, y el historial conserva quién la cerró y cuándo. Si falló una verificación, nada cambia. |
| **Requisitos relacionados** | RF-09, RF-10, RF-11, RF-16, RF-17; HU-08, HU-09; RNF-02 |

### CU-03 · Generar alertas de rezago

| Elemento | Descripción |
| --- | --- |
| **Actor principal** | Sistema (verificación periódica). Destinatarios: estudiante, tutor académico y coordinador. |
| **Precondiciones** | Existen prácticas `en curso`. La carrera tiene configurados los plazos de reporte y de revisión y el umbral de rezago (80 % por defecto). |
| **Flujo principal** | 1. El sistema revisa, al menos una vez al día, cada práctica `en curso`.<br>2. Calcula las horas esperadas a la fecha: horas requeridas × (días transcurridos ÷ días del período).<br>3. Suma las horas validadas y las horas en revisión.<br>4. Si la suma queda por debajo del umbral de rezago aplicado a las horas esperadas, genera una alerta de atraso.<br>5. Notifica al estudiante, a su tutor académico y al coordinador.<br>6. La alerta queda visible en el estado general de las prácticas del coordinador. |
| **Flujos alternativos** | **4a. Sin rezago.** Si la suma alcanza el umbral, no se genera alerta.<br>**4b. Alerta ya activa.** Si ya existe una alerta activa por la misma causa, no se genera otra.<br>**1a. Práctica no activa.** Las prácticas suspendidas, canceladas o cerradas no se evalúan.<br>**1b. Otras causas.** Con el mismo mecanismo se alerta un reporte no enviado dentro del plazo de reporte (al estudiante, al tutor y al coordinador) y un reporte sin revisar más allá del plazo de revisión (al tutor académico). |
| **Postcondiciones** | Cada práctica rezagada tiene una alerta activa visible para sus destinatarios, antes de la fecha de fin del período. |
| **Requisitos relacionados** | RF-07, RF-06, RF-12; HU-06, HU-05; CE-04 |

---

## 11. Criterios de éxito

| ID | Criterio | Cómo se verifica |
| --- | --- | --- |
| CE-01 | El coordinador consulta el estado de todas las prácticas de su carrera **sin pedir archivos por correo**. | Prueba con el coordinador: obtiene el estado de cada práctica sin solicitar nada a terceros. |
| CE-02 | El **100 %** de las evidencias validadas queda con **fecha y nombre de quien la validó**. | Revisión de todas las evidencias validadas: ninguna sin autor o fecha. |
| CE-03 | Un estudiante conoce sus horas validadas y faltantes **en menos de 1 minuto**. | Prueba cronometrada con estudiantes. |
| CE-04 | Toda práctica atrasada genera una alerta **antes** de la fecha de fin del período. | Caso de prueba con una práctica rezagada. |
| CE-05 | **Ninguna** práctica se cierra sin el 100 % de las horas, sin los informes o sin evaluación; **ninguna** queda «aprobada» con menos de 70 %. | Intentos de cierre de prácticas incompletas y evaluación de 69 % y 70 %. |
| CE-06 | Para cualquier práctica se reconstruye el historial completo: quién, qué y cuándo. | Consulta del historial de una práctica cerrada. |
| CE-07 | El coordinador obtiene el consolidado de su carrera **sin armarlo a mano**. | Prueba con el coordinador sobre un período con prácticas cerradas. |

---

## Clarifications

### Session 2026-10-11

- Q: ¿El tutor de la entidad receptora usa el sistema directamente? → A: Sí, con cuenta propia y un rol limitado: solo ve a sus practicantes, confirma sus reportes semanales y registra el informe final.
- Q: ¿Cada cuánto se reporta y con qué plazos? → A: Reporte semanal; los plazos de reporte y de revisión se configuran por carrera (por defecto 3 días tras cerrar la semana y 5 días hábiles).
- Q: ¿Quién suspende una práctica y puede retomarse? → A: Solo el coordinador, con motivo obligatorio; puede reanudarla a `en curso` conservando las horas validadas o pasarla a `cancelada` (final, con motivo).
- Q: ¿Cómo se relacionan las prácticas laboral y comunitaria? → A: Son prácticas separadas, cada una con su tipo, tutor, plan y cierre; las horas requeridas se copian de la configuración de carrera y modalidad al asignarla.
- Q: ¿Cuándo se considera atrasada una práctica? → A: Cuando las horas validadas más las en revisión quedan por debajo del umbral de rezago (80 % por defecto, configurable por carrera) de las horas esperadas linealmente a la fecha.

### Session 2026-10-18 (Reglamento de Régimen Académico UNL)

- Q: ¿Qué hace falta para aprobar una práctica? → A: El 100 % de las horas programadas y al menos 70 % en la evaluación del tutor académico; si no se cumple, se repite la práctica (Art. 339).
- Q: ¿Qué informe usa la evaluación en el servicio comunitario, que no tiene tutor de entidad? → A: El informe del proyecto de vinculación; en la práctica laboral, el informe del tutor de la entidad (Art. 337, 339).
- Q: ¿El estudiante entrega un informe propio? → A: Sí, un informe final de actividades que revisa el tutor académico (Art. 336).
- Q: ¿Las pasantías y ayudantías son prácticas distintas? → A: No; son subtipos de la práctica laboral. Las ayudantías tienen una dedicación máxima de 10 h semanales (Art. 332, 341).
- Q: ¿Se acreditan horas parciales? → A: No; no se reconocen fracciones de horas inferiores a las requeridas (Art. 339, 343).

### Session 2026-10-18 (semana 2)

- Q: ¿El sistema marca o rechaza un reporte de ayudantía de más de 10 h semanales? → A: Lo rechaza al registrarlo e indica el límite del Art. 341. Es un máximo del reglamento, no una sospecha, así que no queda nada para que el tutor decida; uno de exactamente 10 h se acepta. En práctica laboral o comunitaria, donde el reglamento no fija un tope semanal, más de 40 h solo se identifica para revisión.
- Q: ¿Cómo se relaciona el sistema con el sistema académico de la UNL? → A: Se concibe como un módulo de ese sistema. Durante el prototipado su diseño (navegación, terminología y datos de estudiantes) se contrasta con él, y el sistema usa los identificadores institucionales (cédula y código de carrera, RNF-11). La integración técnica con SIAAF sigue fuera del alcance.
