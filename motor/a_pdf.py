"""Motor de Publicación Editorial PDF de Alta Gama (HTML5 + CSS Paged Media + Chromium Headless + PyMuPDF).

Arquitectura:
  1. Reemplazo de diagramas Mermaid por gráficos escalados sin deformación.
  2. Compilación a HTML5 semántico con MathML nativo vectorial para ecuaciones (KaTeX-compatible).
  3. Renderizado de alta fidelidad vía Chromium Headless (Edge / Chrome) con reglas CSS @page:
     - Márgenes normativos (20mm o 25.4mm APA 7ma).
     - Control estricto anti-huérfanas (widows: 3; orphans: 3).
     - Ruptura limpia de páginas (break-inside: avoid en tablas, notas, figuras y ecuaciones).
     - Títulos blindados contra saltos huérfanos (break-after: avoid).
     - Cabeceras de tabla repetidas en saltos (thead: display table-header-group).
  4. Post-procesado vectorial de precisión con PyMuPDF (fitz):
     - Estampado de Running Header superior discreto.
     - Filete ultrafino (0.5 pt) de pie de página en tono secundario.
     - Lógica Anti-Colisión Inteligente entre Texto de Pie y Numeración de Páginas.
     - Formatos de numeración: 'Página X de Y', 'X / Y', 'X'.
     - Exclusión automática en página de portada.
     - Generación de Marcadores / Outlines nativos de PDF para navegación por capítulos.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pymupdf

from motor.a_docx import ruta_pandoc
from motor.a_html import incrustar_imagenes_base64_en_markdown
from motor.a_mermaid import reemplazar_mermaid_por_imagenes
from motor.qa import contar_formulas
from motor.saltos_capitulo import inyectar_saltos_capitulo_html

# Paletas de Colores Sobrias y Ejecutivas para PDF (docs/mejoras de app4 (pdf).md)
PALETAS_EDITORIAL_PDF: dict[str, dict[str, str]] = {
    "pizarra_carbon": {
        "nombre": "Pizarra & Carbón",
        "primario": "#1E293B",      # Gris Pizarra Profundo / Casi Negro
        "secundario": "#475569",    # Gris Acero Templado
        "fondo_suave": "#F8FAFC",   # Blanco Humo / Gris Hielo
        "texto": "#0F172A",
        "borde_tabla": "#CBD5E1",
    },
    "azul_prusia": {
        "nombre": "Azul Prusia & Acero",
        "primario": "#1E3A5F",      # Azul Marino Prusia Oscuro
        "secundario": "#2B547E",    # Azul Cobalto Apagado
        "fondo_suave": "#F0F4F8",   # Azul Niebla Ultrasuave
        "texto": "#0F172A",
        "borde_tabla": "#B0C4DE",
    },
    "grafito_salvia": {
        "nombre": "Grafito & Salvia",
        "primario": "#1C2E24",
        "secundario": "#3F5E4D",
        "fondo_suave": "#F4F7F5",
        "texto": "#111827",
        "borde_tabla": "#A3C4B3",
    },
    "onix_burdeos": {
        "nombre": "Ónix & Burdeos Imperial",
        "primario": "#2D1B22",
        "secundario": "#5C2C38",
        "fondo_suave": "#FAF6F7",
        "texto": "#111827",
        "borde_tabla": "#D1B2BA",
    },
    "negro_papel": {
        "nombre": "Negro Puro & Papel",
        "primario": "#0F172A",
        "secundario": "#334155",
        "fondo_suave": "#F3F4F6",
        "texto": "#000000",
        "borde_tabla": "#94A3B8",
    },
}


class ErrorMotorPDF(RuntimeError):
    """Excepción tipada para fallos del motor editorial PDF."""


def ruta_chromium() -> str | None:
    """Localiza el ejecutable de Microsoft Edge o Google Chrome en el sistema."""
    candidatos = [
        # Edge (disponible por defecto en Windows 10 y 11)
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        # Chrome
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for ruta in candidatos:
        if Path(ruta).is_file():
            return ruta

    en_path = shutil.which("msedge") or shutil.which("chrome") or shutil.which("chromium")
    if en_path:
        return en_path

    return None


def _hex_a_rgb_unitario(hex_color: str) -> tuple[float, float, float]:
    """Convierte un color '#RRGGBB' a tupla (r, g, b) con valores entre 0.0 y 1.0."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)
    return (0.28, 0.33, 0.41)


def _transformar_kpi_premium(texto: str) -> str:
    """Convierte bloques :::kpi ... ::: en HTML crudo de tarjetas (pasa por pandoc)."""
    import re
    patron = re.compile(r":::kpi\s*\n(.*?)\n:::", re.DOTALL | re.IGNORECASE)

    def _repl(m):
        inner = m.group(1).strip()
        cards = []
        for line in inner.splitlines():
            line = line.strip()
            if not line:
                continue
            # formato: **label** | value  o  label | value
            if "|" in line:
                partes = line.split("|", 1)
                label = partes[0].strip().strip("*").strip()
                valor = partes[1].strip() if len(partes) > 1 else ""
            else:
                label = line.strip("*").strip()
                valor = ""
            cards.append(
                f'<div class="kpi-card"><div class="kpi-valor">{valor}</div>'
                f'<div class="kpi-label">{label}</div></div>'
            )
        return '<div class="kpi-grid">\n' + "\n".join(cards) + "\n</div>"

    return patron.sub(_repl, texto)


def _postprocesar_columnas_premium(html: str) -> str:
    """Divide los div.columns-premium en dos columnas usando el <hr /> como separador."""
    import re
    patron = re.compile(r'<div class="columns-premium">(.*?)</div>', re.DOTALL)

    def _repl(m):
        inner = m.group(1)
        # separar por <hr> o <hr />
        partes = re.split(r"<hr\s*/?>", inner, flags=re.IGNORECASE)
        cols = []
        for p in partes:
            p = p.strip()
            if p:
                cols.append(f"<div>{p}</div>")
        if len(cols) < 2:
            cols = [f"<div>{inner.strip()}</div>", "<div></div>"]
        return '<div class="columns-premium">\n' + "\n".join(cols) + "\n</div>"

    return patron.sub(_repl, html)


def _imagen_a_datauri(img) -> str:
    """Convierte una imagen (ruta o data-uri) a data URI base64."""
    import base64
    import mimetypes
    from pathlib import Path
    if isinstance(img, str) and img.strip().startswith("data:"):
        return img.strip()
    p = Path(str(img))
    if p.exists():
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    return str(img)


def _layout_fotos(n: int) -> str:
    n = max(1, min(6, n))
    layouts = {
        1: "grid-template-columns: 1fr;",
        2: "grid-template-columns: 1fr 1fr;",
        3: "grid-template-columns: 1fr 1fr; grid-template-rows: auto auto;",
        4: "grid-template-columns: 1fr 1fr;",
        5: "grid-template-columns: 1fr 1fr;",
        6: "grid-template-columns: 1fr 1fr 1fr;",
    }
    return layouts.get(n, "grid-template-columns: 1fr 1fr;")


