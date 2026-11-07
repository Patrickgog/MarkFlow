"""Router Office de MarkFlow Office.

Capa 2 (API) para la shell de la suite: salud, configuración y preguntas a la
IA (BYO-key / Ollama local) y exportación rápida Markdown → .docx con el núcleo
de GenOffice (generación directa o byte-preserving con plantilla).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from nucleo.docx_avanzado.converter import markdown_to_openxml
from motor.formulas import latex_a_unicode
from app.servicios import sesiones
from app.servicios.editor_markdown import doc_a_md, md_a_doc
from app.version import APP_NOMBRE, APP_VERSION

RAIZ = Path(__file__).resolve().parents[2]
ARCHIVO_CONFIG_IA = RAIZ / "storage" / "config_ia.json"
PLANTILLA_BASE = RAIZ / "plantillas" / "plantilla_base.docx"
DIR_PLANTILLAS_WORD = RAIZ / "storage" / "plantillas_word"
DIR_PLANTILLAS_WORD.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/office", tags=["office"])

_MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_PATRON_NOMBRE = re.compile(r"^[\w][\w \-.]{0,90}$", re.UNICODE)


# ---------------------------------------------------------------------------
# Salud
# ---------------------------------------------------------------------------
@router.get("/salud")
async def salud() -> dict:
    """Estado de la suite: versión, IA disponible y plantilla byte-preserving."""
    from nucleo.ia.ai_gateway import AIConnector
    ia = AIConnector(str(ARCHIVO_CONFIG_IA) if ARCHIVO_CONFIG_IA.exists() else None)
    try:
        disponibilidad = ia.check_availability()
    except Exception:
        disponibilidad = {"local": False, "external": False}
    return {
        "ok": True,
        "datos": {
            "nombre": APP_NOMBRE,
            "version": APP_VERSION,
            "ia": disponibilidad,
            "plantilla_byte_preserving": PLANTILLA_BASE.exists(),
        },
    }


# ---------------------------------------------------------------------------
# IA (configuración BYO-key + preguntas)
# ---------------------------------------------------------------------------
def _cargar_config() -> dict:
    if ARCHIVO_CONFIG_IA.exists():
        try:
            return json.loads(ARCHIVO_CONFIG_IA.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"local": {"enabled": True, "base_url": "http://localhost:11434", "default_model": "llama3"},
            "external": {"enabled": False, "providers": {}}}


def _enmascarar(config: dict) -> dict:
    """Devuelve la config con las claves enmascaradas (nunca salen completas)."""
    copia = json.loads(json.dumps(config, ensure_ascii=False))
    for proveedor in copia.get("external", {}).get("providers", {}).values():
        clave = str(proveedor.get("api_key", ""))
        proveedor["api_key"] = ("••••" + clave[-4:]) if clave else ""
    return copia


@router.get("/ia/config")
async def ia_config_ver() -> dict:
    return {"ok": True, "datos": _enmascarar(_cargar_config())}


class ModeloConfigIA(BaseModel):
    config: dict


@router.post("/ia/config")
async def ia_config_guardar(modelo: ModeloConfigIA) -> dict:
    """Guarda la configuración de IA (las claves viajan completas solo aquí)."""
    ARCHIVO_CONFIG_IA.parent.mkdir(parents=True, exist_ok=True)
    # Si el frontend devuelve una clave enmascarada, conserva la original.
    previa = _cargar_config()
    nueva = modelo.config
    for nombre_prov, prov in nueva.get("external", {}).get("providers", {}).items():
        clave_nueva = str(prov.get("api_key", ""))
        clave_previa = str(previa.get("external", {}).get("providers", {}).get(nombre_prov, {}).get("api_key", ""))
        if "••••" in clave_nueva or not clave_nueva.strip():
            prov["api_key"] = clave_previa
    ARCHIVO_CONFIG_IA.write_text(json.dumps(nueva, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "datos": _enmascarar(nueva)}


class ModeloPregunta(BaseModel):
    texto: str
    contexto: str = ""
    usar_local: bool = True
    modelo: str = ""


@router.post("/ia/pregunta")
async def ia_pregunta(modelo: ModeloPregunta) -> dict:
    """Panel «Preguntar IA»: responde con el proveedor configurado (offline primero)."""
    texto = modelo.texto.strip()
    if not texto:
        raise HTTPException(400, "La pregunta no puede estar vacía.")
    prompt = texto
    if modelo.contexto.strip():
        prompt = (
            "Responde usando SOLO el siguiente contexto del documento. "
            "Si la respuesta no está en el contexto, dilo con claridad.\n\n"
            f"--- CONTEXTO ---\n{modelo.contexto[:8000]}\n--- FIN CONTEXTO ---\n\n"
            f"Pregunta: {texto}"
        )
    from nucleo.ia.ai_gateway import AIConnector
    ia = AIConnector(str(ARCHIVO_CONFIG_IA) if ARCHIVO_CONFIG_IA.exists() else None)
    respuesta = ia.generate_text(prompt, model=modelo.modelo or None, use_local=modelo.usar_local)
    proveedor = "ollama-local" if modelo.usar_local else "externo"
    ok = respuesta and not respuesta.startswith("[Error")
    return {
        "ok": bool(ok),
        "datos": {
            "respuesta": respuesta,
            "proveedor": proveedor,
            "atendido_en": time.time(),
        },
    }


# ---------------------------------------------------------------------------
# Exportación rápida Markdown → DOCX (con motor completo MarkFlow a_docx)
# ---------------------------------------------------------------------------
class ModeloExportar(BaseModel):
    nombre: str = "documento"
    markdown: str = ""
    texto: str = ""
    nombre_archivo: str = ""
    con_plantilla: bool = False
    estilo_excel: str = "clasico"
    # Parámetros avanzados del motor Word
    tema_word: str = "defecto"
    paleta_tabla: str = "defecto"
    paleta_suave_tablas: bool = True
    color_titulos_word: str = "negro"
    fuente: str = "Calibri"
    tamanio_pt: float = 11.0
    interlineado: float = 1.0
    alineacion: str = "justificado"
    fuente_tabla: str | None = None
    tamanio_tabla_pt: float | None = None
    pie_pagina: str = ""
    alineacion_pie: str = "derecha"
    normas_apa: bool = False
    numerar_ecuaciones: bool = False
    crear_indice: bool = False
    posicion_indice: str = "inicio"
    numerar_paginas: bool = True
    color_tit_h1: str = ""
    color_tit_h2: str = ""
    color_tabla_cabecera: str = ""
    color_tabla_filas: str = ""
    color_tabla_borde: str = ""
    modo_color_titulos: str = "auto"
    # Opciones de Hoja de Membrete
    plantilla_word: str = ""
    zona_top: float | None = None
    zona_bottom: float | None = None
    zona_left: float | None = None
    zona_right: float | None = None
    # Parámetros avanzados de Excel
    modo_hojas: str = "multi_hoja"
    tamano_fuente: int = 10
    mostrar_gridlines: bool = True
    autofit: bool = True
    ancho_col: str = "auto"
    paleta_id: str | None = None

    def obtener_nombre(self) -> str:
        return self.nombre_archivo.strip() or self.nombre.strip() or "documento"

    def obtener_markdown(self) -> str:
        return self.markdown if self.markdown else self.texto


def validar_plantilla_word_segura(nombre_archivo: str) -> Path:
    """Valida que un nombre de plantilla pertenezca de forma segura a DIR_PLANTILLAS_WORD.
    
    Aplica resolve() y relative_to() para prevenir ataques de Path Traversal (../).
    Lanza HTTPException 400 si el nombre es inválido o 404 si el archivo no existe.
    """
    nombre_limpio = (nombre_archivo or "").strip()
    if not nombre_limpio or not nombre_limpio.lower().endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail={"codigo": "NOMBRE_PLANTILLA_INVALIDO", "detalle": "Debe especificar un archivo .docx válido."},
        )

    base = DIR_PLANTILLAS_WORD.resolve()
    candidato = (base / nombre_limpio).resolve()

    try:
        candidato.relative_to(base)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"codigo": "ACCESO_DENEGADO", "detalle": "Intento de acceso fuera del directorio de plantillas."},
        )

    if not candidato.is_file():
        raise HTTPException(
            status_code=404,
            detail={"codigo": "PLANTILLA_NO_ENCONTRADA", "detalle": f"La plantilla '{nombre_limpio}' no existe en disco."},
        )

    return candidato


@router.get("/plantillas-word")
async def listar_plantillas_word() -> dict:
    """Lista las hojas de membrete .docx físicamente presentes en storage/plantillas_word/."""
    plantillas = []
    if DIR_PLANTILLAS_WORD.is_dir():
        for f in sorted(DIR_PLANTILLAS_WORD.glob("*.docx")):
            if f.is_file():
                tamano_kb = max(1, round(f.stat().st_size / 1024))
                plantillas.append({
                    "etiqueta": f.stem,
                    "archivo": f.name,
                    "tamano": f"{tamano_kb} KB",
                    "tamano_bytes": f.stat().st_size,
                })
    return {"ok": True, "datos": {"plantillas": plantillas}}


class ModeloGuardarZona(BaseModel):
    top: float
    bottom: float
    left: float
    right: float


@router.get("/plantillas-word/{nombre_archivo}/analisis")
async def obtener_analisis_plantilla_word(nombre_archivo: str) -> dict:
    """Devuelve el análisis geométrico y zona sugerida de una plantilla de membrete."""
    from motor.membrete import analizar_membrete

    candidato = validar_plantilla_word_segura(nombre_archivo)
    analisis = analizar_membrete(candidato)
    return {"ok": True, "datos": analisis}


@router.post("/plantillas-word/{nombre_archivo}/zona")
async def post_guardar_zona_plantilla_word(nombre_archivo: str, modelo_zona: ModeloGuardarZona) -> dict:
    """Guarda o actualiza el archivo Nombre.zona.json para la plantilla especificada."""
    from motor.membrete import guardar_zona_json

    candidato = validar_plantilla_word_segura(nombre_archivo)
    ruta_json = guardar_zona_json(candidato, modelo_zona.model_dump())
    return {
        "ok": True,
        "datos": {
            "archivo_zona": ruta_json.name,
            "zona": modelo_zona.model_dump(),
        },
    }


@router.get("/temas-word")
async def obtener_temas_word(tema: str = "") -> dict:
    """Lista los temas .docx físicamente presentes en templates/temas_word/ con sus estilos reales."""
    from motor.a_docx import inspeccionar_tema_word, listar_temas_word_disco

    if tema.strip():
        try:
            info = inspeccionar_tema_word(tema.strip())
            return {"ok": True, "datos": info}
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail={"codigo": "TEMA_NO_ENCONTRADO", "detalle": str(exc)},
            )
    return {"ok": True, "datos": {"temas": listar_temas_word_disco()}}


@router.post("/exportar-docx")
async def exportar_docx(modelo: ModeloExportar) -> Response:
    """Convierte Markdown a .docx con el motor completo MarkFlow a_docx o núcleo GenOffice.
    
    Aplica temas formales, paletas suaves de tablas, color de títulos, fuentes, APA 7,
    pie de página y fórmulas de forma fiel al motor clásico.
    """
    nombre = modelo.obtener_nombre().strip() or "documento"
    if not _PATRON_NOMBRE.match(nombre):
        # Sanitizar nombre si contiene caracteres especiales
        nombre = re.sub(r'[^\w\s\.-]', '_', nombre)
        if not nombre.strip():
            nombre = "documento"
    if not nombre.lower().endswith(".docx"):
        nombre += ".docx"

    md_texto = modelo.obtener_markdown()
    if not md_texto.strip():
        raise HTTPException(400, "El documento Markdown está vacío.")

    # Directorio de salidas temporales
    dir_salidas = RAIZ / "storage" / "salidas"
    dir_salidas.mkdir(parents=True, exist_ok=True)
    destino = dir_salidas / nombre

    # Intentar conversión profesional con a_docx (motor canónico completo)
    try:
        from motor.a_docx import ErrorMotor, a_docx
        from motor.sanear import saneanar
        md_saneado, _, _ = saneanar(md_texto)
        a_docx(
            texto=md_saneado,
            destino=destino,
            titulo=nombre.replace(".docx", ""),
            fuente=modelo.fuente or "Calibri",
            tamanio_pt=float(modelo.tamanio_pt or 11.0),
            interlineado=float(modelo.interlineado or 1.0),
            alineacion=modelo.alineacion or "justificado",
            tema_word=modelo.tema_word or "defecto",
            color_titulos_word=modelo.color_titulos_word or "negro",
            normas_apa=bool(modelo.normas_apa),
            paleta_tabla=modelo.paleta_tabla or "defecto",
            numerar_ecuaciones=bool(modelo.numerar_ecuaciones),
            crear_indice=bool(modelo.crear_indice),
            posicion_indice=modelo.posicion_indice or "inicio",
            pie_pagina=modelo.pie_pagina or "",
            alineacion_pie=modelo.alineacion_pie or "derecha",
            numerar_paginas=bool(modelo.numerar_paginas),
            fuente_tabla=modelo.fuente_tabla,
            tamanio_tabla_pt=float(modelo.tamanio_tabla_pt) if modelo.tamanio_tabla_pt else None,
            paleta_suave_tablas=bool(modelo.paleta_suave_tablas),
            color_tabla_cabecera=modelo.color_tabla_cabecera or "",
            color_tabla_filas=modelo.color_tabla_filas or "",
            color_tabla_borde=modelo.color_tabla_borde or "",
            color_tit_h1=modelo.color_tit_h1 or "",
            color_tit_h2=modelo.color_tit_h2 or "",
            modo_color_titulos=modelo.modo_color_titulos or "auto",
        )

        # Si se seleccionó una hoja de membrete, trasplantar el cuerpo a la plantilla byte a byte
        if modelo.plantilla_word and modelo.plantilla_word.strip():
            candidato_plantilla = validar_plantilla_word_segura(modelo.plantilla_word)
            zona_req = None
            if modelo.zona_top is not None or modelo.zona_bottom is not None or modelo.zona_left is not None or modelo.zona_right is not None:
                zona_req = {
                    "top": float(modelo.zona_top) if modelo.zona_top is not None else 2.5,
                    "bottom": float(modelo.zona_bottom) if modelo.zona_bottom is not None else 2.0,
                    "left": float(modelo.zona_left) if modelo.zona_left is not None else 2.5,
                    "right": float(modelo.zona_right) if modelo.zona_right is not None else 2.5,
                }
            from motor.membrete import aplicar_cuerpo_sobre_plantilla
            aplicar_cuerpo_sobre_plantilla(
                ruta_plantilla=candidato_plantilla,
                ruta_contenido_docx=destino,
                ruta_destino=destino,
                zona_cm=zona_req,
                numerar_paginas=bool(modelo.numerar_paginas),
                posicion_numero=modelo.alineacion_pie or "derecha",
            )

        docx_bytes = destino.read_bytes()
    except ErrorMotor as exc_tema:
        if "no encontrado en templates/temas_word" in str(exc_tema):
            raise HTTPException(status_code=404, detail={"codigo": "TEMA_NO_ENCONTRADO", "detalle": str(exc_tema)})
        try:
            plantilla = str(PLANTILLA_BASE) if (modelo.con_plantilla and PLANTILLA_BASE.exists()) else None
            docx_bytes = markdown_to_openxml(md_texto, template_path=plantilla)
            destino.write_bytes(docx_bytes)
        except Exception as exc_fallback:
            raise HTTPException(500, f"Error al generar archivo Word (.docx): {exc_tema} | Fallback: {exc_fallback}")
    except Exception as exc_motor:
        # Fallback al núcleo GenOffice si pandoc o motor no estuviera disponible
        try:
            plantilla = str(PLANTILLA_BASE) if (modelo.con_plantilla and PLANTILLA_BASE.exists()) else None
            docx_bytes = markdown_to_openxml(md_texto, template_path=plantilla)
            destino.write_bytes(docx_bytes)
        except Exception as exc_fallback:
            raise HTTPException(500, f"Error al generar archivo Word (.docx): {exc_motor} | Fallback: {exc_fallback}")

    return Response(
        content=docx_bytes,
        media_type=_MIME_DOCX,
        headers={
            "Content-Disposition": f'attachment; filename="{nombre}"',
            "X-Ruta-Local": str(destino),
        },
    )


# ---------------------------------------------------------------------------
# Exportación Directa HTML (.html autónomo)
# ---------------------------------------------------------------------------
class ModeloExportarHtml(BaseModel):
    markdown: str = ""
    texto: str = ""
    nombre: str = "documento"
    titulo: str = ""
    tema_html: str = "defecto"
    paleta_tricolor: str = "tema_default"
    fuente: str = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
    ancho_maximo: str = "900px"
    justificado: bool = True
    numerar_ecuaciones: bool = False
    footer_izq: str = ""
    footer_der: str = "Ing. Patricio Sarmiento Reinoso, Mgst."


@router.get("/temas-html")
async def obtener_temas_html_disco() -> dict:
    """Devuelve el catálogo de plantillas existentes en `templates/temas_html/`."""
    from motor.a_html import listar_temas_html_disco
    temas = ["defecto"] + listar_temas_html_disco()
    return {"ok": True, "temas": temas, "datos": {"temas": temas}}


@router.post("/exportar-html")
async def exportar_html_directo(modelo: ModeloExportarHtml) -> Response:
    """Compila y descarga el archivo .html de forma directa y optimizada."""
    from motor.a_html import a_html
    from motor.sanear import saneanar

    texto_md = modelo.markdown if modelo.markdown else modelo.texto
    nombre_base = modelo.titulo.strip() or modelo.nombre.strip() or "documento"
    nombre_limpio = re.sub(r'[^\w\s\.-]', '_', nombre_base)
    if not nombre_limpio.strip():
        nombre_limpio = "documento"
    if not nombre_limpio.lower().endswith(".html"):
        nombre_limpio += ".html"

    md_saneado, _, _ = saneanar(texto_md)
    try:
        html_res, _, _ = a_html(
            texto=md_saneado,
            titulo=nombre_base,
            tema_html=modelo.tema_html or "defecto",
            paleta_tricolor=modelo.paleta_tricolor or "tema_default",
            fuente=modelo.fuente or 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
            ancho_maximo=modelo.ancho_maximo or "900px",
            justificado=bool(modelo.justificado),
            numerar_ecuaciones=bool(modelo.numerar_ecuaciones),
            footer_izq=modelo.footer_izq or "",
            footer_der=modelo.footer_der or "Ing. Patricio Sarmiento Reinoso, Mgst.",
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"codigo": "TEMA_HTML_NO_ENCONTRADO", "detalle": str(exc)},
        )

    datos_bytes = html_res.encode("utf-8")
    return Response(
        content=datos_bytes,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_limpio}"',
        },
    )




# ---------------------------------------------------------------------------
# Editor visual Docs: Markdown ↔ JSON ProseMirror + saneamiento
# ---------------------------------------------------------------------------
class ModeloMarkdown(BaseModel):
    texto: str = ""
    markdown: str = ""

    def obtener_texto(self) -> str:
        return self.texto if self.texto != "" else self.markdown


class ModeloDocPM(BaseModel):
    doc: dict


@router.post("/md-a-json")
async def endpoint_md_a_json(modelo: ModeloMarkdown) -> dict:
    """Markdown (SSOT de texto) → documento JSON ProseMirror del editor visual."""
    try:
        return {"ok": True, "datos": {"doc": md_a_doc(modelo.texto)}}
    except Exception as exc:  # markdown-it: malformación extrema del texto
        raise HTTPException(400, f"No se pudo interpretar el Markdown: {exc}") from exc


@router.post("/json-a-md")
async def endpoint_json_a_md(modelo: ModeloDocPM) -> dict:
    """Documento JSON ProseMirror → Markdown (referencia del serializador)."""
    try:
        return {"ok": True, "datos": {"texto": doc_a_md(modelo.doc)}}
    except Exception as exc:
        raise HTTPException(400, f"No se pudo serializar el documento: {exc}") from exc


@router.post("/sanear")
async def endpoint_sanear(modelo: ModeloMarkdown) -> dict:
    """Pipeline canónico de saneamiento del motor (botón 🧹 Sanear de Docs)."""
    from motor.sanear import saneanar  # módulo pesado: import diferido
    texto, formulas, avisos = saneanar(modelo.texto)
    return {"ok": True, "datos": {"texto": texto, "formulas": formulas, "avisos": avisos}}


# ---------------------------------------------------------------------------
# PDF: biblioteca de entregables + servicio del binario (v1.3.0)
# ---------------------------------------------------------------------------
def _tamano_legible(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1024 * 1024:
        return f"{bytes_ / 1024:.1f} KB"
    return f"{bytes_ / (1024 * 1024):.1f} MB"


@router.get("/pdfs")
async def listar_pdfs() -> dict:
    """Inventario de PDFs generados bajo `salidas/` (raíz + sesiones), más recientes primero."""
    raiz = sesiones.DIR_SALIDAS
    inventario: list[dict] = []
    if raiz.is_dir():
        for ruta in raiz.rglob("*.pdf"):
            if not ruta.is_file():
                continue
            rel = ruta.relative_to(raiz)
            est = ruta.stat()
            inventario.append({
                "archivo": ruta.name,
                "ruta": str(rel).replace("\\", "/"),
                "sesion": rel.parts[0] if len(rel.parts) > 1 else "",
                "tamano_bytes": est.st_size,
                "tamano": _tamano_legible(est.st_size),
                "modificado": est.st_mtime,
            })
    inventario.sort(key=lambda item: item["modificado"], reverse=True)
    return {"ok": True, "datos": {"pdfs": inventario}}


@router.get("/pdfs/archivo/{ruta_relativa:path}")
async def servir_pdf(ruta_relativa: str) -> FileResponse:
    """Entrega un PDF de `salidas/` inline para el visor pdf.js (defensa anti-traversal)."""
    if not ruta_relativa.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se sirven archivos .pdf")
    raiz = sesiones.DIR_SALIDAS.resolve()
    destino = (raiz / ruta_relativa).resolve()
    try:
        destino.relative_to(raiz)  # path traversal → ValueError
    except ValueError as exc:
        raise HTTPException(400, "Ruta inválida.") from exc
    if not destino.is_file():
        raise HTTPException(404, "El PDF solicitado no existe.")
    return FileResponse(
        destino,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{destino.name}"'},
    )


@router.delete("/pdfs/archivo/{ruta_relativa:path}")
async def eliminar_pdf(ruta_relativa: str) -> dict:
    """Elimina un archivo PDF de `salidas/` con protección anti path-traversal."""
    if not ruta_relativa.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se pueden eliminar archivos .pdf")
    raiz = sesiones.DIR_SALIDAS.resolve()
    destino = (raiz / ruta_relativa).resolve()
    try:
        destino.relative_to(raiz)
    except ValueError as exc:
        raise HTTPException(400, "Ruta no permitida.") from exc
    if not destino.is_file():
        raise HTTPException(404, "El archivo PDF a eliminar no existe.")
    try:
        destino.unlink()
    except Exception as exc:
        raise HTTPException(500, f"Error eliminando el archivo PDF: {exc}") from exc
    return {"ok": True, "mensaje": f"Archivo '{destino.name}' eliminado con éxito."}


# ---------------------------------------------------------------------------
# Round-trip .docx real: importar a Markdown y reguardar byte-preserving (v1.4.0)
# ---------------------------------------------------------------------------
_MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_FIRMA_ZIP = b"PK\x03\x04"


def _validar_docx(nombre: str, datos: bytes) -> None:
    if not nombre.lower().endswith(".docx"):
        raise HTTPException(400, "Solo se admiten archivos .docx.")
    if not datos.startswith(_FIRMA_ZIP):
        raise HTTPException(400, "El archivo no es un .docx válido (paquete OOXML).")


@router.post("/docx-importar")
async def docx_importar(archivo: UploadFile = File(...)) -> dict:
    """Extrae el cuerpo de un .docx a Markdown (mitad "abrir" del round-trip)."""
    from app.servicios.roundtrip_docx import extraer_md

    datos = await archivo.read()
    _validar_docx(archivo.filename or "", datos)

    import tempfile
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "original.docx"
        ruta.write_bytes(datos)
        try:
            resultado = extraer_md(ruta)
        except Exception as exc:
            raise HTTPException(422, f"No se pudo leer el .docx: {exc}") from exc

    nombre_original = Path(archivo.filename).stem
    return {
        "ok": True,
        "datos": {
            "nombre_sugerido": re.sub(r"[^\w \-.]", "_", nombre_original).strip() or "documento",
            "texto": resultado["texto"],
            "stats": resultado["stats"],
            "avisos": resultado["avisos"],
        },
    }


@router.post("/docx-reguardar")
async def docx_reguardar(archivo: UploadFile = File(...),
                         markdown: str = Form(...)) -> Response:
    """Reguarda el .docx original con el Markdown editado (byte-preserving).

    El cuerpo (`word/document.xml`) se reconstruye desde el Markdown; el resto
    del paquete OOXML (estilos, cabeceras/pies, numeración, medios, rels) se
    conserva byte a byte del archivo subido.
    """
    from app.servicios.roundtrip_docx import reguardar

    datos = await archivo.read()
    _validar_docx(archivo.filename or "", datos)

    import tempfile
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "original.docx"
        ruta.write_bytes(datos)
        try:
            docx_bytes = reguardar(markdown, ruta)
        except Exception as exc:
            raise HTTPException(422, f"El reguardado falló: {exc}") from exc

    nombre_salida = f"{Path(archivo.filename).stem}-editado.docx"
    dir_salidas = RAIZ / "storage" / "salidas"
    dir_salidas.mkdir(parents=True, exist_ok=True)
    destino = dir_salidas / nombre_salida
    try:
        destino.write_bytes(docx_bytes)
    except Exception:
        pass

    return Response(
        content=docx_bytes,
        media_type=_MIME_DOCX,
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_salida}"',
            "X-Ruta-Local": str(destino),
        },
    )


# ---------------------------------------------------------------------------
# Tablas estilo Excel y Compilación Completa Multiformato (v1.12.0)
# ---------------------------------------------------------------------------
def sanitizar_texto_celda(texto: str) -> str:
    r"""Convierte fórmulas LaTeX a texto Unicode matemático legible y limpia marcas Markdown."""
    t = str(texto or "").strip()
    if not t:
        return ""

    # Flechas TeX directas
    t = re.sub(r"\\(?:rightarrow|to)\b", "→", t)
    t = re.sub(r"\\(?:leftarrow|gets)\b", "←", t)
    t = re.sub(r"\\(?:leftrightarrow)\b", "↔", t)
    t = re.sub(r"\\(?:Rightarrow)\b", "⇒", t)
    t = re.sub(r"\\(?:Leftarrow)\b", "⇐", t)
    t = re.sub(r"\\(?:Leftrightarrow)\b", "⇔", t)

    # Si contiene fórmulas matemáticas LaTeX o comandos TeX, traducirlos a Unicode
    if any(m in t for m in (r"\(", r"\[", "$$", "$", r"\frac", r"\text", "_", "^", r"\cdot", "\\")):
        # Extraer y traducir fragmentos matemáticos delimitados
        def _traducir_match(m: re.Match) -> str:
            formula = m.group(1) or m.group(0)
            return latex_a_unicode(formula)

        # Reemplazar fórmulas delimitadas
        t = re.sub(r"\\\[([\s\S]+?)\\\]|\$\$([\s\S]+?)\$\$", _traducir_match, t)
        t = re.sub(r"\\\((.+?)\\\)|\$(?!\s)(.+?)(?<!\s)\$", _traducir_match, t)
        # Si la celda contiene comandos TeX (ej. \cdot, etc.) o subíndices TeX con llaves
        if re.search(r"\\[a-zA-Z]+", t) or re.search(r"[a-zA-Z]_\{[^{}]+\}", t):
            t = latex_a_unicode(t)

    # Mapeo de flechas en notación texto plano
    t = re.sub(r"<-->|<=>", "↔", t)
    t = re.sub(r"-->|->|==>|=>", "→", t)
    t = re.sub(r"<--|<-|<=<", "←", t)

    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"<[^>]+>", "", t)
    return t.strip()


def renderizar_html_celda(texto: str) -> str:
    """Convierte fórmulas LaTeX a spans KaTeX y marcas Markdown a HTML para visualización limpia."""
    import html as html_lib
    t = str(texto or "").strip()
    if not t:
        return ""

    formulas: list[tuple[str, str, bool]] = []

    def _guardar_formula(m: re.Match, es_display: bool) -> str:
        idx = len(formulas)
        cuerpo = m.group(1) or m.group(2) or m.group(0)
        token = f"@@CELDA_EQ_{idx}@@"
        formulas.append((token, (cuerpo or "").strip(), es_display))
        return token

    # Proteger display
    t = re.sub(r"\\\[([\s\S]+?)\\\]|\$\$([\s\S]+?)\$\$", lambda m: _guardar_formula(m, True), t)
    # Proteger inline
    t = re.sub(r"\\\((.+?)\\\)|\$(?!\s)(.+?)(?<!\s)\$", lambda m: _guardar_formula(m, False), t)

    # Escapar HTML y formatear texto
    t = html_lib.escape(t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)

    # Reinsertar fórmulas como elementos KaTeX
    for token, cuerpo, es_disp in formulas:
        cuerpo_esc = html_lib.escape(cuerpo, quote=True)
        clase = "display" if es_disp else "inline"
        t = t.replace(
            token,
            f'<span class="mformula {clase}" data-latex="{cuerpo_esc}"></span>',
        )

    return t


def extraer_tablas_markdown(texto_md: str) -> list[dict]:
    """Extrae las tablas en formato GFM presentes en el Markdown con sanitización."""
    lineas = texto_md.splitlines()
    tablas = []
    tabla_actual = []
    en_tabla = False

    for linea in lineas:
        linea_strip = linea.strip()
        if linea_strip.startswith("|") and linea_strip.endswith("|"):
            tabla_actual.append(linea_strip)
            en_tabla = True
        else:
            if en_tabla and len(tabla_actual) >= 2:
                tablas.append(tabla_actual)
            tabla_actual = []
            en_tabla = False

    if en_tabla and len(tabla_actual) >= 2:
        tablas.append(tabla_actual)

    resultado = []
    for idx, t_lineas in enumerate(tablas, 1):
        if len(t_lineas) < 2:
            continue
        # Cabeceras
        cabeceras = [c.strip() for c in t_lineas[0].strip("|").split("|")]

        # Determinar si la segunda línea es un separador de formato Markdown (ej. |:---|:---:|---:|)
        partes_sep = [p.strip() for p in t_lineas[1].strip("|").split("|")]
        es_separador = all(bool(re.match(r"^:?-+:?$", p)) for p in partes_sep if p)
        lineas_datos = t_lineas[2:] if es_separador else t_lineas[1:]

        filas = []
        for l in lineas_datos:
            cols = [c.strip() for c in l.strip("|").split("|")]
            if len(cols) < len(cabeceras):
                cols.extend([""] * (len(cabeceras) - len(cols)))
            elif len(cols) > len(cabeceras):
                cols = cols[:len(cabeceras)]
            filas.append(cols)

        cabeceras_limpias = [sanitizar_texto_celda(c) for c in cabeceras]
        cabeceras_html = [renderizar_html_celda(c) for c in cabeceras]
        filas_limpias = [[sanitizar_texto_celda(c) for c in f] for f in filas]
        filas_html = [[renderizar_html_celda(c) for c in f] for f in filas]

        resultado.append({
            "id": f"tabla_{idx}",
            "titulo": f"Tabla {idx}",
            "cabeceras": cabeceras,
            "cabeceras_limpias": cabeceras_limpias,
            "cabeceras_html": cabeceras_html,
            "filas": filas,
            "filas_limpias": filas_limpias,
            "filas_html": filas_html,
            "total_filas": len(filas),
            "total_columnas": len(cabeceras),
        })

    return resultado


PALETAS_EXCEL = {
    "clasico": {"cabecera": "107C41", "texto_cab": "FFFFFF", "par": "F4FAF5", "borde": "D1D5DB", "titulo": "107C41"},
    "azul": {"cabecera": "1E3A8A", "texto_cab": "FFFFFF", "par": "F0F4F8", "borde": "CBD5E1", "titulo": "1E3A8A"},
    "gris": {"cabecera": "334155", "texto_cab": "FFFFFF", "par": "F8FAFC", "borde": "E2E8F0", "titulo": "334155"},
    "esmeralda": {"cabecera": "046A38", "texto_cab": "FFFFFF", "par": "F0FDF4", "borde": "D1FAE5", "titulo": "046A38"},
    "monocromo": {"cabecera": "18181B", "texto_cab": "FFFFFF", "par": "FAFAFA", "borde": "E4E4E7", "titulo": "18181B"},
}


def generar_excel_de_tablas(
    tablas: list[dict],
    estilo: str = "clasico",
    modo_hojas: str = "multi_hoja",
    tamano_fuente: int = 10,
    mostrar_gridlines: bool = True,
    autofit: bool = True,
    ancho_col: str = "auto",
    paleta_id: str | None = None,
) -> bytes:
    """Genera un archivo Excel (.xlsx) estilizado a partir de una lista de tablas extraídas.
    
    Soporta paletas predefinidas y personalizadas (c1|c2|c3), modo 'multi_hoja' o 'hoja_unica',
    control de cuadrícula visible (showGridLines) y autoajuste inteligente vs ancho fijo.
    """
    import io
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    clave_estilo = str(paleta_id or estilo or "clasico").strip()

    # Detección de Paleta Personalizada (ej: #1E3A8A|#3B82F6|#F0F4F8|#FFFFFF|#CBD5E1 o similar)
    if "|" in clave_estilo or clave_estilo.startswith("#"):
        partes = [p.strip().lstrip("#").upper() for p in clave_estilo.split("|")]
        c_cab = partes[0] if len(partes) > 0 and partes[0] else "107C41"
        c_tit = partes[1] if len(partes) > 1 and partes[1] else c_cab
        c_par = partes[2] if len(partes) > 2 and partes[2] else "F4FAF5"
        if len(partes) > 3 and partes[3]:
            txt_cab = partes[3]
        else:
            try:
                r, g, b = int(c_cab[0:2], 16), int(c_cab[2:4], 16), int(c_cab[4:6], 16)
                txt_cab = "FFFFFF" if (r * 0.299 + g * 0.587 + b * 0.114 < 145) else "1E293B"
            except Exception:
                txt_cab = "FFFFFF"
        c_bor = partes[4] if len(partes) > 4 and partes[4] else "CBD5E1"
        pal = {"cabecera": c_cab, "texto_cab": txt_cab, "par": c_par, "borde": c_bor, "titulo": c_tit}
    else:
        pal = PALETAS_EXCEL.get(clave_estilo.lower(), PALETAS_EXCEL["clasico"])

    fill_cabecera = PatternFill(start_color=pal["cabecera"], end_color=pal["cabecera"], fill_type="solid")
    font_cabecera = Font(name="Calibri", size=tamano_fuente + 1, bold=True, color=pal["texto_cab"])
    font_celda = Font(name="Calibri", size=tamano_fuente)
    fill_par = PatternFill(start_color=pal["par"], end_color=pal["par"], fill_type="solid")
    borde_fino = Border(
        left=Side(style="thin", color=pal["borde"]),
        right=Side(style="thin", color=pal["borde"]),
        top=Side(style="thin", color=pal["borde"]),
        bottom=Side(style="thin", color=pal["borde"]),
    )

    es_hoja_unica = (modo_hojas == "hoja_unica")
    ws_unica = None
    fila_actual = 1

    def _configurar_vista_hoja(hoja):
        # Asignación dual para máxima compatibilidad con visor de Excel nativo y LibreOffice
        hoja.sheet_view.showGridLines = bool(mostrar_gridlines)
        if hasattr(hoja, "views") and hasattr(hoja.views, "sheetView") and hoja.views.sheetView:
            for v in hoja.views.sheetView:
                v.showGridLines = bool(mostrar_gridlines)

    def _aplicar_anchos(hoja):
        ancho_fijo = 15
        if ancho_col == "compacto":
            ancho_fijo = 12
        elif ancho_col == "comodo":
            ancho_fijo = 20
        elif ancho_col == "amplio":
            ancho_fijo = 28

        for col in hoja.columns:
            col_letra = get_column_letter(col[0].column)
            if not autofit:
                hoja.column_dimensions[col_letra].width = ancho_fijo
            else:
                longitud_max = 0
                for cell in col:
                    # Ignorar celda de título en fila 1 para no sobredimensionar la columna A
                    if cell.row == 1 and cell.column == 1:
                        continue
                    val_str = str(cell.value or "").strip()
                    if "\n" in val_str:
                        sub_lens = [len(l) for l in val_str.split("\n")]
                        l_val = max(sub_lens) if sub_lens else 0
                    else:
                        l_val = len(val_str)
                    if l_val > longitud_max:
                        longitud_max = l_val
                hoja.column_dimensions[col_letra].width = max(min(longitud_max + 4, 60), 10)

    if es_hoja_unica:
        ws_unica = wb.create_sheet(title="Tablas")
        _configurar_vista_hoja(ws_unica)

    for i, t in enumerate(tablas, 1):
        if es_hoja_unica:
            ws = ws_unica
            fila_inicio = fila_actual
        else:
            nombre_hoja = f"Tabla_{i}"
            ws = wb.create_sheet(title=nombre_hoja[:31])
            _configurar_vista_hoja(ws)
            fila_inicio = 1

        # Título de la tabla
        ws.cell(row=fila_inicio, column=1, value=sanitizar_texto_celda(t.get("titulo", f"Tabla {i}"))).font = Font(
            name="Calibri", size=tamano_fuente + 3, bold=True, color=pal["titulo"]
        )
        ws.row_dimensions[fila_inicio].height = 24

        fila_cabecera = fila_inicio + 2
        cabeceras = t.get("cabeceras_limpias") or [sanitizar_texto_celda(c) for c in t.get("cabeceras", [])]
        for c_idx, c_val in enumerate(cabeceras, 1):
            celda = ws.cell(row=fila_cabecera, column=c_idx, value=c_val)
            celda.fill = fill_cabecera
            celda.font = font_cabecera
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            celda.border = borde_fino
        ws.row_dimensions[fila_cabecera].height = 22

        filas = t.get("filas_limpias") or [[sanitizar_texto_celda(c) for c in f] for f in t.get("filas", [])]
        fila_datos = fila_cabecera + 1
        for r_idx, f in enumerate(filas, fila_datos):
            ws.row_dimensions[r_idx].height = 18
            es_par = (r_idx % 2 == 0)
            for c_idx, val in enumerate(f, 1):
                val_limpio = str(val).strip()
                val_final = val_limpio
                try:
                    if re.match(r"^-?\d+(\.\d+)?$", val_limpio):
                        val_final = float(val_limpio) if "." in val_limpio else int(val_limpio)
                except Exception:
                    pass
                celda = ws.cell(row=r_idx, column=c_idx, value=val_final)
                celda.font = font_celda
                celda.border = borde_fino
                if es_par:
                    celda.fill = fill_par
                if isinstance(val_final, (int, float)):
                    celda.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    celda.alignment = Alignment(horizontal="left", vertical="center")

        if es_hoja_unica:
            fila_actual = fila_datos + len(filas) + 2
        else:
            _aplicar_anchos(ws)

    if es_hoja_unica and ws_unica:
        _aplicar_anchos(ws_unica)

    if not wb.sheetnames:
        ws = wb.create_sheet("Tablas")
        _configurar_vista_hoja(ws)
        ws.cell(row=1, column=1, value="No se detectaron tablas en el documento.")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@router.post("/extraer-tablas")
async def endpoint_extraer_tablas(modelo: ModeloMarkdown) -> dict:
    """Extrae las tablas del Markdown para renderizar en la vista tipo hoja de cálculo."""
    texto = modelo.obtener_texto()
    tablas = extraer_tablas_markdown(texto)
    return {
        "ok": True,
        "conteo": len(tablas),
        "tablas": tablas,
        "datos": {"total": len(tablas), "tablas": tablas},
    }


@router.post("/exportar-tablas-excel")
async def endpoint_exportar_tablas_excel(modelo: ModeloExportar) -> Response:
    """Genera un archivo Excel .xlsx con todas las tablas detectadas en el Markdown."""
    tablas = extraer_tablas_markdown(modelo.obtener_markdown())
    excel_bytes = generar_excel_de_tablas(
        tablas,
        estilo=modelo.estilo_excel,
        modo_hojas=modelo.modo_hojas,
        tamano_fuente=modelo.tamano_fuente,
        mostrar_gridlines=modelo.mostrar_gridlines,
        autofit=modelo.autofit,
        ancho_col=modelo.ancho_col,
        paleta_id=modelo.paleta_id or modelo.estilo_excel,
    )
    nombre = modelo.obtener_nombre()
    if not nombre.lower().endswith(".xlsx"):
        nombre += ".xlsx"

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


class ModeloExportarPdf(BaseModel):
    nombre: str = "documento"
    markdown: str = ""
    tema_pdf: str = "pizarra_carbon"
    estilo_maquetacion: str = "informe"
    modo_columnas: str = "estandar"
    fuente: str = "Calibri"
    tamanio_pt: float = 11.0
    interlineado: float = 1.15
    justificado: bool = True
    pie_pagina: str = ""
    salto_capitulo: bool = True
    running_header: bool = True
    numerar_paginas: bool = True
    indice_al_final: bool = True
    # Soporte para Hoja de Membrete PDF
    plantilla_word: str = ""
    zona_top: float | None = None
    zona_bottom: float | None = None
    zona_left: float | None = None
    zona_right: float | None = None
    alineacion_num: str = "derecha"
    posicion_numero: str = "derecha"
    # Portada premium configurable
    portada_premium: dict | None = None

@router.post("/exportar-pdf")
async def endpoint_exportar_pdf(modelo: ModeloExportarPdf) -> Response:
    """Compila el Markdown a PDF con las opciones de la barra lateral y retorna application/pdf."""
    import tempfile
    from motor.a_pdf import a_pdf
    from motor.sanear import saneanar

    md_saneado, _, _ = saneanar(modelo.markdown)
    nombre_limpio = (modelo.nombre.strip() or "documento").replace(".pdf", "")

    # Validar hoja de membrete si fue especificada
    candidato_plantilla = None
    zona_req = None
    if modelo.plantilla_word and modelo.plantilla_word.strip():
        candidato_plantilla = validar_plantilla_word_segura(modelo.plantilla_word)
        if (
            modelo.zona_top is not None
            or modelo.zona_bottom is not None
            or modelo.zona_left is not None
            or modelo.zona_right is not None
        ):
            zona_req = {
                "top": float(modelo.zona_top) if modelo.zona_top is not None else 2.5,
                "bottom": float(modelo.zona_bottom) if modelo.zona_bottom is not None else 2.0,
                "left": float(modelo.zona_left) if modelo.zona_left is not None else 2.5,
                "right": float(modelo.zona_right) if modelo.zona_right is not None else 2.5,
            }

    pos_num = modelo.posicion_numero or modelo.alineacion_num or "derecha"

    with tempfile.TemporaryDirectory() as tmp_dir:
        destino = Path(tmp_dir) / f"{nombre_limpio}.pdf"
        try:
            ruta_res, _, _ = a_pdf(
                texto=md_saneado,
                destino=destino,
                titulo=nombre_limpio,
                tema_pdf=modelo.tema_pdf,
                fuente=modelo.fuente,
                interlineado=modelo.interlineado,
                estilo_maquetacion=modelo.estilo_maquetacion,
                pie_pagina=modelo.pie_pagina,
                numerar_paginas=modelo.numerar_paginas,
                running_header=modelo.running_header,
                salto_capitulo=modelo.salto_capitulo,
                modo_diseno=modelo.modo_columnas,
                indice_al_final=modelo.indice_al_final,
                plantilla_word=candidato_plantilla,
                zona_cm=zona_req,
                alineacion_num=pos_num,
                portada_premium=modelo.portada_premium,
                tamanio_pt=modelo.tamanio_pt,
                justificado=modelo.justificado,
            )
            pdf_bytes = ruta_res.read_bytes()
        except Exception as exc:
            raise HTTPException(500, f"Error al generar PDF: {exc}") from exc

    # Guardar copia local en el almacén de salidas
    dir_salidas = RAIZ / "storage" / "salidas"
    dir_salidas.mkdir(parents=True, exist_ok=True)
    copia_salida = dir_salidas / f"{nombre_limpio}.pdf"
    try:
        copia_salida.write_bytes(pdf_bytes)
    except Exception:
        pass

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_limpio}.pdf"',
        },
    )


class ModeloCompilacionCompleta(BaseModel):
    nombre: str = "documento"
    titulo: str = ""
    markdown: str = ""
    formatos: list[str] = ["word", "pdf", "html"]
    paleta: str = "editorial"
    paleta_word: str = ""
    paleta_tricolor: str = ""
    tema_html: str = "defecto"
    tema_word: str = "consultor_moderno"
    tema_pdf: str = "informe_tecnico"
    fuente_word: str = "Calibri"
    tamano_fuente_word: int = 11
    interlineado_word: float = 1.15
    margen_word: str = "normal"
    orientacion_word: str = "vertical"
    portada_word: bool = True
    indice_word: bool = True
    salto_capitulo: bool = True
    running_header: bool = True
    indice_al_final: bool = True
    dos_columnas: bool = False
    firmas_tecnicas: bool = False
    orientacion_pdf: str = "vertical"
    tamano_pagina_pdf: str = "a4"
    sidebar_navegacion: bool = True
    resaltado_codigo: bool = True
    render_formulas: bool = True
    diagramas_mermaid: bool = True
    generar_excel: bool = False
    estilo_excel: str = "clasico"


@router.post("/compilar-completo")
async def compilar_completo(modelo: ModeloCompilacionCompleta) -> dict:
    """Compila el documento activo a múltiples formatos con opciones avanzadas."""
    from motor.a_html import a_html
    from motor.a_docx import a_docx
    from motor.a_pdf import a_pdf
    from motor.sanear import saneanar
    from app.rutas.plantillas import slug_archivo

    md_saneado, _, avisos_sanear = saneanar(modelo.markdown)
    nombre_base = modelo.titulo.strip() or modelo.nombre.strip() or "documento"
    slug_doc = slug_archivo(nombre_base) or "documento"

    sesion = sesiones.crear_sesion()
    carpeta_sesion = sesiones._carpeta(sesion)
    entregables = []
    avisos_totales = list(avisos_sanear)

    formatos_a_procesar = list(modelo.formatos)
    if modelo.generar_excel and "excel" not in formatos_a_procesar and "xlsx" not in formatos_a_procesar:
        formatos_a_procesar.append("excel")

    # 1. Word (.docx)
    if "word" in formatos_a_procesar or "docx" in formatos_a_procesar:
        nombre_arch = f"{slug_doc}.docx"
        ruta_salida = carpeta_sesion / nombre_arch
        try:
            ruta_res, _, avisos_w = a_docx(
                md_saneado,
                destino=ruta_salida,
                tema_word=modelo.tema_word,
                color_titulos_word=modelo.paleta_word or "negro",
                fuente=modelo.fuente_word,
                interlineado=modelo.interlineado_word,
                titulo=nombre_base
            )
            avisos_totales.extend(avisos_w)
            tam = f"{max(1, ruta_salida.stat().st_size // 1024)} KB" if ruta_salida.exists() else "—"
            entregables.append({
                "formato": "word",
                "archivo": nombre_arch,
                "url": f"/api/descargar/{sesion}/{nombre_arch}",
                "tamano": tam,
                "subtitulo": "Documento Microsoft Word con estilos y tablas"
            })
        except Exception as exc:
            avisos_totales.append(f"Error generando Word: {exc}")

    # 2. PDF (.pdf)
    if "pdf" in formatos_a_procesar:
        nombre_arch = f"{slug_doc}.pdf"
        ruta_salida = carpeta_sesion / nombre_arch
        try:
            ruta_res, _, avisos_p = a_pdf(
                md_saneado,
                destino=ruta_salida,
                tema_pdf=modelo.tema_pdf,
                salto_capitulo=modelo.salto_capitulo,
                running_header=modelo.running_header,
                indice_al_final=modelo.indice_al_final,
                titulo=nombre_base
            )
            avisos_totales.extend(avisos_p)
            tam = f"{max(1, ruta_salida.stat().st_size // 1024)} KB" if ruta_salida.exists() else "—"
            entregables.append({
                "formato": "pdf",
                "archivo": nombre_arch,
                "url": f"/api/descargar/{sesion}/{nombre_arch}",
                "tamano": tam,
                "subtitulo": "Documento PDF maquetado con CSS Paged Media"
            })
        except Exception as exc:
            avisos_totales.append(f"Error generando PDF: {exc}")

    # 3. HTML (.html)
    if "html" in formatos_a_procesar:
        nombre_arch = f"{slug_doc}.html"
        try:
            html_res, _, avisos_h = a_html(
                md_saneado,
                titulo=nombre_base,
                tema_html=modelo.tema_html,
                paleta_tricolor=modelo.paleta_tricolor or None
            )
            datos_bytes = html_res.encode("utf-8")
            sesiones.guardar(sesion, nombre_arch, datos_bytes)
            avisos_totales.extend(avisos_h)
            entregables.append({
                "formato": "html",
                "archivo": nombre_arch,
                "url": f"/api/descargar/{sesion}/{nombre_arch}",
                "tamano": f"{max(1, len(datos_bytes) // 1024)} KB",
                "subtitulo": "Página HTML interactiva con sidebar y temas",
                "permiteVer": True
            })
        except Exception as exc:
            avisos_totales.append(f"Error generando HTML: {exc}")

    # 4. Excel (.xlsx)
    if "excel" in formatos_a_procesar or "xlsx" in formatos_a_procesar:
        tablas = extraer_tablas_markdown(md_saneado)
        if tablas:
            excel_bytes = generar_excel_de_tablas(tablas, estilo=modelo.estilo_excel)
            nombre_arch = f"{slug_doc}_tablas.xlsx"
            sesiones.guardar(sesion, nombre_arch, excel_bytes)
            entregables.append({
                "formato": "xlsx",
                "archivo": nombre_arch,
                "url": f"/api/descargar/{sesion}/{nombre_arch}",
                "tamano": f"{max(1, len(excel_bytes) // 1024)} KB",
                "subtitulo": f"{len(tablas)} tablas extraídas en hojas de cálculo"
            })

    # 5. Markdown (.md saneado)
    if "markdown" in formatos_a_procesar or "md" in formatos_a_procesar:
        nombre_arch = f"{slug_doc}.md"
        datos_bytes = md_saneado.encode("utf-8")
        sesiones.guardar(sesion, nombre_arch, datos_bytes)
        entregables.append({
            "formato": "markdown",
            "archivo": nombre_arch,
            "url": f"/api/descargar/{sesion}/{nombre_arch}",
            "tamano": f"{max(1, len(datos_bytes) // 1024)} KB",
            "subtitulo": "Markdown limpio y saneado con pipeline del motor"
        })

    rutas_map = {item["formato"]: item["url"] for item in entregables}
    if "word" in rutas_map:
        rutas_map["docx"] = rutas_map["word"]
    if "docx" in rutas_map:
        rutas_map["word"] = rutas_map["docx"]
    if "xlsx" in rutas_map:
        rutas_map["excel"] = rutas_map["xlsx"]
    if "markdown" in rutas_map:
        rutas_map["md"] = rutas_map["markdown"]

    return {
        "ok": True,
        "rutas": rutas_map,
        "datos": {
            "sesion": sesion,
            "total_generados": len(entregables),
            "entregables": entregables,
            "avisos": avisos_totales
        }
    }


# ---------------------------------------------------------------------------
# Validación de Fórmulas Matemáticas (Fase 2)
# ---------------------------------------------------------------------------
class EntradaValidarFormulas(BaseModel):
    markdown: str


@router.post("/validar-formulas")
def validar_formulas_api(datos: EntradaValidarFormulas) -> dict:
    """Extrae las fórmulas del documento Markdown y valida su sintaxis LaTeX reportando errores y líneas."""
    from motor.formulas import extraer_y_proteger_formulas, validar_formulas_documento

    texto_md = datos.markdown or ""
    _, formulas = extraer_y_proteger_formulas(texto_md)
    resumen = validar_formulas_documento(formulas, texto_completo=texto_md)

    return {
        "ok": True,
        "resumen": resumen
    }

