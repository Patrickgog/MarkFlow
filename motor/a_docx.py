"""Motor de transformación a DOCX (pandoc + OMML nativo + barnizado profesional).

Pipeline:
  1. pandoc convierte el Markdown saneado a .docx; las fórmulas `\\( \\)` /
     `\\[ \\]` salen como ecuaciones OMML nativas de Word (editables).
  2. Separación estricta entre Temas Nativos (inmutables en sus tablas) y
     "Tema Personalizado" (con paleta suave).
  3. Barnizado con python-docx:
     - Interlineado 1.0 (Sencillo) por defecto con espaciado posterior compacto.
     - Tabla de Contenidos (TOC) nativa configurable (inicio / final) con updateFields.
     - Índice automático de Ecuaciones ubicado tras el TOC general.
     - Alineación horizontal configurable del pie de página (izquierda, centro, derecha).
     - Formato APA 7ma Edición (márgenes 2.54 cm, sangría 1.27 cm, tablas APA, títulos).
     - Paleta de colores suaves (pastel / soft tones) en tablas para Tema Personalizado.
     - Tipografía de alta fidelidad (Times New Roman, Arial, Calibri, Georgia, Aptos, etc.).
     - Numeración automática de ecuaciones display `(1)`, `(2)`.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, Inches, Mm, Pt, RGBColor
import docx.enum.text

from motor.a_mermaid import reemplazar_mermaid_por_imagenes
from motor.qa import contar_formulas

_PANDOC_LOCAL = Path(__file__).resolve().parent / "assets" / "pandoc" / ("pandoc.exe" if __import__("os").name == "nt" else "pandoc")

_DIR_TEMAS_WORD = Path(__file__).resolve().parent.parent / "templates" / "temas_word"

_ALINEACIONES = {
    "izquierda": WD_ALIGN_PARAGRAPH.LEFT,
    "centrado": WD_ALIGN_PARAGRAPH.CENTER,
    "derecha": WD_ALIGN_PARAGRAPH.RIGHT,
    "justificado": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

_MAPA_JC_VAL = {
    "izquierda": "left",
    "centrado": "center",
    "derecha": "right",
    "justificado": "both",
}

_NOMBRES_TEMAS_DISCO = {
    "tema1": "Tema 1: Memoria Técnica Clásica (templates/temas_word/tema1.docx)",
    "tema2": "Tema 2: Ingeniería Sobria Sin Laterales (templates/temas_word/tema2.docx)",
    "tema3": "Tema 3: Editorial Azul Acero (templates/temas_word/tema3.docx)",
}


def inspeccionar_tema_word(tema_id: str) -> dict:
    """Inspecciona físicamente un archivo .docx en templates/temas_word/ y retorna sus estilos reales.

    Si el archivo no existe en disco, lanza FileNotFoundError con un aviso explícito.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    clave = (tema_id or "").strip().lower().replace(".docx", "")
    ruta = _DIR_TEMAS_WORD / f"{clave}.docx"
    if not ruta.is_file():
        raise FileNotFoundError(
            f"Tema '{tema_id}' no encontrado en templates/temas_word ({ruta.name} no existe)."
        )

    ns_w = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    fuente_base = "Calibri"
    tamanio_base = 11.0
    h1_color = "#111827"
    h2_color = "#111827"
    h3_color = "#111827"
    h1_pt = 15.0
    h2_pt = 14.0
    h3_pt = 12.0
    cabecera_bg = "#F2F2F2"
    cabecera_txt = "#111827"
    fila_par_bg = "#FFFFFF"
    borde_tabla = "#999999"
    estilo_bordes = "completo"

    try:
        with zipfile.ZipFile(str(ruta), "r") as zf:
            if "word/styles.xml" in zf.namelist():
                root = ET.fromstring(zf.read("word/styles.xml"))
                for st in root.findall("w:style", ns_w):
                    if st.attrib.get(f"{{{ns_w['w']}}}type") != "paragraph":
                        continue
                    sid = (st.attrib.get(f"{{{ns_w['w']}}}styleId") or "").lower()
                    name_el = st.find("w:name", ns_w)
                    sname = (name_el.attrib.get(f"{{{ns_w['w']}}}val") if name_el is not None else "").lower()
                    rpr = st.find("w:rPr", ns_w)
                    if rpr is None:
                        continue
                    col_el = rpr.find("w:color", ns_w)
                    col_val = col_el.attrib.get(f"{{{ns_w['w']}}}val") if col_el is not None else None
                    sz_el = rpr.find("w:sz", ns_w)
                    sz_val = (
                        int(sz_el.attrib.get(f"{{{ns_w['w']}}}val")) / 2.0
                        if (sz_el is not None and sz_el.attrib.get(f"{{{ns_w['w']}}}val", "").isdigit())
                        else None
                    )
                    rf_el = rpr.find("w:rFonts", ns_w)
                    rf_val = (
                        rf_el.attrib.get(f"{{{ns_w['w']}}}ascii")
                        or rf_el.attrib.get(f"{{{ns_w['w']}}}hAnsi")
                        if rf_el is not None
                        else None
                    )

                    if sname == "normal" or sid == "normal":
                        if rf_val:
                            fuente_base = rf_val
                        if sz_val:
                            tamanio_base = sz_val
                    elif sname == "heading 1" or sid in ("ttulo1", "heading1", "titulo1"):
                        if col_val and col_val.lower() != "auto":
                            h1_color = f"#{col_val.upper()}"
                        if sz_val:
                            h1_pt = sz_val
                    elif sname == "heading 2" or sid in ("ttulo2", "heading2", "titulo2"):
                        if col_val and col_val.lower() != "auto":
                            h2_color = f"#{col_val.upper()}"
                        if sz_val:
                            h2_pt = sz_val
                    elif sname == "heading 3" or sid in ("ttulo3", "heading3", "titulo3"):
                        if col_val and col_val.lower() != "auto":
                            h3_color = f"#{col_val.upper()}"
                        if sz_val:
                            h3_pt = sz_val

            if "word/document.xml" in zf.namelist():
                doc_root = ET.fromstring(zf.read("word/document.xml"))
                tbl = doc_root.find(".//w:tbl", ns_w)
                if tbl is not None:
                    bdr_top = tbl.find("./w:tblPr/w:tblBorders/w:top", ns_w)
                    bdr_left = tbl.find("./w:tblPr/w:tblBorders/w:left", ns_w)
                    bdr_inh = tbl.find("./w:tblPr/w:tblBorders/w:insideH", ns_w)
                    if bdr_top is not None:
                        c_top = bdr_top.attrib.get(f"{{{ns_w['w']}}}color", "")
                        if c_top and c_top.lower() != "auto":
                            borde_tabla = f"#{c_top.upper()}"
                        elif c_top.lower() == "auto":
                            borde_tabla = "#111827"
                    if bdr_left is None or bdr_left.attrib.get(f"{{{ns_w['w']}}}val") in ("none", "nil"):
                        estilo_bordes = "horizontal"
                    elif bdr_inh is not None and bdr_inh.attrib.get(f"{{{ns_w['w']}}}val") in ("none", "nil"):
                        estilo_bordes = "exterior"

                    shds = [
                        el.attrib.get(f"{{{ns_w['w']}}}fill", "")
                        for el in tbl.findall(".//w:tc/w:tcPr/w:shd", ns_w)
                        if el.attrib.get(f"{{{ns_w['w']}}}fill", "").upper() not in ("", "AUTO", "FFFFFF")
                    ]
                    if shds:
                        cabecera_bg = f"#{shds[0].upper()}"
    except Exception:
        pass

    # Ajustes canónicos de tabla según la estructura real verificada en tema1.docx, tema2.docx, tema3.docx
    if clave == "tema1":
        cabecera_bg = "#F2F2F2"
        cabecera_txt = "#111827"
        fila_par_bg = "#FFFFFF"
        borde_tabla = "#999999"
        estilo_bordes = "exterior"
    elif clave == "tema2":
        cabecera_bg = "#F8FAFC"
        cabecera_txt = "#111827"
        fila_par_bg = "#FFFFFF"
        borde_tabla = "#111827"
        estilo_bordes = "horizontal"
        h2_pt = 12.0
        h3_pt = 11.0
    elif clave == "tema3":
        cabecera_bg = "#4F81BD"
        cabecera_txt = "#FFFFFF"
        fila_par_bg = "#F2F2F2"
        borde_tabla = "#BFBFBF"
        estilo_bordes = "completo"
        h1_pt = 16.0
        h2_pt = 14.0
        h3_pt = 12.0

    return {
        "id": clave,
        "archivo": ruta.name,
        "ruta": str(ruta),
        "existe": True,
        "nombre": _NOMBRES_TEMAS_DISCO.get(clave, f"Tema {clave.upper()} ({ruta.name})"),
        "fuente": fuente_base,
        "tamanio_pt": tamanio_base,
        "h1_color": h1_color,
        "h2_color": h2_color,
        "h3_color": h3_color,
        "h1_pt": h1_pt,
        "h2_pt": h2_pt,
        "h3_pt": h3_pt,
        "tabla": {
            "cabecera_bg": cabecera_bg,
            "cabecera_txt": cabecera_txt,
            "fila_par_bg": fila_par_bg,
            "borde": borde_tabla,
            "estilo_bordes": estilo_bordes,
        },
    }


def listar_temas_word_disco() -> list[dict]:
    """Lista todos los temas .docx físicamente existentes en templates/temas_word/."""
    temas: list[dict] = []
    if _DIR_TEMAS_WORD.is_dir():
        for archivo in sorted(_DIR_TEMAS_WORD.glob("*.docx")):
            if archivo.name.startswith("~$"):
                continue
            try:
                temas.append(inspeccionar_tema_word(archivo.stem))
            except Exception:
                continue
    return temas

# Paletas de colores suaves (Pastel / Soft tones) para cuadros y tablas
PALETAS_TABLA: dict[str, dict[str, str]] = {
    "defecto": {
        "nombre": "Gris Sobrio / Clásico",
        "header_bg": "F1F5F9",
        "row_alt": "FFFFFF",
        "border": "9CA3AF",
        "text": "111827",
    },
    "gris_ejecutivo": {
        "nombre": "Gris Ejecutivo Formal",
        "header_bg": "E5E7EB",
        "row_alt": "F9FAFB",
        "border": "6B7280",
        "text": "111827",
    },
    "salvia_suave": {
        "nombre": "Verde Salvia Apagado",
        "header_bg": "E6F0EB",
        "row_alt": "F5FAF7",
        "border": "A3C4B3",
        "text": "1E3A2B",
    },
    "crema_neutro": {
        "nombre": "Crema Marfil Neutro",
        "header_bg": "F8F5EE",
        "row_alt": "FDFBF7",
        "border": "CFC4B0",
        "text": "2D2A26",
    },
    "ceniza_formal": {
        "nombre": "Ceniza Grafito Suave",
        "header_bg": "EBECEF",
        "row_alt": "F7F8F9",
        "border": "B4B8C2",
        "text": "1A1D23",
    },
    "azul_acero_suave": {
        "nombre": "Azul Acero Apagado (Pastel)",
        "header_bg": "E8EEF5",
        "row_alt": "F6F9FC",
        "border": "ADC3DC",
        "text": "1E2D3D",
    },
}


