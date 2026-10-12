## Modelo de Datos Preliminar

### Entidades principales[cite: 9]
*   **Usuario / Rol:** Manejo de autenticación para Estudiantes, Tutores académicos, Tutores institucionales, Coordinadores.
*   **Carrera y Configuración:** Define las horas requeridas y umbrales por modalidad.
*   **Entidad Receptora y Escenario:** Almacena la institución externa y el convenio vigente.
*   **Programa y Asignación (Práctica):** Vincula al estudiante, el escenario, el tutor y el período.
*   **Actividad y Evidencia:** El registro de horas (asistencia) y los archivos de respaldo (planes, informes).
*   **Bitácora de Auditoría (Historial):** Log inmutable de cambios de estado.

### Riesgos Técnicos y Mitigación

1.  **Riesgo: Exposición cruzada de datos (Tutores Externos)**
    *   *Mitigación:* Implementar validaciones a nivel de QuerySet en el ORM para asegurar que el tutor institucional solo pueda consultar registros vinculados a su ID.
2.  **Riesgo: Saturación de almacenamiento por evidencias**
    *   *Mitigación:* Limitar formatos permitidos a PDF ligeros y establecer cuotas de tamaño en el modelo `FileField` del backend.
3.  **Riesgo: Modificación indebida del historial (Pérdida de trazabilidad)**
    *   *Mitigación:* La tabla de Bitácora de Auditoría debe ser *append-only* (solo inserciones), bloqueando actualizaciones o borrados desde el panel de administración o APIs.