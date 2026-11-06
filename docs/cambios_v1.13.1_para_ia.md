# 🤖 Resumen Técnico de Cambios v1.13.1 — Contexto de Arquitectura para IA

> **Destinatario:** Asistentes de IA, Modelos de Lenguaje (LLMs) y Desarrolladores del Proyecto.  
> **Versión del Software:** `v1.13.1` (Incremento SemVer: PATCH).  
> **Fecha de Implementación:** 2026-10-25.  
> **Objetivo:** Documentar exhaustivamente la causa raíz, la refactorización arquitectónica y los cambios aplicados en la versión 1.13.1 para prevenir regresiones y facilitar el mantenimiento futuro.

---

## 1. Contexto del Problema y Reporte del Usuario

El usuario reportó tres fallas críticas tras editar en el **Visor y Editor Interactivo (Split-View)**:
1. **Rompimiento de tablas y cuadros en Word (.docx) y HTML:** Al editar dentro del modal Split-View y luego exportar, las tablas salían colapsadas, rotas, desordenadas y en HTML no se veían. Sin embargo, si se pulsaba «Formatear ahora» en la pantalla principal sin editar en Split-View, salía bien.
2. **Palabra parásita `[!NOTE]` dentro de las notas:** Al colocar o envolver una nota técnica, aparecía por defecto el texto literal `[!NOTE]` dentro de la nota tanto en la interfaz como en los documentos generados.
3. **Diagramas Mermaid desaparecidos:** En los entregables exportados no salían los diagramas de flujo y esquemas Mermaid; en el archivo Markdown exportado habían desaparecido por completo los cercos ````mermaid ... ````.

Los archivos con errores fueron provistos para auditoría en:
`docs/exportados/SELECCIÓN_Y_DIMENSIONAMIENTO_DE_MEDIDORES_DE_AGUA_POTABLE_BAJO_LAS_NORMAS_ISO_4064_Y_OIML_R_49.md`

---

## 2. Diagnóstico Técnico y Causa Raíz

### 2.1. El Anti-Patrón Destructivo de `sincronizarVisualACodigo()`
En versiones anteriores (v1.8.0 a v1.13.0), el modal Split-View contaba con un panel izquierdo (`splitviewTextarea`) y un panel derecho (`splitviewEditorVisual`) que tenía `contenteditable="true"`.

Para lograr una supuesta "edición visual bidireccional", se implementó en `static/js/app.js` una función llamada `sincronizarVisualACodigo()` vinculada al evento `input` del panel visual.
Esta función intentaba **re-parsear a texto Markdown el DOM HTML compilado por el servidor**:
```javascript
// CÓDIGO PROBLEMÁTICO PREVIO EN app.js:
clon.childNodes.forEach((nodo) => {
    ...
    else if (tag === "table") {
        mdRes += `${nodo.outerHTML}\n\n`; // <--- INSERTA HTML CRUDO <table>
    }
    else if (tag === "blockquote") {
        mdRes += `> [!NOTE]\n> ${txt}\n\n`; // <--- HARDCODING DE [!NOTE]
    }
});
...
splitviewTextarea.value = mdRes.trim(); // <--- SOBREESCRITURA SILENCIOSA CADA 90ms
```

#### Consecuencias Catastróficas:
1. **Degradación de Tablas:** Las tablas nativas Markdown GFM (`| Col 1 | Col 2 |\n|---|---|`) compiladas a `<table>` en el servidor eran serializadas de vuelta al textarea como HTML crudo `<table>...<thead>...<tr><th>...`. Pandoc y `a_docx.py` no procesaban adecuadamente estas tablas HTML crudas mezcladas con fórmulas, perdiendo el formateo uniforme, anchos de columna y bordes.
2. **Destrucción de Diagramas Mermaid:** Cuando el servidor compilaba un cerco ````mermaid ... ````, el visor generaba un contenedor SVG o un div renderizado. Al leer `nodo.textContent`, la función no reconocía el cerco ````mermaid y lo borraba por completo del Markdown.
3. **Pérdida de Delimitadores KaTeX:** Las fórmulas matemáticas compiladas a spans de KaTeX perdían los delimitadores originales `$$ ... $$` o `\( ... \)`.
4. **Sobreescritura Cíclica:** Cada microsegundo que el usuario hacía foco o tocaba el visual, el textarea de Markdown puro era sobreescrito por la versión degradada.

### 2.2. Inyección de `[!NOTE]`
Los botones de la barra de herramientas ejecutaban:
```javascript
aplicarFormato("> [!NOTE]\n> ", "");
```
Esto hardcodeaba la cadena `[!NOTE]` en el texto fuente, impidiendo que el motor Word y HTML presentaran la caja de nota de manera limpia sin dicho prefijo textual.

---

## 3. Arquitectura y Soluciones Implementadas en v1.13.1

