"""Router de la API de MarkFlow AI.

Todas las respuestas usan el sobre estándar:
    {"ok": bool, "datos": {...} | null, "errores": [{"codigo", "detalle"}]}
y los errores HTTP van tipados ({codigo, detalle}) sin excepciones crudas.
"""

from __future__ import annotations

import html as _html
import os
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.servicios import sesiones
from app.version import APP_NOMBRE, APP_VERSION
from motor import qa
from motor.a_docx import PALETAS_TABLA, ErrorMotor, a_docx, ruta_pandoc
from motor.a_html import PALETAS_HTML, PALETAS_TRICOLOR, a_html, copiar_activos_katex
from motor.a_pdf import PALETAS_EDITORIAL_PDF, ErrorMotorPDF, a_pdf
from motor.capitulos import consolidar_documentos
from motor.extraer import ErrorMotor as ErrorExtraccion
from motor.extraer import docx_a_markdown
from motor.ingesta import (
    MAXIMO_BYTES,
    clasificar_tipo,
    leer_ingesta,
)
from motor.reverse_converter import (
    ErrorConversionInversa,
    convertir_docx_a_markdown,
    convertir_pdf_a_markdown,
)
from motor.sanear import saneanar

router = APIRouter(prefix="/api")

_DIR_TEMAS_HTML = Path(__file__).resolve().parents[2] / "templates" / "temas_html"
_DIR_TEMAS_WORD = Path(__file__).resolve().parents[2] / "templates" / "temas_word"


def _sobre(datos=None, ok: bool = True, errores: list[dict] | None = None) -> dict:
    """Sobre de respuesta homologado para toda la API."""
    return {"ok": ok, "datos": datos, "errores": errores or []}


def _fallo(codigo: str, detalle: str, estado: int) -> HTTPException:
    return HTTPException(
        status_code=estado, detail={"codigo": codigo, "detalle": detalle}
    )


# ---------------------------------------------------------------------------
#  GET /api/version
# ---------------------------------------------------------------------------
@router.get("/version")
async def version() -> dict:
    """Versión leída del SSOT (`app/version.py`) — sin hardcodeo."""
    return _sobre(datos={"version": APP_VERSION, "nombre": APP_NOMBRE})


# ---------------------------------------------------------------------------
#  GET /api/temas
# ---------------------------------------------------------------------------
@router.get("/temas")
async def listar_temas() -> dict:
    """Devuelve las plantillas HTML y Word disponibles, junto con las paletas suaves y tri-color."""
    temas_html = ["defecto"]
    if _DIR_TEMAS_HTML.is_dir():
        for f in sorted(_DIR_TEMAS_HTML.glob("*.html")):
            temas_html.append(f.stem)

    temas_word = ["defecto"]
    if _DIR_TEMAS_WORD.is_dir():
        for f in sorted(_DIR_TEMAS_WORD.glob("*.docx")):
            temas_word.append(f.stem)
    if "personalizado" not in temas_word:
        temas_word.append("personalizado")

    paletas = [
        {"clave": k, "nombre": v["nombre"], "header_bg": v["header_bg"], "border": v["border"]}
        for k, v in PALETAS_TABLA.items()
    ]

    paletas_tricolor = [
        {
            "clave": k,
            "nombre": v["nombre"],
            "primario": v["primario"],
            "secundario": v["secundario"],
            "fondo_suave": v.get("fondo_suave", ""),
        }
        for k, v in PALETAS_TRICOLOR.items()
    ]

    paletas_pdf = [
        {
            "clave": k,
            "nombre": v["nombre"],
            "primario": v["primario"],
            "secundario": v["secundario"],
            "fondo_suave": v.get("fondo_suave", ""),
        }
        for k, v in PALETAS_EDITORIAL_PDF.items()
    ]

    return _sobre(datos={
        "temas_html": temas_html,
        "temas_word": temas_word,
        "paletas": paletas,
        "paletas_tricolor": paletas_tricolor,
        "paletas_pdf": paletas_pdf,
    })


# ---------------------------------------------------------------------------
#  GET /api/registro-opciones (v1.13.0)
# ---------------------------------------------------------------------------
@router.get("/registro-opciones")
async def endpoint_registro_opciones() -> dict:
    """Devuelve el árbol completo del registro único de opciones para HTML, Word, PDF y Excel."""
    from motor.registro_opciones import obtener_registro_completo
    return _sobre(datos=obtener_registro_completo())


