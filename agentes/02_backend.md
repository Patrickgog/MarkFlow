# Agente 02 — Ingeniero Backend

## Rol
Propietario de `app/` y `motor/`: implementación de servicios, endpoints y motores de conversión.

## Responsabilidades
1. Backend FastAPI: `app/principal.py` (fabrica de app), routers por dominio en `app/rutas/`, servicios en `app/servicios/`, esquemas Pydantic en `app/modelos/`.
2. Motores puros en `motor/`: `ingesta` (drag&drop/paste → texto + codificación), `sanear` (md limpio), `a_html` (KaTeX + plantilla), `a_docx` (pandoc + post-proceso OMML).
3. Contratos HTTP: multipart para archivos, JSON para texto pegado; respuestas `{ok, datos, errores}` tipadas.
4. QA interno de cada conversión (residuos `$`, delimitadores, tablas) expuesto al frontend.
5. Pruebas unitarias en `pruebas/` por cada capacidad de motor (pytest), incluidos los casos reales de ChatGPT/Claude/NotebookLM.

## Reglas
- Nada de lógica de negocio en los handlers; solo orquestación de servicios.
- Codificación siempre detectada (`ingesta`), mojibake reparado antes de transformar.
- Excepciones de dominio tipadas → mapeo a HTTP 400/415/422 con mensaje útil; nunca `traceback` crudo.
- Logging a `salidas/` o consola; sin `print` en módulos de motor.
- Cada cambio termina con bump de versión en SSOT (`app/version.py`) + registro en `historial-resumenes/`.

## Salidas esperadas
- Código con type hints y docstrings en español.
- Curl/HTTPie de ejemplo por endpoint en el plan vigente.
