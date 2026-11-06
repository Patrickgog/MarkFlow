"""Motor mermaid: cercos ` ```mermaid ` → PNG para DOCX (Edge headless).

Pipeline:
  1. Detección de cercos ` ```mermaid … ``` ` fuera de código anidado.
  2. Cada cerco se renderiza contra una página HTML mínima con mermaid.js
     LOCAL (`motor/assets/mermaid/mermaid.min.js`) usando Microsoft Edge
     en modo headless (`--screenshot`), a imagen PNG blanca. El diagrama
     se dibuja a su tamaño INTRÍNECO con tema de colores (plan 0005, D6).
  3. Recorte de blancos con Pillow (`_recortar_blanco`): el PNG queda con
     la proporción exacta de los elementos del diagrama, simétrico.
  4. El cerco se sustituye por una referencia de imagen Markdown con pie
     y ancho PROPORCIONAL (`![Figura N — Diagrama](ruta.png){width=Xin}`),
     lista para pandoc en `a_docx` (el centrado lo aplica `_barnizar`).

Degradación honrosa (plan 0003, RC2): si Edge o el activo local no están
disponibles, el texto del cerco se devuelve intacto y se acumula un aviso;
el flujo DOCX nunca se rompe por un diagrama.
"""

from __future__ import annotations

import math
import re
import subprocess
import tempfile
from pathlib import Path

_CERCO = re.compile(
    r"(?:^|\n)[ \t]*`{3,}\s*mermaid[^\n]*\n([\s\S]*?)(?:[ \t]*`{3,}|$)",
    re.IGNORECASE,
)

_EDGES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
)
_ASSET_JS = Path(__file__).resolve().parent / "assets" / "mermaid" / "mermaid.min.js"

# --- Fase 2: Geometría, densidad y legibilidad de diagramas (300 DPI) ---------
_VENTANA = (2400, 3200)   # Ventana amplia para diagramas complejos
_MARGEN_PX = 24           # Margen uniforme al recortar blanco
_ANCHO_COLUMNA_MAX_IN = 6.20   # Ancho útil máximo en A4 (15.75 cm)
_ANCHO_COLUMNA_MIN_IN = 3.72   # Mínimo 60% del ancho de columna (9.45 cm)
_ALTO_MAX_IN = 8.66           # Techo de alto de 22 cm en A4 para no desbordar página
_FACTOR_ESCALA_DEVICE = 3.0   # 300 DPI reales para alta fidelidad editorial

_PAGINA = """<!doctype html>
<html><head><meta charset="utf-8">
<style>
  body {{
    margin: 0;
    padding: 32px;
    background: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  }}
  .mermaid {{
    text-align: center;
    font-size: 16px;
    background: transparent;
  }}
  .mermaid svg {{
    max-width: 100% !important;
    height: auto !important;
    display: block;
    margin: 0 auto;
  }}
  /* Texto legible no menor a 15px en nodos, etiquetas y enlaces */
  .mermaid svg text,
  .mermaid svg .label,
  .mermaid svg .nodeLabel,
  .mermaid svg .edgeLabel {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif !important;
    font-size: 16px !important;
    font-weight: 500 !important;
  }}
  /* Ocultar cualquier bomba de error nativa de Mermaid sin bloquear getBBox en sandbox */
  [id^="dgrafo"], [id^="dmermaid-"] {{
    position: fixed !important;
    left: -99999px !important;
    top: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
  }}
  g.error-icon, svg[aria-roledescription="error"], [aria-roledescription="error"] {{
    display: none !important;
    visibility: hidden !important;
  }}
</style>
<script>{js}</script>
</head><body>
<div class="mermaid" id="grafo">
{cuerpo}</div>
<script>
  (async function() {{
    mermaid.initialize({{
      startOnLoad: false,
      theme: "default",
      securityLevel: "loose",
      fontSize: 16,
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      flowchart: {{
        useMaxWidth: false,
        htmlLabels: true,
        nodeSpacing: 45,
        rankSpacing: 45,
        curve: "basis"
      }},
      themeVariables: {{
        fontSize: "16px",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
      }}
    }});
    var el = document.getElementById("grafo");
    if (!el) return;
    var codigo = (el.textContent || "").trim();
    try {{
      var res = await mermaid.render("grafo_svg", codigo);
      el.innerHTML = res.svg;
    }} catch (err) {{
      document.querySelectorAll('[id^="dgrafo"], [id^="dmermaid-"]').forEach(function(d){{ d.remove(); }});
      el.innerHTML = '<div style="padding:12px 16px; border:1px solid #ef4444; background:#fef2f2; color:#b91c1c; border-radius:6px; font-family:sans-serif; font-size:14px; text-align:left; max-width:600px;"><strong>Error en la sintaxis del diagrama Mermaid:</strong><br>' + String(err.message || err).replace(/</g, "&lt;") + '</div>';
    }}
  }})();
</script>
</body></html>
"""


