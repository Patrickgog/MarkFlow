"""Saneador Markdown de asistentes de IA (módulo puro, autocontenido).

Porta el núcleo probado y calibrado con documentos reales de ingeniería:
  1. Máquina de estados de '$'/'$$' mal emparejados + soldadura de fórmulas
     troceadas + rescate de ecuaciones sin delimitar + deTeX de prosa.
  2. Re-derivación de estructura: pares de espacios pegados se convierten en
     saltos de párrafo, las vinetas tras cierres se separan y los títulos
     con doble espacio se normalizan (tablas y código quedan intactos).

Garantía de idempotencia: `saneanar(saneanar(x)) == saneanar(x)`, de modo que
el botón «Formatear ahora» puede pulsarse sin riesgo (los spans `\\( \\)` /
`\\[ \\]` ya saneados se dejan intactos).

API pública:
    saneanar(texto) -> (texto_saneado, formulas_envueltas, avisos)
"""

from __future__ import annotations

import re

from motor.formulas import rescatar_formulas_defectuosas_fuente

# ---------------------------------------------------------------------------
#  Saneador de matemática (calibrado con los .md reales del proyecto origen)
# ---------------------------------------------------------------------------
# Los .md de asistentes de IA traen '$' y '$$' con cierres dobles y '$' huérfanos
# (p. ej. `($4.694 $ m$^3/$h$$)`, `$$Sustituyendo...$$$$`). El parser canónico
# empareja como puede y traga prosa, encabezados e incluso tablas dentro de un
# «bloque de fórmulas». El saneador separa lo que SÍ es TeX de lo que es prosa
# disfrazada: la prosa vuelve al texto y con ella las tablas y títulos atrapados.

_TEX_TEXTO = re.compile(
    r"\\(?:text|textbf|textit|textrm|textup|textnormal|mathrm|mathbf)\s*\{[^{}]*\}"
)
_TEX_COMANDO = re.compile(r"\\[A-Za-z]+\*?")
_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{4,}")
_PALABRA_MEDIA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3,}")
_SEP_INICIO = ")] ,.;:\t"
_SUBINDICE = r"[_^]\{(?:\{[^{}]*\}|[^{}])*\}"
# D1 (plan 0004): forma compilada para neutralizar etiquetas de sub/superíndice
# en `_es_prosa` (identificadores como `_{entrada}` no son palabras castellanas).
_ETIQUETA_SUBSUP = re.compile(_SUBINDICE)
_FIRMA_TEX = re.compile(
    r"(?:[A-Za-z][A-Za-z0-9]*(?:" + _SUBINDICE + r")?|\\[A-Za-z]+)\s*=")

# D2 (plan 0004): `|` prohibido en el hueco SOLDABLE — el separador de celda
# de una tabla jamás pertenece a una fórmula (los 3 cuerpos `$\eta_x$` de la
# cabecera "3.4 Rendimientos unitarios" se fundían en un solo span que
# cruzaba las celdas y desfallecía la tabla en HTML/DOCX).
_HUECO_PROHIBIDO = re.compile(r"[:,;()\[\]]|\.(?!\d)|\n|\|")
_INICIO_EQ = re.compile(
    r"(?<![A-Za-z0-9_\\])"
    r"[A-Za-z][A-Za-z0-9]*"
    r"(?:" + _SUBINDICE + r")?"
    r"\s*=\s*"
    r"(?:\\[A-Za-z]+|[A-Za-z][A-Za-z0-9]*(?:" + _SUBINDICE + r")?)")

_DOLAR_CUALQUIERA = re.compile(r"\$")

# contador de fórmulas ya envueltas en la entrada (para paridad estable)
_ABIERTO_MATE = re.compile(r"\\\(|\\\[")
# C9 — envolturas híbridas del autor (`\[ \( cuerpo \] \)` y su espejo
# `\(\[ cuerpo \) \]`): el abridor display/inline va seguido del parásito
# del otro modo y el cierre llega cruzado. Provienen del documento de
# origen del asistente de IA y atraviesan intactas el saneador si no se
# reparan (los bloques display salen contaminados de `\( … \)` parásitos
# y no renderizan en HTML/DOCX).
# C9b — delimitadores DUPLICADOS del mismo modo (opener/cierre pegados a
# su gemelo) y cierre con barra de escape malformada (`\\)`), p. ej.
# `\(\(ADT = … \\))`; la entrada de Informe 1 trae ambas variantes.
_HIBRIDA_DISPLAY = re.compile(r"\\\[\s*\\\((.*?)\\\]\s*\\\)", re.S)
_HIBRIDA_INLINE = re.compile(r"\\\(\s*\\\[(.*?)\\\)\s*\\\]", re.S)
_DOBLE_ABIERTO = re.compile(r"(\\\(|\\\[)(?:\s*\1)+")
# solo cierres TAMBIÉN con barra (`\)` `\)`) — un paréntesis desnudo de
# prosa legítima después del cierre (`\(x\))`) no se toca
_DOBLE_CIERRE = re.compile(r"(\\\))(?:\s*\\\1\\?)+")
# C9b: cuatro caracteres malformados `\` `)` `)` con DOBLE barra previa
# (`\\))`) — cerrado del autor con barra de escape que estorba; los
# cierres dobles legítimos (`\\)`, tres caracteres) no casa este patrón
_CERRO_MALFORMADO = re.compile(r"\\\\\)\)+")
# C9c — híbrido display con abridor inline NO adyacente al `\[`: el
# parásito `\(` llega después de texto del cuerpo y el cierre llega
# cruzado `\] \)` (Hallado en Informe 1: `\[Δ \(H = … \] \)`).
# SÓLO una línea: un span que cruce párrafos arrancaría displays
# legítimos con su sección «Donde:» completa (5 devorados en Informe 1).
_HIBRIDA_LADIA_DISPLAY = re.compile(r"\\\[([^\n]*?)\\\]\s*\\\)", re.S)
# C9d — subspan parado dentro del display: `\[ \(…\) \]` (el inline
# completo vive dentro del display; Informe 2 marca 6 casos) y su variante
# malformada `\[ \(\(…\)) \]`: abridor inline duplicado y cierre con
# paréntesis parásito ANTES del cierre display (Informe 2: bloque Q_max).
_HIBRIDA_DISPLAY_NEST = re.compile(r"\\\[\s*\\\((.*?)\\\)\s*\\\]", re.S)
_HIBRIDA_NEST_CERRO = re.compile(r"\\\[\s*(?:\\\()+\s*(.*?\\\))\)+\s*\\\]", re.S)

