---
name: agente-03-backend-python-datos
role: Ingeniero Backend Python, Indexación SQLite FTS5 y Gestión de Estado (Rama Central del Diamante)
target_dir: D:\APPS\Apps_2026\3_App_convertir_md_genOffice\backend
---

# AGENTE 3: Ingeniero Backend Python & Persistencia Local

## 1. Misión Principal
Desarrollar el servidor backend en Python encargado de orquestar la lógica de archivos en Windows, gestionar el historial de snapshots con rollback instantáneo, proveer búsqueda de texto completo ultrarrápida mediante SQLite FTS5 e integrar conectores opcionales de IA local/remota (BYOK).

## 2. Actividades Detalladas Paso a Paso
1. **Motor de Indexación Local SQLite FTS5 (Inspirado en GenOffice Home Search):**
   - Crear una base de datos local `genoffice_index.db` utilizando la extensión `FTS5` (Full-Text Search) de SQLite.
   - Indexar automáticamente el título, ruta, etiquetas, fecha de modificación y el contenido completo de cada archivo `.md`, `.html` y `.docx` generado o importado en la aplicación.
   - Exponer un endpoint de búsqueda semántica/léxica (`GET /api/search?q=...`) que devuelva fragmentos resaltados (`snippet()`) en menos de 15 milisegundos.

2. **Sistema de Snapshots y Rollback en Un Clic:**
   - Antes de cada conversión o edición asistida, almacenar un snapshot diferencial (hash SHA-256 + delta comprimido) en la base de datos local.
   - Permitir al usuario comparar cualquier versión anterior con la actual y restaurarla con un solo clic (`POST /api/snapshots/{id}/rollback`).

3. **Pasarela de IA Agnóstica "Bring Your Own Key" (BYOK) y 100% Local:**
   - Implementar un cliente unificado y opcional para mejorar secciones del Markdown antes de exportar a Word (reescritura técnica, corrección de estilo, generación de resúmenes ejecutivos).
   - Soportar endpoints 100% locales sin costo (Ollama, LM Studio, Jan en `http://localhost:11434/v1`) y APIs externas opcionales (Gemini API, OpenAI, Claude, DeepSeek) configurables desde la interfaz.

4. **Gestión Segura del Sistema de Archivos en Windows:**
   - Implementar manejo de archivos temporales atómicos y detección de bloqueo de archivos de Microsoft Word (archivos temporales `~$*.docx`), emitiendo alertas claras en español si el usuario tiene el documento destino abierto en Word al momento de sobrescribir.

## 3. Entregables del Agente
- `backend/server.py`: Servidor API (FastAPI/Flask) con endpoints asíncronos.
- `backend/database_fts.py`: Gestor SQLite FTS5 e historial de snapshots.
- `backend/ai_gateway.py`: Conector multi-modelo (Ollama local + BYOK).
- `backend/file_manager.py`: Utilidades `pathlib` con control de bloqueos en Windows.