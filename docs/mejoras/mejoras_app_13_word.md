#  Hojas de membrete en la pestaña Word (MarkFlow Office)

ejecútalo **por fases, en el orden indicado**. No avances a la siguiente fase sin cumplir los criterios de la actual y sin entregar su reporte.

---

## 0. Reglas generales

1. **Analiza antes de cambiar.** En cada fase, primero describe el código relacionado con nombres reales de archivos y funciones. No inventes nombres. Si algo de este documento no existe en el código, dilo.
2. **No rompas lo que funciona:** ingesta de archivos, round-trip `.docx`, numeración existente, pestaña **MarkFlow Conversión Completa**, fórmulas, cuadros anchos, visor flotante y la exportación Word actual cuando no se elige plantilla.
3. **Sin CDN.** La app funciona offline. Si una librería no está en el proyecto, pide aprobación antes de incorporarla.
4. **Idioma:** español en toda la interfaz y en los mensajes.
5. **Alcance de este prompt:** solo Word. PDF y HTML se tratan en otro prompt.
6. **Reporte por fase.** Al terminar cada fase, entrega su reporte (sección 9) y espera confirmación del usuario.

---

## 1. Contexto

### 1.1 Qué es una hoja de membrete
Cada archivo `.docx` de la carpeta es una **hoja de membrete**: una hoja **vacía** cuyo único contenido es una **imagen del membrete** (logotipo, franja o fondo) anclada a la página. La imagen puede ocupar parte de la hoja o toda ella. No tiene números de página. El cuerpo del documento no tiene texto ni placeholders; si lo tuviera, se ignora.

### 1.2 Qué hace el usuario
1. Elige una hoja en un combobox dentro de la pestaña Word.
2. Opcionalmente completa los datos del oficio.
3. Escribe o pega su contenido en Docs (Markdown).
4. Exporta a Word: el informe sale escrito sobre la hoja elegida.

### 1.3 Carpeta de plantillas
- Ubicación: `storage/plantillas_word/` (dentro del proyecto, junto a `storage/documentos/` y `storage/salidas/`).
- Créala si no existe. Antes de crearla, revisa cómo `app/rutas/documentos.py` define la ruta de `storage/` y usa la misma constante.
- Ejemplos actuales: `OficiosPlantilla1.docx` y `OficiosPlantilla2.docx` (ya sin texto, solo el membrete).

### 1.4 Decisión de diseño (obligatoria)
- **No rellenes placeholders.** Las hojas no tienen texto.
- **Trabaja siempre sobre una copia** de la plantilla.
- En la copia, **reemplaza el `w:body`** por el contenido generado.
- **Conserva intactos:** headers, footers, imágenes del membrete, relaciones (`word/_rels/`) y el `w:sectPr` de la plantilla. Modifica solo `word/document.xml`; el resto del zip se copia byte a byte (mismo principio que `roundtrip_docx.py` y `BytePreserver`).
- Para convertir el Markdown de Docs usa el motor existente (`motor/a_docx.py` / `converter.py`). No escribas un conversor nuevo.

---

## 2. FASE 0 — Lectura del código y diagnóstico

**Objetivo:** entender el flujo actual antes de tocar nada.

**Tareas**
1. Lee: `app/rutas/office.py`, `app/rutas/documentos.py`, `motor/a_docx.py`, `nucleo/docx_avanzado/` (`byte_preserver.py`, `converter.py`), `app/servicios/roundtrip_docx.py`, `templates/office.html` (sección `#sidebar-word-opciones`), `static/js/office.js`, `static/js/registro_temas.js`, `motor/registro_opciones.py` y `historial_de_versiones.md`.
2. Describe el flujo actual de exportación Word: qué endpoint recibe el Markdown, qué función genera el `.docx` y dónde se aplica la plantilla hoy (si es que se aplica).
3. Analiza un `.docx` de membrete leyendo su XML con `zipfile`: `word/document.xml` (sectPr, anclajes), `word/header*.xml`, `word/footer*.xml`, `word/_rels/document.xml.rels` y `word/media/`. Documenta:
   - tipo de anclaje de la imagen (`wp:anchor` o `wp:inline`);
   - `relativeFrom` y `posOffset` de `positionH` y `positionV`;
   - `wp:extent` (`cx`, `cy` en EMU);
   - `behindDoc` y tipo de envoltura;
   - márgenes del `sectPr` y si `titlePg` está activo;
   - si la imagen está en el header o en el cuerpo.

