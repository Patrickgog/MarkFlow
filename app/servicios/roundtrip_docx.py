# -*- coding: utf-8 -*-
"""Round-trip .docx real: extracción docx→Markdown y reguardado byte-preserving.

Fase 2 del plan (v1.4.0). Dos mitades sobre el mismo archivo .docx:

1. **Extracción** (`extraer_md`): python-docx lee el cuerpo en orden de
   documento (párrafos y tablas) y produce Markdown para el editor Docs:
   - Títulos por `style_id` (`Heading1..6`, `Title`) — invariante de idioma.
   - Párrafos con negrita/cursiva por runs, enlaces `[texto](destino)`.
   - Listas por `w:numPr` (numFmt `bullet`→`-`, `decimal`→contadores), con
     sangría de 2 espacios por nivel.
   - Tablas GFM (primera fila = cabecera; alineación por `w:jc`).
   - Imágenes/OMML/revisiones → texto marcado + aviso (no representables).

2. **Reguardado** (`reguardar`): reconstruye el cuerpo OOXML desde el
   Markdown editado (markdown-it-py → lxml) y lo **trasplanta** al
   `word/document.xml` original reemplazando su contenido salvo el `w:sectPr`
   final (márgenes, orientación, referencias de cabecera/pie). El resto del
   paquete (styles.xml, headers, footers, numbering, media, rels) se copia
   byte a byte — patrón GenOffice.

Limitaciones documentadas (v1.5.0):
- Las listas se reguardan con marcador literal y sangría (sin numeración
  OOXML real — requeriría ids de `numbering.xml` de la plantilla).
- Los enlaces se reguardan como texto (hyperlink requiere rels propios).
- Fórmulas OMML no se reconstruyen (quedan marcadas).
- El control de cambios (`w:ins`/`w:del`) SÍ hace round-trip vía CriticMarkup
  (`{++insertado++}`/`{--borrado--}`), pero el autor y la fecha originales no
  se preservan: el reguardado estampa "MarkFlow Office" y la fecha actual.
- El contenido de los cambios no anida otras marcas (regla CriticMarkup con
  token plano — misma limitación del SSOT `editor_markdown.py`).
"""

from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lxml import etree

from app.servicios.editor_markdown import parser_con_criticmarkup

_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS_M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
_W = "{%s}" % _NS_W
_QN = lambda etiqueta: "{%s}%s" % (_NS_W, etiqueta)

_PARSER = parser_con_criticmarkup()
_AUTOR_CC = "MarkFlow Office"
_FECHA_CC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ════════════════════════════════════════════════════════════════════════════
# 1) Extracción: .docx → Markdown
# ════════════════════════════════════════════════════════════════════════════
_PATRON_HEADING = re.compile(r"^(?:Heading|T[íi]tulo)\s*([1-6])$", re.IGNORECASE)


