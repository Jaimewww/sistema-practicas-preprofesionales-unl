# 0005. Evidencias en PDF, de hasta 5 MB y versionadas

- **Estado**: Aceptada
- **Fecha**: 2026-10-11
- **Decisores**: equipo (fase 0 de la planificación)

## Contexto

Cuando una evidencia se devuelve varias veces hay que conservar cada versión y cada observación. El almacenamiento del servidor es un riesgo de saturación identificado en el diseño. Origen: [research.md, Tema 5](../../specs/001-seguimiento-practicas/research.md), RNF-05.

## Decisión

Guardar las evidencias con **`FileField`**, restringidas a **PDF** y a **5 MB por archivo**, versionadas: cada devolución conserva el archivo y la observación anteriores. El prototipo ya aplica la regla en `backend/apps/prototipo/forms.py` (`MAX_EVIDENCIA_BYTES`, `_is_pdf` con firma `%PDF-`), pero no guarda el archivo, solo su nombre.

## Alternativas consideradas

- **Almacenamiento externo (S3 o MinIO)**: escala mejor, pero agrega un servicio y credenciales que el MVP no necesita.
- **Sin límite de tipo ni tamaño**: elimina una validación, pero deja el almacenamiento a merced de cualquier archivo subido.

## Consecuencias

- **Positivas**: control del crecimiento del almacenamiento; superficie de carga de archivos acotada.
- **Negativas o costos**: el volumen de archivos debe respaldarse (RNF-06) y servirse sin ejecutar contenido.
- **Pendiente**: la persistencia real del archivo no está en #76 ni #78; la validación de tipo y tamaño debe repetirse en el serializer.

## Referencias

- [research.md, Tema 5](../../specs/001-seguimiento-practicas/research.md)
- [seguridad.md](../seguridad.md)
