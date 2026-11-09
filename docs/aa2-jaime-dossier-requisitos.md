# Dossier individual de AA 2: requisitos, historias y trazabilidad

## 1. Identificación del proyecto

| Campo | Valor |
| --- | --- |
| **Proyecto** | Sistema de seguimiento de prácticas preprofesionales de la Universidad Nacional de Loja |
| **Repositorio** | <https://github.com/Jaimewww/sistema-practicas-preprofesionales-unl> |
| **Portal de documentación (Quarto)** | <https://jaimewww.github.io/sistema-practicas-preprofesionales-unl/> |
| **Especificación vigente** | [`specs/001-seguimiento-practicas/spec.md`](../specs/001-seguimiento-practicas/spec.md), versión **v0.4.0** (APE 002, 2026-11-08) |
| **Documentos de apoyo de la especificación** | [`data-model.md`](../specs/001-seguimiento-practicas/data-model.md), [`tasks.md`](../specs/001-seguimiento-practicas/tasks.md), [`research.md`](../specs/001-seguimiento-practicas/research.md), [`plan.md`](../specs/001-seguimiento-practicas/plan.md) |
| **Autor del dossier** | Jaime Landázuri — **@Jaimewww** |
| **Fecha** | 2026-11-12 |
| **Entregable** | AA 2, dossier individual de requisitos |
| **Rama de evidencia** | `docs/evidencias-sumativa`, tip `332f56b` |
| **Cadena revisada** | PR #98 (#76 cimientos), #100 (#77 contrato de respuesta y OpenAPI), #101 (#78 flujo de reportes), #102 (#79 autenticación y permisos), #103 (#80 pytest y cobertura) |

Este dossier es individual: registra **lo que revisé, corregí y justifiqué** sobre los requisitos de la especificación v0.4.0 en AA 2. La carpeta `docs/` es zona de otro colaborador; este documento se crea con autorización explícita para la entrega y no modifica ningún otro archivo de esa carpeta.

---

## 2. Síntesis del problema

Las prácticas preprofesionales son obligatorias para titularse: el certificado de horas cumplidas es requisito de la declaratoria de aptitud legal previa a la sustentación o al examen complexivo (Art. 235). Hoy su seguimiento se hace con formularios, correos, mensajes y archivos sueltos, y cada carrera los maneja a su manera.

| Situación actual | Consecuencia |
| --- | --- |
| El avance de cada práctica está repartido entre estudiante y tutores. | El coordinador no sabe en qué estado está cada práctica sin pedir información. |
| Las horas se suman a mano. | El atraso se descubre tarde, cuando ya no hay tiempo de corregirlo. |
| Las evidencias circulan sin registro de revisión. | No se sabe quién validó qué ni cuándo: no hay trazabilidad. |
| Los documentos de cierre están dispersos. | Cerrar una práctica exige reunirlos y revisarlos uno por uno. |
| La evaluación final no queda en un registro común. | No se puede demostrar que la práctica se aprobó con el **100 % de las horas y al menos 70 %** de desempeño (Art. 339). |

**Problema delimitado:** no existe una forma única y confiable de dar seguimiento a una práctica ya asignada, desde su inicio hasta su cierre, que muestre el avance de horas, el estado de las evidencias, la evaluación final y quién validó cada paso. El valor del sistema no está en almacenar formularios, sino en el **seguimiento y la trazabilidad** del proceso.

**Queja concreta del cierre al 70 %.** El reglamento acredita la práctica solo con el 100 % de las horas programadas y al menos 70 % en la evaluación; por debajo de ese 70 % la práctica se repite y las horas no se trasladan (Art. 339). Sin un registro común, la universidad no puede demostrar ese resultado ni distinguir un 69 % de un 70 %, y el cierre depende de reunir a mano documentos que nadie firmó de forma verificable.

**Deriva del informe.** El informe consolidado de cumplimiento que el coordinador presenta a la dirección (Art. 335, 340) se reconstruye manualmente a partir de soportes que no comparten formato ni momento. El consolidado, entonces, no deriva del estado real de cada práctica sino de la última copia que alguien reunió: cualquier cambio posterior en horas o en resultado deja el informe desactualizado sin que se note. Igual pasa con el historial: sin un registro inalterable, no se puede reconstruir quién cambió qué ni cuándo (CE-06).

**Bloque normativo que enmarca la solución (Art. 335–341).** 335: el docente responsable de prácticas de cada carrera gestiona las prácticas y presenta el informe consolidado. 336: el tutor académico orienta el plan, da seguimiento y evalúa. 337: el tutor institucional existe en la práctica **laboral**; el servicio comunitario no lo tiene. 338: la práctica comunitaria se realiza dentro de un proyecto de vinculación aprobado. 339: acreditación con el 100 % de horas y al menos 70 %. 340: el director de carrera certifica las horas y la Secretaría recibe los anexos de cierre. 341: dedicación máxima de 10 horas semanales en ayudantías.

---

## 3. Actores principales

