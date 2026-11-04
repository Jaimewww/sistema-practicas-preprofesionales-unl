# Datos e interfaces — #61

Sin modelos ni migraciones nuevos. Se conservan los diccionarios sintéticos y las horas requeridas asignadas a cada práctica.

- Alerta DTO: `tipo`, `tipo_display`, `estado_badge`, `detalle`, `fecha` ISO y `practica` con `id`, `estudiante`, `tipo`, `tipo_display`, `carrera`, `url` de consulta API y `detalle_url` de pantalla del destinatario.
- Listado de alertas: `count` numérico total y `alertas` filtradas por tipo, ordenadas por fecha e ID de práctica descendentes.
- Cierre: `en_revision_final → cerrada`; se conserva resultado de evaluación. Una entrada aditiva en `cambios[id]` registra origen, destino, autor, fecha y motivo.
- Conflicto: `error` con `code=transicion_invalida`, `message`, `recurso` y `faltante` como lista de requisitos legibles; lista vacía si el conflicto es únicamente el estado de origen.
- Cookie `prototipo_coordinador_v2`, firma y duración existentes, `Path=/`, `HttpOnly`, `SameSite=Lax`, `Secure` con HTTPS. Cookie anterior `prototipo_coordinador`, `Path=/prototipo/`, solo respaldo para migración desde las pantallas.

Los reportes nuevos siguen en la sesión emisora y las validaciones en su cookie. Este incremento no añade almacenamiento compartido ni amplía el catálogo de documentos revisables del API de validaciones.