def extraer_md(ruta: str | Path) -> dict:
    """Extrae el cuerpo de un .docx a Markdown (para el editor Docs)."""
    from docx import Document as abrir_documento
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    documento = abrir_documento(str(ruta))
    bloques: list[list[str]] = []  # cada bloque = grupo de líneas separado por línea en blanco
    ultimo_item = False  # los ítems consecutivos comparten bloque (lista compacta)
    stats = {"titulos": 0, "parrafos": 0, "items": 0, "tablas": 0}
    avisos: list[str] = []
    contadores = {"imagenes": 0, "enlaces": 0, "formulas": 0, "revisiones": 0}
    numeracion: dict[tuple[int, int], int] = {}  # (numId, ilvl) → contador decimal

    def texto_de_run(run_xml) -> str:
        """Texto de un `w:r`: `w:t`, `w:tab`→espacio, `w:br`→espacio, `w:delText`."""
        trozos: list[str] = []
        for hijo in run_xml:
            etiqueta = etree.QName(hijo).localname
            if etiqueta in ("t", "delText"):
                trozos.append(hijo.text or "")
            elif etiqueta in ("tab", "br"):
                trozos.append(" ")
        return "".join(trozos)

    def propiedades_de_run(run_xml) -> tuple[bool, bool]:
        """(negrita, cursiva) desde `w:rPr` (val != false/0/none)."""
        rpr = run_xml.find(_QN("rPr"))
        if rpr is None:
            return False, False

        def activo(nombre: str) -> bool:
            nodo = rpr.find(_QN(nombre))
            if nodo is None:
                return False
            return nodo.get(_QN("val")) not in ("false", "0", "none")

        return activo("b"), activo("i")

    partes: list[dict] = []  # {"texto": str, "revision": ""|"ins"|"del"}

    def caminar(elemento, revision: str) -> None:
        """Recorre hijos de `w:p` en orden de documento acumulando segmentos.

        `w:ins`/`w:del` marcan la revisión de sus runs (control de cambios);
        `w:hyperlink` se aplana a texto con destino; `w:r` aporta el texto.
        """
        for hijo in elemento:
            etiqueta = etree.QName(hijo).localname
            if etiqueta == "r":
                texto = texto_de_run(hijo)
                if not texto:
                    continue
                negrita, cursiva = propiedades_de_run(hijo)
                texto = texto.replace("|", "\\|")
                if negrita:
                    texto = f"**{texto.strip()}**" + (" " if texto.endswith(" ") else "")
                if cursiva:
                    texto = f"*{texto.strip()}*" + (" " if texto.endswith(" ") else "")
                partes.append({"texto": texto, "revision": revision})
            elif etiqueta == "hyperlink":
                rid = hijo.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
                destino = ""
                if rid and rid in parrafo.part.rels:
                    destino = str(parrafo.part.rels[rid].target_ref or "")
                texto = "".join(t.text or "" for t in hijo.iter(_QN("t"))).strip()
                if texto:
                    contadores["enlaces"] += 1
                    partes.append({
                        "texto": f"[{texto}]({destino})" if destino else texto,
                        "revision": revision,
                    })
            elif etiqueta in ("ins", "del", "smartTag", "sdt", "sdtContent"):
                caminar(hijo, etiqueta if etiqueta in ("ins", "del") else revision)

    def inline_de(parrafo: Paragraph) -> str:
        partes.clear()
        caminar(parrafo._p, "")
        # Agrupa segmentos consecutivos por revisión y aplica CriticMarkup
        salida: list[str] = []
        i = 0
        while i < len(partes):
            rev = partes[i]["revision"]
            trozos: list[str] = []
            j = i
            while j < len(partes) and partes[j]["revision"] == rev:
                trozos.append(partes[j]["texto"])
                j += 1
            bloque = "".join(trozos)
            if rev == "ins" and bloque.strip():
                bloque = f"{{++{bloque.strip()}++}}"
            elif rev == "del" and bloque.strip():
                bloque = f"{{--{bloque.strip()}--}}"
            salida.append(bloque)
            i = j
        return "".join(salida).strip()

    def nivel_de(parrafo: Paragraph) -> int:
        estilo = parrafo.style
        if estilo is None:
            return 0
        m = _PATRON_HEADING.match(estilo.style_id or "")
        if not m and estilo.name:
            m = _PATRON_HEADING.match(estilo.name)
        return int(m.group(1)) if m else 0

    def lista_de(parrafo: Paragraph) -> tuple[str, int] | None:
        """Marcador y nivel si el párrafo participa de una lista numerada.

        El `numPr` puede estar en el `pPr` directo del párrafo o heredarse del
        estilo de párrafo (`List Bullet`, `List Number`, … definidos en
        styles.xml) — se consulta primero el directo y luego el del estilo.
        """
        numpr = None
        ppr = parrafo._p.find(_QN("pPr"))
        if ppr is not None:
            numpr = ppr.find(_QN("numPr"))
        if numpr is None:
            estilo = parrafo.style
            ppr_estilo = estilo._element.find(_QN("pPr")) if estilo is not None else None
            if ppr_estilo is not None:
                numpr = ppr_estilo.find(_QN("numPr"))
        if numpr is None:
            return None
        num_id_n = numpr.find(_QN("numId"))
        if num_id_n is None or num_id_n.get(_QN("val")) in (None, "0"):
            return None  # numId 0 = sin numeración
        num_id = int(num_id_n.get(_QN("val")))
        ilvl_n = numpr.find(_QN("ilvl"))
        ilvl = int(ilvl_n.get(_QN("val"), "0")) if ilvl_n is not None else 0
        formato = "bullet"
        try:
            numeracion_xml = documento.part.numbering_part.element
            num = numeracion_xml.find(
                f"{_QN('num')}[@{_QN('numId')}='{num_id}']")
            abstract = numeracion_xml.find(
                f"{_QN('abstractNum')}[@{_QN('abstractNumId')}='"
                f"{num.get(_QN('abstractNumId'))}']")
            nivel_xml = abstract.find(f"{_QN('lvl')}[@{_QN('ilvl')}='{ilvl}']")
            formato = nivel_xml.find(_QN("numFmt")).get(_QN("val"))
        except Exception:
            formato = "bullet"
        if formato == "decimal":
            clave = (num_id, ilvl)
            numeracion[clave] = numeracion.get(clave, 0) + 1
            return f"{numeracion[clave]}. ", ilvl
        return "- ", ilvl  # bullet y demás formatos → viñeta

    def tabla_a_md(tabla: Table) -> list[str]:
        filas_texto: list[list[str]] = []
        alineaciones: list[str] = []
        for indice_fila, fila in enumerate(tabla.rows):
            celdas: list[str] = []
            for indice, celda in enumerate(fila.cells):
                trozos = [
                    inline_de(p) for p in celda.paragraphs if p.text.strip()
                ]
                texto = " ".join(t for t in trozos if t) or " "
                celdas.append(texto.replace("|", "\\|"))
                if indice_fila == 0:
                    valor = (celda.paragraphs[0].alignment
                             if celda.paragraphs else None)
                    if valor == WD_ALIGN_PARAGRAPH.CENTER:
                        alineaciones.append("center")
                    elif valor == WD_ALIGN_PARAGRAPH.RIGHT:
                        alineaciones.append("right")
                    else:
                        alineaciones.append("")
            filas_texto.append(celdas)
        if not filas_texto:
            return []
        columnas = max(len(f) for f in filas_texto)
        lineas_tabla: list[str] = []
        for indice_fila, fila in enumerate(filas_texto):
            fila = fila + [" "] * (columnas - len(fila))
            lineas_tabla.append("| " + " | ".join(fila) + " |")
            if indice_fila == 0:
                while len(alineaciones) < columnas:
                    alineaciones.append("")
                mapa = {"center": ":---:", "right": "---:", "left": ":---"}
                separadores = [mapa.get(a, "---") for a in alineaciones]
                lineas_tabla.append("|" + "|".join(separadores) + "|")
        return lineas_tabla

    for elemento in documento.element.body.iterchildren():
        etiqueta = etree.QName(elemento).localname

        if etiqueta == "p":
            parrafo = Paragraph(elemento, documento)
            contadores["formulas"] += len(
                elemento.findall(f".//{{{_NS_M}}}oMath"))
            contadores["revisiones"] += len(
                elemento.findall(f".//{_QN('ins')}")
                + elemento.findall(f".//{_QN('del')}"))
            contadores["imagenes"] += len(
                elemento.findall(f".//{_QN('drawing')}")
                + elemento.findall(f".//{_QN('pict')}"))

            nivel = nivel_de(parrafo)
            if nivel:
                texto = inline_de(parrafo)
                if texto:
                    bloques.append(["#" * nivel + " " + texto])
                    stats["titulos"] += 1
                    ultimo_item = False
            else:
                marcador = lista_de(parrafo)
                texto = inline_de(parrafo)
                if marcador and texto:
                    marca, nivel_lista = marcador
                    linea = f"{'  ' * nivel_lista}{marca}{texto}"
                    if ultimo_item and bloques:
                        bloques[-1].append(linea)  # lista compacta
                    else:
                        bloques.append([linea])
                    stats["items"] += 1
                    ultimo_item = True
                elif texto:
                    bloques.append([texto])
                    stats["parrafos"] += 1
                    ultimo_item = False

        elif etiqueta == "tbl":
            lineas_tabla = tabla_a_md(Table(elemento, documento))
            if lineas_tabla:
                bloques.append(lineas_tabla)
                stats["tablas"] += 1
                ultimo_item = False

    texto = "\n\n".join("\n".join(b) for b in bloques if b and any(b)) + "\n"
    if contadores["imagenes"]:
        avisos.append(f"{contadores['imagenes']} imagen(es) marcadas como "
                      "[imagen: …] — no se reinsertan al reguardar.")
    if contadores["formulas"]:
        avisos.append(f"{contadores['formulas']} fórmula(s) OMML convertidas "
                      "a texto plano (sin round-trip de ecuaciones).")
    if contadores["revisiones"]:
        avisos.append(f"{contadores['revisiones']} marca(s) de revisión conservadas "
                      "como control de cambios ({++insertado++}/{--borrado--}); "
                      "el autor y la fecha originales no se preservan al reguardar.")
    if contadores["enlaces"]:
        avisos.append(f"{contadores['enlaces']} enlace(s) conservados como "
                      "Markdown; al reguardar quedan como texto.")
    return {
        "texto": texto,
        "stats": stats,
        "avisos": avisos,
        "contadores": contadores,
    }


