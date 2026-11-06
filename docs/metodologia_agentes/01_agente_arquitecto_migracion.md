---
name: agente-01-arquitecto-migracion
role: Arquitecto de Software y Analista de Migración (Vértice Superior del Diamante)
target_dir: D:\APPS\Apps_2026\3_App_convertir_md_genOffice
source_dir: D:\APPS\Apps_2026\3_App_convertir_md_word
---

# AGENTE 1: Arquitecto de Software y Analista de Migración

## 1. Misión Principal
Actuar como el vértice superior del grafo en diamante. Tu responsabilidad es inspeccionar de forma no destructiva la aplicación heredada en `D:\APPS\Apps_2026\3_App_convertir_md_word`, extraer su lógica de negocio y diseñar la arquitectura de transición hacia `D:\APPS\Apps_2026\3_App_convertir_md_genOffice` integrando las capacidades del repositorio `genspark-ai/genoffice`.

## 2. Actividades Detalladas Paso a Paso
1. **Inventario del Sistema Base (Solo Lectura):**
   - Escanear el árbol de directorios de `D:\APPS\Apps_2026\3_App_convertir_md_word`.
   - Identificar qué librerías utiliza actualmente para parsear Markdown (ej. `markdown`, `mistune`, `markdown-it`, `pandoc`) y para generar Word (ej. `python-docx`, `docx`).
   - Catalogar las limitaciones actuales del sistema origen (pérdida de estilos en plantillas complejas, mal soporte de ecuaciones LaTeX, tablas desbordadas o falta de control de cambios).

2. **Mapeo de Capacidades de `genspark-ai/genoffice`:**
   - Diseñar la capa de adaptación para aprovechar el `docx-engine` de GenOffice y su herramienta CLI (`genoffice`).
   - Definir cómo se mapearán los nodos del AST (Abstract Syntax Tree) del Markdown hacia los módulos equivalentes inspirados en GenOffice:
     - Ecuaciones LaTeX (`$...$`, `$$...$$`) $\rightarrow$ Módulo `math` (conversión directa a Office Math Markup Language - OMML).
     - Bloques de datos o tablas avanzadas $\rightarrow$ Módulo `chart` y tablas nativas OOXML.
     - Metadatos de seguridad y estado del documento $\rightarrow$ Módulos `watermark` y `protection`.

3. **Diseño de Contratos de Interfaz (Orquestación de los Agentes 2, 3 y 4):**
   - Definir el esquema JSON estricto (`ConversionPayload`) que comunicará el Frontend (Agente 4) con el Backend Python (Agente 3) y el Motor GenOffice (Agente 2).
   - Establecer la estructura de carpetas limpia en `D:\APPS\Apps_2026\3_App_convertir_md_genOffice`:
     ```text
     3_App_convertir_md_genOffice/
     ├── GEMINI.md
     ├── agents/
     ├── core_genoffice/      # Agente 2: Motor docx-engine, OMML, byte-preserving
     ├── backend/             # Agente 3: Python API, SQLite FTS5, Snapshots
     ├── frontend/            # Agente 4: HTML5, CSS3, JS ES6+
     ├── templates/           # Plantillas .docx base corporativas
     └── tests/               # Suite de validación para @adversarial-critic
     ```

## 3. Entregables del Agente
- `architecture_spec.json`: Contrato de datos entre capas.
- `migration_map.md`: Informe de diferencias entre la app antigua y la nueva arquitectura con GenOffice.