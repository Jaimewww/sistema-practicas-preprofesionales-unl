# API de alertas y cierre — #61

Fecha: 2026-10-24. Incremento del prototipo de `001-seguimiento-practicas`.

## Requisitos y aceptación

- RF-07/RF-12/RF-18: consultar alertas activas por destinatario y carrera, con plazos configurables y rezago del 80 % por defecto. El coordinador recibe toda su carrera; estudiante recibe reportes vencidos y rezago; tutor académico añade revisión vencida e incumplimiento; tutor de entidad recibe una lista vacía.
- RF-09/COR-02/CE-05: solo el coordinador de la carrera cierra desde `en_revision_final`, con horas validadas suficientes, informe del estudiante validado, informe externo y evaluación. Una evaluación menor al 70 % conserva el resultado «no aprobada».
- RF-10/RF-11: rechazos sin efectos, historial aditivo e aislamiento de otras carreras. Una segunda petición de cierre devuelve 409.
- C2 lista y contador consumen JSON; C4 presenta `error.faltante`. Las pantallas conservan una alternativa sin JavaScript.
- Solo datos sintéticos, `DEBUG=True` y estado por navegador. Persistencia compartida, identidad real y notificaciones programadas quedan fuera de este incremento.

Los criterios de dominio originales siguen en [spec.md](../001-seguimiento-practicas/spec.md), HU-08, CU-02 y CU-03.
