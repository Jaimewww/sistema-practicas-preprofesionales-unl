# Especificación funcional: Seguimiento de prácticas preprofesionales

**Rama:** `feature/spec`
**Fase SDD:** specify
**Autora:** Ivett
**Estado:** Borrador para revisión
**Entrada:** Ficha 7 del banco de proyectos, guía interna del equipo y contexto del caso UNL (`README.md`).

> Este documento describe **qué** problema se resuelve y **para quién**. No menciona tecnologías, herramientas ni diseño de interfaz; esas decisiones pertenecen a la fase *plan*.

---

## 1. Problema

En la universidad, las prácticas preprofesionales son obligatorias para titularse. Hoy su seguimiento se hace con formularios, correos, mensajes y archivos sueltos que cada carrera maneja a su manera. Como resultado:

- El coordinador de prácticas **no sabe en qué estado está cada práctica** sin pedir información a cada estudiante o tutor.
- Las horas cumplidas se suman a mano y **el atraso se descubre tarde**, cuando ya no hay tiempo de corregirlo.
- Las evidencias (actividades, asistencia, informes) **no quedan ligadas a quién las revisó ni cuándo**, así que no hay trazabilidad.
- Cerrar una práctica exige reunir documentos dispersos y confirmar uno por uno que estén completos.

**Problema delimitado:** no existe una forma única y confiable de dar seguimiento a una práctica ya asignada, desde su inicio hasta su cierre, que muestre el avance de horas, el estado de las evidencias y quién validó cada paso.

El valor del sistema **no está en almacenar formularios**, sino en el **seguimiento y la trazabilidad** del proceso.

## 2. Actores y necesidades

| Actor | Rol en el proceso | Necesidad concreta |
| --- | --- | --- |
| Estudiante | Desarrolla la práctica, planifica sus actividades y reporta su avance. | Saber cuántas horas lleva, cuántas le faltan y qué actividades o evidencias tiene pendientes o devueltas. |
| Tutor académico | Docente que orienta, revisa y valida el trabajo del estudiante. | Revisar las actividades semanales de sus estudiantes y aprobarlas o devolverlas con observaciones, sin perseguir documentos. |
| Tutor de la entidad receptora | Persona de la institución o empresa donde el estudiante hace la práctica. | Confirmar que las actividades reportadas ocurrieron y dejar su informe final registrado sin trámites adicionales. |
| Coordinador de prácticas | Docente responsable de las prácticas de la carrera. | Consultar el estado de todas las prácticas de la carrera en un solo lugar y enterarse a tiempo de las que van atrasadas. |

**Actor secundario:** el director de carrera consulta el resultado del cierre para continuar con la acreditación, que queda fuera de este alcance.

## 3. Historias de usuario

### HU-01 · Registrar el plan de actividades (Prioridad: P1)

**Como** estudiante, **quiero** registrar mi plan de actividades al inicio de la práctica **para** que mi tutor académico sepa qué voy a hacer y pueda aprobarlo.

**Criterios de aceptación:**

1. **Dado** un estudiante con una práctica asignada, **cuando** registra su plan de actividades, **entonces** el plan queda en estado «en revisión» y su tutor académico ve que tiene un plan pendiente.
2. **Dado** un plan en revisión, **cuando** el tutor académico lo devuelve con observaciones, **entonces** el estudiante ve las observaciones y puede corregirlo.

### HU-02 · Reportar actividades semanales (Prioridad: P1)

**Como** estudiante, **quiero** reportar cada semana las actividades realizadas con sus horas y evidencias **para** que mi avance quede registrado y se sumen mis horas.

**Criterios de aceptación:**

1. **Dado** un plan aprobado, **cuando** el estudiante reporta la semana con sus horas y evidencias, **entonces** el reporte queda con fecha de registro y en estado «en revisión».
2. **Dado** un reporte semanal, **cuando** todavía no ha sido validado, **entonces** sus horas no se cuentan como cumplidas.

### HU-03 · Validar actividades semanales (Prioridad: P1)

**Como** tutor académico, **quiero** validar o devolver las actividades semanales de mis estudiantes **para** que solo cuenten las horas que realmente se revisaron.

**Criterios de aceptación:**

1. **Dado** un reporte en revisión, **cuando** el tutor académico lo valida, **entonces** las horas se suman al acumulado del estudiante y queda registrado quién validó y cuándo.
2. **Dado** un reporte en revisión, **cuando** el tutor lo devuelve, **entonces** debe escribir una observación y el reporte vuelve al estudiante.

### HU-04 · Consultar las horas acumuladas (Prioridad: P1)

**Como** estudiante, **quiero** ver mis horas validadas frente a las horas requeridas **para** saber cuánto me falta y si voy a tiempo.

