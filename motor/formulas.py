"""Motor unificado de protección, rescate y transformación de fórmulas matemáticas.

Cumple con la arquitectura de MarkFlow Office (SSOT único para Docs, Word, PDF, HTML y Excel):
  1. Rescate y limpieza de fórmulas malformadas (corchetes sueltos, variables entre paréntesis,
     subíndices partidos por saltos de línea, llaves sin guion bajo, etc.).
  2. Extracción y protección estricta previa al renderizado de Markdown (tokens @@FORMULA_...@@).
  3. Re-inserción canónica según formato (HTML con KaTeX local, Word con OMML para Pandoc,
     PDF editorial y texto legible en Unicode para celdas de Excel).
  4. Conversión determinista de LaTeX a notación Unicode legible para Excel (.xlsx).
"""

from __future__ import annotations

import re
from typing import Any

# Delimitadores canónicos
_RE_BLOQUE_CODIGO = re.compile(r"```[\s\S]*?(?:```|\Z)|`[^`\n]+`")

# Subíndices y superíndices Unicode
_MAPA_SUBINDICES = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
    "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ",
    "k": "ₖ", "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ",
    "p": "ₚ", "r": "ᵣ", "s": "ₛ", "t": "ₜ", "u": "ᵤ",
    "v": "ᵥ", "x": "ₓ",
    "A": "ₐ", "E": "ₑ", "H": "ₕ", "I": "ᵢ", "J": "ⱼ",
    "K": "ₖ", "L": "ₗ", "M": "ₘ", "N": "ₙ", "O": "ₒ",
    "P": "ₚ", "R": "ᵣ", "S": "ₛ", "T": "ₜ", "U": "ᵤ",
    "V": "ᵥ", "X": "ₓ",
}

_MAPA_SUPERINDICES = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ",
    "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ",
    "k": "ᵏ", "l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ",
    "p": "ᵖ", "r": "ʳ", "s": "ˢ", "t": "ᵗ", "u": "ᵘ",
    "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ",
    "A": "ᴬ", "B": "ᴮ", "D": "ᴰ", "E": "ᴱ", "G": "ᴳ",
    "H": "ᴴ", "I": "ᴵ", "J": "ᴶ", "K": "ᴷ", "L": "ᴸ",
    "M": "ᴹ", "N": "ᴺ", "O": "ᴼ", "P": "ᴾ", "R": "ᴿ",
    "T": "ᵀ", "U": "ᵁ", "V": "ⱽ", "W": "ᵂ",
}

_SIMBOLOS_TEX = {
    r"\cdot": "·",
    r"\times": "×",
    r"\approx": "≈",
    r"\leq": "≤",
    r"\le": "≤",
    r"\geq": "≥",
    r"\ge": "≥",
    r"\neq": "≠",
    r"\ne": "≠",
    r"\pm": "±",
    r"\mp": "∓",
    r"\infty": "∞",
    r"\pi": "π",
    r"\rightarrow": "→",
    r"\to": "→",
    r"\leftarrow": "←",
    r"\gets": "←",
    r"\leftrightarrow": "↔",
    r"\Rightarrow": "⇒",
    r"\Leftarrow": "⇐",
    r"\Leftrightarrow": "⇔",
    r"\mapsto": "↦",
    r"\uparrow": "↑",
    r"\downarrow": "↓",
    r"\equiv": "≡",
    r"\sim": "~",
    r"\dots": "...",
    r"\cdots": "⋯",
    r"\Delta": "Δ",
    r"\delta": "δ",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\theta": "θ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\rho": "ρ",
    r"\sigma": "σ",
    r"\tau": "τ",
    r"\phi": "φ",
    r"\omega": "ω",
    r"\Omega": "Ω",
    r"\partial": "∂",
    r"\nabla": "∇",
    r"\sum": "∑",
    r"\prod": "∏",
    r"\int": "∫",
}


# ============================================================================
#  1. RESCATE Y SANEAMIENTO DE FÓRMULAS DEFECTUOSAS DEL FUENTE
# ============================================================================

