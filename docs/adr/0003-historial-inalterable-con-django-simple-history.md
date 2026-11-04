# 0003. Historial inalterable con django-simple-history

- **Estado**: Aceptada
- **Fecha**: 2026-10-11
- **Decisores**: equipo (fase 0 de la planificación)

## Contexto

RF-10 y CE-06 exigen reconstruir el historial completo de una práctica (quién, qué y cuándo) y que ningún registro pueda modificarse ni borrarse. Origen: [research.md, Tema 3](../../specs/001-seguimiento-practicas/research.md).

## Decisión

Usar **`django-simple-history`** sobre el modelo de práctica, con una tabla de historial de solo inserción (entidad `HistorialEstado` del [data-model.md](../../specs/001-seguimiento-practicas/data-model.md)). El API no ofrece `DELETE` ni escritura sobre el historial.

## Alternativas consideradas

- **Triggers en PostgreSQL**: potentes, pero sacan la regla del código de la aplicación y la vuelven difícil de revisar y probar.
- **Tabla de auditoría escrita a mano con señales de Django**: control total, pero más código propio y más formas de olvidar un caso.

## Consecuencias

- **Positivas**: la tabla histórica se mantiene sin lógica propia; la regla de inalterabilidad se revisa en código Python.
- **Negativas o costos**: una dependencia más y una tabla de historial por modelo auditado.
- **Pendiente**: hoy el historial es una lista en memoria de `sample_data.py` (`_historial_inicial`) expuesta por `facade.historial_de`; pasa a persistencia con #76.

## Referencias

- [research.md, Tema 3](../../specs/001-seguimiento-practicas/research.md)
- [docs/api.md, §9.1](../api.md)