**Criterios de aceptación:**

1. **Dado** un estudiante con reportes validados, **cuando** consulta su avance, **entonces** ve horas validadas, horas pendientes de validación y horas requeridas.

### HU-05 · Conocer el estado de todas las prácticas (Prioridad: P1)

**Como** coordinador de prácticas, **quiero** consultar el estado de todas las prácticas de mi carrera **para** saber cuáles avanzan bien y cuáles requieren intervención, sin pedir archivos por correo.

**Criterios de aceptación:**

1. **Dado** un conjunto de prácticas en curso, **cuando** el coordinador consulta el estado general, **entonces** ve por cada práctica su estado, las horas acumuladas y si tiene pendientes o atrasos.

### HU-06 · Recibir alertas de atraso (Prioridad: P2)

**Como** coordinador de prácticas, **quiero** recibir una alerta cuando una práctica se atrasa **para** intervenir antes de que el estudiante incumpla.

**Criterios de aceptación:**

1. **Dado** un estudiante que no reporta actividades en el plazo acordado, **cuando** se cumple ese plazo, **entonces** el estudiante, su tutor académico y el coordinador reciben una alerta.
2. **Dado** un reporte que lleva más tiempo del acordado sin ser revisado, **cuando** se cumple ese plazo, **entonces** el tutor académico recibe una alerta.
3. **Dado** un estudiante cuyas horas validadas están por debajo de lo esperado para la fecha, **cuando** se detecta el rezago, **entonces** se genera una alerta de atraso.

### HU-07 · Confirmar actividades e informar desde la entidad receptora (Prioridad: P2)

**Como** tutor de la entidad receptora, **quiero** confirmar las actividades del estudiante y registrar mi informe final **para** que mi evaluación forme parte del cierre de la práctica.

**Criterios de aceptación:**

1. **Dado** un estudiante que terminó sus actividades, **cuando** el tutor de la entidad registra su informe final, **entonces** el informe queda asociado a la práctica con su autor y fecha.

> [NEEDS CLARIFICATION: ¿el tutor de la entidad receptora usa el sistema directamente o su informe lo registra el tutor académico o el coordinador?]

### HU-08 · Cerrar la práctica con informe final (Prioridad: P2)

**Como** coordinador de prácticas, **quiero** cerrar una práctica cuando cumple las horas y tiene sus informes finales **para** dejar constancia de que terminó correctamente.

**Criterios de aceptación:**

1. **Dado** una práctica con horas validadas iguales o mayores a las requeridas y con informe final, **cuando** el coordinador la cierra, **entonces** pasa al estado «cerrada» y ya no admite cambios.
2. **Dado** una práctica sin las horas requeridas o sin informe final, **cuando** se intenta cerrar, **entonces** el cierre se rechaza indicando qué falta.

### HU-09 · Consultar el historial de la práctica (Prioridad: P3)

**Como** coordinador de prácticas, **quiero** ver el historial de cambios de estado de una práctica **para** saber quién hizo qué y cuándo.

**Criterios de aceptación:**

1. **Dado** una práctica con movimientos, **cuando** se consulta su historial, **entonces** cada cambio muestra el estado anterior, el nuevo, quién lo hizo y la fecha.
2. **Dado** un registro del historial, **cuando** alguien intenta modificarlo o borrarlo, **entonces** la acción no se permite.

### Casos límite

- El tutor académico deja de ejercer durante la práctica y hay que asignar otro sin perder lo ya validado.
- El estudiante reporta horas que superan lo razonable para una semana.
- Una evidencia se devuelve varias veces; debe conservarse cada versión y cada observación.
- El estudiante alcanza las horas requeridas antes de la fecha prevista de fin.
- La práctica se suspende o se abandona antes de terminar.

## 4. Alcance

### Dentro del alcance (MVP)

La práctica **ya asignada**, desde su inicio hasta su cierre:

- Plan de actividades del estudiante y su aprobación.
- Registro semanal de actividades con horas.
- Evidencias asociadas a cada reporte.
- Validación o devolución con observaciones por parte del tutor académico.
- Cálculo de horas acumuladas frente a las requeridas.
- Alertas de atraso (reportes no enviados, revisiones pendientes, horas rezagadas).
- Informe final y cierre de la práctica.
- Historial de cambios de estado de la práctica.
- Acceso según el rol: cada actor ve y hace solo lo que le corresponde.

### Fuera del alcance

