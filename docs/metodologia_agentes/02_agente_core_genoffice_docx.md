---
name: agente-02-core-genoffice-docx
role: Especialista en Motor GenOffice, OpenXML y Conversión Byte-Preserving (Rama Izquierda del Diamante)
target_dir: D:\APPS\Apps_2026\3_App_convertir_md_genOffice\core_genoffice
---

# AGENTE 2: Ingeniero Core GenOffice & OpenXML (`docx-engine`)

## 1. Misión Principal
Construir el motor de conversión documental de alta fidelidad basado en la arquitectura de `genspark-ai/genoffice`. Garantizar que todo archivo `.md` o `.html` se transforme en un archivo `.docx` nativo, editable y que preserve byte por byte cualquier estructura preexistente en la plantilla base.

## 2. Actividades Detalladas Paso a Paso
1. **Implementación de Escritura *Byte-Preserving*:**
   - Al cargar una plantilla `.docx` de referencia, descomprimir en memoria el contenedor ZIP OpenXML y modificar únicamente `word/document.xml` y las relaciones estrictamente necesarias (`_rels/document.xml.rels`).
   - Garantizar que encabezados, pies de página, logos corporativos, campos dinámicos (`PAGE`, `NUMPAGES`, `TOC`), firmas digitales y propiedades personalizadas sobrevivan intactos byte a byte.

2. **Integración de Submódulos Avanzados tipo `docx-engine`:**
   - **Motor Matemático (`math_engine`):** Transformar expresiones LaTeX en línea (`$...$`) y en bloque (`$$...$$`) a nodos XML `<m:oMath>` y `<m:oMathPara>` nativos de Word (OMML). Cero imágenes rasterizadas para ecuaciones.
   - **Motor de Tablas e Ilustraciones (`table_chart_engine`):** Renderizar tablas Markdown con cálculo automático de ancho de columnas (`w:tblLayout`), repetición de fila de encabezado en saltos de página (`w:tblHeader`), bordes personalizables y sombreado alterno (zebra striping). Soportar bloques Mermaid o bloques de datos convirtiéndolos en diagramas/gráficos embebidos de alta resolución.
   - **Marcas de Agua y Protección (`watermark_protection_engine`):** Inyectar marcas de agua diagonales configurables (ej. "BORRADOR", "CONFIDENCIAL") en los encabezados VML/DrawingML y permitir bloqueo de edición por contraseña o restricción de solo lectura/comentarios (`w:documentProtection`).

3. **Generación de Control de Cambios Nativo (`Tracked Changes`):**
   - Cuando el usuario edite un documento previamente exportado o aplique una mejora con IA sobre el Markdown, generar etiquetas `<w:ins w:author="..." w:date="...">` y `<w:del w:author="..." w:date="...">` para que al abrir el `.docx` en Microsoft Word o GenOffice Docs los cambios puedan aceptarse o rechazarse con un clic.

4. **Puente con `genoffice` CLI / Skill:**
   - Configurar un wrapper limpio en Python que detecte si el binario/CLI de `genoffice` está disponible en el entorno local para delegar operaciones nativas directas sobre `.docx`, `.xlsx` y `.pdf`, con fallback automático al motor interno OpenXML en Python.

## 3. Entregables del Agente
- `core_genoffice/converter.py`: Pipeline principal de AST Markdown a OpenXML.
- `core_genoffice/byte_preserver.py`: Manipulador quirúrgico de paquetes ZIP/OOXML.
- `core_genoffice/omml_math.py`: Traductor de LaTeX a ecuaciones nativas de Word.
- `core_genoffice/tracked_changes.py`: Generador de diffs nativos `w:ins` y `w:del`.