# C9e — estilos MEZCLADOS: el autor mezcla delimitadores de doble barra
# `\\( …\\)` con simples `\(` y vuelca el balance (Informe 2). La
# canónica del proyecto es el estilo simple; delimitadores legítimos
# nunca llevan barra doble (`\\left(` tiene letras intermedias, no casa).
_NORMALIZAR_DOBLES = re.compile(r"\\\\([()\[\]])")


def _reparar_hibridas(texto: str) -> tuple[str, int]:
    """Caso C9: normaliza las envolturas híbridas a fórmulas limpias.

    `\\[ \\( cuerpo \\] \\)` → `\\[\\n cuerpo \\n\\]` (display puro) y
    `\\( \\[ cuerpo \\) \\]` → `\\( cuerpo \\)` (inline puro). El cuerpo se
    despoja de delimitadores parásitos pegados a los bordes y los cierres
    cruzados se descartan. Se ejecuta ANTES de la normalización'$'/'$$'
    para que los bloques display lleguen íntegros a la máquina de estados.
    Idempotente: tras el pase no queda ningún par cruzado (segunda pasada
    == sin cambios).
    """
    reparadas = len(_HIBRIDA_DISPLAY.findall(texto))
    reparadas += len(_HIBRIDA_INLINE.findall(texto))
    reparadas += len(_HIBRIDA_LADIA_DISPLAY.findall(texto))
    reparadas += len(_HIBRIDA_DISPLAY_NEST.findall(texto))
    reparadas += len(_HIBRIDA_NEST_CERRO.findall(texto))
    duplicados = len(_DOBLE_ABIERTO.findall(texto))
    duplicados += len(_DOBLE_CIERRE.findall(texto))
    dobles = len(_NORMALIZAR_DOBLES.findall(texto))
    if not reparadas and not duplicados and not dobles:
        return texto, 0

    # C9e primero: el estilo con doble barra no es canónico y mezclado
    # con el simple rompe el balance de pares (y la conversión OMML)
    texto = _NORMALIZAR_DOBLES.sub(r"\\\1", texto)

    def _desparasitar(cuerpo: str) -> str:
        """Quita delimitadores residuales pegados al cuerpo del híbrido."""
        limpio = cuerpo.strip()
        # parásitos iniciales: `\(`, `\[` repetidos en el borde
        while limpio.startswith("\\(") or limpio.startswith("\\["):
            limpio = limpio[2:].lstrip()
        while limpio.endswith("\\)") or limpio.endswith("\\]"):
            limpio = limpio[:-2].rstrip()
        return limpio

    def _a_display(m: re.Match) -> str:
        cuerpo = _desparasitar(m.group(1))
        if not cuerpo:
            return ""
        return "\\[\n" + cuerpo + "\n\\]"

    def _a_inline(m: re.Match) -> str:
        cuerpo = _desparasitar(m.group(1))
        if not cuerpo:
            return ""
        return "\\(" + cuerpo + "\\)"

    def _a_display_ladia(m: re.Match) -> str:
        # el cuerpo puede arrastrar el abridor interno `\(`/cierre `\)`
        cuerpo = m.group(1).replace("\\(", "").replace("\\)", "")
        cuerpo = _desparasitar(cuerpo)
        if not cuerpo:
            return ""
        return "\\[\n" + cuerpo + "\n\\]"

    texto = _HIBRIDA_DISPLAY.sub(_a_display, texto)
    texto = _HIBRIDA_INLINE.sub(_a_inline, texto)
    texto = _HIBRIDA_LADIA_DISPLAY.sub(_a_display_ladia, texto)
    texto = _HIBRIDA_DISPLAY_NEST.sub(_a_display, texto)
    texto = _HIBRIDA_NEST_CERRO.sub(_a_display, texto)
    # C9b: apertura/cierre duplicados del mismo modo -> par único.
    # ALCANCE DE LÍNEA con abridor duplicado: así nunca se devora un
    # cierre legítimo del autor (`\\)`) seguido de un paréntesis de prosa,
    # como en `* **Carga (\(C_{org}\)):* (m^3/día \\))` del Informe 2.
    if duplicados:
        lineas = texto.split("\n")
        for k, linea in enumerate(lineas):
            if _DOBLE_ABIERTO.search(linea):
                # abridores gemelos pegados (`\(\(`) colapsan al primero:
                # dos abridores contiguos jamás son fórmula legítima
                linea = _DOBLE_ABIERTO.sub(r"\1", linea)
                lineas[k] = _DOBLE_CIERRE.sub(
                    r"\1", _CERRO_MALFORMADO.sub(r"\\)", linea)
                )
        texto = "\n".join(lineas)
    return texto, reparadas + duplicados

_CODIGO_LINEA = re.compile(r"`[^`\n]*`")
_BLOQUE_CODIGO = re.compile(r"```[\s\S]*?(?:```|\Z)")
_TROZO_CODIGO = re.compile(
    r"```[\s\S]*?(?:```|\Z)|`+[^`\n]*`+|`[^`\n]*`|[^`]+")

_TEXTEX_EN_PROSA = re.compile(
    r"\\(?:text|textbf|textit|textrm|textup|textnormal|mathrm|mathbf)\s*\{([^{}]*)\}"
)
_SIMBOLO_TEX = {
    "cdot": "·", "times": "×", "approx": "≈", "leq": "≤", "geq": "≥",
    "le": "≤", "ge": "≥", "Delta": "Δ", "delta": "δ", "pi": "π",
    "sigma": "σ", "rho": "ρ", "sqrt": "√", "infty": "∞",
}


def _es_tex(markup: str) -> bool:
    """True si un fragmento lleva marcadores que solo existen en TeX."""
    return bool(_TEX_COMANDO.search(markup) or "_" in markup or "^" in markup)


