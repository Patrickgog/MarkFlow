# CORRECCIÓN — Controles PDF (tipografía/justificado) y Premium (portada, columnas, tema)

**Destinatario:** IA de desarrollo (Python + JS vanilla)
**Repositorio:** https://github.com/Patrickgog/markflow — rama `main`
**Base:** commit `a8cc170` (v1.23.7). Versión objetivo: **1.23.8**
**Idioma:** español (comentarios, UI, historial)

---

## 0. Reglas de trabajo

1. Trabaja sobre `main` en `a8cc170` o posterior. No reescribas historial.
2. No cambies la lógica de Word, HTML ni Excel. Solo PDF.
3. Cada bloque (A–E) es independiente. Haz commit por bloque si es posible.
4. Al final ejecuta **sección 8 (Verificación)** y reporta el resultado de cada punto con evidencia (salida de comando o captura).
5. Si no puedes verificar algo visualmente, dilo explícitamente.

---

## 1. Diagnóstico verificado

Revisado el código de `a8cc170` y ejecutado el pipeline Python (`_transformar_kpi_premium`, `_generar_html_portada_premium`, `_generar_html_impresion`, pandoc real) en el repo local.

### 1.1 Controles de tipografía y justificado (PDF) — faltantes

| # | Hallazgo | Evidencia |
|---|---|---|
| T1 | La barra lateral PDF **no tiene** control de tamaño de letra ni de justificado. Solo existen `#pdf-opt-fuente` e `#pdf-opt-interlineado`. | `templates/office.html` sección `data-seccion-id="pdf-tipografia"` (≈ línea 721) |
| T2 | `ModeloExportarPdf` (`app/rutas/office.py`) **no declara** `tamanio_pt` ni `justificado`, y `endpoint_exportar_pdf` **no los pasa** a `a_pdf`. Se usan los defaults (11 pt, justificado=True) siempre. | `app/rutas/office.py` ≈ líneas 1036–1110 |
| T3 | `a_pdf` **sí acepta** `tamanio_pt` y `justificado` y los usa en el CSS. El motor está listo; falta el cableado. | `motor/a_pdf.py` firma de `a_pdf` y `_generar_html_impresion` |
| T4 | El plan oficial `docs/planes/0025-…` y `docs/mejoras/mejoras_app_07.md` especifican para la barra PDF: `opt-tamanio-pdf` (10, 10.5, 11, 12) y `chk-justificado-pdf`. Esa especificación **no está** implementada en la barra PDF de la UI. | Documentos citados |
| T5 | Git no contiene un commit que elimine estos controles: el repositorio tiene un único commit base (`a126347`, "Initial commit") y el resto de commits no tocan esa sección. Por tanto, la regresión respecto a versiones anteriores no es trazable en este repo. **No asumas que basta con revertir un commit**: implementa desde la especificación. | `git log --oneline` |

### 1.2 Premium — portada

| # | Hallazgo | Evidencia |
|---|---|---|
| P1 | **La portada se muestra como texto de código.** El HTML de la portada se antepone al Markdown y pandoc lo interpreta como bloque de código porque las líneas van indentadas (4+ espacios). Resultado: `<pre><code>&lt;p class=…`. | Probe: `pandoc` sobre `portada + markdown` → `<pre><code>&lt;p class=&quot;portada-tipo…` |
| P2 | Las líneas en blanco (campos vacíos generan líneas con solo espacios) rompen el bloque HTML crudo para pandoc. | Mismo probe: `portada_html` contiene líneas con espacios que separan bloques |
| P3 | `_generar_html_impresion` **ya tiene** un hueco `{portada_html}` en el `<body>`, pero solo se llena para el estilo `portada` legado. La portada premium no se inyecta ahí; se inyecta al Markdown (causa de P1/P2). | `motor/a_pdf.py` ≈ línea 1120–1130 y ≈ 729 |
| P4 | **Las columnas premium no existen.** `_postprocesar_columnas_premium` busca `<div class="columns-premium">`, pero ningún código genera ese div. No hay transformación de `:::columns` (la especificación en `docs/mejoras/mejoras_app_15_maquetacion_premium.md` la pide). | `grep -rn "columns-premium\|:::columns" motor/` → solo CSS y la función de postproceso |
| P5 | `_postprocesar_columnas_premium` usa `(.*?)</div>` no codicioso; con divs anidados (p. ej. `kpi-grid`) cortaría mal. | Lectura del regex |
| P6 | Los inputs de la portada **no disparan** la vista previa en vivo (`inputsPdf` en `office.js` no incluye `#pdf-portada-*`). | `static/js/office.js` ≈ línea 2540 |
| P7 | `recolectarPortadaPremium()` lee `#pdf-portada-tipo-doc` y `#pdf-portada-codigo`, que **no existen** en `office.html`. Siempre llegan vacíos/por defecto. | `grep -n "pdf-portada-tipo-doc\|pdf-portada-codigo" templates/office.html` → vacío |
| P8 | La línea `cuerpo_html.replace('<div class="cuerpo-editorial"', ...)` (≈ línea 1508) es **código muerto**: el wrapper `cuerpo-editorial` se crea después, en `_generar_html_impresion`, que ya añade `modo-premium` por sí mismo. | Probe: `"modo-premium" in html` → True sin ese replace |

