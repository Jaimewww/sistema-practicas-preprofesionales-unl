## Modelo de Datos Preliminar

### Entidades principales y sus relaciones

Para organizar la información de manera eficiente y segura, el sistema se basará en las siguientes entidades clave:

-   **Usuarios y Roles:** Gestiona el acceso, las credenciales y los permisos específicos de cada persona que entra al sistema (Estudiantes, Tutores académicos, Tutores de la entidad externa y Coordinadores).
-   **Carrera y Configuración:** Almacena las reglas particulares de cada programa de estudio, definiendo cuántas horas son obligatorias por modalidad y cuáles son los plazos permitidos.
-   **Entidad Receptora y Escenarios:** Registra la información de la empresa o institución donde se hace la práctica, vinculándola con los convenios legales vigentes.
-   **Práctica (Asignación):** Es la entidad central que conecta todas las partes; une al estudiante con su escenario de práctica, su tutor académico y el período en curso.
-   **Actividades y Evidencias:** Lleva el registro detallado de las horas que el estudiante reporta semanalmente, junto con los archivos adjuntos (planes o informes) que respaldan ese trabajo.
-   **Bitácora de Auditoría:** Funciona como un registro histórico automático que guarda absolutamente todos los cambios de estado y aprobaciones para garantizar la transparencia del proceso.

### Riesgos Técnicos y Estrategias de Mitigación

Al diseñar el sistema, se han identificado los siguientes riesgos operativos y técnicos, junto con las medidas para prevenirlos:

1.  **Riesgo: Acceso no autorizado a datos (Exposición cruzada)**
    -   *Descripción:* Al darle cuentas de usuario a tutores de empresas externas, existe el peligro de que puedan ver información de estudiantes que no están a su cargo.
    -   *Mitigación:* Se programarán filtros de seguridad estrictos directamente en las consultas a la base de datos. Esto garantizará que, al iniciar sesión, un tutor institucional solo reciba la información de los practicantes vinculados explícitamente a su perfil.

2.  **Riesgo: Saturación del almacenamiento por exceso de archivos**
    -   *Descripción:* La subida constante de evidencias semanales por parte de cientos de estudiantes podría llenar rápidamente la memoria del servidor.
    -   *Mitigación:* El sistema restringirá la subida de archivos exclusivamente a documentos PDF, y se establecerá un límite máximo de tamaño (por ejemplo, 5 MB por archivo) para controlar el peso de la información almacenada.

3.  **Riesgo: Alteración o pérdida de la trazabilidad (Historial)**
    -   *Descripción:* Si alguien logra borrar o modificar un registro antiguo sobre quién aprobó un documento, el sistema pierde su credibilidad y transparencia.
    -   *Mitigación:* La tabla de la Bitácora de Auditoría se configurará en modo de "solo escritura". Esto significa que el sistema bloqueará cualquier intento de editar o eliminar registros pasados, permitiendo únicamente agregar los nuevos eventos que vayan ocurriendo.