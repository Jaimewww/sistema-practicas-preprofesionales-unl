# Guía de requisitos: el porqué de cada uno

Esta guía recorre los 19 requisitos funcionales de la [especificación](../specs/001-seguimiento-practicas/spec.md) en el orden en que aparecen durante la vida de una práctica. Para cada uno explica qué pide, por qué existe y cómo se comprueba que se cumple.

> [!TIP]
> **Cómo leer cada ficha**
>
> - **Qué pide:** el requisito en una frase.
> - **Por qué:** el problema que resuelve y, si aplica, el artículo del reglamento que lo exige.
> - **Se comprueba cuando:** la prueba concreta que demuestra que está cumplido.
> - **Si faltara:** qué se rompe sin él. Sirve para defender el requisito si alguien propone recortarlo.
>
> «Art. N» remite al [Reglamento de Régimen Académico de la UNL](fuentes/reglamento-practicas-unl.md).

## Contenido

1. [El recorrido de una práctica](#1-el-recorrido-de-una-práctica)
2. [Etapa 0 · Configuración](#2-etapa-0--configuración) — RF-12, RF-14
3. [Etapa 1 · Planificación](#3-etapa-1--planificación) — RF-01, RF-03
4. [Etapa 2 · Ejecución semanal](#4-etapa-2--ejecución-semanal) — RF-02, RF-15, RF-04, RF-08
5. [Etapa 3 · Seguimiento](#5-etapa-3--seguimiento) — RF-05, RF-06, RF-07, RF-18, RF-13
6. [Etapa 4 · Evaluación y cierre](#6-etapa-4--evaluación-y-cierre) — RF-16, RF-17, RF-09, RF-19
7. [Transversales](#7-transversales) — RF-10, RF-11
8. [Matriz de trazabilidad](#8-matriz-de-trazabilidad)
9. [Qué cambió con el reglamento](#9-qué-cambió-con-el-reglamento)

---

## 1. El recorrido de una práctica

```text
 Configuración      Planificación       Ejecución semanal        Evaluación y cierre
 ─────────────      ─────────────       ─────────────────        ───────────────────
 horas, plazos  ──► plan del       ──►  reporte + evidencias ──► informe del estudiante
 tipo, subtipo      estudiante          validación del tutor     informe externo
                    aprobado            confirmación entidad     evaluación ≥ 70 %
                                                                 cierre + consolidado
                         └──────────── Seguimiento: horas, alertas, suspensión ────────┘
                         └──────────── Transversal: historial y permisos ──────────────┘
```

> [!IMPORTANT]
> **La idea que ordena todo:** el reglamento dice que una práctica se aprueba con el **100 % de las horas** y **al menos 70 %** de desempeño (Art. 339), y que ese certificado es requisito para titularse (Art. 235). Casi todos los requisitos existen para que esas dos cifras sean **verificables y confiables**: quién validó cada hora, con qué evidencia y con qué informe se evaluó.

---

## 2. Etapa 0 · Configuración

### RF-12 · Configuración por carrera

| | |
| --- | --- |
| **Qué pide** | Configurar por carrera las horas de cada modalidad, los plazos de reporte y revisión, y el umbral de rezago. |
| **Por qué** | Las horas no son iguales para todos: 240 + 120 h en presencial, 256 + 144 h a distancia y 480 + 120 h en Odontología (Art. 334). Si el sistema fijara 240 h, estaría mal para la mitad de las carreras. |
| **Se comprueba cuando** | Dos carreras con valores distintos generan prácticas con horas requeridas distintas, y cambiar la configuración no altera las prácticas ya asignadas. |
| **Si faltara** | Habría que tocar el sistema cada vez que una carrera tenga otra carga horaria o cambie el reglamento. |

> [!NOTE]
> Las horas se **copian** a la práctica al asignarla. Así, un cambio de configuración a mitad de período no cambia las reglas a un estudiante que ya empezó.

### RF-14 · Tipo, subtipo y proyecto de vinculación

| | |
| --- | --- |
| **Qué pide** | Registrar si la práctica es laboral o comunitaria; si es laboral, su subtipo (práctica, pasantía, ayudantía de docencia o de investigación); si es comunitaria, su proyecto de vinculación. |
| **Por qué** | Cada tipo sigue reglas distintas: las ayudantías tienen tope semanal (Art. 341), la comunitaria no tiene tutor de entidad (Art. 337) y debe estar dentro de un proyecto aprobado (Art. 338, 347). Sin el tipo, el sistema no sabe qué regla aplicar. |
| **Se comprueba cuando** | Una práctica comunitaria sin proyecto no puede registrarse y una ayudantía activa el tope de 10 h. |
| **Si faltara** | El cierre pediría un informe de tutor de entidad que en el servicio comunitario **no existe**, y la práctica nunca podría cerrarse. |

---

## 3. Etapa 1 · Planificación

### RF-01 · Plan de actividades

| | |
| --- | --- |
| **Qué pide** | Que el estudiante registre su plan de actividades y lo envíe a revisión. |
| **Por qué** | El tutor académico debe orientar la elaboración del plan (Art. 336) y el tutor de la entidad monitorea las actividades **según ese plan** (Art. 337). Sin plan no hay contra qué comparar lo que se hace. |
| **Se comprueba cuando** | El plan enviado aparece como pendiente para el tutor académico. |
| **Si faltara** | Los reportes semanales no tendrían referencia y el tutor no podría decir si el estudiante se desvía. |

### RF-03 · Validar o devolver con observación

| | |
| --- | --- |
| **Qué pide** | Que el tutor académico valide o devuelva planes y reportes; devolver exige escribir una observación. |
| **Por qué** | El reglamento asigna al tutor el seguimiento y la **retroalimentación** (Art. 336). Una devolución sin motivo deja al estudiante sin saber qué corregir. |
| **Se comprueba cuando** | Devolver sin observación se rechaza, y la observación le llega al estudiante. |
| **Si faltara** | Volveríamos al ida y vuelta por correo que el sistema quiere eliminar. |

---

## 4. Etapa 2 · Ejecución semanal

### RF-02 · Reporte semanal con evidencias

| | |
| --- | --- |
| **Qué pide** | Que el estudiante registre cada semana sus actividades, horas y evidencias. |
| **Por qué** | La práctica sirve para aplicar lo aprendido y **sistematizar información** (Art. 11). El reporte semanal es la unidad mínima de avance: corta, revisable y con respaldo. |
| **Se comprueba cuando** | El reporte queda con fecha de registro, «en revisión», y sus horas no cuentan hasta validarse. |
| **Si faltara** | Las horas se declararían al final, sin respaldo, y el atraso se descubriría tarde. |

### RF-15 · Tope de 10 h en ayudantías

| | |
| --- | --- |
| **Qué pide** | Marcar para revisión los reportes de ayudantías que superen 10 h semanales. |
| **Por qué** | El reglamento fija una dedicación máxima de 10 h semanales para ayudantías (Art. 341). Pasarse puede invalidar esas horas. |
| **Se comprueba cuando** | Un reporte de 11 h en una ayudantía queda marcado; uno de 10 h, no. |
| **Si faltara** | Se validarían horas que el reglamento no permite y el problema aparecería recién al certificar. |

> [!NOTE]
> El sistema **marca**, no bloquea: el tutor decide. Es el mismo criterio que el caso límite de «horas poco razonables», ahora con un número concreto.

### RF-04 · Quién validó y cuándo

| | |
| --- | --- |
| **Qué pide** | Registrar en cada validación su autor y su fecha. |
| **Por qué** | Es el núcleo del problema: hoy **no se sabe quién validó qué ni cuándo**. Una hora validada sin autor no vale como prueba ante la dirección. |
| **Se comprueba cuando** | El 100 % de las validaciones tiene autor y fecha (CE-02). |
| **Si faltara** | El sistema sería otro repositorio de archivos, sin trazabilidad. |

### RF-08 · Participación del tutor de la entidad

| | |
| --- | --- |
| **Qué pide** | Que el tutor de la entidad, con cuenta propia, confirme los reportes de sus practicantes y registre su informe final. |
| **Por qué** | El reglamento le asigna monitorear las actividades y emitir un **informe final** (Art. 337), que el tutor académico usa para evaluar (Art. 339). Solo aplica a prácticas laborales. |
| **Se comprueba cuando** | Su confirmación y su informe quedan con autor y fecha, y no puede ver practicantes ajenos. |
| **Si faltara** | La evaluación dependería de un PDF por correo, justo lo que se quiere evitar. |

---

## 5. Etapa 3 · Seguimiento

### RF-05 · Horas validadas frente a requeridas

| | |
| --- | --- |
| **Qué pide** | Calcular las horas validadas y compararlas con las requeridas. |
| **Por qué** | Aprobar exige el **100 %** de las horas programadas (Art. 339) y no se acreditan fracciones (Art. 343). El estudiante necesita saber exactamente cuánto le falta. |
| **Se comprueba cuando** | El estudiante ve validadas, pendientes y requeridas en menos de 1 minuto (CE-03). |
| **Si faltara** | Seguirían sumándose a mano, con el error y el atraso que eso trae. |

### RF-06 · Estado de todas las prácticas

| | |
| --- | --- |
| **Qué pide** | Mostrar al coordinador el estado de todas las prácticas de su carrera. |
| **Por qué** | El docente responsable debe presentar el consolidado de cumplimiento (Art. 335) y Vinculación con la Sociedad monitorea el cumplimiento (Art. 331). Ninguno puede hacerlo sin una vista general. |
| **Se comprueba cuando** | El coordinador conoce el estado de cada práctica sin pedir archivos (CE-01). |
| **Si faltara** | El coordinador seguiría preguntando práctica por práctica. |

### RF-07 · Alertas

| | |
| --- | --- |
| **Qué pide** | Alertar por reportes no enviados, revisiones pendientes, horas rezagadas e incumplimientos reportados. |
| **Por qué** | El reglamento pide **seguimiento** (Art. 336), no solo registro. Una alerta a tiempo permite corregir; un dato visto al final solo confirma el fracaso. |
| **Se comprueba cuando** | Una práctica rezagada genera alerta antes del fin del período (CE-04). Ejemplo: 240 h en 16 semanas; en la semana 8 se esperan 120 h y la alerta salta por debajo de 96 h. |
| **Si faltara** | El estudiante descubriría en la última semana que le faltan 80 h y tendría que **repetir** la práctica (Art. 339). |

### RF-18 · Reporte de incumplimiento

| | |
| --- | --- |
| **Qué pide** | Que el tutor de la entidad reporte incumplimientos al tutor académico. |
| **Por qué** | Es una obligación expresa del tutor institucional: «reportar incumplimientos al tutor académico» (Art. 337). |
| **Se comprueba cuando** | El reporte genera una alerta al tutor académico y queda en la práctica con autor y fecha. |
| **Si faltara** | El aviso llegaría por teléfono o correo, sin registro, y no se podría reconstruir después. |

### RF-13 · Suspender, reanudar y cancelar

| | |
| --- | --- |
| **Qué pide** | Que el coordinador suspenda, reanude o cancele una práctica, con motivo obligatorio para suspender y cancelar. |
| **Por qué** | Las prácticas se interrumpen (enfermedad, cierre de la entidad, abandono). Sin estos estados, una práctica detenida parecería atrasada para siempre. |
| **Se comprueba cuando** | Una práctica suspendida conserva sus horas al reanudarse y una cancelada no admite cambios. |
| **Si faltara** | Las alertas de rezago se dispararían sobre prácticas que nadie espera que avancen. |

---

## 6. Etapa 4 · Evaluación y cierre

### RF-16 · Informe final del estudiante

| | |
| --- | --- |
| **Qué pide** | Que el estudiante presente su informe final de actividades y que el tutor académico lo revise o lo devuelva. |
| **Por qué** | El tutor académico debe «revisar el informe final de actividades presentado por el estudiante» (Art. 336). Es la voz del estudiante en el cierre. |
| **Se comprueba cuando** | El informe pasa por revisión igual que el plan, con observaciones si se devuelve. |
| **Si faltara** | Faltaría un documento que el reglamento exige y el cierre no sería válido. |

### RF-17 · Evaluación final con 70 %

| | |
| --- | --- |
| **Qué pide** | Que el tutor académico registre el desempeño en porcentaje; desde 70 % el resultado es «aprobada» y por debajo, «no aprobada». |
| **Por qué** | Lo dice el Art. 339: la evaluación la hace el tutor académico **considerando el informe externo**, y hace falta al menos 70 % para aprobar. |
| **Se comprueba cuando** | 70 % da «aprobada», 69 % da «no aprobada» y sin informe externo la evaluación se rechaza (CE-05). |
| **Si faltara** | El sistema podría «cerrar bien» una práctica reprobada. Es el error más caro: afecta la titulación. |

> [!WARNING]
> El límite es **inclusivo**: 70 % aprueba. Por eso la prueba de CE-05 usa justo 69 % y 70 %.

### RF-09 · Cierre con todos los requisitos

| | |
| --- | --- |
| **Qué pide** | Cerrar solo con 100 % de horas validadas, informe del estudiante revisado, informe externo y evaluación; el cierre guarda el resultado. |
| **Por qué** | Es la suma de las reglas anteriores en un solo control. El informe externo depende del tipo: tutor de la entidad en la laboral, proyecto de vinculación en la comunitaria (Art. 339). |
| **Se comprueba cuando** | Cualquier faltante rechaza el cierre e indica qué falta; una práctica «no aprobada» obliga a una práctica nueva. |
| **Si faltara** | El coordinador volvería a revisar documento por documento antes de cerrar. |

### RF-19 · Informe consolidado

| | |
| --- | --- |
| **Qué pide** | Generar el consolidado de la carrera con horas y resultado por estudiante y componente. |
| **Por qué** | El docente responsable presenta el consolidado al director (Art. 335), y el director certifica las horas **por componente** (Art. 340). |
| **Se comprueba cuando** | El coordinador obtiene el consolidado de un período sin armarlo a mano (CE-07). |
| **Si faltara** | El trabajo de seguimiento terminaría en una planilla manual justo antes de certificar. |

---

## 7. Transversales

### RF-10 · Historial inalterable

| | |
| --- | --- |
| **Qué pide** | Guardar cada cambio de estado de la práctica sin permitir modificarlo ni borrarlo. |
| **Por qué** | La certificación se emite con el expediente consolidado en el portafolio del estudiante (Art. 340). Un historial editable no prueba nada. |
| **Se comprueba cuando** | Se reconstruye quién, qué y cuándo de una práctica cerrada (CE-06) y editar un registro se rechaza. |
| **Si faltara** | Ante un reclamo, no habría forma de demostrar qué pasó. |

### RF-11 · Permisos por rol

| | |
| --- | --- |
| **Qué pide** | Que cada actor vea y haga solo lo que le corresponde. |
| **Por qué** | El reglamento reparte funciones distintas a cada actor (Art. 335–337) y los datos del estudiante son personales. El tutor de una entidad no debe ver a los practicantes de otra. |
| **Se comprueba cuando** | Cada acción fuera del rol se rechaza (por ejemplo, HU-07 #3). |
| **Si faltara** | Cualquiera podría validar horas, y la trazabilidad de RF-04 perdería sentido. |

---

## 8. Matriz de trazabilidad

| RF | Etapa | Actor principal | Historia | Norma | Criterio |
| --- | --- | --- | :---: | :---: | :---: |
| RF-01 | Planificación | Estudiante | HU-01 | Art. 336 | — |
| RF-02 | Ejecución | Estudiante | HU-02 | Art. 11 | — |
| RF-03 | Planificación | Tutor académico | HU-01, HU-03 | Art. 336 | — |
| RF-04 | Ejecución | Tutor académico | HU-03 | — | CE-02 |
| RF-05 | Seguimiento | Estudiante | HU-04 | Art. 334, 339 | CE-03 |
| RF-06 | Seguimiento | Coordinador | HU-05 | Art. 331, 335 | CE-01 |
| RF-07 | Seguimiento | Sistema | HU-06, HU-12 | Art. 336 | CE-04 |
| RF-08 | Ejecución | Tutor de la entidad | HU-07 | Art. 337 | — |
| RF-09 | Cierre | Coordinador | HU-08 | Art. 339 | CE-05 |
| RF-10 | Transversal | Sistema | HU-09 | Art. 340 | CE-06 |
| RF-11 | Transversal | Sistema | Todas | Art. 335–337 | — |
| RF-12 | Configuración | Coordinador | HU-04, HU-06 | Art. 334 | — |
| RF-13 | Seguimiento | Coordinador | HU-09 | — | — |
| RF-14 | Configuración | Coordinador | HU-02, HU-08 | Art. 332, 338, 341, 347 | — |
| RF-15 | Ejecución | Sistema | HU-02 | Art. 341 | — |
| RF-16 | Cierre | Estudiante, tutor académico | HU-10 | Art. 336 | — |
| RF-17 | Cierre | Tutor académico | HU-11 | Art. 339 | CE-05 |
| RF-18 | Seguimiento | Tutor de la entidad | HU-12 | Art. 337 | — |
| RF-19 | Cierre | Coordinador | HU-13 | Art. 335, 340 | CE-07 |

> RF-04 y RF-13 no salen de un artículo: salen del **problema** (trazabilidad y prácticas interrumpidas). Que un requisito no tenga artículo no lo hace menos necesario.

---

## 9. Qué cambió con el reglamento

| Cambio | Antes (v0.1.0) | Ahora (v0.2.0) | Base |
| --- | --- | --- | --- |
| Regla de aprobación | Cerrar con horas e informe final. | 100 % de horas, informes y evaluación con al menos 70 %; resultado aprobada o no aprobada. | Art. 339 |
| Informe del estudiante | No existía. | RF-16 y HU-10. | Art. 336 |
| Evaluación final | No existía. | RF-17 y HU-11. | Art. 339 |
| Servicio comunitario | Debía funcionar sin tutor de entidad, pero el cierre pedía su informe. | Usa el informe del proyecto de vinculación; el proyecto es obligatorio. | Art. 337–339, 347 |
| Subtipos laborales | No existían. | Práctica, pasantía, ayudantía de docencia o de investigación (RF-14). | Art. 332, 341 |
| Tope de ayudantías | «Horas poco razonables», sin número. | 10 h semanales (RF-15). | Art. 341 |
| Incumplimientos | Sin canal. | El tutor de la entidad los reporta (RF-18). | Art. 337 |
| Consolidado | No existía. | RF-19 y HU-13. | Art. 335, 340 |
| Horas por carrera | 240 + 120 h citadas del caso de estudio. | Tabla completa del Art. 334 como referencia de configuración. | Art. 334 |
| Fuera del alcance | — | Se suman selección de ayudantes, programa del período, IESS de pasantes, internados, Derecho y posgrado. | Art. 333, 335, 341, 345, 580, 581 |