# ════════════════════════════════════════════════════════════════════════════
# 2) Reguardado: Markdown editado → cuerpo OOXML → trasplante byte-preserving
# ════════════════════════════════════════════════════════════════════════════
def reguardar(texto_md: str, ruta_original: str | Path) -> bytes:
    """Reconstruye el .docx original con el cuerpo editado (byte-preserving)."""
    with zipfile.ZipFile(ruta_original, "r") as zin:
        partes = {nombre: zin.read(nombre) for nombre in zin.namelist()}

    xml = partes["word/document.xml"].decode("utf-8")
    raiz = etree.fromstring(xml.encode("utf-8"))
    cuerpo = raiz.find(f"{_W}body")
    if cuerpo is None:
        raise ValueError("El documento no tiene w:body.")

    sectpr = cuerpo.find(f"{_W}sectPr")
    for hijo in list(cuerpo):
        if hijo is not sectpr:
            cuerpo.remove(hijo)

    contadores: dict[str, int] = {"imagenes": 0, "enlaces": 0, "revisiones": 0}
    for nodo in _cuerpo_desde_md(texto_md, contadores):
        cuerpo.append(nodo)

    partes["word/document.xml"] = etree.tostring(
        raiz, xml_declaration=True, encoding="UTF-8", standalone=True)

    bufer = io.BytesIO()
    with zipfile.ZipFile(bufer, "w", zipfile.ZIP_DEFLATED) as zout:
        for nombre, datos in partes.items():
            zout.writestr(nombre, datos)
    return bufer.getvalue()