# ---------------------------------------------------------------------------
#  POST /api/abrir-carpeta
# ---------------------------------------------------------------------------
@router.post("/abrir-carpeta")
async def abrir_carpeta(request: Request) -> dict:
    """Abre un directorio en el explorador de Windows de manera segura."""
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "Cuerpo JSON inválido.", 400)

    ruta_str = str(cuerpo.get("ruta", "")).strip() if isinstance(cuerpo, dict) else ""
    if not ruta_str:
        # Abrir carpeta salidas por defecto
        ruta = sesiones.DIR_SALIDAS.resolve()
    else:
        ruta = Path(ruta_str).resolve()

    if not ruta.exists():
        try:
            ruta.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise _fallo("RUTA_INVALIDA", f"No se pudo crear o acceder a la ruta: {exc}", 400)

    try:
        if os.name == "nt":
            os.startfile(str(ruta))
        else:
            subprocess.Popen(["xdg-open", str(ruta)])
    except Exception as exc:
        raise _fallo("ERROR_ABRIR", f"No se pudo abrir el explorador: {exc}", 500)

    return _sobre(datos={"abierta": str(ruta)})


# ---------------------------------------------------------------------------
#  POST /api/ingesta
# ---------------------------------------------------------------------------
def _es_archivo(valor: object) -> bool:
    return hasattr(valor, "filename") and hasattr(valor, "read")


async def _leer_formulario(request: Request) -> tuple[list[UploadFile], str]:
    tipo_contenido = request.headers.get("content-type", "").lower()

    if tipo_contenido.startswith("multipart/form-data"):
        formulario = await request.form()
        archivos = [v for v in formulario.getlist("archivos") if _es_archivo(v)]
        texto = formulario.get("texto") or ""
        return archivos, str(texto)

    if tipo_contenido.startswith("application/json"):
        try:
            cuerpo = await request.json()
        except Exception:
            raise _fallo("JSON_INVALIDO", "El cuerpo JSON no se pudo interpretar.", 400)
        if not isinstance(cuerpo, dict):
            raise _fallo("JSON_INVALIDO", "Se esperaba un objeto JSON.", 400)
        return [], str(cuerpo.get("texto", ""))

    raise _fallo(
        "TIPO_CONTENIDO_NO_SOPORTADO",
        "Usa multipart/form-data (archivos) o application/json (texto pegado).",
        415,
    )


