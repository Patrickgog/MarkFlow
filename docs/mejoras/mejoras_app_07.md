# PROMPT v2 — Rediseño de exportación en Markflow Office: documento único, pestañas de formato con barra lateral

Copia este documento completo en tu asistente de IA (Claude, ChatGPT, Cursor, etc.) y pídele que lo ejecute. **Antes de escribir código, revisa el proyecto real.** No inventes nombres de archivos, funciones ni endpoints.

---

## 0. Reglas para la IA

1. **Analiza primero, después programa.** Lo primero es leer el código de la pestaña **MarkFlow Conversión Completa**, en sus subpestañas **Temas HTML**, **Temas Word** y **Opciones de Formato** (con sus sub-paneles Word, HTML y PDF). Esa es la **única fuente válida** de temas y opciones. Entrega un inventario (sección 3) antes de tocar código.
2. **Un solo registro de temas.** Extrae las opciones de esas subpestañas a **un único registro** (JSON, diccionario o módulo). Todas las pestañas de formato leen de ese registro. No puede haber listas de temas escritas a mano en otro lugar. Elimina las listas duplicadas que encuentres.
3. **Un solo contenido.** El documento se edita en la pestaña **Docs**. Las pestañas Word, HTML, PDF y Excel **muestran** ese mismo documento; no tienen editor propio.
4. **Una sola función de render por formato.** La vista previa y el archivo exportado deben salir del **mismo** generador. Si la vista previa y el archivo final difieren, es un error.
5. **No cambies la lógica que ya funciona**: ingesta de archivos, detección de codificación, sintaxis de fórmulas, numeración de capítulos, firma e índice al final.
6. **Estilo visual vigente**: IBM Plex Sans, paleta índigo → violeta, tarjetas `.tarjeta`, botones `.btn`, chips `.chip`, modo claro y oscuro. Sin CDNs externos: la app funciona 100 % offline.
7. **Librerías nuevas**: pide aprobación antes de instalar cualquiera, con su justificación.
8. **Idioma**: todos los textos de interfaz, nombres de temas y mensajes en español.
9. Si algo no está claro, **pregunta antes de asumir**. Al final entrega el reporte de la sección 12.

---

## 1. Estructura de pestañas que debe quedar

| Pestaña | Función |
| --- | --- |
| **Docs** | Editor del documento: pegar o escribir Markdown, cargar archivos, insertar imágenes, configurar la ventana de conversión inicial. Es el **único lugar donde se edita el contenido**, proviene de pestaña Documentos |
| **Word** | Vista previa paginada del documento en formato `.docx`, con **barra lateral derecha deslizable** y exportación. |
| **HTML** | Vista previa del `.html` con **barra lateral derecha deslizable** y exportación. |
| **PDF** | Vista previa del `.pdf` con **barra lateral derecha deslizable** y exportación. |
| **Excel** | Tablas del documento con **barra lateral derecha deslizable**, exportación a `.xlsx` y copia con formato. Solo se habilita si el documento contiene tablas. |
| **Entregables** | **Pestaña dedicada** (no dentro de otra). Lista de todos los archivos generados en la sesión, con Ver y Descargar. |
| **MarkFlow Conversión Completa** | Pestaña de referencia (última vertical de la app). Contiene las subpestañas Temas HTML, Temas Word y Opciones de Formato, que alimentan el registro único. Se conserva como está. |
| **Manual de Usuario** | Se conserva. |

Nota: la pestaña **Ventana Conversión y Exploración** actual (que hoy vive dentro de Docs) se **reemplaza** por las barras laterales de cada pestaña de formato. Dentro de Docs solo debe quedar lo necesario para editar y cargar contenido.

---

## 2. Principio de funcionamiento

```
Docs (edición del Markdown)
   │
   ├── Word   → barra lateral (opciones Word)  → vista previa paginada → exportar .docx
   ├── HTML   → barra lateral (opciones HTML)  → vista previa HTML      → exportar .html
   ├── PDF    → barra lateral (opciones PDF)   → vista previa PDF       → exportar .pdf
   └── Excel  → barra lateral (opciones tablas)→ vista de tablas        → exportar .xlsx / copiar con formato
                                                       │
                                                       ▼
                                          Entregables (archivos generados)
```

