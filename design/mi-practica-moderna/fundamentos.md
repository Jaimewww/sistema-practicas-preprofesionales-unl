# Mi práctica: fundamentos del diseño

Estilo: **Calma precisa**. Es la línea de las interfaces de producto actuales que se toman en serio la densidad de información,
como Linear y Vercel Geist: neutros casi sin color, un solo acento, bordes finos en lugar de sombras, números alineados y movimiento mínimo.
En esta pantalla todo tiene que justificarse con una pregunta del estudiante; si no responde ninguna, se va.

La pantalla responde cuatro preguntas, en este orden:

1. ¿Estoy bien o estoy atrasado? (estado)
2. ¿Qué tengo que hacer ahora? (acción)
3. ¿Cómo voy semana a semana? (historia)
4. ¿Quién decide y cuándo vence cada cosa? (contexto)

## Fuentes

| Id | Fuente | Qué tomamos |
| --- | --- | --- |
| F1 | Linear, "A calmer interface for a product in motion" (linear.app/now/behind-the-latest-design-refresh) | "Don't compete for attention you haven't earned": no todo pesa igual; lo central a la tarea manda |
| F2 | Linear, "How we redesigned the Linear UI" (linear.app/now/how-we-redesigned-the-linear-ui) | Menos ruido visual en barras, pestañas y paneles; colores en LCH y poco azul en los neutros |
| F3 | Vercel Geist, Colors (vercel.com/geist/colors) | Escalas con un uso por paso (fondo, hover, borde, texto); colores semánticos con un solo significado |
| F4 | Vercel Geist, Terminal (vercel.com/geist/terminal) | Tres grises para separar texto principal, secundario y detalle |
| F5 | Apple HIG, Layout (developer.apple.com/design/human-interface-guidelines/layout) | Ordenar por importancia: lo principal arriba y al inicio de la lectura |
| F6 | Stephen Few, Bullet Graph Design Specification (perceptualedge.com, 2005) | La gráfica de bala reemplaza medidores y anillos: medida, objetivo y rangos cualitativos en poco espacio |
| F7 | Kivetz, Urminsky y Zheng, "The Goal-Gradient Hypothesis Resurrected", J. Marketing Research 43(1), 2006 | El esfuerzo aumenta cuando la meta se ve cerca, siempre que el progreso mostrado sea honesto |
| F8 | W3C, WCAG 2.2, SC 1.4.1 Use of Color | El color nunca es el único medio para transmitir un estado |
| F9 | Leyes de UX (Hick, Fitts, Von Restorff, Zeigarnik), uxdesigninstitute.com/blog/laws-of-ux | Menos opciones aceleran la decisión; los objetivos importantes van grandes y cerca; lo distinto se recuerda; lo pendiente se recuerda |

## Color: cada color tiene un único significado

La regla general: **el color significa algo o no aparece.** El fondo y la estructura van en grises, y el color se reserva
para dos cosas: *lo suyo* (sus horas, su acción) y *el estado* (validado, en espera, devuelto). (F1, F3)

| Rol | Valor | Contraste | Por qué este color |
| --- | --- | --- | --- |
| Fondo de lienzo | `#F6F7F9` | — | Un gris apenas frío, para que las superficies blancas se separen sin sombras (F2, F3). El frío viene del azul UNL, pero muy rebajado para que no tiña la lectura (F2) |
| Superficie | `#FFFFFF` | — | Donde vive el contenido. El blanco marca lo legible y el gris lo que es solo fondo |
| Tinta principal | `#0E1621` | 18.2:1 | Casi negro con un toque azul: contraste máximo sin el negro puro, que encandila sobre blanco |
| Tinta secundaria | `#4A5361` | 7.8:1 | Etiquetas y texto de apoyo. Es el segundo de tres grises de jerarquía (F4) |
| Tinta terciaria | `#6A7280` | 4.8:1 | Fechas y metadatos. Llega a AA para texto chico; es lo más claro que se permite para un texto que hay que poder leer |
| Línea | `#E4E7EC` | — | Bordes de un píxel en lugar de sombras: separan sin pesar (F2) |
| **Acento UNL** | `#00509E` | 8.0:1 | Viene del SIAAF real, así que conserva la identidad institucional. Se usa **solo** para la acción principal, sus horas validadas, el foco y lo seleccionado. Al ser el único color saturado en reposo, el ojo va primero a él (Von Restorff, F9) |
| Acento en revisión | `#8DB4DC` | (gráfico) | Mismo tono que el acento pero más claro: son las *mismas horas*, todavía sin certeza. Si fuera otro color se leería como otra cosa |
| Rojo | `#B42318` sobre `#FEF0EE` | 5.9:1 | Solo para lo que **pide acción**: la semana devuelta y el rezago. Si el rojo aparece en otros lugares deja de servir como alarma |
| Ámbar | `#8A5300` sobre `#FFF5DB` | 5.8:1 | Para lo que **está en espera de otra persona**. Indica que no se debe alarmar ni actuar. Es ámbar oscuro porque el amarillo puro no alcanza contraste como texto |
| Verde | `#1E7B34` sobre `#EBF6EE` | 4.8:1 | Validado. Aparece chico y desaturado: el éxito confirma, no compite con lo pendiente (F1) |
| Gris futuro | `#EEF0F3` | — | Semanas que todavía no ocurren. Deben verse, para que se entienda cuánto falta (F7), pero en el plano más bajo |