@router.post("/ingesta")
async def ingesta(request: Request) -> dict:
    """Ingesta de documentos (hasta 200 MB por archivo)."""
    archivos, texto = await _leer_formulario(request)
    if not archivos and not texto.strip():
        raise _fallo(
            "ENTRADA_VACIA",
            "Envía al menos un archivo en 'archivos' o texto en 'texto'.",
            400,
        )

    sesion = sesiones.crear_sesion()
    documentos: list[dict] = []
    textos_para_consolidar: list[tuple[str, str]] = []

    for subido in archivos:
        nombre_bruto = subido.filename or "entrada.md"
        tipo = clasificar_tipo(nombre_bruto)
        if tipo is None:
            raise _fallo(
                "TIPO_NO_SOPORTADO",
                f"Extensión no aceptada en '{nombre_bruto}'. "
                "Formatos válidos: .md .txt .docx .pdf",
                415,
            )
        dato = await subido.read()
        if len(dato) > MAXIMO_BYTES:
            raise _fallo(
                "TAMANO_EXCEDIDO",
                f"'{nombre_bruto}' supera el límite de 200 MB por archivo.",
                400,
            )
        destino = Path(str(sesiones.guardar(sesion, nombre_bruto, dato)))
        if tipo == "texto":
            texto_doc, info = leer_ingesta(dato, nombre=nombre_bruto)
            sesiones.guardar(sesion, f"{destino.stem}-texto.md", texto_doc.encode("utf-8"))
            textos_para_consolidar.append((nombre_bruto, texto_doc))
            documentos.append({
                "nombre": nombre_bruto,
                "codificacion": info.codificacion,
                "con_bom": info.con_bom,
                "mojibake_reparado": info.mojibake_reparado,
                "tamano_bytes": info.tamano_bytes,
                "avisos": info.avisos,
            })
        else:
            sufijo = Path(nombre_bruto).suffix.lower()
            if sufijo == ".docx" and ruta_pandoc() is not None:
                try:
                    texto_doc, avisos_doc = docx_a_markdown(dato)
                    sesiones.guardar(
                        sesion, f"{destino.stem}-texto.md", texto_doc.encode("utf-8")
                    )
                    textos_para_consolidar.append((nombre_bruto, texto_doc))
                    documentos.append({
                        "nombre": nombre_bruto,
                        "codificacion": "docx -> markdown (pandoc)",
                        "con_bom": False,
                        "mojibake_reparado": False,
                        "tamano_bytes": len(dato),
                        "avisos": avisos_doc,
                    })
                except ErrorExtraccion as exc:
                    documentos.append({
                        "nombre": nombre_bruto,
                        "codificacion": "docx (falla la extracción)",
                        "con_bom": False,
                        "mojibake_reparado": False,
                        "tamano_bytes": len(dato),
                        "avisos": [str(exc)],
                    })
            elif sufijo == ".pdf":
                documentos.append({
                    "nombre": nombre_bruto,
                    "codificacion": "pdf (binario en cola)",
                    "con_bom": False,
                    "mojibake_reparado": False,
                    "tamano_bytes": len(dato),
                    "avisos": [
                        "PDF registrado en la sesión: pega su texto en el editor "
                        "mientras llega la extracción nativa."
                    ],
                })
            else:
                documentos.append({
                    "nombre": nombre_bruto,
                    "codificacion": "binario (sin decodificar)",
                    "con_bom": False,
                    "mojibake_reparado": False,
                    "tamano_bytes": len(dato),
                    "avisos": ["Documento binario registrado."],
                })

    if texto.strip():
        texto_doc, info = leer_ingesta(texto.encode("utf-8"), nombre="pegado.md")
        sesiones.guardar(sesion, "pegado.md", texto_doc.encode("utf-8"))
        textos_para_consolidar.append(("pegado.md", texto_doc))
        documentos.append({
            "nombre": "pegado.md",
            "codificacion": "utf-8 (origen: texto pegado)",
            "con_bom": False,
            "mojibake_reparado": False,
            "tamano_bytes": len(texto.encode("utf-8")),
            "avisos": info.avisos,
        })

    # Lógica de nombre inteligente:
    if len(documentos) == 1:
        nombre_sugerido = Path(documentos[0]["nombre"]).stem
    elif len(documentos) > 1:
        nombre_sugerido = "Documento_consolidado"
    else:
        nombre_sugerido = "Documento"

    # Texto consolidado inicial (por defecto capítulos continuos si son varios)
    texto_combinado = consolidar_documentos(
        textos_para_consolidar,
        modo_capitulos=True if len(textos_para_consolidar) > 1 else False,
        salto_entre_archivos=True,
    )

    return _sobre(datos={
        "sesion": sesion,
        "documentos": documentos,
        "nombre_sugerido": nombre_sugerido,
        "texto_combinado": texto_combinado,
    })


# ---------------------------------------------------------------------------
#  POST /api/consolidar
# ---------------------------------------------------------------------------
@router.post("/consolidar")
async def consolidar(request: Request) -> dict:
    """Re-consolida una lista de documentos con opciones de capítulos continuos."""
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "Cuerpo JSON no interpretable.", 400)

    documentos = cuerpo.get("documentos") or []
    modo_capitulos = bool(cuerpo.get("modo_capitulos", True))
    salto_entre_archivos = bool(cuerpo.get("salto_entre_archivos", True))

    lista_docs = [(d.get("nombre", f"doc_{i}"), d.get("texto", "")) for i, d in enumerate(documentos, 1)]
    texto_resultante = consolidar_documentos(
        lista_docs,
        modo_capitulos=modo_capitulos,
        salto_entre_archivos=salto_entre_archivos,
    )

    return _sobre(datos={"texto": texto_resultante})