```
+-----------------------------------------------------------------------------------+
|                           NUEVA ARQUITECTURA SPLIT-VIEW                            |
|                                                                                   |
|  [ splitviewTextarea ] (SSOT Inmutable)  -------> Compilación API (/api/render-preview)
|         ▲                                                        |                |
|         │ (Solo lectura directa de eventos de usuario)           ▼                |
|  [ Barra de Herramientas Word ]                         [ splitviewEditorVisual ]  |
|  (Inyecta Markdown puro:                                (contenteditable="false") |
|   **, *, ~~, `, >, -, 1.)                               Previsualizador en Vivo   |
|                                                         KaTeX / Mermaid dinámicos  |
+-----------------------------------------------------------------------------------+
```

### 3.1. Blindaje del Editor Markdown (`static/js/app.js` y `templates/index.html`)
- **Single Source of Truth (SSOT):** `splitviewTextarea` es el **único contenedor de verdad** del documento. Ninguna función externa o evento del DOM puede sobreescribir su valor salvo la acción directa del usuario o el botón «Limpiar notas».
- **Visor Visual de Solo Lectura:** En `templates/index.html`, se fijó `contenteditable="false"` en `splitview-editor-visual`, renombrando su encabezado a *"VISTA PREVIA / RENDER EN VIVO"*.
- **Eliminación Total de `sincronizarVisualACodigo()`:** Se eliminó la función y el listener `splitviewEditorVisual.addEventListener("input", sincronizarVisualACodigo)`.
- **Barra de Herramientas Desacoplada del DOM:** `aplicarFormato()` opera exclusivamente sobre la selección y texto del `splitviewTextarea`.
- **Renderizado Dinámico de KaTeX y Mermaid en Vivo:** En `actualizarRenderEnVivo()`, tras inyectar el HTML compilado en el visual, se invocan:
  ```javascript
  if (window.renderMathInElement) {
    window.renderMathInElement(splitviewEditorVisual, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
        { left: "\\(", right: "\\)", display: false },
        { left: "\\[", right: "\\]", display: true },
      ],
      throwOnError: false,
    });
  }
  if (window.mermaid) {
    try {
      window.mermaid.run({ nodes: splitviewEditorVisual.querySelectorAll(".mermaid, pre.mermaid") });
    } catch (eMermaid) {}
  }
  ```

### 3.2. Erradicación de `[!NOTE]`
1. **En la Barra de Herramientas (`static/js/app.js`):**
   - El botón `tbBtnNota` inserta directamente `> ` en cada línea seleccionada o `\n> Nota técnica: [Escriba aquí la nota...]\n\n` si no hay selección.
   - El selector `tbEstiloParrafo` mapea `"quote"` a `aplicarFormato("> ", "")`.
2. **En el Saneador (`motor/sanear.py`):**
   - Se añadió `limpiar_etiquetas_nota_parasitas(texto: str) -> str`:
     ```python
     re.sub(
         r'^(>\s*)\[!(?:NOTE|NOTA|TIP|CONSEJO|IMPORTANT|IMPORTANTE|WARNING|ADVERTENCIA|CAUTION)\]\s*',
         r'\1',
         texto,
         flags=re.MULTILINE | re.IGNORECASE,
     )
     ```
   - Integrada en el pipeline canónico de `saneanar(texto)`.
3. **En el Generador DOCX (`motor/a_docx.py`):**
   - En `_barnizar()`, al detectar un párrafo de nota (`elif es_nota:`), se limpian las cadenas `[!NOTE]` de los runs del párrafo antes de aplicar el barnizado de borde lateral y sombreado institucional.
4. **En el Conversor Inverso (`motor/reverse_converter.py`):**
   - Las citas de DOCX/PDF se transforman en `> {texto}` limpio.

### 3.3. Conversor Automático de Tablas HTML a Markdown GFM (`motor/sanear.py`)
Para reparar documentos que ya hayan sido dañados con tablas `<table>` o que provengan de fuentes HTML externas, se incorporó:
```python
def convertir_tablas_html_a_markdown(texto: str) -> str:
    """Convierte bloques <table>...</table> a sintaxis de tablas Markdown GFM.
    
    1. Extrae filas <tr> y celdas <th> o <td>.
    2. Sanea el texto de las celdas (eliminando tags HTML internos, preservando texto).
    3. Escapa caracteres pipe '|' internos.
    4. Normaliza el número de columnas y genera la fila divisoria '|---|---|'.
    """
    ...
