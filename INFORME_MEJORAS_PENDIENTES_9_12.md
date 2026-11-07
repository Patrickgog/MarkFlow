# Informe de Mejoras Pendientes (Puntos 9-12)

Generado automáticamente. Estos puntos quedan pendientes para corrección posterior.

## Punto 9 — obsidian_wikilinks

**Problemas:**
- Skill muy extenso (4700+ líneas) que mezcla lógica con instrucciones.
- No hay script automatizado; todo es manual por el agente.
- La conversión LaTeX es frágil (regex complejos, casos edge).
- No hay validación post-procesamiento automática (solo instrucciones manuales).

**Mejoras propuestas:**
- Extraer la lógica de corrección LaTeX a `scripts/corregir_latex.py` (ya existe `correccion_final_v3.py` referenciado).
- Crear pipeline automatizado: inventario → normalización → wikilinks → MOC → reporte.
- Añadir tests de regresión para la conversión LaTeX (casos edge).
- Modularizar: un script por fase, orquestados por un `main.py`.
- Añadir `--dry-run` y reporte de cambios.

## Punto 10 — correccion_markdown

**Problemas:**
- No hay script; todo es manual.
- No valida que el Markdown resultante sea válido (lint).
- No maneja plantillas con placeholders `{{ var }}` de forma segura (regla dice no tocarlos, pero no hay validación).

**Mejoras propuestas:**
- Crear script `scripts/corregir_md.py` con reglas configurables.
- Validar Markdown resultante con un linter (markdownlint).
- Proteger placeholders `{{ ... }}` con regex y verificar que sigan intactos al final.
- Añadir modo `--check` (solo reporta, no modifica).

## Punto 11 — ingesta_subvault

**Problemas:**
- No hay script.
- Estructura rígida (00_Meta/, 01_Fuentes/, etc.) sin configuración.
- No valida duplicados entre sub-vaults.

**Mejoras propuestas:**
- Crear script `scripts/ingestar.py`.
- Configurar estructura por template (YAML).
- Detectar duplicados por hash de contenido.
- Generar MOC automático.

## Punto 12 — Skills de dominio específico

Skills afectados: `gemini_md_resolver`, `Generador_AutoCAD_VBA`, `generador_excel_calculo`, `Generador_Memoria_Tecnica`, `1_Mathpocock`.

**Mejoras propuestas:**
- Verificar que cada uno tenga `scripts/` funcionales.
- Añadir ejemplos de uso y casos de prueba.
- Documentar dependencias externas (AutoCAD, Excel, Calibre, etc.).
- Añadir validación de inputs y manejo de errores.

## Prioridad sugerida

1. Punto 10 (correccion_markdown) — alto impacto, script simple.
2. Punto 9 (obsidian_wikilinks) — alto impacto, pero complejo.
3. Punto 11 (ingesta_subvault) — medio impacto.
4. Punto 12 (dominio específico) — bajo impacto, incremental.

---
*Generado automáticamente. Revisar y corregir posteriormente.*