# Referencia visual: SIAAF

El sistema de seguimiento de prácticas se concibe como un módulo del sistema académico de la UNL (SIAAF). Durante el prototipado, su navegación, su terminología y sus datos de estudiantes se contrastan con ese sistema ([spec, sección 6](../specs/001-seguimiento-practicas/spec.md)). Este documento recoge lo observado en el SIAAF para que el prototipo lo respete.

**Fuente:** capturas de `siaaf.unl.edu.ec` tomadas el 2026-10-20 con una cuenta de estudiante. Se recortó la ventana del navegador y se taparon los datos personales (foto, nombre, correo y nombres de docentes).

| Captura | Pantalla |
| --- | --- |
| [01-inicio.png](referencias/siaaf/01-inicio.png) | Menú principal del SIAAF |
| [02-modulo-academico.png](referencias/siaaf/02-modulo-academico.png) | Inicio del módulo académico |
| [03-listado-tutorias.png](referencias/siaaf/03-listado-tutorias.png) | Listado de tutorías (patrón de lista) |
| [04-evaluacion-docente.png](referencias/siaaf/04-evaluacion-docente.png) | Inicio del módulo de evaluación docente |
| [05-detalle-persona.png](referencias/siaaf/05-detalle-persona.png) | Detalle de una persona (patrón de vista de detalle) |
| [06-formulario-persona.png](referencias/siaaf/06-formulario-persona.png) | Modificar datos personales (patrón de formulario) |
| [07-formulario-persona-pie.png](referencias/siaaf/07-formulario-persona-pie.png) | Final del mismo formulario: carga de archivo, botones y pie de página |

---

## 1. Ubicación del módulo

Las prácticas preprofesionales se ubican como una sección del **módulo académico** (`/academico/`), junto a «Tutorías». No forman un módulo independiente en el menú principal.

El tutor de la entidad receptora, que es externo a la UNL, entra con una cuenta propia y ve este mismo marco con un menú reducido a sus practicantes (decisión del 2026-10-20).

## 2. Marco de cada módulo

| Elemento | Cómo se ve en el SIAAF |
| --- | --- |
| Barra lateral | Fija a la izquierda, fondo blanco. |
| Bloque del logo | Arriba de la barra lateral, con un color por módulo: rojo en el menú principal y azul en Académico y en Evaluación. |
| Menú del módulo | Empieza con «← Menú Principal» y «Tablero»; siguen las secciones, con flecha (›) cuando tienen submenú. |
| Barra superior | Blanca: ícono ☰, nombre del módulo («Módulo de Gestión Académico»), pantalla completa, campana de notificaciones y usuario (foto y nombre en mayúsculas). |
| Título de página | Grande, en gris claro y peso ligero («Módulo académico», «Bienvenido»). |
| Ubicación | Botón redondeado a la derecha del título, con ícono de casa («⌂ Curricular», «⌂ Inicio»). |
| Fondo | Gris claro; el contenido va en tarjetas blancas. |
| Tarjetas | Blancas, con un borde superior celeste. Algunas tienen la cabecera de color: naranja en «Manuales» y azul en «Listas de reproducción». |
| Botón principal | Azul oscuro, con ícono a la izquierda («⊕ Ir a perfil»). |
| Mensajes | Franja verde clara para avisos de éxito. |
| Accesibilidad | Botón rojo fijo en la esquina inferior izquierda. |
| Pie de página | Franja azul oscuro a lo ancho del contenido, con el texto centrado «2025 © Sistema de Información Académico, Administrativo y Financiero» y el enlace «Universidad Nacional de Loja». A la derecha, un botón cuadrado para volver arriba. |
| Tipografía | Sans geométrica, parecida a Poppins. |

## 3. Patrón de lista

El «Listado de tutorías» es el patrón que siguen las listas del prototipo (reportes pendientes, prácticas de una carrera, alertas).

- **Filtros** en una fila, sobre la tabla: desplegables con la etiqueta encima y la opción «--Todos--» por defecto (Periodos académicos, Asignaturas, Tutoría recibida, Tutoría tipo).
- **Controles de tabla**: «Mostrar [10] registros» a la izquierda y «Buscar:» a la derecha.
- **Columnas** ordenables (↑↓ junto al encabezado).
- **Celdas compuestas**: varios datos en formato **Etiqueta**: valor dentro de una misma celda (Fecha, Horario, Duración, Modalidad).
- **Etiquetas de estado** de color, en mayúsculas o versalitas:
  - verde para el tipo (`ASIGNATURA`);
  - amarillo para la modalidad (`Virtual`, `Presencial`);
  - rojo `NO` y verde `SI` para una respuesta binaria.

## 4. Patrón de vista de detalle

