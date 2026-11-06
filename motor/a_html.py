"""Motor de transformación a HTML imprimible (markdown-it + KaTeX + Temas locales).

Pipeline:
  1. Blindaje: las fórmulas `\\( \\)` / `\\[ \\]` del texto saneado se
     sustituyen por tokens (el markdown parser no las toca).
  2. Render: markdown-it (preset commonmark + tablas GFM).
  3. Enchufe: cada token vuelve como `<span class="mformula" data-latex>`.
  4. Favicon de alto contraste (fondo negro sólido e isotipo blanco) embebido
     como Data-URI vectorial para perfecta visibilidad en todos los navegadores.
  5. Centrado estricto estructural (`max-width: 900px; margin: 0 auto !important`).
  6. Renderizado garantizado de fórmulas en el 100% de los temas (Temas 1..6 y base).
  7. Sistema de paletas Tri-Color (Primario, Secundario, Fondo Suave).
  8. Pie de página (footer) dinámico configurable (izq / der) con año actual.
"""

from __future__ import annotations

import base64
import datetime
import functools
import html as _html
import re
import shutil
from pathlib import Path

from markdown_it import MarkdownIt

from motor.formulas import reparar_sintaxis_latex_interna
from motor.sanear import _TROZO_CODIGO

_KATEX_CDN_CSS = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"
_KATEX_CDN_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"
_MERMAID_CDN_JS = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"
_CARPA_KATEX = Path(__file__).resolve().parent / "assets" / "katex"
_DIR_TEMAS_HTML = Path(__file__).resolve().parent.parent / "templates" / "temas_html"


def listar_temas_html_disco() -> list[str]:
    """Devuelve la lista ordenada de identificadores de temas HTML existentes en `templates/temas_html/`."""
    if not _DIR_TEMAS_HTML.is_dir():
        return []
    return sorted(p.stem for p in _DIR_TEMAS_HTML.glob("*.html") if p.is_file())


_INLINE = re.compile(
    r"\\\((.+?)\\\)|(?<!\\)\$(?!\s)(.+?)(?<!\s)(?<!\\)\$",
    re.S,
)
_DISPLAY = re.compile(
    r"\\\[([\s\S]+?)\\\]|"
    r"\$\$([\s\S]+?)\$\$|"
    r"(\\begin\{(?:equation|align|aligned|gather|cases|matrix|pmatrix|bmatrix)\*?\}[\s\S]+?\\end\{(?:equation|align|aligned|gather|cases|matrix|pmatrix|bmatrix)\*?\})",
    re.S,
)
_PARASITO_INI = re.compile(r"^(?:\\\(|\\\[|\$\$|\$)+")
_PARASITO_FIN = re.compile(r"(?:\\\)|\\\]|\$\$|\$)+$")
_MERMAID_CERCO = re.compile(
    r"`{3,}\s*mermaid[^\n]*\n([\s\S]*?)(?:`{3,}|$)",
    re.IGNORECASE,
)


# Favicon azul corporativo oficial (#3b82f6/#2563eb/#8b5cf6/#1e3a8a con isotipo blanco) embebido como Data-URI
_FAVICON_DATA_URI = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NCA2NCI+CiAgPGRlZnM+"
    "CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Im1mX2F6dWwiIHgxPSIwIiB5MT0iMCIgeDI9IjEiIHkyPSIxIj4KICAgICAgPHN0b3Agb2Zmc2V0"
    "PSIwJSIgc3RvcC1jb2xvcj0iIzNiODJmNiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjUwJSIgc3RvcC1jb2xvcj0iIzI1NjNlYiIvPgogICAg"
    "ICA8c3RvcCBvZmZzZXQ9Ijg1JSIgc3RvcC1jb2xvcj0iIzhiNWNmNiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9"
    "IiMxZTNhOGEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHg9IjIiIHk9IjIiIHdpZHRoPSI2MCIgaGVpZ2h0"
    "PSI2MCIgcng9IjE2IiBmaWxsPSJ1cmwoI21mX2F6dWwpIi8+CiAgPHJlY3QgeD0iMiIgeT0iMiIgd2lkdGg9IjYwIiBoZWlnaHQ9IjYwIiBy"
    "eD0iMTYiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjMpIiBzdHJva2Utd2lkdGg9IjEuNSIvPgogIDxwYXRoIGQ9"
    "Ik0xNSA0NSBWMjMuNSBsOS41IDEyIDkuNS0xMiBWNDUiCiAgICAgICAgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmZmZmIiBzdHJva2Utd2lk"
    "dGg9IjUuNSIKICAgICAgICBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KICA8cGF0aCBkPSJNMzcu"
    "NSA0NSBjMy41LTQgNy41IDMgMTEtMSIKICAgICAgICBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iNCIKICAg"
    "ICAgICBzdHJva2UtbGluZWNhcD0icm91bmQiIG9wYWNpdHk9IjAuOTUiLz4KPC9zdmc+Cg=="
)

# Catálogo de Paletas Tri-Color (Primario/Títulos, Secundario/Acentos y Bordes, Fondo Suave/Tablas)
PALETAS_TRICOLOR: dict[str, dict[str, str]] = {
    "tema_default": {
        "nombre": "Por Defecto del Tema",
        "primario": "#0284c7",
        "secundario": "#0d9488",
        "fondo_suave": "#f1f5f9",
        "texto": "#0f172a",
    },
    "oceano_ejecutivo": {
        "nombre": "Océano Ejecutivo",
        "primario": "#1E3A8A",
        "secundario": "#3B82F6",
        "fondo_suave": "#EFF6FF",
        "texto": "#0f172a",
    },
    "bosque_academico": {
        "nombre": "Bosque Académico",
        "primario": "#14532D",
        "secundario": "#22C55E",
        "fondo_suave": "#F0FDF4",
        "texto": "#0f172a",
    },
    "pizarra_minimalista": {
        "nombre": "Pizarra Minimalista",
        "primario": "#1E293B",
        "secundario": "#64748B",
        "fondo_suave": "#F8FAFC",
        "texto": "#0f172a",
    },
    "terracota_editorial": {
        "nombre": "Terracota Editorial",
        "primario": "#7C2D12",
        "secundario": "#EA580C",
        "fondo_suave": "#FFF7ED",
        "texto": "#0f172a",
    },
    "vino_corporativo": {
        "nombre": "Vino Tinto Corporativo",
        "primario": "#581C87",
        "secundario": "#9333EA",
        "fondo_suave": "#FAF5FF",
        "texto": "#0f172a",
    },
    "ambar_dorado": {
        "nombre": "Ámbar Dorado",
        "primario": "#78350F",
        "secundario": "#D97706",
        "fondo_suave": "#FFFBEB",
        "texto": "#0f172a",
    },
}

