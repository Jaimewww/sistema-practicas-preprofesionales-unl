# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Cuatro roles trabajan sobre una práctica preprofesional que ya llega asignada ([spec, sección 2](specs/001-seguimiento-practicas/spec.md)):

| Rol | Situación | Trabajo que hace en el sistema |
| --- | --- | --- |
| Estudiante | Desarrolla su práctica laboral o comunitaria durante el período. | Registra su plan de actividades, reporta cada semana sus actividades con horas y evidencias, presenta su informe final y consulta cuántas horas lleva y cuántas le faltan. |
| Tutor académico | Docente de la UNL (Art. 336). | Aprueba el plan, valida o devuelve con observaciones los reportes semanales, revisa el informe final y registra la evaluación. |
| Tutor de la entidad receptora | Persona externa a la UNL, nombrada por la entidad de una práctica laboral (Art. 337). No existe en el servicio comunitario. | Confirma los reportes de sus practicantes, reporta incumplimientos y registra su informe final. |
| Coordinador de prácticas | Docente responsable de prácticas de la carrera (Art. 335). | Consulta el estado de todas las prácticas de su carrera, recibe alertas de atraso, suspende o cierra prácticas y obtiene el informe consolidado. |

El director de carrera recibe el consolidado, pero no usa el sistema en este alcance.

## Product Purpose

Dar seguimiento y trazabilidad a una práctica ya asignada, desde su inicio hasta su cierre. El valor no está en almacenar formularios, sino en responder en todo momento en qué estado está cada práctica, cuántas horas validadas lleva frente a las requeridas y quién validó cada paso.

El éxito se mide con los criterios del spec (sección 11): el coordinador conoce el estado de cada práctica sin pedir archivos por correo, el estudiante sabe sus horas faltantes en menos de 1 minuto, toda práctica atrasada genera una alerta antes del fin del período y ninguna práctica se cierra sin el 100 % de las horas y al menos 70 % en la evaluación (Art. 339).

## Positioning

Es un módulo del sistema académico de la UNL (SIAAF), no un producto aparte. Vive como una sección del módulo académico, junto a «Tutorías», y aplica las reglas del Reglamento de Régimen Académico de la UNL (horas por carrera y modalidad, tope de 10 h semanales en ayudantías, acreditación con el 100 % de las horas).

## Operating Context

- Todos los roles trabajan desde una computadora de escritorio, como en el resto del SIAAF. En el celular el sistema debe funcionar, pero no es el caso principal.
- El tutor de la entidad receptora entra con una cuenta propia y ve el mismo marco del SIAAF, con un menú reducido y solo sus practicantes.
- El reporte es semanal. Los plazos de reporte y de revisión, y el umbral de rezago (80 % por defecto), se configuran por carrera.
- Las evidencias son archivos PDF de hasta 5 MB (RNF-05).
- Las personas y las carreras se identifican con los identificadores institucionales: cédula y código de carrera (RNF-11).

## Capabilities and Constraints

- **Alcance:** plan de actividades, reportes semanales, validación, acumulado de horas, alertas, informe final del estudiante, informe externo, evaluación final, cierre, historial de estados y permisos por rol ([spec, secciones 4 y 7](specs/001-seguimiento-practicas/spec.md)).
- **Stack existente:** Django con plantillas renderizadas en el servidor, sin API ni SPA en el MVP ([plan.md](specs/001-seguimiento-practicas/plan.md)). El prototipo es la base para implementar: sus pantallas se pasan directamente a las plantillas Django del backend, así que se construye con HTML y CSS compatibles con esas plantillas.
- **Terminología:** la del SIAAF y la del reglamento, por ejemplo «Periodo académico» (`MAR.26-AGO.26 GRADO`), «Docente», «Tablero» y «Tutor académico». Ver [docs/referencia-siaaf.md](docs/referencia-siaaf.md).
- **Fuera del alcance:** postulación, convenios, integración técnica con SIAAF, firma electrónica, aplicación móvil nativa y certificado oficial.
- **Decisiones abiertas:**
  - Qué actor registra el informe del proyecto de vinculación en la práctica comunitaria.
  - Si cada práctica tiene un solo tutor académico activo a la vez (S-02).

## Brand Commitments

El sistema debe verse y comportarse como un módulo más del SIAAF: mismo marco (barra lateral, barra superior, pie de página), mismos patrones de lista, detalle y formulario, y misma terminología. La referencia obligatoria es [docs/referencia-siaaf.md](docs/referencia-siaaf.md), con las capturas de `docs/referencias/siaaf/`. GLPI (Servicios de TI) no es referencia visual.

## Evidence on Hand

- Especificación funcional, plan, modelo de datos y tareas en `specs/001-seguimiento-practicas/`.
- Capturas del SIAAF, con los datos personales tapados, en `docs/referencias/siaaf/`.
- Guía de requisitos en `docs/guia-requisitos.md`.
- No hay logos oficiales en el repositorio ni datos reales de prácticas; el prototipo usa datos de ejemplo verosímiles y no inventa nombres de personas reales.

## Product Principles

1. **El estado primero:** cada pantalla responde en qué estado está la práctica y qué falta, antes de mostrar formularios.
2. **Solo cuentan las horas validadas:** el sistema muestra siempre por separado las horas validadas, en revisión y requeridas.
3. **Trazabilidad visible:** cada validación, devolución y cambio de estado muestra quién lo hizo y cuándo.
4. **El reglamento se aplica, no se sugiere:** los límites del reglamento rechazan la acción y citan el artículo; las sospechas se marcan para revisión.
5. **Integrado al SIAAF:** un usuario del SIAAF no debe notar que cambió de sistema.

## Accessibility & Inclusion

WCAG 2.1 nivel AA en contraste, uso con teclado y etiquetas de formulario (RNF-08). Un estudiante nuevo debe registrar su primer reporte semanal sin ayuda en menos de 5 minutos (RNF-07).
