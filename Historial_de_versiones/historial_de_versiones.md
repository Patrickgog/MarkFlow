# 📜 Historial de Versiones — MarkFlow Office

Este documento registra la evolución cronológica del software **MarkFlow Office**,
suite de documentos con IA (motor MarkFlow + núcleo GenOffice byte-preserving),
con gobernanza de versión SSOT en `app/version.py` (Regla de oro: la UI nunca
hardcodea la versión).

---

## 📦 Registro de Versiones

### 📌 [v1.23.2] — 2026-11-06 00:00:00
* **Tipo de Incremento:** PATCH (Corrección total del registro de opciones)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.23.2"`
* **Componentes Afectados:**
  - `motor/registro_opciones.py`: normalizador `_a_lista_opciones` / `_normalizar_arbol_registro`; listas nuevas (fuentes_tabla, tamanios_tabla, alineaciones_pie, posiciones_indice, anchos_columna, tamanios_fuente); defaults alineados.
  - `static/js/registro_temas.js`: convertido en cargador dinámico (eliminado `const REGISTRO` hardcodeado).
  - `static/js/office.js`: `poblarSelect` reemplaza `poblarSelectSiVacio`; `inicializarBarrasLaterales` async con `MFORegistro.cargar()`.
  - `tests/test_registro_contrato.py`: nuevo test de contrato.
* **Descripción Técnica de Cambios:**
  1. Contrato único: todas las listas del registro se devuelven como arrays `{valor, nombre}`.
  2. Eliminado el hardcodeo de opciones del frontend.
  3. Corregido: los selects PDF/Word quedaban vacíos tras v1.23.1 (dict vs array).


### 📌 [v1.23.1] — 2026-11-06 00:00:00
* **Tipo de Incremento:** PATCH (Portada Premium configurable)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.23.1"`
* **Componentes Afectados:**
  - `motor/registro_opciones.py`: bloque `portada_premium` (temas, layouts de fotos, defaults).
  - `motor/a_pdf.py`: función `_generar_html_portada_premium` + `_imagen_a_datauri` + `_layout_fotos`; integración en `a_pdf` (prepend portada, omitir numeración en página 1).
  - `app/rutas/office.py`: campo `portada_premium` en `ModeloExportarPdf` y paso a `a_pdf`.
* **Descripción Técnica de Cambios:**
  1. Portada premium configurable con 6 temas y galería de 1-6 fotos con layout automático.
  2. Imágenes convertidas a data URI base64 para incrustación.
  3. Numeración de páginas omite la portada cuando está activa.


### 📌 [v1.23.0] — 2026-11-06 00:00:00
* **Tipo de Incremento:** MINOR (Nueva funcionalidad: modo de maquetación Premium para PDF)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.23.0"`
* **Componentes Afectados:**
  - `motor/registro_opciones.py`: añadida opción "premium" en `MODOS_COLUMNAS_PDF` y `ESTILOS_MAQUETACION_PDF`.
  - `motor/a_pdf.py`: CSS premium (tarjetas KPI, columnas selectivas, figuras premium, callouts), parser de bloques `:::kpi` y post-proceso de `:::columns-premium`.
* **Descripción Técnica de Cambios:**
  1. Nuevo modo "✨ Premium Ejecutivo (Tarjetas + Layout Mixto)" seleccionable en la pestaña PDF.
  2. Soporte de marcadores Markdown `:::kpi` (tarjetas) y `:::columns-premium` (columnas locales).
  3. Clase `modo-premium` aplicada al cuerpo editorial cuando corresponde.


### 📌 [v1.22.2] — 2026-10-31 19:50:00
* **Tipo de Incremento:** PATCH (Depuración y supresión de frontmatter YAML en PDF, verificación de sangrado físico total de borde a borde y reinicio del servidor de desarrollo con recarga activa --reload).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.22.2"`
* **Componentes Afectados:**
  - `motor/a_pdf.py`:
    - Adición de saneamiento automático de bloques iniciales YAML (`--- ... ---`) para evitar que metadatos crudos (`title:`, `author:`, etc.) se impriman sobre el encabezado o la banda de membrete superior.
    - Extracción reactiva de título documental desde `title:` del frontmatter si no fue suministrado explícitamente.
  - Servidor Uvicorn (`http://127.0.0.1:8320`):
    - Reinicio del proceso en memoria con recarga automática `--reload` activa, garantizando que el navegador consuma inmediatamente el motor de fondo completo A4 sin márgenes residuales.
  - Directorio de artefactos:
    - Verificación visual con capturas reales de alta fidelidad `captura_p0_bombeo_p1.png` y `captura_p0_bombeo_p2.png`.

### 📌 [v1.22.1] — 2026-10-31 19:25:00
* **Tipo de Incremento:** PATCH (Desacoplamiento geométrico absoluto entre la plantilla de membrete A4 y los márgenes de texto en PDF Editorial: renderizado de fondo físico A4 de borde a borde mediante PyMuPDF overlay=False en capa subyacente física Rect(0, 0, ancho, alto), eliminación de capas fixed HTML distorsionadas por @page, y aislamiento estricto de las reglas @page métricas exclusivamente para la zona de texto/escritura).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.22.1"`
* **Componentes Afectados:**
  - `motor/membrete.py`:
    - En `extraer_membrete_pdf()`: inclusión directa de `bytes_img` en la estructura de cada elemento para evitar decodificaciones redundantes y alimentar PyMuPDF directamente.
  - `motor/a_pdf.py`:
    - En `_generar_html_impresion()`: remoción de capas fijas HTML `.mfo-membrete-fondo` que sufrían desplazamiento y recorte por las reglas `@page`, e inyección de `html, body { background: transparent !important; }` para asegurar que el lienzo de Chromium sea 100% transparente ante la capa de fondo física.
    - En `_postprocesar_con_pymupdf()`: adición del parámetro `elementos_membrete` y estampado vectorial de fondo físico en cada página con `p.insert_image(rect_dest, stream=img_bytes, overlay=False, keep_proportion=False)`. En fondos completos abarca `Rect(0, 0, ancho, alto)` (210 mm × 297 mm exactos); en cabecera y pie abarca el ancho físico de borde a borde.
    - Desacoplamiento total: los márgenes `zona_cm` configuran únicamente el área de flujo de texto `@page` en Chromium sin mover, recortar ni alterar la plantilla A4 física.
  - `pruebas/test_fase_pdf_membrete.py`:
    - Ampliación de pruebas con validación cromática por píxeles en bordes (`pix.pixel(10, 10)`) comprobando cobertura A4 total e invariancia del fondo ante variaciones en los márgenes de texto (`test_independencia_margenes_texto_y_plantilla_a4`).

### 📌 [v1.22.0] — 2026-10-31 15:50:00
* **Tipo de Incremento:** MINOR (Soporte integral para Hojas de Membrete en PDF Editorial: extracción automática de imágenes de membrete raster con conversión a Data URI Base64, reglas CSS @page con márgenes métricos dinámicos respetando la zona de escritura calculada o personalizada, capas fijas de fondo repetitivas en Chromium Headless, supresión de filetes invasivos y running header artificial en presencia de membrete, numeración de páginas anti-colisión en PyMuPDF, y tarjeta interactiva de selección y previsualización en la barra lateral de PDF).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.22.0"`
* **Componentes Afectados:**
  - `motor/membrete.py`:
    - Función pura `extraer_membrete_pdf(ruta_docx)` que inspecciona las partes OpenXML, extrae imágenes PNG/JPEG raster a Data URIs Base64 y clasifica la orientación (fondo completo vs. bandas de cabecera y pie).
    - Mecanismo de caché en memoria `_CACHE_MEMBRETE_PDF` basado en timestamp de modificación `mtime` del archivo.
  - `motor/a_pdf.py`:
    - En `_generar_html_impresion()`: inyección de márgenes `@page` según `zona_cm` y de capas fijas `.mfo-membrete-fondo`, `.mfo-membrete-cabecera`, `.mfo-membrete-pie` con `position: fixed` y `z-index: -100`.
    - En `_postprocesar_con_pymupdf()`: supresión de `running_header` y filete inferior en presencia de membrete, y estampado vectorial de numeración de páginas en el margen inferior libre sin colisiones.
    - En `a_pdf()`: integración de los parámetros `plantilla_word` y `zona_cm`.
  - `app/rutas/office.py`:
    - Ampliación de `ModeloExportarPdf` con `plantilla_word`, `zona_top`, `zona_bottom`, `zona_left`, `zona_right`, `posicion_numero`.
    - En `POST /api/office/exportar-pdf`: validación estricta de plantillas con `validar_plantilla_word_segura()` y paso de parámetros métricos a `a_pdf()`.
  - `templates/office.html`:
    - Nueva sección colapsable `📄 Hoja de Membrete PDF` en `#sidebar-pdf-opciones` con combo `<select id="pdf-opt-hoja-membrete">`, botón de refresco y contenedor dinámico con los 4 márgenes métricos en cm (`#contenedor-zona-membrete-pdf`).
  - `static/js/office.js`:
    - Funciones `consultarAnalisisMembretePdf()` y actualización de `cargarPlantillasWordDesdeDisco()` para poblar los selectores de Word y PDF.
    - Sincronización en vivo del visor PDF (`refrescarVisorPdfEnVivo()`) y envío de parámetros de membrete en `ejecutarExportarPdf()`.
  - `pruebas/test_fase_pdf_membrete.py`:
    - Suite completa con 8 pruebas automatizadas verificando extracción de bandas y fondo completo, caché `mtime`, generación real con Chromium, numeración, cero regresiones y blindaje Path Traversal.

### 📌 [v1.21.0] — 2026-10-31 14:55:00
* **Tipo de Incremento:** MINOR (Soporte integral para Hojas de Membrete en Word .docx: listado dinámico seguro, análisis geométrico OpenXML de márgenes y zonas de escritura, trasplante de cuerpo conservando membrete byte a byte, consolidación de sección continua sin titlePg, numeración opcional de páginas 'Página X de Y' y panel interactivo en la pestaña Word con edición y guardado de márgenes métricos).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.21.0"`
* **Componentes Afectados:**
  - `motor/membrete.py`:
    - Funciones puras `analizar_membrete()`, `guardar_zona_json()` y `aplicar_cuerpo_sobre_plantilla()`.
    - Inspección de cabeceras, pies y cuerpo con cálculo de cotas métricas (EMU/dxa a cm).
    - Trasplante de elementos `<w:body>` con remapeo de relaciones `rId` sin colisiones y aseguramiento de `behindDoc="1"` en imágenes de fondo.
    - Supresión de `<w:titlePg>` y normalización de cabeceras/pies a tipo `default` para garantizar la repetición del membrete en todas las páginas.
    - Inyección de numeración de páginas opcional con campos Word nativos `PAGE` y `NUMPAGES` sin alterar gráficos preexistentes.
  - `app/rutas/office.py`:
    - Definición de constante segura `DIR_PLANTILLAS_WORD = RAIZ / "storage" / "plantillas_word"`.
    - Función de validación de seguridad `validar_plantilla_word_segura()` contra ataques de Path Traversal (`../`).
    - Nuevos endpoints de API: `GET /api/office/plantillas-word`, `GET /api/office/plantillas-word/{nombre}/analisis`, `POST /api/office/plantillas-word/{nombre}/zona`.
    - Conexión de parámetros de hoja de membrete y zona métrica (`zona_top`, `zona_bottom`, etc.) en el endpoint de exportación `POST /api/office/exportar-docx`.
  - `templates/office.html`:
    - Selector desplegable `#word-opt-hoja-membrete` y botón de actualización `#btn-refrescar-plantillas-word`.
    - Subpanel interactivo `#contenedor-zona-membrete` con inputs numéricos editables en cm (`#word-membrete-top`, `#word-membrete-bottom`, `#word-membrete-left`, `#word-membrete-right`), badge de origen (`#badge-origen-zona`), caja de avisos geométricos y botón `#btn-guardar-zona-membrete`.
  - `static/js/office.js`:
    - Funciones `cargarPlantillasWordDesdeDisco()`, `consultarAnalisisMembrete()` y `guardarZonaMembreteActual()`.
    - Sincronización en vivo del padding del visor Word (`renderizarHojaWordPreview()`) al cambiar los inputs métricos de márgenes.
    - Inclusión de parámetros de membrete y cotas métricas en el payload de `ejecutarExportarWord()`.
  - `pruebas/`:
    - Suites automatizadas creadas: `test_fase_1_plantillas_word.py` (3 tests), `test_fase_2_analisis_membrete.py` (4 tests), `test_fase_3_cuerpo_membrete.py` (4 tests), `test_fase_4_numeracion_membrete.py` (5 tests), `test_fase_5_interfaz_exportacion.py` (4 tests), acumulando 20 tests verdes específicos de la mejora.

### 📌 [v1.20.10] — 2026-10-30 17:00:00
* **Tipo de Incremento:** PATCH (Notificación visual al cambiar opciones en Word + seguro de renderizado).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.10"`
* **Componentes Afectados:** `static/js/office.js`

### 📌 [v1.20.9] — 2026-10-30 16:00:00
* **Tipo de Incremento:** PATCH (Seguro de renderizado en vivo en pestaña Word: try/catch en handlers, re-render al recuperar foco, y propagación segura de promesas).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.9"`
* **Componentes Afectados:** `static/js/office.js`

### 📌 [v1.20.8] — 2026-10-30 14:00:00
* **Tipo de Incremento:** PATCH (Renderizado de fórmulas en vivo: conversión de variables con subíndice (j_k)/(Q_k) a notación LaTeX preservando paréntesis, carga correcta de fuentes KaTeX desde /assets/katex/fonts, y saneamiento de términos explicativos en 'Donde:').
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.8"`
* **Componentes Afectados:** `motor/formulas.py`, `motor/a_html.py`

### 📌 [v1.20.7] — 2026-10-30 12:00:00
* **Tipo de Incremento:** PATCH (Fase 2 Word: previsualización en vivo estable y sin cancelación cruzada para paletas y temas, re-render inmediato al cambiar selectores y pickers de color, re-sincronización tras cargar temas desde disco, y debounce dedicado para la hoja Word).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.7"`
* **Componentes Afectados:** `static/js/office.js`

### 📌 [v1.20.6] — 2026-10-29 11:45:00
* **Tipo de Incremento:** PATCH (Fase 4: Paridad espejo exacta Previsualización ↔ Exportación `.html` en la pestaña HTML, lectura y validación estricta de plantillas desde `templates/temas_html/Tema1.html` … `Tema6.html` con error HTTP 404 claro si no existe el tema, respeto íntegro de todas las opciones del panel lateral en vivo y en el archivo exportado —Plantilla de Tema, Paleta Tri-Color nativa y personalizada `c1|c2|c3`, Ancho Máximo de Lectura, Tipografía, Texto justificado web, Numeración de ecuaciones y Pie de página izquierdo/derecho—, y suite de regresión integral de las 4 fases).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.6"`
* **Componentes Afectados:**
  - `motor/a_html.py`:
    - Incorporación de `listar_temas_html_disco()` y validación estricta de `templates/temas_html/{tema_id}.html`, lanzando `FileNotFoundError("Tema '<id>' no encontrado en templates/temas_html")` cuando se solicita un tema que no existe en disco.
    - En la rama de plantillas locales (`Tema1.html` … `Tema6.html`), inyección completa de todas las opciones del panel lateral: `--font-main`, `--hdxf-font-main` y `font-family` con `!important`; `--ancho-maximo` sobre `.hdxf-with-sidebar, .doc-main, article`; `justificado_css` (`text-align: justify !important` vs `text-align: left !important`); `numerar_eq_css` con `counter-reset: num_eq` y `counter-increment: num_eq`; sobrescritura de paleta sobre `:root, [data-theme="light"], [data-palette], body.custom-theme` para imponerse a `[data-palette="..."]` en `Tema2..Tema6`; e inyección garantizada de `<footer class="hdxf-footer pie-doc">` tanto en `Tema1` (reemplazo) como en `Tema2..Tema6` (inserción tras `</article>`).
    - Neutralización de la invocación redundante de `window.CNW_MERMAID.run()` en `Tema2..Tema6` para que únicamente se ejecute el motor saneado `_iniciarRenderMarkflow()`.
  - `app/rutas/api.py`, `app/rutas/office.py`:
    - En `POST /api/render-preview` (`app/rutas/api.py`), lectura y envío a `a_html()` de todos los parámetros del panel lateral (`tema_html`, `paleta_tricolor`, `fuente`, `ancho_maximo`, `justificado`, `numerar_ecuaciones`, `footer_izq`, `footer_der`) y captura de `FileNotFoundError` con HTTP 404 (`TEMA_HTML_NO_ENCONTRADO`).
    - En `ModeloExportarHtml` y `POST /api/office/exportar-html` (`app/rutas/office.py`), adición de `justificado`, `footer_izq` y `footer_der`, captura de `FileNotFoundError` con HTTP 404 y nuevo endpoint `GET /api/office/temas-html`.
  - `static/js/office.js`:
    - Unificación de la carga de opciones mediante `construirPayloadHtml(md, nombreDoc)`, consumida tanto por `cargarVisorHtmlDedicado()` como por `ejecutarExportarHtml()`, leyendo directamente los controles reales `#html-opt-tema`, `#html-opt-paleta`, `#html-opt-ancho`, `#html-opt-fuente`, `#html-opt-justificado`, `#html-opt-num-eq`, `#html-opt-footer-izq` y `#html-opt-footer-der`.
    - Sincronización inmediata del visor HTML al aplicar una paleta personalizada desde el modal (`cargarVisorHtmlDedicado()`) y al escribir en `#html-opt-footer-izq` / `#html-opt-footer-der` (`input` + `change`).
  - `pruebas/test_fase_4_html.py`:
    - Suite de 14 pruebas automatizadas verificando el catálogo de `templates/temas_html/`, error HTTP 404 ante tema inexistente, jerarquía `H1/H2/H3` y negritas sin marcadores residuales, diagrama Mermaid del Anexo A sin scrollbars, aplicación de opciones del panel lateral en `defecto` y `Tema1`..`Tema6`, y paridad espejo byte a byte entre `/api/render-preview` y `/api/office/exportar-html`.