PALETAS_HTML = PALETAS_TRICOLOR

_JS_INICIAR_RENDER = r"""<script>
async function _iniciarRenderMarkflow() {
  if (window._renderMarkflowEnCurso) {
    return window._renderMarkflowEnCurso;
  }
  window._renderMarkflowEnCurso = (async function () {
    try {
      var nodos = document.querySelectorAll(".mformula");
      if (typeof katex !== "undefined") {
        nodos.forEach(function (el) {
          if (el.getAttribute("data-renderizado") === "true") return;
          var tex = el.getAttribute("data-latex");
          if (!tex) return;
          try {
            katex.render(tex, el, {
              displayMode: el.classList.contains("display"),
              throwOnError: false
            });
            el.setAttribute("data-renderizado", "true");
          } catch (errK) {
            el.textContent = tex;
          }
        });
      } else {
        nodos.forEach(function (el) {
          if (el.getAttribute("data-renderizado") !== "true") {
            el.textContent = el.getAttribute("data-latex");
          }
        });
      }
      if (typeof mermaid !== "undefined" && document.querySelector(".mermaid")) {
        try {
          mermaid.initialize({
            startOnLoad: false,
            theme: "default",
            securityLevel: "loose",
            fontSize: 16,
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            flowchart: { useMaxWidth: false, htmlLabels: true, nodeSpacing: 45, rankSpacing: 45 },
            sequence: { useMaxWidth: false },
            themeVariables: {
              fontSize: "16px",
              fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
            }
          });
          function _sanearMermaid(codigo) {
            if (!codigo || typeof codigo !== "string") return "";
            var c = codigo;
            var superindices = {
              "\u00b2": "2", "\u00b3": "3", "\u2070": "0", "\u00b9": "1",
              "\u2074": "4", "\u2075": "5", "\u2076": "6", "\u2077": "7",
              "\u2078": "8", "\u2079": "9"
            };
            Object.keys(superindices).forEach(function (k) {
              c = c.split(k).join(superindices[k]);
            });
            c = c.replace(/(\]|\)|\}|>|\w)\s+:::/g, "$1:::").replace(/\s+:::/g, ":::");
            c = c.replace(/<=/g, "\u2264").replace(/>=/g, "\u2265");
            var DIRECTIVAS = /^\s*(classDef|style|click|linkStyle|subgraph|end)\b/i;
            function sanitizarInteriorNodo(texto) {
              var t = texto
                .replace(/\u2192/g, "->")
                .replace(/\u2190/g, "<-")
                .replace(/\u2194/g, "<->");
              t = t.replace(/\[([^\[\]]*?)\]/g, "($1)");
              t = t.replace(/<(?![=-])/g, "&lt;").replace(/(?<![=-])>/g, "&gt;");
              t = t.replace(/"/g, "'");
              return t;
            }
            function procesarLinea(linea) {
              var resultado = [];
              var i = 0;
              var n = linea.length;
              while (i < n) {
                var ch = linea[i];
                if (ch !== "[") { resultado.push(ch); i++; continue; }
                var j = i + 1;
                if (j < n && linea[j] === '"') {
                  var k = linea.indexOf('"]', j + 1);
                  if (k !== -1) {
                    resultado.push(linea.slice(i, k + 2));
                    i = k + 2;
                    continue;
                  }
                  resultado.push(ch); i++; continue;
                }
                var nivel = 1;
                var k2 = j;
                while (k2 < n && nivel > 0) {
                  if (linea[k2] === "[") nivel++;
                  else if (linea[k2] === "]") nivel--;
                  k2++;
                }
                if (nivel === 0) {
                  var interior = linea.slice(j, k2 - 1);
                  var interiorSano = sanitizarInteriorNodo(interior);
                  resultado.push('["' + interiorSano + '"]');
                  i = k2;
                  continue;
                }
                resultado.push(ch); i++;
              }
              return resultado.join("");
            }
            return c.split("\n").map(function (linea) {
              return DIRECTIVAS.test(linea) ? linea : procesarLinea(linea);
            }).join("\n");
          }
          var diags = document.querySelectorAll(".mermaid");
          for (var idx = 0; idx < diags.length; idx++) {
            var el = diags[idx];
            var estadoProc = el.getAttribute("data-processed");
            if (estadoProc === "true" || estadoProc === "processing") continue;
            var codigoRaw = el.getAttribute("data-mermaid-raw") || (el.querySelector("svg") ? "" : (el.textContent || "").trim());
            if (!codigoRaw) continue;
            el.setAttribute("data-mermaid-raw", codigoRaw);
            el.setAttribute("data-processed", "processing");
            var codigo = _sanearMermaid(codigoRaw);
            var id = "mermaid-diag-" + idx + "-" + Math.random().toString(36).substring(2, 7);
            try {
              var res = await mermaid.render(id, codigo);
              el.innerHTML = res.svg;
              el.setAttribute("data-processed", "true");
              var svgEl = el.querySelector("svg");
              if (svgEl) {
                svgEl.style.width = "100%";
                svgEl.style.maxWidth = "100%";
                svgEl.style.minWidth = "60%";
                svgEl.style.height = "auto";
                svgEl.style.display = "block";
                svgEl.style.margin = "0 auto";
              }
            } catch (err) {
              document.querySelectorAll('[id^="dmermaid-"]').forEach(function(d){ d.remove(); });
              document.querySelectorAll('[id^="d' + id + '"]').forEach(function(d){ d.remove(); });
              el.innerHTML = '<div class="alerta-error-mermaid" style="padding:12px 16px; border:1px solid #ef4444; background:#fef2f2; color:#b91c1c; border-radius:6px; font-family:sans-serif; font-size:0.88rem; text-align:left; margin:1rem auto; max-width:90%;"><strong style="display:block; margin-bottom:4px;">⚠️ Error en la sintaxis del diagrama Mermaid:</strong><span style="font-size:0.82rem; white-space:pre-wrap;">' + (err.message || String(err)) + '</span></div>';
              el.setAttribute("data-processed", "true");
            }
          }
          document.querySelectorAll('[id^="dmermaid-"]').forEach(function(d){ d.remove(); });
        } catch (e) {
          console.warn("Fallo al inicializar Mermaid:", e);
        }
      }
    } finally {
      window._renderMarkflowEnCurso = null;
    }
  })();
  return window._renderMarkflowEnCurso;
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", _iniciarRenderMarkflow);
} else {
  _iniciarRenderMarkflow();
}
window._iniciarRenderMarkflow = _iniciarRenderMarkflow;
</script>"""

