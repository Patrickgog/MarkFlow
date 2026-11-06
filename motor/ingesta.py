"""Lectura robusta de entradas: detección de codificación y reparación de mojibake.

Todo lo que entra a MarkFlow AI (archivos subidos o texto pegado) pasa por aquí:
se replica el enfoque probado del convertidor de escritorio, aislado como motor
puro para que sea reutilizable por la API y por las pruebas.
"""

from __future__ import annotations

import codecs
from dataclasses import dataclass, field
from pathlib import PurePosixPath, PureWindowsPath

# --- Límite de seguridad ---------------------------------------------------
MAXIMO_BYTES = 200 * 1024 * 1024        # 200 MB por archivo


# --- Whaztlist de tipos aceptados por drag & drop --------------------------
# "texto"  : se decodifica y sanea (Markdown puro)
# "binario": se guarda tal cual; su conversión llega en la fase de motores
TIPOS_ACEPTADOS: dict[str, str] = {
    ".md": "texto",
    ".markdown": "texto",
    ".txt": "texto",
    ".docx": "binario",
    ".pdf": "binario",
}

_SECUENCIAS_SOSPECHOSAS = ("Ã", "Â", "â€")


@dataclass
class InfoIngesta:
    """Metadatos de una entrada decodificada."""

    nombre: str
    tamano_bytes: int
    codificacion: str
    con_bom: bool
    mojibake_reparado: bool = False
    avisos: list[str] = field(default_factory=list)


def clasificar_tipo(nombre: str) -> str | None:
    """Devuelve 'texto' | 'binario' | None según la extensión del archivo."""
    sufijo = PurePosixPath(nombre).suffix.lower() or PureWindowsPath(nombre).suffix.lower()
    return TIPOS_ACEPTADOS.get(sufijo)


def _puntaje_mojibake(texto: str) -> int:
    """Número de secuencias típicas de UTF-8 mal decodificado presentes."""
    return sum(texto.count(marca) for marca in _SECUENCIAS_SOSPECHOSAS)


def leer_ingesta(dato: bytes, nombre: str = "entrada.txt") -> tuple[str, InfoIngesta]:
    """Decodifica bytes a texto sano y reporta cómo lo hizo.

    Estrategia (igual que el convertidor de escritorio):
      1. BOM UTF-8/UTF-16 → decodificación directa.
      2. UTF-8 estricto → válido sin reparación.
      3. Si falla → Windows-1252 (codificación por defecto del ecosistema
         Windows) y como respaldo Latin-1 con reemplazo parcial.
      4. Si el texto muestra marcas de mojibake (UTF-8 leído como Latin-1
         en origen), se intenta el round-trip inverso.
    """
    avisos: list[str] = []
    tamano = len(dato)
    con_bom = dato.startswith(codecs.BOM_UTF8)

    if dato.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        texto, codificacion = dato.decode("utf-16"), "utf-16 (con BOM)"
    else:
        if con_bom:
            dato = dato[len(codecs.BOM_UTF8):]
            codificacion = "utf-8-sig"
            texto = dato.decode("utf-8-sig")
        else:
            try:
                texto, codificacion = dato.decode("utf-8"), "utf-8"
            except UnicodeDecodeError:
                try:
                    texto, codificacion = dato.decode("cp1252"), "cp1252"
                    avisos.append(
                        "Sin BOM ni UTF-8 válido: se leyó como Windows-1252."
                    )
                except UnicodeDecodeError:
                    texto = dato.decode("latin-1", errors="replace")
                    codificacion = "latin-1"
                    avisos.append(
                        "Símbolos indecodificables reemplazados (reparación parcial)."
                    )

    reparado = False
    if not con_bom and _puntaje_mojibake(texto) >= 2:
        try:
            texto = texto.encode("latin-1").decode("utf-8")
            codificacion, reparado = "utf-8 (mojibake reparado)", True
            avisos.append("Mojibake detectado y reparado (UTF-8 leído como Latin-1).")
        except (UnicodeEncodeError, UnicodeDecodeError):
            avisos.append(
                "Mostró secuencias sospechosas de mojibake; no se pudo reparar en automático."
            )

    info = InfoIngesta(
        nombre=nombre,
        tamano_bytes=tamano,
        codificacion=codificacion,
        con_bom=con_bom,
        mojibake_reparado=reparado,
        avisos=avisos,
    )
    return texto, info
