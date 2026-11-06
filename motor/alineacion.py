# -*- coding: utf-8 -*-
"""Soporte canónico de alineación de bloques para MarkFlow Office (v1.21.0).

Mejora 1 del plan ``mejoras_app_12``: botones de alineación (izquierda,
centrado, derecha, justificado) aplicados al párrafo/bloque seleccionado.

Markdown no soporta alineación nativa; se usa **HTML embebido** como
representación persistente:

    <div align="center">

    Contenido del párrafo con **negrita** y $fórmulas$.

    </div>

Reglas (idénticas en Python y en el espejo JS del editor):

- ``align="center|right|justify"`` → atributo ``alignment`` en los nodos
  ``paragraph``/``heading`` del documento ProseMirror (``attrs.alignment``).
- ``align="left"`` (o ausencia) → sin atributo (valor por defecto): el
  serializador elimina la envoltura.
- El envoltorio reemplaza cualquier alineación previa (nunca se anida).
- El contenido interno del ``<div>`` se parsea como Markdown normal
  (negritas, fórmulas, listas… no se tocan).

Módulos consumidores:

- ``app/servicios/editor_markdown.py`` — parseo MD→doc y serialización doc→MD.
- ``motor/a_html.py`` — ``aplicar_alineacion_html`` tras el render de
  markdown-it (que deja pasar el HTML crudo) para que la alineación sobreviva
  al CSS global ``p { text-align: … !important }``.
- ``motor/a_docx.py`` — ``limpiar_alineacion_para_pandoc`` elimina los
  envoltorios antes de pandoc (Word no representa alineación de bloque desde
  Markdown crudo; se evita texto HTML literal en el .docx).
"""

from __future__ import annotations

import re

ALINEACIONES_VALIDAS = ("left", "center", "right", "justify")

# Apertura de envoltorio: <div align="center"> o <div style="text-align: center">
_RE_APERTURA = re.compile(
    r'^[ \t]*<div\s+(?:align=["\'](?P<align1>' + "|".join(ALINEACIONES_VALIDAS) + r')["\']'
    r'|style=["\'][^"\']*text-align:\s*(?P<align2>' + "|".join(ALINEACIONES_VALIDAS) + r')[^"\']*["\'])'
    r"[^>]*>[ \t]*$",
    re.IGNORECASE,
)
_RE_CIERRE = re.compile(r"^[ \t]*</div>[ \t]*$")

_CLASES = {a: f"mfo-align-{a}" for a in ALINEACIONES_VALIDAS}

ALINEACION_CSS = """
  /* ── Alineación de bloques (v1.21.0) — gana al `p { text-align: … !important }` ── */
  .mfo-align-center p, .mfo-align-center h1, .mfo-align-center h2, .mfo-align-center h3,
  .mfo-align-center h4, .mfo-align-center h5, .mfo-align-center h6,
  .mfo-align-center li, .mfo-align-center pre, .mfo-align-center blockquote { text-align: center !important; }
  .mfo-align-right p, .mfo-align-right h1, .mfo-align-right h2, .mfo-align-right h3,
  .mfo-align-right h4, .mfo-align-right h5, .mfo-align-right h6,
  .mfo-align-right li, .mfo-align-right pre, .mfo-align-right blockquote { text-align: right !important; }
  .mfo-align-justify p, .mfo-align-justify h1, .mfo-align-justify h2, .mfo-align-justify h3,
  .mfo-align-justify li, .mfo-align-justify pre, .mfo-align-justify blockquote {
    text-align: justify !important; text-justify: inter-word !important;
  }
  .mfo-align-left p, .mfo-align-left h1, .mfo-align-left h2, .mfo-align-left h3,
  .mfo-align-left li, .mfo-align-left pre, .mfo-align-left blockquote { text-align: left !important; }
"""


def normalizar_alineacion(valor: object) -> str:
    """Devuelve una alineación válida (``''``/``left``/``center``/``right``/``justify``)."""
    v = str(valor or "").strip().lower()
    return v if v in ALINEACIONES_VALIDAS else ""