class ErrorMotor(RuntimeError):
    """Fallo de un motor de transformación (documento no generado)."""


def ruta_pandoc() -> str | None:
    """Ejecutable de pandoc disponible (PATH o respaldo local)."""
    en_path = shutil.which("pandoc")
    if en_path:
        return en_path
    if _PANDOC_LOCAL.is_file():
        return str(_PANDOC_LOCAL)
    return None


_MARCA_LISTA = re.compile(r"^\s*(?:[-*+] .|\d+[.)] )")
_CERCO_PANDOC = re.compile(r"^\s*```")


def _adaptar_listas_pandoc(texto: str) -> str:
    """Garantiza línea en blanco antes de cada bloque de lista (pandoc)."""
    lineas = texto.split("\n")
    fuera: list[str] = []
    cerca = False
    for linea in lineas:
        if _CERCO_PANDOC.match(linea):
            cerca = not cerca
            fuera.append(linea)
            continue
        if cerca or linea.lstrip().startswith("|"):
            fuera.append(linea)
            continue
        es_lista = bool(_MARCA_LISTA.match(linea))
        previa = fuera[-1] if fuera else ""
        if (
            es_lista
            and previa.strip()
            and not _MARCA_LISTA.match(previa)
        ):
            fuera.append("")
        fuera.append(linea)
    return "\n".join(fuera)


# Catálogo de Paletas de Títulos para Word (docs/mejoras/mejoras_app_01.md y mejoras_app_02.md)
PALETAS_TITULOS_WORD: dict[str, dict[str, str]] = {
    "negro": {"primario": "000000", "secundario": "111111", "acento": "333333", "nombre": "Negro Absoluto (#000000)"},
    "azul": {"primario": "1E3A8A", "secundario": "2563EB", "acento": "3B82F6", "nombre": "Azul Institucional (#1E3A8A)"},
    "corporate-blue": {"primario": "003366", "secundario": "205081", "acento": "4682B4", "nombre": "Azul Ejecutivo (#003366)"},
    "emerald-tech": {"primario": "046A38", "secundario": "1F8A53", "acento": "50C878", "nombre": "Esmeralda Académico (#046A38)"},
    "slate-modern": {"primario": "2F4F4F", "secundario": "4A6B6B", "acento": "708090", "nombre": "Pizarra Minimalista (#2F4F4F)"},
    "burgundy-classic": {"primario": "6B1426", "secundario": "85223A", "acento": "A3334D", "nombre": "Vino Tinto Editorial (#6B1426)"},
}


def _hex_a_rgb_color(hex_str: str, default_hex: str = "000000") -> tuple[RGBColor, str]:
    """Convierte un string hexadecimal a RGBColor y HEX limpio."""
    h = (hex_str or "").strip().lstrip("#")
    if len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h):
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)), h.upper()
    dh = default_hex.lstrip("#")
    return RGBColor(int(dh[0:2], 16), int(dh[2:4], 16), int(dh[4:6], 16)), dh.upper()


def _obtener_paleta_titulos_3c(color_str: str) -> dict[str, Any]:
    """Extrae la paleta completa de 3 colores (H1, H2/H3 y Acento/Borde) para Word."""
    c_clean = (color_str or "").strip()
    c_lower = c_clean.lower()
    if c_lower in PALETAS_TITULOS_WORD:
        item = PALETAS_TITULOS_WORD[c_lower]
        r1, h1 = _hex_a_rgb_color(item["primario"])
        r2, h2 = _hex_a_rgb_color(item["secundario"])
        r3, h3 = _hex_a_rgb_color(item.get("acento", item["secundario"]))
        return {
            "nombre": item["nombre"],
            "primario_rgb": r1, "primario_hex": h1,
            "secundario_rgb": r2, "secundario_hex": h2,
            "acento_rgb": r3, "acento_hex": h3,
        }

    if "|" in c_clean:
        partes = [p.strip() for p in c_clean.split("|")]
        h1_raw = partes[0] if len(partes) > 0 and partes[0] else "000000"
        h2_raw = partes[1] if len(partes) > 1 and partes[1] else h1_raw
        h3_raw = partes[2] if len(partes) > 2 and partes[2] else h2_raw
        r1, h1 = _hex_a_rgb_color(h1_raw, "000000")
        r2, h2 = _hex_a_rgb_color(h2_raw, h1)
        r3, h3 = _hex_a_rgb_color(h3_raw, h2)
        return {
            "nombre": f"Personalizada (#{h1})",
            "primario_rgb": r1, "primario_hex": h1,
            "secundario_rgb": r2, "secundario_hex": h2,
            "acento_rgb": r3, "acento_hex": h3,
        }

    hex_puro = c_clean.lstrip("#")
    if len(hex_puro) == 6 and all(c in "0123456789abcdefABCDEF" for c in hex_puro):
        r1, h1 = _hex_a_rgb_color(hex_puro)
        return {
            "nombre": f"Personalizada (#{h1})",
            "primario_rgb": r1, "primario_hex": h1,
            "secundario_rgb": r1, "secundario_hex": h1,
            "acento_rgb": r1, "acento_hex": h1,
        }

    r0, h0 = RGBColor(0, 0, 0), "000000"
    return {
        "nombre": "Negro Absoluto (#000000)",
        "primario_rgb": r0, "primario_hex": h0,
        "secundario_rgb": r0, "secundario_hex": h0,
        "acento_rgb": r0, "acento_hex": h0,
    }


def _obtener_color_titulos(color_str: str) -> tuple[RGBColor, str, str]:
    """Interpreta el color de títulos y retorna RGBColor, HEX y Nombre primario."""
    pal = _obtener_paleta_titulos_3c(color_str)
    return pal["primario_rgb"], pal["primario_hex"], pal["nombre"]


def resolver_imagenes_en_markdown_docx(texto: str, base_dir: Path | str | None = None) -> str:
    """Resuelve rutas de imágenes locales relativas a absolutas para que pandoc las incruste sin enlaces rotos."""
    base = Path(base_dir) if base_dir else Path.cwd()

    def _resolver_ruta(ruta_str: str) -> str:
        ruta_limpia = ruta_str.strip()
        if not ruta_limpia or ruta_limpia.startswith(("http://", "https://", "data:")):
            return ruta_str
        ruta_sin_comillas = ruta_limpia.strip("'\"")
        candidatos = [
            base / ruta_sin_comillas,
            Path.cwd() / ruta_sin_comillas,
            Path(ruta_sin_comillas),
        ]
        for cand in candidatos:
            try:
                if cand.is_file():
                    return str(cand.resolve()).replace("\\", "/")
            except Exception:
                continue
        return ruta_str

    # Sintaxis Markdown: ![alt](ruta "opcional")
    def _sub_md_img(m: re.Match) -> str:
        alt = m.group(1)
        resto = m.group(2).strip()
        partes = resto.split(maxsplit=1)
        ruta = partes[0]
        titulo = f" {partes[1]}" if len(partes) > 1 else ""
        nueva_ruta = _resolver_ruta(ruta)
        return f"![{alt}]({nueva_ruta}{titulo})"

    texto_res = re.sub(r"!\[(.*?)\]\((.*?)\)", _sub_md_img, texto)

    # Sintaxis HTML: <img ... src="..." ...>
    def _sub_html_img(m: re.Match) -> str:
        attrs_antes = m.group(1) or ""
        src = m.group(2)
        attrs_despues = m.group(3) or ""
        nueva_ruta = _resolver_ruta(src)
        return f'<img{attrs_antes} src="{nueva_ruta}"{attrs_despues}>'

    texto_res = re.sub(r'<img\b([^>]*?)\bsrc=["\']([^"\']+)["\']([^>]*?)>', _sub_html_img, texto_res, flags=re.I)
    return texto_res


def _pandoc_a_docx(
    texto: str,
    destino: Path,
    plantilla_referencia: Path | None = None,
) -> None:
    """Convierte Markdown saneado a .docx con pandoc (stdin -> archivo)."""
    exe = ruta_pandoc()
    if exe is None:
        raise ErrorMotor(
            "pandoc no está disponible (ni en PATH ni como binario local)."
        )
    texto = _adaptar_listas_pandoc(texto)
    cmd = [
        exe,
        "--from",
        "markdown+tex_math_dollars+tex_math_single_backslash+tex_math_double_backslash+raw_tex+link_attributes",
        "--to", "docx",
        "-o", str(destino),
    ]
    if plantilla_referencia and plantilla_referencia.is_file():
        cmd.extend(["--reference-doc", str(plantilla_referencia)])
    cmd.append("-")

    proceso = subprocess.run(
        cmd,
        input=texto.encode("utf-8"),
        capture_output=True,
        timeout=120,
    )
    if proceso.returncode != 0 or not destino.is_file():
        detalle = proceso.stderr.decode("utf-8", errors="replace")[:300]
        raise ErrorMotor(f"pandoc rechazó el documento: {detalle}")


# Orden del esquema CT_TblPrBase (ECMA-376)
_ORDEN_TBLPR = (
    "tblStyle", "tblpPr", "tblOverlap", "bidiVisual",
    "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc",
    "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout",
    "tblCellMar", "tblLook", "tblCaption", "tblDescription",
)


def _insertar_ordenado(contenedor, nodo, etiqueta: str) -> None:
    """Inserta `nodo` en `contenedor` respetando el orden del esquema."""
    objetivo = _ORDEN_TBLPR.index(etiqueta)
    for hijo in contenedor:
        nombre = hijo.tag.rsplit("}", 1)[-1]
        if nombre in _ORDEN_TBLPR and _ORDEN_TBLPR.index(nombre) > objetivo:
            hijo.addprevious(nodo)
            return
    contenedor.append(nodo)


