# Prototipo del Coordinador y del Analista DVS — issue #53

Fecha: 2026-10-21. Rama: `feature/prototipo-coordinador`. Dependencias: PR #56 y #57 integrados.

## Alcance y diseño

El prototipo implementa C1–C7 y A1–A2 con las plantillas Django y los patrones SIAAF existentes. Reutiliza `practica_detalle.html` de T4: el contexto del coordinador agrega historial y acciones; el tutor mantiene su menú y sus acciones anteriores. El analista usa el patrón de listado de C6, ampliado a todas las carreras.

Las reglas siguen RF-06 a RF-13, RF-18, RF-19, HU-13, RNF-04 y RNF-10. La tabla de transiciones de `data-model.md` limita la cancelación a prácticas suspendidas. Una práctica suspendida conserva las horas y solo ofrece reanudar o cancelar; cerrada y cancelada son terminales. La revisión final conserva el resultado de la evaluación: menos de 70 % permite cerrar como «no aprobada», siempre que estén completos los demás requisitos.

El informe externo comunitario se representa mediante el informe del proyecto de vinculación. El actor que lo registra sigue pendiente de definición en el mapa; este prototipo no incorpora un formulario de registro ni asigna esa responsabilidad a un actor nuevo.

## Decisiones

**Decision**: conservar únicamente las decisiones y configuración de la demostración en una cookie firmada, de 24 horas, sin base de datos.

**Rationale**: permite recorrer lista → detalle → formulario → historial → consolidado y CSV, manteniendo aislados los navegadores y los datos originales de tutores. Las vistas siguen disponibles solo con `DEBUG=True`, igual que el prototipo existente. La cookie no contiene documentos; solo transiciones y números de configuración. Se comprueba su firma y expiración, y se rechaza una demostración que supere su límite de tamaño. Configuración ofrece restablecer los datos. Las horas ya asignadas no cambian al modificar la configuración.

**Alternatives considered**: cambios globales en memoria (mezclarían navegadores), sesión en base de datos (exigiría migraciones para abrir un prototipo) y mostrar solo el resultado del POST (no permitiría consultar después el cambio desde el consolidado).

Esto no implementa autenticación, almacenamiento duradero ni auditoría de producción. El historial de demostración solo agrega entradas desde las acciones permitidas; puede restablecerse con los datos ficticios. Las tareas de modelos y servicios de producción siguen pendientes.

## Tareas del prototipo

- [x] P-C01: datos deterministas de 150 prácticas propias y 40 de otras carreras; estados, informes y resultados.
- [x] P-C02: C1, filtros y columnas RF-06; C2, cuatro tipos de alerta y vacío.
- [x] P-C03: C3, detalle compartido e historial con autor, transición, fecha y motivo.
- [x] P-C04: C4, requisitos visibles y comprobación de cierre también ante un POST directo.
- [x] P-C05: C5, suspensión y cancelación con motivo; reanudación conserva horas.
- [x] P-C06: C6, consolidado de prácticas cerradas; C7, configuración de horas, plazos y rezago.
- [x] P-C07: A1/A2, consolidado entre carreras y exportación CSV UTF-8 con fechas ISO.
- [x] P-C08: pruebas de vistas, reglas, aislamiento, CSV y diez cargas con 150 prácticas activas.
- [x] P-C09: recorrido real en Chrome, capturas de escritorio y móvil, guía de reproducción.

La fila de seguimiento de CONTRIBUTING se marca «PR abierto» cuando se publique el PR y «Mergeado» después de integrarlo. No se adelantan estos estados.

## Verificación

Ver [guía y evidencia](../../evidencias/prototipo-coordinador-verificacion.md). Pruebas iniciales en rojo por rutas inexistentes y escenarios inconsistentes; después de implementar, la suite incluye los casos previos de estudiante/tutores y los nuevos del coordinador.