**Criterios de aceptación**
- [ ] Flujo actual descrito con nombres reales.
- [ ] Tabla con los datos del membrete de cada hoja de ejemplo.
- [ ] Lista de dudas o incoherencias encontradas.

---

## 3. FASE 1 — Carpeta y listado de plantillas

**Objetivo:** que el backend y el frontend conozcan las hojas disponibles.

**Backend (`app/rutas/office.py`)**
- `GET /api/office/plantillas-word`: devuelve la lista de `.docx` de `storage/plantillas_word/`, con:
  - `etiqueta`: nombre sin extensión (lo que ve el usuario);
  - `archivo`: nombre de archivo;
  - `tamano`: en KB legibles.
- Se lee la carpeta en cada llamada: las hojas nuevas aparecen sin reiniciar.
- Lista vacía si no hay archivos (no es un error).

**Seguridad**
- Cualquier nombre recibido en cualquier endpoint se valida contra la lista real de archivos.
- Solo se aceptan `.docx`.
- Aplica `resolve()` y `relative_to()`, igual que en `GET /api/office/pdfs/archivo/...`.
- Un nombre como `../version.py` responde 400 o 404.

**Frontend (`static/js/office.js`)**
- Al abrir la app y al pulsar "Actualizar lista", llama al endpoint y llena el combobox.
- Primera opción siempre: "Sin plantilla (predeterminada)".

**Criterios de aceptación**
- [ ] Carpeta vacía: solo aparece "Sin plantilla".
- [ ] Con varias hojas: aparece una opción por cada `.docx`.
- [ ] Nombre inventado o con `../` responde 400 o 404.
- [ ] Una hoja agregada a la carpeta aparece al actualizar, sin reiniciar la app.

---

## 4. FASE 2 — Análisis de la hoja y zona de escritura

**Objetivo:** calcular dónde puede escribirse el contenido sin tapar el membrete.

**Función nueva**: `analizar_membrete(ruta)` (en `motor/a_docx.py` o en un módulo nuevo `motor/membrete.py`, según la estructura real). Devuelve un diccionario con:

- `imagenes`: lista con:
  - `ubicacion`: `header`, `footer` o `cuerpo`;
  - `anclaje`: `anchor` o `inline`;
  - `relativeFrom` y `posOffset` para horizontal y vertical;
  - `ancho_cm` y `alto_cm` (a partir de `wp:extent`, 1 cm = 360000 EMU);
  - `behind_doc` (booleano);
  - `envoltura`: `none`, `square`, `topAndBottom` u otra.
- `margenes_cm`: top, bottom, left, right del `sectPr`.
- `titlePg`: booleano.
- `zona_sugerida_cm`: top, bottom, left, right.

**Reglas para `zona_sugerida_cm`**
- **Imagen anclada detrás del texto** (`behindDoc = 1`): la zona empieza debajo del borde inferior de la imagen más **0,5 cm** de margen de seguridad.
- **Imagen en línea o con envoltura** (`inline`, `square`, `topAndBottom`): su altura empuja la zona de escritura.
- **Imagen de página completa**: se usan los márgenes del `sectPr`.
- **Caso ambiguo**: no adivines. Propón una zona conservadora y avisa al usuario.
- **Membrete en el cuerpo y no en el header**: avisa. Solo aparecería en la primera página. Debe repetirse en todas: propón moverlo al header o marca la hoja como advertencia.

**Archivo de zona opcional**
- `Nombre.zona.json` junto a la plantilla, con `top`, `bottom`, `left`, `right` en cm.
- Si existe, se usa en lugar del análisis.
- Si no existe, el análisis se muestra en la tarjeta (Fase 5) y el usuario puede guardarlo.