Se conservan los identificadores de la tabla de actores de `spec.md` §2, que son la base de la trazabilidad de este dossier.

| Actor | Papel | Necesidad | ID |
| --- | --- | --- | :---: |
| **Estudiante** | Desarrolla la práctica, planifica sus actividades, reporta su avance y presenta su informe final (Art. 336). | Saber cuántas horas lleva, cuántas le faltan y qué tiene pendiente o devuelto. | N-01 |
| **Tutor académico** | Docente que orienta el plan, da seguimiento, revisa el informe final y evalúa la práctica (Art. 336). | Aprobar o devolver las actividades semanales con observaciones y registrar la evaluación final, sin perseguir documentos. | N-02 |
| **Tutor de la entidad receptora** | Persona nombrada por la entidad donde se hace una práctica **laboral**; usa el sistema con cuenta propia y solo ve a sus practicantes. No existe en el servicio comunitario (Art. 337). | Confirmar las actividades, reportar incumplimientos y dejar su informe final registrado sin trámites adicionales. | N-03 |
| **Coordinador de prácticas** | Docente designado en cada carrera para gestionar las prácticas y presentar el informe consolidado (Art. 335). | Ver el estado de todas las prácticas en un solo lugar, enterarse a tiempo de los atrasos y obtener el consolidado. | N-04 |
| **Director de carrera** *(secundario)* | Recibe el informe consolidado y emite la certificación de horas, que queda fuera del alcance (Art. 340). | Consultar, sin poder modificarlos, los cierres y el historial de las prácticas de su carrera antes de certificar. | N-05 |
| **Secretaría de la carrera** *(secundario)* | Recibe los anexos de cierre de cada práctica para el expediente del estudiante (Art. 340). | Dejar constancia de qué anexos de cierre revisó, con autor y fecha, sin depender de correos. | N-06 |

Los actores secundarios (N-05, N-06) se incorporaron en la APE 002 (COR-12) para que cada acción de la matriz de permisos de RF-11 naciera de un actor y una historia. El tutor de la entidad se limita a la práctica laboral: esa delimitación es una de las correcciones que sostiene este dossier (§5, HU-07).

---

## 4. Fuentes consultadas

