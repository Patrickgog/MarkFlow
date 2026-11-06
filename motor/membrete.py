"""Motor de análisis geométrico e inspección de hojas de membrete Word (.docx).

Analiza cabeceras, pies y cuerpo de documentos OpenXML sin requerir Word instalado,
identificando imágenes de membrete, dimensiones, anclajes y calculando la zona
de escritura sugerida para que el contenido no tape los logotipos ni las franjas.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Any

# Constantes de conversión métrica
EMU_POR_CM = 360000
DXA_POR_CM = 566.929133858
EMU_POR_DXA = 635


def _dxa_a_cm(dxa_val: int | float | str | None) -> float:
    if dxa_val is None:
        return 0.0
    try:
        return round(float(dxa_val) / DXA_POR_CM, 2)
    except (ValueError, TypeError):
        return 0.0


def _emu_a_cm(emu_val: int | float | str | None) -> float:
    if emu_val is None:
        return 0.0
    try:
        return round(float(emu_val) / EMU_POR_CM, 2)
    except (ValueError, TypeError):
        return 0.0


def analizar_membrete(ruta: Path | str) -> dict[str, Any]:
    """Analiza una hoja de membrete Word (.docx) y calcula la zona de escritura segura.
    
    Retorna un diccionario con:
        - imagenes: lista de imágenes detectadas con dimensiones y anclajes.
        - margenes_cm: top, bottom, left, right definidos en sectPr.
        - dimensiones_pagina_cm: ancho y alto de página en cm.
        - titlePg: booleano indicando si titlePg está activo.
        - zona_sugerida_cm: top, bottom, left, right recomendados en cm.
        - origen_zona: 'analisis' o 'archivo_zona'.
        - advertencias: lista de avisos para el usuario.
    """
    ruta_p = Path(ruta).resolve()
    if not ruta_p.is_file():
        raise FileNotFoundError(f"El archivo '{ruta_p}' no existe.")

    # 1. Comprobar si existe archivo de zona explícito (ej. HojaPlantilla1.zona.json)
    ruta_zona_json = ruta_p.with_suffix(".zona.json")
    zona_personalizada = None
    if ruta_zona_json.is_file():
        try:
            datos_z = json.loads(ruta_zona_json.read_text(encoding="utf-8"))
            if all(k in datos_z for k in ("top", "bottom", "left", "right")):
                zona_personalizada = {
                    "top": round(float(datos_z["top"]), 2),
                    "bottom": round(float(datos_z["bottom"]), 2),
                    "left": round(float(datos_z["left"]), 2),
                    "right": round(float(datos_z["right"]), 2),
                }
        except Exception:
            zona_personalizada = None

    imagenes: list[dict[str, Any]] = []
    advertencias: list[str] = []

    # Valores por defecto de página A4
    ancho_pag_cm = 21.0
    alto_pag_cm = 29.7
    margenes_cm = {
        "top": 2.5,
        "bottom": 2.5,
        "left": 3.0,
        "right": 3.0,
    }
    title_pg = False

    with zipfile.ZipFile(ruta_p, "r") as z:
        nombres = z.namelist()

        # 2. Leer sectPr en word/document.xml
        if "word/document.xml" in nombres:
            doc_xml = z.read("word/document.xml").decode("utf-8", errors="replace")
            title_pg = "<w:titlePg" in doc_xml

            # Extraer dimensiones de página (w:pgSz)
            m_sz = re.search(r'<w:pgSz\b[^>]*w:w="(\d+)"[^>]*w:h="(\d+)"', doc_xml)
            if not m_sz:
                m_sz = re.search(r'<w:pgSz\b[^>]*w:h="(\d+)"[^>]*w:w="(\d+)"', doc_xml)
                if m_sz:
                    alto_pag_cm = _dxa_a_cm(m_sz.group(1))
                    ancho_pag_cm = _dxa_a_cm(m_sz.group(2))
            else:
                ancho_pag_cm = _dxa_a_cm(m_sz.group(1))
                alto_pag_cm = _dxa_a_cm(m_sz.group(2))

            # Extraer márgenes de sección (w:pgMar)
            m_mar = re.search(
                r'<w:pgMar\b[^>]*w:top="(\d+)"[^>]*w:right="(\d+)"[^>]*w:bottom="(\d+)"[^>]*w:left="(\d+)"',
                doc_xml,
            )
            if m_mar:
                margenes_cm = {
                    "top": _dxa_a_cm(m_mar.group(1)),
                    "right": _dxa_a_cm(m_mar.group(2)),
                    "bottom": _dxa_a_cm(m_mar.group(3)),
                    "left": _dxa_a_cm(m_mar.group(4)),
                }

        # 3. Escanear cabeceras, pies y cuerpo en busca de imágenes
        partes_inspeccionar = [
            n for n in nombres if re.match(r"^word/(document|header\d*|footer\d*)\.xml$", n)
        ]

        for parte in partes_inspeccionar:
            xml_str = z.read(parte).decode("utf-8", errors="replace")
            ubicacion = "cuerpo" if parte == "word/document.xml" else ("header" if "header" in parte else "footer")

            # Buscar imágenes <wp:anchor> y <wp:inline>
            for match in re.finditer(r"<wp:(anchor|inline)\b(.*?)</wp:\1>", xml_str, re.DOTALL):
                tipo_anclaje = match.group(1)
                bloque = match.group(0)

                # Dimensiones en EMU
                ext = re.search(r'<wp:extent\b[^>]*cx="(\d+)"[^>]*cy="(\d+)"', bloque)
                ancho_cm = _emu_a_cm(ext.group(1)) if ext else 0.0
                alto_cm = _emu_a_cm(ext.group(2)) if ext else 0.0

                # Propiedades de anclaje
                behind_doc = False
                m_behind = re.search(r'\bbehindDoc="([01])"', bloque)
                if m_behind:
                    behind_doc = m_behind.group(1) == "1"

                # Posición horizontal
                rel_h = "column"
                pos_h_emu = 0
                ph = re.search(r'<wp:positionH\b[^>]*relativeFrom="(\w+)"[^>]*>.*?<wp:posOffset>(-?\d+)</wp:posOffset>', bloque, re.DOTALL)
                if ph:
                    rel_h = ph.group(1)
                    pos_h_emu = int(ph.group(2))

                # Posición vertical
                rel_v = "paragraph"
                pos_v_emu = 0
                pv = re.search(r'<wp:positionV\b[^>]*relativeFrom="(\w+)"[^>]*>.*?<wp:posOffset>(-?\d+)</wp:posOffset>', bloque, re.DOTALL)
                if pv:
                    rel_v = pv.group(1)
                    pos_v_emu = int(pv.group(2))

                # Envoltura de texto
                envoltura = "none"
                if "<wp:wrapSquare" in bloque:
                    envoltura = "square"
                elif "<wp:wrapTight" in bloque:
                    envoltura = "tight"
                elif "<wp:wrapThrough" in bloque:
                    envoltura = "through"
                elif "<wp:wrapTopAndBottom" in bloque:
                    envoltura = "topAndBottom"
                elif "<wp:wrapNone" in bloque:
                    envoltura = "none"

                img_info = {
                    "parte": parte,
                    "ubicacion": ubicacion,
                    "anclaje": tipo_anclaje,
                    "ancho_cm": ancho_cm,
                    "alto_cm": alto_cm,
                    "relativeFrom_H": rel_h,
                    "posOffset_H_cm": _emu_a_cm(pos_h_emu),
                    "relativeFrom_V": rel_v,
                    "posOffset_V_cm": _emu_a_cm(pos_v_emu),
                    "posOffset_V_emu": pos_v_emu,
                    "behind_doc": behind_doc,
                    "envoltura": envoltura,
                }
                imagenes.append(img_info)

                if ubicacion == "cuerpo":
                    advertencias.append(
                        "Se detectó una imagen de membrete en el cuerpo del documento. "
                        "El motor la ubicará detrás del texto (behindDoc=1) para que el informe fluya al frente."
                    )

    # 4. Cálculo de la zona_sugerida_cm
    if zona_personalizada:
        zona_sugerida = zona_personalizada
        origen_zona = "archivo_zona"
    else:
        origen_zona = "analisis"
        # Iniciar con los márgenes del sectPr
        top_calc = margenes_cm["top"]
        bottom_calc = margenes_cm["bottom"]
        left_calc = margenes_cm["left"]
        right_calc = margenes_cm["right"]

        # Revisar si hay imagen de página completa
        hay_pagina_completa = any(img["alto_cm"] >= (alto_pag_cm - 2.0) for img in imagenes)

        if hay_pagina_completa:
            # Página completa: se respetan fielmente los márgenes del sectPr
            zona_sugerida = {
                "top": max(2.5, top_calc),
                "bottom": max(2.0, bottom_calc),
                "left": max(2.5, left_calc),
                "right": max(2.5, right_calc),
            }
        else:
            # Inspeccionar bandas superiores e inferiores
            margen_seguridad_cm = 0.5

            for img in imagenes:
                # 4.1 Banda superior
                if img["ubicacion"] == "header":
                    # Altura ocupada por la imagen desde el borde superior
                    # Si relativeFrom es page o paragraph, la cota inferior aprox es pos + alto
                    borde_inf = max(img["alto_cm"], img["posOffset_V_cm"] + img["alto_cm"])
                    top_calc = max(top_calc, round(borde_inf + margen_seguridad_cm, 2))

                # 4.2 Banda inferior
                elif img["ubicacion"] == "footer":
                    # Si la imagen está en el footer, su altura ocupa un espacio inferior
                    if img["relativeFrom_V"] == "page":
                        # posOffset respecto al tope de página
                        dist_desde_abajo = max(0.0, alto_pag_cm - img["posOffset_V_cm"])
                        borde_sup = max(img["alto_cm"], dist_desde_abajo)
                    else:
                        borde_sup = img["alto_cm"]
                    bottom_calc = max(bottom_calc, round(borde_sup + margen_seguridad_cm, 2))

            zona_sugerida = {
                "top": max(2.5, top_calc),
                "bottom": max(2.0, bottom_calc),
                "left": max(2.5, left_calc),
                "right": max(2.5, right_calc),
            }

    # Ancho útil resultante
    ancho_util_cm = round(ancho_pag_cm - zona_sugerida["left"] - zona_sugerida["right"], 2)
    ancho_util_dxa = int(round(ancho_util_cm * DXA_POR_CM))

    return {
        "archivo": ruta_p.name,
        "dimensiones_pagina_cm": {"ancho": ancho_pag_cm, "alto": alto_pag_cm},
        "margenes_sectpr_cm": margenes_cm,
        "titlePg": title_pg,
        "imagenes": imagenes,
        "zona_sugerida_cm": zona_sugerida,
        "ancho_util_cm": ancho_util_cm,
        "ancho_util_dxa": ancho_util_dxa,
        "origen_zona": origen_zona,
        "archivo_zona_existe": bool(zona_personalizada),
        "advertencias": advertencias,
    }


def guardar_zona_json(ruta_docx: Path | str, zona: dict[str, float | int | str]) -> Path:
    """Guarda o actualiza un archivo Nombre.zona.json junto a la plantilla."""
    ruta_p = Path(ruta_docx).resolve()
    ruta_json = ruta_p.with_suffix(".zona.json")

    top = round(float(zona.get("top", 2.5)), 2)
    bottom = round(float(zona.get("bottom", 2.0)), 2)
    left = round(float(zona.get("left", 2.5)), 2)
    right = round(float(zona.get("right", 2.5)), 2)

    contenido = {
        "plantilla": ruta_p.name,
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
    }

    ruta_json.write_text(json.dumps(contenido, indent=2, ensure_ascii=False), encoding="utf-8")
    return ruta_json


def _crear_parrafo_numeracion(pos_val: str = "right") -> Any:
    """Crea un párrafo OpenXML con formato 'Página X de Y' discreto."""
    import lxml.etree as etree

    NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    p = etree.Element(f"{{{NS_W}}}p")
    pPr = etree.SubElement(p, f"{{{NS_W}}}pPr")
    jc = etree.SubElement(pPr, f"{{{NS_W}}}jc")
    jc.set(f"{{{NS_W}}}val", pos_val)

    def _crear_r(texto: str) -> etree._Element:
        r = etree.Element(f"{{{NS_W}}}r")
        rPr = etree.SubElement(r, f"{{{NS_W}}}rPr")
        sz = etree.SubElement(rPr, f"{{{NS_W}}}sz")
        sz.set(f"{{{NS_W}}}val", "18")  # 9 pt
        szCs = etree.SubElement(rPr, f"{{{NS_W}}}szCs")
        szCs.set(f"{{{NS_W}}}val", "18")
        col = etree.SubElement(rPr, f"{{{NS_W}}}color")
        col.set(f"{{{NS_W}}}val", "666666")
        t = etree.SubElement(r, f"{{{NS_W}}}t")
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = texto
        return r

    def _crear_fld(tipo: str) -> etree._Element:
        fld = etree.Element(f"{{{NS_W}}}fldSimple")
        fld.set(f"{{{NS_W}}}instr", tipo)
        r = etree.SubElement(fld, f"{{{NS_W}}}r")
        rPr = etree.SubElement(r, f"{{{NS_W}}}rPr")
        sz = etree.SubElement(rPr, f"{{{NS_W}}}sz")
        sz.set(f"{{{NS_W}}}val", "18")
        col = etree.SubElement(rPr, f"{{{NS_W}}}color")
        col.set(f"{{{NS_W}}}val", "666666")
        t = etree.SubElement(r, f"{{{NS_W}}}t")
        t.text = "1"
        return fld

    p.append(_crear_r("Página "))
    p.append(_crear_fld("PAGE"))
    p.append(_crear_r(" de "))
    p.append(_crear_fld("NUMPAGES"))
    return p


def aplicar_cuerpo_sobre_plantilla(
    ruta_plantilla: Path | str,
    ruta_contenido_docx: Path | str,
    ruta_destino: Path | str,
    zona_cm: dict[str, float] | None = None,
    numerar_paginas: bool = False,
    posicion_numero: str = "derecha",
) -> Path:
    """Trasplanta el contenido generado al cuerpo de la plantilla de membrete conservando el membrete byte a byte.
    
    1. Lee word/document.xml y word/_rels/document.xml.rels de ambos documentos.
    2. Reemplaza todos los elementos del w:body de la plantilla (salvo el sectPr final) por los del contenido.
    3. Asegura una sola sección consolidada, eliminando titlePg y normalizando cabeceras a default.
    4. Actualiza los márgenes w:pgMar del sectPr según la zona de escritura en dxa.
    5. Gestiona opcionalmente la numeración 'Página X de Y' en el pie sin dañar gráficos existentes.
    6. Si hay imágenes en el cuerpo de la plantilla, se asegura behindDoc="1" para que queden al fondo.
    7. Reasigna y fusiona relaciones rId sin colisiones e incorpora los archivos de medios/numbering/footnotes.
    """
    import shutil
    import tempfile
    import lxml.etree as etree

    ruta_plan = Path(ruta_plantilla).resolve()
    ruta_cont = Path(ruta_contenido_docx).resolve()
    ruta_dest = Path(ruta_destino).resolve()
    ruta_dest.parent.mkdir(parents=True, exist_ok=True)

    NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    NS_R = "http://schemas.openxmlformats.org/package/2006/relationships"
    NS_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
    NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    NS_R_DOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"

    # Resolver márgenes finales en dxa
    if not zona_cm:
        analisis = analizar_membrete(ruta_plan)
        zona_cm = analisis["zona_sugerida_cm"]

    top_dxa = int(round(float(zona_cm.get("top", 2.5)) * DXA_POR_CM))
    bottom_dxa = int(round(float(zona_cm.get("bottom", 2.0)) * DXA_POR_CM))
    left_dxa = int(round(float(zona_cm.get("left", 2.5)) * DXA_POR_CM))
    right_dxa = int(round(float(zona_cm.get("right", 2.5)) * DXA_POR_CM))

    with tempfile.TemporaryDirectory(prefix="mfo_trans_") as tmpdir:
        tmp_path = Path(tmpdir)
        dir_plan = tmp_path / "plan"
        dir_cont = tmp_path / "cont"

        with zipfile.ZipFile(ruta_plan, "r") as z_p:
            z_p.extractall(dir_plan)

        with zipfile.ZipFile(ruta_cont, "r") as z_c:
            z_c.extractall(dir_cont)

        # 1. Parsear XML de documentos
        file_doc_plan = dir_plan / "word" / "document.xml"
        file_doc_cont = dir_cont / "word" / "document.xml"

        root_doc_plan = etree.parse(str(file_doc_plan)).getroot()
        root_doc_cont = etree.parse(str(file_doc_cont)).getroot()

        body_plan = root_doc_plan.find(f"{{{NS_W}}}body")
        body_cont = root_doc_cont.find(f"{{{NS_W}}}body")

        if body_plan is None or body_cont is None:
            raise ValueError("No se encontró el elemento <w:body> en el documento.")

        # Preservar sectPr final de la plantilla
        sectpr_plan = body_plan.find(f"{{{NS_W}}}sectPr")
        if sectpr_plan is None:
            sectpr_plan = etree.SubElement(body_plan, f"{{{NS_W}}}sectPr")

        # 1.1 Desactivar titlePg para que el membrete y el pie se repitan en todas las páginas
        for tpg in list(sectpr_plan):
            if tpg.tag == f"{{{NS_W}}}titlePg":
                sectpr_plan.remove(tpg)

        # 1.2 Normalizar cabeceras de sección a una sola continua
        hdrs = sectpr_plan.findall(f"{{{NS_W}}}headerReference")
        hdr_def = [h for h in hdrs if h.attrib.get(f"{{{NS_W}}}type") == "default"]
        if not hdr_def and hdrs:
            hdrs[0].set(f"{{{NS_W}}}type", "default")
            hdr_def = [hdrs[0]]
        for h in hdrs:
            if h not in hdr_def:
                sectpr_plan.remove(h)

        # 1.3 Normalizar pies de sección existentes a default
        ftrs = sectpr_plan.findall(f"{{{NS_W}}}footerReference")
        ftr_def = [f for f in ftrs if f.attrib.get(f"{{{NS_W}}}type") == "default"]
        if not ftr_def and ftrs:
            ftrs[0].set(f"{{{NS_W}}}type", "default")
            ftr_def = [ftrs[0]]
        for f in ftrs:
            if f not in ftr_def:
                sectpr_plan.remove(f)

        # Actualizar márgenes en sectPr
        pgmar = sectpr_plan.find(f"{{{NS_W}}}pgMar")
        if pgmar is None:
            pgmar = etree.SubElement(sectpr_plan, f"{{{NS_W}}}pgMar")
        pgmar.set(f"{{{NS_W}}}top", str(top_dxa))
        pgmar.set(f"{{{NS_W}}}bottom", str(bottom_dxa))
        pgmar.set(f"{{{NS_W}}}left", str(left_dxa))
        pgmar.set(f"{{{NS_W}}}right", str(right_dxa))

        # 2. Gestionar relaciones y resolver colisiones de rId
        file_rels_plan = dir_plan / "word" / "_rels" / "document.xml.rels"
        file_rels_cont = dir_cont / "word" / "_rels" / "document.xml.rels"

        root_rels_plan = etree.parse(str(file_rels_plan)).getroot() if file_rels_plan.is_file() else etree.Element(f"{{{NS_R}}}Relationships")
        root_rels_cont = etree.parse(str(file_rels_cont)).getroot() if file_rels_cont.is_file() else etree.Element(f"{{{NS_R}}}Relationships")

        # Identificar rIds existentes en plantilla
        rids_usados = set()
        for rel in root_rels_plan:
            rid = rel.attrib.get("Id", "")
            if rid.startswith("rId"):
                try:
                    rids_usados.add(int(rid[3:]))
                except ValueError:
                    pass

        max_rid = max(rids_usados) if rids_usados else 100

        # 2.1 Numeración de páginas opcional en el pie
        if numerar_paginas:
            pos_val = "right"
            p_str = str(posicion_numero).lower()
            if "cent" in p_str:
                pos_val = "center"
            elif "izq" in p_str or "left" in p_str:
                pos_val = "left"

            ftr_def_actual = sectpr_plan.find(f"{{{NS_W}}}footerReference[@{{{NS_W}}}type='default']")
            parrafo_num = _crear_parrafo_numeracion(pos_val)

            if ftr_def_actual is not None:
                # Caso A: La plantilla ya tiene pie default (ej. HojaPlantilla1.docx)
                rid_ftr = ftr_def_actual.attrib.get(f"{{{NS_R_DOC}}}id") or ftr_def_actual.attrib.get(f"{{{NS_R}}}id")
                target_ftr = ""
                for r in root_rels_plan:
                    if r.attrib.get("Id") == rid_ftr:
                        target_ftr = r.attrib.get("Target", "")
                        break
                if target_ftr:
                    arch_ftr = dir_plan / "word" / target_ftr
                    if arch_ftr.is_file():
                        root_ftr = etree.parse(str(arch_ftr)).getroot()
                        # Comprobar si ya existe PAGE
                        tiene_page = any("PAGE" in (el.attrib.get(f"{{{NS_W}}}instr") or "") for el in root_ftr.iter(f"{{{NS_W}}}fldSimple"))
                        if not tiene_page:
                            root_ftr.append(parrafo_num)
                            etree.ElementTree(root_ftr).write(str(arch_ftr), xml_declaration=True, encoding="utf-8", standalone=True)
            else:
                # Caso B: La plantilla no tiene pie (ej. HojaPlantilla2.docx) -> Crear footer1.xml
                idx_ftr = 1
                while (dir_plan / "word" / f"footer{idx_ftr}.xml").is_file():
                    idx_ftr += 1
                nombre_ftr = f"footer{idx_ftr}.xml"
                arch_nuevo_ftr = dir_plan / "word" / nombre_ftr

                root_ftr = etree.Element(f"{{{NS_W}}}ftr", nsmap={"w": NS_W, "r": NS_R_DOC})
                root_ftr.append(parrafo_num)
                etree.ElementTree(root_ftr).write(str(arch_nuevo_ftr), xml_declaration=True, encoding="utf-8", standalone=True)

                max_rid += 1
                rid_nuevo_ftr = f"rId{max_rid}"
                rel_ftr = etree.SubElement(root_rels_plan, f"{{{NS_R}}}Relationship")
                rel_ftr.set("Id", rid_nuevo_ftr)
                rel_ftr.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer")
                rel_ftr.set("Target", nombre_ftr)

                nuevo_ftr_ref = etree.SubElement(sectpr_plan, f"{{{NS_W}}}footerReference")
                nuevo_ftr_ref.set(f"{{{NS_W}}}type", "default")
                nuevo_ftr_ref.set(f"{{{NS_R_DOC}}}id", rid_nuevo_ftr)

                # Registrar en [Content_Types].xml
                file_ct = dir_plan / "[Content_Types].xml"
                if file_ct.is_file():
                    ct_root = etree.parse(str(file_ct)).getroot()
                    part_name = f"/word/{nombre_ftr}"
                    ya_existe_ct = any(ov.attrib.get("PartName") == part_name for ov in ct_root.findall(f"{{{NS_CT}}}Override"))
                    if not ya_existe_ct:
                        ov = etree.SubElement(ct_root, f"{{{NS_CT}}}Override")
                        ov.set("PartName", part_name)
                        ov.set("ContentType", "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml")
                        etree.ElementTree(ct_root).write(str(file_ct), xml_declaration=True, encoding="utf-8", standalone=True)

        mapa_rids: dict[str, str] = {}

        for rel in list(root_rels_cont):
            old_rid = rel.attrib.get("Id", "")
            tipo = rel.attrib.get("Type", "")
            target = rel.attrib.get("Target", "")
            target_mode = rel.attrib.get("TargetMode")

            # Estilos y settings de la plantilla tienen prioridad inmutable
            if tipo.endswith("/styles") or tipo.endswith("/settings") or tipo.endswith("/webSettings"):
                continue

            max_rid += 1
            new_rid = f"rId{max_rid}"
            mapa_rids[old_rid] = new_rid

            nueva_rel = etree.SubElement(root_rels_plan, f"{{{NS_R}}}Relationship")
            nueva_rel.set("Id", new_rid)
            nueva_rel.set("Type", tipo)
            nueva_rel.set("Target", target)
            if target_mode:
                nueva_rel.set("TargetMode", target_mode)

            # Copiar archivo destino si no existe en plantilla
            if not target.startswith("http://") and not target.startswith("https://") and not target.startswith("mailto:"):
                orig_file = (dir_cont / "word" / target).resolve()
                dest_file = (dir_plan / "word" / target).resolve()
                if orig_file.is_file() and not dest_file.is_file():
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(orig_file, dest_file)

        # Copiar recursos globales necesarios generados por motor (ej. numbering.xml, footnotes.xml)
        for parte_global in ("numbering.xml", "footnotes.xml"):
            f_orig = dir_cont / "word" / parte_global
            f_dest = dir_plan / "word" / parte_global
            if f_orig.is_file() and not f_dest.is_file():
                f_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f_orig, f_dest)
                max_rid += 1
                rel_glob = etree.SubElement(root_rels_plan, f"{{{NS_R}}}Relationship")
                rel_glob.set("Id", f"rId{max_rid}")
                rel_glob.set("Type", f"http://schemas.openxmlformats.org/officeDocument/2006/relationships/{parte_global.split('.')[0]}")
                rel_glob.set("Target", parte_global)

        # 3. Actualizar rIds en los elementos del contenido y suprimir saltos de sección intermedios
        hijos_contenido = []
        for child in list(body_cont):
            if child.tag == f"{{{NS_W}}}sectPr":
                continue  # No copiamos el sectPr del contenido generado

            # Si algún párrafo contiene un sectPr incrustado (salto de sección), convertirlo en salto de página simple
            ppr = child.find(f"{{{NS_W}}}pPr")
            if ppr is not None:
                sect_incrustado = ppr.find(f"{{{NS_W}}}sectPr")
                if sect_incrustado is not None:
                    ppr.remove(sect_incrustado)
                    r_br = etree.SubElement(child, f"{{{NS_W}}}r")
                    br = etree.SubElement(r_br, f"{{{NS_W}}}br")
                    br.set(f"{{{NS_W}}}type", "page")

            # Reemplazar referencias r:id / r:embed con los nuevos rIds
            if mapa_rids:
                xml_child_str = etree.tostring(child, encoding="utf-8").decode("utf-8")
                for o_id, n_id in mapa_rids.items():
                    xml_child_str = re.sub(
                        rf'(r:(?:id|embed|link)=["\']){re.escape(o_id)}(["\'])',
                        rf'\g<1>{n_id}\g<2>',
                        xml_child_str,
                    )
                child = etree.fromstring(xml_child_str.encode("utf-8"))

            hijos_contenido.append(child)

        # 4. Vaciar body de la plantilla y colocar los hijos del contenido
        # Si la plantilla tenía imágenes en el cuerpo, conservarlas marcadas con behindDoc="1"
        imagenes_cuerpo_plantilla = []
        for c in list(body_plan):
            if c.tag != f"{{{NS_W}}}sectPr":
                c_xml = etree.tostring(c, encoding="utf-8").decode("utf-8")
                if "<wp:anchor" in c_xml or "<wp:inline" in c_xml:
                    # Asegurar behindDoc="1"
                    if 'behindDoc="0"' in c_xml:
                        c_xml = c_xml.replace('behindDoc="0"', 'behindDoc="1"')
                    elif 'behindDoc=' not in c_xml:
                        c_xml = c_xml.replace("<wp:anchor ", '<wp:anchor behindDoc="1" ')
                    imagenes_cuerpo_plantilla.append(etree.fromstring(c_xml.encode("utf-8")))
            body_plan.remove(c)

        # Insertar primero las imágenes de fondo si las hubiera
        for img_p in imagenes_cuerpo_plantilla:
            body_plan.append(img_p)

        # Insertar los hijos del contenido
        for h in hijos_contenido:
            body_plan.append(h)

        # Restaurar el sectPr final
        body_plan.append(sectpr_plan)

        # 5. Guardar XMLs modificados
        file_rels_plan.parent.mkdir(parents=True, exist_ok=True)
        etree.ElementTree(root_rels_plan).write(
            str(file_rels_plan), xml_declaration=True, encoding="utf-8", standalone=True
        )

        etree.ElementTree(root_doc_plan).write(
            str(file_doc_plan), xml_declaration=True, encoding="utf-8", standalone=True
        )

        # 6. Reempaquetar zip final byte a byte
        if ruta_dest.exists():
            ruta_dest.unlink()

        with zipfile.ZipFile(ruta_dest, "w", zipfile.ZIP_DEFLATED) as z_out:
            for arch in dir_plan.rglob("*"):
                if arch.is_file():
                    arcname = arch.relative_to(dir_plan).as_posix()
                    z_out.write(arch, arcname)

    return ruta_dest


_CACHE_MEMBRETE_PDF: dict[str, tuple[float, dict[str, Any]]] = {}


def extraer_membrete_pdf(ruta_docx: Path | str) -> dict[str, Any]:
    """Extrae las imágenes de membrete y sus cotas métricas para el pipeline HTML/PDF.
    
    Aplica caché en memoria según el mtime del archivo DOCX.
    Devuelve un diccionario con:
        - archivo: nombre del archivo.
        - es_pagina_completa: booleano indicando si cubre la hoja entera.
        - elementos: lista de elementos con posicion ('fondo_completo', 'cabecera', 'pie'), data_uri, ancho_cm, alto_cm.
        - zona_sugerida_cm: zona calculada en cm (top, bottom, left, right).
    """
    import base64
    import mimetypes

    ruta_p = Path(ruta_docx).resolve()
    if not ruta_p.is_file():
        raise FileNotFoundError(f"El archivo '{ruta_p}' no existe.")

    mtime = ruta_p.stat().st_mtime
    ruta_str = str(ruta_p)
    if ruta_str in _CACHE_MEMBRETE_PDF:
        cached_mtime, cached_datos = _CACHE_MEMBRETE_PDF[ruta_str]
        if cached_mtime == mtime:
            return cached_datos

    analisis = analizar_membrete(ruta_p)
    elementos: list[dict[str, Any]] = []

    with zipfile.ZipFile(ruta_p, "r") as z:
        nombres = z.namelist()
        partes_inspeccionar = [
            n for n in nombres if re.match(r"^word/(document|header\d*|footer\d*)\.xml$", n)
        ]

        for parte in partes_inspeccionar:
            xml_str = z.read(parte).decode("utf-8", errors="replace")
            nom_xml = parte.split("/")[-1]
            rels_part = f"word/_rels/{nom_xml}.rels"
            rels_str = z.read(rels_part).decode("utf-8", errors="replace") if rels_part in nombres else ""

            for match in re.finditer(r"<wp:(anchor|inline)\b(.*?)</wp:\1>", xml_str, re.DOTALL):
                bloque = match.group(0)

                # Buscar id de imagen r:embed
                m_blip = re.search(r'r:embed="([^"]+)"', bloque)
                if not m_blip:
                    continue
                r_id = m_blip.group(1)

                # Buscar target en el archivo .rels
                m_target = re.search(rf'Id="{re.escape(r_id)}"[^>]*Target="([^"]+)"', rels_str)
                if not m_target:
                    continue
                target_rel = m_target.group(1).lstrip("/")
                if not target_rel.startswith("word/"):
                    target_rel = f"word/{target_rel}"

                if target_rel not in nombres:
                    continue

                bytes_img = z.read(target_rel)
                mime_type, _ = mimetypes.guess_type(target_rel)
                if not mime_type:
                    mime_type = "image/png" if target_rel.lower().endswith(".png") else "image/jpeg"

                b64_str = base64.b64encode(bytes_img).decode("ascii")
                data_uri = f"data:{mime_type};base64,{b64_str}"

                # Dimensiones en cm
                ext = re.search(r'<wp:extent\b[^>]*cx="(\d+)"[^>]*cy="(\d+)"', bloque)
                ancho_cm = _emu_a_cm(ext.group(1)) if ext else 21.0
                alto_cm = _emu_a_cm(ext.group(2)) if ext else 2.5

                ubicacion_general = "cabecera" if "header" in parte else ("pie" if "footer" in parte else "cuerpo")
                if alto_cm >= 25.0:
                    posicion = "fondo_completo"
                elif ubicacion_general == "pie":
                    posicion = "pie"
                else:
                    posicion = "cabecera"

                elementos.append({
                    "posicion": posicion,
                    "ubicacion_xml": ubicacion_general,
                    "target_rel": target_rel,
                    "bytes_img": bytes_img,
                    "data_uri": data_uri,
                    "ancho_cm": ancho_cm,
                    "alto_cm": alto_cm,
                })

    es_pagina_completa = any(el["posicion"] == "fondo_completo" for el in elementos)

    resultado = {
        "archivo": ruta_p.name,
        "es_pagina_completa": es_pagina_completa,
        "elementos": elementos,
        "zona_sugerida_cm": analisis["zona_sugerida_cm"],
    }

    _CACHE_MEMBRETE_PDF[ruta_str] = (mtime, resultado)
    return resultado