**Aplicación de la zona**
- Se aplica como márgenes de la sección (`w:pgMar`) de la copia de trabajo.
- Evita espacios vacíos manuales al inicio del cuerpo salvo como último recurso.
- El **ancho útil** (ancho de página menos márgenes izquierdo y derecho) reemplaza los 6.20 in fijos de `_adaptar_ancho` en `motor/a_docx.py`, para tablas y figuras.

**Criterios de aceptación**
- [ ] Hoja con imagen de página completa: zona igual a los márgenes del `sectPr`.
- [ ] Hoja con banda superior: la zona empieza debajo de la banda más 0,5 cm.
- [ ] Hoja con banda superior e inferior: la zona queda entre ambas.
- [ ] Membrete en el cuerpo: se emite advertencia.
- [ ] Con `Nombre.zona.json` presente, se usa ese archivo y no el análisis.
- [ ] Tablas y figuras se calculan con el ancho útil de la hoja elegida.

---

## 5. FASE 3 — Reemplazo del cuerpo y generación del contenido

**Objetivo:** escribir el informe sobre la hoja, conservando el membrete.

**Pasos**
1. Crea una copia de la plantilla elegida en una carpeta temporal.
2. Abre la copia y lee `word/document.xml`.
3. Reemplaza todos los hijos de `w:body` **salvo el `w:sectPr` final**, por el contenido generado.
4. Aplica la zona de escritura (Fase 2) como márgenes de la sección.
5. Si hay datos del oficio (sección 6 de este prompt, pregunta 1), escríbelos como bloque antes del contenido.
6. Genera el contenido del Markdown de Docs con el motor de Word existente.
7. Guarda `word/document.xml` y reempaqueta el `.docx`. Todo lo demás del zip se copia byte a byte.

**Datos del oficio (si se usan)**
- Campos: ciudad, fecha, número de oficio, destinatario (`titulo_abbr`, `nombre_dest`, `cargo`), asunto, `firma_nombre`, `firma_cargo`.
- Fecha por defecto: la actual, en formato "30 de octubre de 2026".
- Si un dato obligatorio está vacío: escribe `[campo]` en rojo y añade un aviso en el panel de validación. No bloquees la generación.
- El número de oficio no se inventa: lo digita el usuario (ver pregunta 3).

**Criterios de aceptación**
- [ ] La salida no contiene restos del texto de la plantilla (la plantilla está vacía; comprobarlo).
- [ ] El membrete (header o imagen anclada) sigue presente en la salida.
- [ ] El contenido aparece en el orden del Markdown.
- [ ] Varios párrafos, una lista y una tabla se insertan sin perder formato.
- [ ] Salida reabierta con python-docx: `sectPr` y márgenes son los de la zona.

---

## 6. FASE 4 — Numeración de páginas y una sola sección

**Objetivo:** que la hoja se repita en todas las páginas y que pueda numerarse sin tapar el membrete.

**Una sola sección**
- La copia debe tener una sola sección. Si `titlePg` está activo, desactívalo para que el membrete se repita en todas las páginas.
- Si el membrete estaba solo en la primera página, avisa al usuario.

**Numeración (opcional, desactivada por defecto)**
- Opción en la tarjeta: "Numerar páginas", con posición `centro` o `derecha`.
- Formato: "Página X de Y", con los campos `PAGE` y `NUMPAGES`.
- **Caso A:** si la plantilla no tiene footer con contenido, crea un footer con la numeración en la posición elegida.
- **Caso B:** si el footer ya tiene contenido (gráfico o texto), **no lo sobrescribas**. Añade la numeración como párrafo al final del cuerpo, dentro del margen inferior reservado, y avisa.

**Criterios de aceptación**
- [ ] Informe de tres páginas: el membrete aparece en las tres.
- [ ] Con numeración activa, aparece "Página X de Y" y no tapa el membrete.
- [ ] Con numeración desactivada, la salida no contiene campos de página.
- [ ] Con footer existente, el footer original no cambia.

---

## 7. FASE 5 — Tarjeta de interfaz y exportación

