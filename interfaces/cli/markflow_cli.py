"""CLI de MarkFlow Office — `python -m interfaces.cli`.

Distribución agnóstica del agente (patrón REA): las mismas capacidades de la
suite, operables desde cualquier consola sin abrir la UI. Cero dependencias
externas (solo stdlib + los núcleos ya instalados).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from app.version import APP_NOMBRE, APP_VERSION  # noqa: E402


def _cmd_version(_args) -> int:
    print(f"{APP_NOMBRE} v{APP_VERSION}")
    return 0


def _cmd_salud(_args) -> int:
    print(json.dumps({
        "nombre": APP_NOMBRE,
        "version": APP_VERSION,
        "raiz": str(RAIZ),
        "motor": "MarkFlow (saneamiento · QA · temas · PDF editorial)",
        "nucleo_docx": "GenOffice byte-preserving (Apache-2.0)",
        "documentos": str(RAIZ / "storage" / "documentos"),
    }, indent=2, ensure_ascii=False))
    return 0


def _cmd_sanear(args) -> int:
    """Sanea un archivo Markdown (pegado de Word/ChatGPT) con el motor MarkFlow."""
    from motor.sanear import saneanar

    entrada = Path(args.entrada)
    if not entrada.exists():
        print(f"ERROR: no existe {entrada}", file=sys.stderr)
        return 2
    texto = entrada.read_text(encoding="utf-8", errors="ignore")
    saneado, formulas, avisos = saneanar(texto)
    destino = Path(args.salida) if args.salida else entrada.with_name(entrada.stem + "_saneado.md")
    destino.write_text(saneado, encoding="utf-8")
    print(f"✔ Saneado → {destino}  (fórmulas envueltas: {formulas}, avisos: {len(avisos)})")
    for aviso in avisos[:10]:
        print(f"  · {aviso}")
    return 0


def _cmd_convertir(args) -> int:
    """Convierte Markdown → .docx con el núcleo de GenOffice (byte-preserving opcional)."""
    from nucleo.docx_avanzado.converter import markdown_to_openxml

    entrada = Path(args.entrada)
    if not entrada.exists():
        print(f"ERROR: no existe {entrada}", file=sys.stderr)
        return 2
    markdown = entrada.read_text(encoding="utf-8", errors="ignore")

    plantilla = None
    if args.plantilla:
        ruta_plantilla = RAIZ / "plantillas" / "plantilla_base.docx"
        if not ruta_plantilla.exists():
            print("ERROR: no se encontró plantillas/plantilla_base.docx", file=sys.stderr)
            return 2
        plantilla = str(ruta_plantilla)

    docx_bytes = markdown_to_openxml(markdown, template_path=plantilla)
    destino = Path(args.salida) if args.salida else entrada.with_suffix(".docx")
    destino.write_bytes(docx_bytes)
    print(f"✔ DOCX generado → {destino}  ({len(docx_bytes) / 1024:.1f} KB"
          f"{' · byte-preserving' if plantilla else ''})")
    return 0


def _cmd_documentos(args) -> int:
    """Lista (o lee) los documentos del almacén de la suite."""
    dir_docs = RAIZ / "storage" / "documentos"
    if args.leer:
        ruta = dir_docs / args.leer
        if not ruta.exists():
            print(f"ERROR: no existe {ruta}", file=sys.stderr)
            return 2
        print(ruta.read_text(encoding="utf-8", errors="ignore"))
        return 0
    if not dir_docs.exists():
        print("(almacén vacío)")
        return 0
    archivos = sorted(dir_docs.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not archivos:
        print("(almacén vacío)")
        return 0
    for ruta in archivos:
        print(f"{ruta.name:40s} {ruta.stat().st_size / 1024:8.1f} KB")
    return 0


def _cmd_buscar(args) -> int:
    """Búsqueda de texto completo (FTS5) sobre los documentos."""
    from nucleo.busqueda.database_fts import FTS5Index

    indice = FTS5Index(str(RAIZ / "storage" / "busqueda" / "indice_documentos.db"))
    filas = indice.search(args.consulta, limit=args.limite)
    if not filas:
        print("(sin coincidencias)")
        return 0
    for fila in filas:
        print(f"· {Path(fila.get('path', '?')).name}")
        snippet = (fila.get("snippet") or "").replace("\n", " ")
        snippet = snippet.replace("<mark>", "").replace("</mark>", "")[:160]
        if snippet:
            print(f"    {snippet}")
    return 0


def _cmd_servir(args) -> int:
    """Arranca el servidor web de la suite (shell Office + API)."""
    import uvicorn

    puerto = args.puerto
    print(f"▶ {APP_NOMBRE} v{APP_VERSION} → http://127.0.0.1:{puerto}")
    uvicorn.run("app.principal:app", host="127.0.0.1", port=puerto, log_level="info")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m interfaces.cli",
        description=f"{APP_NOMBRE} v{APP_VERSION} — CLI de la suite de documentos con IA.",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("version", help="Muestra la versión SSOT").set_defaults(func=_cmd_version)
    sub.add_parser("salud", help="Estado de la suite").set_defaults(func=_cmd_salud)

    p = sub.add_parser("sanear", help="Sanea un Markdown (pegado de Word/ChatGPT)")
    p.add_argument("entrada", help="Archivo .md de entrada")
    p.add_argument("-o", "--salida", help="Archivo de salida (por defecto *_saneado.md)")
    p.set_defaults(func=_cmd_sanear)

    p = sub.add_parser("convertir", help="Convierte Markdown → .docx (núcleo GenOffice)")
    p.add_argument("entrada", help="Archivo .md de entrada")
    p.add_argument("-o", "--salida", help="Archivo .docx de salida")
    p.add_argument("--plantilla", action="store_true",
                   help="Usa la plantilla base (modo byte-preserving)")
    p.set_defaults(func=_cmd_convertir)

    p = sub.add_parser("documentos", help="Lista o lee documentos del almacén")
    p.add_argument("--leer", metavar="NOMBRE", help="Lee un documento concreto")
    p.set_defaults(func=_cmd_documentos)

    p = sub.add_parser("buscar", help="Búsqueda FTS5 sobre los documentos")
    p.add_argument("consulta")
    p.add_argument("--limite", type=int, default=20)
    p.set_defaults(func=_cmd_buscar)

    p = sub.add_parser("servir", help="Arranca el servidor web de la suite")
    p.add_argument("--puerto", type=int, default=8320)
    p.set_defaults(func=_cmd_servir)

    return parser


def principal(argv=None) -> int:
    # Consolas Windows (cp1252): salida siempre UTF-8 sin romper símbolos
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = construir_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(principal())