Todo estado lleva **color + ícono + texto**, sin excepciones (F8): ✓ validada, reloj en revisión, flecha de vuelta devuelta, línea punteada en curso.

## Tipografía

| Decisión | Por qué |
| --- | --- |
| Poppins solo en cifras y títulos | Es la tipografía institucional del SIAAF, así que la identidad se mantiene donde se nota |
| `system-ui` para el texto corrido | Tiene mejor altura de x y hinting a 14–15 px que Poppins, que es geométrica y se lee mejor en tamaños grandes |
| `tabular-nums` en todo número | Para que 15 h, 16 h y 105 h queden alineadas y se puedan comparar en columna |
| Escala 12 / 13 / 15 / 20 / 28 / 48 | Pocos tamaños con saltos claros: cada rol (metadato, etiqueta, cuerpo, sección, título, cifra clave) se reconoce sin dudar |
| Letter-spacing negativo en tamaños grandes | Las tipografías se dibujan para tamaño de texto; en grande el espaciado se abre y se ve desarmado |

## Espacio y forma

| Decisión | Por qué |
| --- | --- |
| Cuadrícula de 4 px (4, 8, 12, 16, 24, 32, 48) | Un ritmo único hace que todo se vea alineado aunque nadie mida (F3) |
| Radio 12 en tarjetas, 8 en controles, píldora en estados | Radio interior = radio exterior − padding: las curvas anidadas se ven paralelas |
| Bordes y no sombras; una sola elevación | La única sombra es la del panel de acción, porque es lo único que "flota" sobre el resto (F1, F5) |
| Ancho máximo de 1200 px | Con más ancho, las líneas de texto pasan de ~75 caracteres y la mirada se pierde |

## Elemento por elemento

| # | Elemento | Pregunta que responde | Por qué tiene esta forma |
| --- | --- | --- | --- |
| 1 | Barra superior mínima: marca, secciones y avatar | ¿Dónde estoy? | Sin buscador ni atajos: con 16 semanas no hay nada que buscar. Cada control que no se usa suma ruido (F1, F9-Hick) |
| 2 | **Frase de estado** ("Está 3 h por debajo del mínimo") | ¿Estoy bien? | Es lo primero que se lee (F5). Una frase en lenguaje llano se entiende antes que un porcentaje; el número la acompaña, no la reemplaza |
| 3 | **Gráfica de bala** de horas: validadas, en revisión, marca de lo esperado, banda del mínimo y meta de 240 | ¿Cuánto me falta y dónde debería estar? | Few la diseñó para reemplazar anillos y medidores: un anillo obliga a comparar ángulos, que el ojo estima mal, y ocupa mucho espacio (F6). La barra horizontal se lee como una regla |
| 4 | **Panel "Siguiente paso"** con un solo botón primario | ¿Qué hago ahora? | Una acción en lugar de tres decide más rápido (F9-Hick). Es el botón más grande y está donde termina la lectura (F9-Fitts). Es el único elemento con sombra (F1) |
| 5 | Observación del tutor **textual**, con nombre y fecha | ¿Por qué me lo devolvieron? | Citarla sin parafrasear evita interpretaciones y genera confianza; el nombre deja claro a quién preguntar |
| 6 | Proyección ("pasaría a 87 %") | ¿Vale la pena corregirlo ya? | El efecto de gradiente de meta: ver la meta más cerca da impulso (F7). Es un cálculo real a partir de las horas reportadas, no una promesa inflada |
| 7 | **Tira de 16 semanas** con forma e ícono por estado | ¿Cómo vengo? | Lo pendiente se recuerda (F9-Zeigarnik). Mostrar las semanas futuras deja ver el total del camino (F7). Cada estado se distingue también sin color (F8) |
| 8 | Sección "No tiene que hacer nada" para la semana 7 | ¿Me falta algo más? | Separar lo que espera de otra persona de lo que depende del estudiante quita ansiedad y evita mensajes innecesarios al tutor |
| 9 | Equipo, con **qué decide cada uno** | ¿A quién le escribo? | El tutor académico valida y la tutora de la entidad confirma asistencia. Saber quién hace qué evita consultas mal dirigidas |
| 10 | Fechas como cuenta regresiva ("en 6 días") | ¿Cuándo vence? | Los días restantes se procesan más rápido que una fecha que hay que restar mentalmente; la fecha exacta queda al lado como respaldo |
| 11 | Movimiento de 160 ms, solo al cambiar de estado | — | El movimiento explica un cambio y no decora; con `prefers-reduced-motion` no hay ninguno |

## Qué se quitó de la versión anterior y por qué

| Quitado | Motivo |
| --- | --- |
| "Hola, Andrea" como título | El saludo no responde ninguna pregunta y ocupaba el lugar más visible (F5). El título pasa a ser el estado |
| Anillo de progreso | Ángulos difíciles de comparar y mucho espacio para un solo dato (F6) |
| Degradados y logo con degradado | Era decoración sin significado: el color solo aparece cuando significa algo |
| Buscador con Ctrl K | No hay una colección que buscar |
| Rojo en el botón "Corregir" | El rojo es para el estado, no para la acción: la acción va siempre en el acento. Si no, dos llamados compiten |
| Cuatro tarjetas del mismo peso | No todo merece la misma atención (F1): ahora hay un primer plano (estado y acción) y un segundo (historia y contexto) |