### 1.3 Lo que SÍ funciona (no tocar)

- `:::kpi … :::` → tarjetas `kpi-grid` / `kpi-card`: confirmado en probe (pandoc real).
- Clase `modo-premium` en el cuerpo y CSS premium (`.cuerpo-editorial.modo-premium …`): confirmado.
- Estilos de portada `.portada-premium …` existen en el CSS (≈ línea 748).
- Lista de temas de portada de la UI coincide con `_generar_html_portada_premium` (`clasica_blanca`, `ejecutiva_navy`, `consultoria_verde`, `blueprint`, `foto_hero`, `minimal_slate`).

---

## 2. Bloque A — Restaurar controles de tipografía y justificado (PDF)

### A.1 `templates/office.html` — reemplazar la sección `pdf-tipografia`

Sustituye el `<details data-seccion-id="pdf-tipografia">…</details>` completo por:

```html
<details class="sidebar-seccion" data-seccion-id="pdf-tipografia">
  <summary>🔤 Tipografía e Interlineado</summary>
  <div class="sidebar-seccion-contenido">
    <div class="campo-sidebar">
      <label for="pdf-opt-fuente">Tipografía:</label>
      <select id="pdf-opt-fuente" class="select-lateral"></select>
    </div>
    <div class="campo-sidebar">
      <label for="pdf-opt-tamanio">Tamaño de letra:</label>
      <select id="pdf-opt-tamanio" class="select-lateral"></select>
    </div>
    <div class="campo-sidebar">
      <label for="pdf-opt-interlineado">Interlineado:</label>
      <select id="pdf-opt-interlineado" class="select-lateral"></select>
    </div>
    <div class="campo-sidebar">
      <label class="chk-lateral"><input type="checkbox" id="pdf-opt-justificado" checked> <span>Texto justificado</span></label>
    </div>
  </div>
</details>
```

> Decisión de diseño: se usan `<select>` (no `<input type="range">`) para coherencia con el resto de barras laterales y con la especificación `planes/0025`. Si el usuario exige deslizador, sustituir por `<input type="range" min="10" max="12" step="0.5">` con una etiqueta de valor, y mantener el mismo `id`.

### A.2 `static/js/office.js` — población, persistencia y payload

1. En `inicializarBarrasLaterales()` añade (junto a los otros `poblarSelect` de PDF):
```js
poblarSelect("#pdf-opt-tamanio", MFORegistro.opciones("pdf", "tamanios"));
```
2. En la restauración de valores (bloque donde hoy se hace `$("#pdf-opt-fuente").value = opcPdf.fuente …`) añade:
```js
if ($("#pdf-opt-tamanio")) $("#pdf-opt-tamanio").value = String(opcPdf.tamanio_pt ?? 11);
if ($("#pdf-opt-justificado")) $("#pdf-opt-justificado").checked = opcPdf.justificado !== false;
```
3. En el listener de guardado de PDF (`alCambiar`, bloque `MFORegistro.guardarOpciones("pdf", {...})`) añade:
```js
tamanio_pt: parseFloat($("#pdf-opt-tamanio")?.value || "11"),
justificado: $("#pdf-opt-justificado")?.checked ?? true,
```
4. En `inputsPdf` (listeners) añade `"#pdf-opt-tamanio", "#pdf-opt-justificado"`.
5. En **los tres** payloads que llaman a `/api/office/exportar-pdf` (vista previa en vivo, exportación desde Docs y exportación desde la barra) añade:
```js
tamanio_pt: parseFloat($("#pdf-opt-tamanio")?.value || opc.tamanio_pt || "11"),
justificado: $("#pdf-opt-justificado") ? $("#pdf-opt-justificado").checked : (opc.justificado !== false),
```
   Búscalos con: `grep -n "/api/office/exportar-pdf" static/js/office.js`.

