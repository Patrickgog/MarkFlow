# -*- coding: utf-8 -*-
"""Servicio de conversión Markdown ↔ JSON ProseMirror (editor visual Docs).

Puente entre el SSOT de texto (Markdown) y el documento estructurado del
editor visual (`#editor-docs`). Este módulo es la **referencia canónica** del
conversor; el frontend (`static/js/editor_docs.js`) mantiene un espejo en JS
del serializador `doc → Markdown` para rendimiento en vivo (las reglas deben
permanecer idénticas en ambos lados).

Reglas de conversión:
- ``softbreak`` → espacio simple (texto corrido); ``hardbreak`` → ``\\`` + ``\\n``.
- Tablas → nodos nativos ``table/table_row/table_header/table_cell`` (GFM);
  la primera fila siempre es cabecera (única representación del formato);
  la alineación por columna (``:--:``/``---:``) se conserva en ``attrs.alignment``.
- Listas: sangría de 2 espacios por nivel; ``ordered`` conserva ``start``.
- Marcas: ``strong`` ``**`` · ``em`` ``*`` · ``s`` ``~~`` · ``code`` `` ` ``
  (exclusiva: ignora las demás marcas del run) · ``link`` ``[t](href "title")``.
- Control de cambios (v1.5.0): CriticMarkup ``{++insertado++}`` → marca ``ins``
  y ``{--borrado--}`` → marca ``del`` (regla inline propia registrada antes de
  ``text``); el contenido es texto plano (las marcas anidadas se aplanan).
- Idempotencia estructural: ``md → doc → md → doc`` produce ``doc1 == doc2``
  (verificada en pruebas).

Limitaciones documentadas (v1.5.0):
- El texto no se escapa: ``*``/``_``/``#`` a inicio de línea pueden
  reinterpretarse al re-parsear (misma regla en JS y Python).
- Dos listas del mismo tipo adyacentes se representan como una sola en
  Markdown (estructura unrepresentable del formato).
- Tablas: la primera fila siempre se exporta como cabecera (GFM no representa
  tablas sin cabecera); el contenido multilínea de celda se aplana con
  espacios; los pipes dentro de ``code`` en celdas no son idempotentes.
- CriticMarkup: el contenido de ``{++…++}``/``{--…--}`` no anida otras marcas
  (si el usuario combina negrita dentro de un cambio, la marca interna se
  aplana a literal al serializar — misma regla en JS y Python).
"""

from __future__ import annotations

import json
import re
from typing import Any

from markdown_it import MarkdownIt

# Parser GFM-ish: CommonMark + tablas + tachado (strikethrough) + CriticMarkup.
_MD = MarkdownIt("commonmark").enable("table").enable("strikethrough")

_MARCAS_ENVOLTURA = {
    "strong": ("**", "**"),
    "em": ("*", "*"),
    "s": ("~~", "~~"),
    "ins": ("{++", "++}"),
    "del": ("{--", "--}"),
}
_ORDEN_MARCAS = ("ins", "del", "strong", "em", "s")


# ---------------------------------------------------------------------------
# Regla inline CriticMarkup (compartida con el round-trip .docx)
# ---------------------------------------------------------------------------
_RE_CRITIC = re.compile(r"\{(\+\+|--)(.*?)\1\}")


def _regla_criticmarkup(state, silent) -> bool:
    """Regla inline de markdown-it: ``{++texto++}`` → ins, ``{--texto--}`` → del.

    Escanea el marcador Crítico más cercano desde ``state.pos``; el texto
    previo se emite literal. El contenido es un token ``text`` plano (sin
    anidar marcas — limitación documentada).
    """
    m = _RE_CRITIC.search(state.src, state.pos)
    if m is None:
        return False  # sin marcador: la regla `text` por defecto continúa
    if m.start() > state.pos:
        if not silent:
            state.pending += state.src[state.pos:m.start()]
        state.pos = m.start()
        return True
    tipo = "ins" if m.group(1) == "++" else "del"
    if not silent:
        state.push(f"{tipo}_open", tipo, 1)
        if m.group(2):
            tok = state.push("text", "", 0)
            tok.content = m.group(2)
        state.push(f"{tipo}_close", tipo, -1)
    state.pos = m.end()
    return True