# ── Fábrica de elementos OOXML ──────────────────────────────────────────────
def _nodo(etiqueta: str, atributos: dict | None = None) -> etree._Element:
    elemento = etree.Element(_W + etiqueta)
    for clave, valor in (atributos or {}).items():
        elemento.set(_QN(clave), str(valor))
    return elemento


def _run(texto: str, negrita: bool = False, cursiva: bool = False,
         mono: bool = False, salto: bool = False) -> etree._Element:
    """Un `w:r` con propiedades opcionales; `salto` produce `w:br`."""
    r = _nodo("r")
    if negrita or cursiva or mono or salto:
        rpr = _nodo("rPr")
        if negrita:
            rpr.append(_nodo("b"))
        if cursiva:
            rpr.append(_nodo("i"))
        if mono:
            rfonts = _nodo("rFonts")
            rfonts.set(_QN("ascii"), "Consolas")
            rfonts.set(_QN("hAnsi"), "Consolas")
            rpr.append(rfonts)
        r.append(rpr)
    if salto:
        r.append(_nodo("br"))
        return r
    t = _nodo("t")
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = texto
    r.append(t)
    return r


def _runs_de_inline(children: list, contadores: dict) -> list[etree._Element]:
    """Convierte los hijos `inline` de markdown-it en runs (b/i/code/br).

    Los tokens `ins_open/ins_close`/`del_open/del_close` (CriticMarkup) envuelven
    los runs en `w:ins`/`w:del` reales — Microsoft Word los muestra como control
    de cambios aceptable/rechazable (el `w:del` usa `w:delText`).
    """
    runs: list[etree._Element] = []
    estado = {"negrita": False, "cursiva": False, "ins": False, "del": False}
    pendiente: list[str] = []

    def vaciar() -> None:
        if not pendiente:
            return
        texto = "".join(pendiente)
        pendiente.clear()
        r = _run(texto, estado["negrita"], estado["cursiva"])
        if estado["del"]:
            contadores["revisiones"] += 1
            envoltura = _nodo("del", {"id": contadores["revisiones"],
                                      "author": _AUTOR_CC, "date": _FECHA_CC})
            t = r.find(_QN("t"))
            if t is not None:
                t.tag = _QN("delText")
            envoltura.append(r)
            runs.append(envoltura)
        elif estado["ins"]:
            contadores["revisiones"] += 1
            envoltura = _nodo("ins", {"id": contadores["revisiones"],
                                      "author": _AUTOR_CC, "date": _FECHA_CC})
            envoltura.append(r)
            runs.append(envoltura)
        else:
            runs.append(r)

    for hijo in children or []:
        tipo = hijo.type
        if tipo == "text":
            pendiente.append(hijo.content)
        elif tipo in ("ins_open", "ins_close", "del_open", "del_close"):
            vaciar()
            estado[tipo.rsplit("_", 1)[0]] = tipo.endswith("_open")
        elif tipo == "strong_open":
            vaciar(); estado["negrita"] = True
        elif tipo == "strong_close":
            vaciar(); estado["negrita"] = False
        elif tipo == "em_open":
            vaciar(); estado["cursiva"] = True
        elif tipo == "em_close":
            vaciar(); estado["cursiva"] = False
        elif tipo == "s_open":
            vaciar(); estado["cursiva"] = True  # tachado ≈ cursiva v1.4
        elif tipo == "s_close":
            vaciar(); estado["cursiva"] = False
        elif tipo == "code_inline":
            vaciar()
            runs.append(_run(hijo.content, mono=True))
        elif tipo == "softbreak":
            pendiente.append(" ")
        elif tipo == "hardbreak":
            vaciar()
            runs.append(_run("", salto=True))
        elif tipo == "image":
            vaciar()
            contadores["imagenes"] += 1
            alt = (hijo.children[0].content if hijo.children else "") or ""
            pendiente.append(f"[imagen: {alt}]".strip())
        elif tipo == "link_open":
            contadores["enlaces"] += 1
    vaciar()
    return runs