def _generar_html_portada_premium(tema: str, datos: dict, imagenes: list, paleta: dict) -> str:
    """Genera el HTML de una portada premium (primera página)."""
    tema = (tema or "clasica_blanca").lower()
    tipo_doc = datos.get("tipo_documento", "ESTUDIO DE CONSULTORÍA DEL PROYECTO:")
    titulo = datos.get("titulo_proyecto", "")
    memoria = datos.get("memoria_fase", "")
    componente = datos.get("componente", "")
    consultor = datos.get("consultor", "")
    fecha = datos.get("fecha", "")
    codigo = datos.get("codigo_proyecto", "")

    imgs = [_imagen_a_datauri(i) for i in (imagenes or [])]
    n = len(imgs)

    # Estilos por tema
    if tema == "ejecutiva_navy":
        bg = "#1E3A5F"
        fg = "#FFFFFF"
        acento = "#38bdf8"
        card_bg = "rgba(255,255,255,0.08)"
    elif tema == "consultoria_verde":
        bg = "#1C2E24"
        fg = "#FFFFFF"
        acento = "#34d399"
        card_bg = "rgba(255,255,255,0.08)"
    elif tema == "blueprint":
        bg = "#0F172A"
        fg = "#E2E8F0"
        acento = "#60A5FA"
        card_bg = "rgba(96,165,250,0.08)"
    elif tema == "minimal_slate":
        bg = "#F8FAFC"
        fg = "#0F172A"
        acento = paleta.get("primario", "#1E293B")
        card_bg = "#FFFFFF"
    elif tema == "foto_hero":
        bg = "#0F172A"
        fg = "#FFFFFF"
        acento = "#F59E0B"
        card_bg = "rgba(255,255,255,0.10)"
    else:  # clasica_blanca
        bg = "#FFFFFF"
        fg = "#0F172A"
        acento = paleta.get("primario", "#1E293B")
        card_bg = "#F8FAFC"

    # Galería de fotos
    fotos_html = ""
    if imgs:
        layout = _layout_fotos(n)
        cells = []
        for src in imgs:
            cells.append(f'<div class="portada-foto"><img src="{src}" alt="Foto de campo" /></div>')
        fotos_html = f'<div class="portada-galeria" style="{layout}">' + "".join(cells) + "</div>"

    html = f'''
<div class="portada-premium tema-{tema}" style="background:{bg}; color:{fg};">
  <div class="portada-banda" style="border-bottom: 3pt solid {acento};"></div>
  <div class="portada-contenido">
    <p class="portada-tipo" style="color:{acento};">{tipo_doc}</p>
    <h1 class="portada-titulo" style="color:{fg};">{titulo}</h1>
    {f'<p class="portada-memoria" style="color:{acento};">{memoria}</p>' if memoria else ""}
    {f'<p class="portada-componente">{componente}</p>' if componente else ""}
    {fotos_html}
    <div class="portada-datos" style="background:{card_bg};">
      {f'<p><b>Consultor:</b> {consultor}</p>' if consultor else ""}
      {f'<p><b>Fecha:</b> {fecha}</p>' if fecha else ""}
      {f'<p><b>Código:</b> {codigo}</p>' if codigo else ""}
    </div>
  </div>
</div>
'''
    return html