_MD.inline.ruler.before("text", "criticmarkup", _regla_criticmarkup)


def parser_con_criticmarkup() -> MarkdownIt:
    """Parser canónico con la regla CriticMarkup (lo usa también el round-trip)."""
    md = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    md.inline.ruler.before("text", "criticmarkup", _regla_criticmarkup)
    return md


# ---------------------------------------------------------------------------
# Markdown → JSON ProseMirror
# ---------------------------------------------------------------------------
def md_a_doc(texto: str) -> dict[str, Any]:
    """Convierte Markdown en un documento JSON ProseMirror (esquema Docs).

    Entrada vacía o colapsada → doc con un párrafo vacío (contenido válido
    para el esquema ``block+`` del editor).
    """
    tokens = _MD.parse(texto or "")
    nodos, _consumido = _rango_bloques(tokens, 0, len(tokens), cierre=None)
    if not nodos:
        nodos = [{"type": "paragraph"}]
    return {"type": "doc", "content": nodos}


def _rango_bloques(
    tokens: list, desde: int, hasta: int, cierre: str | None
) -> tuple[list[dict], int]:
    """Convierte ``tokens[desde:hasta]`` en nodos de bloque.

    Si ``cierre`` no es ``None``, se detiene al encontrar el token de cierre
    indicado (no lo consume) y devuelve ``(nodos, indice_del_cierre)``.
    """
    nodos: list[dict] = []
    i = desde
    while i < hasta:
        tok = tokens[i]
        tipo = tok.type
        if cierre and tipo == cierre:
            return nodos, i
        if tipo == "paragraph_open":
            inline = tokens[i + 1] if i + 1 < hasta and tokens[i + 1].type == "inline" else None
            hijos = _inline_a_nodos(inline.children) if inline else []
            if hijos:
                nodos.append({"type": "paragraph", "content": hijos})
            i += 3 if inline else 1
        elif tipo == "heading_open":
            nivel = int(tok.tag[1]) if len(tok.tag) == 2 and tok.tag[1].isdigit() else 1
            inline = tokens[i + 1] if i + 1 < hasta and tokens[i + 1].type == "inline" else None
            nodos.append({
                "type": "heading",
                "attrs": {"level": nivel},
                "content": _inline_a_nodos(inline.children) if inline else [],
            })
            i += 3 if inline else 1
        elif tipo == "blockquote_open":
            hijos, i2 = _rango_bloques(tokens, i + 1, hasta, "blockquote_close")
            nodos.append({"type": "blockquote", "content": hijos})
            i = i2 + 1
        elif tipo in ("bullet_list_open", "ordered_list_open"):
            cerrar = tipo.replace("_open", "_close")
            hijos, i2 = _rango_bloques(tokens, i + 1, hasta, cerrar)
            nodo: dict = {"type": "bullet_list" if tipo.startswith("bullet") else "ordered_list",
                          "content": hijos}
            if tipo.startswith("ordered"):
                nodo["attrs"] = {"start": _entero(tok.attrs.get("start"), 1)}
            nodos.append(nodo)
            i = i2 + 1
        elif tipo == "list_item_open":
            hijos, i2 = _rango_bloques(tokens, i + 1, hasta, "list_item_close")
            nodos.append({"type": "list_item", "content": hijos})
            i = i2 + 1
        elif tipo == "fence":
            nodos.append(_nodo_code_block((tok.info or "").strip() or None, tok.content))
            i += 1
        elif tipo == "code_block":
            nodos.append(_nodo_code_block(None, tok.content))
            i += 1
        elif tipo == "hr":
            nodos.append({"type": "horizontal_rule"})
            i += 1
        elif tipo == "table_open":
            tabla, i2 = _tabla(tokens, i, hasta)
            nodos.append(tabla)
            i = i2
        elif tipo == "html_block":
            # HTML en bloque se conserva como texto literal (documentado).
            if tok.content.strip():
                nodos.append({"type": "paragraph", "content": [_texto(tok.content)]})
            i += 1
        else:
            i += 1  # *_close y tokens residuales
    return nodos, hasta


