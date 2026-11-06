#  Hojas de membrete en la pestaña PDF (MarkFlow Office)

. No avances a la siguiente fase sin cumplir los criterios de la actual y sin entregar su reporte.

Este prompt depende del prompt de Word (`prompt_word_hojas_membrete.md`): reutiliza la carpeta de hojas, el análisis de zona y los archivos `Nombre.zona.json`. Si el prompt de Word aún no está implementado, la Fase 0 de este documento lo indica y debes pedir confirmación antes de continuar.

---

## 0. Reglas generales

1. **Analiza antes de cambiar.** En cada fase, describe primero el código relacionado con nombres reales de archivos y funciones. No inventes nombres. Si algo de este documento no existe en el código, dilo.
2. **No rompas lo que funciona:** la exportación PDF actual (PDF Editorial de `motor/a_pdf.py`), el salto de página por capítulo, el índice al final, la numeración existente, el visor PDF local (`static/js/visor_pdf.js`) y las fórmulas.
3. **Sin CDN.** Todo local. Si una librería no está en el proyecto, pide aprobación antes de incorporarla.
4. **Idioma:** español en toda la interfaz y en los mensajes.
5. **Alcance:** solo PDF. HTML queda para otro prompt.
6. **Cuando no hay plantilla elegida, el PDF debe salir exactamente igual que hoy.**
7. **Reporte por fase.** Al terminar cada fase, entrega su reporte (sección 9) y espera confirmación del usuario.

---

## 1. Contexto

### 1.1 Cómo se genera el PDF hoy
El PDF se genera con **Chromium headless** a partir de un HTML intermedio construido en `motor/a_pdf.py`. Ese HTML pasa por el pipeline de Pandoc y las reglas CSS de impresión (`@page`, salto de página por capítulo, índice al final). Después Chromium imprime a PDF.

### 1.2 Qué es una hoja de membrete para PDF
Es un `.docx` de la carpeta `storage/plantillas_word/` cuyo único contenido es una **imagen del membrete** anclada a la página (puede ocupar parte de la hoja o toda ella). En PDF no se usa el `.docx` como base: se extrae la imagen del membrete y se coloca como **fondo fijo** en cada página del HTML intermedio.

### 1.3 Qué hace el usuario
1. Elige una hoja en el combobox de la pestaña PDF.
2. Opcionalmente activa la numeración de páginas.
3. Exporta: cada página del PDF lleva el membrete y el contenido escrito en la zona de escritura.

### 1.4 Dos caminos técnicos
- **Opción A (recomendada por defecto):** el membrete se extrae del `.docx` como imagen (`word/media/`) y se inserta como fondo fijo en el HTML intermedio. No requiere librerías nuevas.
- **Opción B (requiere aprobación):** el membrete se guarda como PDF de una página (`Nombre.pdf` en la misma carpeta) y se sobrepone a cada página generada con `pypdf` (`merge_page`). Solo se usa si la hoja tiene formas, texto vectorial o efectos que la opción A no puede capturar, y si el usuario aprueba incorporar `pypdf`.

**Regla:** en la Fase 0 decide cuál aplica a cada hoja. No cambies de opción sin preguntar.

---

## 2. FASE 0 — Diagnóstico del membrete y decisión de camino

**Objetivo:** saber si el membrete se puede representar como imagen (Opción A) o necesita superposición (Opción B).

**Tareas**
1. Lee `motor/a_pdf.py`, `app/rutas/office.py` (endpoint `POST /api/office/exportar-pdf`), `static/js/office.js` (sección PDF de la barra lateral), `templates/office.html` (`#sidebar-pdf-opciones`) y `historial_de_versiones.md`.
2. Confirma si ya existe la carpeta `storage/plantillas_word/` y la función `analizar_membrete` del prompt de Word. Si no existen, detente y pide confirmación del orden de implementación.
3. Inspecciona cada hoja de la carpeta leyendo su XML con `zipfile`:
   - `word/document.xml`: ¿la imagen está en `wp:anchor` con `relativeFrom="page"`? ¿Hay formas (`wps:wsp`), grupos (`wpg:wgp`) o texto dibujado?
   - `word/media/`: ¿hay una imagen (PNG, JPG, EMF, WMF)? ¿Qué formato y resolución tiene?
   - `word/header*.xml` y `word/footer*.xml`: ¿contienen texto o solo la imagen?
4. Clasifica cada hoja:
   - **Tipo 1 (imagen simple):** una sola imagen raster o vector de mapa de bits, anclada a la página. → Opción A.
   - **Tipo 2 (compuesta):** imagen más texto, formas o grupos. → Opción B, con aprobación.
   - **Tipo 3 (vectorial no extraíble):** formas o EMF/WMF que no se pueden convertir de forma fiable. → Opción B, o advertir al usuario que el resultado puede no coincidir.