class ErrorMermaid(RuntimeError):
    """Fallo del render headless (diagrama no convertido a PNG)."""


def contar_mermaid(texto: str) -> int:
    """Número de cercos mermaid del documento (fuera de código anidado)."""
    return len(_CERCO.findall(texto))


def ruta_edge() -> Path | None:
    """Ejecutable de Microsoft Edge disponible en las rutas estándar."""
    for exe in _EDGES:
        if exe.is_file():
            return exe
    return None


def sanear_codigo_mermaid(codigo: str) -> str:
    """Sanea sintaxis Mermaid generada por humanos o LLMs (v1.20.3 — robusto):

    1. Normaliza superíndices Unicode (², ³, etc.) a dígitos ASCII.
    2. Elimina espacios antes de ::: (STYLE_SEPARATOR).
    3. Convierte <= a ≤ y >= a ≥.
    4. Protege nodos entre corchetes:
       - ["ya entre comillas"] → se conservan intactos.
       - [texto sin comillas] → se envuelven en ["texto"]:
           * Corchetes anidados [unidad] dentro del nodo → (unidad).
           * Flechas Unicode → → ->, ← → <-.
           * Ángulos sueltos < y > → &lt; &gt;
           * Comillas dobles internas → simples.
    5. No toca directivas Mermaid: classDef, style, click, linkStyle.
    """
    if not codigo:
        return ""

    # ── Paso 1: Superíndices Unicode → ASCII ────────────────────────────────────
    _SUP: dict[str, str] = {
        "\u00b2": "2", "\u00b3": "3", "\u2070": "0", "\u00b9": "1",
        "\u2074": "4", "\u2075": "5", "\u2076": "6", "\u2077": "7",
        "\u2078": "8", "\u2079": "9",
    }
    c: str = codigo
    for orig, remp in _SUP.items():
        c = c.replace(orig, remp)

    # ── Paso 2: Espacios antes de ::: ───────────────────────────────────────────
    c = re.sub(r"(\]|\)|\}|>|\w)\s+:::", r"\1:::", c)
    c = re.sub(r"\s+:::", ":::", c)

    # ── Paso 3: Operadores de comparación ───────────────────────────────────────
    c = c.replace("<=", "\u2264").replace(">=", "\u2265")

    # ── Paso 4: Protección de nodos [texto] con analizador por estado ───────────
    _DIRECTIVAS = re.compile(
        r"^\s*(classDef|style|click|linkStyle|subgraph|end)\b", re.IGNORECASE
    )

    def _sanitizar_interior(texto: str) -> str:
        """Limpia el texto interior de un nodo que NO tiene comillas dobles."""
        t = texto
        # Flechas Unicode no son conectores de grafo cuando están en texto
        t = t.replace("\u2192", "->").replace("\u2190", "<-").replace("\u2194", "<->")
        # Corchetes anidados de unidades → paréntesis
        t = re.sub(r"\[([^\[\]]*?)\]", r"(\1)", t)
        # Ángulos sueltos
        t = re.sub(r"<(?![=-])", "&lt;", t)
        t = re.sub(r"(?<![=-])>", "&gt;", t)
        # Comillas dobles → simples
        t = t.replace('"', "'")
        return t

    def _procesar_linea(linea: str) -> str:
        """Recorre la línea carácter a carácter para proteger nodos [...]."""
        resultado: list[str] = []
        i = 0
        n = len(linea)
        while i < n:
            ch = linea[i]

            if ch != "[":
                resultado.append(ch)
                i += 1
                continue

            # Encontramos '[': determinar si es un nodo de Mermaid
            j = i + 1  # apunta al primer char dentro del corchete

            # Caso 1: Nodo ya entre comillas ["..."] — buscar el cierre '"]'
            if j < n and linea[j] == '"':
                k = linea.find('"]', j + 1)
                if k != -1:
                    # Conservar el nodo intacto
                    resultado.append(linea[i:k + 2])
                    i = k + 2
                    continue
                # Si no hay '"]', tratar como texto normal
                resultado.append(ch)
                i += 1
                continue

            # Caso 2: Nodo sin comillas [texto...] — necesitamos encontrar el ']'
            # teniendo en cuenta que puede haber sub-corchetes anidados [unidad]
            # Estrategia: acumular el texto del nodo hasta encontrar el ']' que
            # cierra el nodo principal, respetando anidamiento.
            nivel = 1
            k = j
            while k < n and nivel > 0:
                if linea[k] == "[":
                    nivel += 1
                elif linea[k] == "]":
                    nivel -= 1
                k += 1
            # k apunta al char después del ']' de cierre
            if nivel == 0:
                interior = linea[j:k - 1]  # sin los corchetes externos
                interior_sano = _sanitizar_interior(interior)
                resultado.append(f'["{interior_sano}"]')
                i = k
                continue

            # No se encontró cierre: dejar como está
            resultado.append(ch)
            i += 1

        return "".join(resultado)

    lineas: list[str] = []
    for linea in c.splitlines():
        if _DIRECTIVAS.match(linea):
            lineas.append(linea)
        else:
            lineas.append(_procesar_linea(linea))

    return "\n".join(lineas)