def _nodo_code_block(params: str | None, contenido: str) -> dict:
    texto = contenido.rstrip("\n")
    nodo: dict = {"type": "code_block", "attrs": {"params": params}}
    if texto:
        nodo["content"] = [_texto(texto)]
    return nodo


def _entero(valor: Any, defecto: int) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def _alineacion_de_style(style: Any) -> str:
    """Extrae la alineación de columna del estilo GFM (``text-align:center``)."""
    if not style:
        return ""
    m = re.search(r"text-align:\s*(center|right|left)", str(style))
    return m.group(1) if m else ""


def _tabla(tokens: list, desde: int, hasta: int) -> tuple[dict, int]:
    """Convierte una tabla GFM en nodos ``table/table_row/table_header/table_cell``."""
    filas: list[list[tuple[str, str, list[dict]]]] = []
    i = desde + 1
    while i < hasta:
        tok = tokens[i]
        if tok.type == "table_close":
            i += 1
            break
        if tok.type == "tr_open":
            celdas: list[tuple[str, str, list[dict]]] = []
            i += 1
            while i < hasta and tokens[i].type != "tr_close":
                if tokens[i].type in ("th_open", "td_open"):
                    tipo_celda = "table_header" if tokens[i].type == "th_open" else "table_cell"
                    alineacion = _alineacion_de_style(tokens[i].attrs.get("style"))
                    inline = tokens[i + 1] if i + 1 < hasta and tokens[i + 1].type == "inline" else None
                    contenido = _inline_a_nodos(inline.children) if inline else []
                    celdas.append((tipo_celda, alineacion, contenido))
                    i += 2 if inline else 1
                else:
                    i += 1
            filas.append(celdas)
            i += 1  # tr_close
        else:
            i += 1
    filas_nodos: list[dict] = []
    for celdas in filas:
        hijos: list[dict] = []
        for tipo_celda, alineacion, contenido in celdas:
            nodo_celda: dict = {"type": tipo_celda}
            if alineacion:
                nodo_celda["attrs"] = {"alignment": alineacion}
            nodo_celda["content"] = (
                [{"type": "paragraph", "content": contenido}] if contenido
                else [{"type": "paragraph"}]
            )
            hijos.append(nodo_celda)
        filas_nodos.append({"type": "table_row", "content": hijos})
    return {"type": "table", "content": filas_nodos}, i


def _inline_a_nodos(hijos: list | None) -> list[dict]:
    nodos: list[dict] = []
    _recorrer_inline(hijos or [], {}, nodos)
    return nodos


