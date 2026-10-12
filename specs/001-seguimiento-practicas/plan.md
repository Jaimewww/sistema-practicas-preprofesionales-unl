## Papel del Backend

El backend actuará como el núcleo lógico del sistema. Su función principal no es solo guardar datos, sino asegurar que todas las reglas del proceso de prácticas preprofesionales se cumplan de forma automática y segura. Sus responsabilidades principales son:

- **Gestión del ciclo de vida:** Controlar de forma estricta los estados por los que pasa una práctica (`asignada`, `en curso`, `en revisión final`, `cerrada`), asegurando que el proceso avance en el orden correcto y no se omitan pasos.
- **Validación de normativas (Horas por carrera):** Calcular automáticamente las horas validadas del estudiante y compararlas con los requisitos específicos de su carrera (por ejemplo, diferenciando entre las 240 horas laborales estándar y exigencias mayores en áreas como Salud).
- **Control de acceso y privacidad:** Garantizar que cada usuario vea únicamente la información que le corresponde a su rol. Por ejemplo, asegurar que un tutor de la entidad externa solo tenga acceso a los datos de sus propios practicantes, evitando que vea información de otros estudiantes.
- **Registro de auditoría (Historial):** Mantener una bitácora automática e inalterable que registre quién aprueba, devuelve o modifica cualquier documento y en qué fecha lo hizo, para garantizar la transparencia del proceso.
- **Generación de alertas preventivas:** Monitorear continuamente los plazos de entrega y el avance de horas (mediante tareas programadas) para enviar notificaciones automáticas a los involucrados antes de que ocurra un atraso.