def reparar_sintaxis_latex_interna(tex: str) -> str:
    r"""Corrige errores sintácticos comunes generados por LLMs o conversiones OCR.

    Ejemplos:
      - `\right){codo}` -> `\right)_{codo}`
      - `n{tees}` -> `n_{tees}`
      - `·` (Unicode) -> `\cdot`
      - `({L_{e}}{D}){tee}` -> `\left(\frac{L_{e}}{D}\right)_{tee}`
      - `( {d{int}}{1000} )` -> `\left(\frac{d_{int}}{1000}\right)`
    """
    if not tex:
        return ""

    t = tex

    # Normalizar punto medio tipográfico a \cdot
    t = re.sub(r"(?<=\S)\s*[·•]\s*(?=\S)", r" \\cdot ", t)

    # Corregir subíndices sin guion bajo tras cierres: `\right){etiqueta}` -> `\right)_{etiqueta}`
    t = re.sub(r"(\\right\s*[\)\]\}])\s*\{([a-zA-Z0-9_+ -]+)\}", r"\1_{\2}", t)

    # Corregir subíndices de variables: `n{tees}` o `Q{medio}` -> `n_{tees}`, `Q_{medio}`
    t = re.sub(r"\b([a-zA-Z])\{([a-zA-Z0-9_+ -]+)\}", r"\1_{\2}", t)

    # Corregir fracciones truncadas como `({L_{e}}{D})` o `({d{int}}{1000})`
    def _reparar_frac_implicita(m: re.Match) -> str:
        num = m.group(1).strip()
        den = m.group(2).strip()
        # Si num o den parecen componentes de fracción
        return rf"\left(\frac{{{num}}}{{{den}}}\right)"

    # Caso 1: `({A}{B})`
    t = re.sub(
        r"\(\s*\{([^{}]+)\}\s*\{([^{}]+)\}\s*\)",
        _reparar_frac_implicita,
        t,
    )
    # Caso 2: `({d{int}}{1000})` (anidamiento de un subíndice en numerador)
    t = re.sub(
        r"\(\s*\{([a-zA-Z0-9_\\]+(?:\{[^{}]*\})?)\}\s*\{([0-9a-zA-Z_\\]+)\}\s*\)",
        _reparar_frac_implicita,
        t,
    )

    # Subíndice pegado tras paréntesis: `\right)_{tee}` ya reparado o `){tee}` -> `)_{tee}`
    t = re.sub(r"\)\s*\{([a-zA-Z0-9_+ -]+)\}", r")_{\1}", t)

    # Corregir `\left(` sin delimitador de escape si está desbalanceado
    t = re.sub(r"\\left\s*\$\s*\)", r"\right)", t)

    return t


