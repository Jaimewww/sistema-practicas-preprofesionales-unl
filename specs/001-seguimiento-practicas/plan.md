## Papel del Backend

El backend no es un simple almacén, es el motor de reglas de negocio[cite: 9]:

*   **Máquina de Estados y Transiciones:** Controlar el ciclo de vida de la práctica y de los documentos (`asignada`, `en curso`, `en revisión`, `cerrada`)[cite: 9].
*   **Reglas de Negocio (Horas y Carreras):** Validar horas acumuladas contra la configuración específica de cada carrera (ej. 240h laborales vs 480h en Medicina)[cite: 7, 9].
*   **RBAC y Aislamiento de Datos:** Garantizar que el tutor institucional solo vea a sus practicantes y que la DVS o coordinadores accedan a datos consolidados[cite: 4, 9].
*   **Auditoría Inmutable:** Mantener un historial (Bitácora de auditoría) de quién aprueba, devuelve o modifica cada evidencia[cite: 9].
*   **Tareas Programadas (Cron Jobs):** Evaluar plazos y horas para emitir alertas tempranas antes del incumplimiento[cite: 5, 9].