### 📌 [v1.20.5] — 2026-10-29 08:28:00
* **Tipo de Incremento:** PATCH (Fase 3: Zoom tipo visor real en pestaña PDF mediante re-render en `pdf.js` de 25 % a 400 % con crecimiento físico de la hoja y barras de desplazamiento, soporte de `Ctrl + rueda` sobre el lienzo principal excluyendo miniaturas, atajos `Ctrl+"+"`/`"-"`/`"0"` con foco en el visor, previsualización en vivo con debounce único de 300 ms sin colisión con `salidas/`, y regla canónica de salto de capítulo exclusivo a `H1` con excepción de primera hoja y eliminación de páginas en blanco).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.5"`
* **Componentes Afectados:**
  - `motor/saltos_capitulo.py`, `motor/a_pdf.py`:
    - Nuevo módulo puro `motor/saltos_capitulo.py` (`es_titulo_numerado`, `indices_h1_con_salto`, `inyectar_saltos_capitulo_html`) que centraliza la regla de salto de capítulo exclusivo a `H1` con excepción de primera hoja (el título general y la introducción breve precedentes comparten la Hoja 1 con el primer `H1` numerado; desde el 2.º `H1` en adelante se fuerza página nueva; `H2`, `H3` y `<hr>` jamás generan salto).
    - En `_generar_html_impresion()` (`motor/a_pdf.py`), eliminación de `page-break-before: always !important` sobre `.cuerpo-editorial h1` y `.cuerpo-editorial hr`, que provocaban saltos en el primer capítulo, en separadores `---` antes de `H2` y hojas en blanco intermedias.
    - Eliminación del `<div class="capitulo-salto-pagina">` duplicado antes de `.indice-final-documento` que producía una hoja en blanco previa al índice final.
  - `static/js/visor_pdf.js`, `templates/office.html`, `static/css/office.css`:
    - Reemplazo del indicador estático `#pdf-zoom` por `<select id="pdf-zoom">` (`Ajustar página`, `Ajustar ancho`, `25 %` … `400 %`) y adición de `tabindex="0"` en `#lienzo-pdf`.
    - Eliminación en `static/css/office.css` de `max-width: 95% !important; max-height: 95% !important; width: auto !important; height: auto !important;` sobre `.lienzo-pdf canvas` que impedían crecer físicamente a la hoja al hacer zoom, y cambio de `.lienzo-pdf` a `align-items: flex-start; justify-content: flex-start;` con `margin: auto` en el canvas.
    - Re-renderizado nítido con `pdf.js` (`pag.getViewport({ scale: escalaCss * dpr })`), cancelación y espera de `renderEnCurso` antes de redimensionar el `<canvas>`, conservación del punto bajo el cursor, zoom con `Ctrl + rueda` (paso 10 %, límites 25 %–400 %) exclusivo en `#lienzo-pdf` (excluido en `#pdf-lista-miniaturas`), atajos `Ctrl+"+"`/`"-"`/`"0"` con foco en el visor y preservación de página/zoom al recompilar en vivo.
  - `static/js/office.js`:
    - Eliminación del doble debounce (300 ms + 350 ms) dejando un único debounce de `300 ms` en `refrescarVisorPdfEnVivo()` con control de secuencia `secuenciaPdfEnVivo`.
  - `pruebas/test_fase_3_pdf.py`:
    - Suite de 13 pruebas automatizadas verificando la regla canónica de salto H1-only con excepción de primera hoja, exportación PDF real de `Prueba_Saltos_Fase3.md`, presencia del diagrama Mermaid del Anexo A, re-render real en `visor_pdf.js`, exclusión de miniaturas en `Ctrl + rueda` y debounce único de 300 ms.

### 📌 [v1.20.4] — 2026-10-28 21:50:00
* **Tipo de Incremento:** PATCH (Fase 2: Paridad total previsualización ↔ exportación `.docx` en pestaña Word, lectura directa de estilos reales desde `templates/temas_word/tema1.docx`, `tema2.docx` y `tema3.docx` con aviso explícito si el tema no existe, población y aplicación de paletas personalizadas en selectores y `.docx`, protección de temas nativos y paletas contra sobrescritura por pickers de color, y soporte de los 4 modos de alineación `justificado`, `izquierda`, `centrado`, `derecha`).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.4"`
* **Componentes Afectados:**
  - `motor/a_docx.py`:
    - Implementación de `inspeccionar_tema_word(tema_id)` y `listar_temas_word_disco()`, que extraen directamente desde `templates/temas_word/*.docx` (`word/styles.xml` y `word/document.xml`) los estilos de fuente, tamaños y colores de H1/H2/H3, cabeceras, filas y bordes de tablas, y emiten `FileNotFoundError("Tema '<id>' no encontrado en templates/temas_word ...")` si el archivo no existe.
    - En `_barnizar_tabla()`, prioridad estricta para los temas nativos (`tema1`, `tema2`, `tema3`) sobre `color_tabla_cabecera` y `color_tabla_filas`, más soporte de paletas personalizadas `c1|c2|c3|c4|c5`, evitando que valores residuales de pickers pisen las plantillas de `templates/temas_word/` o las paletas suaves.
    - En `_barnizar()`, corrección del orden de precedencia de `modo_color_titulos` para que `modo_color_titulos="personalizado"` no sea forzado a negro cuando `color_titulos_word` conserve su valor por defecto `"negro"`, y escritura explícita de tamaños y colores reales de H1/H2/H3 en `tema1`, `tema2` y `tema3`.
    - En `_barnizar()`, escritura explícita de `<w:jc w:val="both|left|center|right"/>` en cada párrafo de cuerpo y en los estilos base `Normal`, `Body Text` y `First Paragraph` para los 4 modos de alineación (`justificado`, `izquierda`, `centrado`, `derecha`).
  - `motor/registro_opciones.py`, `app/rutas/office.py`:
    - Ampliación de `ALINEACIONES_WORD` a `["justificado", "izquierda", "centrado", "derecha"]`.
    - Nuevo endpoint `GET /api/office/temas-word` para listar o inspeccionar los temas de `templates/temas_word/`, devolviendo HTTP 404 con detalle explícito cuando el tema no existe.
  - `static/js/registro_temas.js`, `static/js/office.js`:
    - Incorporación de `{ valor: "derecha", nombre: "Derecha" }` en `word.alineaciones` y vinculación de `word.temas` a `templates/temas_word/`.
    - Sincronización de `#word-opt-tema` con `/api/office/temas-word` (`cargarTemasWordDesdeDisco()`), población de paletas personalizadas en `#word-opt-paleta-titulos` y `#word-opt-paleta-tablas`, mapeo CSS real de las 4 alineaciones (`justify`, `left`, `center`, `right`) en `renderizarHojaWordPreview()` y envío de colores de pickers en `ejecutarExportarWord()` únicamente cuando no hay tema nativo ni paleta suave activa.
  - `pruebas/test_fase_2_word.py`:
    - Suite de 6 pruebas automatizadas verificando lectura de `templates/temas_word/`, error ante tema inexistente, fidelidad OpenXML de `tema1`, `tema2` y `tema3`, aplicación de paletas personalizadas, los 4 modos de alineación en `word/document.xml` y renderizado de negritas y diagrama Mermaid del Anexo A en `.docx`.