# ---------------------------------------------------------------------------
#  POST /api/sesion/purgar
# ---------------------------------------------------------------------------
@router.post("/sesion/purgar")
async def purgar_sesion(request: Request) -> dict:
    """Purga sesiones temporales del servidor."""
    try:
        cuerpo = await request.json()
    except Exception:
        cuerpo = {}

    identificador = str(cuerpo.get("sesion", "")).strip() if isinstance(cuerpo, dict) else ""
    if identificador:
        try:
            n = sesiones.limpiar_sesion(identificador)
        except ValueError as exc:
            raise _fallo("SESION_INVALIDA", str(exc), 400)
        if n == 0:
            raise _fallo("SESION_INEXISTENTE", "La sesión no existe o ya fue purgada.", 400)
        return _sobre(datos={"purgada": identificador, "eliminados": n})

    return _sobre(datos={"purgadas": sesiones.limpiar_todo() - 0, "alcance": "todas"})


# ---------------------------------------------------------------------------
#  POST /api/formatear
# ---------------------------------------------------------------------------
@router.post("/formatear")
async def formatear(request: Request) -> dict:
    """Sanea el texto Markdown y audita calidad."""
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "El cuerpo JSON no se pudo interpretar.", 400)
    texto = str(cuerpo.get("texto", "")) if isinstance(cuerpo, dict) else ""
    if not texto.strip():
        raise _fallo("ENTRADA_VACIA", "Envía el texto Markdown en 'texto'.", 400)

    salida, formulas, avisos = saneanar(texto)
    control = qa.auditar(salida, formulas)
    return _sobre(datos={
        "texto": salida,
        "formulas": formulas,
        "qa": control,
        "avisos": avisos,
    })


# ---------------------------------------------------------------------------
#  POST /api/transformar
# ---------------------------------------------------------------------------
_FORMATOS = {"md", "html", "docx", "pdf"}


def _cuerpos_formulas(texto: str) -> list[str]:
    limpio = re.sub(r"```[\s\S]*?(?:```|\Z)|`[^`\n]*`", " ", texto)
    en_linea = re.findall(r"\\\((.+?)\\\)", limpio, re.S)
    en_display = re.findall(r"\\\[(.+?)\\\]", limpio, re.S)
    return [_html.unescape(t.strip()) for t in (*en_linea, *en_display)]


def _cuerpos_html(documento: str) -> list[str]:
    return [_html.unescape(t) for t in re.findall(r'data-latex="([^"]*)"', documento)]


