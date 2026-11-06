"""Módulo de consolidación y renumeración jerárquica de capítulos Markdown.

Permite unir múltiples documentos Markdown como capítulos correlativos continuos
(cada documento es un capítulo: 1., 2., 3., con sus respectivos subniveles 1.1, 1.2, etc.
iniciando en hoja nueva) o en flujo continuo sin salto de página con numeración continua global.
"""

from __future__ import annotations

import re

# Expresión para detectar encabezados Markdown ATX (# Título)
_RE_ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*)$")

# Expresión para remover numeraciones existentes en títulos (ej: "1. ", "1.2 ", "Capítulo 1 - ")
_RE_NUM_PREVIA = re.compile(
    r"^(?:(?:cap[ií]tulo\s*\d+\s*[-:.]?\s*)|(?:\d+(?:\.\d+)*\s*[-:.)]?\s*)|(?:[a-zA-Z]\.\s+))",
    re.IGNORECASE,
)


def limpiar_numeracion_previa(texto: str) -> str:
    """Remueve prefijos numéricos previos evitando duplicaciones como '1. 1. Título'."""
    t = texto.strip()
    while True:
        nuevo_t = _RE_NUM_PREVIA.sub("", t).strip()
        if nuevo_t == t:
            break
        t = nuevo_t
    return t


def renumerar_documento(
    markdown_texto: str,
    indice_capitulo: int = 1,
    numero_capitulo: int | None = None,
) -> str:
    """Renumera los títulos de un documento Markdown para integrarlo como capítulo.

    Parámetros:
        markdown_texto: Texto Markdown del documento individual.
        indice_capitulo: Número entero correlativo del capítulo principal (1, 2, ...).
        numero_capitulo: Alias de indice_capitulo por conveniencia.

    Regla:
        H1 -> # {indice_capitulo}. Título
        H2 -> ## {indice_capitulo}.{sub}. Título
        H3 -> ### {indice_capitulo}.{sub}.{sub2}. Título
        H4+ -> sin número (solo se numeran H1, H2 y H3).
    """
    if numero_capitulo is not None:
        indice_capitulo = numero_capitulo

    lineas = markdown_texto.split("\n")
    salida: list[str] = []
    en_cerco_codigo = False

    h1_count = 0
    sub_idx = 0
    sub2_idx = 0

    for linea in lineas:
        linea_strip = linea.strip()
        if linea_strip.startswith("```"):
            en_cerco_codigo = not en_cerco_codigo
            salida.append(linea)
            continue

        if en_cerco_codigo:
            salida.append(linea)
            continue

        match = _RE_ENCABEZADO.match(linea)
        if match:
            hashes = match.group(1)
            nivel = len(hashes)
            texto_titulo = match.group(2).strip()

            # Limpiar cualquier numeración previa
            texto_limpio = limpiar_numeracion_previa(texto_titulo)

            if nivel == 1:
                h1_count += 1
                sub_idx = 0
                sub2_idx = 0
                if h1_count == 1:
                    nuevo_titulo = f"{hashes} {indice_capitulo}. {texto_limpio}"
                else:
                    nuevo_titulo = f"{hashes} {indice_capitulo}.{h1_count} {texto_limpio}"
            elif nivel == 2:
                sub_idx += 1
                sub2_idx = 0
                nuevo_titulo = f"{hashes} {indice_capitulo}.{sub_idx} {texto_limpio}"
            elif nivel == 3:
                sub2_idx += 1
                sec = f"{indice_capitulo}.{max(1, sub_idx)}.{sub2_idx}"
                nuevo_titulo = f"{hashes} {sec} {texto_limpio}"
            else:
                # H4 en adelante NO se numeran
                nuevo_titulo = f"{hashes} {texto_limpio}"

            salida.append(nuevo_titulo)
        else:
            salida.append(linea)

    return "\n".join(salida)