def _generar_html_impresion(
    cuerpo_html: str,
    titulo: str,
    paleta: dict[str, str],
    fuente: str = "Calibri",
    tamanio_pt: float = 11.0,
    interlineado: float = 1.15,
    justificado: bool = True,
    estilo_maquetacion: str = "informe",
    normas_apa: bool = False,
    numerar_ecuaciones: bool = False,
    salto_capitulo: bool = False,
    modo_diseno: str = "estandar",
    elementos_membrete: list[dict[str, Any]] | None = None,
    zona_cm: dict[str, float] | None = None,
) -> str:
    """Genera el documento HTML5 completo con reglas CSS Paged Media optimizadas para Chromium."""
    if zona_cm:
        t_cm = round(float(zona_cm.get("top", 2.5)), 2)
        r_cm = round(float(zona_cm.get("right", 2.5)), 2)
        b_cm = round(float(zona_cm.get("bottom", 2.0)), 2)
        l_cm = round(float(zona_cm.get("left", 2.5)), 2)
        margen_css = f"{t_cm}cm {r_cm}cm {b_cm}cm {l_cm}cm"
    else:
        margen_css = "25.4mm" if normas_apa else "20mm 20mm 25mm 20mm"
    sangria_p = "12.7mm" if normas_apa else "0"
    alineacion_p = "justify" if justificado else "left"

    # Reglas para Salto de Página en Capítulos (H1 / 1, 2, 3...)
    salto_capitulo_css = ""
    if salto_capitulo:
        # Fase 3 (v1.20.5): el salto lo decide EXCLUSIVAMENTE el marcador que inyecta
        # motor/saltos_capitulo.py antes de los H1 seleccionados (H1-only + excepción
        # de primera hoja). Las reglas previas sobre `h1` y `hr` genéricos provocaban
        # saltos en el primer capítulo, en separadores `---` entre H2 y hojas en blanco.
        salto_capitulo_css = """
    /* Salto de capítulo: solo el marcador canónico inyectado antes de H1 (2.º en adelante) */
    .cuerpo-editorial .capitulo-salto-pagina {
        page-break-before: always !important;
        break-before: page !important;
        column-span: all !important;
        clear: both !important;
    }
    /* H1/H2/H3 y separadores nunca fuerzan salto por sí mismos */
    .cuerpo-editorial h1,
    .cuerpo-editorial h2,
    .cuerpo-editorial h3,
    .cuerpo-editorial hr {
        page-break-before: auto !important;
        break-before: auto !important;
    }
    """

    # Reglas para Modos Adicionales de Diseño (Estándar, 2 Columnas, Paper Científico, Revista)
    modo_clean = (modo_diseno or "estandar").lower()
    diseno_columnas_css = ""
    if modo_clean in ("dos_columnas", "2_columnas", "2col"):
        diseno_columnas_css = f"""
    .cuerpo-editorial {{
        column-count: 2;
        column-gap: 16mm;
        text-align: {alineacion_p};
    }}
    .cuerpo-editorial h1,
    .cuerpo-editorial .full-width,
    .cuerpo-editorial table,
    .cuerpo-editorial .table-container,
    .cuerpo-editorial figure,
    .cuerpo-editorial .mermaid-contenedor,
    .cuerpo-editorial img,
    .cuerpo-editorial p:has(> img),
    .cuerpo-editorial .indice-final-documento,
    .cuerpo-editorial .bloque-firma {{
        column-span: all !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        width: 100% !important;
        max-width: 100% !important;
        display: block !important;
        clear: both !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }}
    .cuerpo-editorial figure img,
    .cuerpo-editorial .mermaid-contenedor img,
    .cuerpo-editorial img {{
        display: block !important;
        margin: 1.2rem auto !important;
        width: auto !important;
        max-width: 100% !important;
        min-width: 60% !important;
        height: auto !important;
        max-height: 22cm !important;
        object-fit: contain !important;
    }}
    """
    elif modo_clean in ("paper_cientifico", "paper", "cientifico"):
        diseno_columnas_css = f"""
    body {{
        font-family: "Times New Roman", "Cambria", "Newsreader", serif !important;
        font-size: 10pt !important;
        line-height: 1.25 !important;
    }}
    .cuerpo-editorial {{
        column-count: 2;
        column-gap: 14mm;
        text-align: justify !important;
    }}
    .cuerpo-editorial h1 {{
        column-span: all;
        font-size: 15pt !important;
        text-align: center !important;
        text-transform: uppercase;
        border-bottom: 1.5pt solid #000000;
        margin-bottom: 1.2em;
        letter-spacing: 0.5px;
    }}
    .cuerpo-editorial h2 {{
        font-size: 11pt !important;
        text-transform: uppercase;
        border-bottom: 0.5pt solid #cbd5e1;
        margin-top: 1.2em;
    }}
    .cuerpo-editorial h3 {{
        font-size: 10pt !important;
        font-style: italic;
    }}
    .cuerpo-editorial blockquote:first-of-type {{
        column-span: all;
        background: transparent !important;
        border-left: none !important;
        border-top: 1pt solid #000;
        border-bottom: 1pt solid #000;
        padding: 8px 18px !important;
        font-style: italic;
        margin: 1.2em auto;
        font-size: 9pt;
    }}
    .cuerpo-editorial table,
    .cuerpo-editorial .table-container,
    .cuerpo-editorial figure,
    .cuerpo-editorial .mermaid-contenedor,
    .cuerpo-editorial img,
    .cuerpo-editorial p:has(> img),
    .cuerpo-editorial .indice-final-documento,
    .cuerpo-editorial .bloque-firma {
        column-span: all !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        width: 100% !important;
        max-width: 100% !important;
        display: block !important;
        clear: both !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    .cuerpo-editorial figure img,
    .cuerpo-editorial .mermaid-contenedor img,
    .cuerpo-editorial img {
        display: block !important;
        margin: 1.2rem auto !important;
        max-width: 95% !important;
        height: auto !important;
        object-fit: contain !important;
    }
    """
    elif modo_clean in ("revista", "magazine", "editorial"):
        diseno_columnas_css = f"""
    body {{
        font-family: "Georgia", "Newsreader", "Times New Roman", serif;
        font-size: 10.5pt;
        line-height: 1.4;
    }}
    .cuerpo-editorial {{
        column-count: 2;
        column-gap: 18mm;
        text-align: justify;
    }}
    .cuerpo-editorial h1 {{
        column-span: all;
        font-size: 22pt;
        font-weight: 800;
        line-height: 1.15;
        border-bottom: 3pt solid {paleta["secundario"]};
        padding-bottom: 6px;
        margin-bottom: 1em;
    }}
    .cuerpo-editorial h2 {{
        font-size: 13pt;
        color: {paleta["primario"]};
        border-bottom: 1pt solid #e2e8f0;
    }}
    .cuerpo-editorial > p:first-of-type::first-letter {{
        font-size: 3.2em;
        float: left;
        line-height: 0.8;
        margin: 4px 8px 0 0;
        font-weight: 800;
        color: {paleta["primario"]};
        font-family: "Arial", sans-serif;
    }}
    .cuerpo-editorial blockquote {{
        border-left: 4pt solid {paleta["secundario"]};
        background: {paleta["fondo_suave"]};
        font-style: italic;
        padding: 12px 16px;
        margin: 1.5em 0;
        break-inside: avoid;
    }}
    .cuerpo-editorial table,
    .cuerpo-editorial .table-container,
    .cuerpo-editorial figure,
    .cuerpo-editorial .mermaid-contenedor,
    .cuerpo-editorial img,
    .cuerpo-editorial p:has(> img),
    .cuerpo-editorial .indice-final-documento,
    .cuerpo-editorial .bloque-firma {{
        column-span: all !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        width: 100% !important;
        max-width: 100% !important;
        display: block !important;
        clear: both !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }}
    .cuerpo-editorial figure img,
    .cuerpo-editorial .mermaid-contenedor img,
    .cuerpo-editorial img {{
        display: block !important;
        margin: 1.2rem auto !important;
        max-width: 95% !important;
        height: auto !important;
        object-fit: contain !important;
    }}
    """

    elif modo_clean in ("premium", "premium_ejecutivo", "ejecutivo"):
        diseno_columnas_css = f"""
    /* ===== MODO PREMIUM EJECUTIVO ===== */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 10px;
        margin: 1.4em 0 1.8em 0;
        break-inside: avoid;
        page-break-inside: avoid;
    }}
    .kpi-card {{
        background: var(--fondo-suave, {paleta["fondo_suave"]});
        border-left: 3.5pt solid {paleta["primario"]};
        border-radius: 0 6px 6px 0;
        padding: 12px 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }}
    .kpi-valor {{
        font-size: 1.35em;
        font-weight: 800;
        color: {paleta["primario"]};
        line-height: 1.15;
    }}
    .kpi-label {{
        font-size: 0.78em;
        color: {paleta["secundario"]};
        margin-top: 3px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }}
    .columns-premium {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14mm;
        margin: 1.3em 0;
        break-inside: avoid;
        page-break-inside: avoid;
    }}
    .figura-premium {{
        margin: 1.6em auto;
        text-align: center;
        break-inside: avoid;
        page-break-inside: avoid;
    }}
    .figura-premium img {{
        max-width: 100%;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    .caption-premium {{
        font-size: 8.5pt;
        color: #64748b;
        font-style: italic;
        margin-top: 6px;
    }}
    .callout-premium {{
        border-left: 4pt solid {paleta["secundario"]};
        background: {paleta["fondo_suave"]};
        padding: 12px 16px;
        margin: 1.5em 0;
        break-inside: avoid;
        border-radius: 0 6px 6px 0;
    }}
    .separador-premium {{
        border: none;
        border-top: 1.5pt solid {paleta["secundario"]};
        margin: 1.8em 0;
        opacity: 0.6;
    }}
    .cuerpo-editorial h1 {{
        color: {paleta["primario"]};
        letter-spacing: 0.3px;
    }}
    .cuerpo-editorial table {{
        border-collapse: collapse;
        width: 100%;
        break-inside: avoid;
    }}
    .cuerpo-editorial th {{
        background: {paleta["primario"]};
        color: #ffffff;
        font-weight: 700;
        padding: 8px 10px;
    }}
    .cuerpo-editorial td {{
        padding: 6px 10px;
        border-bottom: 0.5pt solid #e2e8f0;
    }}
    .cuerpo-editorial figure,
    .cuerpo-editorial .mermaid-contenedor,
    .cuerpo-editorial img,
    .cuerpo-editorial .table-container,
    .cuerpo-editorial .indice-final-documento,
    .cuerpo-editorial .bloque-firma {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }}
    """

    portada_html = ""
    if estilo_maquetacion == "portada":
        portada_html = f"""
        <div class="portada-editorial">
            <div class="portada-decoracion"></div>
            <div class="portada-contenido">
                <p class="portada-categoria">MEMORIA TÉCNICA DE CONSULTORÍA</p>
                <h1 class="portada-titulo">{titulo}</h1>
                <div class="portada-filete"></div>
                <p class="portada-metadato"><b>Fecha:</b> Documento Oficial</p>
                <p class="portada-metadato"><b>Especialidad:</b> Ingeniería Hidrosanitaria & Civil</p>
                <p class="portada-autor">Preparado con MarkFlow AI Suite</p>
            </div>
        </div>
        """

    # Fondo transparente si hay membrete para permitir que PyMuPDF estampe el fondo en toda la hoja A4
    fondo_body_css = "background: transparent !important;" if elementos_membrete else "background: #ffffff;"

    portada_css = """
    .portada-premium {
        page-break-after: always;
        min-height: 100%;
        padding: 2cm 1.5cm;
        box-sizing: border-box;
        position: relative;
        font-family: "Calibri", "Inter", sans-serif;
    }
    .portada-premium .portada-banda {
        height: 6pt;
        margin-bottom: 2cm;
    }
    .portada-premium .portada-tipo {
        font-size: 10pt;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-bottom: 0.6cm;
    }
    .portada-premium .portada-titulo {
        font-size: 20pt;
        font-weight: 800;
        line-height: 1.15;
        margin: 0 0 0.4cm 0;
    }
    .portada-premium .portada-memoria {
        font-size: 12pt;
        font-weight: 600;
        margin-bottom: 0.3cm;
    }
    .portada-premium .portada-componente {
        font-size: 11pt;
        opacity: 0.85;
        margin-bottom: 1.2cm;
    }
    .portada-premium .portada-galeria {
        display: grid;
        gap: 8px;
        margin: 1.2cm 0;
    }
    .portada-premium .portada-foto img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 4px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.12);
    }
    .portada-premium .portada-datos {
        margin-top: 1.5cm;
        padding: 1cm;
        border-radius: 6px;
        font-size: 10pt;
        line-height: 1.5;
    }
    .portada-premium .portada-datos p {
        margin: 0.2cm 0;
    }
    """
    css = portada_css + f"""
    @page {{
        size: A4;
        margin: {margen_css};
    }}

    *, *::before, *::after {{
        box-sizing: border-box;
    }}

    html {{
        background: transparent !important;
    }}

    /* Supresión absoluta de elementos de interfaz de usuario en PDF */
    .no-print, header.no-print, nav, aside, button,
    .action-icon, .btn, .hdxf-btn, .hdxf-header, .hdxf-sidebar,
    .hdxf-header-actions, #hdxfThemeToggle, #btn-tema, .theme-toggle,
    .boton-flotante, .floating-btn, .toolbar, .barra-herramientas,
    [class*="theme-toggle"], [class*="boton-flotante"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        overflow: hidden !important;
        opacity: 0 !important;
    }}
    @media print {{
        .no-print, header, nav, aside, button, .action-icon, .hdxf-btn, [class*="theme-toggle"] {{
            display: none !important;
        }}
    }}

    body {{
        font-family: "{fuente}", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        font-size: {tamanio_pt}pt;
        line-height: {interlineado};
        color: {paleta["texto"]};
        {fondo_body_css}
        margin: 0;
        padding: 0;
        text-rendering: optimizeLegibility;
    }}

    /* Portada Editorial */
    .portada-editorial {{
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 40mm 20mm 30mm 20mm;
        page-break-after: always;
        break-after: page;
        position: relative;
    }}
    .portada-categoria {{
        font-size: 9pt;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-weight: 700;
        color: {paleta["secundario"]};
        margin: 0 0 15px 0;
    }}
    .portada-titulo {{
        font-size: 26pt;
        line-height: 1.2;
        color: {paleta["primario"]};
        margin: 0 0 20px 0;
        font-weight: 800;
        border: none;
    }}
    .portada-filete {{
        width: 80px;
        height: 4px;
        background: {paleta["secundario"]};
        margin: 0 0 35px 0;
    }}
    .portada-metadato {{
        font-size: 10pt;
        margin: 6px 0;
        color: #475569;
    }}
    .portada-autor {{
        margin-top: 40px;
        font-size: 9.5pt;
        font-weight: 600;
        color: {paleta["primario"]};
    }}

    /* Jerarquía Tipográfica */
    h1, h2, h3, h4, h5, h6 {{
        color: {paleta["primario"]};
        font-weight: 700;
        break-after: avoid;
        page-break-after: avoid;
    }}

    h1 {{
        font-size: 18pt;
        line-height: 1.25;
        margin-top: 1.6em;
        margin-bottom: 0.6em;
        padding-bottom: 4px;
        border-bottom: 1.5pt solid {paleta["secundario"]};
    }}

    h2 {{
        font-size: 14pt;
        line-height: 1.3;
        margin-top: 1.4em;
        margin-bottom: 0.5em;
    }}

    h3 {{
        font-size: 12pt;
        line-height: 1.35;
        margin-top: 1.2em;
        margin-bottom: 0.4em;
    }}

    p {{
        margin: 0 0 0.8em 0;
        text-align: {alineacion_p};
        text-indent: {sangria_p};
        orphans: 3;
        widows: 3;
    }}

    /* Listas y viñetas SIEMPRE alineadas estrictamente a la izquierda */
    ul, ol {{
        margin: 0.5em 0 1em 1.5em;
        padding: 0;
        text-align: left !important;
    }}
    li {{
        text-align: left !important;
        margin-bottom: 0.3em;
    }}

    /* Tablas Editoriales */
    table, .table-container {{
        width: 100%;
        border-collapse: collapse;
        margin: 1.5em 0;
        font-size: {max(7.5, tamanio_pt - 1.5)}pt;
        line-height: 1.2;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }}

    thead {{
        display: table-header-group;
    }}

    tr {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }}

    th {{
        background-color: {paleta["primario"]} !important;
        color: #ffffff !important;
        font-weight: 700;
        text-align: left;
        padding: 7px 10px;
        border-bottom: 1.5pt solid {paleta["secundario"]};
    }}

    td {{
        padding: 6px 10px;
        border-bottom: 0.5pt solid {paleta["borde_tabla"]};
        color: {paleta["texto"]};
    }}

    tbody tr:nth-child(even) {{
        background-color: {paleta["fondo_suave"]};
    }}

    /* Notas Técnicas / Callouts */
    blockquote {{
        margin: 1.2em 0;
        padding: 10px 14px;
        background-color: {paleta["fondo_suave"]};
        border-left: 3.5pt solid {paleta["primario"]};
        border-radius: 0 4px 4px 0;
        text-align: justify !important;
        break-inside: avoid;
        page-break-inside: avoid;
    }}
    blockquote p {{
        margin: 0;
        text-align: justify !important;
        text-indent: 0 !important;
        font-size: {tamanio_pt - 0.5}pt;
        color: {paleta["texto"]};
    }}

    /* Ecuaciones Matemáticas MathML */
    math {{
        font-family: "Cambria Math", "Latin Modern Math", serif;
    }}
    .math.display, div.equation, p:has(> math[display="block"]) {{
        margin: 1.2em 0;
        text-align: center;
        break-inside: avoid;
        page-break-inside: avoid;
    }}

    /* Figuras y Diagramas Mermaid */
    figure, img, .mermaid-contenedor {{
        margin: 1.5em auto;
        text-align: center;
        display: block;
        max-width: 100%;
        break-inside: avoid;
        page-break-inside: avoid;
    }}
    img {{
        max-height: 22cm;
        max-width: 100%;
        height: auto;
        object-fit: contain;
    }}
    .figura-flotante-izq, figure.flotante-izq, img.flotante-izq {{
        float: left !important;
        max-width: 48% !important;
        margin: 0.5rem 1cm 0.75rem 0 !important;
        clear: left !important;
    }}
    .figura-flotante-der, figure.flotante-der, img.flotante-der {{
        float: right !important;
        max-width: 48% !important;
        margin: 0.5rem 0 0.75rem 1cm !important;
        clear: right !important;
    }}
    figcaption {{
        margin-top: 6px;
        font-size: 8.5pt;
        color: #64748B;
        font-style: italic;
    }}

    code {{
        font-family: "Consolas", "Courier New", monospace;
        font-size: 0.9em;
        background: #f1f5f9;
        padding: 1px 4px;
        border-radius: 3px;
    }}

    /* Bloques colapsables details: siempre expandidos para impresión PDF */
    details, .cuerpo-editorial details {{
        margin: 1.5em auto;
        display: block !important;
        break-inside: avoid;
        page-break-inside: avoid;
    }}
    details summary {{
        font-size: 8.5pt;
        font-weight: 700;
        color: #334155;
        margin-bottom: 6px;
        list-style: none;
    }}
    details summary::-webkit-details-marker {{
        display: none;
    }}

    {salto_capitulo_css}
    {diseno_columnas_css}
    """

    # Forzar que los bloques details se abran para que la imagen salga en el PDF
    cuerpo_con_details_abiertos = re.sub(r'<details\b(?![^>]*\bopen\b)', '<details open', cuerpo_html, flags=re.IGNORECASE)

    # El membrete es estampado a nivel físico en la hoja completa A4 mediante PyMuPDF
    # para evitar que los márgenes de texto (@page) recorten o desplacen la plantilla.
    membrete_html = ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>{titulo}</title>
    <style>
{css}
    </style>