@router.post("/transformar")
async def transformar(request: Request) -> dict:
    """Genera entregables enriquecidos (MD / HTML / DOCX / PDF) con opciones de formato."""
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "El cuerpo JSON no se pudo interpretar.", 400)
    if not isinstance(cuerpo, dict) or not str(cuerpo.get("texto", "")).strip():
        raise _fallo("ENTRADA_VACIA", "Envía el texto Markdown en 'texto'.", 400)

    texto = str(cuerpo.get("texto", ""))
    titulo = str(cuerpo.get("titulo", "Documento")).strip() or "Documento"
    pedidos = [str(f).lower() for f in (cuerpo.get("formatos") or ["html"])]
    validos = [f for f in pedidos if f in _FORMATOS]
    if not validos:
        raise _fallo("FORMATO_INVALIDO", "Formatos válidos: 'md', 'html', 'docx', 'pdf'.", 400)

    # Parámetros avanzados
    fuente = str(cuerpo.get("fuente", "Calibri"))
    tamanio_pt = float(cuerpo.get("tamanio_pt", 11.0))
    interlineado = float(cuerpo.get("interlineado", 1.0))
    alineacion = str(cuerpo.get("alineacion", "justificado"))
    normas_apa = bool(cuerpo.get("normas_apa", False))
    numerar_ecuaciones = bool(cuerpo.get("numerar_ecuaciones", False))
    crear_indice = bool(cuerpo.get("crear_indice", False))
    posicion_indice = str(cuerpo.get("posicion_indice", "inicio")).lower()
    pie_pagina = str(cuerpo.get("pie_pagina", ""))
    alineacion_pie = str(cuerpo.get("alineacion_pie", "derecha")).lower()
    numerar_paginas = bool(cuerpo.get("numerar_paginas", False))
    tema_word = str(cuerpo.get("tema_word", "defecto"))
    color_titulos_word = str(cuerpo.get("color_titulos_word", "negro")).lower()
    fuente_tabla_raw = str(cuerpo.get("fuente_tabla", "")).strip()
    fuente_tabla = fuente_tabla_raw if fuente_tabla_raw.lower() not in ("heredar", "auto", "") else None
    tema_html = str(cuerpo.get("tema_html", "defecto"))
    paleta_tabla = str(cuerpo.get("paleta_tabla", "defecto"))
    paleta_tricolor = str(cuerpo.get("paleta_tricolor", "defecto"))
    footer_izq = str(cuerpo.get("footer_izq", "MarkFlow AI 2026"))
    footer_der = str(cuerpo.get("footer_der", ""))
    ancho_maximo = str(cuerpo.get("ancho_maximo", "900px"))
    ruta_salida_custom = str(cuerpo.get("ruta_salida", "")).strip()

    # Parámetros para Word / Tablas y Títulos
    modo_color_titulos = str(cuerpo.get("modo_color_titulos", "negro")).strip()
    paleta_suave_tablas = bool(cuerpo.get("paleta_suave_tablas", True))
    color_tabla_cabecera = str(cuerpo.get("color_tabla_cabecera", "")).strip()
    color_tabla_filas = str(cuerpo.get("color_tabla_filas", "")).strip()

    # Parámetros específicos para PDF Editorial (valores por defecto obligatorios)
    tema_pdf = str(cuerpo.get("tema_pdf", "pizarra_carbon"))
    estilo_maquetacion_pdf = str(cuerpo.get("estilo_maquetacion_pdf", "informe"))
    fuente_pdf = str(cuerpo.get("fuente_pdf", fuente))
    tamanio_pdf = float(cuerpo.get("tamanio_pdf", tamanio_pt))
    interlineado_pdf = float(cuerpo.get("interlineado_pdf", 1.15))
    justificado_pdf = bool(cuerpo.get("justificado_pdf", True))
    pie_pagina_pdf = str(cuerpo.get("pie_pagina_pdf", pie_pagina))
    alineacion_pie_pdf = str(cuerpo.get("alineacion_pie_pdf", alineacion_pie))
    numerar_paginas_pdf = bool(cuerpo.get("numerar_paginas_pdf", True))
    formato_num_pdf = str(cuerpo.get("formato_num_pdf", "pagina_x_de_y"))
    alineacion_num_pdf = str(cuerpo.get("alineacion_num_pdf", "derecha"))
    running_header_pdf = bool(cuerpo.get("running_header_pdf", True))
    running_header_texto = str(cuerpo.get("running_header_texto", "")).strip()
    salto_capitulo_pdf = bool(cuerpo.get("salto_capitulo_pdf", True))
    modo_diseno_pdf = str(cuerpo.get("modo_diseno_pdf", "estandar"))
    firma_nombre = str(cuerpo.get("firma_nombre", "")).strip() or ""
    firma_cargo = str(cuerpo.get("firma_cargo", "")).strip() or ""
    indice_al_final = bool(cuerpo.get("indice_al_final", True))

    tamanio_tabla_raw = cuerpo.get("tamanio_tabla_pt")
    tamanio_tabla_pt = float(tamanio_tabla_raw) if tamanio_tabla_raw and str(tamanio_tabla_raw).strip() not in ("auto", "0", "") else None

    salida, formulas, avisos = saneanar(texto)
    control = qa.auditar(salida, formulas)

    sesion = sesiones.crear_sesion()
    tallo = sesiones.nombre_seguro(f"{titulo}").replace(".md", "") or "documento"
    if not running_header_texto:
        running_header_texto = tallo

    generados: list[dict] = []
    rutas_generadas: list[Path] = []

    def _formato_tamano(bytes_cant: int) -> str:
        if bytes_cant < 1024:
            return f"{bytes_cant} B"
        elif bytes_cant < 1024 * 1024:
            return f"{bytes_cant / 1024:.1f} KB"
        return f"{bytes_cant / (1024 * 1024):.1f} MB"

    # 1) MD saneado (estrictamente solo si fue solicitado)
    if "md" in validos:
        ruta_md = sesiones.guardar(sesion, f"{tallo}-saneado.md", salida.encode("utf-8"))
        tam_md = ruta_md.stat().st_size
        generados.append({
            "formato": "md",
            "archivo": ruta_md.name,
            "tamano_bytes": tam_md,
            "tamano": _formato_tamano(tam_md),
        })
        rutas_generadas.append(ruta_md)

    # 2) HTML imprimible
    if "html" in validos:
        documento, _, avisos_html = a_html(
            salida,
            titulo=titulo,
            tema_html=tema_html,
            fuente=fuente,
            tamanio_pt=tamanio_pt,
            interlineado=1.6 if interlineado < 1.3 else interlineado,
            justificado=(alineacion == "justificado"),
            ancho_maximo=ancho_maximo,
            paleta_tabla=paleta_tabla,
            paleta_tricolor=paleta_tricolor,
            footer_izq=footer_izq,
            footer_der=footer_der,
            numerar_ecuaciones=numerar_ecuaciones,
        )
        ruta_html = sesiones.guardar(
            sesion, f"{tallo}.html", documento.encode("utf-8")
        )
        tam_html = ruta_html.stat().st_size
        generados.append({
            "formato": "html",
            "archivo": ruta_html.name,
            "tamano_bytes": tam_html,
            "tamano": _formato_tamano(tam_html),
        })
        rutas_generadas.append(ruta_html)
        avisos.extend(avisos_html)
        if copiar_activos_katex(sesiones.DIR_SALIDAS / sesion / "katex"):
            avisos.append("Paquete KaTeX localizado junto al entregable.")

        cuerpos_md = _cuerpos_formulas(salida)
        cuerpos_html = _cuerpos_html(documento)
        control["paridad_html"] = (
            Counter(cuerpos_html) == Counter(cuerpos_md)
            and control["formulas"] == len(cuerpos_md)
        )

    # 3) DOCX profesional
    if "docx" in validos:
        if ruta_pandoc() is None:
            raise _fallo(
                "PANDOC_NO_DISPONIBLE",
                "El motor DOCX requiere pandoc y no está instalado.",
                503,
            )
        try:
            ruta_docx, _, avisos_docx = a_docx(
                salida,
                sesiones.DIR_SALIDAS / sesion / f"{tallo}.docx",
                titulo=titulo,
                fuente=fuente,
                tamanio_pt=tamanio_pt,
                interlineado=interlineado,
                alineacion=alineacion,
                tema_word=tema_word,
                color_titulos_word=color_titulos_word,
                normas_apa=normas_apa,
                paleta_tabla=paleta_tabla,
                numerar_ecuaciones=numerar_ecuaciones,
                crear_indice=crear_indice,
                posicion_indice=posicion_indice,
                pie_pagina=pie_pagina,
                alineacion_pie=alineacion_pie,
                numerar_paginas=numerar_paginas,
                tamanio_tabla_pt=tamanio_tabla_pt,
                fuente_tabla=fuente_tabla,
                modo_color_titulos=modo_color_titulos,
                paleta_suave_tablas=paleta_suave_tablas,
                color_tabla_cabecera=color_tabla_cabecera,
                color_tabla_filas=color_tabla_filas,
            )
        except ErrorMotor as exc:
            raise _fallo("ERROR_MOTOR_DOCX", str(exc), 500)
        tam_docx = ruta_docx.stat().st_size
        generados.append({
            "formato": "docx",
            "archivo": ruta_docx.name,
            "tamano_bytes": tam_docx,
            "tamano": _formato_tamano(tam_docx),
        })
        rutas_generadas.append(ruta_docx)
        avisos.extend(avisos_docx)

    # 4) PDF Editorial de Alta Gama (Chromium Headless + PyMuPDF)
    if "pdf" in validos:
        try:
            ruta_pdf, _, avisos_pdf = a_pdf(
                salida,
                sesiones.DIR_SALIDAS / sesion / f"{tallo}.pdf",
                titulo=titulo,
                tema_pdf=tema_pdf,
                fuente=fuente_pdf,
                tamanio_pt=tamanio_pdf,
                interlineado=interlineado_pdf,
                justificado=justificado_pdf,
                estilo_maquetacion=estilo_maquetacion_pdf,
                pie_pagina=pie_pagina_pdf,
                alineacion_pie=alineacion_pie_pdf,
                numerar_paginas=numerar_paginas_pdf,
                formato_num=formato_num_pdf,
                alineacion_num=alineacion_num_pdf,
                running_header=running_header_pdf,
                running_header_texto=running_header_texto,
                normas_apa=normas_apa,
                numerar_ecuaciones=numerar_ecuaciones,
                salto_capitulo=salto_capitulo_pdf,
                modo_diseno=modo_diseno_pdf,
                firma_nombre=firma_nombre,
                firma_cargo=firma_cargo,
                indice_al_final=indice_al_final,
            )
        except ErrorMotorPDF as exc:
            raise _fallo("ERROR_MOTOR_PDF", str(exc), 500)
        tam_pdf = ruta_pdf.stat().st_size
        generados.append({
            "formato": "pdf",
            "archivo": ruta_pdf.name,
            "tamano_bytes": tam_pdf,
            "tamano": _formato_tamano(tam_pdf),
        })
        rutas_generadas.append(ruta_pdf)
        avisos.extend(avisos_pdf)

    # Persistencia y Escritura Real en Disco (docs/mejoras de app5.md - Corrección 4)
    # Si el usuario especificó ruta_salida_custom, se escribe directamente en ella;
    # si no, se garantiza en ./salidas de trabajo.
    try:
        carpeta_destino_fisico = Path(ruta_salida_custom).resolve() if ruta_salida_custom else (Path.cwd() / "salidas").resolve()
        carpeta_destino_fisico.mkdir(parents=True, exist_ok=True)
        for r in rutas_generadas:
            destino_archivo = carpeta_destino_fisico / r.name
            shutil.copy2(r, destino_archivo)
        if ruta_salida_custom:
            avisos.append(f"Archivos guardados físicamente en: {carpeta_destino_fisico}")
    except Exception as exc:
        avisos.append(f"Aviso de escritura física en disco: {exc}")

    for g in generados:
        g["url"] = f"/api/descargar/{sesion}/{g['archivo']}"

    return _sobre(datos={
        "sesion": sesion,
        "qa": control,
        "generados": generados,
        "avisos": avisos,
    })


