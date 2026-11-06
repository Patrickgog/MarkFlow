# Prompt de mejoras para MarkFlow (React)

## Contexto

Estoy desarrollando **MarkFlow**, un editor de Markdown hecho en **React**. Tiene vista de código/fuente (botón "Fuente", panel izquierdo), vista renderizada, soporte LaTeX y pestañas "Docs" y "Word" en el menú superior.

Necesito implementar las mejoras y correcciones descritas abajo.

**Antes de modificar nada:**
- Revisa la estructura actual del proyecto: componentes del menú superior, editor, parser/renderizador de Markdown (por ejemplo `react-markdown`, `remark`, `rehype`, `marked`, `markdown-it`, `KaTeX` o `MathJax`), manejo de estado y módulo de exportación a Word.
- Respeta el estilo de código, la librería de iconos, la solución de estilos (CSS Modules, Tailwind, styled-components, etc.) y los componentes ya existentes.
- Usa componentes funcionales y hooks. Extrae la lógica de manipulación de texto a funciones utilitarias puras y testeables (por ejemplo en `utils/markdownTransforms.js`) en lugar de dejarla dentro de los componentes.
- No rompas ninguna funcionalidad que ya funciona.

---

## 1. Botones de alineación de texto (pestaña "Docs")

En la pestaña **Docs** del menú superior, añadir un grupo de botones para alinear el texto seleccionado:

- Izquierda
- Centrado
- Derecha
- Justificado

**Requisitos:**
- Cada botón usa un **icono** (la librería que ya use el proyecto, o `lucide-react` / `react-icons` si no hay ninguna) y muestra un **tooltip** con su nombre.
- Se aplica únicamente al párrafo o bloque seleccionado (o al bloque donde está el cursor si no hay selección).
- El botón de la alineación actual del bloque debe aparecer **resaltado** (estado activo). Calcular este estado a partir de la selección/cursor.
- La alineación debe persistir al guardar y al exportar. Como Markdown no soporta alineación nativa, usar HTML embebido, por ejemplo:
  - `<div align="center">...</div>`
  - `<p style="text-align:justify">...</p>`
- Verificar que el renderizador interprete ese HTML (si se usa `react-markdown`, habilitar `rehype-raw` y sanitizar con `rehype-sanitize` permitiendo `align` y `style="text-align"`).
- La alineación **no debe romper** fórmulas LaTeX ni otros elementos dentro del bloque.
- Si el bloque ya tiene una alineación, **reemplazarla** en lugar de anidar etiquetas.
- Al elegir "Izquierda" (valor por defecto), **eliminar** la envoltura HTML.

---

## 2. Rediseño del menú superior en varias filas

Rediseñar la barra superior con **varias filas (estilo ribbon)** para que haya espacio para las herramientas nuevas:

- **Fila 1:** pestañas principales (Archivo, Docs, Word, etc.).
- **Fila 2 en adelante:** herramientas de la pestaña activa, agrupadas por categorías con separadores y una etiqueta pequeña por grupo (por ejemplo: *Formato de texto*, *Alineación*, *Bloques/Notas*, *Insertar*).
- Debe ser **responsive**: si el ancho es reducido, los grupos deben reorganizarse (`flex-wrap`) sin desbordar ni ocultar botones.
- Mantener consistencia visual con el tema actual (claro/oscuro) y con el tamaño de los iconos existentes.
- Crear componentes reutilizables, por ejemplo `<Ribbon>`, `<RibbonTab>`, `<RibbonGroup label="...">` y `<RibbonButton icon tooltip active onClick>`.
- Conservar **todas** las funciones actuales; solo se reorganiza su ubicación.

---

## 3. Corregir el botón "Nota"

**Problema actual:** el botón "Nota" solo funciona en la vista de código (cuando está activo el botón "Fuente" a la izquierda). Al seleccionar un párrafo y pulsarlo, inserta el texto literal `> [!NOTE]` en una línea y luego `>` seguido del párrafo. Esto es incorrecto desde la perspectiva del usuario.