_PLANTILLA_BASE = """<!doctype html>
<html lang="es" data-theme="claro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITULO__</title>
<link rel="icon" type="image/svg+xml" href="__FAVICON__">
__KATEX_CSS_TAG__
<style>
  :root {
    color-scheme: light dark;
    --fuente-doc: __FUENTE__;
    --tamanio-doc: __TAMANIO__pt;
    --interlineado-doc: __INTERLINEADO__;
    --ancho-maximo: __ANCHO_MAXIMO__;
    --color-primario: __PALETA_PRIMARIO__;
    --color-secundario: __PALETA_SECUNDARIO__;
    --th-bg: __PALETA_FONDO_SUAVE__;
    --tr-alt: #f8fafc;
    --border-tbl: rgba(0, 0, 0, 0.12);
  }
  body {
    font-family: var(--fuente-doc);
    font-size: var(--tamanio-doc);
    line-height: var(--interlineado-doc);
    max-width: var(--ancho-maximo);
    margin: 2.5rem auto;
    padding: 0 1.5rem;
    color: #1f2937;
    background: #ffffff;
    counter-reset: num_eq;
  }
  __JUSTIFICADO_CSS__
  h1 { font-size: 1.75rem; margin: 0 0 .5rem; color: var(--color-primario); font-weight: 700; }
  h2 { font-size: 1.35rem; margin-top: 2rem; color: var(--color-primario); border-bottom: 2px solid var(--color-secundario); padding-bottom: .3rem; font-weight: 700; }
  h3 { font-size: 1.15rem; color: var(--color-primario); margin-top: 1.5rem; font-weight: 600; }
  h2, h3 { break-after: avoid; }
  p { margin: 0.8rem 0; }
  pre { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: .8rem 1rem; overflow-x: auto; font-size: .9rem; }
  code { font-family: Consolas, "Cascadia Code", monospace; background: #f1f5f9; border-radius: 4px; padding: .1rem .3rem; }
  pre code { background: transparent; padding: 0; }
  blockquote, .note, .callout {
    border-left: 4px solid var(--color-primario);
    margin: 1.25rem 0;
    padding: .85rem 1.25rem;
    color: #374151;
    background: var(--card-alt, rgba(59, 130, 246, 0.05));
    border-radius: 0 8px 8px 0;
    text-align: justify !important;
  }
  blockquote strong, .note strong, .callout strong { color: var(--color-primario); }
  /* Tablas HTML estrictas: display table, 100% width, border-collapse, sin scrollbars */
  table {
    border-collapse: collapse !important;
    margin: 1.5rem auto !important;
    width: 100% !important;
    max-width: 100% !important;
    overflow: visible !important;
    display: table !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    border-radius: 6px;
    font-size: 0.90rem;
  }
  th, td { border: 1px solid var(--border-tbl); padding: .65rem .95rem; text-align: left; vertical-align: top; }
  thead, th { background: var(--th-bg); font-weight: 700; color: #0f172a !important; }
  tbody tr:nth-child(even) { background: var(--tr-alt); }
  tbody tr:hover { background: #f1f5f9; }

  /* Soporte integral de modo oscuro con contraste calibrado */
  [data-theme="dark"] body { background: #0b0f19; color: #e2e8f0; }
  [data-theme="dark"] h1, [data-theme="dark"] h2, [data-theme="dark"] h3 { color: #f1f5f9 !important; }
  [data-theme="dark"] pre { background: #161e2e; border-color: #334155; }
  [data-theme="dark"] code { background: #1e293b; color: #f8fafc; }
  [data-theme="dark"] blockquote, [data-theme="dark"] .note, [data-theme="dark"] .callout { background: #161e2e !important; color: #cbd5e1 !important; border-left-color: var(--color-secundario) !important; }
  [data-theme="dark"] table { box-shadow: 0 1px 3px rgba(0,0,0,0.5); }
  [data-theme="dark"] thead, [data-theme="dark"] th { background: #1e293b !important; color: #f8fafc !important; }
  [data-theme="dark"] td { border-color: #334155; color: #e2e8f0; }
  [data-theme="dark"] tbody tr:nth-child(even) { background: #161e2e !important; }
  [data-theme="dark"] tbody tr:hover { background: #1e293b !important; }

  img { max-width: 100%; height: auto; border-radius: 6px; }
  .mformula { white-space: nowrap; }
  .mformula.display {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    margin: 1.5rem 0 !important;
    position: relative !important;
    width: 100% !important;
  }
  __NUMERAR_EQ_CSS__
  /* Fase 2: Control estricto de dimensiones y erradicación total de scroll interno y errores */
  [id^="dmermaid-"] {
    position: fixed !important;
    left: -99999px !important;
    top: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -1 !important;
  }
  g.error-icon, svg[aria-roledescription="error"], [aria-roledescription="error"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
  }
  .mermaid, .diagram-container, pre.mermaid, div.mermaid, .mermaid-contenedor {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    margin: 1.8rem auto !important;
    width: 100% !important;
    max-width: 100% !important;
    padding: 0.5rem 0 !important;
    overflow: visible !important;
    overflow-x: visible !important;
    overflow-y: visible !important;
    background: transparent !important;
    border: none !important;
  }
  .mermaid::before, pre.mermaid::before, div.mermaid::before, .mermaid-contenedor::before,
  pre:has(.mermaid)::before, pre:has(svg)::before, div.mermaid *::before {
    display: none !important;
    content: none !important;
  }
  .mermaid svg {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 60% !important;
    height: auto !important;
    max-height: none !important;
    display: block !important;
    margin: 0 auto !important;
  }
  .mermaid svg text, .mermaid svg .label, .mermaid svg .nodeLabel, .mermaid svg .edgeLabel {
    font-size: 15px !important;
  }

  /* Figuras en línea y figuras flotantes con envoltura de texto fluida (Fase 2) */
  figure, .figura-contenedor {
    margin: 1.5rem auto !important;
    text-align: center;
    max-width: 100%;
    overflow: visible !important;
  }
  figure img, .figura-contenedor img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
  }
  figure figcaption, .epigrafe-figura {
    margin-top: 0.5rem;
    font-size: 0.88rem;
    color: #64748b;
    font-style: italic;
  }
  .figura-flotante-izq, figure.flotante-izq, img.flotante-izq {
    float: left !important;
    max-width: 48% !important;
    margin: 0.5rem 1cm 0.75rem 0 !important;
    clear: left !important;
  }
  .figura-flotante-der, figure.flotante-der, img.flotante-der {
    float: right !important;
    max-width: 48% !important;
    margin: 0.5rem 0 0.75rem 1cm !important;
    clear: right !important;
  }
  /* Pie de página institucional configurable */
  .pie-doc {
    margin-top: 3.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
    color: #64748b;
    font-size: 0.88rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  /* Bloques colapsables de figuras e imágenes Base64 */
  details {
    margin: 1.5rem 0;
    padding: 0.75rem 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #f8fafc;
    transition: background-color 0.2s ease;
  }
  [data-theme="dark"] details {
    border-color: #334155;
    background: #1e293b;
  }
  details summary {
    cursor: pointer;
    font-weight: 600;
    color: #1e293b;
    outline: none;
    user-select: none;
  }
  [data-theme="dark"] details summary {
    color: #f1f5f9;
  }
  details summary:hover {
    color: #3b82f6;
  }
  details[open] {
    padding-bottom: 1.25rem;
  }
  @media print {
    body { margin: 1cm 1.4cm; max-width: none; }
    pre, table, blockquote, .mformula.display, details { break-inside: avoid; }
    details { border: none !important; background: transparent !important; padding: 0 !important; }
    details summary { cursor: default !important; }
    a { color: inherit; text-decoration: none; }
    .no-print { display: none !important; }
  }
</style>
</head>
<body>
<main class="contenedor contenido-principal">
__CONTENIDO__
</main>
<div class="pie-doc">
  <span>__FOOTER_IZQ__</span>
  <span>__FOOTER_DER__</span>
</div>
__KATEX_JS_TAG__
__EXTRA__
__JS_INICIAR_RENDER__
</body>
</html>
"""