def renumerar_flujo_continuo(textos: list[str]) -> list[str]:
    """Renumera los títulos en flujo continuo global a lo largo de varios documentos."""
    h1_global = 0
    h2_global = 0
    h3_global = 0
    salida_docs: list[str] = []

    for markdown_texto in textos:
        lineas = markdown_texto.split("\n")
        salida_lineas: list[str] = []
        en_cerco_codigo = False

        for linea in lineas:
            linea_strip = linea.strip()
            if linea_strip.startswith("```"):
                en_cerco_codigo = not en_cerco_codigo
                salida_lineas.append(linea)
                continue

            if en_cerco_codigo:
                salida_lineas.append(linea)
                continue

            match = _RE_ENCABEZADO.match(linea)
            if match:
                hashes = match.group(1)
                nivel = len(hashes)
                texto_titulo = match.group(2).strip()
                texto_limpio = limpiar_numeracion_previa(texto_titulo)

                if nivel == 1:
                    h1_global += 1
                    h2_global = 0
                    h3_global = 0
                    nuevo = f"{hashes} {h1_global}. {texto_limpio}"
                elif nivel == 2:
                    h2_global += 1
                    h3_global = 0
                    nuevo = f"{hashes} {max(1, h1_global)}.{h2_global} {texto_limpio}"
                elif nivel == 3:
                    h3_global += 1
                    sec = f"{max(1, h1_global)}.{max(1, h2_global)}.{h3_global}"
                    nuevo = f"{hashes} {sec} {texto_limpio}"
                else:
                    nuevo = f"{hashes} {texto_limpio}"

                salida_lineas.append(nuevo)
            else:
                salida_lineas.append(linea)

        salida_docs.append("\n".join(salida_lineas))

    return salida_docs


def consolidar_documentos(
    documentos: list[tuple[str, str]] | list[str],
    modo_capitulos: bool = True,
    salto_entre_archivos: bool = True,
    cada_documento_es_capitulo: bool | None = None,
) -> str:
    """Consolida múltiples documentos Markdown en un único texto.

    Parámetros:
        documentos: Lista de tuplas `(nombre_archivo, texto_markdown)` o lista de `str`.
        modo_capitulos: Si es True ("Cada documento es un capítulo distinto"),
                        cada documento inicia en hoja nueva y se numera correlativamente
                        por capítulo (1., 2., ...).
                        Si es False, se unen en flujo continuo sin salto de hoja y con
                        numeración correlativa continua global de H1..H3.
        salto_entre_archivos: Si es True, inserta una directiva de salto de página
                              compatible con Word, HTML y PDF entre documentos.
        cada_documento_es_capitulo: Alias opcional de modo_capitulos.

    Retorna:
        Texto consolidado en Markdown.
    """
    if cada_documento_es_capitulo is not None:
        modo_capitulos = cada_documento_es_capitulo

    if not documentos:
        return ""

    # Normalizar documentos a tuplas (nombre, contenido)
    docs_normalizados: list[tuple[str, str]] = []
    for elem in documentos:
        if isinstance(elem, tuple) and len(elem) == 2:
            docs_normalizados.append(elem)
        elif isinstance(elem, str):
            docs_normalizados.append(("", elem))
        else:
            docs_normalizados.append(("", str(elem)))

    if len(docs_normalizados) == 1:
        return docs_normalizados[0][1]

    # Salto de página unificado (HTML, PDF y Word)
    salto_pagina = '\n\n<div style="page-break-before: always; page-break-after: always; break-after: page;"></div>\n\\newpage\n\n'

    if modo_capitulos:
        bloques: list[str] = []
        for idx, (nombre, contenido) in enumerate(docs_normalizados, start=1):
            texto = contenido.strip()
            if not texto:
                continue
            texto_procesado = renumerar_documento(texto, indice_capitulo=idx)
            bloques.append(texto_procesado)

        separador = salto_pagina if salto_entre_archivos else "\n\n\n\n"
        return separador.join(bloques)
    else:
        # Flujo continuo sin salto de hoja y con numeración continua global
        textos_crudos = [contenido.strip() for _, contenido in docs_normalizados if contenido.strip()]
        bloques_renumerados = renumerar_flujo_continuo(textos_crudos)
        # En flujo continuo, se unen sin salto de hoja
        return "\n\n\n\n".join(bloques_renumerados)
