# PROMPT DE INGENIERÍA — EVOLUCIÓN DEL EDITOR DE PLANTILLAS: VISTA ANCHA, SELECTOR DE MODOS, EDICIÓN VISUAL, SCROLL SINCRONIZADO, AUTO-REEMPLAZO GLOBAL Y ETIQUETAS ROJAS DISCRETAS ("MARKFLOW AI")

## 1. Rol y Contexto Técnico
Actúa como un **Arquitecto de Software Senior Full-Stack experto en interfaces de automatización documental (WYSIWYG, Editores de Markdown con Placeholders, Sincronización de DOM y Diseño UI/UX Responsive)**.

Debemos actualizar radicalmente la sección **"3 · Editor de Plantilla y Previsualización"**[cite: 4] para solucionar problemas críticos de usabilidad, desbordamiento visual de etiquetas, falta de edición directa en la vista renderizada y ausencia de automatización en la repetición de variables.

---

## 2. Especificaciones Técnicas de Corrección y Mejora

### REQUISITO 1: Ampliación de Pantalla y Selector de Modos de Vista (Código | Dividida | Renderizada)
- **Problema actual:** El contenedor actual es demasiado estrecho, provocando que las dos ventanas se amontonen y que las etiquetas de los placeholders ("globos") se superpongan de manera ilegible sobre el texto y las tablas[cite: 4].
- **Solución obligatoria:**
  1. **Ancho Extendido (Full-Width / Modal Ampliado):** Amplía el contenedor principal del editor para que ocupe el ancho máximo disponible de la pantalla (`width: 96vw; max-width: 1600px;`), otorgando el espacio necesario para trabajar cómodamente.
  2. **Barra de Modos de Visualización (View Switcher):** Añade un selector de iconos interactivos en la parte superior derecha de la sección que permita alternar instantáneamente entre tres modos de pantalla:
     - 🖥️ **Pantalla Dividida (Split-View):** Muestra código a la izquierda y renderizado a la derecha.
     - 📝 **Solo Código Markdown:** Oculta el panel derecho para maximizar el espacio de edición de texto plano.
     - 👁️ **Solo Pantalla Renderizada (Editor Visual):** Oculta el código y maximiza el panel de previsualización para realizar la selección y mapeo de placeholders de manera totalmente limpia y cómoda.

---

### REQUISITO 2: Edición Directa en la Pantalla Renderizada (Vista Visual)
- **Problema actual:** Editar únicamente desde el código Markdown resulta complejo y propenso a errores de sintaxis.
- **Solución obligatoria:**
  1. Transforma el panel de la vista renderizada en un **Editor Visual Interactivo (Estilo WYSIWYG)**. 
  2. Cualquier cambio de texto, corrección de redacción o ajuste realizado directamente sobre la pantalla renderizada debe actualizar en tiempo real y de forma bidireccional el código Markdown subyacente.

---

### REQUISITO 3: Scroll Sincronizado Simultáneo
- **Problema actual:** Al desplazar una pantalla, la otra se queda estática, dificultando la comparación visual.
- **Solución obligatoria:**
  1. Implementa un listener de desplazamiento vertical (*scroll*) sincronizado por porcentajes (`scrollTop` relativo) entre el panel de código y el panel renderizado en el modo de pantalla dividida, asegurando que ambos se muevan simultáneamente hacia arriba y hacia abajo de forma fluida.

---

### REQUISITO 4: Autoreemplazo Global de Placeholders Repetidos
- **Problema actual:** Si una misma frase o valor numérico (ej. un caudal o un nombre de proyecto) aparece varias veces en el documento, actualmente hay que convertirla en placeholder de forma manual una por una.
- **Solución obligatoria:**
  1. Cuando el usuario seleccione una frase o fragmento de texto y lo convierta en placeholder (asignándole una variable, ej. `[caudal_diseno]`), el sistema debe buscar automáticamente **todas las ocurrencias idénticas de esa misma frase** en todo el texto del documento y **aplicarles el mismo placeholder de manera automática**.
  2. Esto garantiza que cualquier cambio posterior en la variable actualice de forma unificada todas las repeticiones del informe.

---

### REQUISITO 5: Eliminación de los "Globos" Invasivos y Reemplazo por Estilo Rojo Sutil
- **Problema actual:** Como se aprecia en la interfaz actual[cite: 4], las etiquetas de placeholders generan grandes "globos" o contenedores de fondo flotantes que rompen las líneas de texto, desplazan las celdas de las tablas y saturan visualmente la pantalla.
- **Solución obligatoria:**
  1. **Eliminación total de los globos/contenedores:** Remueve los estilos tipo tarjeta o fondo flotante con bordes redondeados que ocupan tanto espacio[cite: 4].
  2. **Estilo de Texto Rojo Discreto:** Reemplaza el marcador visual por un formato de texto en **color rojo plano (o negrita roja)** directamente sobre la palabra o frase, manteniendo el flujo natural de lectura del documento y de las tablas sin alterar las dimensiones de las celdas.

---
### REQUISITO 6: Gestión y Eliminación Sencilla de Placeholders Erróneos
- **Problema a resolver:** Al eliminar los globos flotantes, se perdió la posibilidad de ver rápidamente qué palabras son variables y la opción directa de "quitar" o revertir un placeholder que se aplicó de forma errónea o automática.
- **Solución obligatoria:**
  1. **Interacción al hacer clic:** Al hacer clic sobre cualquier texto en color rojo (placeholder) en la pantalla renderizada, debe desplegarse un pequeño menú contextual flotante o tooltip minimalista que muestre:
     - El nombre de la variable actual.
     - Un botón o icono claro de **Deshacer / Eliminar placeholder** (representado con un icono de papelera o una "X" sutil).
  2. **Reversión instantánea:** Al hacer clic en eliminar, el placeholder seleccionado (y opcionalmente sus ocurrencias globales si el usuario lo confirma) se revierte inmediatamente a texto plano original en el código Markdown y en la vista visual, actualizando el documento al instante.

### REQUISITO 7: Renombrar Placeholders desde el Tooltip Interactivo
- **Funcionalidad requerida:**
  1. Cuando el usuario haga clic sobre cualquier texto en color rojo (placeholder) en la pantalla renderizada, el tooltip flotante minimalista no solo debe mostrar la opción de eliminar, sino también un **campo de entrada editable con el nombre actual de la variable** y un botón de **"Renombrar / Guardar"**.
  2. Al modificar el nombre de la variable en el input y confirmar, el sistema actualizará de manera global todas las ocurrencias de ese placeholder en el código Markdown y en la vista renderizada al instante.



## 3. Criterios de Aceptación (Checklist de Validación)
1. [ ] El editor cuenta con un ancho maximizado y un menú de iconos para alternar entre pantalla dividida, solo código o solo vista renderizada.
2. [ ] La pantalla renderizada permite edición de texto de forma directa, sincronizándose con el código Markdown.
3. [ ] El desplazamiento vertical (*scroll*) está sincronizado entre ambas pantallas.
4. [ ] Al convertir una frase en placeholder, el sistema la reemplaza automáticamente en todas las veces que se repita a lo largo del documento.
5. [ ] Se eliminaron los globos visuales voluminosos de la vista previa, mostrándose ahora las variables en un formato de texto rojo limpio y sin interferir con las tablas.
6. [ ] Al hacer clic en un placeholder rojo, el tooltip permite renombrarlo globalmente o eliminarlo de forma sencilla.