### 📌 [v1.20.3] — 2026-10-28 20:48:00
* **Tipo de Incremento:** PATCH (Fase 1 Consolidada: Analizador de sintaxis Mermaid por estado que respeta nodos ya entrecomillados `["..."]` y corchetes anidados `[unidad]`, erradicación del error `Parse error ... [mm"]"]` en `CRITERIO DE REDES 3` y en todas las pestañas de exportación, corrección de medición SVG de Mermaid 10.9.1 moviendo `[id^="dmermaid-"]` fuera de pantalla en lugar de `display: none` para eliminar `Could not find a suitable point for the given distance`, actualización in-place reactiva de `.contenedor` en `#visor-docs` preservando scroll y caché de SVG, y soporte de pegado e InputRules para bloques Mermaid/Markdown en `#editor-docs`).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.3"`
* **Componentes Afectados:**
  - `motor/a_mermaid.py`, `motor/a_html.py`, `static/js/office.js`:
    - Reemplazo de la expresión regular agresiva `\[([^\]]*?)\]` por un analizador por estado simétrico en Python y JavaScript (`sanear_codigo_mermaid`, `_sanearMermaid`, `sanearCodigoMermaid`) que preserva intactos los nodos ya entrecomillados `["..."]` y transforma corchetes internos anidados `[mm]` en `(mm)` solo cuando el nodo externo carece de comillas, eliminando el fallo `[mm"]"]` en todas las vistas y pestañas.
  - `motor/a_html.py`, `static/css/office.css`:
    - Reemplazo de `[id^="dmermaid-"] { display: none !important; width: 0 !important; height: 0 !important; }` por posicionamiento fuera de pantalla (`position: fixed !important; left: -99999px !important; opacity: 0 !important;`), permitiendo que `dagre-d3` mida `getTotalLength()` y `getBBox()` durante `mermaid.render()` sin lanzar `Could not find a suitable point for the given distance`.
    - Envoltura del cuerpo de `_PLANTILLA_BASE` en `<main class="contenedor contenido-principal">__CONTENIDO__</main>` para actualización en vivo in-place en `#visor-docs` y extracción exacta en la vista previa de Word.
    - Incorporación de mutex `window._renderMarkflowEnCurso` y estado `data-processed="processing"` para impedir condiciones de carrera entre el script del iframe y el listener del contenedor padre.
  - `static/js/editor_docs.js`, `app/servicios/editor_markdown.py`:
    - Incorporación de `handlePaste` en ProseMirror (`#editor-docs`) para detectar diagramas Mermaid pegados (con o sin cerco ```` ```mermaid ````) y bloques Markdown estructurados (`#`, `**`, tablas), convirtiéndolos en nodos reales y disparando la previsualización en vivo de inmediato.
    - Inferencia automática de `params = "mermaid"` en `code_block` cuando el contenido empieza por `graph TD`, `flowchart`, `sequenceDiagram`, etc., más `InputRule` en vivo para ```` ```mermaid ```` + espacio, `**negrita**` y `*cursiva*`.
  - `pruebas/test_fase_1_docs.py`:
    - Ampliación a 6 pruebas unitarias cubriendo el documento real `CRITERIO DE REDES 3.md`, el diagrama del Anexo A, la inferencia de bloques Mermaid en el editor visual y el saneador por estado.

### 📌 [v1.20.2] — 2026-10-28 16:40:00
* **Tipo de Incremento:** PATCH (Fase 1: Corrección de renderizado en vivo en la pestaña Docs, erradicación de marcadores internos <1 id="..."> y <2 id="..."> restaurando la jerarquía H1/H2/H3 y negrita, subsanación del SyntaxError de await en scripts cliente, reactivación del renderizado de diagramas Mermaid en el panel de Docs con manejo amigable de errores en español, debounce reducido a 300 ms en vivo, y unificación de la función de renderizado compartida).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.2"`
* **Componentes Afectados:**
  - `motor/a_html.py`:
    - Corrección en `_asignar_ids_titulos`: sustitución de `tag = m.group(1)` por `tag = f"h{m.group(1)}"`. Se erradica por completo la generación defectuosa de etiquetas `<1 id="...">` y `<2 id="...">`, restituyendo etiquetas legítimas `<h1>`, `<h2>` y `<h3>` con sus estilos nativos de peso (`font-weight: 700`), colores temáticos y jerarquía tipográfica.
    - Corrección en `_JS_INICIAR_RENDER`: conversión de `function _iniciarRenderMarkflow()` en `async function _iniciarRenderMarkflow()`, subsanando el fallo de parseo `SyntaxError: await is only valid in async functions` que bloqueaba la ejecución de KaTeX y Mermaid.
  - `static/js/office.js`:
    - En `previsualizar()`: ajuste del retardo del debounce de 500 ms a 300 ms para actualización en tiempo real mientras el usuario escribe en Docs sin cambiar de pestaña.
    - En `vincularScrollDocs()` / evento `load` de `#visor-docs`: integración garantizada que ejecuta `_iniciarRenderMarkflow()` dentro del iframe y enlaza de forma reactiva `window.renderizarMermaidCompartido(docIframe.body)`, asegurando que los bloques Mermaid se procesen siempre como SVG vectoriales legibles.
    - En `renderizarMermaidCompartido`: adición de verificación `data-processed` para evitar re-renderizados innecesarios y protección de nodos contra errores de sintaxis.
  - `templates/office.html` e `index.html`:
    - Restauración de la integridad de las plantillas principales del sistema en `templates/`.
  - `pruebas/test_fase_1_docs.py`:
    - Cobertura de 4 pruebas unitarias certificando ausencia total de marcadores `<1`, `<2>`, renderizado correcto de negritas/cursivas, compilación del diagrama del Anexo A, async function en el script cliente y debounce de 300 ms.
  - `docs/planes/0030-v1.20.2-fase-1-correccion-renderizado-docs-mermaid-titulos.md`:
    - Plan de implementación estructurado de la Fase 1.

### 📌 [v1.20.1] — 2026-10-28 13:35:00
* **Tipo de Incremento:** PATCH (Corrección de sintaxis de Mermaid en nodos con 'pipe' '|', erradicación absoluta de bombas SVG de error en pie de página/footer, eliminación total de scrollbars horizontales y verticales en diagramas HTML y Word preview, aislamiento de Edge headless mediante user-data-dir temporal evitando timeouts, y restauración fiel de la integridad de los Temas 1, 2 y 3 tanto en Word como en HTML en el visor de la aplicación).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.1"`
* **Componentes Afectados:**
  - `motor/a_mermaid.py`:
    - Incorporación en `sanear_codigo_mermaid` de envoltura estricta en comillas dobles `["..."]` para nodos entre corchetes `[...]` que contengan caracteres pipe `|`, dos puntos o símbolos conflictivos, evitando el fallo de parseo `got PIPE` de Mermaid.
    - Configuración en `renderizar_a_png` de `--user-data-dir` temporal aislado y `--virtual-time-budget=2000` para Microsoft Edge headless, erradicando bloqueos y timeouts de renderizado.
  - `motor/a_html.py`:
    - Incorporación de `_asignar_ids_titulos` asignando identificadores `id` únicos a cada encabezado `<h1>`, `<h2>`, `<h3>`, permitiendo que el ScrollSpy e índice lateral interactivo de las plantillas funcione de forma dinámica.
    - Sincronización fiel de los temas locales (`Tema1.html` a `Tema6.html`): actualización del título en Hero y encabezados, y población dinámica de las listas de capítulos en `#hdxfNav` (Tema 1) y `#docNav` (Temas 2 a 6) sin alterar la estructura corporativa de las plantillas de `templates/temas_html/`.
    - Neutralización de llamadas duplicadas no saneadas de `window.CNW_MERMAID.run()` en las plantillas originales para prevenir renderizados dobles y colisiones de Mermaid.
    - Regla CSS universal `[id^="dmermaid-"], .error-icon, [aria-roledescription="error"] { display: none !important; }` tanto en `_PLANTILLA_BASE` como en `inyeccion_head`, impidiendo que Mermaid inyecte bombas o mensajes de error al final del documento.
    - Contención fluida `.mermaid { overflow: visible !important; width: 100% !important; max-height: none !important; }` eliminando cualquier barra de desplazamiento en el HTML maquetado.
  - `static/js/office.js`:
    - Refuerzo de `sanearCodigoMermaid` en frontend para envolver con comillas dobles los nodos con pipes.
    - En `renderizarHojaWordPreview`: aplicación de las paletas fieles de `tema1` (Azul #1E3A8A), `tema2` (Verde Esmeralda #046A38) y `tema3` (Pizarra #2F4F4F), y ajuste de diagramas Mermaid a `overflow: visible !important` y `max-height: none` sin desbordes.
    - En `cargarVisorHtmlDedicado`: lectura directa del tema seleccionado en `#html-opt-tema` y limpieza inmediata de cualquier elemento residual de error en el DOM.
    - En `renderizarMermaidCompartido`: limpieza de divs residuales `[id^="dmermaid-"]` tras la compilación.
  - `static/js/app.js`:
    - Captura protegida en `window.mermaid.run` con saneamiento previo y limpieza obligatoria de nodos `[id^="dmermaid-"]`.
  - `static/css/office.css`:
    - Inclusión de regla global anti-bomba de Mermaid y ajuste de `.hoja-word-pagina .mermaid` a `overflow: visible !important`.

### 📌 [v1.20.0] — 2026-10-28 11:25:00
* **Tipo de Incremento:** MINOR (Fase 2: Legibilidad y dimensionamiento editorial de diagramas y figuras en Word, PDF y HTML. Renderizado Mermaid a 300 DPI reales mediante Edge headless con escala de dispositivo 3x, tipografía base aumentada a 16 px legible sin lupa equivalente a >= 9 pt impreso, acotamiento geométrico de ancho entre 60% (3.72 in) y 100% (6.20 in) de la columna A4, limitación estricta de altura a 22 cm (8.66 in) evitando desbordes de página en Word y PDF, eliminación absoluta de barras de scroll horizontal o vertical en HTML y temas con overflow visible, y soporte editorial para figuras flotantes con texto envolvente mediante clases .figura-flotante-izq y .figura-flotante-der acotadas al 48%).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.20.0"`
* **Componentes Afectados:**
  - `motor/a_mermaid.py`:
    - Incorporación de `_FACTOR_ESCALA_DEVICE = 3.0` inyectado dinámicamente como `--force-device-scale-factor=3` en la llamada a Microsoft Edge headless, generando capturas nítidas a 300 DPI reales.
    - Tipografía de diagramas aumentada en la plantilla HTML interna (`fontSize: 16`, `font-size: 16px !important`, espaciado de nodos y niveles aumentado a 45 px).
    - Nueva lógica geométrica en `_atributo_ancho(ruta)`: calcula el ancho proporcional en pulgadas asegurando que ningún diagrama mida menos del 60% de la columna (`3.72 in`) ni más del 100% (`6.20 in`), y trunca matemáticamente a 2 decimales para garantizar que la altura máxima nunca supere 22 cm (`8.66 in`).
  - `motor/a_html.py`:
    - Eliminación de `max-height: 620px` y `overflow-x: auto` en los contenedores de diagramas `.mermaid` y `.diagram-container`.
    - Regla de contención `overflow: visible !important; max-height: none !important; width: 100% !important; min-width: 60% !important;` impidiendo cualquier scrollbar interno y asegurando renderizado completo y fluido.
    - Soporte completo para figuras flotantes editoriales `.figura-flotante-izq` y `.figura-flotante-der` con `float: left/right`, ancho máximo acotado al 48% y márgenes de 1 cm para una envoltura de texto fluida.
  - `motor/a_pdf.py`:
    - Actualización del límite de imágenes en Weasyprint/HTML a `max-height: 22cm`, ancho mínimo del 60% y ancho máximo del 100%.
    - Reglas de salto de página y figuras flotantes con texto envolvente en PDF.
  - `motor/a_docx.py`:
    - Normalización de párrafos con figuras e imágenes (`w:drawing` y `w:pict`): sangría izquierda y derecha forzada a 0 y centrado simétrico `w:jc w:val="center"`.
  - `templates/temas_html/Tema1.html` a `Tema6.html`:
    - Actualización unificada de los 6 temas HTML con estilos CSS `.mermaid` y `.mermaid svg` sin scrollbars, ancho mínimo del 60% y tamaño de texto de 15/16 px.
    - Configuración en JS `init()` de Mermaid con `fontSize: 16`, `useMaxWidth: false` y espaciado de nodos ampliado en todos los temas.
    - Estilos de figuras flotantes `.figura-flotante-izq` y `.figura-flotante-der` en los 6 temas.
  - `storage/documentos/Diagrama_Prueba_Anexo_A.md`:
    - Documento de validación integral con el diagrama hidrosanitario del Anexo A (efluente doméstico rural, fosa séptica, humedales horizontales y verticales, remoción DBO5), figuras flotantes con isotipo y tablas comparativas.
  - `pruebas/test_v1_20_0.py`:
    - Suite de 7 pruebas unitarias certificando SSOT 1.20.0, factor de escala 3x a 300 DPI, geometría proporcional acotada (3.72 in a 6.20 in de ancho, <= 8.66 in / 22 cm de alto), ausencia de scroll en HTML y en los 6 temas, reglas de figuras flotantes y conversión limpia del documento Anexo A.
  - `pruebas/test_mermaid.py`:
    - Adaptación de pruebas proporcionales a las normas de geometría editorial de la Fase 2.

### 📌 [v1.19.0] — 2026-10-28 09:49:00
* **Tipo de Incremento:** MINOR (Fase 1: Fusión interactiva de documentos en la pestaña Documentos, selección múltiple mediante checkboxes en tarjetas, barra contextual flotante con contador y opción de capítulos, modal dinámico con reordenamiento secuencial ▲ Subir / ▼ Bajar, renumeración jerárquica limpia de títulos H1, H2, H3 sin duplicación de prefijos ni afectación de H4+, separación por saltos de página editoriales en modo capítulos vs flujo continuo correlativo global, preservación de documentos originales con distintivo «🔗 en fusión» y apertura automática del consolidado).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.19.0"`
* **Componentes Afectados:**
  - `motor/capitulos.py`:
    - `limpiar_numeracion_previa(texto)`: remueve de forma idempotente prefijos numéricos preexistentes (`1.`, `1.1`, `Capítulo 1:`, etc.) garantizando que no se generen duplicaciones como `1. 1. Título`.
    - `renumerar_documento(markdown_texto, indice_capitulo)`: renumeración de encabezados H1, H2, H3 anteponiendo el número de capítulo correlativo (`1.`, `1.1`, `1.1.1`), respetando bloques de código cercados y omitiendo numeración en H4 o niveles inferiores.
    - `renumerar_flujo_continuo(textos)`: numeración correlativa corrida global a lo largo de múltiples textos sin saltos de página ni reinicios artificiales.
    - `consolidar_documentos(documentos, modo_capitulos, salto_entre_archivos)`: ensamblaje consolidado insertando directivas de salto de página editorial (`<div style="page-break-before: always; page-break-after: always; break-after: page;"></div>\n\\newpage`) en modo capítulos o unión fluida en modo continuo.
  - `app/rutas/documentos.py`:
    - Esquema Pydantic `ModeloFusion(nombres, nombre_resultado, cada_documento_es_capitulo)`.
    - Nueva función `sanitizar_nombre_documento(nombre)`: sustituye automáticamente caracteres especiales incompatibles con sistemas de archivos y rutas seguras (`:`, `+`, `*`, `?`, `"`, `<`, `>`, `|`, `/`, `\`) por conectores limpios ` - `, erradicando el error `400 Bad Request` cuando los nombres sugeridos o ingresados por el usuario contienen dos puntos o signos más.
    - Persistencia de metadatos de documentos involucrados en `storage/documentos/.fusionados.json`.
    - Enriquecimiento del endpoint `GET /api/documentos` con la propiedad booleana `en_fusion: true/false`.
    - Nuevo endpoint `POST /api/documentos/fusionar`: validación de mínimo 2 documentos, lectura secuencial, desambiguación automática de nombres duplicados, consolidación con el motor de capítulos, persistencia e indexación FTS inmediata.
  - `templates/office.html`:
    - Inclusión de la barra contextual `#barra-fusion-docs` con contador dinámico `#contador-seleccion-fusion`, casilla de verificación `#chk-fusion-capitulos`, botón `#btn-abrir-modal-fusion` y botón `#btn-cancelar-seleccion-fusion`.
    - Estructura del modal `#modal-orden-fusion` con lista dinámica `#lista-orden-fusion`, campo de texto para nombre personalizado `#input-nombre-fusion` y selector de modalidad `#chk-modal-fusion-capitulos`.
  - `static/css/office.css`:
    - Estilos visuales para tarjetas seleccionadas `.doc-card.seleccionada` y cabeceras con checkbox `.doc-card-check`.
    - Badge editorial `.chip-fusion` con icono 🔗 para identificar documentos participantes en fusiones.
    - Barra flotante contextual `.barra-fusion-docs` con diseño glassmorphism centrado y sombras suaves en el pie de la vista de Documentos.
    - Estilos de la lista de ordenación `.item-orden-fusion`, índice circular `.item-orden-indice` y controles de micro-interacción `.btn-subir` y `.btn-bajar`.
    - Regla global `.btn:disabled, button:disabled` con opacidad `0.35`, `pointer-events: none` y `cursor: not-allowed` para evidenciar con claridad el bloqueo de extremos en la lista.
  - `static/js/office.js`:
    - Estado de selección múltiple `seleccionadosDocsFusion`, sincronizado reactivamente con las tarjetas del DOM.
    - Barra contextual inteligente que se visualiza automáticamente al seleccionar 2 o más documentos.
    - Modal interactivo con reordenamiento en memoria usando `splice`, eventos independientes en botones `▲ Subir` y `▼ Bajar`, y actualización dinámica del nombre sugerido al modificar la primera posición.
    - Generación automática de nombre sugerido por defecto (`Fusion - [primer doc] y N mas`) limpio y sin caracteres prohibidos, con sanitización preventiva en cliente.
    - Extracción robusta de mensajes de error en `jsonFetch` leyendo `cuerpo?.detalle || cuerpo?.detail || cuerpo?.message`.
    - Consumo del endpoint `POST /api/documentos/fusionar` y apertura directa del archivo consolidado para su edición o visualización inmediata.
  - `pruebas/test_v1_19_0.py`:
    - Cobertura técnica de 8 pruebas unitarias certificando SSOT 1.19.0, funciones puras del motor de capítulos, flujo continuo, sanitización de nombres con caracteres especiales (`:` y `+`), endpoint API con validaciones de error y respuesta exitosa, y presencia de todos los componentes DOM.

* **Tipo de Incremento:** MINOR (Exportación directa a Markdown (.md) desde tarjetas de Docs, perfeccionamiento del renderizado paginado en Word A4 con medición DOM en dos fases (Two-Pass), contención física y vectorial de diagramas Mermaid al 100% del ancho útil, y erradicación total de páginas en blanco intermedias con el índice TOC al final tanto en pantalla como en .docx).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.18.0"`
* **Componentes Afectados:**
  - `static/js/office.js`:
    - En `listarDocumentos()`: incorporación del botón e icono de descarga `.btn-exportar-md` en cada tarjeta `.doc-card` con tooltip accesible `Exportar / Descargar Markdown (.md)`.
    - Nueva función `exportarDocumentoMd(nombre)`: generación y descarga de Blob `text/markdown;charset=utf-8` del documento persistido, con notificación visual en la interfaz y registro en el panel de entregables de la suite.
    - En `renderizarHojaWordPreview()`: reingeniería del algoritmo de paginación A4 sustituyendo la estimación heurística ciega por un motor de medición real en dos fases (Two-Pass DOM Measurement) en caja A4 de 602 px útiles con tipografía, interlineado y fórmulas computadas. Subdivisión de párrafos extensos y partición limpia antes de los límites de página (815-845 px útiles), impidiendo que el texto se desborde por la parte inferior de la hoja.
    - Manejo determinista del Índice TOC: si se ubica al final, se cierra la página de contenido previa y se inicia una página nueva dedicada, filtrando cualquier nodo o página vacía para evitar páginas en blanco intermedias.
    - Acotación de diagramas Mermaid tras su renderizado dinámico (`max-width: 100% !important; max-height: 460px !important; margin: 0 auto; display: block;`).
  - `static/css/office.css`:
    - Reglas de contención física estricta para `.hoja-word-pagina`: fijación de ancho `794px` (210 mm) y alto `1123px` (297 mm), `padding: 2.54cm`, `overflow: hidden` y sombra editorial de 30 px.
    - `.hoja-word-pagina-cuerpo`: `max-height: 870px; overflow: hidden;` impidiendo cualquier intrusión o desborde sobre el pie de página.
    - Contención de diagramas Mermaid (`.hoja-word-pagina .mermaid`, `pre.mermaid`, `svg`): centrado simétrico, fondo y bordes de código transparentes, y límite de `max-width: 100% !important; max-height: 460px !important;` garantizando que los diagramas nunca sobrepasen el margen derecho ni la altura de la página.
    - Estilos de diseño glassmorphism con micro-animaciones para el botón `.btn-exportar-md`.
  - `motor/a_docx.py`:
    - `_insertar_toc_e_indice_ecuaciones`: cuando `posicion == "final"`, purga estricta de párrafos vacíos trailing generados por Pandoc al pie del documento y sustitución del salto de párrafo intermedio `p_salto.add_break(PAGE)` por la propiedad nativa de OpenXML `p_tit.paragraph_format.page_break_before = True`, erradicando páginas en blanco fantasma en el documento Word final exportado.
  - `app/rutas/documentos.py`:
    - Incorporación del endpoint `GET /api/documentos/{nombre}/descargar` para descarga nativa como archivo adjunto (`Content-Disposition: attachment; filename="{nombre}.md"`).
  - `pruebas/test_v1_18_0.py`:
    - Suite de 5 pruebas unitarias automatizadas que certifican la versión SSOT 1.18.0, el endpoint de descarga MD, la presencia de botones y estilos en el frontend, la contención estricta A4/Mermaid en CSS y el salto de página del TOC en python-docx sin páginas vacías.

### 📌 [v1.17.4] — 2026-10-27 21:55:00
* **Tipo de Incremento:** PATCH (Formato A4 estricto en el visor PDF interactivo sin compresión cuadrada, salto de capítulo infalible y aislamiento del primer capítulo, índice/TOC garantizado en hoja nueva tanto al inicio como al final y en documentos a 2 columnas, sincronización integral de previsualización en vivo con opciones del DOM, contención de diagramas Mermaid en ancho completo evitando colapsos multi-columna, supresión absoluta del rótulo parásito BLOQUE DE CÓDIGO en Mermaid HTML, y soporte estricto de paletas personalizadas, modo de generación de hojas, cuadrícula y ajuste de celdas en exportación Excel .xlsx).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.17.4"`
* **Componentes Afectados:**
  - `static/css/office.css`:
    - Corrección del visor PDF: asignación de `aspect-ratio: 210 / 297 !important`, `max-width: 95% !important`, `max-height: 95% !important`, `width: auto !important` y `height: auto !important` a `.lienzo-pdf canvas` y `#panel-pdf .lienzo-pdf canvas`, eliminando de raíz la deformación y compresión cuadrada del canvas.
  - `static/js/visor_pdf.js`:
    - `renderPagina()`: cálculo de escala armónica basado en las dimensiones disponibles del contenedor del visor y la relación de aspecto A4 de la página (`Math.min(anchoDisp / vpBase.width, altoDisp / vpBase.height) * zoom`), proyectando siempre la hoja A4 centrada y sin distorsión.
  - `motor/a_pdf.py`:
    - Salto de capítulo: refinamiento de `salto_capitulo_css` eliminando el selector genérico `h1:first-of-type` que anulaba todos los capítulos por el anidamiento en `<section class="level1">` generado por Pandoc, e inyección estricta de `<div class="capitulo-salto-pagina">` antes de cada `H1` a partir del segundo.
    - Índice en hoja nueva: inyección de salto explícito `capitulo-salto-pagina` y asignación de `column-span: all !important; page-break-before: always !important; break-before: page !important; width: 100% !important; display: block !important; clear: both !important;` al bloque `.indice-final-documento`, garantizando su inicio en página limpia incluso en maquetaciones de 2 columnas o paper científico.
    - Anti-colapso de Mermaid en 2 columnas: envoltura de párrafos con imágenes en `<figure class="mermaid-contenedor full-width">` con `column-span: all !important; clear: both !important; width: 100% !important;`, impidiendo que los diagramas se confinen a una sola columna o colapsen sobre el texto adyacente.
  - `static/js/office.js`:
    - `refrescarVisorPdfEnVivo()` y `ejecutarExportarPdf()`: sincronización directa con los controles del DOM (`#pdf-opt-paleta`, `#pdf-opt-salto-cap`, `#pdf-opt-toc`, `#pdf-opt-modo-diseno`, `#pdf-opt-estilo`), garantizando que la vista previa en vivo refleje exactamente el PDF final exportado.
    - `ejecutarExportarExcel()`: resolución automática de IDs de paletas personalizadas (`pal_custom_...`) a su definición de 5 colores `#c1|#c2|#c3|#c4|#c5`, lectura directa de `#excel-opt-modo-hojas`, `#excel-opt-gridlines`, `#excel-opt-autofit`, `#excel-opt-ancho-col`, y transmisión simultánea de `paleta_id` y `estilo_excel`.
  - `templates/temas_html/Tema1.html` y `motor/a_html.py`:
    - Erradicación del rótulo parásito `BLOQUE DE CÓDIGO` en Mermaid HTML: exclusión estricta de diagramas en la regla `pre:not(.mermaid):not(:has(.mermaid)):not(:has(svg)):not(:has(img))::before` y supresión absoluta mediante `display: none !important; content: none !important;` para cualquier pseudoelemento de Mermaid.
  - `app/rutas/office.py`:
    - `generar_excel_de_tablas`: soporte completo de paletas personalizadas de 5 colores (`c_cab`, `c_tit`, `c_par`, `txt_cab`, `c_bor`), asignación dual de cuadrícula con `sheet_view.showGridLines = bool(mostrar_gridlines)`, soporte de `modo_hojas` ("hoja_unica" consolida en una sola hoja vs "multi_hoja" crea una por tabla), y cálculo de `autofit` excluyendo la fila de título para evitar el ensanchamiento desmedido de la columna A, respetando anchos fijos de 12, 15, 20 o 28 pt cuando `autofit=False`.
    - `sanitizar_texto_celda`: traducción de flechas ASCII (`->`, `-->`, `<-`, `<--`, `<->`, `=>`) y comandos TeX a caracteres Unicode matemáticos nativos (`→`, `←`, `↔`).
  - `pruebas/test_v1_17_4.py`:
    - 7 pruebas unitarias automatizadas que certifican el salto de capítulo, índice en hoja nueva, anti-colapso en 2 columnas, ausencia de rótulo parásito en Mermaid HTML, y las opciones avanzadas de Excel (paleta, modo de hojas, cuadrícula, autofit y flechas Unicode).

### 📌 [v1.17.3] — 2026-10-27 20:10:00
* **Tipo de Incremento:** PATCH (Resolución de paleta exclusiva de tablas y negro absoluto garantizado en Word descargado, contención fija del visor PDF con scroll independiente de miniaturas, descarga instantánea optimizada de HTML autónomo con streaming directo y caché de assets, y renderizado Unicode de flechas y subíndices de ingeniería en Excel descargado).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.17.3"`
* **Componentes Afectados:**
  - `motor/formulas.py`:
    - Ampliación del diccionario `_SIMBOLOS_TEX` con flechas y operadores matemáticos estándar (`\rightarrow`: `→`, `\to`: `→`, `\leftarrow`: `←`, `\gets`: `←`, `\leftrightarrow`: `↔`, `\Rightarrow`: `⇒`, `\Leftarrow`: `⇐`, `\Leftrightarrow`: `⇔`, `\mapsto`: `↦`, `\uparrow`: `↑`, `\downarrow`: `↓`, `\equiv`: `≡`, `\sim`: `~`, `\dots`: `...`, `\cdots`: `⋯`).
    - En `latex_a_unicode`: eliminación de comandos no mapeados residuales (`\foo` → `foo`) y limpieza de llaves `{}` residuales para garantizar celdas de Excel perfectamente legibles.
  - `app/rutas/office.py`:
    - `sanitizar_texto_celda`: detección automática y traducción de expresiones que contengan comandos TeX con barra (`\\[a-zA-Z]+`) o subíndices complejos con llaves (`[a-zA-Z]_\{[^{}]+\}`) a Unicode matemático para Excel (.xlsx), resolviendo el problema de flechas y fórmulas mostradas como código LaTeX crudo.
    - `ModeloExportar`: añadido campo `color_tabla_borde: str = ""` y propagación completa hacia `a_docx()`.
    - Endpoint streaming dedicado `POST /api/office/exportar-html`: exportación directa sin transitar por JSON pesado, con compresión y cabeceras `Content-Disposition: attachment; filename="..."`.
  - `motor/a_docx.py`:
    - `_barnizar_tabla`: añadido soporte de `color_tabla_borde` y priorización incondicional de colores personalizados (`color_tabla_cabecera`, `color_tabla_filas`) independientemente de si la paleta suave está activa. Cálculo automático de luminancia para asignar texto blanco `#FFFFFF` a cabeceras oscuras.
    - `_barnizar`: corrección de la lógica de "Negro Absoluto" (`es_modo_negro`): si el usuario selecciona Negro Absoluto o color negro, `hex_h1`, `hex_h2`, `hex_h3` se fijan estrictamente en `000000`, y los selectores visuales por defecto no pueden sobreescribirlos.
    - Firma de `a_docx()` actualizada con `color_tabla_borde`.
  - `motor/a_html.py`:
    - Implementación de `@functools.lru_cache(maxsize=1)` para `_tag_katex_css()`, `_tag_katex_js()`, y la lectura de `mermaid.min.js`, reduciendo a cero el tiempo de lectura de disco en exportaciones consecutivas.
  - `static/css/office.css`:
    - Reglas de contención rígida para `#panel-pdf`: `.area-principal-visor` fijado con `overflow: hidden !important`, `.visor-pdf` con `height: 100% !important`, `.pdf-lista-miniaturas` con `overflow-y: auto !important`, y `.lienzo-pdf` centrado con `max-height: 100%` y `object-fit: contain`, impidiendo cualquier desplazamiento o salto hacia arriba de la hoja al navegar o usar la rueda.
  - `static/js/visor_pdf.js`:
    - Detección de rueda en el lienzo: si la página cabe en pantalla, la rueda navega de forma suave entre páginas (siguiente/anterior) con prevención de burbujeo (`preventDefault`), sin saltar ni desplazar el contenedor superior.
  - `static/js/office.js`:
    - `ejecutarExportarWord`: envío consistente de `color_titulos_word: "negro"` y `color_tit_h1: "#000000"` cuando el modo seleccionado es negro absoluto, envío de los pickers de paleta de tablas, y descarga forzada segura con `document.body.appendChild(enlace)`.
    - `ejecutarExportarHtml`: conexión con `POST /api/office/exportar-html`, feedback visual inmediato con texto temporal "⏳ Generando HTML…", y descarga directa del archivo `.html`.
  - `pruebas/test_v1_17_3.py`:
    - 4 pruebas unitarias que certifican la traducción de flechas y subíndices en Excel, aplicación de paleta exclusiva de tablas en Word, respeto irrestricto del Negro Absoluto en títulos y caché de assets HTML.

### 📌 [v1.17.2] — 2026-10-27 18:15:00
* **Tipo de Incremento:** PATCH (Pipeline canónico unificado de fórmulas matemáticas offline KaTeX/OMML en toda la suite, rescate automático y reparación de fórmulas rotas del fuente, traducción determinista LaTeX → Unicode matemático en celdas de Excel (.xlsx) y renderizado KaTeX en cuadrícula, panel interactivo y modal de diagnóstico de fórmulas con localización de línea en Docs, ajuste adaptativo de tablas anchas en Word (.docx) hasta 7 pt con aviso de contención y aislamiento estricto de scroll de miniaturas en visor PDF).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.17.2"`
* **Componentes Afectados:**
  - `motor/formulas.py` (Nuevo módulo canónico SSOT):
    - `reparar_sintaxis_latex_interna`: normalización de puntos de multiplicación `·` a `\cdot`, reparación de agrupamientos rotos (`\right){codo}` → `\right)_{codo}`, adición de guiones bajos faltantes (`n{tees}` → `n_{tees}`), transformación de fracciones implícitas `({L_e}{D})` a `\left(\frac{L_e}{D}\right)` y corrección de delimitadores corruptos `\right$)` → `\right)`.
    - `rescatar_formulas_defectuosas_fuente`: rescate de fórmulas delimitadas erróneamente por corchetes planos `[...]` a `\[...\]`, reconstrucción de fórmulas partidas en múltiples líneas verticales (como subíndices partidos por saltos de línea de IA) y protección de variables explicativas en prosa `(L_e):` a `\(L_e\):`.
    - `extraer_y_proteger_formulas`: tokenización canónica de fórmulas en marcadores opacos `@@FORMULA_DISPLAY_0000@@` y `@@FORMULA_INLINE_0000@@`, respetando estrictamente bloques de código fuente preexistentes.
    - `latex_a_unicode`: traductor recursivo de LaTeX a Unicode matemático legible para Excel (subíndices `Vᵣₑₐₗ`, superíndices `x⁴` o `Q₍ₘ₃ₛ₎`, fracciones balanceadas `(A)/(B)`, raíces `√` y operadores `·`), garantizando celdas legibles sin comandos LaTeX crudos.
    - `validar_formulas_documento`: validador sintáctico estricto con reporte de línea en el texto fuente, conteo de totales, correctas y con error (detectando llaves desbalanceadas, `\left`/`\right` disparejos, subíndices vacíos o comandos corruptos).
    - `reinsertar_formulas_html` y `reinsertar_formulas_pandoc`.
  - `motor/sanear.py`:
    - Incorporación de `rescatar_formulas_defectuosas_fuente` en la fase 0 del pipeline de saneamiento previo a `_detex_prosiano()`, evitando que los comandos `\left`, `\right` y `\frac` de fórmulas mal delimitadas sean mutilados como texto plano.
  - `motor/a_docx.py`:
    - Implementación de `_calcular_tamanio_fuente_tabla`: medición del ancho disponible en dxa y longitud máxima de palabras para reducir progresivamente la fuente de la tabla hasta un mínimo de 7.0 pt antes de permitir el corte de palabras.
    - Emisión del aviso formal de auditoría `"Tabla N reducida a 7 pt; revisa su contenido"` cuando una tabla compleja alcanza el límite tipográfico inferior.
  - `motor/a_pdf.py`:
    - Configuración ampliada de extensiones de Pandoc (`markdown+tex_math_dollars+tex_math_single_backslash+tex_math_double_backslash+raw_tex+link_attributes`) para asegurar el renderizado de fórmulas complejas en el motor PDF.
  - `app/rutas/office.py`:
    - Endpoint `POST /api/office/validar-formulas`: recibe el contenido Markdown, extrae y analiza las expresiones matemáticas con número de línea, y devuelve el diagnóstico estructurado para Docs.
    - Sanitización y renderizado de tablas Excel: traducción selectiva de expresiones matemáticas a Unicode en `sanitizar_texto_celda` y encapsulado en `.mformula` para KaTeX en `renderizar_html_celda`.
  - `templates/office.html`:
    - Inclusión del botón `∑ Validar fórmulas` en la barra de herramientas `#barra-docs`.
    - Creación del modal interactivo `#modal-validar-formulas` con contadores de estado (Total, Correctas, Con error) y tarjetas descriptivas de error con línea, fragmento de código y botón de acceso rápido.
  - `static/js/office.js`:
    - Integración de `irALineaMarkdown(numLinea)` y apertura del modal de validación desde el editor de Docs.
    - Renderizado KaTeX reactivo en las celdas de la cuadrícula de la pestaña Excel (`renderizarCuadriculaExcel`).
  - `static/css/office.css` y `static/js/visor_pdf.js`:
    - Aislamiento estricto de desplazamiento vertical en el panel de miniaturas del visor PDF (`overscroll-behavior: contain` y `wheel` stopPropagation), evitando que el scroll de las miniaturas desplace la vista de lectura principal del documento.
  - `pruebas/test_formulas_v1_17_2.py`:
    - Suite de 4 pruebas unitarias que certifican al 100% los casos de prueba de fórmulas de la Sección 2.4, rescate de fórmulas reales malformadas, traducción LaTeX → Unicode y detección de errores sintácticos.
    - Resultado de suite general: 188 pruebas aprobadas (1 skipped) en pytest.

### 📌 [v1.17.1] — 2026-10-27 16:38:00
* **Tipo de Incremento:** PATCH (Resolución definitiva de renderizado universal de fórmulas matemáticas en Word, soporte omnicanal de LaTeX/fórmulas con `$..$` y entornos multilínea, renderizado garantizado de diagramas Mermaid en HTML y visor dedicado, y corrección estricta de jerarquía OpenXML ISO/IEC 29500-1 para ecuaciones en .docx).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.17.1"`
* **Componentes Afectados:**
  - `motor/a_docx.py`:
    - Corrección de la jerarquía OpenXML en `_numerar_ecuaciones_omml`: si el nodo de fórmula generado por Pandoc es un `<m:oMathPara>`, se extraen sus elementos hijos `<m:oMath>` y se agregan directamente al párrafo `w:p` de la celda de la tabla. Esto subsana una infracción del estándar ISO/IEC 29500-1 (que prohíbe `<m:oMathPara>` dentro de `<w:p>`), la cual provocaba que en varias versiones de Word (Word 2013, Word 2016, Word para Mac, Word Online) las ecuaciones no se mostraran o se renderizaran en blanco.
    - Configuración integral de extensiones de Pandoc en `_pandoc_a_docx`: `markdown+tex_math_dollars+tex_math_single_backslash+tex_math_double_backslash+raw_tex+link_attributes`. Permite procesar de forma nativa fórmulas inline `$..$`, display `$$..$$`, `\(..\)`, `\[..\]` y bloques LaTeX puros (`\begin{equation}..\end{equation}`, etc.) de cualquier Markdown.
  - `motor/a_html.py`:
    - Ampliación de expresiones regulares de blindaje (`_INLINE` y `_DISPLAY`) para capturar fórmulas con delimitadores `$..$`, `$$..$$`, `\(..\)`, `\[..\]` y entornos multilínea de LaTeX (`\begin{equation|align|aligned|gather|cases|matrix|pmatrix|bmatrix}`).
    - Corrección en el reemplazo de tokens Mermaid en `_enchufar`: reemplazo directo del párrafo `<p>MERMTOKEN...</p>` por `<pre class="mermaid">...</pre>`, eliminando el anidamiento inválido `<p><pre>` que distorsionaba el árbol DOM en los navegadores.
    - Creación de la constante limpia `_JS_INICIAR_RENDER` con la función universal `_iniciarRenderMarkflow()`. Utiliza detección de ciclo de vida (`document.readyState`), sanea en caliente el código Mermaid antes de renderizar y se inyecta homogéneamente tanto en la plantilla base como en los temas locales `Tema1..Tema6`.
  - `motor/a_mermaid.py`:
    - Ampliación de la expresión regular `_CERCO` para aceptar sangrías previas, 3 o más backticks (``` o ````) y saltos de línea CRLF/LF.
    - Mejora continua en `sanear_codigo_mermaid` para limpiar espacios antes de `:::`, convertir `<=` / `>=` y resguardar corchetes con etiquetas.
  - `static/js/office.js`:
    - En `cargarVisorHtmlDedicado()`: suscripción reactiva en `iframe.onload` para invocar inmediatamente `iframe.contentWindow._iniciarRenderMarkflow()`, garantizando que tanto los diagramas Mermaid como las ecuaciones KaTeX se procesen sin retardo ni omisión en el visor HTML.
    - En `renderizarHojaWordPreview()`: ampliación del procesamiento de ecuaciones para contemplar `.mformula.display` y aplicación de estilos CSS en `.hoja-word-pagina` con centrado simétrico y posicionamiento absoluto del número de ecuación a la derecha.
  - `pruebas/test_v1_17_1.py`:
    - Suite de 4 pruebas unitarias que verifican: inyección y disponibilidad de `_iniciarRenderMarkflow` en plantilla base y temas locales, blindaje de expresiones matemáticas con `$..$` y corchetes, generación de OMML válido sin anidamiento ilícito `m:oMathPara` dentro de `w:p`, y detección de cercos Mermaid con sangrías y backticks cuádruples.
    - Total de pruebas en verde: 184 pruebas aprobadas (1 skipped) en pytest.

### 📌 [v1.17.0] — 2026-10-27 14:20:00
* **Tipo de Incremento:** MINOR (Fase 3: Miniaturas laterales en visor PDF, Sincronización en vivo y exportación con paletas personalizadas en toda la suite, soporte de 'Century Gothic' en Word, resolución definitiva de errores de sintaxis en diagramas Mermaid, renderizado en vivo y corrección de la jerarquía OpenXML de numeración de ecuaciones `(1)` y generación estática de Tabla de Contenidos TOC en documentos `.docx`).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.17.0"`
* **Componentes Afectados:**
  - `motor/a_mermaid.py` y `motor/a_html.py`:
    - Implementación de `sanear_codigo_mermaid`: elimina automáticamente espacios en blanco que preceden a `:::` (evitando el error de lexer `'STYLE_SEPARATOR'` ante sintaxis como `A[...] :::startFill`), convierte operadores de comparación (`<=` a `≤`, `>=` a `≥`) y sanea corchetes de nodo para una compatibilidad perfecta con Mermaid v10/v11 offline.
    - Integración del saneamiento tanto en el compilador backend como en los scripts embebidos de plantillas base y temas locales HTML 1..6.
  - `static/js/app.js`:
    - Saneamiento previo a la ejecución dinámica de `window.mermaid.run` en el editor Split-View.
  - `static/js/office.js`:
    - Creación de `sanearCodigoMermaid(codigo)` expuesto en `window.sanearCodigoMermaid` y aplicado en `window.renderizarMermaidCompartido`.
    - Solución al renderizado en vivo de ecuaciones matemáticas en la vista previa de Word: procesamiento directo de los contenedores `.mformula` leyendo su atributo canónico `data-latex` mediante `katex.render()`, con numeración consecutiva `(1)`, `(2)`, etc.
    - Sincronización en vivo y reactiva de los pickers y paletas personalizadas en Word, PDF y HTML: invocación de `poblarPaletasPersonalizadasEnSelects()` al inicializar las barras laterales, permitiendo persistir y seleccionar paletas creadas en `localStorage`.
    - Enlace completo de parámetros de paleta personalizada (`modo_color_titulos`, `color_tit_h1`, `color_tit_h2`, `color_tabla_cabecera`, `color_tabla_filas`, `color_tabla_borde`) en el payload enviado al endpoint `/api/office/exportar-docx`.
    - Incorporación de `Century Gothic` al selector de fuentes de tabla en Word.
  - `motor/registro_opciones.py` y `static/js/registro_temas.js`:
    - Incorporación de `Century Gothic` a la lista de fuentes canónicas de Word (`FUENTES_WORD`).
  - `motor/a_docx.py`:
    - Corrección estructural estricta de OpenXML en `_numerar_ecuaciones_omml`: colocación de `w:fldSimple` (`SEQ Equation \* ARABIC`) como hijo directo del párrafo `w:p` en lugar de anidarlo inválidamente dentro de un `w:r`, e inyección de run interno con texto precalculado `str(contador)` para que el número de fórmula aparezca siempre entre los paréntesis `(1)` en todos los visores (Word Desktop, Word Online, LibreOffice).
    - Corrección en `_insertar_toc_e_indice_ecuaciones`: eliminación del estilo `Heading 1` autorreferencial en el encabezado de "Tabla de Contenidos", inyección válida de `fld` en el párrafo y adición de salto de página al inicio para que el TOC ocupe su propia página preliminar.
    - Subsanación de variables `rgb_h1` y `hex_h1` en la llamada al generador de TOC.
  - `app/rutas/office.py`:
    - Expansión de `ModeloExportar` con campos `modo_color_titulos`, `color_tit_h1`, `color_tit_h2`, `color_tabla_cabecera`, `color_tabla_filas` y `color_tabla_borde` propagados a `a_docx(...)`.
  - `templates/office.html`:
    - Inyección de cache-busting dinámico `?v={{ version }}` en todas las hojas de estilo y scripts locales para prevenir el consumo de scripts desactualizados por el navegador.
    - Reestructuración del visor PDF con contenedor flex `.visor-pdf-cuerpo-flex`, panel lateral izquierdo `#pdf-panel-miniaturas`, cabecera `#pdf-total-minis` y lista `#pdf-lista-miniaturas`.
  - `static/css/office.css`:
    - Reglas de diseño y maquetación glassmorphism para el panel lateral izquierdo de miniaturas del visor PDF (`.pdf-panel-miniaturas`, `.pdf-miniatura-tarjeta`, `.pdf-miniatura-lienzo`, etc.).
  - `static/js/visor_pdf.js`:
    - Implementación de `generarMiniaturas()` (renderizado progresivo a escala `0.18`) y `actualizarMiniaturaActiva()` con desplazamiento suave `scrollIntoView`.
  - `pruebas/test_v1_17_0.py`:
    - Suite de 4 pruebas unitarias validando saneamiento Mermaid, fuente Century Gothic, exportación con paleta personalizada y estructura HTML de miniaturas PDF (180 pruebas totales pasando).

### 📌 [v1.16.0] — 2026-10-27 12:41:00
* **Tipo de Incremento:** MINOR (Fase 2: Registro único de temas y barra lateral reutilizable — Arquitectura unificada, acordeón exclusivo cerrado por defecto, altura automática sin scroll interno recortado, selector de color visual interactivo sin tipear hex, persistencia por pestaña en sessionStorage y gestión de paletas personalizadas en localStorage compartidas entre Word, HTML, PDF y Excel).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.16.0"`
* **Componentes Afectados:**
  - `motor/registro_opciones.py`:
    - Enriquecimiento integral del registro único con listas canónicas de `colores: [...]` en todas las paletas (`PALETAS_HTML_TRICOLOR`, `PALETAS_TABLAS_WORD`, `PALETAS_EDITORIAL_PDF`, `PALETAS_EXCEL`), asegurando consistencia matemática y cromática entre el backend y los visores.
    - Exposición directa mediante el endpoint SSOT `GET /api/registro-opciones`.
  - `static/js/registro_temas.js`:
    - Sincronización completa con el registro del backend incorporando matrices de `colores: [...]` para cada paleta.
    - Incorporación de los métodos de gestión de paletas personalizadas en `window.MFORegistro`: `obtenerPaletasPersonalizadas()`, `guardarPaletaPersonalizada(nombre, formato, colores)` y `eliminarPaletaPersonalizada(id)` con persistencia en `localStorage` bajo la clave `mfo_paletas_personalizadas`.
    - Metadatos de compatibilidad y descripciones en temas HTML y Word.
  - `templates/office.html`:
    - Eliminación de todos los atributos estáticos `open` en los elementos `<details class="sidebar-seccion">` de las barras laterales de Word, HTML, PDF y Excel, garantizando que todas inicien cerradas por defecto.
    - Asignación de atributos semánticos `data-seccion-id` a cada sección para soporte de persistencia y acordeón exclusivo.
    - Reemplazo completo de los campos de texto manual donde el usuario debía escribir códigos hexadecimales (`#word-hex-...`) por el componente visual `.selector-color-visual` con pastilla interactiva `.pastilla-color-visual`, muestra circular `.muestra-color-circulo` y código de solo lectura `.muestra-color-codigo`.
    - Incorporación de botones de acceso rápido `.btn-abrir-modal-paletas` en las barras laterales de Word, HTML, PDF y Excel.
    - Adición del modal `#modal-paletas-personalizadas` para creación, gestión, aplicación y eliminación de paletas personalizadas (de 2 a 6 colores) compartidas en toda la suite.
  - `static/css/office.css`:
    - Regla de altura automática mandatoria para el acordeón: `details.sidebar-seccion[open] .sidebar-seccion-contenido { height: auto !important; max-height: none !important; overflow: visible !important; }`, eliminando recortes y scrolls internos artificiales.
    - Scroll unificado para toda la barra lateral: `.sidebar-cuerpo { overflow-y: auto !important; overflow-x: hidden; scrollbar-width: thin; }`.
    - Estilos visuales con tokens de diseño para `.selector-color-visual`, `.pastilla-color-visual`, `.muestra-color-circulo`, `.muestra-color-codigo`, `.input-color-nativo` y el modal `.modal-fondo` con backdrop-blur.
  - `static/js/office.js`:
    - Implementación de `configurarAcordeonExclusivo(formato)`: cierre automático de secciones abiertas al abrir otra en el mismo sidebar, con recuerdo de la sección abierta durante la sesión en `sessionStorage` (`mfo-sidebar-open-${formato}`).
    - Detención de propagación de eventos (`e.stopPropagation()`) en `.sidebar-seccion-contenido` y sus controles internos (selects, checkboxes, pickers, inputs), garantizando que ninguna interacción cierre la sección.
    - Implementación de `conectarPickersVisualesWord()` y `sincronizarPastillasWord()`: selección de color sin teclear cadenas de texto, actualizando la interfaz y persistiendo reactivamente en tiempo real.
    - Sincronización del estado visible/colapsado de la barra lateral en `sessionStorage` (`mfo-sidebar-colapsada-${formato}`) y `localStorage`.
    - Implementación de `inicializarModalPaletasPersonalizadas()` con constructor interactivo dinámico de 2 a 6 colores, validación y aplicación inmediata a los controles cromáticos de la suite.
  - `pruebas/test_fase_2.py` (NUEVO):
    - Suite de 5 pruebas unitarias verificando endpoint de registro único con colores completos, ausencia de `open` estático en details, eliminación de inputs de texto hex, presencia del modal de paletas y reglas de altura automática en CSS.

### 📌 [v1.15.0] — 2026-10-27 11:27:00
* **Tipo de Incremento:** MINOR (Fase 1: Mejoras de la pestaña Docs — Edición, Títulos, Guardar como, Manejo robusto de Imágenes referenciadas, Diagramas Mermaid dinámicos offline con captura de errores en español y eliminación de duplicidad de paneles).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.15.0"`
* **Componentes Afectados:**
  - `app/rutas/documentos.py`:
    - Incorporación de modelo `ModeloRenombrar` y endpoint `POST /api/documentos/{nombre}/renombrar` para cambio seguro de nombre y reindexación FTS5.
    - Implementación de la función `limpiar_referencias_imagenes_huerfanas` para descartar definiciones Base64 al pie que carezcan de llamadas activas en el cuerpo.
    - Saneamiento automático de imágenes huérfanas al guardar documentos (`PUT /api/documentos/{nombre}`).
  - `app/servicios/editor_markdown.py`:
    - Extracción y serialización canónica de imágenes Base64 referenciadas (`doc_a_md`): generación de `![alt][img-N]` con referencias al pie `[img-N]: data:image/...` evitando la inyección de cadenas masivas en línea.
    - Preservación de round-trip e idempotencia con `md_a_doc` y eliminación automática de definiciones huérfanas.
  - `motor/a_html.py`:
    - Incorporación de script local de Mermaid (`motor/assets/mermaid/mermaid.min.js`) para funcionamiento 100% offline y autónomo sin depender de CDN externo.
    - Captura resiliente de errores de sintaxis en `mermaid.render` con contenedor visual amigable en español (`.alerta-error-mermaid`), evitando pantallas en blanco o bloqueos ante fallos tipográficos en diagramas.
    - Soporte completo para renderizado de diagramas de ingeniería hidrosanitaria con múltiples clases cromáticas (`classDef`), decisiones y ramificaciones (verificado con diagrama Anexo A).
    - Inyección universal de scripts en plantillas base y temas HTML 1..6.
  - `templates/office.html`:
    - Inclusión en `<head>` de los activos locales de KaTeX y Mermaid (`/assets/mermaid/mermaid.min.js`, `/assets/katex/katex.min.js`, `/assets/katex/contrib/auto-render.min.js`, `/assets/katex/katex.min.css`).
    - Eliminación de la sección duplicada `<section id="panel-markflow">` de la línea 206, manteniendo un único contenedor limpio sincronizado con el riel de navegación.
    - Incorporación en la cabecera de Docs (`#panel-docs .panel-cabecera`) del campo de título editable sincronizado `#docs-titulo-input` y del botón `#btn-guardar-como-doc`.
    - Restricción estricta del selector de archivos de imagen a formatos válidos: `accept="image/png,image/jpeg,image/gif"`.
  - `static/js/office.js`:
    - Definición global de `window.escapeHtml` y `window.renderizarMermaidCompartido` para evitar excepciones `ReferenceError` y permitir renderizado compartido entre pestañas.
    - Validación estricta de nombres de documentos mediante expresión regular Unicode (`validarNombreDocumento`), rechazando caracteres peligrosos o nombres vacíos con alertas claras en español.
    - Sincronización bidireccional en tiempo real entre `#titulo-documento` (barra superior) y `#docs-titulo-input` (cabecera de Docs).
    - Implementación de `guardarComoDocumento()` con solicitud interactiva de nuevo nombre, validación y persistencia inmediata.
    - Renombrado transparente en `guardarDocumento()` cuando el usuario modifica el campo de título antes de guardar.
    - Validación de formato en `insertarImagenReferencia`: admisión exclusiva de PNG, JPG y GIF con mensaje descriptivo en español ante formatos no admitidos.
    - Advertencia preventiva si la imagen supera los 5 MB.
  - `static/js/editor_docs.js`:
    - Paridad de serialización con el motor Python: emisión de `![alt][img-N]` con recopilación de definiciones al pie en `docAMd` y saneamiento de huérfanas en el editor visual.
  - `pruebas/test_fase_1.py` (NUEVO):
    - Suite de 5 pruebas unitarias verificando validación de títulos, endpoint de renombrado, limpieza de huérfanas, serialización referenciada y renderizado del diagrama Mermaid del Anexo A con 4 `classDef`.

### 📌 [v1.14.0] — 2026-10-26 22:25:00
* **Tipo de Incremento:** MINOR (Paleta de colores personalizada en cuadros y títulos de Word, renderizado reactivo en tiempo real de todas las opciones de maquetación Word, aviso de inmutabilidad de temas nativos, round-trip completo con descarga directa a Markdown y carga a Docs, paneles dedicados de Manual de Usuario y motor clásico MarkFlow en el riel, y corrección de aislamiento visual de pestañas eliminando fuga de PDF).
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.14.0"`
* **Componentes Afectados:**
  - `static/css/office.css`:
    - Corrección de la precedencia CSS de `.app-con-sidebar-derecha` para respetar `display: none` cuando no tenga la clase `.activo`, eliminando la fuga visual de la cabecera y botón exportar de PDF al final de Word y la superposición entre paneles de pestañas.
    - Estilos para la sección de tema personalizado en Word, aviso de tema nativo inmutable (`.alerta-tema-inmutable`) y controles cromáticos de títulos y tablas.
  - `templates/office.html`:
    - Incorporación en `#sidebar-word-opciones` del aviso `#aviso-tema-word-lateral` cuando se seleccionan plantillas nativas (`tema1`, `tema2`, `tema3`).
    - Incorporación de selectores para color de títulos H1/H2 (`#word-picker-tit-h1`, `#word-picker-tit-h2`) y selector de modo de color de títulos.
    - Incorporación de configuración integral de cuadros y tablas: paleta suave o paleta custom con selectores de color RGB para cabecera (`#word-picker-tabla-cabecera`), filas alternas (`#word-picker-tabla-filas`) y bordes (`#word-picker-tabla-borde`).
    - En la sección `♻️ Round-Trip .docx`: añadido de botones `#btn-rt-descargar-md` (extraer a Markdown descargable) y `#btn-rt-cargar-docs` (cargar directamente en el editor Docs).
    - En el riel lateral de navegación: añadido botón dedicado `📖 Manual` (`data-app="manual"`).
    - Agregado del panel `#panel-markflow` (embebido con `/clasico`) y `#panel-manual` (manual de usuario técnico integral, interactivo y accesible).
  - `static/js/office.js`:
    - Implementación de `actualizarVisibilidadTemaWord()` para conmutar dinámicamente entre el aviso de tema nativo inmutable y la paleta personalizada.
    - Implementación de `conectarPickersHexWord()` para sincronizar inputs de tipo color con sus campos de texto hexadecimal.
    - Reescritura integral de `renderizarHojaWordPreview()` para inyectar en tiempo real estilos CSS por hoja A4 respondiendo a cada cambio en la barra lateral:
      * Paleta y colores de cuadros y tablas (cabecera con cálculo dinámico de luminancia y contraste para texto blanco/oscuro, alternancia de filas `tr:nth-child(even)` y bordes).
      * Tipografía y tamaño de fuente en tablas.
      * Normas APA 7ma Edición (márgenes de 2.54 cm, sangría en primera línea de 1.27 cm y formato de tablas sin líneas verticales).
      * Numeración automática de ecuaciones correlativas `(1)`, `(2)` alineadas a la derecha.
      * Generación dinámica y ubicación del Índice General (TOC).
      * Alineación y formato del pie de página con paginación dinámica.
    - Lógica de Round-Trip: descarga instantánea de Markdown extraído (`Blob text/markdown`) y transferencia directa al editor Docs con actualización de estado y previsualización.
    - Enlace de visor PDF local para compilación binaria y paso directo del buffer vía `MFOPDF.cargarDesdeArrayBuffer()`.
  - `static/js/plantillas.js`:
    - Elevación de `actualizarRenderHtmlResultado` al ámbito superior de la IIFE, erradicando el error `ReferenceError` que bloqueaba la ejecución de scripts al iniciar la aplicación.
  - `static/js/visor_pdf.js`:
    - Soporte para renderizado directo desde `ArrayBuffer` (`window.MFOPDF.cargarDesdeArrayBuffer`).

### 📌 [v1.13.0] — 2026-10-26 20:20:00
* **Tipo de Incremento:** MINOR (Rediseño integral de exportación: Docs como SSOT de contenido, barras laterales deslizables de 340 px conectadas al registro único centralizado de temas y opciones, visor Word de páginas continuas A4 maquetadas, endpoint dedicado para exportación de PDF solucionando descarga de .htm, soporte de Excel multi-hoja y copiado enriquecido HTML/TSV, pestaña independiente de Entregables en el riel principal e inserción de imágenes por referencia Markdown al pie del documento con paste/drag-and-drop)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.13.0"`
* **Componentes Afectados:**
  - `motor/registro_opciones.py` (NUEVO):
    - Single Source of Truth (SSOT) backend para temas, anchos, paletas tri-color, fuentes, estilos de maquetación, modos de columnas y opciones de hojas Excel.
    - Funciones `obtener_registro_completo()`, `obtener_arbol_opciones()` y `obtener_defaults(formato)`.
  - `app/rutas/api.py`:
    - Endpoint `GET /api/registro-opciones` para exponer el árbol de opciones homologado en JSON.
  - `app/rutas/office.py`:
    - Endpoint dedicado `POST /api/office/exportar-pdf` con `Content-Type: application/pdf`, compilación en memoria y cabeceras estrictas, resolviendo la descarga errónea de archivos `.htm`.
    - Actualización de `generar_excel_de_tablas` con parámetros `modo_hojas` (`multi_hoja` vs `hoja_unica`), `mostrar_gridlines`, `tamano_fuente` y alias `paleta_id`.
  - `static/js/registro_temas.js` (NUEVO):
    - Módulo SSOT en frontend exponiendo `window.MFORegistro` con estructuras completas, persistencia en `localStorage`, métodos `obtenerOpciones(formato)`, `guardarOpciones(formato, valores)` y `restablecerOpciones(formato)`.
  - `templates/office.html`:
    - Eliminado el panel lateral de conversión `#panel-lateral-conversion` de Docs. Docs queda limpio para edición, previsualización y saneamiento.
    - Incorporación de botón de navegación `Entregables` (`data-app="entregables"`) en el riel lateral izquierdo.
    - Reestructuración de `#panel-word` con visor de páginas A4 continuas maquetadas (`.hoja-word-pagina`) y barra lateral deslizable `#sidebar-word-opciones` (340 px) con botón flotante `#btn-toggle-sidebar-word`.
    - Reestructuración de `#panel-pdf` con barra lateral deslizable `#sidebar-pdf-opciones` (340 px) y botón flotante `#btn-toggle-sidebar-pdf`.
    - Reestructuración de `#panel-html` con barra lateral deslizable `#sidebar-html-opciones` (340 px) y botón flotante `#btn-toggle-sidebar-html`.
    - Reestructuración de `#panel-tablas` con barra lateral deslizable `#sidebar-excel-opciones` (340 px) y aviso visual cuando el documento activo no contiene tablas Markdown (`#excel-sin-tablas-aviso`).
    - Creación del panel `#panel-entregables` para gestión unificada de descargas y auditoría de documentos exportados.
  - `static/css/office.css`:
    - Reglas CSS para `.barra-lateral-derecha` (ancho fijo de 340 px, transform 250ms ease, sombras suaves de elevación y accesibilidad con `prefers-reduced-motion`).
    - Reglas CSS para botones toggle flotantes (`.btn-toggle-sidebar-flotante`).
    - Estilos de secciones colapsables (`details.sidebar-seccion`), campos de opciones, radios, selects y botones de acción.
    - Estilos para hojas Word A4 continuas (`.hoja-word-pagina`, 210mm x 297mm con simulación de salto de página y márgenes de 2.54cm).
    - Estilos para la pestaña de Entregables y badges con códigos cromáticos canónicos (Word `#2563eb`, PDF `#dc2626`, HTML `#ea580c`, Excel `#16a34a`, MD `#10b981`).
  - `static/js/office.js`:
    - Inserción de imágenes por referencia Markdown `![nombre][img-N]` con `[img-N]: data:...` al pie del documento, soporte para drag-and-drop, selección de archivos y atajo de teclado / pegado `paste` con validación de tamaño (< 5 MB).
    - Inicialización y sincronización bidireccional reactiva de las 4 barras laterales (Word, PDF, HTML, Excel) con `MFORegistro` y `localStorage` con debounce de 300 ms.
    - Conexión de botones *Restablecer valores* en cada barra lateral.
    - Sincronización transparente de Docs como SSOT: visores y exportaciones siempre leen el documento activo de Docs, eliminando descargas de documentos vacíos.
    - Copiado de tablas al portapapeles en formato enriquecido (MIME `text/html` + fallback `text/plain` TSV).
    - Registro automático en tiempo real de todos los artefactos generados en la pestaña Entregables.
  - `pruebas/test_v1_13_0.py` (NUEVO):
    - Suite de pruebas unitarias verificando SSOT, registro de opciones, endpoint de exportación DOCX binario real y presencia de todos los componentes UI. Pase del 100 % de pruebas en pytest (166 pasadas, 1 ignorada intencionalmente).
  - Hotfixes de estabilidad y paginación:
    - Corrección en `poblarSelectSiVacio` y `registro_temas.js` para evitar bloqueos por `undefined`, restableciendo la navegación de todas las pestañas del riel.
    - Conexión de `POST /api/office/exportar-docx` con `motor.a_docx.a_docx` para generar documentos Word binarios completos y no vacíos.
    - Implementación de partición dinámica en múltiples páginas A4 (`.hoja-word-pagina`) con numeración `Página X de Y` y pie de página integrado.

### 📌 [v1.12.0] — 2026-10-26 15:35:00
* **Tipo de Incremento:** MINOR (Scroll sincronizado bidireccional y proporcional en Docs, inserción de figuras encapsuladas con details/summary y numeración automática, botón de limpieza global de notas, panel lateral retráctil con 3 subpestañas homologadas HTML/DOCX/PDF, visor Word maquetado estilo página A4, solución de pantalla en blanco HTML, rediseño de tablas fijas estilo Excel con columnas de relleno y sidebar retráctil de paletas openpyxl)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.12.0"`
* **Componentes Afectados:**
  - `templates/office.html`:
    - Depuración del riel vertical eliminando el botón intermedio de "Conversión Completa" (`markflow`), preservando únicamente el acceso final de la suite.
    - Incorporación en la barra de Docs de dos nuevos botones: `🖼️ Imagen` (`#btn-docs-insertar-img` / `#input-docs-img-file`) para figuras numeradas en `<details><summary>` y `🚫 Quitar Notas` (`#btn-docs-quitar-todas-notas`) para remoción global de marcas `>`.
    - Reestructuración del panel lateral retráctil `#panel-lateral-conversion` en 3 subpestañas completas (`HTML`, `DOCX`, `PDF`) homologadas con los parámetros del motor clásico (temas, fuentes, tamaños, interlineado, paletas, márgenes, dos columnas, running header y firmas).
    - Rediseño de la pestaña Word (`#panel-word`) con layout dividido: columna izquierda con controles y round-trip, y columna derecha con visor maquetado estilo hoja A4 (`#hoja-word-papel`) con botón de refresco desde Docs.
    - Rediseño de la pestaña Tablas (`#panel-tablas`): botón selector de estilos de tabla (`#btn-toggle-sidebar-estilos-tablas`), mesa de trabajo fija `.excel-mesa-trabajo` con cuadrícula acotada y sidebar retráctil derecho `#sidebar-estilos-tablas` con 5 paletas ejecutivas.
  - `app/rutas/api.py`:
    - Corrección en `render_preview` aceptando indistintamente `{ texto: ... }` o `{ markdown: ... }`, eliminando el problema de pantalla en blanco en el visor HTML.
  - `app/rutas/office.py`:
    - Implementación de `sanitizar_texto_celda(texto)` y `renderizar_html_celda(texto)` para separar el texto plano de las marcas HTML en la vista y en el archivo binario.
    - Actualización de `extraer_tablas_markdown` proporcionando `cabeceras_limpias`, `cabeceras_html`, `filas_limpias` y `filas_html`.
    - Actualización de `generar_excel_de_tablas` con soporte de 5 paletas ejecutivas (`clasico`, `azul`, `gris`, `esmeralda`, `monocromo`), eliminación de asteriscos en celdas y formateo profesional con `openpyxl`.
    - Enriquecimiento de `ModeloCompilacionCompleta` y `compilar_completo` para procesar los parámetros avanzados de las 3 subpestañas y el estilo de Excel.
  - `static/css/office.css`:
    - Estilos ergonómicos para los botones de la barra de Docs (`.bd-quitar-notas`, `.bd-imagen`).
    - Estilos para la barra de navegación de subpestañas del panel lateral (`.sub-tabs-lat-nav`, `.sub-tab-lat-btn`, `.sublat-panel`).
    - Estilos para el visor Word maquetado (`.split-word-layout`, `.hoja-word-marco`, `.hoja-word-papel` con sombra de papel, márgenes de 2.54cm y tipografía formal).
    - Estilos para la cuadrícula fija de Excel (`.tabla-excel-fija`, anchos acotados de 140px-280px) y el sidebar retráctil derecho `#sidebar-estilos-tablas`.
  - `static/js/office.js`:
    - Implementación de scroll sincronizado bidireccional y proporcional en Docs (`vincularScrollDocs`) entre el editor y el iframe.
    - Lógica de inserción de imágenes con FileReader en Base64, conteo correlativo de figuras y encapsulamiento en `<details open><summary>🖼️ <strong>Figura N: Nombre</strong></summary>...</details>`.
    - Lógica de remoción global de notas mediante regex (`^\s*>\s?` y tags `[!NOTE]`, etc.).
    - Navegación de las 3 subpestañas en el panel lateral y envío de parámetros enriquecidos a `/api/office/compilar-completo`.
    - Función `renderizarHojaWordPreview` para el visor maquetado de Word conectado a `#btn-refrescar-vista-word` y a la apertura de la app.
    - Renderizado de cuadrícula fija de Excel con relleno automático de columnas vacías (mínimo 8 columnas A..H) para evitar estiramiento extremo, renderizado de celdas sanitizadas sin asteriscos y descarga con la paleta seleccionada en el sidebar.
  - `pruebas/test_v1_12_0.py`:
    - Suite de 7 pruebas unitarias cubriendo sanitización, extracción de tablas, paletas Excel, compatibilidad en render-preview, exportación con estilo y compilación multiformato.

### 📌 [v1.11.0] — 2026-10-26 13:20:00
* **Tipo de Incremento:** MINOR (Panel lateral retráctil de conversión multiformato, solución de Word en blanco, visor HTML interactivo, hoja de cálculo Excel de tablas con copiado TSV y visor PDF con eliminación segura)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.11.0"`
* **Componentes Afectados:**
  - `app/rutas/office.py`:
    - Incorporación del endpoint `DELETE /api/office/pdfs/archivo/{ruta_relativa:path}` con validación estricta anti-traversal para borrado seguro de PDFs en `salidas/`.
    - Implementación de `extraer_tablas_markdown(texto_md)` con parser tolerante a tablas Markdown GFM con o sin divisorias explícitas.
    - Implementación de `generar_excel_de_tablas(tablas)` usando `openpyxl` con estilización ejecutiva (cabecera con gradiente de color, bordes finos, alineación numérica y autoajuste de anchos de columna).
    - Creación de endpoints `POST /api/office/extraer-tablas` y `POST /api/office/exportar-tablas-excel`.
    - Creación del endpoint `POST /api/office/compilar-completo` que procesa coordinadamente documentos a Word (.docx), PDF (.pdf), HTML interactivo (.html), Excel (.xlsx) y Markdown saneado (.md) con opciones avanzadas de diseño.
  - `templates/office.html` e `index.html`:
    - Actualización del riel de navegación `.riel-apps` incorporando accesos a `html` (🌐 Visor HTML) y `tablas` (📊 Hoja de Cálculo / Tablas Excel).
    - Incorporación de botón de importación de Markdown (`#btn-importar-md` / `#input-md-importar`) en el panel de Documentos.
    - Rediseño de la barra de herramientas del editor Docs: botón de inserción de Notas (`📝 Nota`) y botón dinámico `#btn-modo-fuente` con indicación de estado activo.
    - Creación del panel lateral retráctil `#panel-lateral-conversion` a la derecha del editor Docs con selector de formatos, tema Word, tema PDF, tema HTML, tipografías e interlineado.
    - Panel Word (`#panel-word`): auditoría de estructura previa a descarga y botón de descarga directa sincronizado.
    - Panel PDF (`#panel-pdf`): incorporación de botones de descarga directa y eliminación (`🗑️ Eliminar`) en la barra del visor.
    - Panel HTML (`#panel-html` - NUEVO): visualizador `<iframe>` interactivo con selector dinámico de temas y descarga directa.
    - Panel Tablas Excel (`#panel-tablas` - NUEVO): interfaz de hoja de cálculo con barra de fórmulas, cuadrícula mallada Excel (columnas A, B, C... filas 1, 2, 3...), botón flotante para copiar al portapapeles en formato TSV y exportación a libro `.xlsx`.
    - Homologación de atributos `accept` en zonas de suelta e inputs a `.md,.markdown,.txt,text/markdown,text/plain`.
  - `static/css/office.css`:
    - Aumento de tamaño y ergonomía de botones de la barra de Docs (`.bd-btn` a 34px de alto con fuente 0.88rem).
    - Estilo de alto contraste para `#btn-modo-fuente.activo` (verde esmeralda `#10b981` con brillo sutil y contraste óptimo en temas claro y oscuro).
    - Estilos fluidos de transición para el panel lateral retráctil (`.panel-lateral-conversion`).
    - Estilos completos de hoja de cálculo para tablas: `.excel-barra-superior`, `.excel-cuadricula-scroll`, `.tabla-excel` con celdas seleccionables y contornos azules estilo Microsoft Excel.
  - `static/js/office.js`:
    - Solución definitiva al error de archivos Word en blanco mediante la función centralizadora `obtenerMarkdownActual()`, que prioriza `window.MFOEditor.getTexto()` sobre el textarea inactivo.
    - Control de colapso y apertura del panel lateral retráctil con invocación a `/api/office/compilar-completo`.
    - Dinamización de `#btn-modo-fuente` con actualización de etiquetas e inserción de notas `> [!NOTE]` / `> **Nota:** ` según el modo de edición.
    - Lógica de la hoja de cálculo: selector de tablas, renderizado de matriz, copiado al portapapeles en formato TSV (listo para pegar en Excel con Ctrl+V) y descarga de `.xlsx`.
    - Carga en tiempo real del visor HTML interactivo con inyección del tema seleccionado.
  - `static/js/editor_docs.js`:
    - Incorporación del comando `cmdNota` e integración en el dispatcher de comandos de ProseMirror.
  - `static/js/visor_pdf.js`:
    - Conexión de descarga directa y botón de eliminación en barra superior y en tarjetas del catálogo con confirmación y llamada a `DELETE /api/office/pdfs/archivo/...`.
  - `pruebas/test_v1_11_0.py`:
    - Batería completa de pruebas de integración y seguridad (extracción de tablas, exportación Excel, borrado anti-traversal, compilación completa multiformato y verificación de versión SSOT).

### 📌 [v1.10.0] — 2026-10-26 11:55:00
* **Tipo de Incremento:** MINOR (Reincorporación condicional de JSON y paquetes ZIP, tarjetas horizontales modernas con iconos vectoriales SVG, tabla de candidatos con altura fija/scroll y rediseño de pantalla dividida con renderizado HTML en vivo)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.10.0"`
* **Componentes Afectados:**
  - `templates/office.html` y `templates/index.html`:
    1. Rediseño completo de la Tarjeta 3 de Creación de Plantilla (Editor y Previsualización):
       - Columna izquierda: previsualización interactiva HTML en vivo mediante `<iframe>` sandbox con estilos y KaTeX completos (`/api/render-preview`).
       - Columna derecha: panel dedicado a manipular placeholders con resaltado visual (`contenteditable`) y editor de código fuente subyacente.
       - Barra conmutadora con 3 modos: `🖥️ Dividida (Resultado / Variables)`, `👁️ Solo Resultado HTML`, `📝 Solo Manipular Placeholders`.
    2. Incorporación de casillas de verificación para la descarga condicional en el Paquete de Plantilla:
       - Plantilla Markdown limpia (`.md`).
       - Hoja de Datos Excel (`.xlsx`).
       - Estructura JSON (`.json`) condicional.
       - Paquete comprimido integral (`.zip`).
    3. Reconfiguración del contenedor de entregables `#lista-archivos-plantilla-generados` y `#lista-documentos-generados-grid` con clase de layout `.entregables` para disponer tarjetas horizontales similares a las de conversión completa.
    4. Adición de la casilla de verificación JSON (`#chk-usar-formato-json`) en los formatos de entrega de la sub-pestaña "Usar Plantilla".
  - `static/css/components.css`:
    - Incorporación de tokens, paletas y badges dedicados para formatos `.formato-xlsx`, `.formato-json`, `.formato-zip`, `.badge-xlsx`, `.badge-json`, `.badge-zip`.
    - Limitación de altura para la tabla de candidatos: contenedor `.tabla-candidatos-contenedor` acotado con `max-height: 380px`, scroll vertical/horizontal suave y cabecera pegajosa `position: sticky; top: 0` para evitar desplazamientos infinitos al arrastrar documentos extensos.
    - Clases de layout de la pantalla dividida: `.col-resultado-html-plantilla`, `.col-manipular-placeholders` y `.preview-render-html-box`.
  - `static/js/plantillas.js`:
    - Incorporación del diccionario de íconos vectoriales modernos `svgIconosModernos` (MD, XLSX, JSON, ZIP, DOCX, PDF, HTML) con SVG nítidos y escalables.
    - Implementación de la función generadora `crearTarjetaEntregable(...)` para estandarizar la renderización de tarjetas de descarga horizontales con nombre, peso legible, descripción, botón de descarga directa y botón de previsualización para HTML/JSON.
    - Conexión de `actualizarRenderHtmlResultado(mdTexto)` con debounce para compilar y reflejar en vivo los cambios en el iframe de la columna izquierda.
    - Integración de casillas de verificación (`#chk-paquete-md`, `#chk-paquete-xlsx`, `#chk-paquete-json`, `#chk-paquete-zip`) en `btnGenerarPaquete`.
    - Soporte completo de descarga JSON en `btnEjecutar` de la pestaña "Usar Plantilla".
  - `app/rutas/plantillas.py`:
    - Generación y empaquetado de archivo comprimido `paquete_<slug>.zip` mediante `zipfile.ZipFile` en memoria.
    - Retorno estructurado de metadatos con tamaño legible (`tamano`) en KB tanto en `crear_paquete` como en `generar-documentos`.
  - `pruebas/test_plantillas.py`:
    - Cobertura de pruebas ampliada verificando `paquete_zip`, `tamano` y compilación en formato `json`.
* **Descripción Técnica de Cambios:**
  1. Se reincorporó de manera integral la opción de generar y descargar esquemas JSON (`.json`) y paquetes ZIP (`.zip`), permitiendo al usuario activarlos o desactivarlos mediante casillas de verificación en la tarjeta "¡Paquete de Plantilla Generado Exitosamente!".
  2. Se sustituyó la renderización básica de descargas por tarjetas horizontales modernas (`.tarjeta-entregable`) con íconos vectoriales SVG modernos y badges de formato, alineadas a la experiencia de conversión completa.
  3. Se acotó la altura de la tabla de revisión de placeholders candidatos a un máximo de 380px con scrollbar estilizada y cabecera fija para garantizar ergonomía de uso con documentos largos.
  4. Se rediseñó la pantalla dividida orientándola a resultados: previsualización HTML interactiva completa a la izquierda y panel de manipulación de placeholders y variables a la derecha.

---

### 📌 [v1.9.0] — 2026-10-26 09:22:00
* **Tipo de Incremento:** MINOR (Evolución completa del editor de plantillas: vista ancha 96vw, view switcher Split/Código/Visual, WYSIWYG bidireccional, autoreemplazo global, tooltip contextual flotante, app independiente en riel vertical de Office, exportación exclusiva a Excel sin JSON e inclusión de Excel en pestaña de generación)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.9.0"`
* **Componentes Afectados:**
  - `templates/office.html`:
    1. Integración de la app `Plantillas` (`data-app="plantillas"`) directamente en el riel de navegación vertical independiente, fuera de los iframes clásicos.
    2. Incorporación del panel `<section id="panel-plantillas" class="app-panel">` con contenedor `.plantillas-ancho-extendido` (96vw, máx. 1600px).
    3. Barra conmutadora de modos de vista `.view-switcher-plantilla` (🖥️ Dividida, 📝 Solo Código, 👁️ Solo Visual WYSIWYG).
    4. Panel visual con `contenteditable="true"` y tooltip interactivo flotante `#tooltip-ph-flotante` para renombrar y revertir placeholders.
    5. Omitida la descarga de JSON en el paquete de creación, dejando exclusivamente Markdown (.md) y Hoja Excel (.xlsx).
    6. Incorporada la casilla de verificación `Hoja Excel de Datos (.xlsx)` en la tarjeta `3 · Formatos de Entrega y Generación` para la descarga directa de libros Excel generados con datos consolidados.
  - `templates/index.html`:
    1. Actualización sincronizada de las tarjetas de edición y previsualización con selector de 3 modos (Split, Código, Visual).
    2. Tooltip interactivo contextual flotante.
    3. Descarga exclusiva en Excel en tarjeta 4 y casilla de descarga Excel (.xlsx) en sección de generación sin JSON.
  - `static/js/plantillas.js`:
    1. Mapeo global de valores manuales originales `mapaValoresManuales` al seleccionar frases con el cursor.
    2. Autoreemplazo global de frases seleccionadas en todo el documento Markdown.
    3. Recolección de valores manuales y envío a `/api/plantillas/crear-paquete` para que las columnas de Excel contengan los datos seleccionados por el usuario.
    4. Eliminación de enlaces y botones de descarga de formato JSON en el paquete generado.
    5. Soporte en tiempo real para generar documentos en formato Hoja Excel (`.xlsx`) en `btnEjecutar` y formateo de badge verde `EXCEL (.XLSX)`.
  - `static/js/office.js`:
    1. Sincronización en `abrirApp("plantillas")` para activar e invocar `window.MFOPlantillas.abrir()`.
  - `motor/plantillas.py` y `app/rutas/plantillas.py`:
    1. Extracción exhaustiva de placeholders tanto automáticos como manuales en `crear_paquete`.
    2. Asignación del valor manual original en la columna B del Excel generado.
    3. Generación directa de libros Excel `.xlsx` como formato de salida en `/api/plantillas/generar-documentos`.
  - `pruebas/test_plantillas.py`:
    1. Nuevas pruebas de integración `test_api_generar_formato_excel_y_placeholders_manuales` validando la inclusión de placeholders manuales y generación de `.xlsx`.
* **Descripción Técnica de Cambios:**
  1. Se implementó la restricción solicitada: solo permitir descarga en Excel (`.xlsx`) y omitir JSON (`.json`) en las opciones de descarga de la suite.
  2. Se añadió la opción de descarga de datos en formato Excel en la sub-pestaña `3 · Formatos de Entrega y Generación` (Finalidad B: Usar plantilla), permitiendo compilar tanto documentos textuales (HTML/DOCX/PDF/MD) como libros estructurados de Excel con los datos de cada proyecto.
  3. Se aseguró que los placeholders creados manualmente reconozcan y guarden su valor original en las columnas del archivo Excel.

---

### 📌 [v1.8.0] — 2026-10-26 08:05:00
* **Tipo de Incremento:** MINOR (Incorporación de la pestaña "Plantillas" con placeholders dinámicos {{nombre}}, detección heurística, exportación/importación en Excel .xlsx y JSON, y compilación multiformato por lotes)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.8.0"`
* **Componentes Afectados:**
  - `motor/plantillas.py`:
    1. Detección heurística de patrones (etiqueta: valor, números con unidad, RUC/cédula ecuatoriana, correo, teléfono, fechas, coordenadas) clasificados por niveles de confianza (alta, media, baja).
    2. Aislamiento y protección estricta de bloques matemáticos (`$$...$$`, `\(...\)`, `\[...\]`) y bloques de código (` ``` `).
    3. Normalización estricta de nombres de placeholders: minúsculas, dígitos, guion bajo, sin tildes, máximo 60 caracteres.
    4. Generador y lector de libros Excel `.xlsx` estructurados con `openpyxl`: hoja única 'Datos', columna A `placeholder`, columnas B en adelante por proyecto, estilos con fondo `#eef0fa` y anchos automáticos.
    5. Generador y parser de diccionarios de especificación `plantilla_<proyecto>_datos.json`.
    6. Motor de auditoría y validación de datasets por proyecto (completos, vacíos, tipo incorrecto, sobrantes).
    7. Motor de sustitución y marcado en rojo `[nombre]` de variables vacías sin bloquear la compilación del documento (Sección 7.3).
  - `app/rutas/plantillas.py`:
    1. `POST /api/plantillas/analizar`: Análisis y detección de candidatos en Markdown.
    2. `POST /api/plantillas/crear-paquete`: Ensamblado de `plantilla_<proyecto>.md`, `.xlsx` y `.json` con enlaces de descarga efímeros en `/api/descargar`.
    3. `POST /api/plantillas/leer-datos`: Ingesta y parseo multipart de `.xlsx` y `.json`.
    4. `POST /api/plantillas/extraer-placeholders`: Extracción de tags presentes en plantillas Markdown.
    5. `POST /api/plantillas/validar`: Validación de consistencia previa a la generación.
    6. `POST /api/plantillas/generar-documentos`: Generación individual o en lote para HTML, Word, PDF y Markdown reutilizando los pipelines y temas oficiales.
  - `templates/index.html`:
    1. Nueva pestaña vertical principal `🧩 Plantillas` (`#tab-plantillas`).
    2. Nuevo panel `<section id="panel-plantillas">` con sub-pestañas `✏️ Crear plantilla` y `📄 Usar plantilla`.
    3. Zonas de arrastre `.zona-suelta`, tabla de candidatos interactiva con inputs editables y selectores de tipo, editor con previsualización de tags visuales clicables `[nombre]`, panel de validación semántica con contadores y área de descargas.
  - `static/css/components.css`:
    1. Estilos para `.tabla-candidatos`, `.placeholder-tag` (con fondo suave, borde indigo y hover dinámico), `.placeholder-vacio` (rojo suave), y cuadrícula de validación `.resumen-validacion-grid`.
  - `static/js/plantillas.js`:
    1. Lógica completa del flujo A (arrastre de base, análisis, tabla dinámica, conversión manual por selección de texto, tags interactivos para renombrar/deshacer y descarga de paquetes).
    2. Lógica completa del flujo B (carga de plantilla y Excel/JSON, selector de proyecto o generación por lotes, panel reactivo de validación y generación multiformato).
  - `requirements.txt`: incorporación de `openpyxl>=3.1.2`.
  - `app/principal.py`: registro del router `/api/plantillas`.
  - `pruebas/test_plantillas.py`: 11 pruebas unitarias y de integración de motor y endpoints API (100% aprobadas).
* **Descripción Técnica de Cambios:**
  1. **Cumplimiento exhaustivo de `docs/mejoras/mejoras_app_03_placeholders.md`:** Se implementó la Fase 1 completa respetando todas las reglas de negocio, formatos de archivo y contratos visuales.
  2. **Gobernanza SemVer y SSOT:** La UI consume dinámicamente la versión `1.8.0` desde `app/version.py`.
  3. **Preservación incondicional:** No se modificó la lógica de las pestañas preexistentes ("Tus datos", "Salida", "Manual de Usuario").

### 📌 [v1.7.0] — 2026-10-25 22:08:00
* **Tipo de Incremento:** MINOR (Implementación integral de mejoras editoriales: saltos de capítulo estrictos y defaults institucionales en PDF, inyección de tokens CSS directos en HTML, selector de títulos negro vs paleta tricolor y control de tablas suaves vs cuadros personalizados en Word)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.7.0"`
* **Componentes Afectados:**
  - `motor/a_pdf.py`:
    1. Reglas CSS de salto de página estricto (`page-break-before: always !important; break-before: page !important;`) para `h1, .chapter-title, .capitulo-break`, con excepción estricta para `h1:first-of-type` evitando página en blanco inicial.
    2. Valores por defecto institucionales obligatorios: `salto_capitulo = True`, `numerar_paginas = True`, `running_header = True`, `indice_al_final = True`.
    3. Firma institucional técnica por defecto: `Ing. Patricio Sarmiento Reinoso, Mgst.` y cargo `CONSULTOR`.
    4. Parser de paletas personalizadas tricolor (`#c1|#c2|#c3`) con derivación armónica para PDF.
  - `motor/a_html.py`:
    1. Inyección directa de tokens y variables CSS en `:root`, `[data-theme="light"]` y `body.custom-theme` (`--primary-color`, `--secondary-color`, `--accent-color`, `--primary`, `--accent`, `--table-header-bg`, `--card-alt`).
    2. Sobrescritura estricta para `h1`, `h2`, `h3` y `.subtitle`.
    3. Soporte para paletas personalizadas tricolor en formato compuesto (`#c1|#c2|#c3`).
  - `motor/a_docx.py`:
    1. Paletas de títulos ampliadas a 3 colores canónicos (Primario H1, Secundario H2/H3, Acento para bordes de notas y llamadas).
    2. Nuevo parámetro `modo_color_titulos` con soporte para `"negro"` (todos los títulos en `#000000`) vs `"paleta"` (aplica color primario a H1, secundario a H2/H3 y acento a bordes). Modo `"auto"` para compatibilidad retroactiva.
    3. Parámetro `paleta_suave_tablas` activo por defecto; al desactivarse aplica colores personalizados `color_tabla_cabecera` y `color_tabla_filas` a las tablas del documento.
  - `app/rutas/api.py`:
    1. Extracción y mapeo de `modo_color_titulos`, `paleta_suave_tablas`, `color_tabla_cabecera` y `color_tabla_filas`.
    2. Inyección de valores por defecto requeridos para PDF (`salto_capitulo_pdf=True`, `running_header_pdf=True`, `indice_al_final=True`, firma institucional).
  - `templates/index.html`:
    1. Checkbox "Salto de página por capítulo (H1)", "Numerar páginas", "Encabezado continuo" e "Índice de contenido al final" marcados por defecto en PDF Editorial.
    2. Inputs de firma institucional prellenados con "Ing. Patricio Sarmiento Reinoso, Mgst." y "CONSULTOR".
    3. Selector `#sel-modo-color-titulos` (Todos en Negro vs Usar Color de la Paleta).
    4. Creador de paleta de títulos Word ampliado a 3 selectores de color (Primario, Secundario y Acento).
    5. Checkbox `#chk-paleta-suave-tablas` y contenedor desplegable `#contenedor-paleta-cuadros-custom` con pickers para cabecera y filas alternas y persistencia en `localStorage`.
  - `static/js/app.js`:
    1. Sincronización de creador de paletas a 3 colores con serialización pipe-separated (`${c1}|${c2}|${c3}`).
    2. Lógica interactiva para `inicializarControlCuadros` (conmutación entre paleta suave y selector exclusivo de cuadros).
    3. Inclusión en el `payload` JSON enviado a `/api/transformar`.
  - `lanza_MarkFlowOffice.bat`, `start_MFO.bat`, `interfaces/mcp/server.json`, `README.md`: actualización de versión a `v1.7.0`.
  - `pruebas/test_v1_7_0.py`: nueva suite de pruebas automatizadas cubriendo todas las especificaciones de `mejoras_app_02_paleta de colores.md`.
* **Descripción Técnica de Cambios:**
  1. **Cumplimiento riguroso de `mejoras_app_02_paleta de colores.md`:** Se implementaron las directrices de diseño para los 3 motores (PDF, HTML y Word).
  2. **Garantía de calidad completa:** 138 pruebas unitarias y de integración pasando al 100% (1 skipped condicional).

### 📌 [v1.6.1] — 2026-10-25 20:25:00
* **Tipo de Incremento:** PATCH (eliminación de códigos de texto en paletas HTML y PDF e incorporación de paneles de muestras visuales / swatches reales idénticos a Word)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.6.1"`
* **Componentes Afectados:**
  - `motor/a_html.py`: limpieza de `PALETAS_TRICOLOR` eliminando códigos hexadecimales redundantes en los nombres legibles de cada paleta.
  - `motor/a_pdf.py`: limpieza de `PALETAS_EDITORIAL_PDF` eliminando emojis pesados y códigos entre paréntesis en los nombres legibles.
  - `templates/index.html`:
    1. En `#acordeon-temas-html`: sustitución del `<select>` desplegable tradicional de paletas por el panel visible `#contenedor-paleta-html` con cuadrícula de swatches reales (`#swatches-html-grid`).
    2. En `#subtab-panel-pdf`: sustitución del `<select>` desplegable tradicional por el panel visible `#contenedor-paleta-pdf` con cuadrícula de swatches reales (`#swatches-pdf-grid`).
  - `static/js/app.js`:
    1. Implementación de `renderizarSwatchesHtml` con tarjetas clicables (`.swatch-card`) mostrando los 3 puntos de color (`.swatch-dot`) de cada paleta web (primario, secundario y fondo suave) y sincronización con las paletas personalizadas guardadas por el usuario.
    2. Implementación de `renderizarSwatchesPdf` con tarjetas clicables mostrando los colores sobrios de cada paleta editorial PDF.
    3. Conexión de listeners dinámicos para actualización reactiva del estado activo (`.activa`).
  - `app/version.py`, `lanza_MarkFlowOffice.bat`, `interfaces/mcp/server.json`, `README.md`: sincronización de versión SSOT a `v1.6.1`.
  - `pruebas/test_v1_6_0.py`: verificación de presencia de `#swatches-html-grid`, `#swatches-pdf-grid` y ausencia de códigos de texto crudos en las opciones.
* **Descripción Técnica de Cambios:**
  1. **Homogeneización visual absoluta:** Al igual que en Word, ahora tanto los Temas HTML como el PDF Editorial cuentan con paneles visuales visibles directamente en la interfaz con muestras reales de colores (swatches) y nombres limpios y profesionales sin códigos hexadecimales feos entre paréntesis.
  2. **Compatibilidad total y sincronización:** Los selectores subyacentes se mantienen sincronizados de forma transparente para los endpoints de conversión.
  3. **Suite de pruebas verde:** 130 pruebas pasadas, 1 skip y 0 fallos.

---

### 📌 [v1.6.0] — 2026-10-25 20:00:00
* **Tipo de Incremento:** MINOR (incorporación de mejoras en pestaña Conversión Completa según `docs/mejoras/mejoras_app_01.md`: catálogo completo de temas HTML/Word, centrado y adaptabilidad dinámica de ancho en tablas Word, resolución robusta de imágenes en DOCX y Base64 en HTML/PDF, y selector visual de paletas con swatches y creador de paletas personalizadas)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.6.0"`
* **Componentes Afectados:**
  - `motor/a_docx.py`:
    1. `_adaptar_ancho`: cálculo de ancho natural adaptativo según densidad de caracteres y márgenes; si `ancho_natural < util_dxa`, se asigna un ancho proporcional centrado sin estirar rígidamente al 100% de la página; aplicación explícita de `tabla.alignment = WD_TABLE_ALIGNMENT.CENTER`, `<w:jc w:val="center"/>`, `tabla.autofit = False`, preservando `cantSplit` y `tblHeader`.
    2. `_obtener_color_titulos`: nuevo intérprete de colores para títulos de Word con catálogo de paletas (`negro`, `azul`, `corporate-blue`, `emerald-tech`, `slate-modern`, `burgundy-classic`) y soporte universal de códigos hexadecimales arbitrarios (`#RRGGBB` o `RRGGBB`) aplicados a los estilos Heading 1..6 y TOC.
    3. `resolver_imagenes_en_markdown_docx`: resolución de rutas locales relativas en enlaces Markdown `![alt](ruta)` y etiquetas `<img src="ruta">` a rutas absolutas normalizadas antes de invocar a Pandoc.
  - `motor/a_html.py`:
    1. Funciones `convertir_imagen_a_base64` e `incrustar_imagenes_base64_en_markdown` para convertir imágenes locales relativas a Data URIs Base64 (`data:image/{ext};base64,...`), garantizando entregables HTML 100% autónomos y portables sin dependencias de carpetas externas.
    2. Catálogo de nombres descriptivos para `Tema1` a `Tema6`.
  - `motor/a_pdf.py`:
    1. Incrustación automática de imágenes a Data URI Base64 en el HTML intermedio con MathML antes de llamar a Chromium Headless, eliminando imágenes rotas o vacías en entregables PDF.
  - `templates/index.html`:
    1. Selector de Tema HTML (`#sel-tema-html`) enriquecido con todas las opciones `Tema1` a `Tema6` y sus etiquetas editoriales correspondientes.
    2. Homologación de opciones en el selector de paletas tri-color web (`#sel-paleta-tricolor`).
    3. Sección `#contenedor-color-titulos` actualizada con el grid de muestras visuales de color (`#swatches-titulos-grid`) y el panel desplegable del creador de paletas personalizadas (`#creador-paleta-card`).
  - `static/css/app.css`:
    1. Tokens y estilos visuales glassmorphism para `.contenedor-color-titulos-completo`, chips `.swatch-card` con puntos de color `.swatch-dot`, estados activos `.activa`, botón de eliminación `.swatch-btn-del`, y controles del creador de paleta (`.color-picker-input`, `.hex-text-input`).
  - `static/js/app.js`:
    1. Poblado dinámico con nombres amigables para `Tema1` a `Tema6` en `sel-tema-html`.
    2. Gestor visual de swatches de títulos (`renderizarSwatchesTitulos`) con paletas base y soporte de almacenamiento persistente en `localStorage` (`markflow_paletas_personalizadas`).
    3. Creador de paletas personalizadas (`inicializarCreadorPaleta`) con sincronización bidireccional de pickers de color primario/secundario e inputs hexadecimales.
  - `app/version.py`, `lanza_MarkFlowOffice.bat`, `interfaces/mcp/server.json`, `README.md`: actualización coordinada a `v1.6.0`.
  - `pruebas/test_v1_6_0.py`: nueva suite de 9 pruebas unitarias cubriendo temas HTML/Word, ancho adaptativo de tablas, resolución de imágenes y componentes UI.
* **Descripción Técnica de Cambios:**
  1. **Disponibilidad Total de Temas en la Interfaz Clásica:** Se incorporaron todos los temas HTML (`Tema1`..`Tema6`) y se mantuvieron los temas Word nativos (`tema1`..`tema3`) y personalizado, integrando nombres editoriales claros.
  2. **Tablas Centradas y Ancho Adaptativo en Word:** Se resolvió el problema del estiramiento rígido al 100% en tablas con poco contenido; ahora se adaptan a su ancho natural equilibrado y se centran en la página A4.
  3. **Visualización Impecable de Imágenes en DOCX y PDF:** Se blindó el preprocesamiento de imágenes locales relativas en Markdown convirtiéndolas a rutas absolutas para Pandoc (DOCX) y a Data URIs Base64 para HTML y PDF (Chromium).
  4. **Selector Visual con Swatches y Creador de Paletas:** La interfaz cuenta ahora con tarjetas interactivas con bolitas de color representativas y un creador con inputs de color nativos que guarda paletas personalizadas en `localStorage`.
  5. **Suite de Pruebas 100% Verde:** 130 pruebas pasadas, 1 skip y 0 fallos en pytest.

---
* **Tipo de Incremento:** PATCH (corrección crítica: desacoplamiento y blindaje de Split-View, conversor de tablas HTML a Markdown GFM y erradicación de prefijos parásitos [!NOTE])
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.5.1"`
* **Componentes Afectados:**
  - `motor/sanear.py`: inclusión de `convertir_tablas_html_a_markdown(texto)` (conversión de tablas `<table>` a tablas Markdown GFM con divisorias `:---`, saneamiento de celdas, escape de pipes) y `limpiar_etiquetas_nota_parasitas(texto)` (erradicación de `[!NOTE]`, `[!NOTA]`, `[!TIP]`, `[!WARNING]`, etc. tras `>`); integración como Paso 0 en el pipeline canónico `saneanar()` y en `eliminar_todas_las_notas()`.
  - `motor/a_docx.py`: en `_barnizar_nota()`, limpieza de etiquetas parásitas residuales `[!NOTE]` / `[!NOTA]` en los runs del párrafo de nota antes del barnizado en Word.
  - `motor/reverse_converter.py`: generación de citas limpias `> {texto}` sin inyección parásita de `[!NOTE]`.
  - `app/principal.py`: montaje de `/assets` (`StaticFiles` hacia `motor/assets/`) para servir KaTeX y Mermaid de forma 100% offline y local.
  - `templates/index.html`: `contenteditable="false"` en `#splitview-editor-visual` (solo previsualización); título actualizado a "VISTA PREVIA / RENDER EN VIVO"; tooltip de nota limpio `(>)`; inclusión en el head de los scripts y estilos locales de KaTeX y Mermaid.
  - `static/js/app.js`: eliminación total de la función destructiva `sincronizarVisualACodigo()` y su event listener; `splitviewTextarea` establecido como única fuente de la verdad (SSOT inmutable); barra de herramientas desacoplada del DOM visual operando exclusivamente sobre el textarea; botón de notas sin `[!NOTE]`; renderizado dinámico de KaTeX (`renderMathInElement`) y Mermaid (`mermaid.run`) en vivo.
  - `lanza_MarkFlowOffice.bat`, `interfaces/mcp/server.json`, `README.md`: actualización de versión a `v1.5.1`.
  - `pruebas/test_v1_5_1.py`: suite de 8 pruebas unitarias de regresión cubriendo conversión de tablas, limpieza de notas, pipeline `saneanar`, `contenteditable="false"`, ausencia de `sincronizarVisualACodigo` y versión SSOT.
* **Descripción Técnica de Cambios:**
  1. **Solución a la corrupción destructiva de Split-View:** Se eliminó la serialización inversa del DOM compilado hacia Markdown, protegiendo al 100% las tablas GFM, fórmulas matemáticas y diagramas Mermaid editados en la pestaña clásica de conversión completa (`/clasico`).
  2. **Conversor universal de tablas HTML:** Toda tabla que ingrese como `<table>` (pegada de navegadores, Word o exportaciones previas degradadas) es convertida a tabla Markdown GFM pura antes de continuar por el pipeline de saneamiento.
  3. **Erradicación de la palabra parásita `[!NOTE]`:** Se removió la inyección de la cadena textual `[!NOTE]` en la UI (`tbBtnNota`), en el conversor inverso de DOCX y en el saneador, logrando que los entregables Word, HTML y PDF luzcan bloques de nota limpios y profesionales.
  4. **Suite de pruebas verde al 100%:** 121 pruebas pasadas, 1 skip y 0 fallos en pytest.

---

### 📌 [v1.4.0] — 2026-10-25 17:34:15
* **Tipo de Incremento:** MINOR (nueva funcionalidad: round-trip .docx real — extracción a Markdown y reguardado byte-preserving — sin romper compatibilidad)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.4.0"`
* **Componentes Afectados:**
  - `app/servicios/roundtrip_docx.py` (nuevo): módulo central del round-trip con dos mitades — `extraer_md(ruta)` (python-docx 1.2.0: títulos por `style_id`/nombre con `_PATRON_HEADING` invariante de idioma, runs **negrita**/*cursiva* vía `iter_inner_content`, enlaces `[texto](destino)` vía `hyperlinks`, listas por `w:numPr` consultado primero en el párrafo y luego en el estilo (`List Bullet`/`List Number` lo definen en styles.xml) con lookup de `numFmt` en `numbering.xml` y contadores `(numId, ilvl)`, tablas GFM con alineación por `w:jc` y escape de `|`, bloques separados por línea en blanco con listas compactas, contadores imágenes/fórmulas `m:oMath`/revisiones `w:ins|w:del`/enlaces → avisos) y `reguardar(texto_md, ruta_original)` (empalme de cuerpo: markdown-it-py commonmark+table+strikethrough → lxml genera `w:p`/`w:tbl`/`w:tblGrid` nuevos y reemplaza los hijos de `w:body` salvo el `w:sectPr` final; el resto del zip —styles, headers/footers, numbering, media, rels— se copia byte a byte). Builder OOXML propio (`_nodo`, `_run`, `_runs_de_inline`, `_parrafo`, `_parrafo_mono`, `_separador` con `pBdr`, `_tabla` con bordes/tblGrid/tblHeader/jc, `_lista` con marcador literal y sangría de 360 twips/nivel) porque `parse_markdown` del núcleo no soporta listas ni runs.
  - `app/rutas/office.py`: 2 endpoints nuevos — `POST /api/office/docx-importar` (UploadFile multipart; valida extensión `.docx` + firma `PK\x03\x04`; devuelve `nombre_sugerido` saneado, texto, stats y avisos; 422 si python-docx no puede leer) y `POST /api/office/docx-reguardar` (UploadFile + Form `markdown`; respuesta binaria `application/vnd…document` con `Content-Disposition: attachment` `{stem}-editado.docx` y copia trazable en `storage/salidas/`). Imports `File`, `Form`, `UploadFile` añadidos.
  - `templates/office.html`: botón `⬆ .docx` + input de archivo oculto en el panel Documentos; tarjeta "♻ Round-trip .docx real" en la app Word (input oculto, textarea `#rt-texto` editable, botones `#btn-rt-extraer`/`#btn-rt-reguardar` — este último deshabilitado hasta extraer — y estado `#rt-estado`).
  - `static/js/office.js`: handler de importación (FormData → `docx-importar` → confirmación con stats/avisos → `POST /api/documentos` con nombre y contenido → `abrirDocumento(nombre + ".md")` + refresco de la lista) y handlers del round-trip en Word (extraer llena el textarea y muestra resumen + avisos; reguardar envía FormData con blob+markdown y descarga `{original}-editado.docx` vía blob URL).
  - `pruebas/test_oficina.py`: SSOT v1.4.0 (renombrado) + 4 pruebas nuevas con fixture `.docx` generado por python-docx (Title/Heading1, run bold + italic, `List Bullet` ×2, tabla 2×3 con cabecera centrada): extracción (texto con `# `, `**…**`, `- `, `| … |`), reguardado round-trip real reabierto con python-docx (estilo `Heading1`, tabla 2×3 con `tblGrid`, run bold, `sectPr`/ancho de página sobreviven, párrafo editado presente), endpoints multipart con defensas 400 (extensión no-.docx y binario sin firma ZIP) y chequeos estáticos de la UI.
  - `interfaces/mcp/server.json` (1.4.0, escrito con Python sin BOM), `lanza_MarkFlowOffice.bat` (v1.4.0), `README.md` (badge 1.4.0 + línea Word con round-trip real).
* **Descripción Técnica de Cambios:**
  1. **Se cierra la pieza mayor de la Fase 2:** abrir un `.docx` existente → Markdown → editar en Docs → reguardar byte-preserving. La extracción usa python-docx 1.2.0 (pandoc NO está disponible en el entorno) y el reguardado NO usa `apply_ast_to_template` del núcleo (ingenuo: no limpia el cuerpo) sino empalme de cuerpo OOXML propio.
  2. **Hallazgo empírico clave:** la numeración de listas puede vivir en el **estilo** de párrafo (`List Bullet` de la plantilla de python-docx define `numPr` en styles.xml) y no en el párrafo — `lista_de()` consulta primero el `pPr` directo y luego el del estilo; el docx real además destapó un error de paréntesis en `ilvl_n.get(_QN("val", "0"))` (el default iba al lambda y no a `.get`) corregido a `_QN("val")` + default.
  3. **Fidelidad OOXML:** `w:tblGrid` es hijo obligatorio de `w:tbl` — sin él python-docx lanza `InvalidXmlError` al reabrir; el builder lo emite (una `w:gridCol` por columna). El `w:sectPr` final (márgenes/orientación/referencias de cabecera) se conserva del original.
  4. **Limitaciones documentadas en el docstring:** listas reguardadas con marcador literal + sangría (sin numeración OOXML real), enlaces reguardados como texto (requeriría rels propios), OMML y revisiones no reconstruidos (marcados + avisos al usuario).
  5. **Verificación end-to-end con documento real:** `MEMORIA_TECNICA_HIDROSANITARIA_AF_LEMA_V2.docx` (37 KB) → extracción con **48 títulos, 63 párrafos, 129 ítems, 25 tablas** + avisos (91 fórmulas OMML, 15 enlaces); reguardado 26.8 KB reabierto con **241 párrafos y las 25 tablas intactas** y la edición presente; captura headless del panel Word con la tarjeta round-trip y **v1.4.0** en badge/pie/favicon (`?v=1.4.0`).
  6. **Resultado de la suite:** 110 pasadas · 1 skip · 0 fallos (106 heredadas + 4 nuevas); `node --check` en `office.js` sin errores; servidor detenido y artefactos de verificación (`verif_v140.py`, temporales) eliminados tras la prueba.
* **Correcciones durante la iteración:** import faltante de `Form` en `office.py` ( NameError en colección de tests), palabra clave `cols` en `add_table` del test, separación por bloques en la extracción (CommonMark exige línea en blanco entre párrafos/listas/tablas — sin ella el reguardado colapsaba bloques contiguos en un solo párrafo).

---

### 📌 [v1.3.0] — 2026-10-25 17:15:30
* **Tipo de Incremento:** MINOR (nueva funcionalidad: visor PDF local con pdf.js vendorizado + biblioteca de entregables, sin romper compatibilidad)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.3.0"`
* **Componentes Afectados:**
  - `static/vendor/pdfjs/` (nuevo): Mozilla pdf.js **3.11.174 legacy dist** (build UMD con `window.pdfjsLib`, 695 KB) + `pdf.worker.js` (2 MB) + `LICENSE` (Apache-2.0) + `VENDOR.md` (origen, versión, motivo del vendor, decisión de excluir `cmaps/`/`standard_fonts/` y la UI propia `web/viewer.*`).
  - `app/rutas/office.py`: 2 endpoints nuevos — `GET /api/office/pdfs` (inventario de `salidas/` recursivo, más recientes primero, con archivo/ruta/sesión/tamaño/modificado) y `GET /api/office/pdfs/archivo/{ruta:path}` (FileResponse inline `application/pdf` con defensa anti-traversal por `resolve()` + `relative_to()`, rechaza extensión no-PDF con 400, inexistente con 404).
  - `static/js/visor_pdf.js` (nuevo): módulo del visor — carga perezosa del vendor (patrón `window.PM`: script clásico local + `GlobalWorkerOptions.workerSrc`), biblioteca de tarjetas (nombre/tamaño/fecha, auto-apertura del más reciente), render canvas con `devicePixelRatio` (nítido en HiDPI), navegación ←/→, zoom 50–300 % (pasos 0,25), cancelación del `RenderTask` previo, re-render con debounce en `resize`, apertura en pestaña con `↗`, API pública `window.MFOPDF.abrir()`.
  - `templates/office.html`: el placeholder "Llega en la Fase 2" se sustituye por el panel real (biblioteca `#lista-pdfs` + barra del visor `#pdf-pag`/`#pdf-zoom`/`↗ Abrir` + lienzo `#canvas-pdf` + estado `#pdf-estado`); `visor_pdf.js` en el head con `defer` antes de `office.js`; tooltip del riel "PDF · Fase 2" → "PDF · visor local".
  - `static/js/office.js`: hook en `abrirApp("pdf")` → `window.MFOPDF.abrir()`.
  - `static/css/office.css`: estilos del panel (grid 300px+1fr con colapso a 1 columna en <1080px, tarjetas de la biblioteca con estado activo, barra del visor, lienzo con sombra de página sobre `--bg-canvas`).
  - `pruebas/test_oficina.py`: SSOT v1.3.0 + 3 pruebas nuevas (vendor local con `pdfjsLib`/`GlobalWorkerOptions` y carga perezosa sin CDN, panel real en la shell sin placeholder, endpoints de biblioteca/servicio con PDF de prueba en raíz y en sesión + defensas anti-traversal/404/400).
  - `interfaces/mcp/server.json`, `lanza_MarkFlowOffice.bat`, `README.md`: versión 1.3.0; el README describe el visor PDF local (biblioteca + navegación + zoom, 100 % offline).
* **Descripción Técnica de Cambios:**
  1. **App PDF activa (cierra el 3er punto de la Fase 2):** el riel ya no muestra un placeholder — la app PDF lista los entregables del motor en `salidas/` y los renderiza en canvas con pdf.js, 100 % local (sin CDN; el entorno corporativo bloquea paquetes con `@` y CDN, mitigado con vendor UMD + carga perezosa idéntica al patrón de ProseMirror).
  2. **Selección de versión pdf.js:** la v4.x es ESM puro (`.mjs`); se adoptó la **v3.11.174**, última con build UMD clásico, para mantener el patrón de script clásico global (`window.pdfjsLib`) consistente con `window.PM` y evitar riesgos de MIME/ESM.
  3. **Endpoint de servicio seguro:** reutiliza el patrón de sesiones pero acepta rutas relativas (raíz + sesiones) con verificación `resolve()`/`relative_to()` — el intento `../version.py` se rechaza; solo `.pdf` se sirve.
  4. **Render de calidad:** canvas a `viewport.width × devicePixelRatio` con tamaño CSS ajustado (nítido en pantallas HiDPI), cancelación del render anterior al cambiar de página/zoom y re-render con debounce al redimensionar.
  5. **Diagnóstico headless:** el mecanismo `--screenshot` de Edge congela los Web Workers (la captura queda en "Cargando PDF…" aunque el worker parseó — verificado con el warning de fuentes TT en la consola); la verificación definitiva se hizo con **Chrome DevTools Protocol** (WebSocket nativo de Node 24: navigate → 13 s reales → `Runtime.evaluate` → `captureScreenshot`), confirmando `1 / 21` páginas, canvas 594×841, placeholder oculto y estado "rendered con pdf.js local".
  6. **Resultado de la suite:** 106 pasadas · 1 skip · 0 fallos (103 heredadas + 3 nuevas); `node --check` en los 3 JS sin errores; captura CDP de `/?app=pdf` con la página 1 de la memoria técnica renderizada (índice con enlaces, tipografía correcta), badge y pie con **v1.3.0**; servidor y archivos de diagnóstico eliminados tras la verificación.

---

### 📌 [v1.2.0] — 2026-10-25 16:17:07
* **Tipo de Incremento:** MINOR (nueva funcionalidad: tablas GFM nativas en el editor visual Docs, sin romper compatibilidad)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.2.0"`
* **Componentes Afectados:**
  - `app/servicios/editor_markdown.py`: la degradación `_tabla_a_texto` (v1.1.0: `code_block params="tabla"`) se sustituye por nodos reales `table/table_row/table_header/table_cell` — `_tabla()` construye filas/celdas con `_alineacion_de_style()` (regex `text-align:(center|right|left)` sobre `attrs.style` de `th_open/td_open`); la primera fila siempre es `table_header` (GFM no representa tablas sin cabecera); el serializador añade la rama `table` en `_bloque_a_md` con `_tabla_a_md()` (cabecera + separador `_SEPARADOR_ALINEACION` `{""→---, left→:---, center→:---:, right→---:}` + padding de celdas faltantes) y `_celda_a_texto()` (aplana párrafos con espacios, hardbreaks/saltos → espacio, escapa `|`→`\|`).
  - `static/js/editor_docs.js`: esquema PM con los 4 nodos de tabla (`tableRole` table/row/cell/header_cell, `isolating`, attrs de celda `colspan/rowspan/colwidth/alignment` con `data-align` en DOM); comandos propios sin `@prosemirror-tables` — `tablaDe()` (contexto por `$from.before/index`), `insertarTabla()` (prompt "3x3", límites 12×8, cursor en primera celda), `insertarFila()`, `eliminarFila()` (+ `convertirPrimeraFilaACabecera()` tras borrar cabecera), `insertarColumna()` (inserción en reverso: las posiciones previas no se alteran), `eliminarColumna()` (borra la tabla si queda ≤1 columna), `eliminarTabla()` y `celdaSiguiente()` (Tab/Shift-Tab navegan celdas; Tab en la última celda crea fila nueva al final); espejo JS del serializador (`tablaAMd`/`celdaATexto`/`SEPARADOR_ALINEACION`) con paridad exacta con Python; 6 casos nuevos en `comando()`.
  - `templates/office.html`: grupo de tablas en `#barra-docs` — 6 botones `data-bd="tabla" | fila+ | fila- | col+ | col- | tabla-del`.
  - `static/css/office.css`: estilos de tabla GFM con tokens SSOT — `border-collapse`, bordes th/td `--border-default`, cabecera con `--accent-indigo` al 12 %, zebra con `--bg-subtle`, alineación `td/th[data-align="center"|"right"]`, `table p { margin: 0 }`.
  - `pruebas/test_oficina.py`: SSOT v1.2.0 + 4 pruebas nuevas (estructura/alineación de la tabla, round-trip por endpoints con pipe escapado y separador `|:---:|---:|---|`, doc completo con tabla + otros bloques, toolbar/esquema JS/CSS estáticos).
  - `interfaces/mcp/server.json`, `lanza_MarkFlowOffice.bat`, `README.md`: versión 1.2.0; el README elimina la "Limitación v1" (tablas degradadas) y describe el editor con tablas GFM nativas + exportación a Word.
* **Descripción Técnica de Cambios:**
  1. **Tablas editables como nodos nativos (cierra la limitación de v1.1.0):** una tabla Markdown ya no llega como bloque de código con pipes; se parsea a nodos `table/table_row/table_header/table_cell` (Python y JS en paridad) y se renderiza como `<table>` real con cabecera destacada, zebra y alineación por columna.
  2. **Primera fila siempre cabecera (decisión de diseño GFM):** el formato no representa tablas sin cabecera; al eliminar la primera fila, `convertirPrimeraFilaACabecera()` promueve la siguiente a `table_header` para garantizar el round-trip.
  3. **Alineación GFM conservada en attrs:** `:---:`/`---:` del separador se leen de `attrs.style` (`text-align:center/right`) y se guardan en `attrs.alignment` de la celda; el serializador regenera el separador desde esos attrs (idempotente).
  4. **Idempotencia estructural con tablas verificada:** `md → doc → md → doc` idéntico incluyendo marcas en celdas (**negrita**/`código`/*cursiva*), pipes escapados (`a\|b`), celdas vacías, filas desiguales (padding) y hardbreaks aplanados a espacios.
  5. **Cadena de exportación intacta:** el núcleo GenOffice ya exporta tablas Markdown→Word (`converter.py` + `byte_preserver.py`), por lo que una tabla editada en Docs sale formateada al .docx sin tocar nada del núcleo.
  6. **Limitaciones documentadas (v1.2.0):** sin redimensionado de columnas ni colspan/rowspan en la UI (los attrs existen y sobreviven al round-trip); sin UI de alineación; pipes dentro de `code` en celdas no idempotentes; contenido multilínea de celda se aplana a espacios.
  7. **Resultado de la suite:** 103 pasadas · 1 skip · 0 fallos (99 heredadas + 4 nuevas); `node --check` en `editor_docs.js` y `office.js` sin errores; verificación visual end-to-end con documento de prueba ("Verificacion Tablas v120", 4×4 con alineaciones, marcas, pipe escapado y código en celda): tabla renderizada con cabecera y zebra, grupo de 6 botones de tabla en la toolbar, badge y pie con **v1.2.0** (favicon servido con `?v=1.2.0` desde el SSOT); servidor detenido tras la verificación.

---

### 📌 [v1.1.0] — 2026-10-25 16:07:37
* **Tipo de Incremento:** MINOR (nueva funcionalidad: editor visual en Docs + endpoints md↔doc + deep-links, sin romper compatibilidad)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.1.0"`
* **Componentes Afectados:**
  - `static/vendor/prosemirror/pm_bundle.js` (nuevo, 254 KB) + `pm_editor.css` (nuevo, 7 KB) + `VENDOR.md` (nuevo): ProseMirror oficial vendorizado 100 % local (MIT, atribución); sin CDN.
  - `app/servicios/editor_markdown.py` (nuevo): conversor canónico Markdown ↔ JSON ProseMirror con `markdown-it-py` (CommonMark + tablas + strikethrough); reglas softbreak→espacio, hardbreak→`\`+`\n`, tablas degradadas a `code_block` con `params="tabla"`, listas sangría 2 espacios/nivel, `ordered` con `start`, marcas strong/em/s/code/link; doc vacío → párrafo vacío (contenido válido para el esquema).
  - `app/rutas/office.py`: 3 endpoints nuevos — `POST /api/office/md-a-json`, `POST /api/office/json-a-md` y `POST /api/office/sanear` (pipeline `motor.sanear.saneanar` con fórmulas y avisos).
  - `templates/office.html`: CSS del vendor en el head; panel Docs reconstruido con `#barra-docs` (marcas, bloques, listas, enlaces/imagen/hr, deshacer/rehacer, `#docs-stats`, 🧹 Sanear, `</>` Fuente), contenedor `#editor-docs` y textarea SSOT oculto; scripts `editor_docs.js` + `office.js` con `defer`.
  - `static/css/office.css`: estilos de la barra, tipografía del documento con tokens SSOT, placeholder `.pm-placeholder`, resaltado de botones activos y modo fuente (`.split-docs.modo-fuente`).
  - `static/js/editor_docs.js` (nuevo): esquema PM Docs (doc/paragraph/heading/blockquote/bullet_list/ordered_list/list_item/code_block{params}/hard_break/horizontal_rule/image + marcas strong/em/s/code/link), espejo JS del serializador Python, plugins input-rules (``` ``` / `#` / `>` / viñetas / numerada), keymap (Mod-b/i/`, Mod-k, Shift-Ctrl-0..3/8/9/\\, Ctrl->, Mod-[/], Enter splitListItem, Shift-Enter hardbreak), history/dropcursor/gapcursor, plugin placeholder, toolbar con estados activos y estadísticas en vivo.
  - `static/js/office.js`: carga perezosa del bundle (`cargarPM`), `asegurarEditor` con fallback a modo fuente, hook en `abrirApp("docs")`, sincronización `abrirDocumento` → `setTexto`, toggle `#btn-modo-fuente`, handler `#btn-sanear-pegado` (badge con avisos) y nuevo `arranque()` con deep-links `/?app=` y `/?app=docs&doc=`.
  - `pruebas/test_oficina.py`: SSOT v1.1.0 + 5 pruebas nuevas (editor en shell, vendor local con `window.PM=`, estructura `md-a-json`, round-trip estructural `json-a-md` idempotente, endpoint `sanear`).
  - `interfaces/mcp/server.json`, `lanza_MarkFlowOffice.bat`, `README.md`: versión 1.1.0, banner con editor visual, estructura con `static/vendor/prosemirror/` y atribución ProseMirror MIT.
* **Descripción Técnica de Cambios:**
  1. **Editor visual ProseMirror en Docs (Fase 1 del plan):** el panel Docs pasa de un textarea simple a un editor WYSIWYG completo (negrita/cursiva/tachado/código, títulos H1-H3, listas con sangría/desangrar, citas, bloques de código con lenguaje, enlaces Ctrl+K, imágenes, separadores, deshacer/rehacer) con barra de herramientas con estados activos, placeholder, estadísticas de palabras/caracteres y previsualización en vivo intacta (KaTeX + Mermaid).
  2. **Offline-first real:** el entorno corporativo bloquea toda URL con `@` (paquetes scoped npm, jsDelivr/unpkg/esm.sh y el CLI de npm); solución = bundle IIFE oficial de `prosemirror.net` que expone `window.PM`, vendorizado y servido localmente con carga perezosa (solo al abrir Docs) y fallback automático al modo fuente.
  3. **SSOT del texto inalterado:** `#editor-markdown` sigue siendo la fuente de verdad; guardar (Ctrl+S), exportar Word, IA y preview leen de él. El editor visual lo sincroniza en cada transacción mediante el espejo JS del serializador (paridad estricta con `doc_a_md` de Python); el botón `</>` Fuente permite editar el Markdown crudo y re-parsea al volver.
  4. **Idempotencia estructural verificada:** `md → doc → md → doc` produce documentos JSON idénticos (prueba HTTP extremo a extremo), incluyendo citas multipárrafo (línea `>` en blanco entre párrafos), listas con `start`, fences con lenguaje, hardbreaks, enlaces/imágenes con título y tablas degradadas a `code_block params="tabla"`.
  5. **Limitaciones documentadas (v1.1.0):** las tablas no se editan en el visual (llegan como bloque de código con pipes); la marca `code` es exclusiva (ignora otras marcas del run); dos listas del mismo tipo adyacentes se representan como una sola en Markdown; texto sin escapado (misma regla en JS y Python).
  6. **Correcciones durante la integración:** `md_a_doc("")` ahora devuelve doc con párrafo vacío (contenido válido para el esquema `block+` de PM — sin él, `Node.fromJSON` dejaba un doc ilegal sin placeholder); `init()` limpia el contenedor (el `EditorView` se añade y no reemplaza hijos, dejaba el texto "Cargando editor visual…" residual).
  7. **Resultado de la suite:** 99 pasadas · 1 skip · 0 fallos (94 heredadas + 5 nuevas); verificación end-to-end con `--dump-dom` y capturas headless en `/?app=docs` (placeholder visible, ¶ activo) y `/?app=docs&doc=Bienvenida` (documento renderizado, H1 activo, stats "109 palabras · 672 caracteres", badge "cargado", preview con KaTeX/Mermaid, v1.1.0 en UI y pie).

---

### 📌 [v1.0.0] — 2026-10-25 (nacimiento del producto)
* **Tipo de Incremento:** MAJOR (primera versión de MarkFlow Office como producto independiente)
* **Archivo SSOT:** `app/version.py` → `APP_VERSION = "1.0.0"`, `APP_NOMBRE = "MarkFlow Office"`
* **Componentes Afectados:**
  - `app/principal.py`: ensambla FastAPI con 3 routers (api MarkFlow + documentos + office); rutas `/` (shell Office) y `/clasico` (motor clásico embebido); puerto 8320.
  - `app/rutas/documentos.py` (nuevo): CRUD de documentos Markdown en `storage/documentos/` con validación anti-path-traversal e indexación FTS5.
  - `app/rutas/office.py` (nuevo): `/api/office/salud`, config IA (claves enmascaradas en GET), `/api/office/ia/pregunta` (Ollama local primero) y `/api/office/exportar-docx` (núcleo GenOffice, directo o byte-preserving).
  - `nucleo/docx_avanzado/` (clonado del port GenOffice): `byte_preserver.py`, `converter.py`, `omml_math.py`, `tracked_changes.py` (Apache-2.0, atribución en NOTICE del README).
  - `nucleo/ia/ai_gateway.py` (adaptado): Ollama con URL nativa corregida (`/api/generate`), proveedores externos reales (OpenAI/Anthropic/Gemini vía `requests`), `check_availability` intacto.
  - `nucleo/busqueda/database_fts.py` (clonado): índice SQLite FTS5 para búsqueda local.
  - `templates/office.html` + `static/css/office.css` + `static/js/office.js` (nuevos): shell estilo GenOffice — riel lateral de apps con tooltips, barra superior con título de documento y toggles (IA/tema), lienzo por apps (Documentos, Docs con split editor + vista en vivo, MarkFlow clásico en iframe, Word con export byte-preserving, PDF placeholder Fase 2, Configuración) y panel de IA colapsable a la derecha; tema oscuro/claro persistente.
  - `static/css/tokens.css`, `base.css`, `components.css` (heredados de MarkFlow AI v1.13.0): identidad visual SSOT — Plus Jakarta Sans local, degradados de auroras, componentes vidrio/tarjeta/btn/chip.
  - `interfaces/cli/markflow_cli.py` (nuevo): CLI argparse cero-dependencias — `version`, `salud`, `sanear`, `convertir` (--plantilla), `documentos`, `buscar`, `servir`.
  - `interfaces/mcp/servidor_mcp.py` + `server.json` (nuevos): servidor MCP stdio JSON-RPC mínimo (6 herramientas) con registro para harnesses de agentes.
  - `interfaces/skill/SKILL.md` (nuevo): skill del agente con reglas operativas.
  - `pruebas/`: 5 suites del motor heredadas (api/ingesta/mermaid/motores/sanear, adaptadas a la nueva marca) + `test_oficina.py` (13 pruebas de shell/CRUD/FTS/DOCX/IA) + `test_nucleo.py` (9 pruebas de núcleo GenOffice/MCP/CLI).
  - `plantillas/plantilla_base.docx`, `docs/PLAN_Suite_Documentos_IA.md`, `docs/metodologia_agentes/` (6 agentes + adversarial critic del clon GenOffice).
  - `lanza_MarkFlowOffice.bat`: lanzador con liberación de puerto 8320 y apertura de navegador.
* **Descripción Técnica de Cambios:**
  1. **Producto nuevo:** MarkFlow Office nace de la fusión del motor MarkFlow AI v1.13.0 (clonado íntegro en `motor/`, `app/rutas/api.py`, UI clásica) con el núcleo DOCX del port GenOffice local, bajo la arquitectura de 4 capas del plan (`docs/PLAN_Suite_Documentos_IA.md`).
  2. **UI estilo GenOffice con mejoras MarkFlow:** riel de apps + panel IA (layout GenOffice) construidos sobre los tokens de MarkFlow (Plus Jakarta Sans, degradados de auroras, vidrio, tema claro/oscuro persistente) — 100 % offline, sin CDNs.
  3. **Todo funcional desde v1.0.0:** Documentos (CRUD + FTS5), Docs (editor + KaTeX/Mermaid en vivo), Word (export directo y byte-preserving con plantilla), MarkFlow clásico completo, panel IA (Ollama local; externos BYO-key), CLI, MCP y Skill.
  4. **PDF queda honestamente en Fase 2** con placeholder en la UI y puente al PDF Editorial del motor clásico.
  5. **Correcciones sobre el clon GenOffice (port local)** — defectos heredados detectados y reparados en esta versión:
     1. `nucleo/docx_avanzado/byte_preserver.py` · `BytePreserver.load_template`: el clon extraía el ZIP de la plantilla a un `io.BytesIO` (no soportado por `zipfile.extractall`) → ahora extrae a un directorio temporal real (`tempfile.mkdtemp`).
     2. `nucleo/docx_avanzado/converter.py` · `apply_ast_to_template`: desempaquetado ZIP incorrecto — `{name: data for name, data in zin.namelist()}` (iteraba nombres como pares) → corregido a `{name: zin.read(name)}`.
     3. `byte_preserver.py` · `_apply_ast_to_xml_node`: confusión de variable — usaba `child.get(...)` donde corresponde `ast.get(...)` en `heading`, `paragraph`, `table`, `math` y `code_block` (UnboundLocalError) → normalizado a `ast`.
     4. `byte_preserver.py`: faltaba `from lxml import etree` a nivel de módulo (NameError en la rama de headings) → añadido.
     5. `nucleo/busqueda/database_fts.py` · `FTS5Index.search`: SQL FTS5 inválido (`snippet(d.content, 5, …)` sobre columna inexistente, parámetros duplicados en el bind) → `snippet(documents, 1, '<mark>', '</mark>', '…', 24)` con `MATCH` sobre la tabla.
     6. `database_fts.py` · `remove_document` (nuevo): el DELETE de `/api/documentos/{nombre}` desindexa el documento — el índice FTS queda sin entradas obsoletas (reproduce el bug «resultados fantasma» del clon).
     7. `nucleo/ia/ai_gateway.py`: ruta de Ollama corregida (nativa `/api/generate`, base sin `/v1`) y proveedores externos implementados de verdad (OpenAI/Anthropic/Gemini vía `requests`); claves nunca se devuelven completas por la API (enmascarado `••••xxxx`).
     8. `interfaces/cli/markflow_cli.py`: `sys.stdout/stderr.reconfigure(utf-8)` — sin `UnicodeEncodeError` en consolas Windows cp1252 al imprimir ✔/→/acentos.
     9. CLI y MCP: el `snippet` de búsqueda se entrega sin etiquetas `<mark>` (texto limpio para el agente); `interfaces/mcp/servidor_mcp.py` reconfigura stdio a UTF-8 (canal JSON-RPC íntegro).
     10. Shell: fix CSS `.resultados-busqueda[hidden]{display:none}` (el recuadro vacío no se mostraba oculto) y arranque de `office.js` que respeta el panel activo renderizado por el servidor (deep-links `/`→app Docs).
  6. **Resultado de la suite:** 94 pasadas · 1 skip · 0 fallos (5 suites del motor heredadas + test_oficina + test_nucleo); smoke test end-to-end del CLI (`version`, `salud`, `documentos`, `convertir --plantilla`, `buscar`) y del servidor MCP (initialize → tools/list → buscar → version) verificados sobre consola cp1252.