### A.3 `app/rutas/office.py`

En `ModeloExportarPdf`:
```python
tamanio_pt: float = 11.0
justificado: bool = True
```
En `endpoint_exportar_pdf`, en la llamada a `a_pdf(...)` añade:
```python
tamanio_pt=modelo.tamanio_pt,
justificado=modelo.justificado,
```

### A.4 `motor/registro_opciones.py`

Verifica que `pdf.tamanios` sea `[10.0, 10.5, 11.0, 12.0]` y `pdf.defaults` contenga `"tamanio": 11.0` y `"justificado": True`. Si falta `justificado`, añádelo.

**Criterio de aceptación A:**
- La barra PDF muestra "Tamaño de letra" (4 opciones) y "Texto justificado" (checkbox).
- Cambiar tamaño/justificado modifica el PDF exportado (ver §8.2).
- Recargar la página conserva los valores (`localStorage` clave `mfo_opciones_pdf`).

---

## 3. Bloque B — Portada premium correcta

### B.1 `motor/a_pdf.py` — dejar de inyectar la portada en el Markdown

1. En `_generar_html_impresion(...)` añade el parámetro al final de la firma:
```python
portada_premium_html: str = "",
```
2. Justo **después** del bloque `if estilo_maquetacion == "portada": portada_html = f"""…"""`, añade:
```python
if portada_premium_html:
    portada_html = portada_premium_html
```
3. En `a_pdf(...)`, **elimina** estas dos líneas (≈ 1476–1480):
```python
texto_conversion = portada_html + "\n\n" + texto_conversion
```
   y en su lugar conserva la generación de `portada_html` y guárdala en `portada_premium_html`:
```python
portada_premium_html = ""
if tiene_portada_premium:
    pp = portada_premium or {}
    datos_pp = pp.get("datos", pp)
    imagenes_pp = pp.get("imagenes", [])
    tema_pp = pp.get("tema", datos_pp.get("tema", "clasica_blanca"))
    portada_premium_html = _generar_html_portada_premium(tema_pp, datos_pp, imagenes_pp, paleta)
```
4. En la llamada a `_generar_html_impresion(...)` dentro de `a_pdf`, añade `portada_premium_html=portada_premium_html`.
5. **Elimina** el bloque muerto (≈ línea 1507–1508):
```python
if (modo_diseno or "estandar").lower() in ("premium", ...):
    cuerpo_html = cuerpo_html.replace('<div class="cuerpo-editorial"', ...)
```

### B.2 `motor/a_pdf.py` — `_generar_html_portada_premium` sin líneas en blanco ni indentación

Reescribe la función para que el HTML devuelto:
- no tenga **ninguna línea con solo espacios** ni líneas en blanco (usa `"".join(...)` con elementos en una sola línea);
- no tenga indentación al inicio de línea;
- omita por completo los campos vacíos (p. ej. `<p class="portada-memoria">` solo si `memoria` no está vacía);
- escape el contenido de texto con `html.escape()` (título, consultor, etc.).

Esqueleto:
```python
import html as _html

def _generar_html_portada_premium(tema, datos, imagenes, paleta) -> str:
    e = lambda s: _html.escape(str(s or ""))
    # ... estilos por tema (sin cambios) ...
    partes = [f'<div class="portada-premium tema-{tema}" style="background:{bg}; color:{fg};">']
    partes.append(f'<div class="portada-banda" style="border-bottom: 3pt solid {acento};"></div>')
    partes.append('<div class="portada-contenido">')
    partes.append(f'<p class="portada-tipo" style="color:{acento};">{e(tipo_doc)}</p>')
    partes.append(f'<h1 class="portada-titulo" style="color:{fg};">{e(titulo)}</h1>')
    if memoria:
        partes.append(f'<p class="portada-memoria">{e(memoria)}</p>')
    if componente:
        partes.append(f'<p class="portada-componente">{e(componente)}</p>')
    # galería de fotos: solo si n > 0, una sola línea por <img>
    # datos: solo si hay consultor/fecha/codigo
    partes.append('</div></div>')
    return "".join(partes)
```
> Conserva la lógica de estilos por tema y de `_layout_fotos`. Lo que se cambia es la **forma** de construir el HTML.