Reglas del flujo:
- Cada pestaña de formato tiene **su propia** barra lateral, con **sus propias** opciones, leídas del registro único.
- Cada cambio en una barra lateral regenera la vista previa de **esa** pestaña en tiempo real (retardo de 300 ms para no saturar).
- Las selecciones de cada formato se **conservan** al cambiar de pestaña y durante la sesión.
- Exportar desde la barra lateral genera el archivo con **exactamente** lo que se ve en la vista previa.
- Cada archivo exportado se registra en **Entregables**.

---

## 3. Paso obligatorio: inventario de la pestaña MarkFlow Conversión Completa

Antes de programar, lee y documenta el código de estas subpestañas y entrega esta tabla. **No cambies el orden ni los nombres de las opciones.**

### 3.1 Temas HTML

Plantilla de tema HTML · Paleta paletas, anchos, formatos, deben venir desde la pestaña MarkFlow Conversión Completa

### 3.2 Temas Word

Plantilla formal Word (.docx) · aleta paletas, anchos, formatos, deben venir desde la pestaña MarkFlow Conversión Completa

### 3.3 Opciones de Formato
- **Sub-panel Word (.docx)**: fuente del documento · tamaño de fuente · interlineado · alineación · fuente en cuadros y tablas · alto de fuente en tablas · pie de página personalizado · alineación del pie · numerar ecuaciones · normas APA 7 · creación de índice (TOC e índice de ecuaciones, con ubicación) · numerar páginas.
- **Sub-panel HTML (.html)**: familia tipográfica · tamaño base · interlineado · pie izquierdo · pie derecho · texto justificado · numeración de ecuaciones.
- **Sub-panel PDF (.pdf)**: paleta editorial · estilo de maquetación · modo de columnas · fuente · tamaño · interlineado · pie de página · alineación del pie · salto de página en capítulos · texto justificado · numerar páginas · running header (y su texto) · configurar firma al final · configurar índice al final (con enlaces) · formato de numeración (Página X de Y / X / Y / solo número) · alineación del número.

Entrega la tabla con: **control**, **id del elemento**, **valores posibles**, **valor por defecto**, **formato al que aplica**. Después, crea el registro único a partir de esa tabla.

---

## 4. Barra lateral de cada pestaña de formato

### 4.1 Comportamiento común

- Ubicada a la **derecha**, con ancho aproximado de 340 px.
- **Deslizable**: se oculta y reaparece con un botón (ícono de panel o de engranaje) fijo en el borde derecho. Al ocultarse, la vista previa ocupa el ancho completo. La animación debe ser de 250 ms, respetando `prefers-reduced-motion`.
- Estado de visible u oculta **recordado por pestaña** durante la sesión.
- Encabezado de la barra: título "Opciones de [formato]" y un botón de cierre.
- Agrupa los controles en **secciones colapsables** (por ejemplo: Tipografía, Tablas, Página, Pie y numeración, Avanzado).
- Al pie de la barra: botón primario **Exportar [formato]** y botón secundario **Restablecer valores**.
- Los controles usan los estilos ya existentes (`.controles-grid`, `select`, `input[type="text"]`, `.casilla`).
- Cada cambio se refleja en la vista previa **en tiempo real**.

### 4.2 Contenido de cada barra

- **Barra Word**: plantilla y paleta de tablas, color de títulos (solo si la plantilla es personalizada; si no, se muestra el aviso de tema nativo), fuente, tamaño, interlineado, alineación, fuente y tamaño de tablas, pie y alineación del pie, numeración de páginas, APA 7, índice (con ubicación), numeración de ecuaciones.
- **Barra HTML**: plantilla, paleta tricolor, ancho máximo de lectura, familia tipográfica, tamaño base, interlineado, pies izquierdo y derecho, justificado, numeración de ecuaciones.
- **Barra PDF**: paleta editorial, estilo, modo de columnas, fuente, tamaño, interlineado, pie y alineación, salto de capítulos, justificado, numerar páginas, running header, botones de firma e índice al final, formato y alineación del número.
- **Barra Excel**: combobox de **estilo y paleta de tablas** (lista de la paleta suave del registro), fuente y tamaño de tablas, modo de hoja (una hoja por tabla o todas en una hoja).

---

## 5. Pestaña Docs (edición)