| ID | Fuente | Qué sustenta en este dossier |
| :---: | --- | --- |
| **F-01** | Universidad Nacional de Loja. (2021). *Reglamento de Régimen Académico de la UNL* (aprobado por el OCS el 27-01-2021). Compendio en [`docs/fuentes/reglamento-practicas-unl.md`](fuentes/reglamento-practicas-unl.md). | Los artículos 335–341 que fijan actores, acreditación (100 % de horas y 70 %), tope de ayudantías y certificación; la lectura de cada requisito, con su porqué, en [`docs/guia-requisitos.md`](guia-requisitos.md). Es la norma con la que se depuraron HU-07, HU-08 y HU-15. |
| **F-02** | Fielding, R., Nottingham, M., & Reschke, J. (2022). *RFC 9110: HTTP Semantics*. IETF / HTTP Working Group. <https://httpwg.org/specs/rfc9110.html> (consulta 2026). | Los contratos de la API real: **métodos por recurso** (GET para listado y detalle, POST para creación, en diseño orientado a recursos, §9); **códigos de estado** 201, 400, 401, 403, 404 y 204 (§15), con `WWW-Authenticate` en el 401 (§11.6.1); **representación y errores** como cuerpo de la respuesta (§8); **seguridad de credenciales** en las consideraciones de seguridad del documento; y el **modelo sin estado** del protocolo, que es la razón por la que la API real se identifica con un token JWT en `Authorization` y no con cookies de sesión (razón registrada en el ADR 0011). Explica también las **excepciones 204 y 304** del contrato universal de respuesta (ADR 0012), que no llevan cuerpo y por eso no se envuelven. |
| **F-03** | Django Software Foundation. (s. f.). *Django 5.2 documentation*. <https://docs.djangoproject.com/en/5.2/> — Django REST framework. (s. f.). *DRF 3.18 documentation*. <https://www.django-rest-framework.org/> | Clases de autenticación y de permisos, *throttling* y paginación con los que se implementan RNF-01, RNF-02 y RF-11; la forma de las vistas por recurso del §6. |
| **F-04** | drf-spectacular. (s. f.). *drf-spectacular 0.28 documentation*. <https://drf-spectacular.readthedocs.io/> | El esquema OpenAPI 3.0.3 de `/api/v1/schema/` y la documentación de las respuestas de error de cada operación (criterio del PR #100 y #101). |
| **F-05** | djangorestframework-simplejwt. (s. f.). *Documentation, versión 5.5.1*. <https://django-rest-framework-simplejwt.readthedocs.io/> | Rotación de refresh y lista de bloqueo (`token_blacklist`) con las que se cumple el cierre de sesión de RNF-03, según el ADR 0011. |
| **F-06** | pytest-django. (s. f.). *pytest-django 4.14 documentation*. <https://pytest-django.readthedocs.io/> — pytest-cov. (s. f.). *pytest-cov documentation*. <https://pytest-cov.readthedocs.io/> | El runner de la suite y la medición de cobertura que verifican RNF-09: configuración en `backend/pytest.ini` y `backend/.coveragerc`, comando canónico y reporte `coverage.xml` para Sonar. |
| **F-07** | Registro de requisitos previos del proyecto: [`specs/001-seguimiento-practicas/`](../specs/001-seguimiento-practicas/) (`spec.md` v0.4.0, `data-model.md`, `tasks.md`, `research.md`, `plan.md`), [`docs/bibliografia.md`](bibliografia.md), [`docs/guia-requisitos.md`](guia-requisitos.md) y los ADR del repositorio ([`docs/adr/`](adr/)), en especial 0002 (PostgreSQL), 0003 (historial inalterable), 0004 (RBAC y filtrado por consulta), 0010 (DRF y PostgreSQL), 0011 (autenticación) y 0012 (contrato universal). | Las historias, los requisitos, el modelo de datos, la asignación de tareas a la cadena (#76–#80) y las decisiones de diseño con las que se juzgó si un requisito llegó a producción. |
| **F-08** | Registro de revisión del equipo: sesiones de validación del docente en `spec.md` §Clarifications (2026-10-26 y 2026-11-04, aprobadas sin observaciones), la APE 002 y la revisión de #98 (2026-11-08) con las preguntas pendientes P-01 a P-08, más el registro PR por PR de [`docs/revisiones/cadena-jaime.md`](revisiones/cadena-jaime.md). | Las decisiones que la especificación aún no puede cerrar (P-01..P-08) y el porqué de cada corrección aplicada en la cadena, incluida la que resolvió HU-07 y el alcance de T019. |

Solo F-02 es una fuente externa nueva respecto de la bibliografía de APE-001; el resto ya estaba registrado en `docs/bibliografia.md` o en los ADR. La cita de RFC 9110 se incorpora a la bibliografía del equipo por PR propio: este dossier no edita `docs/bibliografia.md`.

---

## 5. Historias de usuario depuradas

La depuración consistió en tres comprobaciones sobre las quince historias de `spec.md` §3: (a) que cada historia corresponde a un actor real con su necesidad `N-xx` y no a un rol inventado; (b) que la historia y sus criterios coinciden con el reglamento y con el modelo de datos, corrigiendo donde había deriva; y (c) que lo no tocado quede dicho, sin presentar como propio el trabajo de otra persona.

| HU | Necesidad | Depuración aplicada por Jaime |
| :---: | :---: | --- |
| HU-01 | N-01 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-02 | N-01 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-03 | N-02 | **Depurada.** Se confirmó que solo las horas validadas por el tutor académico suman al acumulado (RF-05) y que cada validación deja autor y fecha (RF-04); las horas en revisión cuentan únicamente para el cálculo de rezago (regla 2 de `data-model.md`). La redacción de la historia no se reescribió: la precisión vive en los criterios y en el modelo. La pregunta P-03 (si también cuentan las horas confirmadas por la entidad) sigue abierta al docente. |
| HU-04 | N-01 | **Depurada junto con HU-03.** El avance que ve el estudiante se calcula solo con horas validadas frente a las requeridas; sin reportes validados muestra 0 y las horas requeridas, sin error. Se dejó explícito que un cambio de historia aquí habría contradicho a HU-03 y a la regla 2 del modelo, así que la historia quedó inalterable. |
| HU-05 | N-04 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-06 | N-04 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-07 | N-03 | **Depurada (deriva corregida).** La historia se aplicaba a cualquier práctica. Se fijó que el tutor de la entidad participa **solo en la práctica laboral** y **nunca en la comunitaria** (Art. 337), y que el servicio comunitario se cierra con el informe del proyecto de vinculación. El arreglo se entregó en la unidad T019 dentro del PR #98: `Practica.tutor_entidad` como clave foránea opcional con `PROTECT`, rechazo en `full_clean()` de una práctica comunitaria con tutor de entidad y el filtrado de filas de `practicas_visibles_para`. Queda verificado en `backend/tests/integration/test_aislamiento_roles.py::VinculoTutorEntidadTests::test_una_practica_comunitaria_rechaza_el_tutor_de_entidad`. |
| HU-08 | N-04 | **Depurada.** El cierre exige las cuatro condiciones a la vez: **100 % de las horas requeridas validadas, informe final del estudiante revisado, informe externo registrado y evaluación final**; el resultado se conserva y la práctica deja de admitir cambios (Art. 339). Se precisó además que un cierre con evaluación menor al 70 % queda «no aprobada» y que las horas no se trasladan a la práctica siguiente. Es la corrección COR-02/RF-09 de la especificación. |
| HU-09 | N-04, N-05 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-10 | N-01 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-11 | N-02 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-12 | N-03 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-13 | N-04 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-14 | N-04 | sin cambios desde APE-002 (depuradas por AlejandroTatum 2026-11-08) |
| HU-15 | N-06 | **Depurada.** La legalización del anexo se registraba en el prototipo en una cookie firmada, sin identidad real, y esa forma no se traslada a la API real: para la API se **descartaron la sesión y las cookies** y se fijó **JWT** con access de 15 minutos, refresh de 30 con rotación y lista de bloqueo (ADR 0011), de modo que el autor y la fecha salgan del usuario autenticado y no de una persona sintética. La legalización sigue siendo una acción distinta de la validación del tutor y no cambia el estado de la práctica (RF-20). Sin endpoint todavía: RF-20 está sin implementar y la legalización vive solo en el demo. |

Resultado de la depuración: cuatro historias corregidas o confirmadas por mí (HU-03/HU-04, HU-07, HU-08, HU-15), una deriva real cerrada en código dentro de la cadena (HU-07, T019, PR #98) y once historias declaradas sin cambios, para no atribuirme su depuración.

---

## 6. Requisitos funcionales

Los veinte requisitos de `spec.md` §7. La columna Estado distingue lo que la cadena mergeada (#98–#103) puso en código de producción —modelos, servicios, contrato, reportes y JWT— de lo que sigue existiendo solo como prototipo con datos sintéticos o no existe. «Implementado» exige una prueba que lo verifique sobre la base real.

| RF | Qué exige (una línea) | HU | Estado | Verificación |
| :---: | --- | :---: | --- | --- |
| RF-01 | Registrar el plan de actividades del estudiante y enviarlo a revisión. | HU-01 | implementado (servicio) | `backend/tests/integration/test_plan_actividades.py::EnvioTests::test_enviar_crea_la_version_uno_en_revision_y_el_tutor_la_ve_pendiente` |
| RF-02 | Registrar actividades semanales con horas y evidencias (PDF ≤ 5 MB, RNF-05). | HU-02 | implementado (endpoint real) | `backend/tests/integration/test_reportes_flujo.py::RegistroDeReportesTests::test_el_post_registra_el_reporte_y_responde_201`. Brecha: el endpoint registra semana y horas; las evidencias PDF no tienen modelo todavía. |
| RF-03 | Validar o devolver planes y reportes; la devolución exige observación. | HU-01, HU-03 | parcial | `test_plan_actividades.py::DevolucionTests::test_devolver_sin_observacion_se_rechaza` y `test_devolver_con_observacion_marca_devuelto_y_no_crea_version`. Falta la validación del reporte semanal (llega con HU-03). |
| RF-04 | Registrar en cada validación quién la realizó y en qué fecha. | HU-03 | implementado | `test_plan_actividades.py::ValidacionModeloTests::test_guarda_autor_y_fecha_y_aprueba_sin_observacion` |
| RF-05 | Calcular las horas validadas y compararlas con las requeridas. | HU-04 | sin implementar | Solo prototipo (`sample_data.py`); falta el servicio de dominio. |
| RF-06 | Mostrar al coordinador, por práctica, estado, horas y alertas de su carrera. | HU-05 | parcial | `backend/apps/practicas/api.py` sirve el listado real con alcance por rol (`test_reportes_flujo.py::AlcanceDeFilasTests`); falta el desglose de horas en la tarjeta. |
| RF-07 | Generar alertas por reportes no enviados, revisiones pendientes, rezago e incumplimientos. | HU-06, HU-12 | sin implementar | Solo prototipo; no hay comando de gestión ni tarea programada. |
| RF-08 | Confirmar reportes de sus practicantes y registrar el informe final (tutor de entidad). | HU-07 | parcial | El vínculo y el alcance del tutor de entidad están implementados (T019): `test_aislamiento_roles.py::VinculoTutorEntidadTests` y `test_reportes_flujo.py::AlcanceDeFilasTests::test_el_tutor_externo_solo_ve_la_practica_vinculada_laboral`. La confirmación y el informe externo no tienen endpoint real. |
| RF-09 | Cerrar solo con 100 % de horas, informe revisado, informe externo y evaluación; conservar el resultado. | HU-08 | parcial | La arista `en revisión final → cerrada` exige al coordinador activo de la carrera: `backend/tests/unit/test_transiciones_practica.py::TransicionPermisoTests::test_el_coordinador_activo_de_la_carrera_recorre_las_cuatro_aristas`. Las condiciones de horas e informes y la regla del 70 % no están en producción. |
| RF-10 | Guardar un historial inalterable de los cambios de estado y permitir consultarlo. | HU-09 | implementado | `backend/tests/unit/test_historial_estado.py::HistorialEstadoInmutableTests::test_modificar_un_registro_guardado_se_rechaza` (más borrado masivo y `bulk_create` rechazados) |
| RF-11 | Permitir a cada actor solo sus acciones y rechazar las demás, sin modificar datos. | Todas | implementado | `test_aislamiento_roles.py::AlcancePorRolTests::test_estudiante_solo_ve_sus_practicas`; `backend/tests/integration/test_auth_seguridad.py::PermisosPorRolYObjetoTests::test_un_rol_sin_permiso_en_la_ruta_responde_403`. La matriz completa rol × acción sigue sin recorrerse entera. |
| RF-12 | Configurar por carrera horas por modalidad, plazos y umbral de rezago. | HU-04, HU-06 | parcial | El modelo `ConfiguracionCarrera` existe con sus valores por defecto y sus restricciones: `backend/tests/unit/test_configuracion_carrera.py::ConfiguracionCarreraPorDefectoTests`. No hay endpoint de configuración. |
| RF-13 | Suspender, reanudar y cancelar con motivo obligatorio al suspender y cancelar. | HU-14 | implementado (servicio) | `test_transiciones_practica.py::TransicionMotivosYRechazosTests::test_motivo_obligatorio_solo_al_suspender_y_cancelar` y `test_reanudar_sin_motivo_se_acepta_y_con_motivo_se_guarda_en_el_historial`. Sin endpoint. |
| RF-14 | Registrar tipo, subtipo laboral y proyecto de vinculación obligatorio en la comunitaria. | HU-02, HU-08 | implementado | `backend/tests/unit/test_practica.py::PracticaReglasPorTipoTests::test_comunitaria_sin_proyecto_o_con_subtipo_es_rechazada` y `PracticaSubtiposLaboralesTests::test_los_cuatro_subtipos_se_guardan` |
| RF-15 | Rechazar los reportes de ayudantía que superen 10 horas semanales, citando el Art. 341. | HU-02 | implementado | `test_reportes_flujo.py::RegistroDeReportesTests::test_la_ayudantia_rechaza_mas_de_10_horas_con_el_art_341` y `test_la_ayudantia_admite_exactamente_10_horas` |
| RF-16 | Presentar el informe final de actividades y que el tutor lo revise o lo devuelva. | HU-10 | sin implementar | Solo existe la revisión en el demo; falta que el estudiante pueda presentarlo. |
| RF-17 | Registrar la evaluación final y asignar «aprobada» desde 70 %. | HU-11 | sin implementar | Solo prototipo (`forms.py`, `resultado_evaluacion`). |
| RF-18 | Reportar un incumplimiento del practicante al tutor académico. | HU-12 | sin implementar | Solo pantalla del demo; no se guarda ni genera la alerta. |
| RF-19 | Generar el informe consolidado de cumplimiento de la carrera. | HU-13 | sin implementar | Solo prototipo (CSV del demo). |
| RF-20 | Legalizar una sola vez cada anexo de cierre, con autor y fecha, sin cambiar el estado. | HU-15 | sin implementar | Solo la ruta del demo en `/prototipo/api/v1/`. |

Resumen: **ocho implementados** (RF-01, RF-02, RF-04, RF-10, RF-11, RF-13, RF-14, RF-15), **cinco parciales** (RF-03, RF-06, RF-08, RF-09, RF-12) y **siete sin implementar** (RF-05, RF-07, RF-16, RF-17, RF-18, RF-19, RF-20). El contrato universal de respuesta (#100) y el JWT (#102) no son requisitos funcionales por sí mismos: sirven a RF-11 y a RNF-01, y por eso se registran en los no funcionales.

---

## 7. Requisitos no funcionales

| RNF | Qué garantiza | Dónde se verifica | Estado |
| :---: | --- | --- | --- |
| RNF-01 | Que el usuario se identifique antes de cualquier operación protegida; solo el inicio de sesión y la verificación de salud quedan abiertos. | `test_auth_seguridad.py::SinCredencialesTests::test_sin_credenciales_toda_la_api_real_responde_401`; `/health/` en `backend/apps/health/tests.py::HealthEndpointTests`. | implementado |
| RNF-02 | Rechazar como no autorizada cualquier acción fuera del rol, sin modificar datos. | `test_auth_seguridad.py::PermisosPorRolYObjetoTests::test_un_rol_sin_permiso_en_la_ruta_responde_403` y `test_la_practica_ajena_en_el_post_responde_404_identico_sin_escribir`; `test_plan_actividades.py::PermisosQueNoSeSaltanTests`. | implementado, con la brecha de la matriz completa rol × acción |
| RNF-03 | Contraseñas con hash y cierre de sesión tras 30 minutos de inactividad. | Hash heredado de `AbstractUser`; la ventana de 30 minutos se deriva del refresh con rotación: `backend/tests/integration/test_auth_sesion.py::ConfiguracionSegunAdrTests::test_simple_jwt_sigue_el_adr_0011` y `CierreDeSesionTests`. | parcial: falta la prueba de 31 minutos de inactividad |
| RNF-04 | Panel del coordinador bajo 2 s con 150 prácticas activas. | Solo la medición del prototipo (`tests_coordinador.py`, en la suite del demo). | sin implementar en producción |
| RNF-05 | Evidencias solo PDF de hasta 5 MB, con rechazo de cualquier otro formato o tamaño. | El formulario del demo lo cumple; la API real no tiene entidad de evidencia (declarado como brecha en #101). | pendiente |
| RNF-06 | Disponibilidad del 99 % y respaldo diario. | `/health/` consulta la base y responde 503 si falla; no hay medición de disponibilidad ni restauración de copia. | parcial |
| RNF-07, RNF-08 | Usabilidad (primer reporte en menos de 5 minutos) y accesibilidad WCAG 2.1 AA. | Sin pruebas de usabilidad ni auditoría de accesibilidad. | pendiente |
| RNF-09 | Una prueba del caso válido y otra del caso de error por regla de negocio, cobertura de dominio ≥ 80 % y análisis estático sin errores. | `backend/pytest.ini`, `backend/.coveragerc` y `backend/tests/unit/test_pytest_config.py`; el CI corre `python -m pytest --cov` y la cobertura medida ronda el 97 %. | implementado para las reglas que existen; las de RF-07, RF-09, RF-17 y RF-20 aún no tienen prueba de producción |
| RNF-10 | Exportar el consolidado a CSV en UTF-8 con fechas ISO 8601. | Solo la prueba del demo (`tests_coordinador.py::test_consolidated_csv_scope_encoding_dates_and_filters`). | pendiente |
| RNF-11 | Identificadores institucionales (cédula y código de carrera) sin transformar. | `Carrera.codigo` existe y es único (`test_configuracion_carrera.py::CarreraTests`); la cédula del usuario no está modelada. | pendiente |

La frontera de identidad es la que más cambió en la cadena: el 401 sale del contrato universal con `WWW-Authenticate` (F-02), y el demo `X-Rol` dejó de compartir prefijo con la API real (`/prototipo/api/v1/`), de modo que ninguna ruta de `/api/v1/` lee esa cabecera, con `DEBUG` encendido o apagado.

---

## 8. Criterios de aceptación explícitos

Se explicitan en formato Dado/Cuando/Entonces los tres flujos que sostienen el resto de la matriz. Los criterios completos de las quince historias siguen en `spec.md` §3 y se referencian por requisito en §9; no se duplican aquí para no crear una segunda fuente que pueda desviarse.

### HU-01 · Registrar el plan de actividades

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un estudiante con una práctica asignada | registra su plan de actividades | el plan queda «en revisión» y su tutor académico ve que tiene un plan pendiente |
| 2 | un plan en revisión | el tutor académico lo devuelve con observaciones | el estudiante ve las observaciones y puede corregirlo; el reenvío crea la versión siguiente |
| 3 | un plan en revisión | el tutor académico lo aprueba | la práctica pasa de `asignada` a `en curso` y el estudiante ya puede reportar semanas |
| 4 | un plan en revisión | el tutor intenta devolverlo sin observación | la devolución se rechaza y el plan sigue en revisión |

### HU-02 · Reportar actividades semanales

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un plan aprobado | el estudiante reporta la semana con horas y evidencias | el reporte queda con fecha de registro y «en revisión» (201) |
| 2 | un reporte semanal sin validar | se consultan las horas cumplidas | sus horas todavía no se cuentan |
| 3 | una práctica de subtipo ayudantía | el estudiante intenta reportar más de 10 horas en una semana | el reporte se rechaza y el mensaje indica el máximo del Art. 341; uno de exactamente 10 horas se acepta |
| 4 | una práctica laboral que no es ayudantía, o una comunitaria | el estudiante reporta más de 40 horas en una semana | el reporte se registra «en revisión» y queda marcado para que el tutor lo revise |

### HU-03 · Validar actividades semanales

| # | Dado | Cuando | Entonces |
| :---: | --- | --- | --- |
| 1 | un reporte en revisión | el tutor académico lo valida | las horas se suman al acumulado y queda registrado quién validó y cuándo |
| 2 | un reporte en revisión | el tutor lo devuelve | debe escribir una observación y el reporte vuelve al estudiante |

Estos criterios son los que están detrás de las filas 1 a 3 de la matriz siguiente; los de HU-06, HU-08, HU-09 y HU-15 aparecen en la matriz a través de RF-07, RF-09, RF-10 y RF-20.

---

## 9. Matriz de trazabilidad inicial

Cada fila recorre el camino actor → necesidad → historia y requisito → criterio observable → fuente → prueba. La columna Estado solo dice «implementado» cuando existe el módulo y el nombre exacto de la prueba que lo verifica sobre la base real.

| ID-Actor | Necesidad | Historia / RF | Criterio (Dado / Cuando / Entonces) | Fuente | Estado |
| :---: | --- | --- | --- | :---: | --- |
| N-01 | Registrar el plan y que el tutor lo apruebe | HU-01 / RF-01, RF-03 | Dado un estudiante con práctica asignada, cuando envía su plan, entonces queda «en revisión» y el tutor lo ve pendiente | F-01, F-07 | **implementado** — `backend/tests/integration/test_plan_actividades.py::EnvioTests::test_enviar_crea_la_version_uno_en_revision_y_el_tutor_la_ve_pendiente` |
| N-01 | Registrar el avance semanal con horas y evidencias | HU-02 / RF-02, RF-15 | Dado un plan aprobado, cuando reporta la semana con horas, entonces responde 201 y queda «en revisión» con fecha | F-01, F-02, F-03 | **implementado** — `test_reportes_flujo.py::RegistroDeReportesTests::test_el_post_registra_el_reporte_y_responde_201`. Evidencias PDF pendientes (RNF-05) |
| N-02 | Validar o devolver con observación; solo lo validado suma | HU-03 / RF-03, RF-04 | Dado un pendiente en revisión, cuando el tutor devuelve sin observación, entonces se rechaza; con observación queda «devuelto» con autor y fecha | F-01, F-07 | **implementado para el plan** — `test_plan_actividades.py::DevolucionTests::test_devolver_sin_observacion_se_rechaza` y `test_devolver_con_observacion_marca_devuelto_y_no_crea_version`. La validación del reporte semanal sigue pendiente |
| N-04 | Enterarse a tiempo de los atrasos | HU-06 / RF-07, RF-12 | Dado que las horas validadas más las en revisión quedan bajo el umbral de rezago, cuando se detecta, entonces estudiante, tutor y coordinador reciben la alerta | F-01, F-07 | **no implementado** — solo prototipo; la regla se calcula en datos sintéticos |
| N-04, N-05 | Cerrar solo con 100 % de horas, informes y 70 %, y consultar el cierre | HU-08, HU-09 / RF-09, RF-10 | Dado práctica con 100 % de horas validadas, informe revisado, informe externo y evaluación ≥ 70 %, cuando el coordinador cierra, entonces pasa a «cerrada» y no admite cambios; con 69 % queda «no aprobada» | F-01 | **parcial** — transición y permiso en `test_transiciones_practica.py::TransicionPermisoTests::test_el_coordinador_activo_de_la_carrera_recorre_las_cuatro_aristas`; las condiciones de horas, informes y 70 % no están en producción |
| N-04, N-05 | Saber quién hizo qué y cuándo, sin poder alterarlo | HU-09 / RF-10 | Dado un registro del historial, cuando alguien intenta modificarlo o borrarlo, entonces la acción no se permite | F-01, F-07 | **implementado** — `backend/tests/unit/test_historial_estado.py::HistorialEstadoInmutableTests::test_modificar_un_registro_guardado_se_rechaza` |
| N-01…N-06 | Que cada actor vea y haga solo lo suyo | RF-11 (todas las HU) | Dado un usuario con un rol, cuando consulta una práctica ajena o actúa fuera de su rol, entonces recibe 403 o 404 idéntico sin cambios en los datos | F-02, F-03 | **implementado** — `test_aislamiento_roles.py::AlcancePorRolTests::test_estudiante_solo_ve_sus_practicas` y `test_auth_seguridad.py::PermisosPorRolYObjetoTests::test_un_rol_sin_permiso_en_la_ruta_responde_403` |
| N-03 | Tope del Art. 341 en ayudantías y tutor de entidad solo en la laboral | HU-02, HU-07 / RF-15, RF-08 | Dado una práctica de ayudantía, cuando el estudiante reporta 11 horas, entonces se rechaza citando el Art. 341; con 10 horas se acepta; una práctica comunitaria no admite tutor de entidad | F-01, F-07 | **implementado** — `test_reportes_flujo.py::RegistroDeReportesTests::test_la_ayudantia_rechaza_mas_de_10_horas_con_el_art_341` y `test_aislamiento_roles.py::VinculoTutorEntidadTests::test_una_practica_comunitaria_rechaza_el_tutor_de_entidad` |

**Esta matriz sustituye, para AA 2, a [`docs/trazabilidad.md`](trazabilidad.md).** Ese archivo quedó congelado el 2026-11-03: fija el código en «`develop` en `2cb13f9`» y afirma que «hoy ningún requisito funcional alcanza este estado» de implementado, cuando la cadena #98–#103 ya está mergeada y ocho requisitos tienen código de producción con prueba. La matriz de este dossier es la fotografía vigente; la desactualización de `trazabilidad.md` ya quedó reportada en el PR #108 (comentario `#issuecomment-6731793683`), con el compromiso de actualizarla fila por fila en un PR propio.

---

## 10. Observaciones y decisiones pendientes

### Preguntas pendientes de la especificación (P-01..P-08)

Ninguna se reemplazó por un supuesto: cada una indica qué afecta y qué se hizo mientras tanto.

| ID | Pregunta | Qué se hizo mientras tanto |
| :---: | --- | --- |
| P-01 | ¿Quién registra el informe del proyecto de vinculación en la práctica comunitaria? | El cierre de una comunitaria se prueba con el informe cargado como dato; no hay actor definido porque ese servicio no tiene tutor de entidad (Art. 337). |
| P-02 | ¿Una práctica puede tener más de un tutor académico activo? | El código implementa un solo tutor activo: índice único parcial en `AsignacionTutor` (`backend/tests/unit/test_asignacion_tutor.py`). |
| P-03 | ¿Solo cuentan las horas validadas por el tutor académico? | Solo se suman las validadas; las horas en revisión cuentan únicamente para el rezago (regla 2 de `data-model.md`, HU-03/HU-04). |
| P-04 | ¿Hace falta registrar actividades sin conexión? | Se asume conexión; no se diseñó modo sin conexión. |
| P-05 | ¿Qué devuelve una práctica de «en revisión final» a «en curso»? | La transición no se implementó: el disparador sigue sin decidirse. |
| P-06 | ¿Se rechaza o se reemplaza un segundo reporte de la misma semana? | Se rechaza con 409 `semana_duplicada` (`test_la_semana_duplicada_responde_409_con_su_code_sin_escribir`); si el docente decide distinto, se ajusta el código y no la regla. |
| P-07 | ¿Se aceptan reportes de semanas fuera del período? | Sin regla definida; queda como caso límite pendiente. |
| P-08 | ¿Cómo se identifica el usuario ante la API? | Resuelto de forma provisional con JWT (ADR 0011, «Aceptada» el 2026-11-08): access de 15 minutos, refresh de 30 con rotación y lista de bloqueo, `POST /api/v1/auth/logout/` y tope de 5 intentos por minuto. |

### Deudas de implementación documentadas

- **Retiro del demo `X-Rol`.** Las rutas JSON del demo se movieron a `/prototipo/api/v1/` para que ninguna ruta de `/api/v1/` lea esa cabecera, pero el demo sigue existiendo. Su retiro está pendiente del ADR #84 (modelo de amenazas y análisis de seguridad), que es de otro colaborador.
- **Desalineación del `Makefile`.** `make test` ejecuta `manage.py test`, mientras el CI, el README del backend y el portal usan `pytest`. Ambos runners describen hoy la misma suite, pero mantener dos comandos canónicos es una fuente de confusión; queda registrado en #108.
- **`trazabilidad.md` desactualizada.** Detalle en §9.
- **Otras deudas de la cadena:** las evidencias PDF de RNF-05 no tienen modelo ni almacenamiento; la carrera obligatoria por rol no está restringida en la base; las actividades y versiones del reporte no tienen modelo (llegan con HU-03); `flushexpiredtokens` no está programado; el tope de intentos usa cache local al proceso; `docs/seguridad.md` sigue describiendo el demo; Swagger UI no es navegable con `DEBUG` apagado; PostgreSQL 17 solo lo ejerce el CI.

---

# Nota de cambios respecto a la versión previa

- **La matriz de trazabilidad de este dossier reemplaza a la de APE-002.** `docs/trazabilidad.md` sigue fijando «`develop` en `2cb13f9`» y afirmando que ningún requisito funcional está implementado; con la cadena #98–#103 mergeada, ocho requisitos tienen código de producción y prueba, y otros cinco están parciales. La brecha quedó reportada en el PR #108 (comentario `#issuecomment-6731793683`).
- **Primera cita de RFC 9110 en la evidencia del proyecto.** Se incorpora como fuente que justifica el diseño orientado a recursos, los códigos 201/400/401/403/404/204, `WWW-Authenticate` en el 401, el cuerpo de error como representación y las excepciones 204/304 del contrato universal, además del modelo sin estado que sustenta el JWT del ADR 0011 frente a las cookies. `docs/bibliografia.md` todavía no la registra: se propone por PR propio.
- **HU-07 depurada y cerrada en código.** El tutor de la entidad se limitó a la práctica laboral y se excluyó de la comunitaria (Art. 337); el arreglo se entregó en la unidad T019 del PR #98 y se verifica en `test_aislamiento_roles.py::VinculoTutorEntidadTests`.
- **HU-15 depurada.** Se descartaron la sesión y las cookies para la API real y se fijó JWT con rotación y lista de bloqueo (ADR 0011), de modo que el autor y la fecha de la legalización salgan del usuario autenticado.
- **HU-03, HU-04 y HU-08 confirmadas sin reescritura.** Se dejó explícito que solo las horas validadas cuentan, que el historial asociado es inalterable y que el cierre exige simultáneamente el 100 % de las horas, el informe final revisado, el informe externo y la evaluación con la regla del 70 % (Art. 339).
- **La tabla de requisitos quedó ligada a pruebas de producción.** Cada RF implementado o parcial cita el módulo y el nombre exacto de la prueba que lo verifica; once historias se declaran «sin cambios desde APE-002», para no atribuirme su depuración.
- **Deudas documentadas en lugar de silenciadas.** Retiro del demo `X-Rol` pendiente del ADR #84, desalineación del `Makefile` y de la matriz de trazabilidad registradas en #108, y las ocho deudas de la cadena (RNF-05, carrera obligatoria por rol, actividades del reporte, limpieza de tokens, cache del tope, `docs/seguridad.md`, Swagger con `DEBUG` apagado y PostgreSQL 17).
- **Las preguntas P-01 a P-08 se mantienen abiertas con su respuesta provisional explícita.** P-06 y P-08 ya tienen respuesta en el código; si el docente decide distinto, se ajusta el código y no el requisito.
