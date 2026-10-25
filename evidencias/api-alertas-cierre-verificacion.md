# Verificación del API de alertas y cierre — #61

Fecha: 2026-10-24 (America/Bogota). Rama: `feature/api-alertas-cierre`. Ejecución y recorrido realizados por Codex; revisión humana y prueba cruzada pendientes.

## RED → GREEN

El commit `d9aeb41` incorpora primero los artefactos SDD y 12 pruebas nuevas, antes de implementar. Ejecución inicial:

```text
.venv/bin/python backend/manage.py test apps.prototipo.tests_alertas_cierre --verbosity 0
Ran 12 tests
FAILED (failures=9, errors=2)
```

Fallaron las rutas inexistentes (`404`), la cookie sin migración, la integración HTML/API y las horas de reportes de sesión que C1 no reflejaba. Después se añadieron tres escenarios de integración adicionales.

Verificación final desde la raíz:

```text
make test
Ran 203 tests
OK
System check identified no issues (0 silenced).

.venv/bin/python backend/manage.py check
System check identified no issues (0 silenced).

git diff --check
# sin errores
```

Se ajustaron tres fixtures/tests anteriores al catálogo ampliado: el alcance del coordinador incluye 150 prácticas; los mocks apuntan al nuevo origen de datos; un plan forzado a «en revisión» incluye su fecha de envío.

## Casos cubiertos

- Contrato JSON, métodos/Allow, roles, `DEBUG=False`, aislamiento de carreras, DTO sin ciclos, cuatro alertas, filtros y contador total.
- Reporte vencido al superar el plazo; revisión con cinco días hábiles exactos, fin de semana y vencimiento posterior; rezago al 80 % exacto y umbral del 90 %.
- Validación de un reporte actualiza las horas y elimina la revisión vencida. Validar el informe final desbloquea el cierre cuando los demás requisitos ya se cumplen.
- Cierre con cada requisito faltante, horas en revisión que no cuentan, informe comunitario, evaluaciones 69/70 %, repetición sin historial duplicado y errores sin efectos.
- Cookie nueva y antigua, migración, expiración, firma inválida, límite de tamaño y restablecimiento. CSRF rechazado sin token y cierre aceptado con token.
- Pantallas HTML sin ejecutar JavaScript usan los mismos casos de uso; reportes de sesión aparecen en C1 y consulta API del mismo navegador, sin afectar otro cliente.

## Recorrido del navegador

Iniciar `make run` y abrir C2. La fecha interna de las prácticas es la de los datos sintéticos (`HOY = 2026-06-05`); no se cambió por la fecha real.

1. C2 `/prototipo/coordinador/alertas/`: seleccionar «Incumplimiento reportado» y pulsar «Filtrar». La tabla consumida desde JSON muestra **1 alerta**; badge y campana conservan **62** alertas totales.
2. C4 `/prototipo/coordinador/practicas/6/cerrar/`: confirmar y solicitar cierre. La respuesta `409` muestra tres faltantes: informe del estudiante, informe externo y evaluación. La práctica no cambia.
3. C4 `/prototipo/coordinador/practicas/7/cerrar/`: confirmar y cerrar. Navega a `?tab=historial`, muestra «Cerrada (aprobada)», 160 horas validadas y una entrada del coordinador con fecha y motivo. Sin errores ni advertencias JavaScript en el recorrido.
4. Con C2 filtrado, detener el servidor de prueba y pulsar «Filtrar»: aparece «No se pudieron actualizar las alertas. Se conserva la última consulta.»; siguen visibles 1 alerta y el total 62. Reiniciar el servidor para continuar.

Capturas:

- [C2, filtro y contador](api-alertas-cierre/c2-filtro-contador.jpg)
- [C4, requisitos faltantes del 409](api-alertas-cierre/c4-faltantes-409.jpg)
- [C4, cierre e historial](api-alertas-cierre/c4-cierre-historial.jpg)
- [C2, error de conexión sin perder la consulta](api-alertas-cierre/c2-error-conexion.jpg)

## Pendiente para otro issue

Persistencia compartida entre usuarios/navegadores, identidad autenticada, permisos y almacenamiento del flujo estudiante → tutor → coordinador. Los envíos nuevos aún no se incorporan a la bandeja T1 ni al catálogo revisable del PATCH; la integración actual proyecta las decisiones de documentos originales para consultar horas, alertas y cierre. No se crea un issue adicional en este aporte.

## Estado de publicación

Implementación verificada y publicada en `feature/api-alertas-cierre`, con commits separados por funcionalidad y [PR #72](https://github.com/Jaimewww/sistema-practicas-preprofesionales-unl/pull/72) hacia `develop`. El [comentario en #61](https://github.com/Jaimewww/sistema-practicas-preprofesionales-unl/issues/61#issuecomment-6392456159) documenta el trabajo pendiente para otro issue; la revisión humana y el merge a `develop` quedan pendientes.