# Orden del esquema CT_TcPrBase (ECMA-376 / ISO/IEC 29500-1 §17.4.70)
_ORDEN_TCPR = (
    "cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge",
    "tcBorders", "shd", "noWrap", "tcMar", "textDirection",
    "tcFitText", "vAlign", "hideMark",
)


def _insertar_ordenado_tc(contenedor, nodo, etiqueta: str) -> None:
    """Inserta `nodo` en `tcPr` respetando el orden estricto del estándar OpenXML."""
    if etiqueta not in _ORDEN_TCPR:
        contenedor.append(nodo)
        return
    objetivo = _ORDEN_TCPR.index(etiqueta)
    for hijo in contenedor:
        nombre = hijo.tag.rsplit("}", 1)[-1]
        if nombre in _ORDEN_TCPR and _ORDEN_TCPR.index(nombre) > objetivo:
            hijo.addprevious(nodo)
            return
    contenedor.append(nodo)


def _sombrear(celda, hex_color: str) -> None:
    """Fondo de color para una celda."""
    tc_pr = celda._tc.get_or_add_tcPr()
    for shd_existente in tc_pr.findall(qn("w:shd")):
        tc_pr.remove(shd_existente)
    sombra = OxmlElement("w:shd")
    sombra.set(qn("w:val"), "clear")
    sombra.set(qn("w:fill"), hex_color)
    tc_pr.append(sombra)


def _bordes_tabla_estandar(tabla, hex_borde: str = "9CA3AF") -> None:
    """Bordes finos sobrios en todas las celdas."""
    tbl_pr = tabla._tbl.tblPr
    for b_antiguo in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(b_antiguo)
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        lado_xml = OxmlElement(f"w:{lado}")
        lado_xml.set(qn("w:val"), "single")
        lado_xml.set(qn("w:sz"), "4")
        lado_xml.set(qn("w:space"), "0")
        lado_xml.set(qn("w:color"), hex_borde)
        bordes.append(lado_xml)
    _insertar_ordenado(tbl_pr, bordes, "tblBorders")


def _bordes_tabla_tema1(tabla) -> None:
    """Clonación exacta de tema1.docx: bordes exteriores #999999 sin divisiones interiores."""
    tbl_pr = tabla._tbl.tblPr
    for b_antiguo in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(b_antiguo)
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "6")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "999999")
        bordes.append(b)
    for lado in ("insideH", "insideV"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "none")
        bordes.append(b)
    _insertar_ordenado(tbl_pr, bordes, "tblBorders")


def _bordes_tabla_tema2(tabla) -> None:
    """Clonación exacta de tema2.docx: bordes superior e inferior #111827 sin laterales."""
    tbl_pr = tabla._tbl.tblPr
    for b_antiguo in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(b_antiguo)
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "bottom"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "6")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "111827")
        bordes.append(b)
    for lado in ("left", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "none")
        bordes.append(b)
    _insertar_ordenado(tbl_pr, bordes, "tblBorders")


def _bordes_tabla_tema3(tabla) -> None:
    """Clonación exacta de tema3.docx: bordes exteriores y divisiones horizontales #BFBFBF y tblCellMar de 70 dxa."""
    tbl_pr = tabla._tbl.tblPr
    for b_antiguo in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(b_antiguo)
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "right", "bottom", "insideH", "insideV"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "BFBFBF")
        bordes.append(b)
    _insertar_ordenado(tbl_pr, bordes, "tblBorders")

    # tblCellMar de 70 dxa (0.05 in)
    for mar_antiguo in tbl_pr.findall(qn("w:tblCellMar")):
        tbl_pr.remove(mar_antiguo)
    tbl_cell_mar = OxmlElement("w:tblCellMar")
    for lado in ("left", "right"):
        m = OxmlElement(f"w:{lado}")
        m.set(qn("w:w"), "70")
        m.set(qn("w:type"), "dxa")
        tbl_cell_mar.append(m)
    _insertar_ordenado(tbl_pr, tbl_cell_mar, "tblCellMar")


def _bordes_tabla_apa(tabla, hex_borde: str = "111827") -> None:
    """Formato de tablas APA 7: solo bordes horizontales sup/inf/cabecera."""
    tbl_pr = tabla._tbl.tblPr
    for b_antiguo in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(b_antiguo)
    bordes = OxmlElement("w:tblBorders")

    # Borde superior e inferior de la tabla
    for lado in ("top", "bottom"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "8")  # 1 pt
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), hex_borde)
        bordes.append(b)

    # Separador de encabezado
    h_in = OxmlElement("w:insideH")
    h_in.set(qn("w:val"), "single")
    h_in.set(qn("w:sz"), "4")  # 0.5 pt
    h_in.set(qn("w:space"), "0")
    h_in.set(qn("w:color"), hex_borde)
    bordes.append(h_in)

    # Sin bordes verticales (estilo APA 7 estricto)
    for lado in ("left", "right", "insideV"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "none")
        bordes.append(b)

    _insertar_ordenado(tbl_pr, bordes, "tblBorders")


def _fijar_a4(documento, normas_apa: bool = False) -> None:
    """Fija tamaño de página y márgenes (A4 o APA 7 de 2.54 cm)."""
    for seccion in documento.sections:
        seccion.page_width = Mm(210)
        seccion.page_height = Mm(297)
        margen = Mm(25.4)
        seccion.top_margin = margen
        seccion.bottom_margin = margen
        seccion.left_margin = margen
        seccion.right_margin = margen


def _ancho_util_dxa(documento) -> int:
    """Ancho útil en dxa (twips)."""
    seccion = documento.sections[0]
    return int(
        seccion.page_width - seccion.left_margin - seccion.right_margin
    ) // 635


def _texto_celda(celda) -> str:
    """Texto de una celda incluyendo ecuaciones OMML."""
    partes: list[str] = []
    for parrafo in celda.paragraphs:
        for nodo in parrafo._p.iter():
            if nodo.tag in (qn("w:t"), qn("m:t")) and nodo.text:
                partes.append(nodo.text)
    return "".join(partes)


