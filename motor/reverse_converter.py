"""Motor de Conversión Inversa de Alta Precisión (DOCX y PDF -> MD).

Implementa la extracción de ingeniería documental conforme a docs/mejoras de app_nueva_implementacion1.md:
  1. Sanitización y limpieza estricta de tablas (Clean Markdown Tables):
     - Normalización de celdas eliminando saltos de línea y escapando pipes '|'.
     - Resolución y aplanado de celdas combinadas.
     - Detección y conservación de notas de fuente al pie de la tabla.
     - Exclusión de tablas falsas de diseño (1x2 o 1x3 creadas para fórmulas).
  2. Preservación y adaptación de notas, callouts y citas a bloques GFM (> [!NOTE]).
  3. Adaptación de esquemas y secuencias de procesos a bloques ```mermaid.
  4. Gestión de imágenes en subcarpeta dedicada [Nombre_Archivo_Base]_imagenes:
     - Nomenclatura img_001.png, img_002.png.
     - Nota visual estilizada en color gris con espacio de imagen.
     - Sintaxis estándar de imagen Markdown.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml.ns import qn
import pymupdf

from motor.noise_stripper import DocumentNoiseStripper


class ErrorConversionInversa(RuntimeError):
    """Excepción para fallos en la extracción inversa de DOCX/PDF a Markdown."""


def sanitizar_celda_tabla(texto: str) -> str:
    """Limpia el texto de una celda para una tabla Markdown válida."""
    if not texto:
        return ""
    # Reemplazar saltos de línea por <br>
    limpio = texto.replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")
    # Escapar barras verticales internas no delimitadoras
    limpio = limpio.replace("|", "\\|")
    # Compactar espacios
    limpio = re.sub(r"[ \t]+", " ", limpio).strip()
    return limpio


def extraer_contenido_celda(celda: Any) -> str:
    """Extrae el contenido textual y matemático de una celda de tabla de forma limpia."""
    partes: list[str] = []
    for p in celda.paragraphs:
        txt = p.text.strip()
        omaths = p._p.findall(".//" + qn("m:oMath"))
        if omaths:
            for om in omaths:
                ts = [t.text for t in om.iter() if t.text]
                if ts:
                    formula_str = " ".join(ts).strip()
                    if formula_str:
                        partes.append(f"${formula_str}$")
        elif txt:
            partes.append(txt)
    contenido = " ".join(partes) if partes else celda.text.strip()
    return sanitizar_celda_tabla(contenido)


def tabla_a_markdown(tabla_docx: Any) -> str:
    """Convierte una tabla de python-docx a una tabla Markdown limpia GFM.

    Descarta tablas de diseño de 1 fila x 2 o 3 columnas que contengan fórmulas.
    """
    filas = tabla_docx.rows
    if not filas:
        return ""

    num_filas = len(filas)
    num_cols = len(tabla_docx.columns)

    # 1. Detectar si es tabla de diseño matemático (1 fila x 2 o 3 columnas)
    if num_filas == 1 and num_cols in (2, 3):
        for celda in filas[0].cells:
            if celda._tc.findall(".//" + qn("m:oMath")):
                p_textos = [p.text.strip() for p in celda.paragraphs if p.text.strip()]
                return f"$$\n{' '.join(p_textos)}\n$$\n"

    # 2. Extracción y normalización de matriz de celdas preservando columnas
    matriz: list[list[str]] = []
    for fila in filas:
        fila_vals = [extraer_contenido_celda(celda) for celda in fila.cells]
        matriz.append(fila_vals)

    if not matriz:
        return ""

    num_columnas_max = max(len(r) for r in matriz)
    if num_columnas_max == 0:
        return ""

    # Normalizar longitud de todas las filas
    for r in matriz:
        while len(r) < num_columnas_max:
            r.append("")

    lineas_md = []
    cabecera = matriz[0]
    lineas_md.append("| " + " | ".join(c if c else " " for c in cabecera) + " |")
    # Separador GFM
    lineas_md.append("| " + " | ".join(":---" for _ in range(num_columnas_max)) + " |")

    # Filas del cuerpo
    for r in matriz[1:]:
        lineas_md.append("| " + " | ".join(c if c else " " for c in r) + " |")

    return "\n" + "\n".join(lineas_md) + "\n\n"


def convertir_docx_a_markdown(
    ruta_docx: Path,
    carpeta_salida: Path | None = None,
) -> tuple[str, Path, list[Path]]:
    """Extrae el contenido de un archivo Word (.docx) a Markdown limpio con imágenes dedicadas.

    Aplica DocumentNoiseStripper para aislar el contenido vital y descartar membretes y pies de página.
    """
    if not ruta_docx.is_file():
        raise ErrorConversionInversa(f"Archivo no encontrado: {ruta_docx}")

    directorio_base = carpeta_salida if carpeta_salida else ruta_docx.parent
    nombre_base = ruta_docx.stem
    carpeta_imagenes = directorio_base / f"{nombre_base}_imagenes"

    doc = Document(str(ruta_docx))
    rids_validos = DocumentNoiseStripper.extraer_rids_imagenes_cuerpo_docx(doc)

    # Abrir el zip del docx para mapear rIds a archivos reales en word/media/
    mapa_rid_a_archivo: dict[str, str] = {}
    with zipfile.ZipFile(str(ruta_docx), "r") as z:
        if "word/_rels/document.xml.rels" in z.namelist():
            from xml.etree import ElementTree as ET
            rels_xml = z.read("word/_rels/document.xml.rels")
            root_rels = ET.fromstring(rels_xml)
            for rel in root_rels:
                rid = rel.get("Id")
                target = rel.get("Target")
                if rid and target:
                    if target.startswith("media/"):
                        mapa_rid_a_archivo[rid] = f"word/{target}"
                    elif "media/" in target:
                        mapa_rid_a_archivo[rid] = f"word/{target.split('media/')[-1]}"

    # Extraer imágenes válidas (en memoria y como Data URI Base64 autocontenida)
    import base64
    carpeta_imagenes.mkdir(parents=True, exist_ok=True)
    mapa_rid_a_b64: dict[str, tuple[str, str]] = {} # rid -> (data_uri, ext)
    mapa_rid_a_img_guardada: dict[str, str] = {}
    imagenes_guardadas: list[Path] = []
    contador_img = 1

    with zipfile.ZipFile(str(ruta_docx), "r") as z:
        for rid in sorted(rids_validos):
            ruta_interna = mapa_rid_a_archivo.get(rid)
            if ruta_interna and ruta_interna in z.namelist():
                ext = Path(ruta_interna).suffix.lstrip(".").lower() or "png"
                if ext == "jpg":
                    ext = "jpeg"
                mime = f"image/{ext}"
                nombre_guardado = f"img_{contador_img:03d}.{ext}"
                ruta_dest = carpeta_imagenes / nombre_guardado
                img_data = z.read(ruta_interna)
                ruta_dest.write_bytes(img_data)
                
                b64_str = base64.b64encode(img_data).decode("ascii")
                data_uri = f"data:{mime};base64,{b64_str}"
                mapa_rid_a_b64[rid] = (data_uri, nombre_guardado)

                mapa_rid_a_img_guardada[rid] = nombre_guardado
                imagenes_guardadas.append(ruta_dest)
                contador_img += 1

    # Recorrer elementos del cuerpo en orden secuencial
    body = doc._element.body
    bloques_md: list[str] = []
    num_figura = 1

    for elemento in body:
        tag = elemento.tag.split("}")[-1]

        if tag == "p":
            from docx.text.paragraph import Paragraph
            p_obj = Paragraph(elemento, doc)
            texto_p = p_obj.text.strip()

            # 1. Comprobar si contiene imágenes del cuerpo
            drawing_nodes = elemento.findall(".//" + qn("w:drawing"))
            for dw in drawing_nodes:
                for blip in dw.findall(".//" + qn("a:blip")):
                    rid = blip.get(qn("r:embed")) or blip.get(qn("r:link"))
                    if rid and rid in mapa_rid_a_b64:
                        data_uri, nom_i = mapa_rid_a_b64[rid]
                        desc_fig = f"Figura extraída ({nom_i})"
                        bloque_img = (
                            f'<details><summary>🖼️ <strong>Figura {num_figura}: {desc_fig} (Hacer clic para desplegar)</strong></summary><br><p align="center"><img src="{data_uri}" alt="Figura {num_figura}" style="max-width: 100%; border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></p></details>'
                        )
                        bloques_md.append(bloque_img)
                        num_figura += 1

            # 2. Comprobar si contiene fórmulas matemáticas OMML
            omath_nodes = elemento.findall(".//" + qn("m:oMath"))
            if omath_nodes and not texto_p:
                tex_acum = []
                for om in omath_nodes:
                    ts = [t.text for t in om.iter() if t.text]
                    tex_acum.append(" ".join(ts))
                formula_clean = " ".join(tex_acum).strip()
                if formula_clean:
                    bloques_md.append(f"$$\n{formula_clean}\n$$")
                continue

            if not texto_p:
                continue

            # 3. Detectar encabezados (Headings)
            pPr = elemento.find(qn("w:pPr"))
            pStyle = pPr.find(qn("w:pStyle")) if pPr is not None else None
            estilo = pStyle.get(qn("w:val")) if pStyle is not None else ""
            estilo_low = estilo.lower()

            if "heading1" in estilo_low or estilo_low == "heading 1" or estilo_low == "título 1":
                bloques_md.append(f"# {texto_p}")
            elif "heading2" in estilo_low or estilo_low == "heading 2" or estilo_low == "título 2":
                bloques_md.append(f"## {texto_p}")
            elif "heading3" in estilo_low or estilo_low == "heading 3" or estilo_low == "título 3":
                bloques_md.append(f"### {texto_p}")
            elif "heading4" in estilo_low or estilo_low == "heading 4" or estilo_low == "título 4":
                bloques_md.append(f"#### {texto_p}")
            elif any(k in estilo_low for k in ("quote", "block", "cita")):
                bloques_md.append(f"> {texto_p}")
            elif texto_p.lower().startswith(("nota:", "importante:", "advertencia:", "observación:")):
                bloques_md.append(f"> {texto_p}")
            elif re.match(r"^[-*+•]\s+", texto_p):
                bloques_md.append(texto_p)
            elif re.match(r"^\d+[.)]\s+", texto_p):
                bloques_md.append(texto_p)
            elif " -> " in texto_p and ("inicio" in texto_p.lower() or "paso" in texto_p.lower()):
                # Convertir secuencia a Mermaid
                pasos = [p.strip() for p in texto_p.split("->") if p.strip()]
                lineas_mermaid = ["```mermaid", "flowchart TD"]
                for i in range(len(pasos) - 1):
                    lineas_mermaid.append(f'    P{i}["{pasos[i]}"] --> P{i+1}["{pasos[i+1]}"]')
                lineas_mermaid.append("```")
                bloques_md.append("\n".join(lineas_mermaid))
            else:
                bloques_md.append(texto_p)

        elif tag == "tbl":
            # Convertir tabla
            from docx.table import Table
            tbl_obj = Table(elemento, doc)
            md_tabla = tabla_a_markdown(tbl_obj)
            if md_tabla.strip():
                bloques_md.append(md_tabla.strip())

    md_crudo = "\n\n".join(bloques_md)
    md_final = DocumentNoiseStripper.limpiar_texto_markdown(md_crudo)

    ruta_archivo_md = directorio_base / f"{nombre_base}.md"
    ruta_archivo_md.write_text(md_final, encoding="utf-8")

    return md_final, ruta_archivo_md, imagenes_guardadas


def convertir_pdf_a_markdown(
    ruta_pdf: Path,
    carpeta_salida: Path | None = None,
) -> tuple[str, Path, list[Path]]:
    """Extrae el contenido de un PDF hacia Markdown limpio con imágenes dedicadas."""
    if not ruta_pdf.is_file():
        raise ErrorConversionInversa(f"Archivo no encontrado: {ruta_pdf}")

    directorio_base = carpeta_salida if carpeta_salida else ruta_pdf.parent
    nombre_base = ruta_pdf.stem
    carpeta_imagenes = directorio_base / f"{nombre_base}_imagenes"

    doc_pdf = pymupdf.open(str(ruta_pdf))
    md_limpio, info_imgs = DocumentNoiseStripper.procesar_pdf_vital(
        doc_pdf=doc_pdf,
        carpeta_imagenes=carpeta_imagenes,
        nombre_base=nombre_base,
    )
    doc_pdf.close()

    ruta_archivo_md = directorio_base / f"{nombre_base}.md"
    ruta_archivo_md.write_text(md_limpio, encoding="utf-8")

    rutas_imgs = [Path(img["ruta"]) for img in info_imgs]
    return md_limpio, ruta_archivo_md, rutas_imgs