### B.3 Que la portada sea la primera página

En el CSS de `.portada-premium` (≈ línea 748) asegura:
```css
.portada-premium {
  page-break-after: always;
  break-after: page;
  min-height: 257mm;
  box-sizing: border-box;
  margin: 0 0 0 0;
}
```
Y verifica que `_postprocesar_con_pymupdf(..., omitir_portada=True)` siga siendo el comportamiento cuando `tiene_portada_premium` es verdadero (no duplicar portada).

### B.4 `static/js/office.js` — campos que faltan

1. En `office.html`, dentro de `pdf-portada-premium`, añade (si no existen):
```html
<div class="campo-sidebar">
  <label for="pdf-portada-tipo-doc">Tipo de documento:</label>
  <input type="text" id="pdf-portada-tipo-doc" class="select-lateral" value="ESTUDIO DE CONSULTORÍA DEL PROYECTO:">
</div>
<div class="campo-sidebar">
  <label for="pdf-portada-codigo">Código del proyecto:</label>
  <input type="text" id="pdf-portada-codigo" class="select-lateral" placeholder="Ej: PA-2024-017">
</div>
```
2. En `recolectarPortadaPremium()` ya se leen esos IDs; no cambiar.

### B.5 Vista previa en vivo de la portada

En el bloque `inputsPdf` (≈ línea 2540) añade los IDs de la portada:
```js
"#pdf-portada-incluir", "#pdf-portada-tema", "#pdf-portada-tipo-doc",
"#pdf-portada-titulo", "#pdf-portada-memoria", "#pdf-portada-componente",
"#pdf-portada-consultor", "#pdf-portada-fecha", "#pdf-portada-codigo",
"#pdf-portada-fotos"
```
Para `#pdf-portada-fotos` el evento `change` ya está cubierto por el listener genérico.

**Criterio de aceptación B:**
- Con "Incluir portada premium" activo, la primera página del PDF muestra el bloque de portada renderizado (no texto de código). Ver §8.3.
- El título, consultor, fecha y fotos aparecen en la portada.
- Cambiar el tema de portada actualiza la vista previa sin pulsar exportar.

---

## 4. Bloque C — Columnas premium (`:::columns`)

Implementa la sintaxis del plan `docs/mejoras/mejoras_app_15_maquetacion_premium.md`: un bloque `:::columns` con separadores `---` produce dos columnas.

### C.1 `motor/a_pdf.py` — transformación previa a pandoc

Añade junto a `_transformar_kpi_premium`:
```python
def _transformar_columnas_premium(texto: str) -> str:
    """:::columns … ::: con separadores '---' → bloques HTML marcados para dos columnas."""
    import re
    patron = re.compile(r":::columns\s*\n(.*?)\n:::", re.DOTALL | re.IGNORECASE)

    def _repl(m):
        partes = re.split(r"\n\s*---\s*\n", "\n" + m.group(1).strip() + "\n")
        bloques = [p.strip() for p in partes if p.strip()]
        cuerpo = '\n\n<div class="col-sep"></div>\n\n'.join(bloques)
        return ('\n\n<div class="columns-premium">\n\n' + cuerpo +
                '\n\n<div class="columns-premium-fin"></div>\n\n')

    return patron.sub(_repl, texto)
```
En `a_pdf(...)` llama a esta función **inmediatamente después** de `_transformar_kpi_premium`:
```python
texto_conversion = _transformar_kpi_premium(texto_conversion)
texto_conversion = _transformar_columnas_premium(texto_conversion)
```

### C.2 `motor/a_pdf.py` — reemplazar `_postprocesar_columnas_premium`

```python
def _postprocesar_columnas_premium(html: str) -> str:
    import re
    patron = re.compile(
        r'<div class="columns-premium">(.*?)<div class="columns-premium-fin"></div>',
        re.DOTALL,
    )
    def _repl(m):
        cols = [c.strip() for c in re.split(r'<div class="col-sep"></div>', m.group(1)) if c.strip()]
        if len(cols) < 2:
            cols.append("")
        return ('<div class="columns-premium">\n' +
                "\n".join(f'<div class="col">{c}</div>' for c in cols) +
                "\n</div>")
    return patron.sub(_repl, html)
```

