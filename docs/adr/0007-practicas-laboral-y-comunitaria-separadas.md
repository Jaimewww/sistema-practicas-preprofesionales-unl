# 0007. Prácticas laboral y comunitaria como registros separados

- **Estado**: Aceptada
- **Fecha**: 2026-10-11
- **Decisores**: equipo (clarify)

## Contexto

Una práctica laboral y una comunitaria tienen tutores, planes y cierres distintos; el servicio comunitario funciona incluso sin tutor de entidad (Art. 337). Las horas requeridas se configuran por carrera y modalidad y pueden cambiar. Origen: [research.md, Tema 7](../../specs/001-seguimiento-practicas/research.md).

## Decisión

Son **prácticas separadas**, cada una con su tipo, su tutor, su plan y su cierre. Las horas requeridas se **copian** de la configuración de carrera y modalidad al asignar la práctica (`Practica.horas_requeridas` en [data-model.md](../../specs/001-seguimiento-practicas/data-model.md)).

## Alternativas consideradas

- **Una práctica con dos componentes**: obliga a duplicar tutores, planes y cierres dentro de un registro y complica cada regla de avance.

## Consecuencias

- **Positivas**: un cambio posterior de la configuración no altera una práctica en curso; cada práctica tiene un ciclo de vida independiente.
- **Negativas o costos**: hay dos registros por estudiante que consolidar en el informe del coordinador.

## Referencias

- [research.md, Tema 7](../../specs/001-seguimiento-practicas/research.md)
- [data-model.md](../../specs/001-seguimiento-practicas/data-model.md)