def rescatar_formulas_defectuosas_fuente(texto: str) -> tuple[str, list[str]]:
    """Detecta y normaliza fórmulas malformadas en el Markdown del usuario.

    Detecta:
      1. Ecuaciones en bloque delimitadas con corchetes simples `[ ... ]` en lugar de `\\[ ... \\]`.
      2. Ecuaciones multilínea rotas con saltos de línea arbitrarios entre corchetes `[\\n L \\n total = ... ]`.
      3. Variables explicativas al inicio de párrafo: `(L_{e}):`, `(n_{codos}):`, `(({L_{e}}{D})_{codo}):`.
    """
    avisos: list[str] = []
    lineas = texto.split("\n")
    resultado: list[str] = []
    i = 0
    n = len(lineas)

    while i < n:
        linea = lineas[i]
        linea_strip = linea.strip()

        # -------------------------------------------------------------------
        # Caso A: Bloque con saltos de línea multilinea dentro de corchetes `[` ... `]`
        # Ejemplo:
        # [
        # L
        # total
        #  =L
        # tramo
        #  +L
        # e
        #  ]
        # -------------------------------------------------------------------
        if linea_strip == "[" or (linea_strip.startswith("[") and not linea_strip.endswith("]") and not re.match(r"^\[\^?[a-zA-Z0-9_-]+\]:", linea_strip)):
            # Explorar hacia adelante buscando el cierre `]`
            j = i + 1
            bloque_lineas = [linea]
            encontrado_cierre = False
            while j < n and j <= i + 25:  # Límite de seguridad
                bloque_lineas.append(lineas[j])
                if "]" in lineas[j] and not lineas[j].strip().startswith("["):
                    encontrado_cierre = True
                    break
                j += 1

            if encontrado_cierre:
                contenido_bloque = "\n".join(bloque_lineas)
                # Verificar si contiene signos matemáticos
                if any(op in contenido_bloque for op in ("=", "+", "-", r"\frac", r"\text", "_", r"\cdot")):
                    # Unificar y reconstruir la ecuación
                    partes = [l.strip() for l in bloque_lineas]
                    # Remover el primer '[' y el último ']'
                    texto_unido = " ".join(partes)
                    if texto_unido.startswith("["):
                        texto_unido = texto_unido[1:]
                    if texto_unido.endswith("]"):
                        texto_unido = texto_unido[:-1]

                    # Corregir palabras divididas como "L total" -> "L_{total}", "L tramo" -> "L_{tramo}", "L e" -> "L_{e}"
                    texto_unido = re.sub(r"\bL\s+total\b", r"L_{\\text{total}}", texto_unido, flags=re.I)
                    texto_unido = re.sub(r"\bL\s+tramo\b", r"L_{\\text{tramo}}", texto_unido, flags=re.I)
                    texto_unido = re.sub(r"\bL\s+e\b", r"L_{\\text{e}}", texto_unido, flags=re.I)
                    texto_unido = re.sub(r"\s*=\s*", r" = ", texto_unido)
                    texto_unido = re.sub(r"\s*\+\s*", r" + ", texto_unido)
                    texto_unido = re.sub(r"\s+", " ", texto_unido).strip()

                    eq_limpia = reparar_sintaxis_latex_interna(texto_unido)
                    resultado.append(f"\n\\[\n{eq_limpia}\n\\]\n")
                    avisos.append(f"Línea {i+1}: Se normalizó una fórmula multilínea delimitada incorrectamente con corchetes simples.")
                    i = j + 1
                    continue

        # -------------------------------------------------------------------
        # Caso B: Ecuación unilínea entre corchetes simples `[ ... ]`
        # Ejemplo: `[L_{\text{e}} = \left( ... \right)]`
        # -------------------------------------------------------------------
        if linea_strip.startswith("[") and linea_strip.endswith("]"):
            # Asegurar que no sea un enlace markdown o nota al pie o número simple: `[1]`, `[30.00]`
            contenido = linea_strip[1:-1].strip()
            es_numero_o_ref = bool(re.match(r"^[\d.,\s]+$", contenido) or re.match(r"^\^?[a-zA-Z0-9_-]+$", contenido))
            tiene_signo_mate = any(c in contenido for c in ("=", r"\text", r"\frac", r"\left", r"\cdot", "·", "_", "^"))

            if not es_numero_o_ref and tiene_signo_mate:
                eq_limpia = reparar_sintaxis_latex_interna(contenido)
                resultado.append(f"\n\\[\n{eq_limpia}\n\\]\n")
                avisos.append(f"Línea {i+1}: Se convirtió bloque con corchetes simples '[ ... ]' a ecuación display '\\\\[ ... \\\\]'.")
                i += 1
                continue

        # -------------------------------------------------------------------
        # Caso C: Variables explicativas al inicio de párrafo:
        # Ejemplo: `(L_{e}): Longitud...` -> `\(L_{e}\): Longitud...`
        #          `(({L_{e}}{D})_{codo}): Relación...` -> `\(\left(\frac{L_{e}}{D}\right)_{codo}\): Relación...`
        # -------------------------------------------------------------------
        def _reemplazar_variable_parentesis(m: re.Match) -> str:
            var_raw = m.group(1).strip()
            resto = m.group(2)
            var_limpia = reparar_sintaxis_latex_interna(var_raw)
            avisos.append(f"Línea {i+1}: Variable '({var_raw})' normalizada a notación matemática '\\({var_limpia}\\)'.")
            return f"\\({var_limpia}\\){resto}"

        # Patrón para `(VARIABLE):` o `((VARIABLE)_{sub}):`
        linea_mod = re.sub(
            r"^\s*\(\s*(\([^{}]*\{[^{}]*\}[^{}]*\)|[a-zA-Z0-9_\\]+(?:\{[^{}]*\})?(?:_[a-zA-Z0-9_{}]+)?)\s*\)(\s*:)",
            _reemplazar_variable_parentesis,
            linea,
        )
        # Patrón complementario para variables tipo `(({L_{e}}{D})_{codo}):`
        linea_mod = re.sub(
            r"^\s*\(\s*\(\s*(\{?[a-zA-Z0-9_\\]+\}?\s*\{?[a-zA-Z0-9_\\]+\}?)\s*\)\s*(_(?:\{[^{}]*\}|[a-zA-Z0-9]+))\s*\)(\s*:)",
            lambda m: f"\\(\\left(\\frac{{{m.group(1).replace('{','').replace('}',' ')}}}{{...}}\\right){m.group(2)}\\){m.group(3)}" if False else _reemplazar_variable_parentesis(m),
            linea_mod,
        )

        # Conversión adicional: envolver cualquier variable con subíndice
        # (ej. (j_k), (Q_k), (d_{int, k})) en notación matemática \\( ... \\)
        # para que KaTeX renderice el subíndice en lugar de mostrar 'j_k' literal.
        def _envolver_var_subindice(m: re.Match) -> str:
            var = m.group(1)
            if "_" in var or "{" in var or "\\" in var:
                # Preservar los paréntesis literales: (j_k) -> \\((j_k)\\)
                return f"\\({m.group(0)}\\)"
            return m.group(0)

        linea_mod = re.sub(
            r"\(\s*([a-zA-Z][a-zA-Z0-9_\\{}]*(?:_[a-zA-Z0-9_\\{}]+)*)\s*\)",
            _envolver_var_subindice,
            linea_mod,
        )

        resultado.append(linea_mod)
        i += 1

    return "\n".join(resultado), avisos


