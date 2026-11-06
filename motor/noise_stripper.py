"""Módulo de Aislamiento de Contenido Vital y Supresión de Ruido (Noise & Artifact Stripping).

Implementa DocumentNoiseStripper conforme a la especificación de docs/mejoras de app_nueva_implementacion1.md:
  1. DOCX:
     - Lectura exclusiva del cuerpo principal (<w:body>).
     - Exclusión de <w:headerReference>, <w:footerReference>, secciones header y footer.
     - Extracción exclusiva de imágenes referenciadas en el cuerpo principal.
     - Supresión de marcas de agua (behindDoc="1", v:shape, w:pict de fondo).
  2. PDF:
     - Recorte geométrico de bandas marginales (8% superior e inferior).
     - Filtro estadístico cross-page (>40% de frecuencia en misma Y) para eliminar encabezados y pies repetitivos.
     - Eliminación de marcas de agua diagonales (matriz rotada) y capas de fondo.
     - Filtrado de imágenes de membrete repetitivas por hash MD5 y descarte de iconos menores a 40x40 px.
  3. REGEX POST-PROCESSOR:
     - Supresión de numeración de páginas huérfana en el Markdown generado.
"""

from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from typing import Any

from docx.oxml.ns import qn


class DocumentNoiseStripper:
    """Filtro de aislamiento de contenido vital para descarte de encabezados, pies y marcas de agua."""

    @staticmethod
    def limpiar_texto_markdown(md_texto: str) -> str:
        """Aplica regex post-processor para barrer numeraciones de página huérfanas y marcas de agua."""
        lineas = md_texto.splitlines()
        lineas_limpias = []

        # Patrones de numeración de página y marcas de agua huérfanas
        patron_num_pura = re.compile(r"^\s*[-—–]?\s*\d+\s*[-—–]?\s*$")
        patron_pagina_x_de_y = re.compile(
            r"^\s*(?:[Pp]ág(?:ina)?\.?|[Pp]age)\s*\d+(?:\s*(?:de|/|of)\s*\d+)?\s*$",
            re.IGNORECASE,
        )
        patron_num_pipe = re.compile(r"^\s*\d+\s*\|\s*[Pp]\s*á\s*g\s*i\s*n\s*a\s*$", re.IGNORECASE)
        patron_marca_agua = re.compile(
            r"^\s*[-—–*_#\s]*(?:BORRADOR|CONFIDENCIAL|DRAFT|PROYECTO|PRELIMINAR)\s*[-—–*_#\s]*$",
            re.IGNORECASE,
        )

        for linea in lineas:
            linea_strip = linea.strip()
            if not linea_strip:
                lineas_limpias.append(linea)
                continue

            # Descartar líneas que coincidan con artefactos de encabezado/pie
            if patron_num_pura.match(linea_strip):
                continue
            if patron_pagina_x_de_y.match(linea_strip):
                continue
            if patron_num_pipe.match(linea_strip):
                continue
            if patron_marca_agua.match(linea_strip):
                continue

            lineas_limpias.append(linea)

        # Compactar saltos de línea triples o cuádruples
        resultado = "\n".join(lineas_limpias)
        resultado = re.sub(r"\n{3,}", "\n\n", resultado)
        return resultado.strip() + "\n"

    @classmethod
    def extraer_rids_imagenes_cuerpo_docx(cls, docx_doc: Any) -> set[str]:
        """Extrae únicamente los rId de imágenes que pertenecen al cuerpo (<w:body>).

        Descarta explícitamente cualquier rId que provenga de headers, footers o marcas de agua de fondo.
        """
        rids_validos = set()
        body = docx_doc._element.body

        # Buscar todos los elementos de dibujo en el cuerpo
        for drawing in body.findall(".//" + qn("w:drawing")):
            # Verificar si es marca de agua detrás del documento
            es_marca_agua = False
            for anchor in drawing.findall(".//" + qn("wp:anchor")):
                if anchor.get("behindDoc") == "1":
                    es_marca_agua = True
                    break
            if es_marca_agua:
                continue

            # Extraer blip fill
            for blip in drawing.findall(".//" + qn("a:blip")):
                rid = blip.get(qn("r:embed")) or blip.get(qn("r:link"))
                if rid:
                    rids_validos.add(rid)

        # Buscar elementos VML (v:shape / v:imagedata) sin depender de prefijos
        for imagedata in body.xpath(".//*[local-name()='imagedata']"):
            rid = (
                imagedata.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
                or imagedata.get("{urn:schemas-microsoft-com:office:office}relid")
                or imagedata.get("id")
            )
            if rid:
                # Comprobar si la forma contenedora tiene marca de agua
                forma = imagedata.getparent()
                if forma is not None and "watermark" in (forma.get("id") or "").lower():
                    continue
                rids_validos.add(rid)

        return rids_validos

    @classmethod
    def procesar_pdf_vital(
        cls,
        doc_pdf: Any,
        carpeta_imagenes: Path,
        nombre_base: str,
        filtro_margen: float = 0.08,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Procesa un PDF mediante triple filtro (Geométrico + Frecuencia + Capas).

        Devuelve el texto extraído y la lista de imágenes vitales guardadas.
        """
        import pymupdf

        total_paginas = len(doc_pdf)
        if total_paginas == 0:
            return "", []

        carpeta_imagenes.mkdir(parents=True, exist_ok=True)

        # 1. Paso estadístico: analizar bloques de texto repetitivos cross-page
        frecuencia_lineas: dict[str, int] = {}
        for pag in doc_pdf:
            rect = pag.rect
            y_sup = rect.height * filtro_margen
            y_inf = rect.height * (1.0 - filtro_margen)
            bloques = pag.get_text("blocks")
            for b in bloques:
                bx0, by0, bx1, by1, btxt, _, _ = b
                # Si está en margen superior o inferior, registrar texto
                if by1 <= y_sup or by0 >= y_inf:
                    txt_norm = re.sub(r"\d+", "#", btxt.strip().lower())
                    if txt_norm:
                        frecuencia_lineas[txt_norm] = frecuencia_lineas.get(txt_norm, 0) + 1

        umbral_repeticion = max(2, int(total_paginas * 0.40))
        textos_repetitivos_descartables = {
            txt for txt, count in frecuencia_lineas.items() if count >= umbral_repeticion
        }

        # 2. Paso de extracción de imágenes: filtrar logos de membrete repetitivos
        hash_imagenes_frecuencia: dict[str, int] = {}
        hash_a_bytes: dict[str, tuple[bytes, str]] = {}
        imagenes_pagina: list[list[dict]] = []

        for pag in doc_pdf:
            lista_imgs_pag = []
            rect = pag.rect
            y_sup = rect.height * filtro_margen
            y_inf = rect.height * (1.0 - filtro_margen)

            for img_info in pag.get_images(full=True):
                xref = img_info[0]
                base_img = doc_pdf.extract_image(xref)
                if not base_img:
                    continue

                ancho_img = base_img.get("width", 0)
                alto_img = base_img.get("height", 0)
                ext_img = base_img.get("ext", "png")
                img_bytes = base_img.get("image", b"")

                # Descartar iconos decorativos diminutos (< 40x40 px)
                if ancho_img < 40 and alto_img < 40:
                    continue

                h_val = hashlib.md5(img_bytes).hexdigest()
                hash_imagenes_frecuencia[h_val] = hash_imagenes_frecuencia.get(h_val, 0) + 1
                hash_a_bytes[h_val] = (img_bytes, ext_img)

                # Posición en página si está disponible
                bbox_img = pag.get_image_bbox(img_info)
                en_margen = False
                if bbox_img:
                    if bbox_img.y1 <= y_sup or bbox_img.y0 >= y_inf:
                        en_margen = True

                lista_imgs_pag.append({
                    "hash": h_val,
                    "xref": xref,
                    "en_margen": en_margen,
                    "rect": bbox_img,
                })
            imagenes_pagina.append(lista_imgs_pag)

        # Identificar logos repetitivos (membretes que aparecen en > 40% de las páginas)
        logos_repetitivos = {
            h for h, cant in hash_imagenes_frecuencia.items() if cant >= umbral_repeticion
        }

        # 3. Paso de ensamblado de contenido vital y extracción de imágenes únicas
        imagenes_guardadas: list[dict[str, Any]] = []
        contador_imagen = 1
        partes_markdown: list[str] = []

        for idx, pag in enumerate(doc_pdf):
            rect = pag.rect
            y_sup = rect.height * filtro_margen
            y_inf = rect.height * (1.0 - filtro_margen)

            # Extraer bloques de texto filtrando bandas marginales y marcas de agua diagonales
            dict_texto = pag.get_text("dict")
            texto_vital_bloques: list[str] = []

            for bloque in dict_texto.get("blocks", []):
                if bloque.get("type") == 0:  # Bloque de texto
                    bbox = bloque.get("bbox", (0, 0, 0, 0))
                    # Recorte geométrico de bandas marginales
                    if bbox[3] <= y_sup or bbox[1] >= y_inf:
                        continue

                    # Inspeccionar líneas y spans
                    lineas_validas = []
                    for linea in bloque.get("lines", []):
                        # Descartar rotaciones diagonales (marcas de agua inclinadas)
                        dir_vector = linea.get("dir", (1, 0))
                        if abs(dir_vector[0]) < 0.9 and abs(dir_vector[1]) < 0.9:
                            continue  # Rotado diagonalmente (marca de agua)

                        texto_linea = "".join(span.get("text", "") for span in linea.get("spans", "")).strip()
                        if not texto_linea:
                            continue

                        # Descartar texto repetitivo estadístico
                        txt_norm = re.sub(r"\d+", "#", texto_linea.lower())
                        if txt_norm in textos_repetitivos_descartables:
                            continue

                        lineas_validas.append(texto_linea)

                    if lineas_validas:
                        texto_vital_bloques.append("\n".join(lineas_validas))

            if texto_vital_bloques:
                partes_markdown.append("\n\n".join(texto_vital_bloques))

            # Guardar imágenes de esta página que no sean membrete ni estén en margen
            for img_p in imagenes_pagina[idx]:
                h = img_p["hash"]
                if h in logos_repetitivos or img_p["en_margen"]:
                    continue

                img_bytes, ext = hash_a_bytes[h]
                nombre_archivo = f"img_{contador_imagen:03d}.{ext}"
                ruta_salida_img = carpeta_imagenes / nombre_archivo
                if not ruta_salida_img.exists():
                    ruta_salida_img.write_bytes(img_bytes)

                nota_gris = (
                    f'<div style="background-color: #f1f5f9; border-left: 4px solid #64748b; '
                    f'color: #475569; padding: 10px 14px; margin: 12px 0; border-radius: 4px; '
                    f'font-size: 0.9em; font-style: italic;">\n'
                    f'  🖼️ <strong>[ESPACIO DE IMAGEN]:</strong> La imagen <code>{nombre_archivo}</code> va ubicada aquí. <br>\n'
                    f'  📂 <em>Extraída en: <code>./{nombre_base}_imagenes/{nombre_archivo}</code></em>\n'
                    f'</div>\n\n'
                    f'![{nombre_archivo}](./{nombre_base}_imagenes/{nombre_archivo})\n'
                )
                partes_markdown.append(nota_gris)
                imagenes_guardadas.append({
                    "nombre": nombre_archivo,
                    "ruta": str(ruta_salida_img),
                    "pagina": idx + 1,
                })
                contador_imagen += 1

        md_crudo = "\n\n".join(partes_markdown)
        md_final = cls.limpiar_texto_markdown(md_crudo)
        return md_final, imagenes_guardadas
