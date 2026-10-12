## Análisis de alternativas de Backend

El problema central exige una fuerte trazabilidad (quién, qué, cuándo), gestión de estados y control de acceso robusto para múltiples roles (incluyendo entidades externas)[cite: 4, 5, 8].

| Criterio evaluado | NestJS (Node.js) | Spring Boot (Java) | Django (Python) |
| :--- | :--- | :--- | :--- |
| **Autenticación y roles (RBAC)** | Alta. Guards facilitan el control. | Alta. Spring Security es muy capaz. | Alta. Sistema de permisos y grupos nativo muy maduro. |
| **Gestión de evidencias** | Media. Requiere integraciones externas. | Media. Manejo estándar. | Alta. Manejo nativo (`FileField`) seguro y simplificado. |
| **ORM y migraciones** | Alta. TypeORM/Prisma. | Alta. Hibernate. | Alta. El ORM de Django es referente en la industria. |
| **Auditoría (Trazabilidad inmutable)** | Media. Interceptores manuales. | Media. Hibernate Envers. | Alta. `django-simple-history` automatiza el historial inmutable. |

**Decisión y justificación:**
Se selecciona **Django** con PostgreSQL. El sistema requiere aislar datos por carrera y gestionar cuentas para usuarios externos (tutores institucionales), lo que exige filtros de seguridad muy estrictos para evitar fugas de información. Django ofrece un RBAC nativo comprobado, facilita el almacenamiento estructurado de documentos legales y automatiza la trazabilidad (auditoría), cubriendo el núcleo del "Papel del backend" definido en los requisitos[cite: 9].