**Criterios de aceptación**
- [ ] Tabla con el tipo de cada hoja de ejemplo y su camino recomendado.
- [ ] Si alguna hoja es Tipo 2 o 3: lista de la aprobación que se necesita (por ejemplo, `pypdf`).
- [ ] Confirmación de dependencias del prompt de Word (carpeta, `analizar_membrete`, `.zona.json`).

**Detente y pide aprobación antes de la Fase 1 si hay hojas Tipo 2 o 3.**

---

## 3. FASE 1 — Extracción del membrete

**Objetivo:** obtener la imagen del membrete y su posición, listas para usarse en el HTML intermedio.

**Función nueva**: `extraer_membrete_pdf(ruta_docx)`, en `motor/a_pdf.py` o en un módulo nuevo (según la estructura real). Devuelve:
- `imagen`: ruta a un archivo temporal o a un PNG/JPG generado. Si el formato es EMF o WMF, conviértelo a PNG solo si hay un conversor local disponible; si no, avisa.
- `posicion_cm`: `x`, `y`, `ancho`, `alto` de la imagen sobre la página, calculados desde `positionH`, `positionV` y `wp:extent` (1 cm = 360000 EMU). Si la posición es relativa a la página, usa esa referencia directamente.
- `behind_doc`: booleano.

**Caché**
- Guarda la imagen extraída en `storage/salidas/cache_membrete/` o en la carpeta temporal que use el proyecto, con clave igual al nombre del archivo y su fecha de modificación. Si el `.docx` cambia, se regenera.

**Criterios de aceptación**
- [ ] Hoja Tipo 1: se extrae la imagen y su posición coincide con el análisis de Word.
- [ ] Segunda llamada con el mismo archivo: no vuelve a extraer (usa caché).
- [ ] Hoja sin imagen: devuelve `None` y avisa sin romper la exportación.

---

## 4. FASE 2 — Zona de escritura y reglas `@page`

**Objetivo:** que el contenido del PDF se escriba dentro de la zona libre de la hoja.

**Zona**
- Usa la misma zona de escritura que calcula el prompt de Word (`zona_sugerida_cm`) o el archivo `Nombre.zona.json`.
- Tradúcela a márgenes de página: `@page { size: A4; margin: <top> <right> <bottom> <left>; }`.

**Reglas**
- Si la zona no es la del `sectPr`, la de `@page` tiene prioridad sobre el margen por defecto del motor.
- El ancho útil de tablas y figuras se calcula con la zona, no con un ancho fijo.
- Si el usuario no elige plantilla, `@page` queda como está hoy.

**Criterios de aceptación**
- [ ] Con hoja de página completa: márgenes iguales a los del `sectPr`.
- [ ] Con banda superior: el texto empieza debajo de la banda más 0,5 cm.
- [ ] Sin plantilla: `@page` idéntico al actual (regresión).

---

## 5. FASE 3 — Inserción del membrete en el HTML intermedio

### Opción A (por defecto)

**Objetivo:** que el membrete aparezca en cada página impresa.

**Tareas**
1. En el HTML intermedio de `motor/a_pdf.py`, agrega una imagen con estilo fijo:

```css
.membrete-hoja {
  position: fixed;
  left: <x_cm>cm;
  top: <y_cm>cm;
  width: <ancho_cm>cm;
  height: <alto_cm>cm;
  z-index: -1;
}
```

2. Incrusta la imagen como **Data URI Base64**, igual que ya hace el motor con las imágenes (`convertir_imagen_a_base64`), para que el HTML sea autónomo.
3. Verifica en la impresión de Chromium que la imagen se repite en cada página. Si Chromium no repite el elemento fijo en tu versión, cambia a un `div` dentro de `@page` (ver nota de Opción B) o avisa al usuario.

**Criterios de aceptación**
- [ ] Documento de tres páginas: el membrete aparece en las tres.
- [ ] El contenido no se superpone a la imagen en la zona de escritura.
- [ ] La imagen mantiene su proporción.

### Opción B (solo con aprobación)

**Objetivo:** sobreponer el membrete en PDF cuando la hoja no se puede representar como imagen.

**Tareas**
1. Genera el PDF del contenido con la misma lógica de la Opción A, sin membrete.
2. Carga `Nombre.pdf` (la página del membrete exportada una vez desde Word).
3. Con `pypdf`, combina cada página del contenido con la página del membrete (`merge_page`), usando la misma página como fondo.
4. Guarda el resultado en el mismo flujo de descarga actual.

**Criterios de aceptación**
- [ ] Cada página del PDF final contiene el membrete y el contenido.
- [ ] El número de páginas coincide con el PDF generado sin membrete.

---

## 6. FASE 4 — Numeración de páginas

**Objetivo:** "Página X de Y" en cada página, sin tapar el membrete.

**Opción preferida (CSS con contadores)**
- Dentro de `@page`, usa las cajas de margen:

```css
@page {
  @bottom-center { content: "Página " counter(page) " de " counter(pages); }
}
```

