"""Sesiones efímeras: cada sesión aísla su trabajo en `salidas/<id>/`.

Las sesiones se purgan al arrancar y al apagar el servidor, de modo que la
carpeta del proyecto quede impecable (Regla de higiene R3 de `GEMINI.md`).
"""

from __future__ import annotations

import re
import secrets
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR_SALIDAS = RAIZ / "salidas"

_ID_VALIDO = re.compile(r"^[0-9a-f]{16}$")
# letra, dígito, espacio, punto, guión — todo lo demás se sustituye
_CARACTERES_ALTOS = re.compile(r"(?u)[^\w .\-()&',#\[\]+]")


def crear_sesion() -> str:
    """Crea una sesión nueva con su carpeta de trabajo aislada."""
    identificador = secrets.token_hex(8)
    _carpeta(identificador).mkdir(parents=True, exist_ok=True)
    return identificador


def _carpeta(identificador: str) -> Path:
    """Ruta de la sesión con defensa contra path traversal."""
    if not _ID_VALIDO.match(identificador or ""):
        raise ValueError("Identificador de sesión inválido.")
    return DIR_SALIDAS / identificador


def nombre_seguro(nombre_bruto: str) -> str:
    """Normaliza el nombre de archivo del cliente (evita rutas relativas y rarezas)."""
    bruto = Path(PureWindows(nombre_bruto).name if "\\" in nombre_bruto else nombre_bruto)
    nombre = bruto.name
    limpio = _CARACTERES_ALTOS.sub("_", nombre).strip()
    return limpio or "entrada.md"


def PureWindows(nombre: str):
    """Extrae la parte final de una ruta con separadores Windows o POSIX."""
    from pathlib import PurePosixPath
    return PurePosixPath(nombre.replace("\\", "/"))


def guardar(identificador: str, nombre: str, dato: bytes) -> Path:
    """Guarda bytes en la sesión con nombre saneado y sin colisiones."""
    carpeta = _carpeta(identificador)
    base = nombre_seguro(nombre)
    destino = carpeta / base
    tallo = destino.stem
    genero = destino.suffix
    n = 1
    while destino.exists():
        destino = carpeta / f"{tallo}-{n}{genero}"
        n += 1
    destino.write_bytes(dato)
    return destino


def ruta_archivo(identificador: str, nombre: str) -> Path:
    """Ruta de un archivo de la sesión (validado, sin traversal)."""
    destino = _carpeta(identificador) / nombre_seguro(nombre)
    if not destino.is_file():
        raise FileNotFoundError(f"No existe el archivo solicitado: {nombre}")
    return destino


def limpiar_sesion(identificador: str) -> int:
    """Elimina la carpeta de la sesión; devuelve la cantidad de archivos borrados."""
    carpeta = _carpeta(identificador)
    if not carpeta.is_dir():
        return 0
    n_archivos = sum(1 for p in carpeta.rglob("*") if p.is_file())
    shutil.rmtree(carpeta)
    return n_archivos


def limpiar_todo() -> int:
    """Purga todas las sesiones previas (se llama al arranque/cierre del servidor)."""
    if not DIR_SALIDAS.is_dir():
        DIR_SALIDAS.mkdir(exist_ok=True)
        return 0
    borrados = 0
    for hijo in DIR_SALIDAS.iterdir():
        if hijo.is_dir():
            borrados += limpiar_sesion(hijo.name)
    return borrados