- Mantiene el editor Markdown actual, la carga de archivos (`.md`, `.docx`, `.pdf`), las casillas de modo capítulos y salto de página, y el historial de documentos.
- Se **quita** de aquí la configuración de formatos: ahora vive en cada barra lateral.
- Mantiene el botón de formatear, limpiar y el visor flotante.
- El contenido de Docs es la **fuente única**. Cada pestaña de formato lo toma en vivo.

### 5.1 Imágenes

1. El botón **Imagen** pega una imagen desde el portapapeles (Ctrl+V o desde el botón).
2. También permite **subir una imagen desde una carpeta** del equipo con un selector de archivos.
3. Al insertarla, se escribe en el texto la referencia:
   ```
   ![Descripción breve][img-1]
   ```
4. La definición real se agrega **al final del documento**:
   ```
   [img-1]: data:image/png;base64,iVBORw0KGgo...
   ```
5. Varias imágenes se numeran en orden: `img-1`, `img-2`, `img-3`…
6. Formatos aceptados: PNG, JPG y GIF. Otro formato → aviso en español.
7. Imagen de más de 5 MB → reducirla o avisar.
8. Sin imagen en el portapapeles → "No hay una imagen en el portapapeles. Copia una imagen y vuelve a intentarlo."
9. El texto alternativo toma el nombre del archivo; si no existe, queda `Imagen N`.
10. Las definiciones sin referencia en el texto **no se exportan**.
11. Antes de implementar, revisa cómo funciona hoy la inserción de imágenes en la pestaña de conversión completa y mantén ese mismo comportamiento.

---

## 6. Pestaña Word

### 6.1 Vista previa
- Muestra **todas las páginas** del documento, en vertical, con separación visible entre hojas y número de página.
- Usa dimensiones reales de página (A4 o carta según el tema), márgenes (APA 7 usa 2.54 cm), fuente, tamaño, interlineado y alineación elegidos.
- Puede implementarse convirtiendo el `.docx` a PDF y mostrando las páginas, o con un render paginado que replique el mismo modelo. Elige la opción viable en este equipo y justifícala.
- Se regenera al cambiar cualquier control de la barra Word.

### 6.2 Exportación
- El `.docx` debe contener **todo** el contenido de Docs: títulos, párrafos, listas, tablas, imágenes, fórmulas y notas.
- Aplica las opciones de la barra: tema, fuente, tamaño, interlineado, alineación, pie, numeración, APA 7, índice, numeración de ecuaciones.
- Nombre del archivo: el que venga del campo de nombre (o automático seguro), con extensión `.docx`.
- Registra el archivo en Entregables.

### 6.3 Documento vacío (diagnóstico obligatorio)
Hoy el `.docx` sale vacío. Antes de corregir, identifica la causa exacta: contenido no pasado al generador, texto no convertido a párrafos, error silencioso u otra. Explícala en el reporte.

---

## 7. Pestaña HTML

- Vista previa en tiempo real con el HTML renderizado según las opciones de la barra: tema, paleta tricolor, ancho, tipografía, tamaño, interlineado, justificado, pies y numeración de ecuaciones. Las fórmulas se renderizan.
- Debe mostrar el **documento de Docs**, nunca contenido de ejemplo.
- La descarga entrega un `.html` **completo y autónomo**, con estilos incrustados, sin depender de archivos externos.
- Registra el archivo en Entregables.

---

## 8. Pestaña PDF

### 8.1 Problemas actuales
- No muestra ningún documento en pantalla.
- Al descargar, el archivo sale como `descargar.htm`.

### 8.2 Requisitos
- **Visor**: muestra el PDF real generado con las opciones de la barra PDF (paleta, maquetación, columnas, fuente, pie, numeración, running header, firma e índice). Se regenera al cambiar opciones.
- Si el generador de PDF no está disponible, muestra un mensaje claro en español, no una pantalla vacía.
- **Descarga**: archivo `.pdf` con nombre correcto, `Content-Type: application/pdf` y `Content-Disposition: attachment; filename="..."`.
- Diagnostica por qué sale `.htm` (probablemente se sirve HTML con nombre o tipo incorrecto) y explícalo antes de corregir.
- Registra el archivo en Entregables.

---

## 9. Pestaña Excel