El detalle de una persona (`/core/persona/detalle/<id>`) es el patrón para las vistas de detalle del prototipo (una práctica, un reporte semanal).

- **Título de página**: el nombre del registro, en mayúsculas, gris claro y peso ligero (`APELLIDO APELLIDO NOMBRE NOMBRE`).
- **Ubicación**: ruta completa en el botón de la derecha («⌂ Inicio › Persona»).
- **Pestañas** en una franja gris, encima del contenido («Información Personal»); la activa tiene fondo blanco y texto azul.
- **Tarjeta por grupo de datos**, con cabecera gris azulada, título a la izquierda («Datos personales») y un botón pequeño con forma de píldora a la derecha, verde azulado y con ícono («✎ Editar»).
- **Tabla de dos columnas**: etiqueta en negrita a la izquierda y valor a la derecha, con líneas finas entre filas.
- **Campos vacíos**: se muestran sin valor, sin guion ni «No registrado».
- **Valores sí/no**: con ícono (✖ para «no»).
- La tarjeta ocupa unos dos tercios del ancho; el resto queda vacío.

## 5. Patrón de formulario

«Modificar datos personales» (`/core/persona/editar/<id>?next=/core/persona/detalle/<id>`) es el patrón para los formularios del prototipo (plan de actividades, reporte semanal, validación).

- **Navegación**: el formulario se abre desde el botón «Editar» del detalle y lleva un parámetro `next` para volver al detalle al guardar.
- **Contenedor**: un panel blanco con el título en negrita y gris azulado oscuro («Modificar datos personales»), separado de los campos por una línea punteada. No tiene cabecera de color.
- **Campos**: una sola columna, a todo el ancho y con poco espacio entre campos.
- **Etiqueta**: arriba del campo, en texto chico y regular, terminada en dos puntos («Primer apellido:»).
- **Obligatorio**: prefijo `(*)` en rojo antes de la etiqueta.
- **Ayuda**: una línea entre la etiqueta y el campo, en el mismo color de la etiqueta, con el formato esperado y un ejemplo («Ingrese la fecha en el formato DD/MM/AAAA (ejm: 01/01/2000)»).
- **Campos condicionales**: el campo sigue visible y la ayuda dice cuándo completarlo («Por favor ingrese este dato solo si su Nacionalidad NO es Ecuatoriana»).
- **Desplegables**: nativos, con la opción «-- Seleccione --» cuando no hay valor.
- **Fondo de los campos**: casi todos los que ya tienen valor aparecen en gris y los vacíos en blanco. La captura no permite saber si los grises están bloqueados.
- **Fechas**: formato `DD/MM/AAAA`.
- **Carga de archivos**: campo de archivo nativo del navegador, sin zona para arrastrar. Arriba va la ayuda con el tipo de archivo y lo que debe contener («Subir un archivo PDF que contenga su documento de identificación y el certificado de votacion actualizados.»). Antes del botón se ve el texto «None», un valor vacío que el sistema muestra por error; el prototipo no lo copia.
- **Acciones**: dos botones centrados debajo del último campo, dentro del panel. «Guardar» es azul oscuro, con texto blanco e ícono de disquete. «Cancelar» es gris claro, con texto azul e ícono de prohibido.

## 6. Terminología

| Dato | Formato en el SIAAF |
| --- | --- |
| Periodo académico | `MAR.26-AGO.26 GRADO` |
| Carrera y ciclo | `FEIRNNR - COMPUTACIÓN - PRESENCIAL - Régimen 2019 - CICLO 4A` |
| Personas | Apellidos primero, todo en mayúsculas: `APELLIDO APELLIDO NOMBRE NOMBRE` |
| Usuario | Correo institucional `@unl.edu.ec` |
| Rol docente | «Docente» |
| Inicio de módulo | «Tablero» |

## 7. Pendientes

| Pendiente | Por qué importa |
| --- | --- |
| Vista de docente y de coordinador | Las capturas solo muestran la vista de estudiante; se espera la misma estructura con otro menú. |

## 8. Referencia secundaria: formulario de GLPI

El sistema de Servicios de TI (GLPI, `serviciosti.unl.edu.ec`) es otro producto con otra estética, así que **no** se toma su aspecto visual (colores, cabecera, botones). Los formularios siguen el patrón del SIAAF (sección 5). De su formulario de incidente ([01-formulario-incidente.png](referencias/glpi/01-formulario-incidente.png)) se toma solo una idea opcional:

- **Zona para arrastrar archivos** con el límite de tamaño visible («Archivo(s) (2 MiB max)»). El SIAAF usa el campo de archivo nativo (sección 5). Como el reporte semanal puede llevar varias evidencias, el prototipo puede proponer esta zona, siempre con la apariencia del SIAAF.
