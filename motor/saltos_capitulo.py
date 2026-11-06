"""Regla canónica única de salto de capítulo (H1-only + excepción de primera hoja).

Fase 3 (mejoras_app_11): el salto de página por capítulo se aplica EXCLUSIVAMENTE
a encabezados de nivel 1. Los H2/H3 y los separadores ``<hr>`` nunca generan salto.

Excepción de primera hoja:
    * El primer H1 nunca fuerza salto: el título general y la introducción breve
      que lo preceden comparten la Hoja 1 con él.
    * Si el documento abre con un H1 NO numerado (título general, p. ej.
      ``# MEMORIA TÉCNICA``) seguido de un H1 numerado (``# 1. ...``), ese primer
      H1 numerado también permanece en la Hoja 1 (es el primer capítulo real).
    * Desde el siguiente H1 en adelante el salto se aplica siempre.

Módulo puro y sin estado: es la única implementación que deben invocar los
motores de exportación (PDF hoy; Word/HTML si incorporan la opción equivalente).
"""

from __future__ import annotations

import re

__all__ = [
    "MARCADOR_SALTO_CAPITULO",
    "es_titulo_numerado",
    "indices_h1_con_salto",
    "inyectar_saltos_capitulo_html",
]

#: Marcador HTML neutro (altura cero) que fuerza el salto de página en Paged Media.
MARCADOR_SALTO_CAPITULO = (
    '<div class="capitulo-salto-pagina" aria-hidden="true" '
    'style="page-break-before: always !important; break-before: page !important; '
    'column-span: all !important; height: 0 !important; margin: 0 !important; '
    'padding: 0 !important; clear: both !important;"></div>'
)

_RE_NUMERADO = re.compile(
    r"^\s*(?:cap[ií]tulo\s+)?(?:\d+|[IVXLCDM]+)(?:[.)\-:]|\s)",
    re.IGNORECASE,
)
_RE_H1 = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
_RE_ETIQUETAS = re.compile(r"<[^>]+>")


def es_titulo_numerado(texto: str) -> bool:
    """Indica si un título inicia con numeración de capítulo (``1.``, ``2)``, ``IV.``, ``Capítulo 3``)."""
    return bool(_RE_NUMERADO.match(texto or ""))


def indices_h1_con_salto(titulos_h1: list[str]) -> set[int]:
    """Devuelve los índices (base 0) de los H1 que deben iniciar página nueva.

    Args:
        titulos_h1: textos planos de todos los H1 en orden de aparición.

    Returns:
        Conjunto de índices de H1 que reciben salto de página.
    """
    total = len(titulos_h1)
    if total <= 1:
        return set()
    inicio = 1
    if not es_titulo_numerado(titulos_h1[0]) and es_titulo_numerado(titulos_h1[1]):
        inicio = 2  # H1[0] = título general; H1[1] = primer capítulo en la Hoja 1
    return set(range(inicio, total))


def inyectar_saltos_capitulo_html(cuerpo_html: str) -> str:
    """Inserta el marcador de salto antes de cada H1 que deba iniciar página nueva.

    Args:
        cuerpo_html: fragmento HTML ya compilado desde Markdown.

    Returns:
        HTML con ``MARCADOR_SALTO_CAPITULO`` antepuesto a los H1 seleccionados.
    """
    coincidencias = list(_RE_H1.finditer(cuerpo_html))
    titulos = [_RE_ETIQUETAS.sub("", m.group(1)).strip() for m in coincidencias]
    con_salto = indices_h1_con_salto(titulos)
    if not con_salto:
        return cuerpo_html
    partes: list[str] = []
    cursor = 0
    for indice, m in enumerate(coincidencias):
        if indice in con_salto:
            partes.append(cuerpo_html[cursor:m.start()])
            partes.append(MARCADOR_SALTO_CAPITULO + "\n")
            cursor = m.start()
    partes.append(cuerpo_html[cursor:])
    return "".join(partes)