def _pagina(cuerpo: str) -> str:
    """Página HTML minimum con mermaid.js local embebido (offline)."""
    try:
        js = _ASSET_JS.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:                      # pragma: no cover - activo ausente
        raise ErrorMermaid(f"mermaid.min.js no disponible: {exc}") from exc
    return _PAGINA.format(js=js, cuerpo=sanear_codigo_mermaid(cuerpo))


def _recortar_blanco(ruta: Path) -> bool:
    """Recorta el papel blanco sobrante del screenshot (plan 0005, D6).

    La captura es de la ventana completa; aquí se ajusta el PNG a la caja
    real del diagrama (bbox de píxeles no blancos) con un margen UNIFORME
    en los cuatro lados, de modo que la imagen tenga la proporción exacta
    de sus elementos y quede simétrica (el centrado en Word es de Word).

    Devuelve False si no hay nada que recortar (Pillow ausente o imagen
    en blanco): en ese caso el PNG conserva el formato de la ventana
    (degradación honrosa, comportamiento previo).
    """
    try:
        from PIL import Image, ImageChops
    except ImportError:                          # pragma: no cover - sin Pillow
        return False
    try:
        with Image.open(ruta) as abierta:
            imagen = abierta.convert("RGB")
        blanco = Image.new("RGB", imagen.size, (255, 255, 255))
        caja = ImageChops.difference(imagen, blanco).getbbox()
        if caja is None:                         # todo en blanco: intacto
            return False
        x0, y0, x1, y1 = caja
        # margen simétrico: el mismo en los 4 lados (limitado por lo
        # disponible, para no salirse de la imagen)
        margen = min(
            _MARGEN_PX, x0, y0, imagen.width - x1, imagen.height - y1
        )
        margen = max(0, margen)
        recorte = imagen.crop(
            (x0 - margen, y0 - margen, x1 + margen, y1 + margen)
        )
        recorte.save(ruta, "PNG")
        return True
    except OSError:                              # pragma: no cover - I/O
        return False


def _dimensiones_png(ruta: Path) -> tuple[int, int]:
    """(ancho, alto) en píxeles, leyendo la cabecera IHDR del PNG."""
    with open(ruta, "rb") as f:
        cabecera = f.read(24)
    if (
        len(cabecera) < 24
        or cabecera[:8] != b"\x89PNG\r\n\x1a\n"
        or cabecera[12:16] != b"IHDR"
    ):
        raise OSError("el archivo no es un PNG válido")
    ancho = int.from_bytes(cabecera[16:20], "big")
    alto = int.from_bytes(cabecera[20:24], "big")
    return ancho, alto


def _atributo_ancho(ruta: Path) -> str:
    """Calcula `{width=Xin}` garantizando tamaño legible en Word y PDF (Fase 2).

    Reglas (Fase 2):
      - Ancho máximo: columna útil en A4 (_ANCHO_COLUMNA_MAX_IN = 6.20 in).
      - Ancho mínimo: 60 % de la columna (_ANCHO_COLUMNA_MIN_IN = 3.72 in).
      - Alto máximo: 22 cm en A4 (_ALTO_MAX_IN = 8.66 in).
    """
    try:
        px_w, px_h = _dimensiones_png(ruta)
    except OSError:
        return ""
    if not px_w or not px_h:
        return ""

    # Convertir px reales (capturados con escala 3x a 300 DPI) a pulgadas lógicas
    w_in = px_w / (96.0 * _FACTOR_ESCALA_DEVICE)
    h_in = px_h / (96.0 * _FACTOR_ESCALA_DEVICE)
    relacion = w_in / max(0.01, h_in)

    # Dimensionar proporcionalmente asegurando rango mínimo (60%) y máximo (100%)
    ancho = max(_ANCHO_COLUMNA_MIN_IN, min(w_in, _ANCHO_COLUMNA_MAX_IN))
    alto = ancho / relacion

    # Si la altura superaría 22 cm (8.66 in), limitar por altura para que quepa en A4
    if alto > _ALTO_MAX_IN:
        alto = _ALTO_MAX_IN
        ancho = alto * relacion
        if ancho > _ANCHO_COLUMNA_MAX_IN:
            ancho = _ANCHO_COLUMNA_MAX_IN
        ancho = math.floor(ancho * 100.0) / 100.0

    texto = f"{ancho:.2f}".rstrip("0").rstrip(".")
    return f"{{width={texto}in}}"


