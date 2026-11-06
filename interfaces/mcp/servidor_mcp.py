"""Servidor MCP de MarkFlow Office — `python -m interfaces.mcp`.

Implementación mínima del protocolo MCP (stdio, JSON-RPC 2.0 delimitado por
líneas) con dependencia cero: expone las capacidades de la suite a cualquier
harness de agentes (patrón REA/GenOffice). Registrar con `server.json`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from app.version import APP_NOMBRE, APP_VERSION  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"

# ---------------------------------------------------------------------------
# Catálogo de herramientas (contrato MCP)
# ---------------------------------------------------------------------------
HERRAMIENTAS = [
    {
        "name": "version",
        "description": "Devuelve el nombre y la versión de MarkFlow Office.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "listar_documentos",
        "description": "Lista los documentos Markdown del almacén de la suite.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "leer_documento",
        "description": "Lee el contenido de un documento por su nombre (con o sin .md).",
        "inputSchema": {
            "type": "object",
            "properties": {"nombre": {"type": "string", "description": "Nombre del documento"}},
            "required": ["nombre"],
        },
    },
    {
        "name": "sanear_texto",
        "description": "Sanea Markdown ruidoso (pegado de Word/ChatGPT) con el motor MarkFlow.",
        "inputSchema": {
            "type": "object",
            "properties": {"texto": {"type": "string"}},
            "required": ["texto"],
        },
    },
    {
        "name": "exportar_docx",
        "description": "Convierte Markdown a .docx (núcleo GenOffice). Guarda el archivo y devuelve la ruta.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texto": {"type": "string", "description": "Contenido Markdown"},
                "nombre": {"type": "string", "description": "Nombre del archivo .docx"},
                "con_plantilla": {"type": "boolean", "description": "Modo byte-preserving con plantilla base"},
            },
            "required": ["texto", "nombre"],
        },
    },
    {
        "name": "buscar",
        "description": "Búsqueda de texto completo (FTS5) sobre los documentos.",
        "inputSchema": {
            "type": "object",
            "properties": {"consulta": {"type": "string"}, "limite": {"type": "integer", "default": 10}},
            "required": ["consulta"],
        },
    },
]


# ---------------------------------------------------------------------------
# Implementación de las herramientas
# ---------------------------------------------------------------------------
def _h_version(_args: dict) -> str:
    return f"{APP_NOMBRE} v{APP_VERSION}"


def _h_listar_documentos(_args: dict) -> str:
    dir_docs = RAIZ / "storage" / "documentos"
    if not dir_docs.exists():
        return "(almacén vacío)"
    archivos = sorted(dir_docs.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not archivos:
        return "(almacén vacío)"
    return "\n".join(f"{r.name}  ({r.stat().st_size / 1024:.1f} KB)" for r in archivos)


def _h_leer_documento(args: dict) -> str:
    nombre = str(args.get("nombre", "")).strip()
    if not nombre:
        return "ERROR: falta 'nombre'"
    if not nombre.lower().endswith(".md"):
        nombre += ".md"
    ruta = RAIZ / "storage" / "documentos" / nombre
    if not ruta.exists():
        return f"ERROR: no existe {nombre}"
    return ruta.read_text(encoding="utf-8", errors="ignore")


def _h_sanear_texto(args: dict) -> str:
    from motor.sanear import saneanar

    saneado, formulas, avisos = saneanar(str(args.get("texto", "")))
    resumen = f"[saneado · fórmulas: {formulas} · avisos: {len(avisos)}]\n\n"
    return resumen + saneado


def _h_exportar_docx(args: dict) -> str:
    from nucleo.docx_avanzado.converter import markdown_to_openxml

    nombre = str(args.get("nombre", "documento")).strip() or "documento"
    if not nombre.lower().endswith(".docx"):
        nombre += ".docx"
    con_plantilla = bool(args.get("con_plantilla", False))
    plantilla = RAIZ / "plantillas" / "plantilla_base.docx"
    ruta_plantilla = str(plantilla) if (con_plantilla and plantilla.exists()) else None
    docx_bytes = markdown_to_openxml(str(args.get("texto", "")), template_path=ruta_plantilla)
    destino = RAIZ / "storage" / "salidas" / nombre
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(docx_bytes)
    return f"DOCX generado: {destino} ({len(docx_bytes) / 1024:.1f} KB)"
    


def _h_buscar(args: dict) -> str:
    from nucleo.busqueda.database_fts import FTS5Index

    indice = FTS5Index(str(RAIZ / "storage" / "busqueda" / "indice_documentos.db"))
    limite = int(args.get("limite", 10))
    filas = indice.search(str(args.get("consulta", "")), limit=max(1, limite))
    if not filas:
        return "(sin coincidencias)"
    lineas = []
    for fila in filas:
        nombre = Path(fila.get("path", "?")).name
        snippet = (fila.get("snippet") or "").replace("\n", " ")
        snippet = snippet.replace("<mark>", "").replace("</mark>", "")[:160]
        lineas.append(f"{nombre}: {snippet}")
    return "\n".join(lineas)


DESPACHO = {
    "version": _h_version,
    "listar_documentos": _h_listar_documentos,
    "leer_documento": _h_leer_documento,
    "sanear_texto": _h_sanear_texto,
    "exportar_docx": _h_exportar_docx,
    "buscar": _h_buscar,
}


# ---------------------------------------------------------------------------
# Bucle JSON-RPC sobre stdio (protocolo MCP)
# ---------------------------------------------------------------------------
def _enviar(mensaje: dict) -> None:
    sys.stdout.write(json.dumps(mensaje, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _resultado(id_req, payload: dict) -> dict:
    return {"jsonrpc": "2.0", "id": id_req, "result": payload}


def _error(id_req, codigo: int, mensaje: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_req, "error": {"code": codigo, "message": mensaje}}


def manejar(mensaje: dict) -> dict | None:
    """Procesa un mensaje JSON-RPC y devuelve la respuesta (o None si es notificación)."""
    metodo = mensaje.get("method", "")
    id_req = mensaje.get("id")

    if metodo == "initialize":
        return _resultado(id_req, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": APP_NOMBRE, "version": APP_VERSION},
        })

    if metodo == "notifications/initialized" or metodo.startswith("notifications/"):
        return None

    if metodo == "ping":
        return _resultado(id_req, {})

    if metodo == "tools/list":
        return _resultado(id_req, {"tools": HERRAMIENTAS})

    if metodo == "tools/call":
        nombre = mensaje.get("params", {}).get("name", "")
        argumentos = mensaje.get("params", {}).get("arguments", {}) or {}
        funcion = DESPACHO.get(nombre)
        if not funcion:
            return _error(id_req, -32602, f"Herramienta desconocida: {nombre}")
        try:
            texto = funcion(argumentos)
        except Exception as exc:  # error de herramienta → contenido con is_error
            return _resultado(id_req, {
                "content": [{"type": "text", "text": f"ERROR: {exc}"}],
                "isError": True,
            })
        return _resultado(id_req, {"content": [{"type": "text", "text": texto}]})

    return _error(id_req, -32601, f"Método no implementado: {metodo}")


def principal() -> int:
    """Bucle principal: lee líneas JSON de stdin, responde por stdout."""
    # stdio siempre UTF-8 (los harnesses MCP asumen UTF-8 en el canal)
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue
        try:
            mensaje = json.loads(linea)
        except json.JSONDecodeError:
            _enviar(_error(None, -32700, "JSON inválido"))
            continue
        respuesta = manejar(mensaje)
        if respuesta is not None:
            _enviar(respuesta)
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
