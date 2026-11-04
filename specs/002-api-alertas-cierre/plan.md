# Plan — API de alertas y cierre

## Diseño

Mantener Django 5.2, plantillas SIAAF, `JsonResponse`, fachada y DTO. Reutilizar las reglas existentes de `sample_data`, sin DRF ni migraciones. Las vistas HTTP y HTML invocan los mismos casos de uso.

La fachada reconstruye las 150 prácticas de la carrera y 40 externas. Aplica decisiones del tutor sobre los documentos originales, luego los envíos de sesión (un reenvío reemplaza esa versión), recalcula horas y aplica cambios/configuración del coordinador antes de generar alertas. No modifica los ejemplos compartidos.

`GET /api/v1/alertas/?tipo=...` devuelve `{count, alertas}`; `count` es el total sin filtrar. `POST /api/v1/practicas/<id>/cierre/` no requiere cuerpo; exige CSRF y devuelve el DTO de la práctica o el contrato `error` con `faltante` en conflictos. El formulario HTML mantiene su confirmación explícita.

La cookie nueva del coordinador tiene `Path=/` y 24 h; las pantallas aceptan la antigua como respaldo y la migran al visitar el prototipo. Restablecer elimina ambas. Un exceso del límite de cookie falla sin publicar un cierre exitoso.

## Constitución

GitFlow: `feature/api-alertas-cierre` → PR a `develop`. Documentos SDD previos a código, pruebas RED → GREEN, sin cambios del stack ni de arquitectura. Uso de IA declarado y revisión humana no presumida.

## Verificación

Ejecutar [tasks.md](tasks.md): contrato, permisos, reglas y estado; suite completa y revisión visual de C2/C4 con JavaScript y alternativa HTML. Referencias: [research.md](research.md), [data-model.md](data-model.md).