</head>
<body>
{membrete_html}
{portada_html}
<div class="cuerpo-editorial">
{cuerpo_con_details_abiertos}
</div>
</body>
</html>"""


def _postprocesar_con_pymupdf(
    ruta_pdf: Path,
    titulo: str,
    paleta: dict[str, str],
    pie_pagina: str = "",
    alineacion_pie: str = "derecha",
    numerar_paginas: bool = True,
    formato_num: str = "pagina_x_de_y",
    alineacion_num: str = "derecha",
    running_header: bool = False,
    running_header_texto: str = "",
    omitir_portada: bool = False,
    encabezados_meta: list[tuple[int, str]] | None = None,
    indices_items: list[tuple[str, str]] | None = None,
    tiene_membrete: bool = False,
    zona_cm: dict[str, float] | None = None,
    elementos_membrete: list[dict[str, Any]] | None = None,
) -> None:
    """Aplica estampados vectoriales de precisión: membrete A4 bleed, running header, footer y numeración."""
    doc = pymupdf.open(str(ruta_pdf))
    total_hojas = len(doc)
    if total_hojas == 0:
        return

    rgb_secundario = _hex_a_rgb_unitario(paleta["secundario"])
    rgb_texto = (0.28, 0.33, 0.41)  # Gris pizarra sobrio #475569

    inicio_idx = 1 if (omitir_portada and total_hojas > 1) else 0

    # Si hay membrete, respetar sus márgenes métricos
    margen_l_pt = float(zona_cm.get("left", 2.5)) * 28.346 if (tiene_membrete and zona_cm) else 56.7
    margen_r_pt = float(zona_cm.get("right", 2.5)) * 28.346 if (tiene_membrete and zona_cm) else 56.7
    margen_b_pt = float(zona_cm.get("bottom", 2.0)) * 28.346 if (tiene_membrete and zona_cm) else 56.7

    for i in range(inicio_idx, total_hojas):
        p = doc[i]
        rect = p.rect
        ancho, alto = rect.width, rect.height
        x_min = margen_l_pt
        x_max = ancho - margen_r_pt
        num_visible = (i - inicio_idx + 1)
        total_visible = (total_hojas - inicio_idx)

        # 0. Estampado de Hoja de Membrete en Fondo Físico A4 (Detrás del texto, borde a borde)
        # La plantilla ocupa toda el área física de la hoja A4 sin ser afectada por los márgenes de texto.
        if elementos_membrete:
            for el in elementos_membrete:
                pos = el.get("posicion", "cabecera")
                alto_cm = float(el.get("alto_cm", 2.5))
                alto_pt = alto_cm * 28.3464567

                img_bytes = el.get("bytes_img")
                if not img_bytes and el.get("data_uri"):
                    import base64
                    uri = el["data_uri"]
                    if "," in uri:
                        img_bytes = base64.b64decode(uri.split(",", 1)[1])
                if not img_bytes:
                    continue

                if pos == "fondo_completo":
                    # Toda el área de la hoja A4 de borde a borde (0, 0 a ancho, alto)
                    rect_dest = pymupdf.Rect(0, 0, ancho, alto)
                elif pos == "pie":
                    # Franja de pie ocupando todo el ancho físico de la hoja
                    rect_dest = pymupdf.Rect(0, alto - alto_pt, ancho, alto)
                else:  # cabecera
                    # Franja de cabecera ocupando todo el ancho físico de la hoja
                    rect_dest = pymupdf.Rect(0, 0, ancho, alto_pt)

                p.insert_image(rect_dest, stream=img_bytes, overlay=False, keep_proportion=False)

        # 1. Running Header discreto dinámico (omitido si hay hoja de membrete)
        if running_header and not tiene_membrete:
            y_header = 35.0
            p.draw_line(
                pymupdf.Point(x_min, y_header + 8),
                pymupdf.Point(x_max, y_header + 8),
                color=rgb_secundario,
                width=0.4,
            )
            header_txt_base = running_header_texto.strip() or titulo.strip()
            tit_txt = (header_txt_base[:65] + "...") if len(header_txt_base) > 65 else header_txt_base
            p.insert_text(
                pymupdf.Point(x_min, y_header),
                tit_txt,
                fontsize=8.0,
                color=rgb_texto,
            )

        # 2. Línea divisoria superior de Footer (omitida si hay hoja de membrete para no pisar gráficos)
        if not tiene_membrete:
            y_linea_footer = alto - 45.0
            p.draw_line(
                pymupdf.Point(x_min, y_linea_footer),
                pymupdf.Point(x_max, y_linea_footer),
                color=rgb_secundario,
                width=0.5,
            )

        # 3. Formateo del texto de numeración
        texto_num = ""
        if numerar_paginas:
            f_clean = (formato_num or "").lower()
            if "x_de_y" in f_clean or "x / y" in f_clean:
                texto_num = f"{num_visible} / {total_visible}"
            elif f_clean == "x" or "solo" in f_clean:
                texto_num = str(num_visible)
            else:
                texto_num = f"Página {num_visible} de {total_visible}"

        texto_pie_limpio = pie_pagina.strip()
        pos_pie_clean = (alineacion_pie or "derecha").lower()
        pos_num_clean = (alineacion_num or "derecha").lower()

        # 4. Posición vertical y Anti-Colisión
        if tiene_membrete:
            # En membrete, ubicar el número en el tercio inferior del margen reservado
            y_texto_footer = alto - max(16.0, margen_b_pt * 0.45)
        else:
            y_texto_footer = alto - 30.0

        colision = False
        if texto_pie_limpio and texto_num:
            if pos_pie_clean == pos_num_clean:
                colision = True

        if colision:
            # Separación elegante: texto a la izquierda, número a la derecha
            p.insert_text(
                pymupdf.Point(x_min, y_texto_footer),
                texto_pie_limpio,
                fontsize=8.5,
                color=rgb_texto,
            )
            ancho_n = pymupdf.get_text_length(texto_num, fontsize=8.5)
            p.insert_text(
                pymupdf.Point(x_max - ancho_n, y_texto_footer),
                texto_num,
                fontsize=8.5,
                color=rgb_texto,
            )
        else:
            # Estampar texto de pie
            if texto_pie_limpio and not tiene_membrete:
                ancho_p = pymupdf.get_text_length(texto_pie_limpio, fontsize=8.5)
                if pos_pie_clean in ("centro", "centrado"):
                    x_p = (ancho - ancho_p) / 2.0
                elif pos_pie_clean == "izquierda":
                    x_p = x_min
                else:
                    x_p = x_max - ancho_p
                p.insert_text(
                    pymupdf.Point(x_p, y_texto_footer),
                    texto_pie_limpio,
                    fontsize=8.5,
                    color=rgb_texto,
                )

            # Estampar número de página
            if texto_num:
                ancho_n = pymupdf.get_text_length(texto_num, fontsize=8.5)
                if pos_num_clean in ("centro", "centrado"):
                    x_n = (ancho - ancho_n) / 2.0
                elif pos_num_clean in ("izquierda", "left"):
                    x_n = x_min
                else:
                    x_n = x_max - ancho_n
                p.insert_text(
                    pymupdf.Point(x_n, y_texto_footer),
                    texto_num,
                    fontsize=8.5,
                    color=rgb_texto,
                )

    # 5. Generación de Marcadores Nativos (TOC / Outlines) de Alta Precisión y Mapeo de Páginas
    toc_list = []
    mapa_paginas: dict[str, int] = {}
    if encabezados_meta:
        pagina_cursor = 1
        for nivel, tit_txt in encabezados_meta:
            limpio = tit_txt.strip()
            if not limpio:
                continue
            palabras = limpio.split()
            sub_busq = " ".join(palabras[:2]) if len(palabras) >= 2 else palabras[0]
            pagina_encontrada = pagina_cursor
            for idx_hoja in range(pagina_cursor - 1, total_hojas):
                hoja = doc[idx_hoja]
                rects = hoja.search_for(sub_busq)
                if rects:
                    pagina_encontrada = idx_hoja + 1
                    pagina_cursor = pagina_encontrada
                    break
            toc_list.append([nivel, limpio, pagina_encontrada])
            mapa_paginas[limpio] = pagina_encontrada

    if toc_list:
        try:
            doc.set_toc(toc_list)
        except Exception:
            pass

    # 6. Estampado de números de página reales en el Índice del Documento (multipage support)
    if indices_items:
        inicio_indice = None
        for idx in range(total_hojas):
            texto_h = doc[idx].get_text()
            if "Índice del Documento" in texto_h or "indice-final-documento" in texto_h:
                inicio_indice = idx
                break

        if inicio_indice is not None:
            margen_h = 56.7
            for idx_hoja in range(inicio_indice, total_hojas):
                hoja = doc[idx_hoja]
                x_max = hoja.rect.width - margen_h
                for tit_item, slug in indices_items:
                    pag_dest = mapa_paginas.get(tit_item.strip(), 1)
                    txt_num = str(pag_dest)
                    palabras_item = tit_item.strip().split()
                    sub_item = " ".join(palabras_item[:2]) if len(palabras_item) >= 2 else palabras_item[0]
                    rects = hoja.search_for(sub_item)
                    if rects:
                        r = rects[0]
                        ancho_num = pymupdf.get_text_length(txt_num, fontsize=8.5)
                        x_pos = x_max - ancho_num
                        y_pos = r.y1 - 1.5
                        hoja.insert_text(
                            pymupdf.Point(x_pos, y_pos),
                            txt_num,
                            fontsize=8.5,
                            color=rgb_secundario,
                        )

    ruta_temp = ruta_pdf.with_name(f"{ruta_pdf.stem}_post.pdf")
    doc.save(str(ruta_temp), deflate=True)
    doc.close()
    if ruta_pdf.is_file():
        ruta_pdf.unlink()
    shutil.move(str(ruta_temp), str(ruta_pdf))


def a_pdf(
    texto: str,
    destino: Path,
    titulo: str = "Documento",
    tema_pdf: str = "pizarra_carbon",
    fuente: str = "Calibri",
    tamanio_pt: float = 11.0,
    interlineado: float = 1.15,
    justificado: bool = True,
    estilo_maquetacion: str = "informe",
    pie_pagina: str = "",
    alineacion_pie: str = "derecha",
    numerar_paginas: bool = True,
    formato_num: str = "pagina_x_de_y",
    alineacion_num: str = "derecha",
    running_header: bool = True,
    running_header_texto: str = "",
    normas_apa: bool = False,
    numerar_ecuaciones: bool = False,
    salto_capitulo: bool = True,
    modo_diseno: str = "estandar",
    firma_nombre: str = "",
    firma_cargo: str = "",
    indice_al_final: bool = True,
    plantilla_word: str | Path | None = None,
    zona_cm: dict[str, float] | None = None,
    portada_premium: dict | None = None,
) -> tuple[Path, int, list[str]]:
    """Transforma texto Markdown saneado en un PDF Editorial Profesional de Alta Gama.

    Restricción arquitectónica: 100% independiente de Word (HTML5 + MathML + Chromium + PyMuPDF).
    """
    destino.parent.mkdir(parents=True, exist_ok=True)

    # Saneamiento de frontmatter YAML inicial (evita imprimir metadatos crudos al tope del documento)
    m_fm = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", texto, re.DOTALL)
    if m_fm:
        fm_content = m_fm.group(1)
        if titulo in ("Documento", ""):
            m_tit = re.search(r'title:\s*["\']?([^"\']+)["\']?', fm_content, re.IGNORECASE)
            if m_tit:
                titulo = m_tit.group(1).strip()
        texto = texto[m_fm.end():]

    # Extraer membrete si se especificó una plantilla Word
    elementos_membrete = None
    zona_res = zona_cm
    if plantilla_word:
        from motor.membrete import extraer_membrete_pdf
        datos_m = extraer_membrete_pdf(plantilla_word)
        elementos_membrete = datos_m.get("elementos", [])
        if not zona_res:
            zona_res = datos_m.get("zona_sugerida_cm")
    carpeta_diagramas = destino.parent / "mermaid"
    texto_conversion, _, avisos_mermaid = reemplazar_mermaid_por_imagenes(
        texto, carpeta_diagramas
    )
    # Resolución robusta de imágenes a Data URI Base64 (docs/mejoras/mejoras_app_01.md)
    texto_conversion = incrustar_imagenes_base64_en_markdown(texto_conversion, destino.parent)

    # Transformación de bloques premium (:::kpi) a HTML crudo (pasa a través de pandoc)
    texto_conversion = _transformar_kpi_premium(texto_conversion)

    exe_chromium = ruta_chromium()
    if exe_chromium is None:
        raise ErrorMotorPDF(
            "No se encontró un motor Chromium (Microsoft Edge o Google Chrome) "
            "necesario para el renderizado vectorial de PDF."
        )

    exe_pandoc = ruta_pandoc()
    if exe_pandoc is None:
        raise ErrorMotorPDF(
            "pandoc es requerido para generar la estructura semántica MathML del PDF."
        )

    # 1. Selección de paleta sobria o personalizada
    paleta_clave = (tema_pdf or "pizarra_carbon").strip()
    if "|" in paleta_clave or paleta_clave.startswith("#"):
        partes = [p.strip() for p in paleta_clave.split("|")]
        c_prim = partes[0] if len(partes) > 0 and partes[0] else "#1E293B"
        c_sec = partes[1] if len(partes) > 1 and partes[1] else "#475569"
        c_fondo = partes[2] if len(partes) > 2 and partes[2] else "#F8FAFC"
        paleta = {
            "nombre": f"Personalizada ({c_prim})",
            "primario": c_prim,
            "secundario": c_sec,
            "fondo_suave": c_fondo,
            "texto": "#0F172A",
            "borde_tabla": "#CBD5E1",
        }
    else:
        paleta = PALETAS_EDITORIAL_PDF.get(paleta_clave.lower(), PALETAS_EDITORIAL_PDF["pizarra_carbon"])

    # 2. Generar fragmento HTML semántico con MathML nativo
    # Portada premium (primera pagina) si se solicita
    tiene_portada_premium = bool(portada_premium and portada_premium.get("incluir"))
    if tiene_portada_premium:
        pp = portada_premium or {}
        datos_pp = pp.get("datos", pp)
        imagenes_pp = pp.get("imagenes", [])
        tema_pp = pp.get("tema", datos_pp.get("tema", "clasica_blanca"))
        portada_html = _generar_html_portada_premium(tema_pp, datos_pp, imagenes_pp, paleta)
        texto_conversion = portada_html + "\n\n" + texto_conversion

    html_temp = destino.parent / f"{destino.stem}_temp.html"
    pdf_temp = destino.parent / f"{destino.stem}_crudo.pdf"

    cmd_pandoc = [
        exe_pandoc,
        "--from", "markdown+tex_math_dollars+tex_math_single_backslash+tex_math_double_backslash+raw_tex+link_attributes",
        "--to", "html",
        "--mathml",
    ]
    proc_p = subprocess.run(
        cmd_pandoc,
        input=texto_conversion.encode("utf-8"),
        capture_output=True,
        timeout=60,
    )
    if proc_p.returncode != 0:
        detalle = proc_p.stderr.decode("utf-8", errors="replace")[:250]
        raise ErrorMotorPDF(f"Error procesando estructura del documento: {detalle}")

    cuerpo_html = proc_p.stdout.decode("utf-8", errors="replace")

    # Post-proceso de bloques premium: columnas selectivas (dividir en <hr>)
    cuerpo_html = _postprocesar_columnas_premium(cuerpo_html)

    # Añadir clase modo-premium al cuerpo si aplica
    if (modo_diseno or "estandar").lower() in ("premium", "premium_ejecutivo", "ejecutivo"):
        cuerpo_html = cuerpo_html.replace('<div class="cuerpo-editorial"', '<div class="cuerpo-editorial modo-premium"', 1)

    # Supresión estricta de componentes de interfaz de usuario (botones, sidebars, selectores de tema)
    cuerpo_html = re.sub(r'<button\b[^>]*>[\s\S]*?</button>', '', cuerpo_html, flags=re.IGNORECASE)
    cuerpo_html = re.sub(r'<header[^>]*class=["\'][^"\']*hdxf-header[^"\']*["\'][^>]*>[\s\S]*?</header>', '', cuerpo_html, flags=re.IGNORECASE)
    cuerpo_html = re.sub(r'<aside[^>]*class=["\'][^"\']*hdxf-sidebar[^"\']*["\'][^>]*>[\s\S]*?</aside>', '', cuerpo_html, flags=re.IGNORECASE)
    cuerpo_html = re.sub(r'<aside\b[^>]*>[\s\S]*?</aside>', '', cuerpo_html, flags=re.IGNORECASE)
    cuerpo_html = re.sub(r'<div[^>]*class=["\'][^"\']*(?:action-icon|hdxf-header-actions|theme-toggle)[^"\']*["\'][^>]*>[\s\S]*?</div>', '', cuerpo_html, flags=re.IGNORECASE)

    # Extraer encabezados de la estructura para el árbol de navegación y para el índice final
    encabezados_meta: list[tuple[int, str, str]] = []  # (nivel, texto, id)
    cuerpo_con_ids = []
    cursor_id = 0

    def _asegurar_id(match: re.Match) -> str:
        nonlocal cursor_id
        nivel = int(match.group(1))
        tag = f"h{nivel}"
        attrs = match.group(2) or ""
        contenido = match.group(3)
        texto_limpio = re.sub(r"<[^>]+>", "", contenido).strip()

        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
        if id_match:
            slug = id_match.group(1)
        else:
            cursor_id += 1
            slug = f"sec_{cursor_id}_{re.sub(r'[^a-zA-Z0-9_]+', '_', texto_limpio)[:30]}"
            attrs = f'{attrs} id="{slug}"'

        if texto_limpio:
            encabezados_meta.append((nivel, texto_limpio, slug))
        return f"<{tag}{attrs}>{contenido}</{tag}>"

    cuerpo_html = re.sub(r"<h([1-6])([^>]*)>(.*?)</h\1>", _asegurar_id, cuerpo_html, flags=re.I | re.S)

    # Inserción de Bloque de Firma Institucional al final del documento
    # Valores exactos institucionales requeridos (docs/mejoras/mejoras_app_02_paleta de colores.md)
    f_nom = firma_nombre.strip() if firma_nombre.strip() else "Ing. Patricio Sarmiento Reinoso, Mgst."
    f_car = firma_cargo.strip() if firma_cargo.strip() else "CONSULTOR"
    bloque_firma_html = f"""
    <div class="bloque-firma" style="margin-top: 60px; margin-bottom: 40px; text-align: center; break-inside: avoid; page-break-inside: avoid;">
        <div style="height: 65px;"></div>
        <div style="display: inline-block; min-width: 280px; max-width: 380px; border-top: 1.5pt solid {paleta['secundario']}; padding-top: 8px;">
            <div style="font-weight: 700; font-size: 11pt; color: {paleta['primario']};">{f_nom}</div>
            <div style="font-size: 9.5pt; color: #475569; margin-top: 4px;">{f_car}</div>
        </div>
    </div>
    """

    # Inserción de Índice al final luego de la firma con enlaces a los títulos
    bloque_indice_final = ""
    indices_items_meta: list[tuple[str, str]] = []
    if indice_al_final and encabezados_meta:
        items_indice = []
        for nivel, tit_txt, slug in encabezados_meta:
            if nivel > 3:
                continue
            indices_items_meta.append((tit_txt, slug))
            pad_left = (nivel - 1) * 18
            font_w = "700" if nivel == 1 else "400"
            color_link = paleta["primario"] if nivel == 1 else "#334155"
            items_indice.append(
                f'<li style="margin-bottom: 6px; padding-left: {pad_left}px; display: flex; justify-content: space-between; border-bottom: 1px dotted {paleta["borde_tabla"]}; padding-bottom: 2px;">'
                f'<a href="#{slug}" style="text-decoration: none; color: {color_link}; font-weight: {font_w}; font-size: {max(8.5, tamanio_pt - (nivel - 1))}pt;">{tit_txt}</a>'
                f'<span style="font-size: 8.5pt; color: {paleta["secundario"]}; font-weight: 600; min-width: 25px; text-align: right;"></span>'
                f'</li>'
            )
        lista_html = "\n".join(items_indice)
        bloque_indice_final = f"""
        <div class="indice-final-documento" style="page-break-before: always !important; break-before: page !important; column-span: all !important; width: 100% !important; display: block !important; clear: both !important; margin-top: 35px; padding-top: 25px;">
            <h2 style="text-align: center; margin-bottom: 25px; color: {paleta['primario']}; border-bottom: 2pt solid {paleta['secundario']}; padding-bottom: 8px;">Índice del Documento</h2>
            <ul style="list-style-type: none; padding-left: 0; margin: 0 auto; max-width: 90%;">
                {lista_html}
            </ul>
        </div>
        """

    cuerpo_html = f"{cuerpo_html}\n{bloque_firma_html}\n{bloque_indice_final}"

    # Envolver párrafos con imágenes en un contenedor figure de ancho completo para evitar colapsos en 2 columnas
    cuerpo_html = re.sub(
        r'<p(?:\s+[^>]*)?>\s*(<img\b[^>]*>)\s*</p>',
        r'<figure class="mermaid-contenedor full-width" style="column-span: all !important; width: 100% !important; display: block !important; margin: 1.5rem auto !important; text-align: center !important; break-inside: avoid !important; page-break-inside: avoid !important; clear: both !important;">\1</figure>',
        cuerpo_html,
        flags=re.IGNORECASE,
    )

    # Inyección de salto de capítulo con la regla canónica única (H1-only + excepción de 1.ª hoja)
    if salto_capitulo:
        cuerpo_html = inyectar_saltos_capitulo_html(cuerpo_html)

    # 3. Ensamblar documento HTML5 Paged Media completo
    documento_html = _generar_html_impresion(
        cuerpo_html=cuerpo_html,
        titulo=titulo,
        paleta=paleta,
        fuente=fuente,
        tamanio_pt=tamanio_pt,
        interlineado=interlineado,
        justificado=justificado,
        estilo_maquetacion=estilo_maquetacion,
        normas_apa=normas_apa,
        numerar_ecuaciones=numerar_ecuaciones,
        salto_capitulo=salto_capitulo,
        modo_diseno=modo_diseno,
        elementos_membrete=elementos_membrete,
        zona_cm=zona_res,
    )
    html_temp.write_text(documento_html, encoding="utf-8")

    # 4. Compilación vectorial Headless con Chromium
    cmd_chromium = [
        exe_chromium,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={str(pdf_temp.resolve())}",
        str(html_temp.resolve()),
    ]
    proc_c = subprocess.run(
        cmd_chromium,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc_c.returncode != 0 or not pdf_temp.is_file():
        raise ErrorMotorPDF("Chromium no pudo completar la impresión del documento a PDF.")

    # 5. Mover a destino final y post-procesar con PyMuPDF
    if destino.is_file():
        destino.unlink()
    shutil.move(str(pdf_temp), str(destino))

    # Limpiar archivo HTML efímero
    if html_temp.is_file():
        html_temp.unlink()

    # Extraer encabezados de la estructura para el árbol de navegación TOC
    encabezados_toc = [(n, t) for n, t, _ in encabezados_meta]

    omitir_portada = (estilo_maquetacion == "portada") or tiene_portada_premium
    _postprocesar_con_pymupdf(
        ruta_pdf=destino,
        titulo=titulo,
        paleta=paleta,
        pie_pagina=pie_pagina,
        alineacion_pie=alineacion_pie,
        numerar_paginas=numerar_paginas,
        formato_num=formato_num,
        alineacion_num=alineacion_num,
        running_header=running_header,
        running_header_texto=running_header_texto,
        omitir_portada=omitir_portada,
        encabezados_meta=encabezados_toc,
        indices_items=indices_items_meta,
        tiene_membrete=bool(elementos_membrete),
        zona_cm=zona_res,
        elementos_membrete=elementos_membrete,
    )

    avisos = (
        avisos_mermaid
        + [
            f"PDF Editorial generado con motor independiente ({Path(exe_chromium).stem}).",
            f"Paleta editorial aplicada: {paleta['nombre']}.",
            f"Tipografía: {fuente} {tamanio_pt:g} pt · interlineado {interlineado:.2f}.",
        ]
    )
    if pie_pagina.strip() or numerar_paginas:
        avisos.append("Pie de página y numeración vectorial estampados con lógica anti-colisión.")

    return destino, contar_formulas(texto), avisos