def _es_prosa(tex: str) -> bool:
    """True si un candidato de fórmula es en realidad prosa del autor.

    Reglas calibradas, en este orden (nunca adivinadas):
    (1) arrastra >= 3 palabras castellanas de >= 4 letras una vez retirada la
        sintaxis TeX -> los bloques gigantes con prosa, títulos y tablas;
    (2) empieza por ')' del paréntesis de prosa anterior y detrás no hay firma
        de ecuación (`D = ...`);
    (3) lleva comandos TeX o sub/superíndices -> es matemática de verdad
        (`\\text{ L/s}`, `\\pi`, `\\Delta h`, `Q_{d}`);
    (4) es puro simbolismo sin letras ni cifras (` - `).
    Todo lo demás se considera matemática.
    """
    limpio = tex.strip()
    if not limpio:
        return True

    material = _TEX_TEXTO.sub(" ", limpio)
    # D1 (plan 0004): las etiquetas de sub/superíndice son tokens matemáticos,
    # NO palabras castellanas (`\dot{M}_{entrada}` produjo 4 "palabras" ficticias
    # — entrada/salida/removida/transformada — y cancelaba el par `$$ … $$`
    # como si fuera prosa, dejando la ecuación sin delimitadores y con
    # `\dot` detexizado). Se neutralizan ANTES de contar palabras.
    material = _ETIQUETA_SUBSUP.sub(" ", material)
    material = _TEX_COMANDO.sub(" ", material)
    if len(_PALABRA.findall(material)) >= 3:
        return True

    if limpio[0] in ")]" and not _FIRMA_TEX.match(limpio.lstrip(_SEP_INICIO)):
        return True

    if _es_tex(limpio):
        return False

    if not re.search(r"\w", limpio):
        return True

    return False


def _quitar_dollars(texto: str) -> str:
    """Retira '$' y '$$' huérfanos del autor dejando ileso el código."""
    salida: list[str] = []
    cerca = False              # ``` ... ```
    linea = False              # ` ... `
    i, n = 0, len(texto)
    while i < n:
        if not linea and texto.startswith("```", i):
            cerca = not cerca
            salida.append("```")
            i += 3
            continue
        if not cerca and texto[i] == "`":
            linea = not linea
            salida.append(texto[i])
            i += 1
            continue
        if cerca or linea:
            salida.append(texto[i])
            i += 1
            continue
        if texto[i] == "$":
            i += 1
            continue
        salida.append(texto[i])
        i += 1
    return "".join(salida)


def _dolares(texto: str) -> list[tuple[int, bool]]:
    """Posiciones de cada '$' (o '$$' contiguo) fuera de bloques de código."""
    ocultos = sorted(
        list((m.start(), m.end()) for m in _BLOQUE_CODIGO.finditer(texto))
        + list((m.start(), m.end()) for m in _CODIGO_LINEA.finditer(texto))
    )
    salida: list[tuple[int, bool]] = []
    i, n = 0, len(texto)
    while i < n:
        if any(a <= i < b for a, b in ocultos):
            i += 1
            continue
        if texto[i] == "$":
            doble = i + 1 < n and texto[i + 1] == "$"
            salida.append((i, doble))
            i += 2 if doble else 1
            continue
        i += 1
    return salida


def _emparejar_dolares(texto: str) -> list[tuple[int, int, bool, str]]:
    """Empareja '$'/'$$' con una máquina de estados de modo matemático.

    Un solo abridor activo: cada dólar siguiente prueba de cierre; si su
    interior es prosa del autor se CANCELA el abridor (vuelve a texto plano
    y el dólar probante pasa a ser el nuevo abridor). La regla «cierre más
    cercano» producía pares superpuestos que devoraban el '$' real que
    cerraba la fórmula.
    """
    dolares = _dolares(texto)
    fragmentos: list[tuple[int, int, bool, str]] = []
    abridor = -1

    for k, (pos, doble) in enumerate(dolares):
        if abridor < 0:
            abridor = k
            continue
        pos_a, doble_a = dolares[abridor]
        gancho = 2 if doble_a else 1
        interior = texto[pos_a + gancho:pos]
        if not interior or interior[0] in ")]" or _es_prosa(interior):
            abridor = k
            continue
        fragmentos.append((
            pos_a, pos + (2 if doble else 1),
            doble_a and doble,
            interior,
        ))
        abridor = -1
    return fragmentos


def _absorbible(hueco: str, cuerpo_prev: str, cuerpo: str) -> str:
    """Prefijo del hueco soldable a la fórmula anterior ('' si no lo hay).

    El '$$' del autor cierra su región; solo el texto ANTES del primer dólar
    pertenece a la fórmula (`^2}` en `^2}$$ - $V...`, ` m` en ` m$$,`). Sin
    dólar ninguno el hueco entero es soldable (` y `, ` = \\frac{4 \\cdot `).
    El límite de tamaño rige sobre el prefijo, no sobre el hueco completo.
    """
    if not hueco:
        return ""
    m = _DOLAR_CUALQUIERA.search(hueco)
    prefijo = hueco[:m.start()] if m else hueco
    if not prefijo or "\n" in prefijo or len(prefijo) > 24:
        return ""
    if _HUECO_PROHIBIDO.search(prefijo):
        return ""
    if _PALABRA_MEDIA.findall(prefijo) and not _es_tex(prefijo):
        return ""
    if _es_prosa(cuerpo_prev + prefijo + cuerpo):
        return ""
    return prefijo


def _fusionar(
    fragmentos: list[tuple[int, int, bool, str]],
    texto: str,
) -> list[tuple[int, int, bool, str]]:
    """Une fórmulas contiguas cuyo hueco intermedio no lleva prosa.

    El autor escribe `$$$V_{\\text{real}}$ = \\frac{4 \\cdot $Q_{d}$}{...}`
    donde pretendía UNA ecuación: los pares adyacentes con hueco matemático
    se sueldan (cuerpos + hueco) en un solo `\\(...\\)`. Si el hueco arrastra
    un '$$' de cierre solo se ABSORBE el prefijo anterior a ese dólar.
    """
    soldados: list[tuple[int, int, bool, str]] = []
    for inicio, fin, es_bloque, cuerpo in fragmentos:
        if soldados:
            p_inicio, p_fin, es_bloque_prev, cuerpo_prev = soldados[-1]
            hueco = texto[p_fin:inicio]
            prefijo = _absorbible(hueco, cuerpo_prev, cuerpo)
            if prefijo:
                completo = (
                    "$$" not in hueco
                    and len(prefijo) == len(hueco)
                    and not _es_prosa(cuerpo_prev + hueco + cuerpo)
                )
                if completo:
                    soldados[-1] = (p_inicio, fin, es_bloque_prev or es_bloque,
                                    cuerpo_prev + hueco + cuerpo)
                    continue
                soldados[-1] = (p_inicio, p_fin + len(prefijo),
                                es_bloque_prev,
                                cuerpo_prev + prefijo)
        soldados.append((inicio, fin, es_bloque, cuerpo))

    if soldados:                          # pie: absorber la cola tras la última
        p_inicio, p_fin, es_bloque_prev, cuerpo_prev = soldados[-1]
        resta = texto[p_fin:]
        m = re.search(r"\$|\n", resta)
        pieza = resta[:m.start()] if m else resta
        if pieza and len(pieza) <= 24 and "\n" not in pieza:
            if not _HUECO_PROHIBIDO.search(pieza) and (
                not _PALABRA_MEDIA.findall(pieza) or _es_tex(pieza)
            ):
                if not _es_prosa(cuerpo_prev + pieza):
                    soldados[-1] = (p_inicio, p_fin + len(pieza),
                                    es_bloque_prev, cuerpo_prev + pieza)
    return soldados