# ============================================================================
#  2. EXTRACCIÓN Y BLINDAJE DE FÓRMULAS (SSOT ÚNICO)
# ============================================================================

# Expresiones regulares estrictas de delimitadores matemáticos
_RE_DISPLAY_FORMULA = re.compile(
    r"\\\[([\s\S]+?)\\\]|"
    r"\$\$([\s\S]+?)\$\$|"
    r"(\\begin\{(?:equation|align|aligned|gather|cases|matrix|pmatrix|bmatrix)\*?\}[\s\S]+?\\end\{(?:equation|align|aligned|gather|cases|matrix|pmatrix|bmatrix)\*?\})",
    re.S,
)

_RE_INLINE_FORMULA = re.compile(
    r"\\\((.+?)\\\)|"
    r"(?<!\\)\$(?!\s)(.+?)(?<!\s)(?<!\\)\$",
    re.S,
)


def extraer_y_proteger_formulas(texto: str) -> tuple[str, list[dict[str, Any]]]:
    """Extrae todas las fórmulas del documento y las reemplaza por marcadores seguros.

    Los marcadores tienen el formato:
      - Display: `@@FORMULA_DISPLAY_0000@@`
      - Inline:  `@@FORMULA_INLINE_0000@@`

    Las fórmulas dentro de bloques de código (``` ... ``` o ` ... `) NO se extraen.
    """
    formulas: list[dict[str, Any]] = []

    # Proteger primero bloques de código
    partes_codigo: list[tuple[int, int]] = []
    for m in _RE_BLOQUE_CODIGO.finditer(texto):
        partes_codigo.append((m.start(), m.end()))

    def esta_en_codigo(inicio: int, fin: int) -> bool:
        return any(c_ini <= inicio and fin <= c_fin for c_ini, c_fin in partes_codigo)

    # 1. Extraer fórmulas display
    tablero = texto
    offset = 0

    def _sustituir_display(m: re.Match) -> str:
        nonlocal offset
        idx = len(formulas)
        cuerpo = m.group(1) or m.group(2) or m.group(3) or ""
        cuerpo_limpio = cuerpo.strip()
        # Reparar sintaxis interna si tiene imperfecciones
        cuerpo_reparado = reparar_sintaxis_latex_interna(cuerpo_limpio)
        token = f"@@FORMULA_DISPLAY_{idx:04d}@@"
        formulas.append({
            "idx": idx,
            "token": token,
            "cuerpo": cuerpo_reparado,
            "cuerpo_original": cuerpo_limpio,
            "es_display": True,
            "original": m.group(0),
        })
        return token

    # Proceso en trozos no-código para display
    trozos_display: list[str] = []
    cursor = 0
    for c_ini, c_fin in partes_codigo:
        if cursor < c_ini:
            subtexto = tablero[cursor:c_ini]
            trozos_display.append(_RE_DISPLAY_FORMULA.sub(_sustituir_display, subtexto))
        trozos_display.append(tablero[c_ini:c_fin])
        cursor = c_fin
    if cursor < len(tablero):
        trozos_display.append(_RE_DISPLAY_FORMULA.sub(_sustituir_display, tablero[cursor:]))
    tablero = "".join(trozos_display)

    # Actualizar posiciones de código en el nuevo texto
    partes_codigo_inline: list[tuple[int, int]] = []
    for m in _RE_BLOQUE_CODIGO.finditer(tablero):
        partes_codigo_inline.append((m.start(), m.end()))

    def _sustituir_inline(m: re.Match) -> str:
        cuerpo = m.group(1) if m.group(1) is not None else m.group(2)
        if not cuerpo or not cuerpo.strip():
            return m.group(0)
        cuerpo_limpio = cuerpo.strip()
        # Evitar capturar cantidades monetarias como "$100" o "$50.50 USD"
        if re.match(r"^\d+(?:[.,]\d+)?(?:\s*[a-zA-Z]+)?$", cuerpo_limpio):
            return m.group(0)

        cuerpo_reparado = reparar_sintaxis_latex_interna(cuerpo_limpio)
        idx = len(formulas)
        token = f"@@FORMULA_INLINE_{idx:04d}@@"
        formulas.append({
            "idx": idx,
            "token": token,
            "cuerpo": cuerpo_reparado,
            "cuerpo_original": cuerpo_limpio,
            "es_display": False,
            "original": m.group(0),
        })
        return token

    trozos_inline: list[str] = []
    cursor = 0
    for c_ini, c_fin in partes_codigo_inline:
        if cursor < c_ini:
            subtexto = tablero[cursor:c_ini]
            trozos_inline.append(_RE_INLINE_FORMULA.sub(_sustituir_inline, subtexto))
        trozos_inline.append(tablero[c_ini:c_fin])
        cursor = c_fin
    if cursor < len(tablero):
        trozos_inline.append(_RE_INLINE_FORMULA.sub(_sustituir_inline, tablero[cursor:]))
    tablero = "".join(trozos_inline)

    return tablero, formulas