def _desparasitar(cuerpo: str) -> str:
    limpio = cuerpo.strip()
    if _PARASITO_INI.search(limpio):
        limpio = _PARASITO_INI.sub("", limpio)
    if _PARASITO_FIN.search(limpio):
        limpio = _PARASITO_FIN.sub("", limpio)
    return limpio.strip()


def _blindar(texto: str) -> tuple[str, list[tuple[str, str, bool]], list[tuple[str, str]]]:
    formulas: list[tuple[str, str, bool]] = []
    mermaid: list[tuple[str, str]] = []

    def apuntar(tex: str) -> str:
        token = f"MXTOKEN{len(formulas)}FIN"
        return token

    def sust_display(m: re.Match) -> str:
        cuerpo = m.group(1) or m.group(2) or m.group(3) or ""
        cuerpo = _desparasitar(cuerpo)
        cuerpo = reparar_sintaxis_latex_interna(cuerpo)
        if not cuerpo.strip():
            return m.group(0)
        token = apuntar(cuerpo)
        formulas.append((token, cuerpo, True))
        return token

    def sust_inline(m: re.Match) -> str:
        cuerpo = m.group(1) if m.group(1) is not None else m.group(2)
        if not cuerpo or not cuerpo.strip():
            return m.group(0)
        # Evitar capturar cantidades monetarias como "$100" o "$ 50 USD"
        if re.match(r"^\d+(?:[.,]\d+)?(?:\s*[a-zA-Z]+)?$", cuerpo.strip()):
            return m.group(0)
        cuerpo = _desparasitar(cuerpo)
        cuerpo = reparar_sintaxis_latex_interna(cuerpo)
        token = apuntar(cuerpo)
        formulas.append((token, cuerpo, False))
        return token

    def sust_mermaid(m: re.Match) -> str:
        token = f"MERMTOKEN{len(mermaid)}FIN"
        mermaid.append((token, m.group(1).rstrip()))
        return token

    def por_trozo(m: re.Match) -> str:
        trozo = m.group(0)
        if trozo.startswith("`"):
            palo = _MERMAID_CERCO.search(trozo)
            if palo:
                return sust_mermaid(palo)
            return trozo
        return _DISPLAY.sub(sust_display, trozo)

    tablero = _TROZO_CODIGO.sub(por_trozo, texto)
    tablero = _TROZO_CODIGO.sub(
        lambda m: m.group(0) if m.group(0).startswith("`")
        else _INLINE.sub(sust_inline, m.group(0)),
        tablero,
    )
    return tablero, formulas, mermaid


def _enchufar(render: str, formulas: list[tuple[str, str, bool]], mermaid: list[tuple[str, str]]) -> str:
    for token, tex, es_display in formulas:
        escapeado = _html.escape(tex, quote=True)
        clase = "display" if es_display else "inline"
        if es_display:
            render = render.replace(
                f"<p>{token}</p>",
                f'<div class="mformula display" data-latex="{escapeado}"></div>',
            )
        render = render.replace(
            token,
            f'<span class="mformula {clase}" data-latex="{escapeado}"></span>',
        )
    from motor.a_mermaid import sanear_codigo_mermaid
    for token, codigo in mermaid:
        codigo_saneado = _html.escape(sanear_codigo_mermaid(codigo))
        render = render.replace(
            f"<p>{token}</p>",
            f'<pre class="mermaid">{codigo_saneado}</pre>',
        )
        render = render.replace(
            token,
            f'<pre class="mermaid">{codigo_saneado}</pre>',
        )
    return render


def _referencias_katex() -> tuple[str, str, bool]:
    if (
        (_CARPA_KATEX / "katex.min.css").is_file()
        and (_CARPA_KATEX / "katex.min.js").is_file()
        and (_CARPA_KATEX / "fonts").is_dir()
    ):
        return "katex/katex.min.css", "katex/katex.min.js", True
    return _KATEX_CDN_CSS, _KATEX_CDN_JS, False