def _parrafo(inline=None, nivel: int = 0, marcador: str | None = None,
             sangria_twips: int = 0, alineacion: str | None = None,
             mono: bool = False, contadores: dict | None = None) -> etree._Element:
    """Un `w:p` con pStyle HeadingN, jc, sangría y runs del inline."""
    p = _nodo("p")
    if nivel or marcador is not None or sangria_twips or alineacion:
        ppr = _nodo("pPr")
        if nivel:
            ppr.append(_nodo("pStyle", {"val": f"Heading{min(6, max(1, nivel))}"}))
        if alineacion in ("center", "right", "left"):
            ppr.append(_nodo("jc", {"val": alineacion}))
        if sangria_twips:
            ppr.append(_nodo("ind", {"left": sangria_twips}))
        p.append(ppr)
    runs = _runs_de_inline(inline.children if inline is not None else [],
                           contadores or {"imagenes": 0, "enlaces": 0})
    if marcador:
        p.append(_run(marcador, mono=mono))
    for run in runs:
        p.append(run)
    return p


def _parrafo_mono(linea: str) -> etree._Element:
    p = _nodo("p")
    ppr = _nodo("pPr")
    ppr.append(_nodo("spacing", {"after": "0", "line": "240", "lineRule": "auto"}))
    p.append(ppr)
    p.append(_run(linea if linea else " ", mono=True))
    return p