# ============================================================================
#  3. TRADUCCIÓN DETERMINISTA DE LATEX A UNICODE (PARA EXCEL .XLSX)
# ============================================================================

def _resolver_fracciones_balanceadas(tex: str) -> str:
    """Resuelve recursivamente \\frac{num}{den} a (num) / (den) con llaves balanceadas."""
    pos = 0
    t = tex
    while True:
        idx = t.find(r"\frac", pos)
        if idx == -1:
            break
        i1 = t.find("{", idx + 5)
        if i1 == -1:
            pos = idx + 5
            continue
        prof = 0
        fin1 = -1
        for k in range(i1, len(t)):
            if t[k] == "{":
                prof += 1
            elif t[k] == "}":
                prof -= 1
                if prof == 0:
                    fin1 = k
                    break
        if fin1 == -1:
            pos = idx + 5
            continue
        num = t[i1 + 1:fin1]

        i2 = t.find("{", fin1 + 1)
        if i2 == -1 or t[fin1 + 1:i2].strip():
            pos = idx + 5
            continue
        prof = 0
        fin2 = -1
        for k in range(i2, len(t)):
            if t[k] == "{":
                prof += 1
            elif t[k] == "}":
                prof -= 1
                if prof == 0:
                    fin2 = k
                    break
        if fin2 == -1:
            pos = idx + 5
            continue
        den = t[i2 + 1:fin2]

        num_res = _resolver_fracciones_balanceadas(num)
        den_res = _resolver_fracciones_balanceadas(den)
        reemplazo = f"({num_res}) / ({den_res})"
        t = t[:idx] + reemplazo + t[fin2 + 1:]
        pos = idx + len(reemplazo)
    return t