- Solo se habilita si el documento contiene tablas. Si no hay tablas, muestra un mensaje: "Este documento no tiene tablas."
- **Vista en pantalla**: cada tabla se muestra renderizada con el estilo elegido (cabecera de color, filas alternas, bordes), y se actualiza al cambiar el combobox de la barra Excel.
- **Exportar `.xlsx`**: cabecera con el color de la paleta en negrita, filas alternas, bordes y ancho de columnas según el contenido, y fuente de tablas del registro. Una hoja por tabla, o todas en una hoja, según el modo elegido.
- **Copiar con formato**: copia al portapapeles el HTML con estilos en línea (colores, negritas, bordes, fuente) y una versión de texto plano como respaldo. Debe pegarse en Excel y Word conservando el formato.
- Registra el archivo en Entregables.

---

## 10. Pestaña Entregables

- Pestaña propia en la barra principal.
- Lista todos los archivos generados en la sesión, en orden del más reciente al más antiguo.
- Cada entrada muestra: formato con su color (Word azul, PDF rojo, HTML naranja, Excel verde, Markdown verde claro), nombre, tamaño, fecha y hora.
- Botones por entrada: **Ver** (abre la vista previa en el visor) y **Descargar** (con nombre y extensión correctos).
- Botón **Limpiar lista** que quita las entradas de la sesión sin borrar archivos del disco.

---

## 11. Criterios de aceptación

- [ ] Existe un único registro de temas, alimentado desde Temas HTML, Temas Word y Opciones de Formato.
- [ ] Ninguna lista de temas existe fuera de ese registro.
- [ ] Cada pestaña de formato (Word, HTML, PDF, Excel) muestra el documento de Docs.
- [ ] Cada pestaña de formato tiene su barra lateral derecha deslizable, que se oculta y reaparece.
- [ ] Los controles de cada barra coinciden con los de la pestaña de conversión completa.
- [ ] Cada cambio se refleja en la vista previa en menos de 300 ms tras dejar de editar el control.
- [ ] Las selecciones de cada formato se conservan al cambiar de pestaña.
- [ ] La vista previa Word muestra todas las páginas.
- [ ] El `.docx` exportado contiene todo el contenido de Docs (no sale vacío).
- [ ] El visor PDF muestra el resultado configurado y la descarga es `.pdf`.
- [ ] El visor HTML muestra el documento y se actualiza con las opciones.
- [ ] La pestaña Excel muestra las tablas con el estilo elegido y exporta `.xlsx` con esos estilos.
- [ ] Copiar tablas pega con formato en Excel y Word.
- [ ] Entregables es una pestaña propia y lista todos los archivos generados.
- [ ] Las imágenes se pegan desde portapapeles o se suben desde carpeta, y se exportan.
- [ ] Modo claro y oscuro funcionan en todas las pestañas.
- [ ] Sin errores en la consola del navegador ni en el servidor.

---

## 12. Pruebas obligatorias y reporte

### 12.1 Pruebas
1. Documento de prueba con título, párrafo, tabla e imagen.
2. Cambiar una opción en cada barra lateral y verificar que la vista previa cambia.
3. Ocultar y mostrar cada barra lateral.
4. Exportar Word, PDF, HTML y Excel del mismo documento; abrir cada archivo y comprobar texto, tabla e imagen.
5. Copiar una tabla con formato y pegarla en Excel.
6. Cambiar de pestaña, volver, y confirmar que las selecciones persisten.

### 12.2 Reporte que debe entregar la IA
1. **Inventario** de la pestaña MarkFlow Conversión Completa (sección 3).
2. **Diagnóstico** de: documento Word vacío, descarga `.htm` en PDF, visor HTML sin cambios, visor PDF sin contenido.
3. **Archivos creados y modificados**, con su función.
4. **Ruta del registro único** y cómo lo consumen las pestañas.
5. **Endpoints nuevos o modificados** del servidor.
6. **Dependencias nuevas** con justificación, o confirmación de que no hacen falta.
7. **Resultado de las pruebas** (12.1).
8. **Pendientes** y preguntas.

---

## 13. Preguntas que la IA debe hacer si no puede resolver algo

1. ¿Qué archivo del servidor genera `.docx`, `.pdf` y `.html`, y qué librerías usa?
2. ¿Hay LibreOffice u otro conversor disponible para la vista previa de Word y PDF?
3. ¿Se aprueba instalar `openpyxl` (Excel) y `python-docx` (Word), si no existen?
4. ¿El servidor guarda los archivos generados en disco? ¿En qué carpeta?
5. ¿El editor de Docs es un `textarea` o un componente propio? Esto define cómo se sincroniza con las pestañas de formato.