def _recorrer_inline(hijos: list, marcas: dict, salida: list[dict]) -> None:
    """Acumula texto corrido y emite nodos con las marcas activas."""
    buffer = ""

    def volcar() -> None:
        nonlocal buffer
        if buffer:
            nodo: dict = {"type": "text", "text": buffer}
            activas = list(marcas.values())
            if activas:
                nodo["marks"] = activas
            salida.append(nodo)
            buffer = ""

    for tok in hijos:
        tipo = tok.type
        if tipo == "text":
            buffer += tok.content
        elif tipo == "softbreak":
            buffer += " "
        elif tipo == "hardbreak":
            volcar()
            nodo = {"type": "hard_break"}
            activas = list(marcas.values())
            if activas:
                nodo["marks"] = activas
            salida.append(nodo)
        elif tipo == "code_inline":
            volcar()
            salida.append({"type": "text", "text": tok.content, "marks": [{"type": "code"}]})
        elif tipo == "image":
            volcar()
            alt = _texto_plano(tok.children or [])
            salida.append({
                "type": "image",
                "attrs": {
                    "src": tok.attrs.get("src", ""),
                    "alt": alt,
                    "title": tok.attrs.get("title"),
                },
            })
        elif tipo.endswith("_open") or tipo.endswith("_close"):
            base = tipo.rsplit("_", 1)[0]
            if base in ("strong", "em", "s", "link", "ins", "del"):
                volcar()
                if tipo.endswith("_open"):
                    if base == "link":
                        marcas[base] = {
                            "type": "link",
                            "attrs": {
                                "href": tok.attrs.get("href", ""),
                                "title": tok.attrs.get("title"),
                            },
                        }
                    else:
                        marcas[base] = {"type": base}
                else:
                    marcas.pop(base, None)
            else:
                buffer += getattr(tok, "content", "") or ""
        else:
            # html_inline, math_inline, etc.: contenido literal.
            buffer += getattr(tok, "content", "") or ""
    volcar()


def _texto_plano(hijos: list | None) -> str:
    partes: list[str] = []
    for tok in hijos or []:
        if tok.children:
            partes.append(_texto_plano(tok.children))
        elif tok.content:
            partes.append(tok.content)
    return "".join(partes)


def _texto(contenido: str) -> dict:
    return {"type": "text", "text": contenido}


# ---------------------------------------------------------------------------
# JSON ProseMirror → Markdown (referencia canónica)
# ---------------------------------------------------------------------------
def limpiar_referencias_imagenes_huerfanas(texto: str) -> str:
    """Descarta definiciones de imágenes [img-N]: data:... que no tengan referencias en el texto."""
    if not texto:
        return texto
    patron_ref = re.compile(r"!\[.*?\]\[([^\]]+)\]")
    etiquetas_activas = set(patron_ref.findall(texto))

    lineas = texto.splitlines(keepends=True)
    patron_def = re.compile(r"^\s*\[([^\]]+)\]:\s*(data:image/[^\s]+|\S+)")

    lineas_filtradas: list[str] = []
    for linea in lineas:
        m = patron_def.match(linea)
        if m:
            etiqueta = m.group(1).strip()
            if m.group(2).startswith("data:image/") or etiqueta.startswith("img-"):
                if etiqueta not in etiquetas_activas:
                    continue
        lineas_filtradas.append(linea)

    return "".join(lineas_filtradas)


def doc_a_md(doc: dict) -> str:
    """Serializa un documento JSON ProseMirror a Markdown."""
    if not isinstance(doc, dict):
        raise ValueError("El documento debe ser un objeto JSON.")
    lineas: list[str] = []
    imagenes_base64: list[tuple[str, str]] = []
    for nodo in doc.get("content") or []:
        if lineas:
            lineas.append("")
        lineas.extend(_bloque_a_md(nodo, 0, imagenes_base64))
    if imagenes_base64:
        lineas.append("")
        for tag, src in imagenes_base64:
            lineas.append(f"[{tag}]: {src}")
    if not lineas:
        return ""
    salida = "\n".join(lineas).strip("\n") + "\n"
    return limpiar_referencias_imagenes_huerfanas(salida)