### C.3 CSS

Confirma que existe `.columns-premium { display:grid; grid-template-columns: 1fr 1fr; gap: 12mm; }` y `.columns-premium > .col { break-inside: avoid; }` **solo dentro de `modo-premium`** o en general (decisión: general, con `break-inside: auto` para bloques largos). Si ya existe con otro selector (≈ líneas 537 y 659), unifica y no dupliques.

### C.4 Compatibilidad

Un documento sin `:::columns` no debe cambiar en absoluto. Verifica con un Markdown sin marcadores que el HTML resultante es idéntico al de `a8cc170` (diff de la salida de pandoc).

**Criterio de aceptación C:** un bloque `:::columns` con dos secciones separadas por `---` se ve en dos columnas en el PDF (§8.4).

---

## 5. Bloque D — Limpieza de código muerto

- Elimina el `replace` de `modo-premium` sobre `cuerpo_html` (P8). La clase la añade `_generar_html_impresion`.
- No dejes funciones sin uso: tras B y C, `grep -n "_postprocesar_columnas_premium\|_transformar_columnas_premium" motor/a_pdf.py` debe mostrar definición + una llamada cada una.

---

## 6. Bloque E — Historial y versión

1. `app/version.py`: `APP_VERSION = "1.23.8"`.
2. `Historial_de_versiones/historial_de_versiones.md`: entrada 1.23.8 con:
   - Restaurados en la barra PDF: tamaño de letra y texto justificado (cableados a `a_pdf`).
   - Portada premium: inyectada en el `<body>` en lugar del Markdown; corrige que se mostrara como código.
   - Portada: HTML sin indentación ni líneas en blanco; campos escapados.
   - Nueva sintaxis `:::columns` con separadores `---`.
   - Vista previa en vivo reacciona a los campos de portada.
   - Añadidos `#pdf-portada-tipo-doc` y `#pdf-portada-codigo`.
   - Eliminado código muerto de `modo-premium`.

---

## 7. Tests (nuevos)

Crea `tests/test_pdf_premium_1_23_8.py` (o en la carpeta de tests existente):

```python
import re
from pathlib import Path
from motor import a_pdf as a

RAIZ = Path(__file__).resolve().parents[1]

def test_portada_sin_indentacion_ni_lineas_vacias():
    pp = a._generar_html_portada_premium(
        "clasica_blanca",
        {"titulo_proyecto": "Proyecto X", "consultor": "Ing. Y", "memoria_fase": "", "fecha": ""},
        [],
        a.PALETAS_EDITORIAL_PDF["pizarra_carbon"],
    )
    assert "\n\n" not in pp
    assert not any(l != l.lstrip() for l in pp.split("\n"))
    assert "Proyecto X" in pp

def test_portada_escapa_html():
    pp = a._generar_html_portada_premium(
        "clasica_blanca", {"titulo_proyecto": "<script>x</script>"}, [],
        a.PALETAS_EDITORIAL_PDF["pizarra_carbon"])
    assert "<script>" not in pp

def test_columns_transforma_y_postprocesa():
    md = ":::columns\nIzquierda\n\n---\n\nDerecha\n:::\n"
    t = a._transformar_columnas_premium(md)
    assert "columns-premium" in t and "col-sep" in t
    html_fake = t.replace("Izquierda", "<p>Izquierda</p>").replace("Derecha", "<p>Derecha</p>")
    out = a._postprocesar_columnas_premium(html_fake)
    assert out.count('class="col"') == 2

def test_sin_columns_no_cambia_texto():
    md = "# T\n\nTexto normal.\n"
    assert a._transformar_columnas_premium(md) == md

def test_ui_tiene_controles_tipografia_pdf():
    html = (RAIZ / "templates" / "office.html").read_text(encoding="utf-8")
    for id_ in ("pdf-opt-tamanio", "pdf-opt-justificado", "pdf-opt-interlineado",
                "pdf-opt-fuente", "pdf-portada-tipo-doc", "pdf-portada-codigo"):
        assert f'id="{id_}"' in html, id_

def test_modelo_exportar_pdf_declara_tamanio_y_justificado():
    from app.rutas.office import ModeloExportarPdf
    m = ModeloExportarPdf()
    assert m.tamanio_pt == 11.0 and m.justificado is True
```