```
Esta función se ejecuta como **Paso 0** en `saneanar()`, de modo que cualquier tabla HTML incrustada es inmediatamente convertida a tabla Markdown GFM pura antes de pasar a Pandoc o a los motores de renderizado.

### 3.4. Preservación y Renderizado de Mermaid
- Al no existir sobreescritura desde el DOM, los cercos ````mermaid ... ```` permanecen 100% íntegros en el archivo `.md`.
- En `motor/a_docx.py`, la función `reemplazar_mermaid_por_imagenes` extrae los diagramas, los renderiza a imágenes PNG de alta resolución mediante Microsoft Edge headless (`--headless --screenshot`) y los incrusta en el documento Word.
- En HTML (`motor/a_html.py`), los cercos se convierten a `<div class="mermaid">` procesados por `mermaid.min.js`.

---

## 4. Archivos Modificados en el Repositorio

| Archivo | Tipo de Cambio | Justificación Técnica |
|---|---|---|
| `app/version.py` | Modificado | Incremento semántico SSOT a `"1.13.1"`. |
| `motor/sanear.py` | Modificado | Inclusión de `convertir_tablas_html_a_markdown()` y `limpiar_etiquetas_nota_parasitas()`; integración en `saneanar()` y `eliminar_todas_las_notas()`. |
| `motor/a_docx.py` | Modificado | Limpieza de etiquetas parásitas `[!NOTE]` en los runs de notas antes de barnizar con borde y fondo en Word. |
| `motor/reverse_converter.py` | Modificado | Generación de notas limpias `> {texto}` sin prefijo `[!NOTE]`. |
| `static/js/app.js` | Modificado | Eliminación de `sincronizarVisualACodigo()`, toolbar desacoplada directa al textarea, soporte KaTeX/Mermaid en previsualización en vivo y eliminación de `[!NOTE]`. |
| `templates/index.html` | Modificado | `contenteditable="false"` en visor visual, rótulo actualizado a "VISTA PREVIA / RENDER EN VIVO" y tooltip de nota sin `[!NOTE]`. |
| `lanza_MarkFlow.bat` | Modificado | Actualización de banner y título a `v1.13.1`. |
| `pruebas/test_v1_13_1.py` | Creado | Suite de 7 pruebas unitarias de regresión para v1.13.1. |
| `pruebas/test_v1_12_0.py` a `13_0.py` | Modificados | Compatibilidad de aserciones de versión SSOT histórica con `1.13.1`. |
| `Historial_de_versiones/historial_de_versiones.md` | Modificado | Registro formal obligatorio de la versión v1.13.1. |
| `historial-resumenes/2026-10-25_v1.13.1_splitview_limpio_tablas_notas_mermaid.md` | Creado | Registro de auditoría y changelog detallado. |

---

## 5. Reglas Inviolables para Asistentes de IA (Anti-Patrones a Evitar)

Cualquier modelo de IA que trabaje en este proyecto en el futuro **DEBE RESPETAR ESTAS REGLAS**:

1. **PROHIBIDO intentar serializar el DOM compilado de vuelta a Markdown:**
   - La conversión Markdown → HTML compilado es una función **unidireccional** con pérdida de contexto estructural original (los bloques Mermaid se vuelven grafos SVG; KaTeX se convierte en decenas de elementos HTML; las tablas pierden su espaciado ASCII).
   - NUNCA reintroduzcas funciones que lean el HTML del visor para escribir en el textarea. El editor Markdown puro (`splitviewTextarea`) es la **única fuente de la verdad**.
2. **PROHIBIDO hardcodear etiquetas de alerta como `[!NOTE]`:**
   - En Markdown para este proyecto, las notas son bloques estándar de cita `> `. Los motores Word, HTML y PDF se encargan de aplicar el diseño corporativo (borde lateral, fondo suave y tipografía institucional) basándose en la sintaxis de bloque de cita. No se debe insertar `[!NOTE]` como texto.
3. **Las tablas siempre son Markdown GFM:**
   - La sintaxis permitida para tablas en Markdown es estrictamente `| Col 1 | Col 2 |\n|---|---|`. Cualquier bloque `<table>` HTML que ingrese debe ser interceptado por `convertir_tablas_html_a_markdown()`.
4. **Preservar la suite de pruebas al 100% verde:**
   - Tras cualquier cambio funcional, ejecutar `.venv\Scripts\python.exe -m pytest pruebas/` y verificar que las 182 pruebas pasen exitosamente.

---

## 6. Procedimiento de Verificación y Testing

Para verificar que todos los cambios operan al 100%:
```powershell
# 1. Compilación de sintaxis
.venv\Scripts\python.exe -m py_compile app/version.py motor/sanear.py motor/a_docx.py motor/reverse_converter.py pruebas/test_v1_13_1.py

# 2. Ejecución de pruebas unitarias específicas de v1.13.1
.venv\Scripts\python.exe -m pytest pruebas/test_v1_13_1.py -v

# 3. Ejecución de toda la suite de pruebas del proyecto (182 pruebas)
.venv\Scripts\python.exe -m pytest pruebas/
```

Todas las pruebas deben concluir con código de salida `0` y `182 passed`.