def _limpiar_tex(tex: str) -> str:
    """Quita el espacio interior insignificante y escapa '%' para LaTeX."""
    return re.sub(r"(?<!\\)%", r"\\%", tex.strip())


def _fin_cadena(tex: str, inicio: int) -> int:
    """Frontera de prosa de una cadena TeX (fuera de llaves balanceadas).

    D2 (plan 0004): una `|` con espacio adyacente es separador de celda de
    tabla — la cadena de rescate jamás la cruza (sin espacio a los lados puede
    ser valor absoluto legítimo, `|x|`, y se respeta).
    """
    profundidad = 0
    i, n = inicio, len(tex)
    while i < n:
        c = tex[i]
        if c == "{":
            profundidad += 1
        elif c == "}":
            profundidad = max(0, profundidad - 1)
        elif profundidad == 0 and (c == "\n" or c == ")" or tex.startswith("  ", i)):
            return i
        elif (
            profundidad == 0
            and c == "|"
            and (i == 0 or tex[i - 1] == " " or tex[i + 1:i + 2] == " ")
        ):
            return i
        i += 1
    return n


def _detex_prosiano(trozo: str) -> str:
    """Deja legible el TeX sin delimitar que resta en la prosa.

    pandoc interpreta `\\text{ m.c.a.}` como TeX crudo y se come el contenido;
    convertido a texto (`m.c.a.`) el Word conserva la cifra y su unidad.
    """
    trozo = _TEXTEX_EN_PROSA.sub(r"\1", trozo)
    return re.sub(
        r"\\([A-Za-z]+)\\?",
        lambda m: _SIMBOLO_TEX.get(m.group(1), ""),
        trozo,
    )


# ---------------------------------------------------------------------------
#  Rescate de cadenas de ecuación sin delimitar
# ---------------------------------------------------------------------------

# pares de fórmula YA envueltas (inline o display, con cierre a pares):
# se respetan verbatim y marcan el terreno prohibido para el rescate
_PAR_EXISTENTE = re.compile(r"\\\(.*?\\\)|\\\[.*?\\\]", re.S)


def _solo_cadenas(t: str, rescatadas: list[int] | None = None) -> str:
    """Rescata las cadenas de ecuación de un trozo libre de código.

    Los spans `\\( \\)` / `\\[ \\]` ya saneados se copian verbatim
    (garantía de idempotencia: un segundo pase no re-envuelve) y ARRASTRAN
    su alcance: el buscador de ecuaciones nunca entra dentro de un span
    ni lo atraviesa al cortar la cadena (causa raíz de los pares cruzados
    `\\[ \\( … \\] \\)` detectados en Informe 1, caso C9).
    `rescatadas[0]` acumula los envoltorios emitidos (QA de paridad: sin
    ellos, una cadena rescatada no se cuenta en la pasada 1 y el total
    difiere del de la pasada 2).
    """
    salida: list[str] = []
    i, n = 0, len(t)
    ocultos = [(m.start(), m.end()) for m in _PAR_EXISTENTE.finditer(t)]

    def _ocultado(pos: int) -> bool:
        return any(a <= pos < b for a, b in ocultos)

    def _pasar_hasta(limite: int) -> None:
        """Emite [i … limite) con spans verbatim y sólo los huecos detexados.

        La prosa entre fórmulas envueltas puede arrastrar OTROS spans que
        nunca producen candidato `_INICIO_EQ` (`\\\\(Q_e\\\\)`): un salto directo
        a una fórmula lejana los detexizaría (frac, cdot… muertos en
        pasada 2). El avance respeta cada span verbatim.
        """
        nonlocal i
        while i < limite:
            par = _PAR_EXISTENTE.match(t, i)
            if par:
                salida.append(par.group(0))
                i = par.end()
                continue
            # el span verbatim más próximo aún DENTRO del rango
            sig = next((a for a, b in ocultos if i <= a < limite), None)
            destino = sig if sig is not None else limite
            salida.append(_detex_prosiano(t[i:destino]))
            i = destino

    while i < n:
        # guarda de idempotencia: fórmula ya envuelta -> copiar intacta
        par_envuelto = _PAR_EXISTENTE.match(t, i)
        if par_envuelto:
            salida.append(par_envuelto.group(0))
            i = par_envuelto.end()
            continue
        m = _INICIO_EQ.search(t, i)
        # la ecuación candidata cae dentro de un span ya envuelto ->
        # avanzar el cursor HASTA el fin de ese span (verbatímenes)
        while m and _ocultado(m.start()):
            a_span, b_span = next(
                (a, b) for a, b in ocultos if a <= m.start() < b
            )
            _pasar_hasta(a_span)                     # prosa ANTES del span
            salida.append(t[a_span:b_span])          # span verbatim
            i = b_span
            m = _INICIO_EQ.search(t, i)
        if not m:
            _pasar_hasta(n)
            break
        fin = _fin_cadena(t, m.start())
        # la cadena jamás atraviesa un span ya envuelto delante
        limite = [
            a for a, b in ocultos if m.start() <= a < fin
        ]
        if limite:
            fin = min(limite)
        if fin <= m.start():
            salida.append(t[m.start():m.end()])
            i = m.end()
            continue
        # delimitador abierto sin cierre delante (entrada a medio corregir):
        # no envolver, para no soldar un parasesita al abridor caprichoso
        prefijo = t[i:m.start()]
        abiertos = len(re.findall(r"\\\(|\\\[", prefijo))
        cerrados = len(re.findall(r"\\\)|\\\]", prefijo))
        _pasar_hasta(m.start())                  # prosa con spans verbatim
        if fin <= m.start() or abiertos > cerrados:
            salida.append(t[m.start():m.end()])
            i = m.end()
            continue
        cadena = t[m.start():fin]
        # la vineta del autor deja operadores colgantes (`escritura: P = ... - `):
        # un operador al final no continúa la fórmula, vuelve a la prosa
        pica = len(cadena.rstrip())
        while pica > 0 and (cadena[pica - 1].isspace() or cadena[pica - 1] in "+-="):
            pica -= 1
        # solo es fórmula si lleva marcadores TeX (`\\`, `_`, `^`);
        # `D = diametro` en prosa no se envuelve
        if _es_tex(cadena[:pica]):
            salida.append(
                "\\(" + _limpiar_tex(_desparasitar_cuerpo(cadena[:pica])) + "\\)"
            )
            if rescatadas is not None:
                rescatadas[0] += 1
            i = m.start() + pica
        else:
            salida.append(t[m.start():fin])
            i = fin
    return "".join(salida)