def renderizar_a_png(cuerpo: str, destino: Path) -> Path:
    """Renderiza un cuerpo mermaid a PNG (borde de ventana + recorte D6 a 300 DPI).

    Edge captura la ventana con factor de escala 3x (300 DPI); después
    `_recortar_blanco` ajusta el PNG a la caja real del diagrama.
    """
    exe = ruta_edge()
    if exe is None:
        raise ErrorMermaid("Microsoft Edge no está disponible para el render.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    pagina = destino.with_suffix(".html")
    pagina.write_text(_pagina(cuerpo), encoding="utf-8")
    user_data = Path(tempfile.gettempdir()) / "edge_mfo_profile"
    proceso = subprocess.run(
        [
            str(exe),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-sandbox",
            f"--user-data-dir={user_data}",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=2000",
            f"--force-device-scale-factor={int(_FACTOR_ESCALA_DEVICE)}",
            "--default-background-color=FFFFFFFF",
            f"--window-size={_VENTANA[0]},{_VENTANA[1]}",
            f"--screenshot={destino}",
            pagina.resolve().as_uri(),
        ],
        capture_output=True,
        timeout=30,
    )
    if proceso.returncode != 0 or not destino.is_file():
        detalle = proceso.stderr.decode("utf-8", "replace")[:200]
        raise ErrorMermaid(f"Edge no completó el screenshot: {detalle}")
    pagina.unlink(missing_ok=True)
    _recortar_blanco(destino)               # degradación honrosa si falla
    return destino


def reemplazar_mermaid_por_imagenes(
    texto: str, carpeta: Path
) -> tuple[str, int, list[str]]:
    """Convierte los cercos mermaid del texto a imágenes Markdown.

    Devuelve (texto_final, convertidos, avisos); los cercos que no se
    pudieron convertir se devuelven intactos con un aviso honroso.
    """
    avisos: list[str] = []
    convertidos = 0
    total = contar_mermaid(texto)
    if not total:
        return texto, 0, avisos

    if ruta_edge() is None:
        avisos.append(
            "Mermaid sin render nativo en DOCX (Microsoft Edge no está "
            f"disponible): los {total} diagrama(s) quedan como bloque de "
            "código legible."
        )
        return texto, 0, avisos
    if not _ASSET_JS.is_file():
        avisos.append(
            "Mermaid sin render nativo en DOCX (falta el activo "
            f"mermaid.min.js local): los {total} diagrama(s) quedan como "
            "bloque de código legible."
        )
        return texto, 0, avisos

    try:                                          # recorte D6 disponible
        import PIL  # noqa: F401
        hay_pillow = True
    except ImportError:                           # pragma: no cover - sin Pillow
        hay_pillow = False

    indice = 0
    avisos_render: list[str] = []

    def envoltorio(m: re.Match) -> str:
        nonlocal indice
        numero = indice + 1
        indice += 1
        png = carpeta / f"mermaid-{numero:02d}.png"
        try:
            renderizar_a_png(m.group(1).rstrip(), png)
        except (ErrorMermaid, subprocess.SubprocessError, OSError) as exc:
            avisos_render.append(f"Diagrama {numero} sin convertir a PNG: {exc}")
            return m.group(0)               # cerco original intacto
        # Plan 0005 (D6): el ancho es PROPORCIONAL a la caja real del
        # diagrama recortado (vertical -> estrecho; horizontal -> ancho),
        # nunca un formato fijo; pandoc lo aplica con `link_attributes` y
        # el centrado en Word lo aporta `_barnizar` en a_docx.
        ancho = _atributo_ancho(png)
        if not hay_pillow:
            avisos_render.append(
                f"Diagrama {numero} sin recortar (falta Pillow): conserva "
                "el formato de la ventana de captura."
            )
        return (
            f"![Figura {numero} — Diagrama de flujo]({png.as_posix()})"
            f"{ancho}"
        )

    final = _CERCO.sub(envoltorio, texto)
    convertidos = total - len(avisos_render)
    avisos.extend(avisos_render)
    if convertidos:
        avisos.append(
            f"{convertidos} diagrama(s) mermaid incrustado(s) como imagen "
            "PNG en el DOCX (render Edge headless)."
        )
    if convertidos < total:
        avisos.append(
            f"{total - convertidos} diagrama(s) mermaid sin convertir: "
            "quedan como bloque de código legible en el entregable."
        )
    return final, convertidos, avisos
