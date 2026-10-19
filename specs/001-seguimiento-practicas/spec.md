# Especificación funcional: Seguimiento de prácticas preprofesionales

| Campo | Valor |
| --- | --- |
| **Rama** | `001-seguimiento-practicas` (ramas `feature/spec` y `feature/clarify` integradas en `develop`) |
| **Fase SDD** | specify y clarify (completadas; actualizada con el reglamento el 2026-10-18) |
| **Estado** | Vigente para planificación (v0.2.0) |
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
8. [Criterios de éxito](#8-criterios-de-éxito)
9. [Clarifications](#clarifications)

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
| 3 | una práctica de subtipo ayudantía | el estudiante reporta más de 10 horas en una semana | el reporte se marca para revisión por superar la dedicación máxima (Art. 341) |

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
| El estudiante reporta más horas de lo razonable en una semana | El reporte se identifica para revisión; en ayudantías, el límite es 10 h semanales (Art. 341). |
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

---

## 7. Requisitos funcionales

| ID | El sistema debe… | Historia | Norma |
| --- | --- | :---: | :---: |
| RF-01 | Permitir al estudiante registrar su plan de actividades y enviarlo a revisión. | HU-01 | Art. 336 |
| RF-02 | Permitir al estudiante registrar actividades semanales con horas y adjuntar evidencias. | HU-02 | Art. 11 |
| RF-03 | Permitir al tutor académico validar o devolver planes y reportes; la devolución exige observación. | HU-01, HU-03 | Art. 336 |
| RF-04 | Registrar en cada validación quién la realizó y en qué fecha. | HU-03 | — |
| RF-05 | Calcular las horas validadas de cada práctica y compararlas con las requeridas. | HU-04 | Art. 334, 339 |
| RF-06 | Mostrar al coordinador el estado de todas las prácticas de su carrera. | HU-05 | Art. 331, 335 |
| RF-07 | Generar alertas por reportes no enviados, revisiones pendientes, horas rezagadas e incumplimientos reportados, según los plazos y el umbral de rezago de la carrera. | HU-06, HU-12 | Art. 336 |
| RF-08 | Permitir al tutor de la entidad receptora, con cuenta propia, confirmar los reportes semanales de sus practicantes y registrar su informe final. | HU-07 | Art. 337 |
| RF-09 | Permitir el cierre solo si la práctica tiene el 100 % de las horas requeridas validadas, el informe final del estudiante revisado, el informe externo registrado y la evaluación final; el cierre conserva el resultado. | HU-08 | Art. 339 |
| RF-10 | Guardar un historial inalterable de los cambios de estado de cada práctica. | HU-09 | Art. 340 |
| RF-11 | Restringir lo que cada actor puede ver y hacer según su rol. | Todas | Art. 335–337 |
| RF-12 | Permitir configurar por carrera las horas requeridas de cada modalidad, los plazos de reporte y de revisión, y el umbral de rezago. | HU-04, HU-06 | Art. 334 |
| RF-13 | Permitir al coordinador suspender, reanudar y cancelar una práctica, exigiendo un motivo para suspender y para cancelar. | HU-09 | — |
| RF-14 | Registrar el tipo de cada práctica (`laboral` o `comunitaria`), el subtipo de la laboral (práctica, pasantía, ayudantía de docencia o ayudantía de investigación) y, en la comunitaria, su proyecto de vinculación obligatorio. | HU-02, HU-08 | Art. 332, 338, 341, 347 |
| RF-15 | Marcar para revisión los reportes de ayudantías que superen 10 horas semanales. | HU-02 | Art. 341 |
| RF-16 | Permitir al estudiante presentar su informe final de actividades y al tutor académico revisarlo o devolverlo con observación. | HU-10 | Art. 336 |
| RF-17 | Permitir al tutor académico registrar la evaluación final en porcentaje; asignar «aprobada» desde 70 % y «no aprobada» por debajo. | HU-11 | Art. 339 |
| RF-18 | Permitir al tutor de la entidad reportar un incumplimiento del practicante al tutor académico. | HU-12 | Art. 337 |
| RF-19 | Generar para el coordinador el informe consolidado de cumplimiento de la carrera, con horas y resultado por estudiante y componente. | HU-13 | Art. 335, 340 |

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

## 8. Criterios de éxito

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