def copiar_activos_katex(destino: Path) -> bool:
    _, _, local = _referencias_katex()
    if not local:
        return False
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(_CARPA_KATEX, destino)
    return True


@functools.lru_cache(maxsize=1)
def _tag_katex_css() -> tuple[str, bool]:
    if not (_referencias_katex()[2]):
        return f'<link rel="stylesheet" href="{_KATEX_CDN_CSS}">', False
    css = (_CARPA_KATEX / "katex.min.css").read_text(
        encoding="utf-8", errors="replace"
    )
    # Corregir rutas de fuentes: el CSS se inyecta inline en el HTML servido
    # desde la raíz, por lo que `fonts/...` y `katex/fonts/...` dan 404.
    # Se apunta directamente a `/assets/katex/fonts/...` (montado en motor/assets).
    css = re.sub(
        r"url\(fonts/([^)]+)\)",
        lambda m: f'url(/assets/katex/fonts/{m.group(1)})',
        css,
    )
    return f"<style>\n{css}\n</style>", True


@functools.lru_cache(maxsize=1)
def _tag_katex_js() -> str:
    if not (_referencias_katex()[2]):
        return f'<script src="{_KATEX_CDN_JS}" defer></script>'
    js = (_CARPA_KATEX / "katex.min.js").read_text(
        encoding="utf-8", errors="replace"
    )
    return f"<script>\n{js}\n</script>"


_CARPA_MERMAID = Path(__file__).resolve().parent / "assets" / "mermaid" / "mermaid.min.js"


@functools.lru_cache(maxsize=1)
def _leer_mermaid_local_js() -> str:
    if _CARPA_MERMAID.is_file():
        return _CARPA_MERMAID.read_text(encoding="utf-8", errors="replace")
    return ""


def _extra_mermaid(hay_mermaid: bool) -> str:
    if not hay_mermaid:
        return ""
    js = _leer_mermaid_local_js()
    if js:
        return f'<!-- mermaid.min.js local embebido -->\n<script data-asset="mermaid.min.js">\n{js}\n</script>'
    return f'<script src="{_MERMAID_CDN_JS}" defer></script>'


def convertir_imagen_a_base64(image_path: str, base_dir: Path | str | None = None) -> str:
    """Convierte una imagen de disco a Data URI Base64 autónomo (docs/mejoras/mejoras_app_01.md)."""
    base = Path(base_dir) if base_dir else Path.cwd()
    ruta_limpia = image_path.strip().strip("'\"")
    if not ruta_limpia or ruta_limpia.startswith(("http://", "https://", "data:")):
        return image_path

    candidatos = [
        base / ruta_limpia,
        Path.cwd() / ruta_limpia,
        Path(ruta_limpia),
    ]
    for cand in candidatos:
        try:
            if cand.is_file():
                ext = cand.suffix.lower().replace(".", "")
                if ext == "jpg":
                    ext = "jpeg"
                elif ext == "svg":
                    ext = "svg+xml"
                raw = cand.read_bytes()
                encoded = base64.b64encode(raw).decode("utf-8")
                return f"data:image/{ext};base64,{encoded}"
        except Exception:
            continue
    return image_path


def incrustar_imagenes_base64_en_markdown(texto: str, base_dir: Path | str | None = None) -> str:
    """Reemplaza enlaces a imágenes locales en Markdown y HTML por Data URIs en Base64."""
    def _sub_md_img(m: re.Match) -> str:
        alt = m.group(1)
        resto = m.group(2).strip()
        partes = resto.split(maxsplit=1)
        ruta = partes[0]
        titulo = f" {partes[1]}" if len(partes) > 1 else ""
        b64 = convertir_imagen_a_base64(ruta, base_dir)
        return f"![{alt}]({b64}{titulo})"

    texto_res = re.sub(r"!\[(.*?)\]\((.*?)\)", _sub_md_img, texto)

    def _sub_html_img(m: re.Match) -> str:
        attrs_antes = m.group(1) or ""
        src = m.group(2)
        attrs_despues = m.group(3) or ""
        b64 = convertir_imagen_a_base64(src, base_dir)
        return f'<img{attrs_antes} src="{b64}"{attrs_despues}>'

    texto_res = re.sub(r'<img\b([^>]*?)\bsrc=["\']([^"\']+)["\']([^>]*?)>', _sub_html_img, texto_res, flags=re.I)
    return texto_res