def _rescatar_cadenas(prosa: str, rescatadas: list[int] | None = None) -> str:
    """Envuelve como fórmula las cadenas `X = \\comando{...}` de la prosa.

    Los bloques de prosa del autor arrastran ecuaciones sin delimitador
    ('$$...D = \\sqrt{...}$$'); pandoc se las come como TeX crudo y el Word
    pierde el contenido. Se detecta cada cadena (con guarda de código en
    línea y fenced) y se emite como `\\(...\\)`; lo que queda de prosa pasa
    por _detex_prosiano. `rescatadas[0]` acumula los envoltorios emitidos.
    """
    return _TROZO_CODIGO.sub(
        lambda m: (t if (t := m.group(0)).startswith("`")
                   else _solo_cadenas(t, rescatadas)),
        prosa,
    )


def _desparasitar_cuerpo(tex: str) -> str:
    """Vacía delimitadores parásitos pegados a los bordes de un cuerpo.

    Los fragmentos mal emparejados del autor arrastran abridores/cierres
    ajenos (`\\( H = … \\]`): si se envuelven así salen pares cruzados
    (C9). El desparasitado es de bordes solamente: una fórmula legítima
    con paréntesis reales (`\\left( x \\right)`) no casa por las letras
    intermedias.
    """
    limpio = tex.strip()
    while limpio.startswith("\\(") or limpio.startswith("\\["):
        limpio = limpio[2:].lstrip()
    while limpio.endswith("\\)") or limpio.endswith("\\]"):
        limpio = limpio[:-2].rstrip()
    return limpio


def _cuerpa(tex: str, es_bloque: bool) -> list[tuple[str, str]]:
    """Parte una candidata de fórmula en trozos ('texto' | 'mate', contenido).

    'mate' viene ya con el envoltorio '\\(...\\)' / '\\[...\\]'; 'texto' es
    prosa del autor que debe ir al entregable sin matemática ninguna.
    """
    limpio = _desparasitar_cuerpo(tex.strip().replace("$", ""))
    if not limpio:
        return []

    abierto = "\\[" if es_bloque else "\\("
    cerrado = "\\]" if es_bloque else "\\)"

    # ')' huérfano del autor seguido de la prosa precedente, con TeX detrás:
    # p. ej. `): D = \\sqrt{...}` -> prosa `): ` + fórmula `D = \\sqrt{...}`
    prefijo = limpio[: len(limpio) - len(limpio.lstrip(_SEP_INICIO))]
    resto = limpio[len(prefijo):].strip()
    if prefijo and _es_tex(resto):
        return [("texto", prefijo),
                ("mate", abierto + _limpiar_tex(resto) + cerrado)]

    if _es_prosa(limpio):
        return [("texto", limpio)]

    return [("mate", abierto + _limpiar_tex(limpio) + cerrado)]


def _normalizar_matematica(texto: str) -> tuple[str, int, list[str]]:
    """Reescribe los delimitadores de fórmulas a la forma canónica `\\( \\)`.

    Devuelve (texto saneado, fórmulas envueltas, avisos).
    """
    fragmentos = _fusionar(_emparejar_dolares(texto), texto)

    salida: list[str] = []
    cursor = 0
    reconvertidas = 0
    rescates: list[int] = [0]      # fórmulas envueltas por el rescate
    prosa_rescatada = 0
    avisos: list[str] = []

    for inicio, fin, es_bloque, contenido in fragmentos:
        salida.append(_rescatar_cadenas(
            _quitar_dollars(texto[cursor:inicio]), rescates))
        for tipo, cuerpo in _cuerpa(contenido, es_bloque):
            salida.append(cuerpo)
            reconvertidas += tipo == "mate"
            prosa_rescatada += tipo == "texto"
        cursor = fin

    salida.append(_rescatar_cadenas(
        _quitar_dollars(texto[cursor:]), rescates))
    resultado = "".join(salida)
    reconvertidas += rescates[0]

    if prosa_rescatada:
        avisos.append(
            f"{prosa_rescatada} fragmento(s) delimitados con '$'/'$$' son prosa "
            "del autor, no TeX: se devolvieron al texto plano. Si son fórmulas, "
            "corrige los delimitadores en el documento de origen."
        )

    return resultado, reconvertidas, avisos


# ---------------------------------------------------------------------------
#  Re-derivación de la estructura (port del proyecto origen)
# ---------------------------------------------------------------------------

_TITULO_ESPACIO = re.compile(r"(?:(?<=^)|(?<=\s))(#{1,6})\s{2,}")
_TITULO_MEDIA = re.compile(r"#{1,6}\s")
_CODIGO_INDIVIDUAL = re.compile(r"`+[^`\n]*`+|`[^`\n]*`")
_DOBLE_ESPACIO = re.compile(r" {2,}")
_VINETA_TRAS_CIERRE = re.compile(r"\s*-\s*\\[\(\[]")
_HASTA_GUION = re.compile(r"\s*(?=-)")
_PUNTO_ANTES_FORMULA = re.compile(r"\.(?=\s*\\[\(\[])")

_SALIDA_VINETA = re.compile(r"[\)\.]\s*-\s*\\[\(\[]")


