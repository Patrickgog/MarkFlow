"""Router de documentos de MarkFlow Office.

CRUD de documentos Markdown persistidos en `storage/documentos/`, con índice
de búsqueda de texto completo (SQLite FTS5, patrón GenOffice) y saneamiento
vía el motor MarkFlow al abrir/consultar.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.version import APP_NOMBRE, APP_VERSION

RAIZ = Path(__file__).resolve().parents[2]
DIR_DOCS = RAIZ / "storage" / "documentos"
DIR_DOCS.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/documentos", tags=["documentos"])

# Nombre seguro: letras (con acentos), números, espacios, guiones y punto.
_PATRON_NOMBRE = re.compile(r"^[\w][\w \-.]{0,90}$", re.UNICODE)


def sanitizar_nombre_documento(nombre: str) -> str:
    """Sanitiza el nombre eliminando caracteres inválidos para el sistema de archivos y _PATRON_NOMBRE."""
    n = nombre.strip()
    if n.lower().endswith(".md"):
        n = n[:-3]
    # Reemplazar caracteres especiales y prohibidos en Windows por guiones o espacios
    n = re.sub(r'[:+*?"<>|\\/]', ' - ', n)
    n = re.sub(r'[^\w \-.]', ' ', n, flags=re.UNICODE)
    n = re.sub(r'\s+', ' ', n).strip(' -.')
    if not n:
        n = "Documento_Fusionado"
    return n[:80].strip(' -.')


def _ruta_segura(nombre: str) -> Path:
    """Valida el nombre del documento y devuelve su ruta dentro de DIR_DOCS."""
    nombre = nombre.strip()
    if not _PATRON_NOMBRE.match(nombre):
        raise HTTPException(400, "Nombre de documento inválido (usa letras, números, espacios, guion o punto).")
    if not nombre.lower().endswith(".md"):
        nombre += ".md"
    ruta = (DIR_DOCS / nombre).resolve()
    if DIR_DOCS.resolve() not in ruta.parents:
        raise HTTPException(400, "Ruta fuera del almacén de documentos.")
    return ruta


def _indice_fts():
    """Crea (perezosamente) el índice FTS5 sobre el almacén de documentos."""
    from nucleo.busqueda.database_fts import FTS5Index
    return FTS5Index(str(RAIZ / "storage" / "busqueda" / "indice_documentos.db"))


class ModeloNuevo(BaseModel):
    nombre: str
    contenido: str = ""


class ModeloGuardar(BaseModel):
    contenido: str


class ModeloRenombrar(BaseModel):
    nuevo_nombre: str


class ModeloBusqueda(BaseModel):
    consulta: str
    limite: int = 20


class ModeloFusion(BaseModel):
    nombres: list[str]
    nombre_resultado: str
    cada_documento_es_capitulo: bool = True


_RUTA_FUSIONADOS = DIR_DOCS / ".fusionados.json"


def _cargar_fusionados() -> set[str]:
    if not _RUTA_FUSIONADOS.is_file():
        return set()
    try:
        import json
        data = json.loads(_RUTA_FUSIONADOS.read_text(encoding="utf-8"))
        return set(data) if isinstance(data, list) else set()
    except Exception:
        return set()


def _guardar_fusionados(nombres: set[str]) -> None:
    try:
        import json
        _RUTA_FUSIONADOS.write_text(
            json.dumps(sorted(list(nombres)), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def limpiar_referencias_imagenes_huerfanas(texto: str) -> str:
    """Descarta definiciones de imágenes [img-N]: data:... que no tengan referencias en el texto."""
    if not texto:
        return texto
    # Encontrar todas las etiquetas referenciadas: ![...][tag] o [...][tag]
    patron_ref = re.compile(r"!\[.*?\]\[([^\]]+)\]")
    etiquetas_activas = set(patron_ref.findall(texto))

    lineas = texto.splitlines(keepends=True)
    patron_def = re.compile(r"^\s*\[([^\]]+)\]:\s*(data:image/[^\s]+|\S+)")

    lineas_filtradas: list[str] = []
    for linea in lineas:
        m = patron_def.match(linea)
        if m:
            etiqueta = m.group(1).strip()
            # Si es una definición de imagen (data:image o prefijo img-) y no está referenciada, se descarta
            if m.group(2).startswith("data:image/") or etiqueta.startswith("img-"):
                if etiqueta not in etiquetas_activas:
                    continue
        lineas_filtradas.append(linea)

    return "".join(lineas_filtradas)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("")
async def listar() -> dict:
    """Lista los documentos del almacén (más recientes primero)."""
    fusionados = _cargar_fusionados()
    items = []
    for ruta in DIR_DOCS.glob("*.md"):
        stat = ruta.stat()
        items.append({
            "nombre": ruta.name,
            "tamano": stat.st_size,
            "modificado": stat.st_mtime,
            "en_fusion": ruta.name in fusionados,
        })
    items.sort(key=lambda x: x["modificado"], reverse=True)
    return {"ok": True, "datos": items}


@router.post("/fusionar")
async def fusionar(modelo: ModeloFusion) -> dict:
    """Fusiona múltiples documentos respetando el orden especificado."""
    if not modelo.nombres or len(modelo.nombres) < 2:
        raise HTTPException(400, "Se requieren al menos 2 documentos para fusionar.")

    from motor.capitulos import consolidar_documentos

    docs_lista: list[tuple[str, str]] = []
    for nom in modelo.nombres:
        ruta_origen = _ruta_segura(nom)
        if not ruta_origen.is_file():
            raise HTTPException(404, f"No se encontró el documento «{nom}» para la fusión.")
        docs_lista.append((ruta_origen.name, ruta_origen.read_text(encoding="utf-8")))

    nombre_res = modelo.nombre_resultado.strip()
    if not nombre_res:
        nombre_primero = docs_lista[0][0].replace(".md", "").replace(".MD", "")
        nombre_res = f"Fusion - {nombre_primero} y {len(docs_lista) - 1} mas"

    nombre_res_limpio = sanitizar_nombre_documento(nombre_res)
    ruta_destino = _ruta_segura(nombre_res_limpio)
    if ruta_destino.exists():
        base = ruta_destino.stem
        i = 2
        while (DIR_DOCS / f"{base}_{i}.md").exists():
            i += 1
        ruta_destino = DIR_DOCS / f"{base}_{i}.md"

    texto_fusionado = consolidar_documentos(
        docs_lista,
        modo_capitulos=modelo.cada_documento_es_capitulo,
        salto_entre_archivos=modelo.cada_documento_es_capitulo,
    )

    ruta_destino.write_text(texto_fusionado, encoding="utf-8")
    try:
        _indice_fts().index_document(str(ruta_destino), ruta_destino.stem, texto_fusionado)
    except Exception:
        pass

    # Actualizar documentos incluidos en fusión
    fusionados = _cargar_fusionados()
    for nom in modelo.nombres:
        n_seg = _ruta_segura(nom).name
        fusionados.add(n_seg)
    _guardar_fusionados(fusionados)

    return {
        "ok": True,
        "datos": {
            "nombre": ruta_destino.name,
            "resultado": ruta_destino.name,
            "total_documentos": len(docs_lista),
            "fusionados": [d[0] for d in docs_lista],
            "cada_documento_es_capitulo": modelo.cada_documento_es_capitulo,
        },
    }


@router.post("")
async def crear(modelo: ModeloNuevo) -> dict:
    """Crea un nuevo documento Markdown con esqueleto básico."""
    ruta = _ruta_segura(modelo.nombre)
    if ruta.exists():
        raise HTTPException(409, f"Ya existe un documento llamado «{ruta.name}».")
    contenido = modelo.contenido or (
        f"# {ruta.stem}\n\n"
        "Escribe aquí tu documento técnico.\n\n"
        "## Introducción\n\n"
        "…\n"
    )
    ruta.write_text(contenido, encoding="utf-8")
    _indice_fts().index_document(str(ruta), ruta.stem, contenido)
    return {"ok": True, "datos": {"nombre": ruta.name}}


@router.get("/{nombre}")
async def leer(nombre: str) -> dict:
    """Devuelve el contenido de un documento."""
    ruta = _ruta_segura(nombre)
    if not ruta.exists():
        raise HTTPException(404, f"No existe el documento «{ruta.name}».")
    return {
        "ok": True,
        "datos": {
            "nombre": ruta.name,
            "contenido": ruta.read_text(encoding="utf-8"),
            "modificado": ruta.stat().st_mtime,
        },
    }


@router.get("/{nombre}/descargar")
async def descargar(nombre: str) -> FileResponse:
    """Descarga directa del archivo Markdown como archivo adjunto (.md)."""
    ruta = _ruta_segura(nombre)
    if not ruta.exists():
        raise HTTPException(404, f"No existe el documento «{ruta.name}».")
    return FileResponse(
        path=str(ruta),
        media_type="text/markdown; charset=utf-8",
        filename=ruta.name,
    )


@router.put("/{nombre}")
async def guardar(nombre: str, modelo: ModeloGuardar) -> dict:
    """Guarda (sobrescribe) el contenido de un documento y lo indexa."""
    ruta = _ruta_segura(nombre)
    if not ruta.exists():
        raise HTTPException(404, f"No existe el documento «{ruta.name}».")
    contenido_limpio = limpiar_referencias_imagenes_huerfanas(modelo.contenido)
    ruta.write_text(contenido_limpio, encoding="utf-8")
    _indice_fts().index_document(str(ruta), ruta.stem, contenido_limpio)
    return {"ok": True, "datos": {"nombre": ruta.name, "guardado_en": time.time()}}


@router.post("/{nombre}/renombrar")
async def renombrar(nombre: str, modelo: ModeloRenombrar) -> dict:
    """Renombra un documento existente actualizando el archivo y el índice FTS5."""
    ruta_origen = _ruta_segura(nombre)
    if not ruta_origen.exists():
        raise HTTPException(404, f"No existe el documento «{ruta_origen.name}».")
    ruta_destino = _ruta_segura(modelo.nuevo_nombre)
    if ruta_destino.exists() and ruta_destino.resolve() != ruta_origen.resolve():
        raise HTTPException(409, f"Ya existe un documento llamado «{ruta_destino.name}».")

    contenido = ruta_origen.read_text(encoding="utf-8")
    if ruta_destino.resolve() != ruta_origen.resolve():
        ruta_origen.unlink()
        try:
            _indice_fts().remove_document(str(ruta_origen))
        except Exception:
            pass
    ruta_destino.write_text(contenido, encoding="utf-8")
    _indice_fts().index_document(str(ruta_destino), ruta_destino.stem, contenido)
    return {"ok": True, "datos": {"nombre": ruta_destino.name, "anterior": ruta_origen.name}}


@router.delete("/{nombre}")
async def eliminar(nombre: str) -> dict:
    """Elimina un documento del almacén."""
    ruta = _ruta_segura(nombre)
    if not ruta.exists():
        raise HTTPException(404, f"No existe el documento «{ruta.name}».")
    ruta.unlink()
    try:
        _indice_fts().remove_document(str(ruta))
    except Exception:
        pass  # el índice es derivable: se reconstruirá al guardar
    return {"ok": True, "datos": {"nombre": ruta.name, "eliminado": True}}


@router.post("/buscar")
async def buscar(modelo: ModeloBusqueda) -> dict:
    """Búsqueda de texto completo (FTS5) sobre todos los documentos."""
    consulta = modelo.consulta.strip()
    if not consulta:
        return JSONResponse({"ok": True, "datos": []})
    try:
        filas = _indice_fts().search(consulta, limit=max(1, min(modelo.limite, 50)))
    except Exception:
        # FTS5 usa una sintaxis de consulta propia; si falla, busca por substring.
        filas = []
        aguja = consulta.lower()
        for ruta in DIR_DOCS.glob("*.md"):
            texto = ruta.read_text(encoding="utf-8", errors="ignore")
            if aguja in texto.lower():
                pos = texto.lower().find(aguja)
                filas.append({"path": str(ruta), "snippet": texto[max(0, pos - 60):pos + 120]})
    resultados = []
    for fila in filas:
        ruta_doc = Path(fila.get("path", ""))
        if not ruta_doc.is_file():
            continue
        fragmento = str(fila.get("snippet", ""))
        fragmento = fragmento.replace("<mark>", "").replace("</mark>", "")
        resultados.append({
            "nombre": ruta_doc.name,
            "fragmento": fragmento,
        })
    return {"ok": True, "datos": resultados}