---

## 8. Verificación (obligatoria; reporta cada punto)

### 8.1 Tests y sintaxis
```bash
pytest -q
node --check static/js/office.js
python -m py_compile motor/a_pdf.py app/rutas/office.py
```

### 8.2 Tamaño y justificado llegan al PDF
Exporta el mismo Markdown dos veces (11 pt justificado; 12 pt no justificado) y compara:
```bash
python -I -c "
import fitz,sys
a=fitz.open(sys.argv[1]); b=fitz.open(sys.argv[2])
print('tamaños distintos:', a[0].get_text('dict')!=b[0].get_text('dict'))
" salidas/A.pdf salidas/B.pdf
```
Criterio: las dos salidas difieren en tamaño de fuente de cuerpo (`span['size']`).

### 8.3 Portada renderizada
```bash
python -I -c "
import fitz,sys
d=fitz.open(sys.argv[1]); t=d[0].get_text()
print('portada visible:', 'Proyecto X' in t)
print('sin código HTML:', '<p class' not in t and '&lt;' not in t)
" salidas/portada.pdf
```
Criterio: ambas líneas `True`.

### 8.4 Columnas
Exporta un Markdown con `:::columns`. Comprueba visualmente en la vista previa y en el PDF que aparecen dos columnas (rasteriza la página con `pymupdf` y revisa la imagen, o usa `Read` sobre la PNG).

### 8.5 Vista previa en vivo
En el navegador: cambiar `#pdf-portada-titulo` debe refrescar el visor PDF sin pulsar exportar. Consola sin errores.

### 8.6 Regresión
- Sin portada y sin `:::columns`: el PDF es idéntico al de `a8cc170` (compara número de páginas y texto extraído).
- Modo `premium` sin portada: `kpi-card` sigue apareciendo (`"kpi-card" in html`).

### 8.7 Checklist final
- [ ] Barra PDF muestra: Tipografía, Tamaño, Interlineado, Texto justificado.
- [ ] Tamaño y justificado cambian el PDF exportado (§8.2).
- [ ] Portada premium se ve como portada (§8.3); no aparece texto de código.
- [ ] `:::columns` produce dos columnas (§8.4).
- [ ] Portada se refresca en vivo (§8.5).
- [ ] Sin regresiones (§8.6).
- [ ] Historial y versión 1.23.8 actualizados.

---

## 9. Commit

Mensajes sugeridos (uno por bloque):

```
feat(pdf): restaurar tamaño de letra y texto justificado en barra lateral (v1.23.8)

- office.html: control #pdf-opt-tamanio y checkbox #pdf-opt-justificado.
- ModeloExportarPdf: tamanio_pt y justificado, pasados a a_pdf.
- office.js: población, persistencia y payloads de PDF.

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_011TSnYyUQ34QnTjQTko5ipi
```
```
fix(pdf): portada premium inyectada en el <body>, no en el Markdown (v1.23.8)

Evita que pandoc interprete el HTML indentado como bloque de código.
_generar_html_portada_premium sin indentación ni líneas en blanco; campos escapados.

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_011TSnYyUQ34QnTjQTko5ipi
```
```
feat(pdf): sintaxis :::columns para columnas premium (v1.23.8)

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_011TSnYyUQ34QnTjQTko5ipi
```

---

## Anexo A — Orden de ejecución recomendado

1. Bloque B (portada) — es el de mayor impacto visible.
2. Bloque A (tamaño y justificado) — restaura funcionalidad perdida.
3. Bloque C (columnas).
4. Bloque D (limpieza) y E (historial/versión).
5. Sección 8 (verificación) completa.

## Anexo B — Archivos afectados

| Archivo | Bloques |
|---|---|
| `templates/office.html` | A.1, B.4 |
| `static/js/office.js` | A.2, B.5 |
| `app/rutas/office.py` | A.3 |
| `motor/registro_opciones.py` | A.4 (verificación) |
| `motor/a_pdf.py` | B.1, B.2, B.3, C.1, C.2, C.3, D |
| `app/version.py`, `Historial_de_versiones/historial_de_versiones.md` | E |
| `tests/test_pdf_premium_1_23_8.py` | §7 |