def _cortes_linea(linea: str) -> list[int]:
    """Posiciones donde la línea del autor debe reventar en nueva línea.

    Se corta antes de (1) una corrida de 2+ espacios y (2) el separador de
    vineta del autor (`: Ecuacion) - (Simbolo): Definicion`). Nunca se corta
    dentro de una fórmula `\\(...\\)` ni de un span de código.
    """
    cortes: list[int] = []
    i, n = 0, len(linea)
    en_math = None                       # '\\(' | '\\[' | None
    while i < n:
        if en_math:
            par = "\\)" if en_math == "\\(" else "\\]"
            if linea.startswith(par, i):
                en_math = None
                i += len(par)
                # `ecuacion) - \(D\): definicion`: el guion tras el cierre es
                # vineta del autor, no resta de la fórmula
                if _VINETA_TRAS_CIERRE.match(linea, i):
                    _g = _HASTA_GUION.match(linea, i)
                    cortes.append(i)
                    i += _g.end()
                continue
            i += 1
            continue
        m = _CODIGO_INDIVIDUAL.match(linea, i)
        if m:
            i = m.end()
            continue
        if linea[i] == "#" and i > 0 and linea[i - 1] != "#":
            # título del autor pisado a mitad de línea (`text. ###  Cuadro:`):
            # corrida de 2+ almohadillas seguida de espacio en el interior
            j = i
            while j < n and linea[j] == "#":
                j += 1
            if (j - i) >= 2 and j < n and linea[j].isspace():
                cortes.append(i)
        if linea.startswith("\\(", i) or linea.startswith("\\[", i):
            en_math = linea[i:i + 2]
            i += 2
            continue
        m = _DOBLE_ESPACIO.match(linea, i)
        if m:
            cortes.append(i)
            i = m.end()
            continue
        m = _PUNTO_ANTES_FORMULA.match(linea, i)
        if m:
            cortes.append(i + 1)             # después del punto
            i = m.end()
            while i < n and linea[i] == " ":
                i += 1
            continue
        m = _SALIDA_VINETA.match(linea, i)
        if m:
            cortes.append(i + 1)             # después de ')' o '.'
            i = m.end()
            continue
        i += 1
    return cortes


def _partir_parrafo(linea: str) -> list[str]:
    """Reparte una línea pegada por el autor en sus párrafos reales."""
    cortes = _cortes_linea(linea)
    if not cortes:
        return [linea] if linea.strip() else []
    partes: list[str] = []
    desde = 0
    for corte in cortes + [len(linea)]:
        trozo = linea[desde:corte].strip()
        if trozo:
            partes.append(trozo)
        desde = corte
    return partes


def _derivar_estructura(saneado: str) -> str:
    """Convierte las líneas pisadas del autor en párrafos, títulos y vinetas.

    Las tablas (líneas que inician con '|') y los bloques de código fenced
    quedan intocables.
    """
    lineas = saneado.split("\n")
    fuera: list[str] = []
    cerca = False
    for linea in lineas:
        if linea.lstrip().startswith("```"):
            cerca = not cerca
            fuera.append(linea)
            continue
        if cerca or linea.lstrip().startswith("|"):
            fuera.append(linea)          # tabla y código: intocables
            continue
        linea = _TITULO_ESPACIO.sub(r"\1 ", linea)
        fuera.append("\n\n".join(_partir_parrafo(linea)))
    return "\n".join(fuera)


def _aislar_formulas_display(texto: str) -> str:
    """Garantiza que toda fórmula display `\\[ ... \\]` quede aislada con líneas en blanco antes y después.

    Evita que las fórmulas display se fusionen con la prosa circundante o con párrafos
    de definiciones explicativas posteriores ('Donde:').
    """
    def _reemplazo(m: re.Match) -> str:
        cuerpo = m.group(1).strip()
        return f"\n\n{cuerpo}\n\n"

    res = re.sub(r"\s*(\\\[[\s\S]+?\\\])\s*", _reemplazo, texto)
    res = re.sub(r"\n{3,}", "\n\n", res)
    return res.strip()


def _aislar_vinetas_post_formula(texto: str) -> str:
    """Aísla semánticamente las viñetas y descriptores de variables ('Donde:') posteriores a una fórmula.

    Garantiza que toda viñeta (- / •) o descriptor explicativo ('Donde:') posterior a una fórmula
    quede completamente fuera de cualquier bloque de nota (> [!NOTE] / blockquote), normalizando
    además los glifos unicode '•' a viñetas estándar '- ' para su renderizado como lista real.
    """
    lineas = texto.splitlines()
    salida: list[str] = []
    en_seccion_descriptores = False
    vio_formula_reciente = False

    for linea in lineas:
        strip = linea.strip()
        if not strip:
            salida.append(linea)
            continue

        contenido = re.sub(r"^>\s?", "", strip)

        # Normalizar viñetas con glifo unicode '•' a lista estándar '- '
        if re.match(r"^[•]\s*", contenido):
            contenido = re.sub(r"^[•]\s*", "- ", contenido)

        # Si es un número de página huérfano aislado (ej. '7' o '> 7' entre la fórmula y 'Donde:')
        if re.match(r"^\d{1,4}$", contenido) and (vio_formula_reciente or en_seccion_descriptores):
            # No resetear la detección ante números de página huérfanos y desvincular de blockquote
            salida.append(contenido)
            continue

        # Detectar presencia o cierre de fórmula display
        if "\\]" in strip or "$$" in strip or "\\]" in contenido:
            vio_formula_reciente = True
            salida.append(contenido if strip.startswith(">") else linea)
            continue

        es_descriptor = (
            contenido.lower().startswith("donde:")
            or contenido.lower() == "donde"
            or bool(re.match(r"^[-*+•]\s+", contenido))
            or bool(re.match(r"^\d+[.)]\s+", contenido))
        )

        # Si la línea tiene formato de nota pero contiene 'Donde:' o viñeta:
        if strip.startswith(">") and es_descriptor:
            en_seccion_descriptores = True
            salida.append(contenido)
            continue

        if (vio_formula_reciente or en_seccion_descriptores) and es_descriptor:
            en_seccion_descriptores = True
            salida.append(contenido)
            continue

        if not es_descriptor and not strip.startswith(">"):
            en_seccion_descriptores = False
            vio_formula_reciente = False

        # Si no es nota pero contiene viñeta unicode '•', normalizar a '- '
        if re.match(r"^[ \t]*[•][ \t]+", linea):
            linea = re.sub(r"^([ \t]*)[•][ \t]+", r"\1- ", linea)

        salida.append(linea)

    return "\n".join(salida)


