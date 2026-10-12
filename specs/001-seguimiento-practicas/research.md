# Research: Seguimiento de prácticas preprofesionales

**Input**: [plan.md](./plan.md) · **Spec**: [spec.md](./spec.md)

Decisiones de la fase 0. Cada tema resuelto durante la planificación queda con la decisión tomada, su justificación y las alternativas evaluadas. Los temas que el equipo todavía no decidió quedan al final, en **Temas abiertos**.

## Tema 1 · Tecnología del backend

**Decision**: Django (Python) como framework de backend.

**Rationale**: el problema central exige garantizar trazabilidad operativa estricta (quién, qué y cuándo), transiciones de estado controladas y control de acceso riguroso con actores externos a la institución. Django integra de forma nativa un sistema de RBAC muy probado, simplifica el almacenamiento seguro de documentos legales con `FileField` y automatiza el historial inalterable con librerías como `django-simple-history`, que es justamente la base de la trazabilidad pedida. Además coincide con el lineamiento tecnológico del proyecto real (Python, Django y PostgreSQL por DTI), lo que deja el proyecto académico alineado con su contexto de uso.

**Alternatives considered**:

| Criterio evaluado | NestJS (Node.js) | Spring Boot (Java) | Django (Python) |
| :--- | :--- | :--- | :--- |
| **Autenticación y roles (RBAC)** | Alta. Los Guards nativos permiten control granular por roles. | Alta. Spring Security gestiona contextos complejos de forma robusta. | Alta. Sistema nativo de permisos y grupos altamente consolidado. |
| **Gestión de evidencias** | Media. Exige integrar y configurar librerías de terceros. | Media. El manejo estándar de archivos es funcional pero más verboso. | Alta. Gestión nativa simplificada y segura con `FileField`. |
| **ORM y migraciones** | Alta. TypeORM o Prisma manejan relaciones complejas. | Alta. Integra Hibernate, estándar maduro y probado. | Alta. ORM propio reconocido por sus migraciones automáticas confiables. |
| **Auditoría (trazabilidad inmutable)** | Media. Obliga a desarrollar interceptores propios. | Media. Requiere configuración adicional, por ejemplo Hibernate Envers. | Alta. `django-simple-history` automatiza el historial inalterable de inmediato. |

## Tema 2 · Motor de base de datos

**Decision**: PostgreSQL.

**Rationale**: se adopta junto con Django por lineamiento del proyecto real y porque el sistema debe aislar la información por carrera y administrar cuentas de usuarios externos. PostgreSQL permite expresar el aislamiento directamente en las consultas y sostener las restricciones de integridad con las que se protege el historial.

**Alternatives considered**:

- **SQLite**: cómodo para pruebas locales, pero no reproduce el comportamiento de PostgreSQL en concurrencia, tipos ni integridad, así que no se usa como motor del sistema.
- **MySQL o MariaDB**: cumpliría lo básico, pero no aporta nada frente a PostgreSQL en este escenario y agrega una divergencia con el lineamiento del proyecto real.

## Tema 3 · Historial inalterable de cambios de estado

**Decision**: `django-simple-history` sobre el modelo de práctica, con tabla de historial de solo inserción.

**Rationale**: RF-10 y CE-06 exigen reconstruir el historial completo de una práctica (quién, qué y cuándo) y que ningún registro pueda modificarse ni borrarse. La librería crea y mantiene la tabla histórica sin lógica propia, y la regla de solo inserción se aplica sobre ella.

**Alternatives considered**:

- **Triggers en PostgreSQL**: potente, pero saca la regla del código de la aplicación y la vuelve difícil de revisar y de probar.
- **Tabla de auditoría escrita a mano con señales de Django**: control total, pero más código propio que mantener y más formas de olvidar un caso.

## Tema 4 · Autorización y aislamiento de datos

**Decision**: RBAC nativo de Django (usuarios, grupos y permisos) más filtrado obligatorio por consulta: cada usuario ve solo su información, el coordinador solo la de su carrera y el tutor de entidad solo a sus practicantes.

**Rationale**: RF-11 y la restricción de privacidad del spec exigen que cada actor vea y haga solo lo que le corresponde, y HU-07 caso 3 exige rechazar el acceso de un tutor de entidad a una práctica que no es suya. Filtrar en la capa de datos evita que una vista nueva se olvide de aplicar la regla.

**Alternatives considered**:

- **Permisos por objeto con `django-guardian`**: permite reglas muy finas, pero agrega filas de permisos por objeto y una dependencia más para un aislamiento que ya es expresable con consultas.
- **Filtrar solo en las vistas**: menos infraestructura, pero cualquier endpoint nuevo puede exponer datos de otra carrera; se descarta por riesgo de fuga.

## Tema 5 · Gestión de evidencias

**Decision**: evidencias con `FileField`, restringidas a PDF y con un tamaño máximo de 5 MB por archivo, versionadas: cada devolución conserva el archivo y la observación anteriores.

**Rationale**: el caso límite del spec pide conservar cada versión y cada observación cuando una evidencia se devuelve varias veces. El límite de formato y tamaño controla el crecimiento del almacenamiento, que es el riesgo de saturación identificado durante el diseño.

**Alternatives considered**:

- **Almacenamiento externo (S3 o MinIO)**: escala mejor, pero agrega un servicio y credenciales que el MVP no necesita.
- **Sin límite de tipo ni tamaño**: elimina una validación, pero deja el almacenamiento del servidor a merced de cualquier archivo subido.

## Tema 6 · Cálculo de horas y detección de rezago

**Decision**: las horas esperadas a una fecha son `horas requeridas × (días transcurridos ÷ días del período)`. Hay rezago cuando las horas validadas **más las horas en revisión** quedan por debajo del umbral de rezago de la carrera (80 % por defecto, configurable).

**Rationale**: definido en HU-06 y confirmado en la sesión de clarify. Contar también las horas en revisión evita alertar a un estudiante que reportó a tiempo y solo está esperando la validación de su tutor.

**Alternatives considered**:

- **Contar solo las horas validadas**: castigaría al estudiante por la demora del tutor; descartado en clarify.
- **Umbral fijo en el código**: contradice RF-12, que exige que el umbral se configure por carrera.

## Tema 7 · Cómo se separan las prácticas laboral y comunitaria

**Decision**: son prácticas separadas, cada una con su tipo, su tutor, su plan y su cierre. Las horas requeridas se **copian** de la configuración de carrera y modalidad en el momento de asignar la práctica.

**Rationale**: confirmado en clarify. Copiar las horas en lugar de referenciarlas evita que un cambio posterior de la configuración altere una práctica ya en curso y quite o agregue horas a un estudiante que ya venía cumpliendo.

**Alternatives considered**:

- **Una práctica con dos componentes**: obliga a duplicar tutores, planes y cierres dentro de un mismo registro y complica cada regla de avance.

## Temas abiertos

Ninguno de estos tres bloquea el modelo de datos, pero sí conviene cerrarlos antes de generar `tasks.md`.

| # | Tema | Camino A | Camino B |
| --- | --- | --- | --- |
| 1 | Stack del frontend | Plantillas de Django: sin API, menos piezas, un solo despliegue | SPA con API REST (Django REST Framework): mejor interacción, API que hay que versionar y mantener |
| 2 | Generación de alertas | Comando de gestión con cron: sin infraestructura extra, suficiente para la escala del MVP | Celery con Redis: más robusto para reintentos y volumen, agrega dos servicios |
| 3 | Escala del MVP | [NEEDS CLARIFICATION] ¿cuántas carreras, estudiantes y prácticas concurrentes debe soportar? | — |