def _separador() -> etree._Element:
    """Separador horizontal → párrafo con borde inferior."""
    p = _nodo("p")
    ppr = _nodo("pPr")
    pbdr = _nodo("pBdr")
    abajo = _nodo("bottom", {"val": "single", "sz": "6", "space": "1", "color": "auto"})
    pbdr.append(abajo)
    ppr.append(pbdr)
    p.append(ppr)
    p.append(_run(" "))
    return p


def _tabla(tokens: list, desde: int) -> tuple[etree._Element, int]:
    """Tabla GFM (tokens markdown-it) → w:tbl con bordes y alineación."""
    filas: list[tuple[bool, list[tuple[str, list]]]] = []  # (cabecera, celdas)
    i = desde + 1
    while i < len(tokens) and tokens[i].type != "table_close":
        if tokens[i].type == "tr_open":
            cabecera = False
            celdas: list[tuple[str, list]] = []
            i += 1
            while i < len(tokens) and tokens[i].type != "tr_close":
                tipo = tokens[i].type
                if tipo in ("th_open", "td_open"):
                    cabecera = cabecera or tipo == "th_open"
                    estilo = (tokens[i].attrs.get("style") or "")
                    m = re.search(r"text-align:\s*(center|right|left)", estilo)
                    inline = tokens[i + 1] if (i + 1 < len(tokens)
                                               and tokens[i + 1].type == "inline") else None
                    celdas.append((m.group(1) if m else "", inline))
                    i += 2 if inline else 1
                else:
                    i += 1
            filas.append((cabecera, celdas))
            i += 1
        else:
            i += 1

    tbl = _nodo("tbl")
    tblpr = _nodo("tblPr")
    anchura = _nodo("tblW", {"w": "0", "type": "auto"})
    tblpr.append(anchura)
    bordes = _nodo("tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        bordes.append(_nodo(lado, {"val": "single", "sz": "4", "space": "0",
                                   "color": "auto"}))
    tblpr.append(bordes)
    look = _nodo("tblLook", {"val": "04A0", "firstRow": "1", "lastRow": "0",
                             "firstColumn": "1", "lastColumn": "0",
                             "noHBand": "0", "noVBand": "1"})
    tblpr.append(look)
    tbl.append(tblpr)

    # w:tblGrid es hijo obligatorio de w:tbl (columnas del/layout grid)
    filas_planas = [f for _, f in filas]
    n_columnas = max((len(f) for f in filas_planas), default=1)
    grid = _nodo("tblGrid")
    for _ in range(n_columnas):
        grid.append(_nodo("gridCol", {"w": "2880"}))
    tbl.append(grid)

    for cabecera, celdas in filas:
        tr = _nodo("tr")
        if cabecera:
            trpr = _nodo("trPr")
            trpr.append(_nodo("tblHeader"))
            tr.append(trpr)
        for alineacion, inline in celdas:
            tc = _nodo("tc")
            tcpr = _nodo("tcPr")
            tcpr.append(_nodo("tcW", {"w": "0", "type": "auto"}))
            tc.append(tcpr)
            p = _nodo("p")
            if alineacion:
                ppr = _nodo("pPr")
                ppr.append(_nodo("jc", {"val": alineacion}))
                p.append(ppr)
            contadores_local: dict[str, int] = {"imagenes": 0, "enlaces": 0}
            for run in _runs_de_inline(inline.children if inline else [],
                                       contadores_local):
                p.append(run)
            tc.append(p)
            tr.append(tc)
        tbl.append(tr)
    return tbl, i