# ---------------------------------------------------------------------------
#  GET /api/descargar/{sesion}/{nombre}
# ---------------------------------------------------------------------------
@router.get("/descargar/{identificador}/{nombre}")
async def descargar(identificador: str, nombre: str) -> FileResponse:
    try:
        ruta = sesiones.ruta_archivo(identificador, nombre)
    except ValueError as exc:
        raise _fallo("SESION_INVALIDA", str(exc), 400)
    except FileNotFoundError as exc:
        raise _fallo("ARCHIVO_INEXISTENTE", str(exc), 400)
    return FileResponse(
        ruta,
        filename=ruta.name,
        media_type="application/octet-stream",
    )


# ---------------------------------------------------------------------------
#  GET /api/ver/{sesion}/{nombre} (Visualización directa para Visor Flotante)
# ---------------------------------------------------------------------------
@router.get("/ver/{identificador}/{nombre}")
async def ver_documento(identificador: str, nombre: str) -> FileResponse:
    """Entrega el archivo con Content-Disposition 'inline' para visualización en iframe flotante."""
    try:
        ruta = sesiones.ruta_archivo(identificador, nombre)
    except ValueError as exc:
        raise _fallo("SESION_INVALIDA", str(exc), 400)
    except FileNotFoundError as exc:
        raise _fallo("ARCHIVO_INEXISTENTE", str(exc), 400)

    # Determinar tipo de contenido MIME
    nombre_l = nombre.lower()
    if nombre_l.endswith(".html"):
        media_type = "text/html; charset=utf-8"
    elif nombre_l.endswith(".md"):
        media_type = "text/markdown; charset=utf-8"
    elif nombre_l.endswith(".pdf"):
        media_type = "application/pdf"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        ruta,
        media_type=media_type,
        content_disposition_type="inline",
        headers={"Content-Disposition": f'inline; filename="{ruta.name}"'},
    )


