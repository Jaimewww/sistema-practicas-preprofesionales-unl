# Verificación del prototipo Coordinador/DVS — #53

Fecha: 2026-10-21. Datos ficticios, fecha simulada: 2026-06-05.

## Reproducción

Desde la raíz, ejecutar `make run` y abrir `/prototipo/coordinador/practicas/`. No se necesitan migraciones. `make test` ejecuta también `apps.prototipo.tests_coordinador`.

| Escenario | Recorrido y resultado esperado |
| --- | --- |
| C1 | Lista de 150 prácticas de Computación. Filtrar período, tipo, estado, alerta o estudiante; limpiar restaura la lista. Las otras carreras no aparecen. |
| C2 | Alertas por reporte no enviado, revisión vencida, rezago e incumplimiento. Filtrar tipo; un filtro sin resultados muestra el vacío. |
| C3 | Abrir «Ver práctica» y recorrer Resumen, Plan, Reportes, Informe final e Historial. El coordinador no ve enlaces para validar documentos o registrar la evaluación del tutor. |
| C4 completo | `/prototipo/coordinador/practicas/7/cerrar/`: todos los requisitos cumplidos. Confirmar cierra y abre el historial; el consolidado incorpora el cierre. |
| C4 incompleto | `/prototipo/coordinador/practicas/6/cerrar/`: muestra faltantes y deshabilita el cierre; un POST directo también se rechaza sin cambiar la práctica. |
| C4 no aprobada | Cerrar la práctica 10: tiene 160 h y evaluación de 64 %. Se cierra como no aprobada y conserva el resultado en el CSV. |
| C5 | Suspender la práctica 1 exige motivo; reanudar conserva horas. Volver a suspender y cancelar exige motivo. Cerrada y cancelada no ofrecen nuevas acciones. |
| C6 | Consolidado por estudiante/componente de prácticas cerradas, con filtros. Exportar respeta esos filtros y solo incluye la carrera propia. |
| C7 | Guardar horas/plazos/umbral; los valores se conservan al navegar, las alertas usan los nuevos plazos y umbral, y las horas de prácticas ya asignadas no cambian. Restablecer elimina decisiones/configuración del navegador. |
| A1/A2 | `/prototipo/dvs/consolidado/`: incluye las tres carreras de muestra, filtros por período y componente y CSV UTF-8 con fechas AAAA-MM-DD. |
| Aislamiento | El coordinador recibe 403 al consultar/cerrar/cancelar la práctica 1000, de otra carrera. Una práctica inexistente responde 404. |

## Comprobaciones realizadas

- Suite Django: 95 pruebas correctas; incluye las pantallas anteriores de estudiante y tutores.
- RNF-04: test con 150 prácticas activas, diez cargas consecutivas, cada una por debajo de 2 segundos. Es medición del render del prototipo en el cliente de pruebas local, no una prueba de carga de producción.
- Chrome: nueve pantallas respondieron HTTP 200; recorrido de suspensión, reanudación, cierre y restablecimiento completado; sin errores JavaScript.
- Móvil: las nueve pantallas a 390 × 844 sin desbordamiento horizontal de la página.
- Firmas de cookie, confirmación, motivos, transiciones inválidas, CSRF y guardia `DEBUG=False` cubiertos por tests.

## Capturas

| Vista | Evidencia |
| --- | --- |
| C1 | [Prácticas de la carrera](prototipo-coordinador-practicas.png) · [Móvil](prototipo-coordinador-practicas-celular.png) |
| C2 | [Alertas](prototipo-coordinador-alertas.png) · [Móvil](prototipo-coordinador-alertas-celular.png) |
| C3 | [Historial](prototipo-coordinador-historial.png) · [Móvil](prototipo-coordinador-historial-celular.png) |
| C4 | [Requisitos completos](prototipo-coordinador-cierre.png) · [Faltantes](prototipo-coordinador-cierre-incompleto.png) · [Cerrada](prototipo-coordinador-cerrada.png) · [Móvil](prototipo-coordinador-cierre-celular.png) |
| C5 | [Suspender](prototipo-coordinador-suspender.png) · [Suspendida](prototipo-coordinador-suspendida.png) · [Móvil](prototipo-coordinador-suspender-celular.png) |
| C6 | [Consolidado de carrera](prototipo-coordinador-consolidado.png) · [Móvil](prototipo-coordinador-consolidado-celular.png) |
| C7 | [Configuración](prototipo-coordinador-configuracion.png) · [Móvil](prototipo-coordinador-configuracion-celular.png) |
| A1/A2 | [Consolidado general](prototipo-analista-consolidado.png) · [Móvil](prototipo-analista-consolidado-celular.png) |

El prototipo no implementa permisos de producción ni persistencia duradera. Las pantallas de cada actor simulan su identidad en DEBUG. El informe comunitario se representa como requisito, sin definir quién lo registra. Revisión humana pendiente en [PR #66](https://github.com/Jaimewww/sistema-practicas-preprofesionales-unl/pull/66).
