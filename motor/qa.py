"""QA de los entregables: paridad de fórmulas y residuos de delimitadores.

Métricas usadas por la API y la batería de pruebas para acreditar que:
  1. El texto saneado no deja '$' huérfanos fuera de código.
  2. La cantidad de fórmulas declaradas por `saneanar` coincide con las
     envueltas efectivamente en `\\( \\)` / `\\[ \\]` en el texto final.
"""

from __future__ import annotations

import re

_CODIGO_LINEA = re.compile(r"`[^`\n]*`")
_BLOQUE_CODIGO = re.compile(r"```[\s\S]*?(?:```|\Z)")

# QA adversarial (plan 0003): los defectos que el QA v0.5.0 dejaba escapar.
_HIBRIDA_DISPLAY = re.compile(r"\\\[\s*\\\((.*?)\\\]\s*\\\)", re.S)
_HIBRIDA_INLINE = re.compile(r"\\\(\s*\\\[(.*?)\\\)\s*\\\]", re.S)
_ABRIDORES_QA: tuple[str, str] = ("\\[", "\\(")
_CIERRES_QA: dict[str, str] = {"\\[": "\\]", "\\(": "\\)"}


def _fuera_de_codigo(texto: str) -> str:
    """Texto con los bloques de código (fenced y en línea) retirados."""
    limpio = _BLOQUE_CODIGO.sub(" ", texto)
    return _CODIGO_LINEA.sub(" ", limpio)


def residuo_dolares(texto: str) -> int:
    """Cantidad de '$' fuera de bloques de código y código en línea."""
    return _fuera_de_codigo(texto).count("$")


def contar_formulas(texto: str) -> int:
    """Fórmulas envueltas: abre `\\(` más abre `\\[`."""
    return len(re.findall(r"\\\(|\\\[", texto))


def hibridas(texto: str) -> int:
    """Pares cruzados display/inline del autor (caso C9, RC1).

    Cuenta las envolturas híbridas `\\[ \\( … \\] \\)` (y espejo) que
    rompen el renderizado del HTML y del DOCX. El QA v0.5.0 las dejaba
    pasar (conteo de abridores sano con delimitadores cruzados).
    """
    limpio = _fuera_de_codigo(texto)
    return len(_HIBRIDA_DISPLAY.findall(limpio)) + len(
        _HIBRIDA_INLINE.findall(limpio)
    )


def delimitadores_huerfanos(texto: str) -> int:
    """Abridores sin cierre y cierres sin abridor (balance por pares).

    Escaneo lineal en modo matemático: cada abridor (pila) espera su
    cierre del MISMO tipo; un cierre que no casaca con la cima de la
    pila queda huérfano (cierre sin abridor o cruza de pares).
    """
    limpio = _fuera_de_codigo(texto)
    pila: list[str] = []
    huerfanos = 0
    i, n = 0, len(limpio)
    while i < n:
        dos = limpio[i:i + 2]
        if dos in _ABRIDORES_QA:
            pila.append(dos)
            i += 2
            continue
        if dos in _CIERRES_QA.values():
            if not pila or _CIERRES_QA[pila.pop()] != dos:
                huerfanos += 1
            i += 2
            continue
        i += 1
    return len(pila) + huerfanos       # abridores sin cierre + cierres sueltos


def auditar(texto_saneado: str, formulas_declaradas: int = -1) -> dict:
    """Resumen de QA adversarial del texto saneado.

    `formulas_declaradas` es el número que reportó `saneanar`; si se envía,
    se valida la paridad contra lo envuelto en el texto.
    """
    envueltas = contar_formulas(texto_saneado)
    residuo = residuo_dolares(texto_saneado)
    n_hibridas = hibridas(texto_saneado)
    n_huerfanos = delimitadores_huerfanos(texto_saneado)
    balance_ok = n_huerfanos == 0
    paridad_ok = formulas_declaradas < 0 or formulas_declaradas == envueltas
    return {
        "formulas": envueltas,
        "envueltas": envueltas,
        "declaradas": formulas_declaradas,
        "residuo_dolares": residuo,
        "hibridas": n_hibridas,
        "huerfanos": n_huerfanos,
        "balance_ok": balance_ok,
        "paridad_ok": paridad_ok,
        "ok": residuo == 0 and paridad_ok and balance_ok and n_hibridas == 0,
    }