| Elemento | Motivo |
| --- | --- |
| Postulación y emparejamiento de estudiantes con empresas | La práctica llega ya asignada. |
| Gestión de convenios y cartas de compromiso | Corresponde a otro proyecto del banco (proyecto R). |
| Integración con el sistema académico institucional (SIAAF) | Depende de acuerdos externos fuera del ciclo. |
| Firma electrónica | Requiere validez legal y certificación externa. |
| Aplicación móvil nativa | No es necesaria para resolver el problema de seguimiento. |
| Homologación y convalidación de prácticas | Son flujos paralelos con reglas propias; fase posterior. |
| Encuesta de satisfacción y emisión del certificado oficial | Ocurren después del cierre; fase posterior. |
| Cálculo de notas académicas y gestión financiera | No forman parte del seguimiento de la práctica. |

## 5. Supuestos

- La práctica ya viene asignada: estudiante, entidad receptora, tutor académico, período y horas requeridas se conocen al iniciar.
- Cada práctica tiene exactamente un tutor académico activo a la vez.
- El reporte de actividades es semanal. [NEEDS CLARIFICATION: ¿la frecuencia es semanal para todas las carreras?]
- Solo cuentan como cumplidas las horas validadas por el tutor académico.
- Los usuarios disponen de conexión a internet para registrar y revisar actividades.

## 6. Restricciones

- **Normativa:** el reglamento institucional define las horas mínimas. Como referencia, el estudio del caso UNL cita 240 h laborales y 120 h de servicio comunitario en modalidad presencial, con excepciones por carrera. Por eso las horas requeridas deben poder definirse por carrera y modalidad. [NEEDS CLARIFICATION: ¿cuántas horas exige el reglamento vigente para nuestra carrera?]
- **Servicio comunitario:** no siempre tiene tutor de entidad receptora; el proceso debe funcionar sin él.
- **Tiempo:** el proyecto se desarrolla dentro de un ciclo académico, por lo que el alcance se limita al MVP.
- **Información:** los procesos se basan en un instructivo que estaba en construcción y aún no se han validado con usuarios reales.
- **Privacidad:** los datos y evidencias de un estudiante solo los ven él, sus tutores y el coordinador de su carrera.

## 7. Requisitos funcionales

- **RF-01:** Permitir al estudiante registrar su plan de actividades y enviarlo a revisión.
- **RF-02:** Permitir al estudiante registrar actividades semanales con horas y adjuntar evidencias.
- **RF-03:** Permitir al tutor académico validar o devolver planes y reportes; la devolución exige una observación.
- **RF-04:** Registrar en cada validación quién la realizó y en qué fecha.
- **RF-05:** Calcular las horas validadas de cada práctica y compararlas con las requeridas.
- **RF-06:** Mostrar al coordinador el estado de todas las prácticas de su carrera.
- **RF-07:** Generar alertas por reportes no enviados, revisiones pendientes y horas rezagadas.
- **RF-08:** Permitir registrar el informe final del tutor de la entidad receptora.
- **RF-09:** Permitir el cierre de la práctica solo si cumple horas e informe final.
- **RF-10:** Guardar un historial inalterable de los cambios de estado de cada práctica.
- **RF-11:** Restringir lo que cada actor puede ver y hacer según su rol.

### Estados de la práctica

`asignada` → `en curso` → `en revisión final` → `cerrada`

Una práctica también puede pasar a `suspendida` desde `en curso`. [NEEDS CLARIFICATION: ¿quién autoriza la suspensión y si una práctica suspendida puede retomarse?]

### Conceptos clave

- **Práctica:** relación entre un estudiante, una entidad receptora y un tutor académico durante un período, con horas requeridas.
- **Plan de actividades:** lo que el estudiante se compromete a hacer.
- **Reporte semanal:** actividades realizadas en una semana, con horas y evidencias.
- **Evidencia:** respaldo de una actividad, con su autor, fecha y estado de revisión.
- **Validación:** decisión del tutor (aprobado o devuelto), con observación, autor y fecha.
- **Alerta:** aviso generado por un atraso o un pendiente.
- **Informe final:** valoración de cierre del tutor de la entidad receptora.
- **Historial:** registro de cada cambio de estado de la práctica.

## 8. Criterios de éxito

- **CE-01:** El coordinador consulta el estado de todas las prácticas de su carrera **sin pedir archivos por correo**.
- **CE-02:** El 100 % de las evidencias validadas queda con **fecha y nombre de quien la validó**.
- **CE-03:** Un estudiante conoce sus horas validadas y faltantes **en menos de 1 minuto**, sin preguntar a nadie.
- **CE-04:** Toda práctica atrasada genera una alerta **antes** de llegar a la fecha de fin del período.
- **CE-05:** Ninguna práctica se puede cerrar sin cumplir las horas requeridas y sin informe final.
- **CE-06:** Para cualquier práctica se puede reconstruir el historial completo: quién hizo cada cambio, qué cambió y cuándo.

## Clarifications

<!-- Sección a cargo de Alejandro (fase clarify). -->