def _lista(tokens: list, desde: int, contadores: dict,
           nivel: int = 0) -> tuple[list[etree._Element], int]:
    """Listas (bullet/ordered) → párrafos con marcador literal y sangría."""
    tipo = tokens[desde].type  # bullet_list_open | ordered_list_open
    numerada = tipo == "ordered_list_open"
    etiqueta_cierre = "bullet_list_close" if numerada is False else "ordered_list_close"
    contador = 1
    if numerada:
        inicio = (tokens[desde].attrs or {}).get("start")
        contador = int(inicio) if inicio else 1

    nodos: list[etree._Element] = []
    i = desde + 1
    while i < len(tokens) and tokens[i].type != etiqueta_cierre:
        if tokens[i].type == "list_item_open":
            i += 1
            primero = True
            while i < len(tokens) and tokens[i].type != "list_item_close":
                tok = tokens[i]
                if tok.type == "paragraph_open":
                    inline = tokens[i + 1]
                    marca = f"{contador}. " if numerada else "- "
                    nodos.append(_parrafo(
                        inline=inline, marcador=marca if primero else None,
                        sangria_twips=360 * (nivel + 1)))
                    if primero and numerada:
                        contador += 1
                    primero = False
                    i += 3
                elif tok.type in ("bullet_list_open", "ordered_list_open"):
                    sub, i = _lista(tokens, i, contadores, nivel + 1)
                    nodos.extend(sub)
                elif tok.type == "fence":
                    for linea in tok.content.rstrip("\n").split("\n"):
                        nodos.append(_parrafo_mono(linea))
                    i += 1
                else:
                    i += 1
            i += 1  # list_item_close
        else:
            i += 1
    return nodos, i + 1


def _cuerpo_desde_md(texto_md: str,
                     contadores: dict) -> list[etree._Element]:
    tokens = _PARSER.parse(texto_md)
    nodos: list[etree._Element] = []
    i = 0
    total = len(tokens)
    while i < total:
        tipo = tokens[i].type
        if tipo == "heading_open":
            nivel = int(tokens[i].tag[1])
            nodos.append(_parrafo(inline=tokens[i + 1], nivel=nivel,
                                  contadores=contadores))
            i += 3
        elif tipo == "paragraph_open":
            nodos.append(_parrafo(inline=tokens[i + 1], contadores=contadores))
            i += 3
        elif tipo == "fence" or tipo == "code_block":
            contenido = tokens[i].content.rstrip("\n")
            for linea in contenido.split("\n"):
                nodos.append(_parrafo_mono(linea))
            i += 1
        elif tipo == "table_open":
            tabla, i = _tabla(tokens, i)
            nodos.append(tabla)
        elif tipo in ("bullet_list_open", "ordered_list_open"):
            sub, i = _lista(tokens, i, contadores, 0)
            nodos.extend(sub)
        elif tipo == "blockquote_open":
            i += 1  # aplanado: los párrafos internos se renderizan normales
        elif tipo == "blockquote_close":
            i += 1
        elif tipo == "hr":
            nodos.append(_separador())
            i += 1
        else:
            i += 1
    return nodos
