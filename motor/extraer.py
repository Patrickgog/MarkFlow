"""Motor de extracción: .docx → Markdown (pandoc).

Los DOCX de ingeniería llegan con ecuaciones OMML; pandoc las reescribe como
delimitadores `$`/`$$`, que el saneador (`motor.sanear`) normaliza después.
Docx sin pandoc disponible -> ErrorMotor (la API responde 503 con aviso
honroso en la tarjeta del documento).
"""

from __future__ import annotations

from pathlib import Path
import subprocess

from motor.a_docx import ErrorMotor, ruta_pandoc


def docx_a_markdown(dato: bytes) -> tuple[str, list[str]]:
    """Extrae el contenido de un .docx como Markdown con fórmulas `$`/`$$` e imágenes Base64 autocontenidas.

    Devuelve (markdown, avisos). Requiere texto saneable al vuelo: la salida
    de pandoc se integra igual que un pegado del usuario.
    """
    import base64
    import os
    import re
    import tempfile

    exe = ruta_pandoc()
    if exe is None:
        raise ErrorMotor(
            "pandoc no está disponible (ni en PATH ni como binario local)."
        )

    # Extraer medios en carpeta temporal para convertir a Base64 autocontenido
    with tempfile.TemporaryDirectory() as tmpdir:
        proceso = subprocess.run(
            [
                exe,
                "--from", "docx",
                "--to", "gfm+tex_math_dollars",
                "--wrap=none",
                f"--extract-media={tmpdir}",
                "-",
            ],
            input=dato,
            capture_output=True,
            timeout=120,
        )
        if proceso.returncode != 0:
            detalle = proceso.stderr.decode("utf-8", errors="replace")[:300]
            raise ErrorMotor(f"pandoc no pudo leer el DOCX: {detalle}")

        texto = proceso.stdout.decode("utf-8", errors="replace")
        texto = texto.replace("\\$", "$")

        # Reemplazar rutas de imágenes extraídas por referencias compactas en el cuerpo y Base64 al final
        num_figura = 1
        defs_extraidas: list[tuple[str, str]] = []

        def _reemplazar_img_por_base64(match: re.Match) -> str:
            nonlocal num_figura
            ruta_img_rel = match.group(1).replace("\\", "/")
            # Buscar el archivo físico en el tmpdir
            ruta_posible = Path(tmpdir) / ruta_img_rel
            if not ruta_posible.is_file():
                nombre_archivo = Path(ruta_img_rel).name
                encontrados = list(Path(tmpdir).rglob(nombre_archivo))
                if encontrados:
                    ruta_posible = encontrados[0]

            if ruta_posible.is_file():
                img_bytes = ruta_posible.read_bytes()
                ext = ruta_posible.suffix.lstrip(".").lower() or "png"
                if ext == "jpg":
                    ext = "jpeg"
                mime = f"image/{ext}"
                b64_str = base64.b64encode(img_bytes).decode("ascii")
                data_uri = f"data:{mime};base64,{b64_str}"
                n = num_figura
                num_figura += 1
                ref_id = f"fig{n}"
                defs_extraidas.append((ref_id, data_uri))
                return f"\n\n![Figura {n}: Ilustración técnica][{ref_id}]\n\n"
            return match.group(0)

        # Buscar tags <img src="..." /> o sintaxis Markdown ![...](...) generadas por pandoc
        texto = re.sub(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*\/?>', _reemplazar_img_por_base64, texto)
        texto = re.sub(r'!\[[^\]]*\]\(([^)]+)\)', _reemplazar_img_por_base64, texto)

        if defs_extraidas:
            lineas_defs = [
                "\n\n<!-- ======================================================== -->",
                "<!-- DEFINICIONES DE IMÁGENES BASE64 (REFERENCIAS AL FINAL) -->",
                "<!-- ======================================================== -->",
            ]
            for r_id, uri in defs_extraidas:
                lineas_defs.append(f"[{r_id}]: {uri}")
            texto = texto.rstrip() + "\n" + "\n".join(lineas_defs) + "\n"

    avisos = [
        "DOCX convertido a Markdown; imágenes embebidas en Base64 autocontenidas y ecuaciones en '$'/'$$'."
    ]
    return texto, avisos
