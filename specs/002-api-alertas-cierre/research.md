# Decisiones — #61

## Fuente única de datos y reglas

**Decision**: ampliar la fachada al catálogo sintético ya usado por C1/C2, aplicar los overlays del navegador y reutilizar las reglas de alertas/cierre.

**Rationale**: evita que la API omita las prácticas 100–239 o ignore validaciones y configuración. Los DTO proyectan datos explícitos, evitando la referencia circular alerta → práctica → alertas.

**Alternatives considered**: duplicar reglas en las vistas; conservar dos catálogos divergentes; añadir un repositorio o DRF. Descartadas por inconsistencias o complejidad innecesaria.

## Estado de demostración

**Decision**: mantener cookies firmadas y sesión existentes, con nueva cookie del coordinador accesible desde `/api/` y `/prototipo/` y migración de la anterior desde las pantallas.

**Rationale**: permite verificar coherencia en un navegador sin convertir un aporte del prototipo en el backend de producción.

**Alternatives considered**: persistencia compartida en base de datos. Se difiere a otro issue con identidad autenticada, permisos y pruebas entre usuarios.

## Transporte

**Decision**: CSRF obligatorio en cierre; mantener el contrato JSON anidado de `docs/api.md` y `faltante` dentro de `error`. La campana y C2 consumen el mismo endpoint; C4 usa el mismo servicio en fetch y formulario HTML.

**Rationale**: el cierre depende de una cookie del navegador. El issue simplifica el ejemplo del error, pero exige explícitamente fidelidad al contrato adoptado.

**Alternatives considered**: eximir CSRF como PATCH de validaciones; devolver errores planos. Descartadas para conservar protección y compatibilidad.