def desplazar_imagenes_base64_al_final(texto: str) -> tuple[str, int]:
    """Traslada todas las cadenas Base64 al final del documento Markdown como definiciones de referencia.

    En el cuerpo del Markdown se coloca únicamente el link/referencia compacto:
        ![Figura X: Descripción][figX]
    dejando el cuerpo 100% libre de miles de caracteres incomprensibles.
    Al final del documento se concentran todas las definiciones:
        [figX]: data:image/...
    """
    if not texto or "data:image/" not in texto:
        return texto, 0

    # 1. Extraer definiciones de referencias existentes al final: [ref]: data:image/...
    defs_existentes: dict[str, str] = {}
    def _guardar_def_existente(m: re.Match) -> str:
        ref_id = m.group(1).strip()
        data_uri = m.group(2).strip()
        defs_existentes[ref_id] = data_uri
        return ""

    cuerpo = re.sub(
        r'^[ \t]*\[([^\]]+)\]:\s*(data:image/[^;\s]+;base64,[^\s]+)[ \t]*$',
        _guardar_def_existente,
        texto,
        flags=re.MULTILINE,
    )
    # Limpiar encabezados de referencias previos si quedaron vacíos
    cuerpo = re.sub(r'<!--\s*(?:REFERENCIAS DE IMÁGENES|DEFINICIONES DE IMÁGENES)[^>]*-->', '', cuerpo)

    # Identificar números de figura ya existentes en el cuerpo
    nums_existentes = [int(m) for m in re.findall(r"Figura\s+(\d+)", cuerpo, flags=re.IGNORECASE)]
    siguiente_num = max(nums_existentes, default=0) + 1
    total_desplazadas = 0
    nuevas_defs: list[tuple[str, str]] = []

    def _limpiar_desc(d: str) -> str:
        d = re.sub(r"<[^>]+>", "", d).strip()
        d = re.sub(r"^Figura\s+\d+\s*:\s*", "", d, flags=re.IGNORECASE).strip()
        d = re.sub(r"\(Hacer clic para desplegar\)", "", d, flags=re.IGNORECASE).strip()
        d = d.strip(" 🖼️:*-")
        return d or "Ilustración técnica"

    # 2. Recolectar todas las imágenes en orden de aparición en el texto
    # Patrones soportados:
    patron_det = re.compile(
        r'<details\b[^>]*>(?:(?!<\/details>).)*?<img\s+[^>]*src=["\'](data:image/[^;]+;base64,[^"\']+)["\'][^>]*>.*?<\/details>',
        flags=re.DOTALL | re.IGNORECASE,
    )
    patron_fig = re.compile(
        r'<figure\b[^>]*>(?:(?!<\/figure>).)*?<img\s+[^>]*src=["\'](data:image/[^;]+;base64,[^"\']+)["\'][^>]*>.*?<\/figure>',
        flags=re.DOTALL | re.IGNORECASE,
    )
    patron_img = re.compile(
        r'<img\s+[^>]*src=["\'](data:image/[^;]+;base64,[^"\']+)["\'][^>]*\/?>',
        flags=re.IGNORECASE,
    )
    patron_md = re.compile(
        r'!\[([^\]]*)\]\((data:image/[^;]+;base64,[^\)]+)\)'
    )

    matches_crudos: list[tuple[int, int, str, str]] = []

    for m in patron_det.finditer(cuerpo):
        bloque = m.group(0)
        src = m.group(1)
        sum_m = re.search(r"<summary[^>]*>(.*?)</summary>", bloque, re.DOTALL)
        alt_m = re.search(r'alt=["\']([^"\']+)["\']', bloque)
        desc = _limpiar_desc(sum_m.group(1) if sum_m else (alt_m.group(1) if alt_m else ""))
        matches_crudos.append((m.start(), m.end(), desc, src))

    for m in patron_fig.finditer(cuerpo):
        bloque = m.group(0)
        src = m.group(1)
        cap_m = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", bloque, re.DOTALL)
        alt_m = re.search(r'alt=["\']([^"\']+)["\']', bloque)
        desc = _limpiar_desc(cap_m.group(1) if cap_m else (alt_m.group(1) if alt_m else ""))
        matches_crudos.append((m.start(), m.end(), desc, src))

    for m in patron_img.finditer(cuerpo):
        src = m.group(1)
        alt_m = re.search(r'alt=["\']([^"\']+)["\']', m.group(0))
        desc = _limpiar_desc(alt_m.group(1) if alt_m else "")
        matches_crudos.append((m.start(), m.end(), desc, src))

    for m in patron_md.finditer(cuerpo):
        alt = _limpiar_desc(m.group(1))
        src = m.group(2).strip()
        matches_crudos.append((m.start(), m.end(), alt, src))

    if not matches_crudos and not defs_existentes:
        return cuerpo, 0

    # Filtrar matches internos contenidos dentro de otros contenedores más grandes (ej. <img> dentro de <figure>)
    matches_validos: list[tuple[int, int, str, str]] = []
    for ini, fin, desc, src in matches_crudos:
        contenido = False
        for o_ini, o_fin, _, _ in matches_crudos:
            if (o_ini < ini and fin <= o_fin) or (o_ini <= ini and fin < o_fin):
                contenido = True
                break
        if not contenido:
            matches_validos.append((ini, fin, desc, src))

    # Ordenar estrictamente de arriba hacia abajo (orden de lectura natural)
    matches_validos.sort(key=lambda x: x[0])

    # Reemplazar desde el final hacia el principio para mantener estables los offsets
    total_desplazadas = len(matches_validos)
    for idx, (ini, fin, desc, src) in reversed(list(enumerate(matches_validos))):
        n = siguiente_num + idx
        ref_id = f"fig{n}"
        nuevas_defs.insert(0, (ref_id, src))
        reemplazo = f"\n\n![Figura {n}: {desc}][{ref_id}]\n\n"
        cuerpo = cuerpo[:ini] + reemplazo + cuerpo[fin:]

    # Si no se detectaron nuevas ni existían, retornar
    todas_defs = list(defs_existentes.items()) + nuevas_defs
    if not todas_defs:
        return cuerpo.strip(), 0

    # Normalizar saltos de línea al final del cuerpo
    cuerpo_limpio = cuerpo.rstrip()

    # Construir bloque de definiciones al final del Markdown
    lineas_defs = [
        "\n\n<!-- ======================================================== -->",
        "<!-- DEFINICIONES DE IMÁGENES BASE64 (REFERENCIAS AL FINAL) -->",
        "<!-- ======================================================== -->",
    ]
    # Usar dict para evitar claves duplicadas
    defs_unicas: dict[str, str] = {}
    for r_id, uri in todas_defs:
        defs_unicas[r_id] = uri

    for r_id, uri in defs_unicas.items():
        lineas_defs.append(f"[{r_id}]: {uri}")

    texto_final = cuerpo_limpio + "\n" + "\n".join(lineas_defs) + "\n"
    return texto_final, total_desplazadas


