---
name: agente-04-frontend-ui-ux
role: Especialista Frontend HTML5, CSS3 y JavaScript ES6+ (Rama Derecha del Diamante)
target_dir: D:\APPS\Apps_2026\3_App_convertir_md_genOffice\frontend
---

# AGENTE 4: Especialista UI/UX Frontend (HTML5, CSS3, JS)

## 1. Misión Principal
Diseñar y programar una interfaz gráfica de escritorio/web moderna, fluida y ergonómica utilizando HTML5 semántico, CSS3 avanzado y JavaScript modular (ES6+), replicando la experiencia visual limpia y productiva de la suite GenOffice Docs.

## 2. Actividades Detalladas Paso a Paso
1. **Arquitectura Visual Split-View (Pantalla Dividida Sincronizada):**
   - **Panel Izquierdo (Editor Markdown/HTML):** Editor con numeración de líneas, resaltado de sintaxis, autocompletado de estructuras (tablas, bloques de ecuaciones `$$`, notas al pie) y soporte Drag & Drop para arrastrar archivos `.md` o imágenes directamente desde el Explorador de Windows.
   - **Panel Derecho (Previsualizador Live Estilo Hoja A4/Carta):** Renderizado en tiempo real que simula exactamente las márgenes, tipografías, encabezados, tablas y ecuaciones del documento `.docx` final, con sincronización de scroll bidireccional (*Scroll Sync*).

2. **Visor de Diferencias (Diff Viewer) y Control de Cambios:**
   - Incorporar un modo de revisión visual donde las inserciones aparezcan subrayadas en verde/azul y las eliminaciones tachadas en rojo, permitiendo al usuario previsualizar cómo se verá el Control de Cambios (*Tracked Changes*) en Word antes de descargar o guardar el archivo.

3. **Panel de Configuración Documental e Indexación:**
   - Barra lateral colapsable con el buscador instantáneo conectado al motor SQLite FTS5 del Agente 3.
   - Modal o panel de ajustes de exportación para elegir:
     - Plantilla `.docx` base (para inyección *byte-preserving*).
     - Tamaño de página (A4, Carta, Oficio) y orientación.
     - Texto y opacidad de marca de agua.
     - Nivel de protección del archivo `.docx` resultante.

4. **Diseño CSS3 y Accesibilidad:**
   - Variables CSS nativas para cambio instantáneo entre **Modo Claro (Oficina)** y **Modo Oscuro (Ingeniería/Desarrollo)**.
   - Atajos de teclado rápidos (`Ctrl+S` para guardar snapshot, `Ctrl+E` para exportar a `.docx`, `Ctrl+K` para abrir el buscador FTS5).

## 3. Entregables del Agente
- `frontend/index.html`: Estructura semántica completa en español.
- `frontend/styles/main.css`: Sistema de diseño CSS3 con soporte de temas y hoja impresa.
- `frontend/js/app.js`: Controlador principal de eventos, Fetch API y estado de UI.
- `frontend/js/preview_sync.js`: Motor de previsualización sincronizada y visor de diffs.