def latex_a_unicode(latex: str) -> str:
    """Traduce fórmulas LaTeX a texto legible con notación Unicode matemática para Excel.

    Convierte:
      - Subíndices: `V_{real}` -> `Vᵣₑₐₗ`, `Q_{m3s}` -> `Q₍ₘ₃ₛ₎`
      - Superíndices: `x^{1.75}` -> `x¹˙⁷⁵` o `x^(1.75)`
      - Fracciones: `\\frac{A}{B}` -> `(A) / (B)`
      - Comandos: `\\cdot` -> `·`, `\\sqrt{x}` -> `√(x)`, `\\pi` -> `π`
    """
    if not latex:
        return ""

    t = latex.strip()

    # Quitar envolturas de modo display / inline si vinieron incluidas
    for pref in (r"\[", r"$$", r"\(", "$"):
        if t.startswith(pref):
            t = t[len(pref):]
    for suf in (r"\]", r"$$", r"\)", "$"):
        if t.endswith(suf):
            t = t[:-len(suf)]
    t = t.strip()

    # Reemplazar comandos de formato de texto: \text{...}, \mathrm{...}
    t = re.sub(r"\\(?:text|mathrm|mathbf|textit|textbf)\s*\{([^{}]*)\}", r"\1", t)

    # 1. Reemplazar \left y \right ANTES de comandos que contengan 'le' (\le)
    t = re.sub(r"\\left\s*([(\[{|])", r"\1", t)
    t = re.sub(r"\\right\s*([)\]}|])", r"\1", t)
    t = t.replace(r"\left.", "").replace(r"\right.", "")

    # 2. Reemplazar símbolos TeX conocidos
    for cmd, char in _SIMBOLOS_TEX.items():
        # Usar re.sub con frontera para comandos cortos como \le, \ge, \pm
        if len(cmd) <= 4:
            t = re.sub(re.escape(cmd) + r"(?![a-zA-Z])", char, t)
        else:
            t = t.replace(cmd, char)

    # 3. Reemplazar raíces cuadradas: \sqrt{x} -> √(x)
    t = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"√(\1)", t)

    # 4. Resolver fracciones balanceadas recursivas
    t = _resolver_fracciones_balanceadas(t)

    # Reemplazar subíndices: `_{...}` o `_x`
    def _subindice_repl(m: re.Match) -> str:
        contenido = m.group(1) or m.group(2)
        resultado = []
        todos_mapeados = True
        for ch in contenido:
            if ch in _MAPA_SUBINDICES:
                resultado.append(_MAPA_SUBINDICES[ch])
            else:
                todos_mapeados = False
                resultado.append(ch)
        if todos_mapeados:
            return "".join(resultado)
        return f"₍{''.join(resultado)}₎"

    t = re.sub(r"_\{([^{}]+)\}|_([a-zA-Z0-9])", _subindice_repl, t)

    # Reemplazar superíndices: `^{...}` o `^x`
    def _superindice_repl(m: re.Match) -> str:
        contenido = m.group(1) or m.group(2)
        resultado = []
        todos_mapeados = True
        for ch in contenido:
            if ch in _MAPA_SUPERINDICES:
                resultado.append(_MAPA_SUPERINDICES[ch])
            elif ch == ".":
                resultado.append("˙")
            else:
                todos_mapeados = False
                resultado.append(ch)
        if todos_mapeados:
            return "".join(resultado)
        return f"^({contenido})"

    t = re.sub(r"\^\{([^{}]+)\}|\^([a-zA-Z0-9])", _superindice_repl, t)

    # Limpiar dobles espacios y barras invertidas residuales
    t = re.sub(r"\s+", " ", t)
    t = t.replace(r"\,", " ").replace(r"\;", " ").replace(r"\!", "")
    # Si quedó alguna barra invertida con comando no mapeado (ej: \foo), remover la barra
    t = re.sub(r"\\([a-zA-Z]+)", r"\1", t)
    # Limpiar llaves residuales
    t = t.replace("{", "").replace("}", "")

    return t.strip()


# ============================================================================
#  4. RE-INSERCIÓN DE FÓRMULAS SEGÚN DESTINO (HTML, DOCX, MARKDOWN)
# ============================================================================

