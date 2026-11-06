---
name: markflow-office
description: Suite de documentos con IA (MarkFlow Office) — saneamiento de Markdown, conversión a DOCX/HTML/PDF, gestión de documentos técnicos y búsqueda local. Usar cuando el usuario quiera sanear texto pegado de Word/ChatGPT, convertir Markdown a Word/HTML/PDF, o consultar documentos de la suite.
---

# MarkFlow Office — Skill del agente

Suite de documentos con IA, local-first y 100 % offline. Combina el motor
MarkFlow (saneamiento, QA, temas HTML/Word, PDF editorial) con el núcleo
byte-preserving de GenOffice.

## Comandos CLI (preferidos — sin UI)

```bash
# Versión y estado
python -m interfaces.cli version
python -m interfaces.cli salud

# Saneamiento de Markdown (pegado de Word/ChatGPT con fórmulas rotas)
python -m interfaces.cli sanear entrada.md -o salida.md

# Conversión a Word (núcleo GenOffice; --plantilla = byte-preserving)
python -m interfaces.cli convertir entrada.md -o informe.docx --plantilla

# Documentos del almacén (storage/documentos/)
python -m interfaces.cli documentos
python -m interfaces.cli documentos --leer "Informe técnico.md"

# Búsqueda de texto completo (FTS5 local)
python -m interfaces.cli buscar "demanda máxima"

# Servidor web de la suite (puerto 8320)
python -m interfaces.cli servir --puerto 8320
```

## Servidor MCP

```bash
python -m interfaces.mcp
```

Herramientas MCP: `version`, `listar_documentos`, `leer_documento`,
`sanear_texto`, `exportar_docx`, `buscar`.

## Reglas operativas

1. **Sanea antes de convertir**: todo Markdown proveniente de Word/ChatGPT
   debe pasar por `sanear` (o la herramienta MCP `sanear_texto`) antes de
   exportar, para reparar fórmulas `$…$` y residuos de formato.
2. **Rutas del almacén**: los documentos viven en `storage/documentos/*.md`;
   las salidas en `storage/salidas/`. No escribir fuera de ellas.
3. **Byte-preserving**: al exportar DOCX desde una plantilla, el núcleo
   conserva estilos/cabeceras/numeración de la plantilla base
   (`plantillas/plantilla_base.docx`). No regenerar el documento completo
   si solo cambian partes.
4. **Offline primero**: la IA usa Ollama local (configuración en
   `storage/config_ia.json`). Solo usar proveedores externos si el usuario
   configuró su clave (BYO-key).
5. **Puerto**: la UI corre en `http://127.0.0.1:8320` (`/` shell Office,
   `/clasico` motor MarkFlow completo).