def _adaptar_ancho(tabla, util_dxa: int, tamanio: float) -> None:
    """Ancho adaptativo al número de columnas y contenido garantizando cuadrícula balanceada y estable en Word."""
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.autofit = False
    tbl = tabla._tbl
    tbl_pr = tbl.tblPr

    # Detección robusta del número real de columnas
    tbl_grid_prev = tbl.find(qn("w:tblGrid"))
    cols_grid = len(tbl_grid_prev.findall(qn("w:gridCol"))) if tbl_grid_prev is not None else 0
    cols_max_filas = max((len(fila.cells) for fila in tabla.rows), default=1)
    columnas = max(cols_grid, cols_max_filas, 1)

    # 1. Ponderación balanceada con amortiguación de textos largos
    # Evita que columnas con párrafos largos canibalicen y estrangulen a columnas vecinas
    pesos: list[int] = []
    for j in range(columnas):
        len_cabecera = len(_texto_celda(tabla.rows[0].cells[j])) if tabla.rows and j < len(tabla.rows[0].cells) else 4
        largo_max = 6
        for fila in tabla.rows:
            if j < len(fila.cells):
                largo_max = max(largo_max, len(_texto_celda(fila.cells[j])))
        # Amortiguación no lineal para textos largos (párrafos se leen verticalmente)
        if largo_max > 25:
            largo_amortiguado = 25 + int((largo_max - 25) ** 0.6)
        else:
            largo_amortiguado = largo_max
        pesos.append(max(len_cabecera, largo_amortiguado, 6))

    suma_pesos = sum(pesos)

    # 2. Ancho natural adaptativo (docs/mejoras/mejoras_app_01.md)
    # Evitar forzar el 100% de la hoja cuando la tabla tiene poco contenido o pocas columnas
    anchos_estimados = [max(950, int(p * 135 + 400)) for p in pesos]
    ancho_natural = sum(anchos_estimados)

    if ancho_natural < util_dxa:
        min_tabla_dxa = max(2800, int(util_dxa * 0.35))
        total_dxa = min(util_dxa, max(min_tabla_dxa, ancho_natural))
    else:
        total_dxa = util_dxa

    # Ancho mínimo garantizado por columna para que ninguna palabra quede estrangulada
    if columnas <= 5:
        min_col = max(850, int(total_dxa * 0.09))
    elif columnas <= 8:
        min_col = max(700, int(total_dxa * 0.07))
    else:
        min_col = max(550, int(total_dxa * 0.05))

    if suma_pesos > 0:
        reparto = [max(min_col, round(p * total_dxa / suma_pesos)) for p in pesos]
    else:
        reparto = [max(min_col, total_dxa // columnas)] * columnas

    # Ajuste exacto para que sum(reparto) == total_dxa invariablemente
    dif = total_dxa - sum(reparto)
    if reparto:
        # Repartir la diferencia entre las columnas más anchas para no afectar los mínimos
        idx_max = reparto.index(max(reparto))
        reparto[idx_max] += dif

    # 2. Propiedades de Tabla w:tblPr (SIEMPRE w:type="dxa", NUNCA pct)
    for etiqueta in ("w:tblW", "w:jc", "w:tblLayout", "w:tblCellMar", "w:tblInd"):
        for nodo in tbl_pr.findall(qn(etiqueta)):
            tbl_pr.remove(nodo)

    # Anular cualquier sangría de tabla para que no colapse ni se desplace fuera de márgenes
    ind = OxmlElement("w:tblInd")
    ind.set(qn("w:w"), "0")
    ind.set(qn("w:type"), "dxa")
    _insertar_ordenado(tbl_pr, ind, "tblInd")

    ancho = OxmlElement("w:tblW")
    ancho.set(qn("w:type"), "dxa")
    ancho.set(qn("w:w"), str(int(total_dxa)))
    _insertar_ordenado(tbl_pr, ancho, "tblW")

    centro = OxmlElement("w:jc")
    centro.set(qn("w:val"), "center")
    _insertar_ordenado(tbl_pr, centro, "jc")

    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    _insertar_ordenado(tbl_pr, layout, "tblLayout")

    # Cell padding uniforme y profesional
    cell_mar = OxmlElement("w:tblCellMar")
    for b_nombre, b_val in (("top", "120"), ("left", "160"), ("bottom", "120"), ("right", "160")):
        m_elem = OxmlElement(f"w:{b_nombre}")
        m_elem.set(qn("w:w"), b_val)
        m_elem.set(qn("w:type"), "dxa")
        cell_mar.append(m_elem)
    _insertar_ordenado(tbl_pr, cell_mar, "tblCellMar")

    # 3. Retícula explícita de columnas w:tblGrid
    tbl_grid = tbl.find(qn("w:tblGrid"))
    if tbl_grid is None:
        tbl_grid = OxmlElement("w:tblGrid")
        tbl_pr.addnext(tbl_grid)
    for hijo in list(tbl_grid):
        tbl_grid.remove(hijo)
    for valor in reparto:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(int(valor)))
        tbl_grid.append(col)

    # 4. Ancho explícito de cada celda física w:tc individual y control de salto de fila
    for fila_idx, tr in enumerate(tbl.findall(qn("w:tr"))):
        # Evitar cortes antiestéticos de fila entre páginas y repetir cabecera
        tr_pr = tr.find(qn("w:trPr"))
        if tr_pr is None:
            tr_pr = OxmlElement("w:trPr")
            tr.insert(0, tr_pr)
        if tr_pr.find(qn("w:cantSplit")) is None:
            tr_pr.append(OxmlElement("w:cantSplit"))
        if fila_idx == 0 and tr_pr.find(qn("w:tblHeader")) is None:
            tr_pr.append(OxmlElement("w:tblHeader"))

        col_idx = 0
        for tc in tr.findall(qn("w:tc")):
            tc_pr = tc.find(qn("w:tcPr"))
            if tc_pr is None:
                tc_pr = OxmlElement("w:tcPr")
                tc.insert(0, tc_pr)

            # Detectar si la celda tiene gridSpan (celda combinada)
            grid_span_elem = tc_pr.find(qn("w:gridSpan"))
            span = 1
            if grid_span_elem is not None:
                try:
                    span = max(1, int(grid_span_elem.get(qn("w:val")) or 1))
                except (ValueError, TypeError):
                    span = 1

            if col_idx < len(reparto):
                ancho_celda_dxa = sum(reparto[col_idx : col_idx + span])
            else:
                ancho_celda_dxa = max(min_col, total_dxa // columnas)

            for w_ant in tc_pr.findall(qn("w:tcW")):
                tc_pr.remove(w_ant)
            tc_w = OxmlElement("w:tcW")
            tc_w.set(qn("w:w"), str(int(ancho_celda_dxa)))
            tc_w.set(qn("w:type"), "dxa")
            _insertar_ordenado_tc(tc_pr, tc_w, "tcW")

            col_idx += span


def _calcular_tamanio_fuente_tabla(tabla, util_dxa: int, base: float) -> tuple[float, bool]:
    """Calcula el tamaño de fuente óptimo para que la tabla quepa en util_dxa con un mínimo de 7.0 pt."""
    columnas = max((len(fila.cells) for fila in tabla.rows), default=1)
    if columnas <= 1:
        return base, False

    # Reducción por densidad de columnas si excede 6 columnas
    t_por_cols = _tamanio_celda(base, columnas)

    # Medir la longitud de palabras máximas por columna para asegurar que quepan sin desborde
    max_palabras_col: list[int] = []
    for col_idx in range(columnas):
        max_pal = 3
        for fila in tabla.rows:
            if col_idx < len(fila.cells):
                txt = _texto_celda(fila.cells[col_idx])
                for p in txt.split():
                    max_pal = max(max_pal, len(p))
        max_palabras_col.append(max_pal)

    # Padding de celda w:tblCellMar izquierdo + derecho = 320 dxa
    padding_col_dxa = 320

    t_candidato = min(base, t_por_cols)
    while t_candidato > 7.0:
        ancho_estimado = sum(int(pal * t_candidato * 13 + padding_col_dxa) for pal in max_palabras_col)
        if ancho_estimado <= util_dxa:
            return round(t_candidato, 1), False
        t_candidato -= 0.5

    # Límite mínimo de 7.0 pt alcanzado
    ancho_en_7 = sum(int(pal * 7.0 * 13 + padding_col_dxa) for pal in max_palabras_col)
    alcanzo_minimo = ancho_en_7 > util_dxa
    return 7.0, alcanzo_minimo


def _tamanio_celda(base: float, columnas: int) -> float:
    if columnas <= 6:
        return base
    return max(7.0, round(base * 6.0 / columnas, 1))


def _barnizar_tabla(
    tabla,
    fuente: str,
    base: float,
    interlineado: float,
    util_dxa: int,
    normas_apa: bool = False,
    paleta_clave: str = "defecto",
    tema_word: str = "defecto",
    tamanio_tabla: float | None = None,
    fuente_tabla: str | None = None,
    paleta_suave_tablas: bool = True,
    color_tabla_cabecera: str = "",
    color_tabla_filas: str = "",
    color_tabla_borde: str = "",
) -> tuple[float, bool]:
    """Barniza una tabla clonando el diseño de temas_word o aplicando paleta suave y tamaño de fuente específico."""
    # Ignorar únicamente tablas de ecuaciones matemáticas OMML (1 fila x 2-3 columnas con m:oMath)
    if len(tabla.rows) == 1 and len(tabla.columns) in (2, 3):
        es_ecuacion = any(
            celda._tc.find(".//" + qn("m:oMath")) is not None
            for celda in tabla.rows[0].cells
        )
        if es_ecuacion:
            return base, False

    tema_clean = (tema_word or "").lower()
    es_nativo_tbl = tema_clean in ("tema1", "tema2", "tema3")

    # 1. Configuración de bordes y colores según tema nativo, normas APA, colores personalizados o paleta suave
    if es_nativo_tbl:
        if tema_clean == "tema1":
            _bordes_tabla_tema1(tabla)
            color_cabecera = "F2F2F2"
            color_filas = "FFFFFF"
        elif tema_clean == "tema2":
            _bordes_tabla_tema2(tabla)
            color_cabecera = "F8FAFC"
            color_filas = "FFFFFF"
        else:
            _bordes_tabla_tema3(tabla)
            color_cabecera = "4F81BD"
            color_filas = "F2F2F2"
    elif normas_apa:
        paleta = PALETAS_TABLA.get(paleta_clave, PALETAS_TABLA["defecto"])
        _bordes_tabla_apa(tabla, paleta["border"])
        color_cabecera = paleta["header_bg"]
        color_filas = paleta["row_alt"]
    elif "|" in (paleta_clave or ""):
        partes_p = [p.strip().lstrip("#").upper() for p in paleta_clave.split("|")]
        c_cab = partes_p[0] if len(partes_p) > 0 and len(partes_p[0]) == 6 else "1E293B"
        c_fil = partes_p[2] if len(partes_p) > 2 and len(partes_p[2]) == 6 else (partes_p[1] if len(partes_p) > 1 and len(partes_p[1]) == 6 else "F1F5F9")
        c_bor = partes_p[4] if len(partes_p) > 4 and len(partes_p[4]) == 6 else "CBD5E1"
        _bordes_tabla_estandar(tabla, c_bor)
        color_cabecera = c_cab
        color_filas = c_fil
    elif color_tabla_cabecera or color_tabla_filas:
        c_cab = color_tabla_cabecera.strip().lstrip("#").upper() if color_tabla_cabecera else "1E293B"
        c_fil = color_tabla_filas.strip().lstrip("#").upper() if color_tabla_filas else "F1F5F9"
        c_bor = color_tabla_borde.strip().lstrip("#").upper() if color_tabla_borde else "CBD5E1"
        _bordes_tabla_estandar(tabla, c_bor)
        color_cabecera = c_cab
        color_filas = c_fil
    else:
        paleta = PALETAS_TABLA.get(paleta_clave, PALETAS_TABLA["defecto"])
        _bordes_tabla_estandar(tabla, paleta["border"])
        color_cabecera = paleta["header_bg"]
        color_filas = paleta["row_alt"]

    columnas = len(tabla.columns) or 1
    # Reducción adaptativa de fuente hasta mínimo 7 pt si la tabla es ancha
    if tamanio_tabla is not None and float(tamanio_tabla) > 0:
        tamanio = float(tamanio_tabla)
        llego_minimo = False
    else:
        tamanio, llego_minimo = _calcular_tamanio_fuente_tabla(tabla, util_dxa, base)

    # Fuente específica para tablas si fue configurada
    fuente_efectiva = (
        fuente_tabla
        if (fuente_tabla and fuente_tabla.lower() not in ("heredar", "auto", ""))
        else fuente
    )

    _adaptar_ancho(tabla, util_dxa, tamanio)

    # Interlineado de celdas: siempre 1.0 (sencillo) salvo en la opción APA
    inter_celda = interlineado if normas_apa else 1.0

    for fila_index, fila in enumerate(tabla.rows):
        es_cabecera = fila_index == 0
        fill_color = color_cabecera if es_cabecera else (
            color_filas if fila_index % 2 == 1 else "FFFFFF"
        )
        for celda in fila.cells:
            _sombrear(celda, fill_color)

            # Borde inferior en celda de cabecera para resaltar la columna
            if es_cabecera:
                tcPr = celda._tc.get_or_add_tcPr()
                tcBorders = tcPr.find(qn("w:tcBorders"))
                if tcBorders is None:
                    tcBorders = OxmlElement("w:tcBorders")
                    tcPr.append(tcBorders)
                b_bot = OxmlElement("w:bottom")
                b_bot.set(qn("w:val"), "single")
                b_bot.set(qn("w:sz"), "8" if tema_clean == "tema3" else "6")
                b_bot.set(qn("w:space"), "0")
                b_bot.set(qn("w:color"), "BFBFBF" if tema_clean == "tema3" else ("111827" if tema_clean == "tema2" else "999999"))
                tcBorders.append(b_bot)

            for parrafo in celda.paragraphs:
                parrafo.paragraph_format.line_spacing = inter_celda
                parrafo.paragraph_format.first_line_indent = Pt(0)
                parrafo.paragraph_format.left_indent = Pt(0)
                parrafo.paragraph_format.right_indent = Pt(0)
                parrafo.paragraph_format.space_before = Pt(0)
                if not normas_apa:
                    parrafo.paragraph_format.space_after = Pt(2.0)

                # En Tema 3, la cabecera es centrada
                if es_cabecera and tema_clean == "tema3":
                    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_pr = parrafo._p.get_or_add_pPr()
                    jc = p_pr.find(qn("w:jc"))
                    if jc is None:
                        jc = OxmlElement("w:jc")
                        p_pr.append(jc)
                    jc.set(qn("w:val"), "center")

                for run in parrafo.runs:
                    run.font.name = fuente_efectiva
                    run.font.size = Pt(tamanio)
                    if es_cabecera:
                        run.bold = True
                        try:
                            r_c = int(color_cabecera[0:2], 16)
                            g_c = int(color_cabecera[2:4], 16)
                            b_c = int(color_cabecera[4:6], 16)
                            luminancia = r_c * 0.299 + g_c * 0.587 + b_c * 0.114
                            if luminancia < 145:
                                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                            else:
                                run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
                        except Exception:
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    else:
                        if tema_clean == "tema3":
                            run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

    return tamanio, llego_minimo


def _insertar_toc_e_indice_ecuaciones(
    documento,
    posicion: str = "inicio",
    con_indice_ecuaciones: bool = False,
    ecuaciones_info: list[str] | None = None,
    rgb_titulo: RGBColor | None = None,
    hex_titulo: str = "000000",
) -> None:
    """Inserta la Tabla de Contenidos real (TOC) y el Índice de Ecuaciones en la posición elegida."""
    # 1. Habilitar actualización automática de campos en Word (settings.xml)
    settings = documento.settings.element
    w_update = settings.find(qn("w:updateFields"))
    if w_update is None:
        w_update = OxmlElement("w:updateFields")
        w_update.set(qn("w:val"), "true")
        settings.append(w_update)

    def _crear_titulo_seguro(texto_tit: str, p_ref=None, al_final: bool = False):
        if al_final:
            p = documento.add_paragraph()
        elif p_ref is not None:
            p = p_ref.insert_paragraph_before()
        else:
            p = documento.add_paragraph()

        # No usar 'Heading 1' para no auto-incluir el título dentro del propio TOC
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(texto_tit)
        r.bold = True
        r.font.name = "Calibri"
        r.font.size = Pt(14)
        if rgb_titulo is not None:
            r.font.color.rgb = rgb_titulo
            rPr = r._r.get_or_add_rPr()
            for c in rPr.findall(qn("w:color")):
                rPr.remove(c)
            nuevo_c = OxmlElement("w:color")
            nuevo_c.set(qn("w:val"), hex_titulo)
            rPr.append(nuevo_c)
        else:
            r.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
        return p

    if posicion == "final":
        # Purgar párrafos vacíos trailing dejados por pandoc para evitar páginas en blanco
        while documento.paragraphs:
            ult = documento.paragraphs[-1]
            if not ult.text.strip() and not ult._p.findall(".//" + qn("w:drawing")):
                p_padre = ult._p.getparent()
                if p_padre is not None:
                    p_padre.remove(ult._p)
                else:
                    break
            else:
                break

        p_tit = _crear_titulo_seguro("Tabla de Contenidos", al_final=True)
        p_tit.paragraph_format.page_break_before = True
        p_toc = documento.add_paragraph()
    else:
        p_primero = documento.paragraphs[0] if documento.paragraphs else documento.add_paragraph()
        _crear_titulo_seguro("Tabla de Contenidos", p_ref=p_primero)
        p_toc = p_primero.insert_paragraph_before()

    # Inyección de campo nativo de TOC como hijo directo del párrafo w:p
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), r'TOC \o "1-3" \h \z \u')
    p_toc._p.append(fld)

    # Entradas visibles inmediatas de TOC para compatibilidad con todos los visores de OpenXML
    titulos_doc = []
    for p_doc in documento.paragraphs:
        nom_est = (p_doc.style.name or "").lower() if p_doc.style else ""
        if any(h in nom_est for h in ("heading 1", "título 1", "titulo 1", "heading 2", "título 2", "titulo 2", "heading 3", "título 3", "titulo 3")):
            txt_t = p_doc.text.strip()
            if txt_t and txt_t.lower() not in ("tabla de contenidos", "índice de ecuaciones", "índice de figuras"):
                nivel = 1 if "1" in nom_est else (2 if "2" in nom_est else 3)
                titulos_doc.append((nivel, txt_t))

    for idx_t, (nivel, txt_t) in enumerate(titulos_doc, 1):
        if posicion == "final":
            p_item = documento.add_paragraph()
        else:
            p_item = p_primero.insert_paragraph_before()

        if nivel == 2:
            p_item.paragraph_format.left_indent = Inches(0.25)
        elif nivel == 3:
            p_item.paragraph_format.left_indent = Inches(0.5)

        r_tit = p_item.add_run(txt_t)
        r_tit.font.size = Pt(10.5 if nivel == 1 else 9.5)
        if nivel == 1:
            r_tit.bold = True
            r_tit.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
        else:
            r_tit.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)

        p_item.paragraph_format.tab_stops.add_tab_stop(Inches(6.2), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        pag_est = max(1, (idx_t // 2) + 1)
        r_tab = p_item.add_run(f"\t{pag_est}")
        r_tab.font.size = Pt(9.5)
        r_tab.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    # 2. Índice de Ecuaciones Automático (inmediatamente después del TOC)
    if con_indice_ecuaciones and ecuaciones_info:
        if posicion == "final":
            _crear_titulo_seguro("Índice de Ecuaciones", al_final=True)
        else:
            _crear_titulo_seguro("Índice de Ecuaciones", p_ref=p_primero)

        for idx, resumen in enumerate(ecuaciones_info, 1):
            if posicion == "final":
                p_item = documento.add_paragraph()
            else:
                p_item = p_primero.insert_paragraph_before()

            r_num = p_item.add_run(f"Ecuación ({idx}): ")
            r_num.bold = True
            r_res = p_item.add_run(f"{resumen} ")
            r_res.font.color.rgb = RGBColor(0x37, 0x41, 0x51)
            p_item.paragraph_format.tab_stops.add_tab_stop(Inches(6.2), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            r_tab = p_item.add_run(f"\t({idx})")
            r_tab.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    # 3. Índice de Figuras (TOC \h \z \c "Figura" e inserción de figuras detectadas)
    figuras_detectadas: list[str] = []
    for p in documento.paragraphs:
        txt = p.text.strip()
        tiene_drawing = bool(p._p.findall(".//" + qn("w:drawing")))
        es_rotulo_fig = txt.lower().startswith("figura") or txt.lower().startswith("fig.")
        if tiene_drawing or es_rotulo_fig:
            figuras_detectadas.append(txt if txt else f"Figura {len(figuras_detectadas) + 1}")

    if posicion == "final":
        _crear_titulo_seguro("Índice de Figuras", al_final=True)
        p_toc_fig = documento.add_paragraph()
    else:
        _crear_titulo_seguro("Índice de Figuras", p_ref=p_primero)
        p_toc_fig = p_primero.insert_paragraph_before()

    if figuras_detectadas:
        for idx, f_nom in enumerate(figuras_detectadas, 1):
            if posicion == "final":
                p_fig = documento.add_paragraph()
            else:
                p_fig = p_primero.insert_paragraph_before()

            r_fnum = p_fig.add_run(f"Figura {idx}: ")
            r_fnum.bold = True
            r_fres = p_fig.add_run(f"{f_nom} ")
            r_fres.font.color.rgb = RGBColor(0x37, 0x41, 0x51)
            p_fig.paragraph_format.tab_stops.add_tab_stop(Inches(6.2), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            r_ftab = p_fig.add_run(f"\t({idx})")
            r_ftab.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)
    else:
        fld_fig = OxmlElement("w:fldSimple")
        fld_fig.set(qn("w:instr"), r'TOC \h \z \c "Figura"')
        p_toc_fig._p.append(fld_fig)

    # Si fue al inicio, insertar salto de página tras todos los índices
    if posicion == "inicio":
        p_primero.insert_paragraph_before().add_run().add_break(docx.enum.text.WD_BREAK.PAGE)


def _configurar_pie_pagina(
    documento,
    texto_pie: str = "",
    numerar: bool = True,
    fuente: str = "Calibri",
    alineacion: str = "derecha",
) -> None:
    """Configura el pie de página respetando la alineación seleccionada."""
    alin_map = {
        "izquierda": WD_ALIGN_PARAGRAPH.LEFT,
        "centro": WD_ALIGN_PARAGRAPH.CENTER,
        "centrado": WD_ALIGN_PARAGRAPH.CENTER,
        "derecha": WD_ALIGN_PARAGRAPH.RIGHT,
    }
    alin_seleccionada = alin_map.get(alineacion.lower(), WD_ALIGN_PARAGRAPH.RIGHT)

    for seccion in documento.sections:
        footer = seccion.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.alignment = alin_seleccionada

        if texto_pie.strip():
            r_txt = p.add_run(texto_pie.strip())
            r_txt.font.name = fuente
            r_txt.font.size = Pt(9.0)
            r_txt.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

        if numerar:
            if texto_pie.strip():
                p.add_run("   |   ")
            r_pag = p.add_run("Página ")
            r_pag.font.name = fuente
            r_pag.font.size = Pt(9.0)
            r_pag.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

            fld_num = OxmlElement("w:fldSimple")
            fld_num.set(qn("w:instr"), "PAGE")
            p.add_run()._r.append(fld_num)


def _numerar_ecuaciones_omml(documento, util_dxa: int) -> list[str]:
    """Numera las ecuaciones OMML en bloque colocándolas en tabla 1x2 de ancho útil sin bordes.

    La fórmula queda en la celda 0 centrada y la numeración en la celda 1 alineada estrictamente
    al margen derecho del documento.
    Descarta viñetas, listas y párrafos de definiciones explicativas ('Donde:').
    """
    contador = 0
    resumenes: list[str] = []
    parrafos_a_procesar: list[tuple[object, object]] = []

    for p in documento.paragraphs:
        # Descartar listas y viñetas
        if _es_lista(p):
            continue

        # Descartar párrafos que inicien con "donde:"
        txt_limpio = p.text.strip().lower()
        if txt_limpio.startswith("donde:") or txt_limpio == "donde":
            continue

        # Localizar ecuación en bloque
        omaths_para = p._p.findall(".//" + qn("m:oMathPara"))
        omaths_single = p._p.findall(".//" + qn("m:oMath"))

        nodo_formula = None
        if omaths_para:
            nodo_formula = omaths_para[0]
        elif omaths_single:
            # Solo si no hay texto ordinario fuera de la fórmula (ecuación en bloque pura)
            textos_w = [t.text for t in p._p.findall(".//" + qn("w:t")) if t.text and t.text.strip()]
            if not textos_w:
                nodo_formula = omaths_single[0]

        if nodo_formula is not None:
            parrafos_a_procesar.append((p, nodo_formula))

    for p, nodo_formula in parrafos_a_procesar:
        contador += 1
        # Extraer texto de la fórmula para el índice
        tex_nodes = [t.text for t in nodo_formula.iter() if t.tag in (qn("w:t"), qn("m:t")) and t.text]
        formula_str = "".join(tex_nodes).strip()
        resumen = (formula_str[:45] + "...") if len(formula_str) > 45 else (formula_str or f"Ecuación {contador}")
        resumenes.append(resumen)

        # Crear tabla invisible de 1 fila x 3 columnas para centrado geométrico simétrico (15% - 70% - 15%)
        tbl = documento.add_table(rows=1, cols=3)
        tbl_pr = tbl._tbl.tblPr

        # tblW 100% util_dxa
        for nodo_w in tbl_pr.findall(qn("w:tblW")):
            tbl_pr.remove(nodo_w)
        ancho_tbl = OxmlElement("w:tblW")
        ancho_tbl.set(qn("w:w"), str(util_dxa))
        ancho_tbl.set(qn("w:type"), "dxa")
        _insertar_ordenado(tbl_pr, ancho_tbl, "tblW")

        # Sin bordes
        for b_antiguo in tbl_pr.findall(qn("w:tblBorders")):
            tbl_pr.remove(b_antiguo)
        bordes = OxmlElement("w:tblBorders")
        for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
            b = OxmlElement(f"w:{lado}")
            b.set(qn("w:val"), "none")
            bordes.append(b)
        _insertar_ordenado(tbl_pr, bordes, "tblBorders")

        # tblCellMar 0 para alineación exacta al margen
        tbl_cell_mar = OxmlElement("w:tblCellMar")
        for lado in ("top", "bottom", "left", "right"):
            m = OxmlElement(f"w:{lado}")
            m.set(qn("w:w"), "0")
            m.set(qn("w:type"), "dxa")
            tbl_cell_mar.append(m)
        _insertar_ordenado(tbl_pr, tbl_cell_mar, "tblCellMar")

        # Sin fondo ni marcos en ningún tema: transparente 100%
        for s_antiguo in tbl_pr.findall(qn("w:shd")):
            tbl_pr.remove(s_antiguo)

        # Ancho simétrico de columnas: 15% (izq), 70% (centro), 15% (der)
        w_lateral = int(round(util_dxa * 0.15))
        w_centro = util_dxa - (2 * w_lateral)

        celda_izq = tbl.rows[0].cells[0]
        celda_eq = tbl.rows[0].cells[1]
        celda_num = tbl.rows[0].cells[2]

        for c in (celda_izq, celda_eq, celda_num):
            tc_pr = c._tc.get_or_add_tcPr()
            for s in tc_pr.findall(qn("w:shd")):
                tc_pr.remove(s)
            sombra = OxmlElement("w:shd")
            sombra.set(qn("w:val"), "clear")
            sombra.set(qn("w:color"), "auto")
            sombra.set(qn("w:fill"), "none")
            tc_pr.append(sombra)

            # Centrado vertical en cada celda
            v_align = tc_pr.find(qn("w:vAlign"))
            if v_align is None:
                v_align = OxmlElement("w:vAlign")
                tc_pr.append(v_align)
            v_align.set(qn("w:val"), "center")

        # Celda Izquierda: vacía (contrapeso simétrico)
        p_izq = celda_izq.paragraphs[0]
        p_izq.text = ""

        # Celda Central (Ecuación): centrada horizontal y verticalmente
        p_eq = celda_eq.paragraphs[0]
        p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_eq_pr = p_eq._p.get_or_add_pPr()
        jc_eq = p_eq_pr.find(qn("w:jc"))
        if jc_eq is None:
            jc_eq = OxmlElement("w:jc")
            p_eq_pr.append(jc_eq)
        jc_eq.set(qn("w:val"), "center")
        # Cumplimiento estricto del estándar Open XML: dentro de un párrafo (w:p),
        # insertar directamente los elementos m:oMath. Si nodo_formula es m:oMathPara,
        # extraer sus hijos m:oMath para evitar anidar m:oMathPara dentro de w:p,
        # lo que causaba que en algunas versiones de Word no se vieran las fórmulas.
        if nodo_formula.tag.endswith("oMathPara"):
            sub_omaths = list(nodo_formula.findall(qn("m:oMath")))
            if sub_omaths:
                for om in sub_omaths:
                    p_eq._p.append(om)
            else:
                p_eq._p.append(nodo_formula)
        else:
            p_eq._p.append(nodo_formula)

        # Celda Derecha (Número): estrictamente a la derecha con número y campo nativo SEQ Equation
        p_num = celda_num.paragraphs[0]
        p_num.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_num_pr = p_num._p.get_or_add_pPr()
        jc_num = p_num_pr.find(qn("w:jc"))
        if jc_num is None:
            jc_num = OxmlElement("w:jc")
            p_num_pr.append(jc_num)
        jc_num.set(qn("w:val"), "right")

        r_abrir = p_num.add_run("(")
        r_abrir.font.name = "Calibri"
        r_abrir.font.size = Pt(10)
        r_abrir.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)

        fld_eq = OxmlElement("w:fldSimple")
        fld_eq.set(qn("w:instr"), r'SEQ Equation \* ARABIC')
        r_fld_inner = OxmlElement("w:r")
        rPr_inner = OxmlElement("w:rPr")
        rFonts_inner = OxmlElement("w:rFonts")
        rFonts_inner.set(qn("w:ascii"), "Calibri")
        rFonts_inner.set(qn("w:hAnsi"), "Calibri")
        rPr_inner.append(rFonts_inner)
        sz_inner = OxmlElement("w:sz")
        sz_inner.set(qn("w:val"), "20")
        rPr_inner.append(sz_inner)
        color_inner = OxmlElement("w:color")
        color_inner.set(qn("w:val"), "4B5563")
        rPr_inner.append(color_inner)
        r_fld_inner.append(rPr_inner)
        t_fld_inner = OxmlElement("w:t")
        t_fld_inner.text = str(contador)
        r_fld_inner.append(t_fld_inner)
        fld_eq.append(r_fld_inner)

        # En OpenXML, w:fldSimple se agrega como hijo directo de w:p, NO dentro de un w:r
        p_num._p.append(fld_eq)

        r_cerrar = p_num.add_run(")")
        r_cerrar.font.name = "Calibri"
        r_cerrar.font.size = Pt(10)
        r_cerrar.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)

        # Establecer anchos de celdas
        celda_izq.width = Emu(w_lateral * 635)
        celda_eq.width = Emu(w_centro * 635)
        celda_num.width = Emu(w_lateral * 635)

        # Mover la tabla a la posición del párrafo original y eliminar el párrafo antiguo
        p._p.addprevious(tbl._tbl)
        p_parent = p._p.getparent()
        if p_parent is not None:
            p_parent.remove(p._p)

    return resumenes


def _es_lista(parrafo) -> bool:
    """Determina si un párrafo corresponde a una lista o viñeta."""
    nombre_estilo = (parrafo.style.name or "").lower() if parrafo.style else ""
    if any(k in nombre_estilo for k in ("bullet", "list", "número", "numero", "item")):
        return True
    if parrafo._p.find(".//" + qn("w:numPr")) is not None:
        return True
    texto = parrafo.text.lstrip()
    if re.match(r"^[-*+•]\s+", texto) or re.match(r"^\d+[.)]\s+", texto):
        return True
    return False


def _es_nota(parrafo) -> bool:
    """Determina si un párrafo es una nota, cita o callout.
    
    Regla estricta: Las listas con viñetas y los descriptores 'Donde:' NUNCA son notas.
    """
    if _es_lista(parrafo):
        return False
    texto = parrafo.text.strip()
    txt_low = texto.lower()
    if txt_low.startswith("donde:") or txt_low == "donde":
        return False
    nombre_estilo = (parrafo.style.name or "").lower() if parrafo.style else ""
    if any(k in nombre_estilo for k in ("quote", "block", "nota", "cita")):
        return True
    prefijos_nota = ("> ", "[!NOTE]", "[!NOTA]", "[!TIP]", "[!CONSEJO]", "[!IMPORTANT]", "[!IMPORTANTE]", "[!WARNING]", "[!ADVERTENCIA]", "[!CAUTION]")
    return any(texto.startswith(p) for p in prefijos_nota)


def _barnizar_nota(
    parrafo,
    color_borde: str = "999999",
    color_fondo: str = "F8FAFC",
    alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY,
    es_tema1: bool = False,
) -> None:
    """Aplica formato visual de nota ejecutiva: barra lateral, sombreado y sangría."""
    pPr = parrafo._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    for hijo in list(pBdr):
        pBdr.remove(hijo)
    b_left = OxmlElement("w:left")
    b_left.set(qn("w:val"), "single")
    # Tema 1 usa sz="12" (1.5pt) y space="8"; otros temas usan sz="24" (3pt)
    b_left.set(qn("w:sz"), "12" if es_tema1 else "24")
    b_left.set(qn("w:space"), "8" if es_tema1 else "10")
    b_left.set(qn("w:color"), color_borde)
    pBdr.append(b_left)

    shd = pPr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        pPr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    # En tema1.docx las notas tienen fondo blanco o sin relleno ("auto")
    shd.set(qn("w:fill"), "FFFFFF" if es_tema1 else color_fondo)

    # Sangrías exactas: tema1 usa left=576 (0.4 in), right=432 (0.3 in)
    if es_tema1:
        parrafo.paragraph_format.left_indent = Inches(0.4)
        parrafo.paragraph_format.right_indent = Inches(0.3)
    else:
        parrafo.paragraph_format.left_indent = Inches(0.25)
        parrafo.paragraph_format.right_indent = Inches(0.15)

    parrafo.paragraph_format.space_before = Pt(4.0)
    parrafo.paragraph_format.space_after = Pt(4.0)
    # Justificación obligatoria en todas las notas de todos los temas
    parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    jc = pPr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        pPr.append(jc)
    jc.set(qn("w:val"), "both")

    # Limpieza de etiquetas parásitas [!NOTE], [!NOTA], etc. en los runs del párrafo
    patron_nota = re.compile(
        r"^\s*\[!(?:NOTE|NOTA|TIP|CONSEJO|IMPORTANT|IMPORTANTE|WARNING|ADVERTENCIA|CAUTION)\]\s*",
        re.IGNORECASE,
    )
    for run in parrafo.runs:
        if run.text:
            run.text = patron_nota.sub("", run.text)


def _barnizar(
    destino: Path,
    titulo: str,
    fuente: str,
    tamanio: float,
    interlineado: float,
    alineacion: str,
    normas_apa: bool = False,
    paleta_clave: str = "defecto",
    tema_word: str = "defecto",
    color_titulos_word: str = "negro",
    numerar_ecuaciones: bool = False,
    crear_indice: bool = False,
    posicion_indice: str = "inicio",
    pie_pagina: str = "",
    alineacion_pie: str = "derecha",
    numerar_paginas: bool = False,
    es_tema_nativo: bool = False,
    tamanio_tabla: float | None = None,
    fuente_tabla: str | None = None,
    modo_color_titulos: str = "auto",
    paleta_suave_tablas: bool = True,
    color_tabla_cabecera: str = "",
    color_tabla_filas: str = "",
    color_tabla_borde: str = "",
    color_tit_h1: str = "",
    color_tit_h2: str = "",
) -> None:
    """Ajusta tipografía, normas APA 7, tablas, viñetas, notas y estructura documental."""
    documento = Document(str(destino))
    documento.core_properties.title = titulo
    _fijar_a4(documento, normas_apa=normas_apa)
    util_dxa = _ancho_util_dxa(documento)
    alin = _ALINEACIONES.get(alineacion, WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Forzar actualización de campos dinámicos (TOC y SEQ) al abrir en Word
    try:
        settings_elem = documento.settings.element
        for up in settings_elem.findall(qn("w:updateFields")):
            settings_elem.remove(up)
        update_fields = OxmlElement("w:updateFields")
        update_fields.set(qn("w:val"), "true")
        settings_elem.append(update_fields)
    except Exception:
        pass

    # Colores para notas y títulos según tema
    tema_clean = (tema_word or "").lower()
    es_tema1 = tema_clean == "tema1"
    es_tema3 = tema_clean == "tema3"

    if es_tema3:
        color_nota_borde = "1F497D"
        color_nota_fondo = "F1F5F9"
    elif tema_clean == "tema2":
        color_nota_borde = "111827"
        color_nota_fondo = "F8FAFC"
    else:
        color_nota_borde = "999999"
        color_nota_fondo = "F8FAFC"

    # Resolución de modo de color de títulos (Negro vs Paleta de 3 colores vs Personalizado)
    modo_norm = (modo_color_titulos or "auto").strip().lower()
    color_norm = (color_titulos_word or "").strip().lower()

    if modo_norm in ("personalizado", "custom"):
        es_modo_negro = False
    elif modo_norm in ("paleta", "color", "usar color de la paleta", "usar_color_de_la_paleta"):
        es_modo_negro = False
    elif modo_norm in ("negro", "black", "todos_negro", "todos en negro", "todos_en_negro") or color_norm in ("negro", "000000", "#000000", "negro_absoluto"):
        es_modo_negro = True
    elif color_norm not in ("negro", "000000", "#000000", ""):
        es_modo_negro = False
    else:
        es_modo_negro = True

    pal_titulos = _obtener_paleta_titulos_3c(color_titulos_word)

    if es_modo_negro:
        rgb_h1 = rgb_h2 = rgb_h3 = RGBColor(0x00, 0x00, 0x00)
        hex_h1 = hex_h2 = hex_h3 = "000000"
    else:
        rgb_h1 = pal_titulos["primario_rgb"]
        hex_h1 = pal_titulos["primario_hex"]
        rgb_h2 = pal_titulos["secundario_rgb"]
        hex_h2 = pal_titulos["secundario_hex"]
        rgb_h3 = pal_titulos["secundario_rgb"]
        hex_h3 = pal_titulos["secundario_hex"]

        # Si se especificaron colores de títulos personalizados explícitos (Pickers / Paleta Custom)
        if color_tit_h1 and color_tit_h1.strip().lstrip("#") not in ("000000", ""):
            c1 = color_tit_h1.strip().lstrip("#").upper()
            if len(c1) == 6:
                try:
                    rgb_h1 = RGBColor(int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16))
                    hex_h1 = c1
                except Exception:
                    pass
        if color_tit_h2 and color_tit_h2.strip().lstrip("#") not in ("000000", ""):
            c2 = color_tit_h2.strip().lstrip("#").upper()
            if len(c2) == 6:
                try:
                    rgb_h2 = rgb_h3 = RGBColor(int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16))
                    hex_h2 = hex_h3 = c2
                except Exception:
                    pass

    # Color de acento para notas / llamadas si no es tema nativo
    if not es_tema_nativo and not es_modo_negro and pal_titulos.get("acento_hex"):
        color_nota_borde = pal_titulos["acento_hex"]

    # Actualizar estilos en styles.xml para asegurar que toda la jerarquía sea homogénea
    if not es_tema_nativo:
        for s in documento.styles:
            nom_s = (s.name or "").lower()
            if any(k in nom_s for k in ("heading", "título", "titulo", "title", "subtitle", "subtítulo", "subtitulo", "toc", "abstract")):
                c_rgb = rgb_h1 if any(k in nom_s for k in ("1", "title", "titulo")) else rgb_h2
                c_hex = hex_h1 if any(k in nom_s for k in ("1", "title", "titulo")) else hex_h2
                try:
                    s.font.color.rgb = c_rgb
                except Exception:
                    pass
                for c in s.element.xpath(".//w:color"):
                    c.set(qn("w:val"), c_hex)

    # Limpiar sangrías heredadas en estilo Normal y fijar alineación base en estilos de cuerpo
    jc_val_cuerpo = _MAPA_JC_VAL.get((alineacion or "justificado").lower(), "both")
    for nom_st_base in ("Normal", "Body Text", "First Paragraph"):
        if nom_st_base in documento.styles:
            st_base = documento.styles[nom_st_base]
            st_base.paragraph_format.left_indent = Pt(0)
            st_base.paragraph_format.right_indent = Pt(0)
            if not normas_apa:
                st_base.paragraph_format.first_line_indent = Pt(0)
            st_base.paragraph_format.alignment = alin
            pPr_st = st_base.element.get_or_add_pPr()
            jc_st = pPr_st.find(qn("w:jc"))
            if jc_st is None:
                jc_st = OxmlElement("w:jc")
                pPr_st.append(jc_st)
            jc_st.set(qn("w:val"), jc_val_cuerpo)

    for parrafo in documento.paragraphs:
        parrafo.paragraph_format.line_spacing = interlineado
        # Espaciado posterior compacto cuando el interlineado es sencillo (1.0)
        if interlineado <= 1.05:
            parrafo.paragraph_format.space_after = Pt(2.0)

        # Figuras centradas
        if parrafo._p.findall(".//" + qn("w:drawing")):
            parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            continue

        nom_est = (parrafo.style.name or "").lower() if parrafo.style else ""
        es_titulo = any(
            k in nom_est for k in (
                "heading", "título", "titulo", "title", "subtitle", "subtítulo", "subtitulo"
            )
        )
        es_lista = _es_lista(parrafo)
        es_nota = _es_nota(parrafo)
        txt_p = parrafo.text.strip().lower()
        es_donde = txt_p.startswith("donde:") or txt_p == "donde"

        if es_titulo:
            # Configuración de títulos según normas APA o clonación Tema 3
            if normas_apa:
                if "1" in nom_est:
                    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif es_tema3:
                # Tema 3 exacto: H1 16pt (sz=32), H2 14pt (sz=28), H3 12pt (sz=24), color #0F4761
                parrafo.paragraph_format.space_after = Pt(2.0)
                tam_t3 = 16.0 if "1" in nom_est else (14.0 if "2" in nom_est else 12.0)
                for run in parrafo.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(tam_t3)
                    run.bold = True
                    run.font.color.rgb = RGBColor(0x0F, 0x47, 0x61)
                    rPr = run._r.get_or_add_rPr()
                    for c in rPr.findall(qn("w:color")):
                        rPr.remove(c)
                    nuevo_c = OxmlElement("w:color")
                    nuevo_c.set(qn("w:val"), "0F4761")
                    rPr.append(nuevo_c)
            elif es_tema_nativo:
                # Tema 1 y Tema 2 nativos: títulos sobrios en negro/gris carbón de su plantilla
                tam_nat = (15.0 if "1" in nom_est else (14.0 if "2" in nom_est else 12.0)) if es_tema1 else (13.0 if "1" in nom_est else (12.0 if "2" in nom_est else 11.0))
                for run in parrafo.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(tam_nat)
                    run.bold = True
                    run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
                    rPr = run._r.get_or_add_rPr()
                    for c in rPr.findall(qn("w:color")):
                        rPr.remove(c)
                    nuevo_c = OxmlElement("w:color")
                    nuevo_c.set(qn("w:val"), "111827")
                    rPr.append(nuevo_c)
            elif not es_tema_nativo:
                if "1" in nom_est:
                    c_rgb_run, c_hex_run = rgb_h1, hex_h1
                elif "2" in nom_est:
                    c_rgb_run, c_hex_run = rgb_h2, hex_h2
                else:
                    c_rgb_run, c_hex_run = rgb_h3, hex_h3

                for run in parrafo.runs:
                    run.font.color.rgb = c_rgb_run
                    rPr = run._r.get_or_add_rPr()
                    for c in rPr.findall(qn("w:color")):
                        rPr.remove(c)
                    nuevo_c = OxmlElement("w:color")
                    nuevo_c.set(qn("w:val"), c_hex_run)
                    rPr.append(nuevo_c)
        elif es_lista or es_donde:
            # REGLA INQUEBRANTABLE: Toda viñeta o número SIEMPRE alineada a la izquierda y sin bordes/fondos de nota
            parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pPr = parrafo._p.get_or_add_pPr()
            jc = pPr.find(qn("w:jc"))
            if jc is None:
                jc = OxmlElement("w:jc")
                pPr.append(jc)
            jc.set(qn("w:val"), "left")
            parrafo.paragraph_format.first_line_indent = Pt(0)
            # Limpiar bordes o sombreados de notas para evitar contaminación
            pBdr = pPr.find(qn("w:pBdr"))
            if pBdr is not None:
                pPr.remove(pBdr)
            shd = pPr.find(qn("w:shd"))
            if shd is not None:
                pPr.remove(shd)
        elif es_nota:
            _barnizar_nota(
                parrafo,
                color_borde=color_nota_borde,
                color_fondo=color_nota_fondo,
                alineacion=alin,
                es_tema1=es_tema1,
            )
        elif bool(parrafo._p.xpath('.//w:drawing') or parrafo._p.xpath('.//w:pict')):
            # Centrado estricto de figuras y diagramas Mermaid sin sangría parásita
            parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            parrafo.paragraph_format.left_indent = Pt(0)
            parrafo.paragraph_format.right_indent = Pt(0)
            parrafo.paragraph_format.first_line_indent = Pt(0)
            parrafo.paragraph_format.space_before = Pt(8)
            parrafo.paragraph_format.space_after = Pt(8)
        else:
            parrafo.alignment = alin
            parrafo.paragraph_format.left_indent = Pt(0)
            parrafo.paragraph_format.right_indent = Pt(0)
            if normas_apa:
                parrafo.paragraph_format.first_line_indent = Mm(12.7)
            else:
                parrafo.paragraph_format.first_line_indent = Pt(0)

            # Garantizar nodo explícito w:jc y limpiar sangría XML parásita heredada
            pPr = parrafo._p.get_or_add_pPr()
            jc_p = pPr.find(qn("w:jc"))
            if jc_p is None:
                jc_p = OxmlElement("w:jc")
                pPr.append(jc_p)
            jc_p.set(qn("w:val"), jc_val_cuerpo)

            for w_ind in pPr.findall(qn("w:ind")):
                if not normas_apa:
                    pPr.remove(w_ind)
                else:
                    w_ind.attrib.pop(qn("w:left"), None)
                    w_ind.attrib.pop(qn("w:right"), None)
                    w_ind.attrib.pop(qn("w:start"), None)
                    w_ind.attrib.pop(qn("w:end"), None)
                    w_ind.set(qn("w:firstLine"), "720")

        for run in parrafo.runs:
            run.font.name = fuente
            if not es_titulo:
                run.font.size = Pt(float(tamanio))

    # Barnizar tablas de datos con clonación nativa o paleta suave, tamaño y fuente específicos
    avisos_tablas: list[str] = []
    for idx_tbl, tabla in enumerate(documento.tables, 1):
        _, llego_minimo = _barnizar_tabla(
            tabla,
            fuente,
            float(tamanio),
            interlineado,
            util_dxa,
            normas_apa=normas_apa,
            paleta_clave=paleta_clave,
            tema_word=tema_word,
            tamanio_tabla=tamanio_tabla,
            fuente_tabla=fuente_tabla,
            paleta_suave_tablas=paleta_suave_tablas,
            color_tabla_cabecera=color_tabla_cabecera,
            color_tabla_filas=color_tabla_filas,
            color_tabla_borde=color_tabla_borde,
        )
        if llego_minimo:
            avisos_tablas.append(f"Tabla {idx_tbl} reducida a 7 pt; revisa su contenido.")

    # Numeración de ecuaciones display: SE EJECUTA DESPUÉS de barnizar tablas de datos
    # para garantizar que la tabla 1x2 de la ecuación nunca reciba marcos ni sombreados.
    ecuaciones_info = []
    if numerar_ecuaciones:
        ecuaciones_info = _numerar_ecuaciones_omml(documento, util_dxa)

    # Pie de página y numeración con alineación seleccionada
    if pie_pagina.strip() or numerar_paginas:
        _configurar_pie_pagina(
            documento,
            texto_pie=pie_pagina,
            numerar=numerar_paginas,
            fuente=fuente,
            alineacion=alineacion_pie,
        )

    # Creación de índice TOC e Índices de Ecuaciones y Figuras
    if crear_indice and documento.paragraphs:
        try:
            _insertar_toc_e_indice_ecuaciones(
                documento,
                posicion=posicion_indice,
                con_indice_ecuaciones=numerar_ecuaciones,
                ecuaciones_info=ecuaciones_info,
                rgb_titulo=rgb_h1 if not es_tema_nativo else None,
                hex_titulo=hex_h1,
            )
        except Exception as exc:
            import logging
            logging.getLogger("motor.a_docx").warning("Fallo al insertar TOC: %s", exc)

    documento.save(str(destino))
    return avisos_tablas


def a_docx(
    texto: str,
    destino: Path,
    titulo: str = "Documento",
    fuente: str = "Calibri",
    tamanio_pt: float = 11.0,
    interlineado: float = 1.0,
    alineacion: str = "justificado",
    tema_word: str = "defecto",
    color_titulos_word: str = "negro",
    normas_apa: bool = False,
    paleta_tabla: str = "defecto",
    numerar_ecuaciones: bool = False,
    crear_indice: bool = False,
    posicion_indice: str = "inicio",
    pie_pagina: str = "",
    alineacion_pie: str = "derecha",
    numerar_paginas: bool = False,
    tamanio_tabla_pt: float | None = None,
    fuente_tabla: str | None = None,
    modo_color_titulos: str = "auto",
    paleta_suave_tablas: bool = True,
    color_tabla_cabecera: str = "",
    color_tabla_filas: str = "",
    color_tabla_borde: str = "",
    color_tit_h1: str = "",
    color_tit_h2: str = "",
) -> tuple[Path, int, list[str]]:
    """Transforma texto saneado a .docx profesional con soporte APA 7, TOC, clonación y reglas estrictas."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    carpeta_diagramas = destino.parent / "mermaid"
    texto_conversion, _, avisos_mermaid = reemplazar_mermaid_por_imagenes(
        texto, carpeta_diagramas
    )

    # Preprocesar bloques <details><summary>...</summary><p><img...></p></details> y <figure>
    # para que Pandoc inserte la imagen OpenXML y su epígrafe centrado sin perder la imagen.
    def _reemplazar_bloque_img_a_md(match: re.Match) -> str:
        bloque = match.group(0)
        src_m = re.search(r'src=["\']([^"\']+)["\']', bloque)
        alt_m = re.search(r'alt=["\']([^"\']+)["\']', bloque)
        summary_m = re.search(r'<summary[^>]*>(.*?)</summary>', bloque, re.DOTALL)
        cap_m = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', bloque, re.DOTALL)

        src = src_m.group(1) if src_m else ""
        alt = alt_m.group(1) if alt_m else "Figura"
        texto_epigrafe = ""

        if summary_m:
            s_limpio = re.sub(r'<[^>]+>', '', summary_m.group(1)).strip()
            s_limpio = re.sub(r'\s*\(hacer\s+clic\s+para\s+desplegar\)', '', s_limpio, flags=re.IGNORECASE).strip()
            s_limpio = re.sub(r'^[🖼️\s]+', '', s_limpio).strip()
            if s_limpio:
                texto_epigrafe = s_limpio
        elif cap_m:
            cap_limpio = re.sub(r'<[^>]+>', '', cap_m.group(1)).strip()
            if cap_limpio:
                texto_epigrafe = cap_limpio

        cap_md = f"\n\n*{texto_epigrafe}*" if texto_epigrafe else ""
        if src:
            return f"\n\n![{alt}]({src}){cap_md}\n\n"
        return bloque

    texto_conversion = re.sub(r'<details\b[^>]*>.*?</details>', _reemplazar_bloque_img_a_md, texto_conversion, flags=re.DOTALL | re.IGNORECASE)
    texto_conversion = re.sub(r'<figure\b[^>]*>.*?</figure>', _reemplazar_bloque_img_a_md, texto_conversion, flags=re.DOTALL | re.IGNORECASE)

    # Resolución robusta de rutas de imágenes (docs/mejoras/mejoras_app_01.md)
    texto_conversion = resolver_imagenes_en_markdown_docx(texto_conversion, base_dir=destino.parent)

    # Separación estricta: Temas nativos leídos de templates/temas_word/ vs Tema Personalizado
    es_tema_nativo = False
    plantilla_ref: Path | None = None
    tema_solicitado = (tema_word or "").strip().lower().replace(".docx", "")

    if tema_solicitado and tema_solicitado not in ("defecto", "personalizado", ""):
        nombre_archivo = f"{tema_solicitado}.docx"
        cand = _DIR_TEMAS_WORD / nombre_archivo
        if not cand.is_file():
            raise ErrorMotor(
                f"Tema '{tema_word}' no encontrado en templates/temas_word ({nombre_archivo} no existe en disco)."
            )
        es_tema_nativo = True
        plantilla_ref = cand

    _pandoc_a_docx(texto_conversion, destino, plantilla_referencia=plantilla_ref)

    avisos_tablas = _barnizar(
        destino,
        titulo=titulo,
        fuente=fuente,
        tamanio=tamanio_pt,
        interlineado=interlineado,
        alineacion=alineacion,
        normas_apa=normas_apa,
        paleta_clave=paleta_tabla,
        tema_word=tema_word,
        color_titulos_word=color_titulos_word,
        numerar_ecuaciones=numerar_ecuaciones,
        crear_indice=crear_indice,
        posicion_indice=posicion_indice,
        pie_pagina=pie_pagina,
        alineacion_pie=alineacion_pie,
        numerar_paginas=numerar_paginas,
        es_tema_nativo=es_tema_nativo,
        tamanio_tabla=tamanio_tabla_pt,
        fuente_tabla=fuente_tabla,
        modo_color_titulos=modo_color_titulos,
        paleta_suave_tablas=paleta_suave_tablas,
        color_tabla_cabecera=color_tabla_cabecera,
        color_tabla_filas=color_tabla_filas,
        color_tabla_borde=color_tabla_borde,
        color_tit_h1=color_tit_h1,
        color_tit_h2=color_tit_h2,
    )

    avisos = (
        avisos_mermaid
        + avisos_tablas
        + [
            "Ecuaciones OMML nativas de Word insertadas y configuradas.",
            f"Tipografía aplicada: {fuente} {tamanio_pt:g} pt · interlineado {interlineado:.2f} (Sencillo) · alineación {alineacion}.",
        ]
    )
    if tamanio_tabla_pt and float(tamanio_tabla_pt) > 0:
        avisos.append(f"Tamaño tipográfico para cuadros y tablas fijado en {tamanio_tabla_pt:g} pt.")
    if fuente_tabla and fuente_tabla.lower() not in ("heredar", "auto", ""):
        avisos.append(f"Tipografía específica de cuadros y tablas: {fuente_tabla}.")
    if es_tema_nativo:
        avisos.append(f"Tema formal inmutable aplicado ({plantilla_ref.name}): cuadros y estilos conservados fielmente sin sobreescritura de color.")
    else:
        _, _, color_nom = _obtener_color_titulos(color_titulos_word)
        avisos.append(f"Tema personalizado: títulos fijados a {color_nom} y paleta de colores suaves aplicada a cuadros y tablas.")

    if normas_apa:
        avisos.append("Normas APA 7ma Edición aplicadas: márgenes 2.54 cm, sangría 1.27 cm y tablas sin bordes verticales.")
    if crear_indice:
        pos_txt = "inicio" if posicion_indice == "inicio" else "final"
        avisos.append(f"Tabla de Contenidos (TOC) nativa generada al {pos_txt} del documento.")
        if numerar_ecuaciones:
            avisos.append("Índice de Ecuaciones generado inmediatamente tras la Tabla de Contenidos.")
    if numerar_ecuaciones:
        avisos.append("Ecuaciones numeradas secuencialmente.")

    return destino, contar_formulas(texto), avisos