# Alias para retrocompatibilidad
encapsular_imagenes_base64 = desplazar_imagenes_base64_al_final



# ---------------------------------------------------------------------------
#  Conversor de Tablas HTML a Markdown GFM y Limpieza de Notas
# ---------------------------------------------------------------------------

_RE_TABLA_HTML = re.compile(r"<table\b[^>]*>(.*?)</table>", re.IGNORECASE | re.DOTALL)
_RE_TR = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_RE_TH_TD = re.compile(r"<(th|td)\b[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
_RE_TAG_INTERNO = re.compile(r"<[^>]+>")


def convertir_tablas_html_a_markdown(texto: str) -> str:
    """Convierte bloques <table>...</table> a sintaxis de tablas Markdown GFM.

    1. Extrae filas <tr> y celdas <th> o <td>.
    2. Sanea el texto de las celdas (eliminando tags HTML internos, preservando texto y fórmulas).
    3. Escapa caracteres pipe '|' internos no escapados.
    4. Normaliza el número de columnas y genera la fila divisoria '| :--- | :--- |'.
    """
    if not texto or "<table" not in texto.lower():
        return texto

    def _convertir_tabla(match: re.Match) -> str:
        html_tabla = match.group(1)
        filas = _RE_TR.findall(html_tabla)
        if not filas:
            return match.group(0)

        matriz: list[list[str]] = []

        for f in filas:
            celdas_match = _RE_TH_TD.findall(f)
            if not celdas_match:
                continue
            fila_texto = []
            for _, contenido in celdas_match:
                contenido_sin_br = re.sub(r"<br\s*/?>", " ", contenido, flags=re.IGNORECASE)
                texto_celda = _RE_TAG_INTERNO.sub("", contenido_sin_br)
                texto_celda = re.sub(r"(?<!\\)\|", r"\|", texto_celda)
                texto_celda = re.sub(r"\s+", " ", texto_celda).strip()
                fila_texto.append(texto_celda)
            if fila_texto:
                matriz.append(fila_texto)

        if not matriz:
            return match.group(0)

        num_cols = max(len(fila) for fila in matriz)
        if num_cols == 0:
            return match.group(0)

        for fila in matriz:
            while len(fila) < num_cols:
                fila.append("")

        lineas_md = []
        cabecera = matriz[0]
        lineas_md.append("| " + " | ".join(cabecera) + " |")
        lineas_md.append("| " + " | ".join([":---"] * num_cols) + " |")

        for fila in matriz[1:]:
            lineas_md.append("| " + " | ".join(fila) + " |")

        return "\n\n" + "\n".join(lineas_md) + "\n\n"

    return _RE_TABLA_HTML.sub(_convertir_tabla, texto)


def limpiar_etiquetas_nota_parasitas(texto: str) -> str:
    """Elimina etiquetas parásitas [!NOTE], [!NOTA], etc. tras el prefijo de cita '>'.

    Transforma:
        > [!NOTE] Texto
        > [!NOTA] Texto
    en:
        > Texto
    """
    if not texto:
        return ""
    return re.sub(
        r'^(>\s*)\[!(?:NOTE|NOTA|TIP|CONSEJO|IMPORTANT|IMPORTANTE|WARNING|ADVERTENCIA|CAUTION)\]\s*',
        r'\1',
        texto,
        flags=re.MULTILINE | re.IGNORECASE,
    )


# ---------------------------------------------------------------------------
#  API pública
# ---------------------------------------------------------------------------

def saneanar(texto: str) -> tuple[str, int, list[str]]:
    """Sanea una entrada Markdown completa (pipeline canónico).

    0. Convierte tablas HTML residuales <table> a tablas Markdown GFM y limpia etiquetas parásitas [!NOTE].
    1. Repara envolturas híbridas del autor (caso C9: `\\[ \\( … \\] \\)`).
    2. Normaliza la matemática ('$'/'$$' mal puestos -> '\\( \\)'/'\\[ \\]').
    3. Aísla fórmulas display con líneas en blanco antes y después.
    4. Aísla viñetas y definiciones descriptivas posteriores para evitar contaminación con notas.
    5. Re-deriva la estructura (párrafos, títulos y vinetas pisadas).
    6. Encapsula imágenes Base64 en bloques <details><summary> unilineales compactos.

    Devuelve (texto_saneado, formulas_totales, avisos), donde `formulas_totales`
    suma las envueltas en este pase más las ya presentes en la entrada:
    el número queda estable y comparable entre pases (QA de paridad).
    """
    texto, avisos_rescate = rescatar_formulas_defectuosas_fuente(texto)
    texto = convertir_tablas_html_a_markdown(texto)
    texto = limpiar_etiquetas_nota_parasitas(texto)
    texto, hibridas = _reparar_hibridas(texto)
    saneado, formulas, avisos = _normalizar_matematica(texto)
    avisos = avisos_rescate + avisos
    aislado = _aislar_formulas_display(saneado)
    descontaminado = _aislar_vinetas_post_formula(aislado)
    estructurado = _derivar_estructura(descontaminado)
    final, imgs_encapsuladas = encapsular_imagenes_base64(estructurado)

    previas = len(_ABIERTO_MATE.findall(texto))
    if hibridas:
        avisos.append(
            f"C9: {hibridas} envoltura(s) híbrida(s) del autor "
            "(delimitadores display e inline cruzados, p. ej. '\\[ \\( … \\] \\)') "
            "se repararon a fórmulas cerradas por pares."
        )
    if imgs_encapsuladas > 0:
        avisos.append(
            f"Se trasladaron {imgs_encapsuladas} imagen(es) Base64 al final del documento como referencias limpias [figX]."
        )
    return final, formulas + previas, avisos


def eliminar_todas_las_notas(texto: str) -> str:
    r"""Elimina globalmente los prefijos de nota o cita ('>') al inicio de las líneas.

    Aplica expresión regular multilínea ^\s*>\s? preservando párrafos normales, listas,
    bloques de código y tablas.
    """
    if not texto:
        return ""
    texto = limpiar_etiquetas_nota_parasitas(texto)
    return re.sub(r'^\s*>\s?', '', texto, flags=re.MULTILINE)