def reinsertar_formulas_html(html_renderizado: str, formulas: list[dict[str, Any]]) -> str:
    """Inserta las fórmulas en el HTML renderizado para KaTeX."""
    import html as _html
    res = html_renderizado
    for f in formulas:
        token = f["token"]
        cuerpo = f["cuerpo"]
        es_disp = f["es_display"]
        escapado = _html.escape(cuerpo, quote=True)
        if es_disp:
            # Reemplazar envoltorio de párrafo si markdown-it lo envolvió en <p>
            res = res.replace(
                f"<p>{token}</p>",
                f'<div class="mformula display" data-latex="{escapado}"></div>',
            )
            res = res.replace(
                token,
                f'<div class="mformula display" data-latex="{escapado}"></div>',
            )
        else:
            res = res.replace(
                token,
                f'<span class="mformula inline" data-latex="{escapado}"></span>',
            )
    return res


def reinsertar_formulas_pandoc(texto_markdown: str, formulas: list[dict[str, Any]]) -> str:
    """Reinserta las fórmulas con delimitadores limpios para Pandoc (Word y PDF)."""
    res = texto_markdown
    for f in formulas:
        token = f["token"]
        cuerpo = f["cuerpo"]
        es_disp = f["es_display"]
        if es_disp:
            # Líneas en blanco antes y después para asegurar párrafo independiente en Word
            res = res.replace(token, f"\n\n\\[\n{cuerpo}\n\\]\n\n")
        else:
            res = res.replace(token, f"\\({cuerpo}\\)")
    return res


# ============================================================================
#  5. VALIDACIÓN DE FÓRMULAS
# ============================================================================

def validar_formulas_documento(
    formulas: list[dict[str, Any]],
    texto_completo: str | None = None,
) -> dict[str, Any]:
    """Valida la sintaxis básica de cada fórmula y reporta inconsistencias con línea del fuente."""
    total = len(formulas)
    correctas = 0
    con_error = 0
    detalles_error: list[dict[str, Any]] = []

    pos_busqueda = 0
    for f in formulas:
        cuerpo = f["cuerpo"]
        cuerpo_orig = f.get("cuerpo_original", cuerpo)
        orig = f.get("original", "")
        errores: list[str] = []

        # Determinar número de línea en el texto original si se proporcionó
        linea = 1
        if texto_completo and orig:
            pos = texto_completo.find(orig, pos_busqueda)
            if pos != -1:
                linea = texto_completo[:pos].count("\n") + 1
                pos_busqueda = pos + len(orig)
            else:
                pos_cualquiera = texto_completo.find(orig)
                if pos_cualquiera != -1:
                    linea = texto_completo[:pos_cualquiera].count("\n") + 1

        # 1. Balance de llaves
        if cuerpo.count("{") != cuerpo.count("}"):
            errores.append(f"Llaves desbalanceadas: {cuerpo.count('{')} apertura(s) vs {cuerpo.count('}')} cierre(s).")

        # 2. Balance de \left y \right
        num_left = len(re.findall(r"\\left\b", cuerpo))
        num_right = len(re.findall(r"\\right\b", cuerpo))
        if num_left != num_right:
            errores.append(f"Delimitadores '\\left' y '\\right' desbalanceados ({num_left} left vs {num_right} right).")

        # 3. Subíndices o superíndices vacíos: `_{}` o `^{}`
        if re.search(r"[_^]\{\s*\}", cuerpo):
            errores.append("Subíndice o superíndice vacío ('_{}' o '^{}').")

        # 4. Delimitador de cierre corrupto como `\right$)`
        if re.search(r"\\right\s*\$", cuerpo_orig):
            errores.append("Delimitador corrupto '\\right$' en lugar de '\\right)'.")

        # 5. Subíndice sin guion bajo en el fuente (ej. {d{int}} o n{tees})
        if re.search(r"\{[a-zA-Z]+\{[a-zA-Z0-9_]+\}\}", cuerpo_orig) or re.search(r"[a-zA-Z]\{[a-zA-Z0-9_]{2,}\}", cuerpo_orig):
            errores.append("Posible subíndice sin guion bajo en el fuente (ej. '{d{int}}' o 'n{tees}').")

        if errores:
            con_error += 1
            detalles_error.append({
                "indice": f["idx"] + 1,
                "token": f["token"],
                "tipo": "Display" if f["es_display"] else "Inline",
                "linea": linea,
                "cuerpo": cuerpo,
                "cuerpo_original": cuerpo_orig,
                "errores": errores,
            })
        else:
            correctas += 1

    return {
        "total": total,
        "correctas": correctas,
        "con_error": con_error,
        "detalles": detalles_error,
    }

