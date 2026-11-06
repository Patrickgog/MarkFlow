# PROMPT DE INGENIERÍA — SINCRONIZACIÓN DE SCROLL, PANEL LATERAL UNIFICADO (HTML/DOCX/PDF), LIMPIEZA DE PESTAÑAS, VISORES EXPORTADORES Y TABLAS TIPO EXCEL EN "MARKFLOW OFFICE"

## 1. Rol y Contexto Técnico
Actúa como un **Arquitecto de Software Senior Full-Stack experto en interfaces web interactivas (Streamlit / Python / JavaScript), gestión de estados globales y motores de previsualización y exportación documental**.

Debemos aplicar correcciones estructurales e implementar mejoras de alto nivel en **MarkFlow**  para resolver la sincronización en la pestaña Docs, unificar los parámetros del panel lateral con la pestaña de conversión completa, limpiar pestañas duplicadas, reparar los exportadores de Word, PDF y HTML, y rediseñar la vista de Tablas Estilo Excel para que se comporte como una hoja de cálculo real con renderizado limpio.

---

## 2. Especificaciones Técnicas de Implementación

### REQUISITO 1: Sincronización de Scroll y Botones Superiores en la Pestaña "Docs"
1. **Scroll Sincronizado Bidireccional:** Ambas pantallas en la pestaña Docs (código Markdown y previsualización) deben moverse simultáneamente y de forma proporcional al hacer desplazamiento vertical (*scroll*).
2. **Botones de Iconos Superiores:** Añade dos botones con iconos dedicados en la barra superior de la pestaña Docs:
   - **Botón 1 (Inserción de Imagen):** Debe invocar exactamente el mismo formato, motor y lógica de inserción de imágenes (con encapsulamiento en bloques `<details>` y `<summary>` y numeración automática de figuras) que se utiliza en la pestaña de conversión completa.
   - **Botón 2 (Eliminar Todas las Notas):** Un botón ejecutable que barra mediante expresiones regulares (`^\s*>\s?`) y elimine todas las marcas de notas (`>`) del documento al instante.

---

### REQUISITO 2: Panel Lateral de Conversión y Exportación Sincronizado (3 Subpestañas)
1. **Homologación con "Conversión Completa":** El panel lateral retráctil de la pestaña Docs no está heredando los parámetros avanzados. Debe analizar e incorporar la misma lógica de la pestaña de conversión completa.
2. **Estructura de 3 Subpestañas:** Dentro de este panel lateral, implementa 3 subpestañas dedicadas:
   - **HTML:** Opciones de temas, paletas de colores, estructura de sidebar y estilos web.
   - **DOCX (Word):** Opciones de paletas suaves, títulos formales, interlineado y plantillas.
   - **PDF:** Opciones de maquetación (Normal, 2 Columnas, Revista), paletas sobrias, fuentes, tamaños, numeración de páginas, texto de pie de página (footer), running header dinámico y configuración de índices interactivos.

---

### REQUISITO 3: Limpieza de Pestañas Duplicadas
1. **Eliminación de Pestaña Intermedia:** Actualmente existen dos pestañas llamadas *"Conversión Completa"*. Elimina la pestaña intermedia y conserva únicamente la que se encuentra ubicada **al final de las pestañas verticales**.

---

### REQUISITO 4: Visor y Exportador Dedicado para Word (`.docx`)

1. **Visor de Resultado:** La pestaña de Word Exportador debe incluir un visor integrado que muestre el documento configurado y estructurado actualmente en la pestaña Docs. (RENDERIZADO COMO COMO SE EXPORTARIA A WORD)
2. **Corrección de Exportación:** Repara el error crítico por el cual se genera un documento en blanco; ahora debe exportar físicamente el documento con todo el contenido, tablas y estilos configurados en la app.

---

### REQUISITO 5: Visor y Exportador Dedicado para PDF
1. **Visor y Biblioteca de Entregables:** La pestaña PDF Exportador debe incluir un visor funcional que permita previsualizar el PDF configurado en la pestaña Docs, asegurando además la existencia y visibilidad completa de la biblioteca de entregables y el botón para eliminar PDFs obsoletos.
2. **Sincronización:** El PDF generado debe respetar estrictamente los saltos de página por capítulo, las reglas anti-colisión del footer y los números de página reales en los índices.

---

### REQUISITO 6: Visor y Exportador Dedicado para HTML
1. **Visor en Vivo:** La pestaña HTML Exportador debe renderizar correctamente la página HTML configurada en la pestaña Docs (con su sidebar izquierdo fijo, estilos y bloques KaTeX/Mermaid), eliminando el error actual donde solo se visualizaba una página en blanco con el footer.

---

### REQUISITO 7: Rediseño de la Pestaña "Tablas Estilo Excel"
1. **Estructura de Cuadrícula Limitada (Grid Fijo):** Las columnas actuales se estiran ocupando todo el UI de forma anómala. Modifica la interfaz para que actúe como Excel: define un número estándar de columnas visibles con un ancho fijo/limitado, rellenando con columnas vacías adicionales si el contenido es menor, evitando el estiramiento extremo.
2. **Corrección de Renderizado (Cero Asteriscos):** El contenido y los títulos de las tablas están mostrando asteriscos sin procesar (ej. `**Título**`). Asegúrate de sanitizar y parsear el Markdown para que los textos lleguen completamente renderizados (negritas aplicadas, etiquetas limpias) tanto en la visualización como al exportar a Excel.
3. **Sidebar Retráctil de Estilos:** Añade un sidebar oculto/retráctil a la derecha que ofrezca distintos estilos visuales predefinidos para elegir antes de exportar la tabla a formato de hoja de cálculo.

---

## 3. Criterios de Aceptación (Checklist de Validación)
1. [ ] En la pestaña Docs el scroll es fluido y simultáneo, e incluye los botones operativos de inserción de imagen y eliminación global de notas.
2. [ ] El panel lateral de la pestaña Docs cuenta con 3 subpestañas (HTML, DOCX, PDF) con absolutamente todos los parámetros de configuración de la conversión completa.
3. [ ] Se eliminó la pestaña duplicada de conversión completa, quedando solo la final.
4. [ ] Los exportadores de Word, PDF y HTML muestran visores funcionales conectados a la configuración actual de Docs y exportan archivos reales sin errores ni páginas en blanco.
5. [ ] La pestaña de Tablas Estilo Excel muestra celdas acotadas tipo hoja de cálculo, texto completamente renderizado sin asteriscos de Markdown, y un sidebar derecho retráctil con opciones de estilo para exportación.