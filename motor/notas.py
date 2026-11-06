# -*- coding: utf-8 -*-
"""Soporte canónico de notas/callouts GitHub-style para MarkFlow Office (v1.21.0).

Este módulo es la **referencia canónica** del comportamiento de las notas
(``> [!NOTE]``, ``> [!TIP]``, etc.); el frontend mantiene un espejo en JS
(``static/js/markdown_transforms.js`` · ``MFOTransforms``). Mantener ambos en
paridad estricta.

Contrato (v1.21.0 — mejoras 3 y 4 del plan ``mejoras_app_12``):

- ``normalizar_etiquetas_nota`` canonicaliza variantes (``[!NOTA]``,
  ``[!CONSEJO]``…) a la forma GitHub ``[!NOTE]``/``[!TIP]``/… **conservando**
  el marcador: ya no es un "parásito", es sintaxis soportada de callout que
  ``a_html`` renderiza con estilo propio (icono, color y etiqueta).
- ``quitar_notas`` elimina **únicamente** los bloques de callout (bloques
  cuya cabecera lleva ``> [!TIPO]``), preservando bloques LaTeX
  (``$$…$$``, ``\\[…\\]``, entornos), bloques de código, tablas, imágenes,
  HTML embebido y **citas normales** que no sean notas. La protección se hace
  con placeholders únicos y reemplazos por función (nunca cadenas de
  reemplazo que contengan ``$&``/``$1``/``$$``).
- ``envolver_callouts_html`` transforma los ``<blockquote>`` cuya cabecera
  trae ``[!TIPO]`` en ``<div class="callout callout-TIPO">`` renderizados.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Tipos de nota soportados (GitHub canonical + aliases en español)
# ---------------------------------------------------------------------------
TIPOS_NOTA: dict[str, dict[str, str]] = {
    "NOTE": {"icono": "\U0001f4dd", "etiqueta": "Nota", "clase": "note"},
    "TIP": {"icono": "\U0001f4a1", "etiqueta": "Consejo", "clase": "tip"},
    "IMPORTANT": {"icono": "\u2757", "etiqueta": "Importante", "clase": "important"},
    "WARNING": {"icono": "\u26a0\ufe0f", "etiqueta": "Advertencia", "clase": "warning"},
    "CAUTION": {"icono": "\u26d4", "etiqueta": "Precauci\u00f3n", "clase": "caution"},
}

_ALIASES: dict[str, str] = {
    "note": "NOTE", "nota": "NOTE",
    "tip": "TIP", "consejo": "TIP",
    "important": "IMPORTANT", "importante": "IMPORTANT",
    "warning": "WARNING", "advertencia": "WARNING",
    "caution": "CAUTION", "precaucion": "CAUTION",
}

_PATRON_TIPOS = "|".join(sorted(_ALIASES))

_RE_ETIQUETA = re.compile(r"\[!\s*(" + _PATRON_TIPOS + r")\s*\]", re.IGNORECASE)

# Cabecera de bloque de nota en Markdown: línea `> [!TIPO]` (texto tras el
# marcador en la misma línea o continuación en las líneas siguientes `>`).
# Nota: se usa [ \t]* (nunca \s*) para que el patrón no cruce saltos de línea.
_RE_CABECERA_NOTA = re.compile(
    r"^[ \t]*(?P<pre>>[ \t]*)\[!\s*(?P<tipo>" + _PATRON_TIPOS + r")\s*\](?P<resto>[^\n]*)$",
    re.IGNORECASE | re.MULTILINE,
)

_RE_LINEA_CITA = re.compile(r"^\s*>")

# Bloques protegidos durante quitar_notas (LaTeX display y cercos de código)
_RE_BLOQUE_CODIGO = re.compile(
    r"(^[ \t]*`{3,}[^\n]*\n[\s\S]*?^[ \t]*`{3,}[ \t]*$)", re.MULTILINE
)
_RE_BLOQUE_LATEX = re.compile(
    r"(^[ \t]*\$\$[^\n]*\n[\s\S]*?^[ \t]*\$\$[ \t]*$"          # $$ display multilínea
    r"|^[ \t]*\\\[[^\n]*\n[\s\S]*?^[ \t]*\\\][ \t]*$"          # \[ display multilínea
    r"|^[ \t]*\\begin\{[a-zA-Z*]+\}[\s\S]*?\\end\{[a-zA-Z*]+\}[ \t]*$)",  # entornos TeX
    re.MULTILINE,
)


def canonicalizar_tipo(tipo: str) -> str | None:
    """Devuelve el tipo canónico (``NOTE``/``TIP``/…) o ``None`` si es desconocido."""
    if not tipo:
        return None
    return _ALIASES.get(str(tipo).strip().lower())


def normalizar_etiquetas_nota(texto: str) -> str:
    """Canonicaliza las variantes de etiqueta de nota a la forma GitHub.

    ``> [!NOTA] Texto`` → ``> [!NOTE] Texto`` · ``> [!CONSEJO]`` → ``> [!TIP]``…

    A diferencia de la versión anterior (v1.20.x), el marcador **se conserva**:
    es sintaxis soportada que ``a_html`` convierte en un callout renderizado
    (mejora 3 — el usuario ya no ve ``> [!NOTE]`` como texto plano).
    """
    if not texto:
        return ""

    def _canon(m: re.Match) -> str:
        canon = canonicalizar_tipo(m.group(1))
        if canon is None:
            return m.group(0)
        return f"[!{canon}]"

    return _RE_ETIQUETA.sub(_canon, texto)


def quitar_notas(texto: str) -> str:
    r"""Elimina globalmente los bloques de nota/callout (``> [!TIPO]``).

    Reglas (mejora 4):
    - Solo se eliminan los bloques **cuya cabecera lleva** ``[!TIPO]``
      (GitHub alerts). Las citas normales ``> texto`` se conservan intactas.
    - Los bloques LaTeX (``$$``, ``\[…\]``, entornos) y de código
      (``` ``` ```) se protegen previamente con placeholders para que ninguna
      transformación toque ``\``, ``$``, ``>`` o ``_`` dentro de ellos.
    - El reemplazo se hace con **funciones** (nunca cadenas que contengan
      ``$&``/``$1``/``$$``, que producirían símbolos extraños).

    Entrada vacía → cadena vacía.
    """
    if not texto:
        return ""

    texto = normalizar_etiquetas_nota(texto)
    protegido, restituciones = _proteger_bloques(texto)

    lineas = protegido.split("\n")
    salida: list[str] = []
    i = 0
    while i < len(lineas):
        m = _RE_CABECERA_NOTA.match(lineas[i])
        if m:
            # ── Bloque de nota: cabecera + todas las líneas `>` contiguas ──
            cuerpo = [m.group("resto").strip()]
            i += 1
            while i < len(lineas) and _RE_LINEA_CITA.match(lineas[i]):
                cuerpo.append(re.sub(r"^\s*>\s?", "", lineas[i]))
                i += 1
            bloque = "\n".join(cuerpo).strip()
            if bloque:
                salida.extend(bloque.split("\n"))
                salida.append("")
            continue
        salida.append(lineas[i])
        i += 1

    resultado = "\n".join(salida)
    resultado = re.sub(r"\n{3,}", "\n\n", resultado)
    return _restaurar_bloques(resultado, restituciones)


def _proteger_bloques(texto: str) -> tuple[str, dict[int, str]]:
    """Enmascara bloques LaTeX y de código con placeholders únicos.

    Devuelve ``(texto_protegido, mapa_placeholder→fragmento)``.
    """
    restituciones: dict[int, str] = {}
    contador = {"n": 0}

    def _ph(m: re.Match) -> str:
        contador["n"] += 1
        restituciones[contador["n"]] = m.group(0)
        return f"\x00MFOQT{contador['n']}\x00"

    texto = _RE_BLOQUE_LATEX.sub(_ph, texto)
    texto = _RE_BLOQUE_CODIGO.sub(_ph, texto)
    return texto, restituciones


def _restaurar_bloques(texto: str, restituciones: dict[int, str]) -> str:
    """Restaura los placeholders exactamente como estaban (reemplazo por función)."""
    return re.sub(r"\x00MFOQT(\d+)\x00", lambda m: restituciones.get(int(m.group(1)), ""), texto)


def limpiar_notas_para_pandoc(texto: str) -> str:
    """Convierte los callouts en citas simples para pandoc (DOCX/PDF).

    pandoc no entiende ``> [!NOTE]`` y lo mostraría como texto literal dentro
    de la cita; esta función quita **solo el marcador** conservando el bloque
    ``>`` (la nota sigue apareciendo como cita destacada en Word/PDF).
    """
    if not texto or "[!" not in texto:
        return texto

    def _sub(m: re.Match) -> str:
        canon = canonicalizar_tipo(m.group(2))
        if canon is None:
            return m.group(0)
        resto = (m.group(3) or "").lstrip()
        if resto:
            return f"{m.group(1)}{resto}"
        # Marcador solo en su línea: se elimina la línea completa
        return ""

    return _RE_CABECERA_NOTA.sub(_sub, texto)


# ---------------------------------------------------------------------------
# Renderizado de callouts en HTML (para a_html)
# ---------------------------------------------------------------------------
def envolver_callouts_html(html: str) -> str:
    """Transforma ``<blockquote>`` con cabecera ``[!TIPO]`` en callouts renderizados.

    Entrada (markdown-it):
        <blockquote>
        <p>[!NOTE]\nTexto de la nota</p>
        </blockquote>

    Salida:
        <div class="callout callout-note">
          <p class="callout-title">📝 Nota</p>
          <div class="callout-body"><p>Texto de la nota</p></div>
        </div>
    """
    if not html or "[!" not in html:
        return html

    patron = re.compile(
        r"<blockquote>\s*<p>\s*\[!\s*(" + _PATRON_TIPOS + r")\s*\]\s*?"
        r"([\s\S]*?)</p>([\s\S]*?)</blockquote>",
        re.IGNORECASE,
    )

    def _sub(m: re.Match) -> str:
        tipo = canonicalizar_tipo(m.group(1))
        if tipo is None:
            return m.group(0)
        meta = TIPOS_NOTA[tipo]
        cuerpo_primero = (m.group(2) or "").strip()
        resto = m.group(3) or ""
        cuerpo = (f"<p>{cuerpo_primero}</p>" if cuerpo_primero else "") + resto
        return (
            f'<div class="callout callout-{meta["clase"]}" role="note">'
            f'<p class="callout-title">{meta["icono"]} {meta["etiqueta"]}</p>'
            f'<div class="callout-body">{cuerpo}</div>'
            f"</div>"
        )

    return patron.sub(_sub, html)


# CSS de callouts para inyectar en las plantillas HTML (claro y oscuro)
CALLOUT_CSS = """
  /* ── Callouts GitHub-style (notas [!NOTE]… — v1.21.0) ─────────────────── */
  .callout {
    border-left: 4px solid var(--color-primario, #3b82f6);
    margin: 1.25rem 0;
    padding: .85rem 1.1rem;
    border-radius: 0 8px 8px 0;
    background: rgba(59, 130, 246, 0.06);
    break-inside: avoid;
  }
  .callout p { margin: .3rem 0; }
  .callout-title {
    font-weight: 700;
    margin: 0 0 .45rem;
    display: flex;
    align-items: center;
    gap: .4rem;
    color: var(--color-primario, #1d4ed8);
  }
  .callout-body > :first-child { margin-top: 0; }
  .callout-body > :last-child { margin-bottom: 0; }
  .callout-note      { border-left-color: #3b82f6; background: rgba(59, 130, 246, 0.07); }
  .callout-note .callout-title { color: #1d4ed8; }
  .callout-tip       { border-left-color: #10b981; background: rgba(16, 185, 129, 0.07); }
  .callout-tip .callout-title { color: #047857; }
  .callout-important { border-left-color: #8b5cf6; background: rgba(139, 92, 246, 0.07); }
  .callout-important .callout-title { color: #6d28d9; }
  .callout-warning   { border-left-color: #f59e0b; background: rgba(245, 158, 11, 0.08); }
  .callout-warning .callout-title { color: #b45309; }
  .callout-caution   { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.07); }
  .callout-caution .callout-title { color: #b91c1c; }
  [data-theme="dark"] .callout { background: #161e2e !important; }
  [data-theme="dark"] .callout-note .callout-title { color: #93c5fd; }
  [data-theme="dark"] .callout-tip .callout-title { color: #6ee7b7; }
  [data-theme="dark"] .callout-important .callout-title { color: #c4b5fd; }
  [data-theme="dark"] .callout-warning .callout-title { color: #fcd34d; }
  [data-theme="dark"] .callout-caution .callout-title { color: #fca5a5; }
"""