- Antes de usarla, **verifica que tu versión de Chromium la soporta**. Si no la soporta, usa la alternativa siguiente.

**Alternativa**
- Sin soporte de cajas de margen, genera la numeración con `pypdf` (solo con aprobación de la Fase 3, Opción B), o aplica un pie fijo sin total y avisa al usuario.

**Reglas**
- Desactivada por defecto. Se activa con el checkbox "Numerar páginas" y la posición `centro` o `derecha`.
- La numeración se coloca dentro del margen inferior reservado, sin tapar el membrete.
- Sin plantilla y con numeración desactivada, el PDF no cambia.

**Criterios de aceptación**
- [ ] Con numeración activa: "Página X de Y" correcto en todas las páginas.
- [ ] No tapa el membrete ni el contenido.
- [ ] Con numeración desactivada: no aparece texto de página.

---

## 7. FASE 5 — Interfaz y exportación

**Objetivo:** que la pestaña PDF permita elegir la hoja y exportar con ella.

**Interfaz (`templates/office.html`, `#sidebar-pdf-opciones`)**
- Tarjeta "Hoja de membrete" propia, con:
  - `<select id="pdf-plantilla-hoja">`: "Sin plantilla (predeterminada)" y una opción por cada `.docx` de `storage/plantillas_word/` (reutiliza `GET /api/office/plantillas-word`).
  - Checkbox "Numerar páginas" y selector de posición.
  - Indicador del camino técnico que se usará (A o B), según el resultado de la Fase 0 para esa hoja.
- Las opciones se guardan en `MFORegistro` (`registro_temas.js`), igual que el resto de la barra PDF.

**Vista previa**
- `refrescarVisorPdfEnVivo()` en `static/js/office.js` debe incluir el membrete elegido, de modo que la vista previa refleje el PDF final.
- Si la vista previa no puede mostrar el membrete (por ejemplo, Opción B sin aprobación), indícalo en la tarjeta. No finjas una vista previa real.

**Exportación (`POST /api/office/exportar-pdf`)**
- Campos nuevos, además de los actuales:
  - `plantilla_word` (nombre de archivo, opcional);
  - `numerar_paginas` (booleano);
  - `posicion_numero` (`centro` o `derecha`);
  - `zona` (opcional; si no viene, se usa `Nombre.zona.json` o el análisis).
- Valida `plantilla_word` contra la lista real de archivos de `storage/plantillas_word/`. Solo `.docx`. Aplica `resolve()` y `relative_to()`.
- Si `plantilla_word` está vacío, la exportación es la actual, sin cambios.
- Respuesta con `Content-Type: application/pdf` y cabeceras estrictas, como ya hace el endpoint actual.

**Criterios de aceptación**
- [ ] La tarjeta lista las hojas de la carpeta.
- [ ] Elegir una hoja actualiza la vista previa.
- [ ] La exportación con hoja produce un PDF con el membrete en cada página.
- [ ] La exportación sin hoja es idéntica a la actual.
- [ ] Nombre inventado o con `../` responde 400 o 404.

---

## 8. FASE 6 — Versión y pruebas

**Versión:** MINOR. Si se implementa junto con Word, usa **v1.21.0** y una sola entrada en `historial_de_versiones.md`. Si va después, usa **v1.22.0**. Actualiza `app/version.py` (SSOT), `README.md` e `interfaces/mcp/server.json`.

**Pruebas** (en `pruebas/test_v1_21_0.py` o `pruebas/test_v1_22_0.py`):
1. Hoja Tipo 1: extracción de imagen con la posición esperada.
2. Hoja sin imagen: `None` y aviso, sin error.
3. Caché: segunda extracción no regenera la imagen.
4. Zona de hoja de página completa: márgenes de `@page` iguales al `sectPr`.
5. Zona con banda superior: texto debajo de la banda más 0,5 cm.
6. Documento de tres páginas: membrete en las tres (Opción A).
7. Numeración "Página X de Y" correcta y sin tapar el membrete.
8. Exportación sin hoja idéntica a la anterior (regresión).
9. Nombre inventado o con `../`: 400 o 404.
10. Consola del navegador y logs del servidor sin errores.
11. Revisión visual del PDF final en un visor real, con al menos dos hojas de la carpeta.

**Criterios de aceptación**
- [ ] Suite completa en verde.
- [ ] Revisión manual del PDF en visor real, con membrete correcto y numeración legible.

---

## 9. Reporte obligatorio por fase

1. **Fase** y estado: completada, parcial o pendiente.
2. **Diagnóstico** de cada punto de la fase, con su causa.
3. **Archivos creados y modificados**, con su función.
4. **Funciones o endpoints nuevos o cambiados.**
5. **Dependencias nuevas** con justificación, o confirmación de que no hacen falta.
6. **Resultado de cada criterio de aceptación.**
7. **Pendientes y preguntas** para el usuario.

Después de entregar el reporte de cada fase, **detente** y espera la evaluación del usuario.

---