def a_html(
    texto: str,
    titulo: str = "Documento",
    tema_html: str = "defecto",
    fuente: str = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    tamanio_pt: float = 11.0,
    interlineado: float = 1.6,
    justificado: bool = True,
    ancho_maximo: str = "900px",
    paleta_tabla: str = "defecto",
    paleta_tricolor: str = "tema_default",
    numerar_ecuaciones: bool = False,
    footer_izq: str = "",
    footer_der: str = "Ing. Patricio Sarmiento Reinoso, Mgst.",
    base_dir: Path | str | None = None,
) -> tuple[str, int, list[str]]:
    """Transforma texto saneado a HTML imprimible con soporte universal de KaTeX y temas."""
    texto_con_imagenes = incrustar_imagenes_base64_en_markdown(texto, base_dir)
    tablero, formulas, mermaid = _blindar(texto_con_imagenes)
    render = (
        MarkdownIt("commonmark").enable("table").enable("strikethrough")
        .render(tablero)
    )
    render = _enchufar(render, formulas, mermaid)
    def _asignar_ids_titulos(html_bloque: str) -> str:
        conteo = 0
        def _h_sub(m: re.Match) -> str:
            nonlocal conteo
            tag = f"h{m.group(1)}"
            attrs = m.group(2) or ""
            contenido = m.group(3)
            if "id=" not in attrs:
                txt_puro = re.sub(r'<[^>]+>', '', contenido).strip()
                slug = re.sub(r'[^a-zA-Z0-9_\-]+', '-', txt_puro.lower()).strip('-') or f"secc-{conteo}"
                conteo += 1
                return f'<{tag}{attrs} id="{slug}">{contenido}</{tag}>'
            return m.group(0)
        return re.sub(r'<h([1-3])\b([^>]*)>(.*?)</h\1>', _h_sub, html_bloque, flags=re.IGNORECASE | re.DOTALL)

    render = _asignar_ids_titulos(render)
    tag_css, local = _tag_katex_css()
    tag_js = _tag_katex_js()

    # Año dinámico para el pie de página
    anio_actual = datetime.datetime.now().year
    f_izq = footer_izq.strip() if footer_izq.strip() else f"MarkFlow AI {anio_actual}"
    f_der = footer_der.strip() if footer_der.strip() else "Ing. Patricio Sarmiento Reinoso, Mgst."

    # Paleta Tri-Color (predefinida o personalizada #c1|#c2|#c3)
    pal_clave = (paleta_tricolor or "tema_default").strip()
    if pal_clave in PALETAS_TRICOLOR:
        paleta = PALETAS_TRICOLOR[pal_clave]
    elif "|" in pal_clave or pal_clave.startswith("#"):
        partes = [p.strip() for p in pal_clave.split("|")]
        c1 = partes[0] if len(partes) > 0 and partes[0] else "#0284c7"
        c2 = partes[1] if len(partes) > 1 and partes[1] else "#0d9488"
        c3 = partes[2] if len(partes) > 2 and partes[2] else "#f1f5f9"
        paleta = {
            "nombre": f"Personalizada ({c1})",
            "primario": c1,
            "secundario": c2,
            "acento": c3,
            "fondo_suave": c3,
            "texto": "#0f172a",
        }
    else:
        paleta = PALETAS_TRICOLOR["tema_default"]

    justificado_css = (
        "article p, main p, body p, p { text-align: justify !important; text-justify: inter-word !important; }"
        if justificado else
        "article p, main p, body p, p { text-align: left !important; }"
    )
    numerar_eq_css = (
        "body, article { counter-reset: num_eq; }"
        ".mformula.display { counter-increment: num_eq; }"
        ".mformula.display::after { content: '(' counter(num_eq) ')'; position: absolute !important; right: 0 !important; top: 50% !important; transform: translateY(-50%) !important; font-size: 0.95rem; color: #6b7280; font-weight: normal; }"
        if numerar_ecuaciones else ""
    )
    ancho_limpio = (ancho_maximo or "900px").strip() or "900px"
    fuente_limpia = (fuente or 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif').strip()

    # Inyección en temas locales (Tema1..Tema6)
    tema_id = (tema_html or "defecto").strip() or "defecto"
    if tema_id != "defecto":
        tema_candidato = _DIR_TEMAS_HTML / f"{tema_id}.html"
        if not tema_candidato.is_file():
            raise FileNotFoundError(
                f"Tema '{tema_id}' no encontrado en templates/temas_html"
            )
    else:
        tema_candidato = None

    if tema_candidato and tema_candidato.is_file():
        contenido_tema = tema_candidato.read_text(encoding="utf-8", errors="replace")
        if "<article>" in contenido_tema and "</article>" in contenido_tema:
            antes_article = contenido_tema.split("<article>")[0]
            despues_article = contenido_tema.split("</article>")[1]

            # Neutralizar la ejecución redundante no saneada de CNW_MERMAID en las plantillas originales
            antes_article = antes_article.replace("window.CNW_MERMAID.run();", "// window.CNW_MERMAID.run();")
            despues_article = despues_article.replace("window.CNW_MERMAID.run();", "// window.CNW_MERMAID.run();")

            # Actualizar el título del documento en el bloque Hero (Tema 1) o barra superior (Tema 2..Tema 6)
            antes_article = re.sub(
                r'(<(?:h1|div)[^>]*class=["\'][^"\']*hdxf-hero-title[^"\']*["\'][^>]*>)(.*?)(</(?:h1|div)>)',
                rf'\g<1>{_html.escape(titulo)}\g<3>',
                antes_article,
                flags=re.IGNORECASE,
            )
            antes_article = re.sub(
                r'(<span[^>]*style=["\'][^"\']*font-size:\s*12px;[^"\']*["\'][^>]*>📄\s*)(.*?)(</span>)',
                rf'\g<1>{_html.escape(titulo)}\g<3>',
                antes_article,
                flags=re.IGNORECASE,
            )

            # Generar enlaces del sidebar (#hdxfNav en Tema 1 y #docNav en Temas 2..6)
            titulos_h = re.findall(r'<h([1-3])\b[^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</h\1>', render, flags=re.IGNORECASE | re.DOTALL)
            if titulos_h:
                nav_items = []
                for idx, (lvl, id_h, txt_raw) in enumerate(titulos_h):
                    txt_limpio = re.sub(r'<[^>]+>', '', txt_raw).strip()
                    badge = f"{idx+1:02d}" if lvl == "1" else f"{idx+1}.1"
                    pad = "padding-left:1.4rem;font-size:0.8rem;" if lvl in ("2", "3") else ""
                    txt_c = (txt_limpio[:36] + '...') if len(txt_limpio) > 38 else txt_limpio
                    nav_items.append(
                        f'<li><a href="#{id_h}" class="nav-link" style="{pad}" title="{_html.escape(txt_limpio)}">'
                        f'{_html.escape(txt_c)} <span class="nav-badge">{badge}</span></a></li>'
                    )
                nav_html = "\n".join(nav_items)
                antes_article = re.sub(
                    r'(<ul[^>]*id=["\']hdxfNav["\'][^>]*>)[\s\S]*?(</ul>)',
                    rf'\g<1>\n{nav_html}\n\g<2>',
                    antes_article,
                    flags=re.IGNORECASE,
                )
                antes_article = re.sub(
                    r'(<ul[^>]*id=["\']docNav["\'][^>]*>)[\s\S]*?(</ul>)',
                    rf'\g<1>\n{nav_html}\n\g<2>',
                    antes_article,
                    flags=re.IGNORECASE,
                )

            documento = f"{antes_article}<article>\n{render}\n</article>{despues_article}"

            # 1. Asegurar Favicon de alto contraste
            documento = re.sub(r'<link[^>]*rel=["\']icon["\'][^>]*>', '', documento, flags=re.IGNORECASE)
            documento = documento.replace("<head>", f'<head>\n<link rel="icon" type="image/svg+xml" href="{_FAVICON_DATA_URI}">')

            # 1.1 Título del documento tomado directamente del input
            documento = re.sub(r'<title>.*?</title>', f'<title>{_html.escape(titulo)}</title>', documento, flags=re.IGNORECASE)

            # 2. Inyección de KaTeX CSS y reglas para diagramas y fórmulas sin scrollbars
            inyeccion_head = f"""
{tag_css}
<style>
  :root, [data-palette], [data-theme] {{
    --font-main: {fuente_limpia} !important;
    --hdxf-font-main: {fuente_limpia} !important;
    --ancho-maximo: {ancho_limpio} !important;
  }}
  body, article {{
    font-family: {fuente_limpia} !important;
  }}
  .hdxf-with-sidebar, .doc-main {{
    max-width: min({ancho_limpio}, 100%) !important;
    width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
  }}
  article {{
    max-width: 100% !important;
    width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    overflow-wrap: break-word !important;
  }}
  @media (max-width: 1024px) {{
    .hdxf-with-sidebar, .doc-main {{
      padding: 1.5rem 1.75rem 3rem 1.75rem !important;
    }}
  }}
  table {{
    width: 100% !important;
    max-width: 100% !important;
    border-collapse: collapse !important;
    margin: 1.5rem auto !important;
    display: table !important;
  }}
  th, td {{
    border: 1px solid var(--border, #cbd5e1) !important;
    padding: 0.65rem 0.95rem !important;
    text-align: left !important;
    vertical-align: top !important;
  }}
  img, figure {{
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
    max-width: 100% !important;
  }}
  .mformula {{ white-space: nowrap; }}
  .mformula.display {{
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    margin: 1.5rem 0 !important;
    position: relative !important;
    width: 100% !important;
  }}
  {numerar_eq_css}
  /* Diagramas Mermaid y figuras legibles sin barras de desplazamiento (Fase 2) */
  [id^="dmermaid-"] {{
    position: fixed !important;
    left: -99999px !important;
    top: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -1 !important;
  }}
  g.error-icon, svg[aria-roledescription="error"], [aria-roledescription="error"] {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
  }}
  .mermaid, .diagram-container, pre.mermaid, div.mermaid {{
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    margin: 2rem auto !important;
    width: 100% !important;
    max-width: 100% !important;
    max-height: none !important;
    padding: 0.75rem 0 !important;
    overflow: visible !important;
    background: transparent !important;
    border: none !important;
  }}
  .mermaid::before, pre.mermaid::before, div.mermaid::before, .mermaid-contenedor::before,
  pre:has(> .mermaid)::before, pre:has(.mermaid)::before, pre:has(svg)::before, div.mermaid *::before {{
    display: none !important;
    content: none !important;
  }}
  .mermaid svg {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 60% !important;
    max-height: none !important;
    height: auto !important;
    display: block !important;
    margin: 0 auto !important;
    background: transparent !important;
  }}
  .mermaid svg text, .mermaid svg .label, .mermaid svg .nodeLabel, .mermaid svg .edgeLabel {{
    font-size: 15px !important;
  }}

  /* ========================================================================= */
  /* CONTROL DE CONTRASTE ESTRICTO Y ARMONÍA (MODO CLARO Y MODO OSCURO)        */
  /* ========================================================================= */

  :root {{
    --callout-tip-bg: var(--card-alt, rgba(59, 130, 246, 0.05));
    --callout-crit-bg: var(--card-alt, rgba(59, 130, 246, 0.05));
    --callout-warn-bg: var(--card-alt, rgba(59, 130, 246, 0.05));
  }}

  /* MODO CLARO: encabezados de tabla oscuros con contraste absoluto, notas sobrias */
  thead th, th {{
    background: var(--table-header-bg, #f1f5f9) !important;
    color: #0f172a !important; /* Alto contraste 14:1 en modo claro */
    font-weight: 700 !important;
    border: 1px solid var(--border, #cbd5e1) !important;
  }}
  td {{
    color: #1e293b !important;
    border: 1px solid var(--border, #e2e8f0) !important;
  }}
  blockquote, .note, .callout, .admonition, .callout-crit, .callout-warn, .callout-tip, .callout-info, .callout-formula {{
    border-left: 4px solid var(--primary, #3b82f6) !important;
    background-color: var(--card-alt, rgba(59, 130, 246, 0.05)) !important;
    background: var(--card-alt, rgba(59, 130, 246, 0.05)) !important;
    color: #1e293b !important;
    border-radius: 0 8px 8px 0 !important;
    padding: 0.85rem 1.25rem !important;
    margin: 1.25rem 0 !important;
  }}
  blockquote strong, .note strong, .callout strong, .note-title, .callout-crit strong, .callout-warn strong {{
    color: var(--primary, #1e3a8a) !important;
  }}

  /* MODO OSCURO ([data-theme="dark"]): erradicación total de fondos blancos y títulos oscuros */
  [data-theme="dark"], body[data-theme="dark"] {{
    --bg: #0b0f19 !important;
    --text: #f3f4f6 !important;
    --border: #374151 !important;
  }}
  [data-theme="dark"] h1, [data-theme="dark"] h2, [data-theme="dark"] h3, [data-theme="dark"] h4 {{
    color: #f1f5f9 !important; /* Títulos luminosos y legibles contra fondo oscuro */
    border-bottom-color: var(--accent, #60a5fa) !important;
  }}
  [data-theme="dark"] table {{
    background: #111827 !important;
    border-color: #374151 !important;
  }}
  [data-theme="dark"] thead th, [data-theme="dark"] th {{
    background: #1e293b !important; /* Fondo oscuro formal en cabecera */
    color: #f8fafc !important; /* Texto blanco en cabecera */
    border-color: #374151 !important;
  }}
  [data-theme="dark"] tbody tr:nth-child(even) {{
    background: #161e2e !important;
  }}
  [data-theme="dark"] tbody tr:nth-child(odd) {{
    background: #111827 !important;
  }}
  [data-theme="dark"] td {{
    color: #e2e8f0 !important;
    border-color: #374151 !important;
  }}
  [data-theme="dark"] blockquote,
  [data-theme="dark"] .note,
  [data-theme="dark"] .callout,
  [data-theme="dark"] .admonition,
  [data-theme="dark"] .callout-crit,
  [data-theme="dark"] .callout-warn,
  [data-theme="dark"] .callout-tip,
  [data-theme="dark"] .callout-info,
  [data-theme="dark"] .callout-formula {{
    background: #161e2e !important; /* CERO BLOQUES BLANCOS EN OSCURO */
    color: #e2e8f0 !important;
    border-left: 4px solid var(--accent, #60a5fa) !important;
    box-shadow: none !important;
  }}
  [data-theme="dark"] blockquote strong,
  [data-theme="dark"] .note strong,
  [data-theme="dark"] .callout strong,
  [data-theme="dark"] .note-title {{
    color: #93c5fd !important;
  }}

  @media (max-width: 900px) {{
    .hdxf-sidebar {{
      display: none !important;
    }}
    .hdxf-header, .hdxf-with-sidebar {{
      margin-left: 0 !important;
      width: 100% !important;
      padding: 1.5rem 1rem !important;
    }}
  }}
  @media print {{
    .hdxf-sidebar, .hdxf-header, aside, header.no-print, button, .no-print {{
      display: none !important;
    }}
  }}
  {justificado_css}
  {numerar_eq_css}
</style>
"""
            # Inyección de variables CSS dinámicas y sobrescritura de paleta de colores
            # Cumplimiento estricto de docs/mejoras/mejoras_app_02_paleta de colores.md (Sección 2)
            if pal_clave != "tema_default" or paleta["primario"] != "#0284c7":
                inyeccion_head += f"""
<style>
  :root, [data-theme="light"], [data-palette], body.custom-theme {{
    --primary-color: {paleta['primario']};
    --secondary-color: {paleta['secundario']};
    --accent-color: {paleta.get('acento', paleta['secundario'])};
    --primary: {paleta['primario']} !important;
    --accent: {paleta['primario']} !important;
    --accent-hover: {paleta['secundario']} !important;
    --blockquote-border: {paleta['secundario']} !important;
    --table-header-bg: {paleta['fondo_suave']} !important;
    --card-alt: {paleta['fondo_suave']} !important;
  }}
  body.custom-theme h1, body.custom-theme h2, h1, h2, article h1, article h2,
  :root h1, :root h2, [data-theme="light"] h1, [data-theme="light"] h2, [data-palette] h1, [data-palette] h2 {{
    color: var(--primary-color, {paleta['primario']}) !important;
    border-bottom-color: var(--secondary-color, {paleta['secundario']}) !important;
  }}
  body.custom-theme h3, body.custom-theme .subtitle, h3, .subtitle, article h3,
  :root h3, [data-theme="light"] h3, [data-palette] h3 {{
    color: var(--secondary-color, {paleta['secundario']}) !important;
  }}
</style>
"""
            documento = documento.replace("</head>", f"{inyeccion_head}\n</head>")

            # 3. Inyección universal KaTeX + Mermaid para renderizar en cualquier tema
            hay_m = bool(mermaid) or (".mermaid" in render)
            tag_mermaid = _extra_mermaid(True) if hay_m else ""
            inyeccion_body = f"{tag_js}\n{tag_mermaid}\n{_JS_INICIAR_RENDER}"
            # 4. Pie de página dinámico (footer_izq y footer_der) en temas 1..6
            nuevo_footer = f"""
<footer class="hdxf-footer pie-doc" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-top:3rem; padding:1.2rem 0; border-top:1px solid rgba(0,0,0,0.12); font-size:0.88rem;">
    <div><strong>{_html.escape(f_izq)}</strong></div>
    <div>{_html.escape(f_der)}</div>
</footer>
"""
            if re.search(r'<footer[^>]*class=["\'][^"\']*hdxf-footer[^"\']*["\'][^>]*>', documento, flags=re.IGNORECASE):
                documento = re.sub(
                    r'<footer[^>]*class=["\'][^"\']*hdxf-footer[^"\']*["\'][^>]*>[\s\S]*?</footer>',
                    nuevo_footer,
                    documento,
                    flags=re.IGNORECASE,
                )
            else:
                documento = documento.replace("</article>", f"</article>\n{nuevo_footer}", 1)
            documento = documento.replace("</body>", f"{inyeccion_body}\n</body>")

            avisos = [
                f"Plantilla HTML aplicada: {tema_id}. Favicon de alto contraste (fondo negro) e inyección KaTeX universal activas.",
                (
                    "Vista de fórmulas vía KaTeX incrustado en el HTML "
                    "(documento autocontenido; las fuentes se resuelven con el paquete "
                    "local `katex/fonts/` o con el CDN como respaldo). Favicon oficial embebido."
                    if local else
                    "Fórmulas KaTeX vía CDN con fallback offline. Favicon oficial embebido."
                ),
                f"Contenedor ajustado a {ancho_limpio} de ancho máximo.",
            ]
            return documento, len(formulas), avisos

    # Plantilla Base Clásica
    documento = (
        _PLANTILLA_BASE
        .replace("__TITULO__", _html.escape(titulo))
        .replace("__FAVICON__", _FAVICON_DATA_URI)
        .replace("__KATEX_CSS_TAG__", tag_css)
        .replace("__KATEX_JS_TAG__", tag_js)
        .replace("__EXTRA__", _extra_mermaid(bool(mermaid)))
        .replace("__FUENTE__", fuente_limpia)
        .replace("__TAMANIO__", str(tamanio_pt))
        .replace("__INTERLINEADO__", str(interlineado))
        .replace("__ANCHO_MAXIMO__", ancho_limpio)
        .replace("__JUSTIFICADO_CSS__", justificado_css)
        .replace("__NUMERAR_EQ_CSS__", numerar_eq_css)
        .replace("__PALETA_PRIMARIO__", paleta["primario"])
        .replace("__PALETA_SECUNDARIO__", paleta["secundario"])
        .replace("__PALETA_FONDO_SUAVE__", paleta["fondo_suave"])
        .replace("__FOOTER_IZQ__", _html.escape(f_izq))
        .replace("__FOOTER_DER__", _html.escape(f_der))
        .replace("__CONTENIDO__", render)
        .replace("__JS_INICIAR_RENDER__", _JS_INICIAR_RENDER)
    )

    avisos = [
        (
            "Vista de fórmulas vía KaTeX incrustado en el HTML "
            "(documento autocontenido; las fuentes se resuelven con el paquete "
            "local `katex/fonts/` o con el CDN como respaldo). Favicon oficial embebido."
            if local else
            "Fórmulas KaTeX vía CDN con fallback offline. Favicon oficial embebido."
        ),
        "Favicon de alto contraste con fondo negro e isotipo blanco inyectado.",
        "Tablas y ecuaciones centradas horizontalmente.",
    ]
    if numerar_ecuaciones:
        avisos.append("Ecuaciones numeradas a la derecha.")
    if mermaid:
        avisos.append("Diagramas mermaid renderizados con soporte interactivo.")

    return documento, len(formulas), avisos