# ---------------------------------------------------------------------------
#  POST /api/reiniciar (Reinicio en caliente del servidor backend)
# ---------------------------------------------------------------------------
@router.post("/reiniciar")
async def reiniciar_servidor() -> dict:
    """Programa el reinicio del servidor uvicorn backend."""
    import sys
    import threading
    import time

    def _hacer_reinicio():
        time.sleep(0.4)
        raiz_app = Path(__file__).resolve().parents[2]
        cmd = [sys.executable, "-X", "utf8", "-m", "uvicorn", "app.principal:app", "--port", "8310"]
        subprocess.Popen(cmd, cwd=str(raiz_app))
        os._exit(0)

    threading.Thread(target=_hacer_reinicio, daemon=True).start()
    return _sobre(datos={"mensaje": "Servidor reiniciándose en puerto 8310..."})


# ---------------------------------------------------------------------------
#  POST /api/extraer-inverso (Conversión inversa DOCX/PDF -> MD con imágenes)
# ---------------------------------------------------------------------------
@router.post("/extraer-inverso")
async def extraer_inverso(request: Request) -> dict:
    """Extrae Markdown limpio con imágenes en carpeta dedicada desde un .docx o .pdf."""
    archivos, texto = await _leer_formulario(request)
    if not archivos:
        raise _fallo("SIN_ARCHIVOS", "Envía al menos un archivo .docx o .pdf.", 400)

    subido = archivos[0]
    nombre_archivo = subido.filename or "documento.docx"
    tipo = clasificar_tipo(nombre_archivo)
    if tipo not in ("docx", "pdf"):
        raise _fallo("FORMATO_NO_SOPORTADO", "Solo se admite extracción inversa desde .docx o .pdf.", 415)

    sesion = sesiones.crear_sesion()
    bytes_archivo = await subido.read()
    ruta_guardada = sesiones.guardar(sesion, nombre_archivo, bytes_archivo)

    try:
        if tipo == "docx":
            md_limpio, ruta_md, imgs = convertir_docx_a_markdown(
                ruta_guardada, carpeta_salida=ruta_guardada.parent
            )
        else:
            md_limpio, ruta_md, imgs = convertir_pdf_a_markdown(
                ruta_guardada, carpeta_salida=ruta_guardada.parent
            )
    except Exception as exc:
        raise _fallo("ERROR_EXTRACCION_INVERSA", str(exc), 500)

    return _sobre(
        datos={
            "sesion": sesion,
            "archivo_original": nombre_archivo,
            "archivo_md": ruta_md.name,
            "texto_md": md_limpio,
            "imagenes_extraidas": [p.name for p in imgs],
            "total_imagenes": len(imgs),
            "carpeta_imagenes": f"{ruta_guardada.stem}_imagenes",
        }
    )