**Objetivo:** que el usuario pueda elegir la hoja, revisar la zona y exportar.

**Tarjeta "Plantilla de hoja"** (en `#sidebar-word-opciones`, separada de las opciones de estilo)
- `<select id="word-plantilla-hoja">`: "Sin plantilla (predeterminada)" y una opción por cada `.docx`.
- Botón "Actualizar lista".
- Formulario "Datos del oficio" (opcional), guardado en `MFORegistro` (`registro_temas.js`).
- Checkbox "Numerar páginas" y selector de posición.
- Controles de zona: arriba, abajo, izquierda y derecha, en cm, prellenados con el análisis.
- Botón "Guardar zona": escribe `Nombre.zona.json` junto a la plantilla.
- Vista previa: una hoja con un rectángulo punteado de la zona de escritura. **No simules una vista previa real:** si no hay forma fiable de generar una imagen de la plantilla, muestra solo el rectángulo y el nombre.

**Exportación (`POST /api/office/exportar-docx`)**
- Campos nuevos, además de los actuales:
  - `plantilla_word` (nombre de archivo);
  - `datos_oficio` (objeto, opcional);
  - `numerar_paginas` (booleano);
  - `posicion_numero` (`centro` o `derecha`);
  - `zona` (opcional; si no se envía, se usa el análisis o el `.zona.json`).
- Valida `plantilla_word` contra la lista real.
- Si `plantilla_word` está vacío, mantiene el flujo predeterminado actual, sin cambios.

**Criterios de aceptación**
- [ ] Seleccionar una hoja actualiza la vista previa de la zona.
- [ ] "Guardar zona" crea `Nombre.zona.json` y la siguiente exportación lo usa.
- [ ] Exportar sin plantilla produce el mismo resultado que antes de este cambio.
- [ ] Exportar con plantilla produce un `.docx` con el membrete.

---

## 8. FASE 6 — Versión y pruebas

**Versión:** MINOR, sugerida **v1.21.0**. Actualiza `app/version.py` (SSOT), agrega la entrada en `historial_de_versiones.md` con el formato del proyecto y actualiza `README.md` y `interfaces/mcp/server.json`.

**Pruebas** (en `pruebas/test_v1_21_0.py`):
1. Lista vacía devuelve solo "Sin plantilla".
2. Nombre inventado o con `../` responde 400 o 404.
3. Análisis de hoja de página completa: zona igual a los márgenes del `sectPr`.
4. Análisis de hoja con banda superior: zona debajo de la banda más 0,5 cm.
5. Membrete en el cuerpo: se emite advertencia.
6. Reemplazo del cuerpo: no quedan restos de la plantilla y el membrete sigue en la salida.
7. Contenido con varios párrafos, lista y tabla: orden y formato conservados.
8. Dato obligatorio vacío: `[campo]` en rojo y aviso.
9. Salida reabierta con python-docx: membrete presente, márgenes de la zona, `titlePg` desactivado.
10. Informe de tres páginas: membrete en las tres.
11. Numeración "Página X de Y" presente y sin tapar el membrete.
12. Exportación sin plantilla idéntica a la anterior (regresión).
13. Consola del navegador y logs del servidor sin errores.

**Criterios de aceptación**
- [ ] Suite completa en verde.
- [ ] Revisión manual en Word real de al menos dos hojas de la carpeta.

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

## 10. Preguntas que la IA debe hacer si no puede decidir

1. **Datos del oficio:** ¿la app escribe ciudad, número, destinatario, asunto y firma como bloque antes del contenido, o solo va el contenido de Docs?
2. **Zona:** ¿se calcula siempre automáticamente, o el usuario la confirma en cada hoja?
3. **Número de oficio:** ¿lo digita el usuario, o debe generarse de forma correlativa y guardarse?
4. **Footer gráfico:** si una hoja tiene footer con imagen o texto, ¿la numeración va en el cuerpo (Caso B) o se omite con aviso?
5. **Membrete en el cuerpo:** si una hoja tiene la imagen en el cuerpo y no en el header, ¿se corrige automáticamente o solo se avisa?