def _bloque_a_md(nodo: dict, nivel_lista: int, imagenes_base64: list[tuple[str, str]] | None = None) -> list[str]:
    tipo = nodo.get("type", "")
    contenido = nodo.get("content") or []
    if tipo == "paragraph":
        texto = _inline_a_md(contenido, imagenes_base64)
        return [texto] if texto else []
    if tipo == "heading":
        nivel = _entero((nodo.get("attrs") or {}).get("level"), 1)
        texto = _inline_a_md(contenido, imagenes_base64)
        encabezado = "#" * max(1, min(6, nivel))
        return [f"{encabezado} {texto}".rstrip()]
    if tipo == "code_block":
        params = (nodo.get("attrs") or {}).get("params") or ""
        cuerpo = "".join(hijo.get("text", "") for hijo in contenido)
        m_cerco = re.match(r"^`{3,}\s*([a-zA-Z0-9_-]+)?[^\n]*\n([\s\S]*?)\n?`{3,}\s*$", cuerpo.strip())
        if m_cerco:
            if not params and m_cerco.group(1):
                params = m_cerco.group(1)
            cuerpo = m_cerco.group(2)
        if not params and re.match(
            r"^(?:graph\s+(?:TD|TB|BT|RL|LR)|flowchart\s+(?:TD|TB|BT|RL|LR)|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram|gantt|pie|mindmap|timeline|gitGraph)\b",
            cuerpo.strip(),
            re.IGNORECASE,
        ):
            params = "mermaid"
        lineas = cuerpo.split("\n") if cuerpo else [""]
        return [f"```{params}"] + lineas + ["```"]
    if tipo == "horizontal_rule":
        return ["---"]
    if tipo == "blockquote":
        internas: list[str] = []
        for hijo in contenido:
            if internas:
                internas.append("")
            internas.extend(_bloque_a_md(hijo, nivel_lista, imagenes_base64))
        return [("> " + linea) if linea else ">" for linea in internas] or [">"]
    if tipo in ("bullet_list", "ordered_list"):
        return _lista_a_md(nodo, nivel_lista, imagenes_base64)
    if tipo == "table":
        return _tabla_a_md(nodo, imagenes_base64)
    # Nodo de bloque desconocido: serializa sus hijos (defensivo).
    internas = []
    for hijo in contenido:
        internas.extend(_bloque_a_md(hijo, nivel_lista, imagenes_base64))
    return internas


_SEPARADOR_ALINEACION = {"": "---", "left": ":---", "center": ":---:", "right": "---:"}


def _celda_a_texto(celda: dict, imagenes_base64: list[tuple[str, str]] | None = None) -> str:
    """Aplana el contenido de una celda a una línea (GFM) escapando pipes."""
    partes: list[str] = []
    for hijo in celda.get("content") or []:
        if hijo.get("type") == "paragraph":
            partes.append(_inline_a_md(hijo.get("content") or [], imagenes_base64))
        else:
            partes.extend(_bloque_a_md(hijo, 0, imagenes_base64))
    plano = " ".join(p.strip() for p in partes if p.strip())
    plano = plano.replace("\\\n", " ").replace("\n", " ")
    return plano.replace("|", "\\|")


def _tabla_a_md(nodo: dict, imagenes_base64: list[tuple[str, str]] | None = None) -> list[str]:
    filas = nodo.get("content") or []
    if not filas:
        return ["| |", "|---|"]
    columnas = max((len(fila.get("content") or []) for fila in filas), default=1) or 1

    def textos(fila: dict) -> list[str]:
        celdas = [(_celda_a_texto(c, imagenes_base64) or " ") for c in (fila.get("content") or [])]
        return celdas + [" "] * (columnas - len(celdas))

    def alineaciones(fila: dict) -> list[str]:
        al = [((c.get("attrs") or {}).get("alignment") or "") for c in (fila.get("content") or [])]
        return al + [""] * (columnas - len(al))

    lineas = ["| " + " | ".join(textos(filas[0])) + " |"]
    separadores = [_SEPARADOR_ALINEACION.get(a, "---") for a in alineaciones(filas[0])]
    lineas.append("|" + "|".join(separadores) + "|")
    for fila in filas[1:]:
        lineas.append("| " + " | ".join(textos(fila)) + " |")
    return lineas