def segmentar_por_alineacion(texto: str) -> list[tuple[str, str]]:
    """Segmenta un Markdown en ``(alineacion, contenido)`` conservando el orden.

    - Los bloques **fuera** de cualquier envoltorio se emiten como
      ``("", contenido)``.
    - Cada envoltorio ``<div align="X">…</div>`` emite ``(X, contenido_interno)``
      sin las líneas de apertura/cierre.
    - Un ``align="left"`` (o inválido) se emite como ``("", contenido)``: el
      envoltorio no aporta nada representable.

    El segmentador es la base del parseo MD→doc del editor visual: parsea
    **cada segmento por separado** (el contenido interno es Markdown normal)
    y aplica la alineación a los nodos de bloque resultantes, sin depender de
    placeholders ni de que markdown-it soporte HTML de bloque envuelto.
    """
    if not texto or "<div" not in texto:
        return [("", texto or "")]

    lineas = texto.split("\n")
    segmentos: list[tuple[str, str]] = []
    buffer: list[str] = []
    i = 0
    while i < len(lineas):
        m = _RE_APERTURA.match(lineas[i])
        if m:
            alineacion = normalizar_alineacion(m.group("align1") or m.group("align2"))
            i += 1
            cuerpo: list[str] = []
            while i < len(lineas) and not _RE_CIERRE.match(lineas[i]):
                cuerpo.append(lineas[i])
                i += 1
            if i < len(lineas):  # hay cierre </div>
                i += 1
            contenido = "\n".join(cuerpo).strip("\n")
            if buffer:
                segmentos.append(("", "\n".join(buffer).strip("\n")))
                buffer = []
            if alineacion and alineacion != "left" and contenido:
                segmentos.append((alineacion, contenido))
            elif contenido:  # left/inválido: conservar el contenido sin envoltura
                buffer.extend(contenido.split("\n"))
            continue
        buffer.append(lineas[i])
        i += 1
    if buffer:
        segmentos.append(("", "\n".join(buffer).strip("\n")))
    return [(a, c) for a, c in segmentos if c]


def extraer_bloques_alineados(texto: str) -> tuple[str, list[tuple[str, str]]]:
    """Extrae los envoltorios ``<div align>`` de un Markdown.

    Devuelve ``(texto_sin_envoltorios, envoltorios)``, donde cada envoltorio es
    ``(alineacion, contenido)``. El texto resultante lleva un placeholder
    ``\x00MFOALINE<n>\x00`` en la posición del bloque para que ``md_a_doc``
    aplique la alineación a los nodos parseados del contenido.
    """
    if not texto or "<div" not in texto:
        return texto, []

    lineas = texto.split("\n")
    salida: list[str] = []
    envoltorios: list[tuple[str, str]] = []
    i = 0
    while i < len(lineas):
        m = _RE_APERTURA.match(lineas[i])
        if m:
            alineacion = normalizar_alineacion(m.group("align1") or m.group("align2"))
            i += 1
            cuerpo: list[str] = []
            while i < len(lineas) and not _RE_CIERRE.match(lineas[i]):
                cuerpo.append(lineas[i])
                i += 1
            if i < len(lineas):  # hay cierre </div>
                i += 1
            if alineacion:
                envoltorios.append((alineacion, "\n".join(cuerpo).strip("\n")))
                salida.append(f"\x00MFOALINE{len(envoltorios)}\x00")
                salida.append("")
            else:
                # align="left" o inválido: conservar solo el contenido (sin envoltura)
                salida.extend(cuerpo)
            continue
        salida.append(lineas[i])
        i += 1
    return "\n".join(salida), envoltorios


def aplicar_alineacion_html(html: str) -> str:
    """Post-proceso del HTML renderizado: añade las clases ``mfo-align-*``.

    markdown-it deja pasar ``<div align="…">`` como HTML crudo; sin estas
    clases, el CSS global ``p { text-align: justify !important }`` de las
    plantillas anularía la alineación heredada del ``div``. La clase se aplica
    al div (con su ``align`` original conservado para máxima compatibilidad).
    """
    if not html or "align=" not in html:
        return html

    def _sub(m: re.Match) -> str:
        alineacion = normalizar_alineacion(m.group(2))
        if not alineacion:
            return m.group(0)
        attrs = (m.group(1) or "").strip()
        if 'class="' in attrs:
            attrs = re.sub(r'class="([^"]*)"', lambda c: f'class="{c.group(1)} {_CLASES[alineacion]}"', attrs, count=1)
        else:
            attrs = ('class="%s"' % _CLASES[alineacion]) + ((" " + attrs) if attrs else "")
        return f"<div {attrs} align=\"{alineacion}\">"

    return re.sub(r"<div\b([^>]*)\balign=[\"']([^\"']+)[\"']([^>]*)>", _sub, html, flags=re.IGNORECASE)


def limpiar_alineacion_para_pandoc(texto: str) -> str:
    """Elimina los envoltorios ``<div align>…</div>`` conservando el contenido.

    Se usa en el pipeline DOCX (pandoc) y en el fallback GenOffice: Word no
    puede representar la alineación de bloque desde Markdown crudo y el HTML
    literal saldría como texto visible en el documento.
    """
    if not texto or "<div" not in texto:
        return texto
    lineas = texto.split("\n")
    salida: list[str] = []
    dentro = 0
    for linea in lineas:
        if _RE_APERTURA.match(linea):
            dentro += 1
            continue
        if _RE_CIERRE.match(linea):
            dentro = max(0, dentro - 1)
            continue
        salida.append(linea)
    return "\n".join(salida)