# ---------------------------------------------------------------------------
#  POST /api/render-preview (Previsualización KaTeX y Mermaid en vivo)
# ---------------------------------------------------------------------------
@router.post("/render-preview")
async def render_preview(request: Request) -> dict:
    """Compila un fragmento de Markdown a HTML en vivo con KaTeX y Mermaid para el visor Split-View y HTML."""
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "Se esperaba un objeto JSON con 'texto'.", 400)

    texto = str(cuerpo.get("texto") or cuerpo.get("markdown", ""))
    titulo = str(cuerpo.get("titulo", "Vista Previa")).strip() or "Vista Previa"
    tema_html = str(cuerpo.get("tema_html", "defecto")).strip() or "defecto"
    paleta_tricolor = str(cuerpo.get("paleta_tricolor", "tema_default")).strip() or "tema_default"
    fuente = str(cuerpo.get("fuente", 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif')).strip()
    ancho_maximo = str(cuerpo.get("ancho_maximo", "900px")).strip() or "900px"
    justificado_val = cuerpo.get("justificado", True)
    justificado = bool(justificado_val) if isinstance(justificado_val, bool) else str(justificado_val).lower() not in ("false", "0", "no")
    numerar_ecuaciones = bool(cuerpo.get("numerar_ecuaciones", False))
    footer_izq = str(cuerpo.get("footer_izq", "")).strip()
    footer_der = str(cuerpo.get("footer_der", "")).strip()

    texto_saneado, formulas, avisos_sanear = saneanar(texto)
    try:
        html_completo, _, avisos_html = a_html(
            texto=texto_saneado,
            titulo=titulo,
            tema_html=tema_html,
            paleta_tricolor=paleta_tricolor,
            fuente=fuente,
            ancho_maximo=ancho_maximo,
            justificado=justificado,
            numerar_ecuaciones=numerar_ecuaciones,
            footer_izq=footer_izq,
            footer_der=footer_der,
        )
    except FileNotFoundError as exc:
        raise _fallo("TEMA_HTML_NO_ENCONTRADO", str(exc), 404)

    return _sobre(
        datos={
            "html": html_completo,
            "formulas": formulas,
            "avisos": avisos_sanear + avisos_html,
        }
    )