def _lista_a_md(nodo: dict, nivel_lista: int, imagenes_base64: list[tuple[str, str]] | None = None) -> list[str]:
    lineas: list[str] = []
    viñeta_numerada = nodo.get("type") == "ordered_list"
    contador = _entero((nodo.get("attrs") or {}).get("start"), 1)
    sangria = "  " * nivel_lista
    for item in nodo.get("content") or []:
        marca = f"{contador}. " if viñeta_numerada else "- "
        if viñeta_numerada:
            contador += 1
        primera = True
        for hijo in item.get("content") or []:
            if hijo.get("type") in ("bullet_list", "ordered_list"):
                lineas.extend(_lista_a_md(hijo, nivel_lista + 1, imagenes_base64))
                continue
            for k, linea in enumerate(_bloque_a_md(hijo, nivel_lista + 1, imagenes_base64)):
                if primera:
                    lineas.append(f"{sangria}{marca}{linea}".rstrip())
                    primera = False
                else:
                    lineas.append(("  " * (nivel_lista + 1) + linea) if linea else "")
        if primera:  # ítem vacío
            lineas.append(f"{sangria}{marca}".rstrip())
    return lineas


def _inline_a_md(nodos: list[dict], imagenes_base64: list[tuple[str, str]] | None = None) -> str:
    """Agrupa corridas de texto por firma de marcas y aplica envolturas."""
    segmentos: list[dict] = []
    for nodo in nodos:
        tipo = nodo.get("type", "")
        marcas = [m for m in (nodo.get("marks") or []) if isinstance(m, dict) and m.get("type")]
        if tipo == "text":
            segmentos.append({"texto": nodo.get("text", ""), "marcas": marcas})
        elif tipo == "hard_break":
            segmentos.append({"texto": "\\\n", "marcas": marcas})
        elif tipo == "image":
            attrs = nodo.get("attrs") or {}
            alt = str(attrs.get("alt") or "").replace("\n", " ")
            src = str(attrs.get("src") or "")
            titulo = attrs.get("title")
            sufijo = f' "{titulo}"' if titulo else ""
            if src.startswith("data:image/") and imagenes_base64 is not None:
                tag = f"img-{len(imagenes_base64) + 1}"
                imagenes_base64.append((tag, src))
                segmentos.append({"texto": f"![{alt}][{tag}]", "marcas": []})
            else:
                segmentos.append({"texto": f"![{alt}]({src}{sufijo})", "marcas": []})
    if not segmentos:
        return ""
    salida: list[str] = []
    i = 0
    while i < len(segmentos):
        firma = json.dumps([m.get("type") for m in segmentos[i]["marcas"]], sort_keys=True)
        j = i
        partes: list[str] = []
        while j < len(segmentos) and json.dumps(
            [m.get("type") for m in segmentos[j]["marcas"]], sort_keys=True
        ) == firma:
            partes.append(segmentos[j]["texto"])
            j += 1
        salida.append(_envolver("".join(partes), segmentos[i]["marcas"]))
        i = j
    return "".join(salida)


def _envolver(texto: str, marcas: list[dict]) -> str:
    tipos = {m.get("type") for m in marcas}
    if not texto or not tipos:
        return texto
    if "code" in tipos:
        return _envolver_code(texto)
    cuerpo = texto
    prefijo = ""
    sufijo = ""
    for nombre in _ORDEN_MARCAS:
        if nombre in tipos:
            abre, cierra = _MARCAS_ENVOLTURA[nombre]
            prefijo += abre
            sufijo = cierra + sufijo
    envuelto = f"{prefijo}{cuerpo}{sufijo}"
    if "link" in tipos:
        enlace = next(m for m in marcas if m.get("type") == "link")
        attrs = enlace.get("attrs") or {}
        href = str(attrs.get("href") or "")
        titulo = attrs.get("title")
        destino = f"{href} \"{titulo}\"" if titulo else href
        envuelto = f"[{envuelto}]({destino})"
    return envuelto


def _envolver_code(texto: str) -> str:
    comillas = "`"
    while comillas in texto:
        comillas += "`"
    relleno = " " if (texto.startswith("`") or texto.endswith("`")) else ""
    return f"{comillas}{relleno}{texto}{relleno}{comillas}"
