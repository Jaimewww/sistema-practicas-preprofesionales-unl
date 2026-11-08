# Modelado BPMN

Modelo del proceso principal del incremento: el **reporte semanal de actividades** de una práctica preprofesional (HU-02, HU-03, HU-04, HU-06, HU-07; RF-02 a RF-05, RF-07, RF-08).

| Archivo | Contenido |
| --- | --- |
| [`analisis-proceso-reporte-semanal.md`](analisis-proceso-reporte-semanal.md) | Análisis textual previo al diagrama (participantes, eventos, actividades, decisiones, flujos, datos y excepciones) y tabla de trazabilidad actividad → RF/HU → endpoint. |
| [`proceso-reporte-semanal.bpmn`](proceso-reporte-semanal.bpmn) | Diagrama BPMN 2.0.2 con su disposición gráfica completa. |

## Cómo abrir el diagrama

1. Entrar en <https://demo.bpmn.io/> y arrastrar `proceso-reporte-semanal.bpmn` sobre el lienzo (o usar *Open*).
2. Alternativa local: Camunda Modeler → *File → Open File*.
3. Para validar el XML sin abrir un editor: `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" docs/bpmn/proceso-reporte-semanal.bpmn`.

El diagrama es grande (unos 3400 × 2300 px). En bpmn.io, usar *zoom to fit* (`Ctrl+0`) para verlo completo y la rueda con `Ctrl` para acercarse a un carril.

## Vista

**Operativa.** Muestra quién hace qué, en qué orden y qué mensajes se cruzan entre participantes; no modela clases ni tablas. Los detalles de reglas están como documentación de cada elemento (panel de propiedades en bpmn.io) y en el análisis.

Los pools, de arriba abajo: **Estudiante**, **Sistema de seguimiento de prácticas** (lanes *Gestión de reportes* y *Control de atrasos*), **Tutor de la entidad receptora**, **Tutor académico** y **Coordinador de prácticas** (colapsado).

## Leyenda de elementos

| Elemento | Símbolo | Uso en el modelo |
| --- | --- | --- |
| Inicio con temporizador | Círculo con reloj | Cierre semanal (`R/P1W`) y verificación diaria (`R/P1D`). |
| Inicio por mensaje | Círculo con sobre | Recepción de un reporte, una confirmación o una alerta. |
| Evento intermedio de mensaje | Doble círculo con sobre | Respuesta que espera el estudiante. |
| Temporizador de frontera (no interruptor) | Doble círculo punteado con reloj sobre una tarea | Plazo de revisión de 5 días hábiles. |
| Fin | Círculo grueso | Resultado del flujo. |
| Fin con error | Círculo grueso con rayo | Reporte rechazado. |
| Tarea de usuario | Rectángulo con figura | Acción de una persona. |
| Tarea de servicio | Rectángulo con engranajes | Acción automática del sistema. |
| Tarea de envío / recepción | Rectángulo con sobre relleno / vacío | Notificar un mensaje / esperar un mensaje. |
| Gateway exclusivo | Rombo con X | Decisión de un solo camino; la pregunta va como nombre y las ramas como «Sí» / «No». |
| Gateway basado en eventos | Rombo con pentágono | El estudiante sigue la primera respuesta que llegue. |
| Flujo de secuencia | Flecha continua | Orden dentro de un pool. |
| Flujo de mensaje | Flecha punteada | Comunicación entre pools. |
| Objeto de datos | Hoja | Reporte semanal, observación. |
| Almacén de datos | Cilindro | Registro de prácticas, reportes y horas. |
| Anotación | Corchete con texto | Reglas de negocio que aclaran una actividad. |

## Convenciones

- Toda tarea se nombra con **verbo en infinitivo + complemento** («Registrar reporte semanal», «Validar horas reportadas»).
- Cada actividad se relaciona con un RF/HU y con un endpoint o pantalla en la tabla de trazabilidad del análisis (§8). Lo no implementado se marca **pendiente**.
- Los textos del diagrama están en español, igual que el resto de la documentación.
