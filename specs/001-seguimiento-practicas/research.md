## Análisis de alternativas de Backend

La problemática central del sistema demanda garantizar una estricta trazabilidad operativa (registrar quién, qué y cuándo), una gestión segura de las transiciones de estado de cada práctica y un control de acceso riguroso para múltiples actores, incluyendo usuarios externos a la institución. 

A continuación, se evalúan tres tecnologías de backend bajo estos criterios fundamentales:

| Criterio evaluado | NestJS (Node.js) | Spring Boot (Java) | Django (Python) |
| :--- | :--- | :--- | :--- |
| **Autenticación y roles (RBAC)** | Alta. El uso de Guards nativos permite un control granular por roles. | Alta. Spring Security proporciona una gestión robusta en contextos complejos. | Alta. Cuenta con un sistema nativo de permisos y grupos altamente consolidado. |
| **Gestión de evidencias** | Media. Demanda la integración y configuración de librerías de terceros. | Media. Su manejo de archivos estándar es funcional, pero más verboso. | Alta. Gestión nativa simplificada y segura mediante el uso de `FileField`. |
| **ORM y migraciones** | Alta. Herramientas como TypeORM o Prisma gestionan eficientemente relaciones complejas. | Alta. Integra Hibernate, un estándar maduro y probado en la industria. | Alta. Integra un ORM propio reconocido por sus migraciones automáticas confiables. |
| **Auditoría (Trazabilidad inmutable)** | Media. Requiere el desarrollo manual de interceptores personalizados. | Media. Necesita configuración adicional mediante módulos como Hibernate Envers. | Alta. Librerías como `django-simple-history` automatizan el historial inmutable de manera inmediata. |

**Decisión y justificación:**

Tras analizar las alternativas, se determina utilizar **Django** acompañado de **PostgreSQL** como motor de base de datos. 

Dado que el sistema debe aislar la información por carrera y administrar cuentas para usuarios externos (tutores institucionales), resulta imperativo contar con filtros de seguridad estrictos a nivel de base de datos para prevenir cualquier fuga de información. Django sobresale en este escenario al integrar de forma nativa un sistema de control de acceso basado en roles (RBAC) exhaustivamente probado. Asimismo, esta tecnología simplifica el almacenamiento seguro de los documentos legales y automatiza la creación de historiales de auditoría inalterables, satisfaciendo a cabalidad el papel estructural y de seguridad exigido para el backend del proyecto.