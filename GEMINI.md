# GEMINI.md — Contexto de Desarrollo y Reglas de Trabajo de MarkFlow AI

Este archivo define el marco de trabajo para cualquier IA o desarrollador que opere en este repositorio. **Su incumplimiento invalida la entrega.**

---

## 0. Identidad del proyecto

- **Nombre:** MarkFlow AI — Suite de transformación documental (Markdown → MD limpio / HTML / DOCX) con interfaz de lujo.
- **Naturaleza:** aplicación web local (FastAPI), sin nube, para transformar el Markdown defectuoso de asistentes de IA (ChatGPT, Claude, NotebookLM) en documentos profesionales.
- **Pilares:** arquitectura limpia · UI glassmorphism con isotipo · español técnico · higiene de carpeta absoluta.

## 1. Idioma y estilo de comunicación

1. Todo se escribe en **español técnico** (respuestas, planes, comentarios, docstrings, README).
2. Nombres de variables, funciones y commits pueden ir en inglés estándar; la explicación, no.
3. Tono directo, riguroso y de producción — sin divagaciones.

## 2. Reglas de higiene de carpeta (inviolables)

| Regla | Detalle |
|---|---|
| **R1. Raíz mínima** | Solo estos archivos sueltos: `README.md`, `GEMINI.md`, `.gitignore`, `requirements.txt`, `pytest.ini` (config del runner de pruebas) y `lanza_MarkFlow.bat` (fase de despliegue). Carpeta `.venv/` permitida (ignorada por git). Prohibido cualquier otro archivo suelto en raíz. |
| **R2. Cada cosa en su carpeta** | Backend → `app/` · Motores → `motor/` · Vistas → `templates/` · CSS → `static/css/` · JS → `static/js/` · Imagen → `static/img/` · Tests → `pruebas/` · Planes → `docs/planes/` · Auditoría → `historial-resumenes/` · Salidas efímeras → `salidas/`. |
| **R3. Cero basura** | Prohibido crear cachés, temporales o borradores dentro del proyecto. Scripts de diagnóstico van a un `temp` **externo** (`C:\Users\<usuario>\AppData\Local\Temp\…`). `salidas/` puede purgarse sin aviso. |
| **R4. Nombres** | Módulos Python `snake_case`; archivos de planes `0001-nombre.md`; resúmenes `AAAA-MM-DD_vX.Y.Z_titulo.md`. |
| **R5. Nada se borra sin confirmar** | Tratar cada archivo preexistente como trabajo del usuario; investigar antes de eliminar o sobrescribir. |
| **R6. Encoding windows** | Python: UTF-8 (`-X utf8`) · `.bat`: CRLF · `.md`: preferir UTF-8 CRLF. Nunca editar `python -c` con comillas anidadas en PowerShell; usar scripts externos en temp. |

## 3. Estándares de código

1. **Python:** PEP 8, type hints, docstrings en español, funciones puras en `motor/` (sin estado global), errores dominio-propio (excepciones tipadas, no `print`).
2. **Backend FastAPI:** routers por dominio, esquemas Pydantic para entrada/salida, HTTP coherente (200/400/415/422), timeouts y límites de tamaño en la ingestión.
3. **Frontend:** CSS con **tokens de diseño** (variables `--…` para paleta, radios, sombras, easing); clases BEM; JS vanilla modular (IIFE/ES modules) sin framework; accesibilidad AA (contraste, foco visible, `aria-*`).
4. **Diseño (contrato visual):** oscuro fondo `#0b0f19`, vidrio `backdrop-filter: blur(12px)`, degradado acento `linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)`, sombras claras `0 10px 25px -5px rgba(0,0,0,.05)`, interacción `translateY(-2px)` + ripple + `0.3s cubic-bezier`. El modo claro/oscuro cambia **solo** por tokens, nunca duplicando estilos.

## 4. Proceso de trabajo

1. **Planes numerados:** toda hoja de ruta o tarea compleja genera `docs/planes/NNNN-titulo.md` con tareas, criterios de aceptación, riesgos y versiones objetivo. Prohibido improvisar fases grandes sin plan.
2. **Versionado SemVer automático:** todo cambio funcional incrementa `Major.Minor.Patch`, se refleja en el SSOT (`app/version.py`) y se audita en `historial-resumenes/` (archivo `AAAA-MM-DD_vX.Y.Z_titulo.md`).
3. **Definition of Done:** `python -m py_compile` limpio → pruebas en `pruebas/` verdes → QA de la conversión sin observaciones → SSOT de versión actualizado → registro en `historial-resumenes/` → resumen al usuario con bloque de control de cambios.
4. **Motor primero, UI después:** cada capacidad del `motor/` debe poder ejecutarse y probarse por línea de comandos (pytest) antes de exponerla en la interfaz.
5. **Palabra gatillo `RESUMEN`:** emitir reporte estructurado (versión vigente, tareas completadas, archivos tocados, próximos pasos) y archivarlo en `historial-resumenes/`.
6. **Investigación previa y adopción de diseños validados:** Cuando te encuentres con una funcionalidad desconocida, no la implementes desde cero de inmediato. Primero busca en GitHub proyectos de código abierto similares que estén activamente mantenidos y tengan licencias claras, compara enfoques de implementación, dependencias y problemas conocidos. Prioriza adoptar diseños validados, no copies directamente código incompatible o de fuentes desconocidas y aplícalo si lo necesitas.

## 5. Dependencias permitidas

- Python: `fastapi`, `uvicorn`, `jinja2`, `py` y **ninguna más sin plan aprobado** (p. ej. `markdown-it-py`, `mdit-py-plugins`, `pandoc` externo, `pydantic`).
- Node: solo el render KaTeX/Mermaid vía CDN o binario local; prohibidos `node_modules` en el repo.
- Nada de llamadas a servicios externos con contenido del usuario.

## 6. Anti-patrones prohibidos

1. UI con estilos inline o colores hardcodeados fuera de los tokens.
2. Lógica de conversión dentro de rutas FastAPI (debe vivir en `motor/`).
3. Devolver errores crudos al frontend (`traceback`); solo mensajes tipados + `detalle`.
4. Duplicar el emparejamiento de fórmulas: una sola implementación canónica en `motor/`.
5. Ignorar encoding: toda ingestión detecta codificación y sanea mojibake antes de transformar.