**Comportamiento esperado:**
- El usuario selecciona un párrafo (o varios) y pulsa "Nota". El contenido seleccionado se convierte en un **bloque de nota (callout) renderizado**, sin que el usuario vea el marcador `> [!NOTE]` como texto.
- Debe funcionar tanto en la **vista renderizada/editor visual** como en la **vista de código**.
- Internamente se puede seguir guardando la sintaxis `> [!NOTE]`, pero en la vista visual el usuario solo ve el bloque de nota con su estilo (icono, color, etiqueta "Nota").
- Si el párrafo seleccionado ya es una nota, el botón funciona como **toggle** (quita la nota).
- **Evitar duplicar marcadores:** si ya existe `> [!NOTE]` en el bloque, no volver a insertarlo. Cada línea del párrafo debe llevar el prefijo `>` correctamente en modo código.
- Respetar fórmulas LaTeX, listas, negritas y otros elementos dentro de la selección.
- Para renderizar los callouts, usar un plugin remark/rehype de alertas (por ejemplo `remark-github-blockquote-alert`) o un componente `Callout` propio que reemplace al `blockquote` cuando detecte el marcador `[!NOTE]`.

---

## 4. Corregir el botón "Quitar notas"

**Problema actual:** al pulsar "Quitar notas" se rompen las fórmulas LaTeX y aparecen símbolos extraños.

**Comportamiento esperado:**
- Eliminar **únicamente** el formato de nota/callout (marcadores `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, etc., y el prefijo `>` de las líneas que pertenecen a esas notas), conservando el contenido de cada nota como párrafo normal.
- **No tocar** fórmulas LaTeX (`$...$`, `$$...$$`, `\(...\)`, `\[...\]`, entornos `\begin{...}\end{...}`), bloques de código, tablas, imágenes, HTML embebido ni ningún elemento ya renderizado.
- **Implementación recomendada:**
  1. Antes de procesar, **proteger** (enmascarar con placeholders únicos) los bloques LaTeX y de código.
  2. Aplicar la eliminación de notas **solo sobre las líneas de callout**.
  3. **Restaurar** los placeholders exactamente como estaban.
- Evitar regex globales que reemplacen caracteres como `>`, `\`, `$` o `_` fuera de los marcadores de nota.
- Revisar y corregir problemas de escape/codificación que causan los símbolos raros, por ejemplo:
  - Doble escape de `\`.
  - Uso de `String.prototype.replace` con una cadena de reemplazo que contiene patrones especiales como `$&`, `$1` o `$$`. Usar una **función de reemplazo** (`replace(regex, () => texto)`) para evitarlo.
- No eliminar blockquotes normales (`>` comunes) que no sean notas.

---

## 5. Índice en la pestaña "Word"

Al insertar el índice (tabla de contenido) en la pestaña **Word**, la columna de páginas debe mostrar **únicamente el número** (1, 2, 3, …), sin el prefijo "Pág.", "Pag." ni similar.

- ✅ Correcto: `Introducción ........ 1`
- ❌ Incorrecto: `Introducción ........ Pág. 1`
- Aplicar tanto en la **vista previa** como en la **exportación** del documento Word.

---

## Criterios de aceptación

1. Los 4 botones de alineación funcionan con iconos, afectan solo a la selección y no dañan LaTeX.
2. El menú superior se muestra en varias filas, ordenado por grupos, sin desbordamiento.
3. El botón "Nota" convierte la selección en nota sin mostrar `> [!NOTE]` como texto y funciona en ambas vistas.
4. "Quitar notas" elimina solo las notas; las fórmulas LaTeX y demás elementos quedan idénticos a como estaban.
5. El índice de Word muestra solo números de página.
6. No hay regresiones en funciones existentes.

## Entregable final

Al terminar:
- Resume los archivos creados y modificados.
- Explica brevemente la **causa raíz** de los errores de los puntos 3 y 4.
- Indica cómo probar manualmente cada cambio.
- Si es viable, añade pruebas unitarias (Jest/Vitest) para las funciones de transformación: alineación, aplicar nota, quitar notas (con casos que incluyan LaTeX y bloques de código) y formato del índice.
