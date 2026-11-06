# PROMPT POR FASES — Correcciones integrales de Markflow Office

 ejecútalo **fase por fase**. No avances a la siguiente fase hasta que la anterior cumpla sus criterios de aceptación y entregues el reporte de esa fase. Una sola instrucción para todo fallaría: por eso el trabajo está dividido.

---

## 0. Reglas generales (aplican a todas las fases)

1. **Analiza antes de programar.** En cada fase, primero lee el código relacionado y describe lo que encontraste. No inventes nombres de archivos, funciones, endpoints ni clases.
2. **No rompas lo que funciona.** Ingesta de archivos, detección de codificación, sintaxis de fórmulas, numeración de capítulos, firma e índice al final, visor flotante y la pestaña **MarkFlow Conversión Completa** se conservan. Esa pestaña es la **fuente de verdad** de temas y opciones.
3. **Un solo registro de temas.** Todas las listas de paletas, plantillas, tipografías y opciones salen del registro único creado en la Fase 2. Ninguna pestaña escribe listas a mano.
4. **Un solo renderizador por elemento.** Mermaid, fórmulas KaTeX e imágenes se renderizan con **una única** función compartida por todas las pestañas. La vista previa y el archivo exportado usan el mismo resultado.
5. **Vista en vivo.** Todo cambio en un control de cualquier barra lateral se refleja en la vista previa en menos de 300 ms (con retardo para no saturar al escribir).
6. **Estilo vigente.** IBM Plex Sans, paleta índigo → violeta, tarjetas `.tarjeta`, botones `.btn`, chips `.chip`, modo claro y oscuro. Sin CDNs: la app funciona 100 % offline. Si Mermaid o KaTeX ya están en el proyecto, reutilízalos; si no, pide aprobación para incorporarlos localmente.
7. **Librerías nuevas**: pide aprobación con justificación antes de instalar.
8. **Idioma**: todo en español (interfaz, nombres, mensajes).
9. **Reporte por fase**: al terminar cada fase, entrega el reporte de la sección 11 y espera confirmación antes de seguir.

---

## FASE 0 — Diagnóstico (sin cambiar código)

**Objetivo:** entender el estado real de la app antes de tocar nada.

1. Lista el árbol del proyecto (sin `node_modules`, `venv` ni binarios).
2. Identifica: archivo del servidor, archivo principal de frontend, módulos de exportación (Word, PDF, HTML, Excel), y dónde están las listas de temas hoy.
3. Localiza el código de **MarkFlow Conversión Completa** → subpestañas **Temas HTML**, **Temas Word** y **Opciones de Formato** (sub-paneles Word, HTML y PDF). Entrega un inventario: control, id, valores posibles, valor por defecto y formato al que aplica.
4. Localiza dónde se llama a Mermaid y a KaTeX hoy (si existen). Indica por qué dejaron de renderizar en algunas pestañas.
5. Explica la causa probable de estos síntomas (no los corrijas todavía):
   - Word se queda en "Cargando maquetación de Word…".
   - El `.docx` sale vacío.
   - El PDF se descarga como `.htm`.
   - Excel muestra fórmulas KaTeX como símbolos raros.
   - Las opciones de numeración de ecuaciones y de índice no hacen efecto.
   - El footer HTML está codificado en duro.

**Criterios de aceptación de la fase:**
- [ ] Inventario completo de las tres subpestañas.
- [ ] Causa identificada para cada síntoma de la lista.
- [ ] Lista de archivos que se van a modificar en las siguientes fases.

---

## FASE 1 — Pestaña Docs (edición del documento)

**Objetivo:** Docs es la fuente única del contenido. Debe permitir renombrar, guardar, insertar imágenes que se vean y renderizar diagramas Mermaid.

### 1.1 Problemas que corregir
- No se puede editar el título del documento ni guardarlo con otro nombre.
- Al insertar una imagen no se ve renderizada.
- Los diagramas Mermaid no se renderizan (antes sí funcionaban).

### 1.2 Requisitos

**Título y guardado**
- Campo de **título** editable en la parte superior de Docs.
- Botón **Guardar como…** que pide un nombre nuevo (con validación de caracteres no válidos) y guarda el documento con ese nombre en la lista de documentos.
- Botón **Guardar** que actualiza el nombre actual.
- El título se usa como nombre por defecto de los archivos exportados.

**Imágenes**
- El botón **Imagen** pega desde el portapapeles (Ctrl+V o botón) o sube un archivo desde una carpeta del equipo.
- Inserta en el texto `![Descripción breve][img-N]` y agrega al final del documento `[img-N]: data:image/png;base64,...`.
- En Docs, la imagen debe **verse renderizada** en la vista previa del editor, no solo como texto.
- Formatos aceptados: PNG, JPG, GIF. Otros → aviso en español. Más de 5 MB → reducir o avisar.
- Las definiciones sin referencia en el texto no se exportan.

**Mermaid**
- Los bloques ```` ```mermaid ```` se renderizan como diagramas en Docs.
- El renderizado debe ser el **mismo** que usarán las demás pestañas (Word, HTML, PDF y Excel si aplica).
- Si la sintaxis tiene errores, muestra el error en español junto al bloque, no una pantalla vacía.
- Caso de prueba obligatorio: el diagrama del **Anexo A** debe verse completo, con sus colores de `classDef` y sus nodos con formas, en Docs.

### 1.3 Criterios de aceptación
- [ ] El título es editable y se puede guardar con otro nombre.
- [ ] Una imagen pegada o subida se ve en la vista previa de Docs.
- [ ] El diagrama del Anexo A se renderiza en Docs con sus colores.
- [ ] Un error de sintaxis Mermaid muestra un mensaje claro, no se rompe la página.

---

## FASE 2 — Registro único de temas y barra lateral reutilizable

**Objetivo:** crear las dos piezas comunes que usarán todas las pestañas de formato: el registro único de temas y el componente de barra lateral.

### 2.1 Registro único de temas
- Crea un único archivo (JSON, diccionario o módulo) con todas las opciones extraídas en la Fase 0 de Temas HTML, Temas Word y Opciones de Formato.
- Cada entrada contiene: id, etiqueta en español, valores posibles y valor por defecto.
- Las paletas se definen como **listas de colores** (no solo nombres), para que la vista previa y la exportación usen los mismos códigos.
- MarkFlow Conversión Completa debe leer del mismo registro.
- Elimina listas duplicadas en el resto de pestañas.

### 2.2 Componente de barra lateral reutilizable
- Barra lateral **derecha**, deslizable: se oculta y reaparece con un botón fijo en el borde derecho. Animación de 250 ms; respeta `prefers-reduced-motion`.
- **Todas las secciones (sliders) cerradas por defecto.**
- **Acordeón exclusivo**: al abrir una sección, las demás se cierran.
- **Altura automática**: cada sección abierta muestra todo su contenido sin cortar controles ni necesitar desplazamiento interno. Sin alturas fijas.
- Encabezado con título de la barra y botón de cierre. Pie con **Exportar** y **Restablecer valores**.
- Estado (visible/oculta y sección abierta) recordado por pestaña durante la sesión.
- Ninguna sección se cierra al cambiar un control dentro de ella.

### 2.3 Componente de selector de color visual (clave para las paletas personalizadas)
- El usuario **no escribe códigos de color**. Debe elegir con una **vista real de colores**: muestra de cuadros de color, un selector de matiz/saturación/brillo y una vista previa del color elegido.
- Puede guardar una paleta personalizada con nombre, de 2 a 6 colores.
- Esta pieza se usa en Word (títulos y tablas), PDF, HTML (tricolor) y Excel.

### 2.4 Criterios de aceptación
- [ ] Existe un único registro; ninguna pestaña tiene listas propias.
- [ ] La barra lateral se oculta y reaparece.
- [ ] Solo una sección abierta a la vez; todas cerradas al inicio.
- [ ] Las secciones muestran todo su contenido sin recortes.
- [ ] El selector de color visual funciona sin escribir códigos.

---

## FASE 3 — Pestaña Word

**Objetivo:** que Word muestre el documento renderizado, con paletas visibles y opciones que sí cambian el resultado.

### 3.1 Problemas que corregir
1. Se queda en "Cargando maquetación de Word…" y nunca muestra el documento.
2. Plantilla formal Word: falta la separación en dos paletas y la personalización visual.
3. Slider **Estructura y APA**: al activar numeración de ecuaciones, las fórmulas no se numeran (solo aparecen los paréntesis `()`).
4. Slider **Estructura y APA**: al activar el índice, el índice no aparece.
5. Slider **Round-trip.docx**: el diagrama Mermaid no se renderiza.
6. Se debe diagnosticar por qué el `.docx` sale vacío (ver Fase 0).

### 3.2 Requisitos

**Vista previa**
- Muestra todas las páginas del documento renderizado. Se elimina la pantalla de carga que no termina; si la maquetación falla, muestra el error en español.
- Se actualiza en vivo con cada control.
- Mermaid y fórmulas se ven como en Docs.

**Plantilla formal y paletas (dentro de su slider)**
- **Dos paletas** claramente separadas:
  1. **Paleta de títulos y encabezados**.
  2. **Paleta de cuadros y tablas**.
- Cada paleta incluye:
  - Paletas predeterminadas del registro.
  - Una **paleta personalizada** con el selector visual de la Fase 2.3.
- Distribución ordenada dentro del slider: un bloque por paleta, con sus opciones en fila, sin cortes.
- Los cambios se ven **inmediatamente** en la vista previa.

**Estructura y APA**
- **Numeración de ecuaciones**: solo se numeran las fórmulas que el algoritmo detecta como bloque de ecuación (`$$ ... $$`, `\[ ... \]`). Las demás no reciben número. Cada fórmula numerada muestra su número alineado a la derecha, por ejemplo `(1)`, `(2)`.
- **Índice**: al activarlo, el índice aparece en el documento en la ubicación elegida (inicio o final) con sus entradas y números de página.
- **Round-trip.docx**: el diagrama Mermaid debe renderizarse.

### 3.3 Criterios de aceptación
- [ ] La vista previa Word carga y muestra todas las páginas.
- [ ] Las dos paletas están separadas y cada una tiene una personalizada visual.
- [ ] Los cambios de paleta se ven al instante.
- [ ] La numeración de ecuaciones numera solo las fórmulas detectadas como bloque.
- [ ] El índice aparece cuando se activa.
- [ ] Mermaid se renderiza en la vista previa y en el `.docx`.
- [ ] El `.docx` exportado contiene todo el contenido (no sale vacío).

---

## FASE 4 — Pestaña PDF

**Objetivo:** vista previa con miniaturas, paletas personalizables y numeración de páginas con varias presentaciones.

### 4.1 Problemas que corregir
1. Falta el panel de miniaturas a la izquierda.
2. La paleta editorial solo tiene predeterminadas; no se puede personalizar.
3. La numeración anticolisión solo ofrece un formato (`1/20`).

### 4.2 Requisitos

**Vista previa**
- Visor del PDF renderizado en vivo.
- **Panel izquierdo de miniaturas** de todas las hojas. Clic en una miniatura lleva a esa hoja en el visor.
- Se actualiza al cambiar cualquier control.

**Paleta editorial**
- Paletas predeterminadas del registro, más una **paleta personalizada** con el selector visual (Fase 2.3).
- La personalizada se ve en la vista previa y en la descarga.

**Numeración de páginas**
Ofrece al menos estas presentaciones:
- `Página X de Y` (ej. Página 1 de 20)
- `X / Y` (ej. 1 / 20)
- `X` (solo número)
- `X de Y` (ej. 1 de 20)
- `Pág. X` (ej. Pág. 1)
- Números romanos para portada y numeración arábiga para el cuerpo, con opción de activar o no
- Alineación: izquierda, centro o derecha
- Con o sin ceros a la izquierda (`01`, `02`…)

Todas las opciones se reflejan en la vista previa y en el PDF descargado.

### 4.3 Descarga
- Archivo `.pdf` con el nombre del documento.
- `Content-Type: application/pdf` y `Content-Disposition: attachment`.
- El problema de `descargar.htm` se corrige según el diagnóstico de la Fase 0.

### 4.4 Criterios de aceptación
- [ ] Las miniaturas aparecen a la izquierda y navegan a cada hoja.
- [ ] La paleta personalizada funciona en vista previa y en el PDF descargado.
- [ ] Hay al menos seis formatos de numeración y todos se ven en vivo.
- [ ] La descarga es `.pdf` con el nombre del documento.

---

## FASE 5 — Pestaña HTML

**Objetivo:** Mermaid renderizado, paleta tricolor personalizable, tipografía y ecuaciones que sí cambian, y pie de página editable.

### 5.1 Problemas que corregir
1. Mermaid no se renderiza en la vista previa (debe verse como en Docs).
2. La paleta tricolor no permite personalizar colores.
3. En **Diseño y lectura**, cambiar el tipo de letra no cambia la vista previa ni la exportación.
4. La numeración de ecuaciones no funciona.
5. En **Encabezado y pie**, cambiar el texto del footer no cambia el HTML: está codificado en duro.

### 5.2 Requisitos
- **Mermaid**: se renderiza con el mismo renderizador compartido de la Fase 1.
- **Paleta tricolor**: paletas predeterminadas más una personalizada con el selector visual.
- **Tipografía**: el cambio de familia, tamaño e interlineado se refleja en vivo en la vista previa y en el `.html` descargado.
- **Numeración de ecuaciones**: solo las ecuaciones de bloque se numeran (igual que Word), y el número aparece en vista previa y en el `.html`.
- **Pie de página**: los textos izquierdo y derecho son los que el usuario escribe en los campos. Al cambiarlos, la vista previa y el `.html` se actualizan. Ningún texto de pie debe estar fijo en el código.
- La descarga es un `.html` completo y autónomo, con estilos incrustados.

### 5.3 Criterios de aceptación
- [ ] Mermaid se ve en la vista previa HTML.
- [ ] La paleta tricolor tiene personalizada visual.
- [ ] Cambiar la tipografía se ve en vivo y en el archivo.
- [ ] La numeración de ecuaciones funciona en vista previa y en el archivo.
- [ ] Cambiar el pie de página se refleja en vivo y en el archivo.

---

## FASE 6 — Pestaña Excel

**Objetivo:** las tablas se ven y se exportan con fórmulas legibles, paletas en vivo, dimensiones respetadas y modo de hojas funcional.

### 6.1 Problemas que corregir
1. Las fórmulas se ven como KaTeX crudo (símbolos raros), tanto en la vista previa como en el archivo.
2. La paleta no se ve en la vista previa.
3. La paleta no se respeta al exportar.
4. Dimensiones y fuentes: el ancho de columnas y el tamaño de letra no se respetan.
5. Libro y escritura: el modo "una tabla por hoja" o "todas en una hoja" no se respeta; siempre sale una tabla en una hoja.
6. El ajuste de texto en celdas no funciona.

### 6.2 Requisitos

**Fórmulas**
- Las fórmulas se convierten a un **valor legible** antes de exportar: en celda, texto plano con la notación traducida (ejemplo: `x^2` → `x²`, `\frac{a}{b}` → `a/b`). Si una fórmula no se puede traducir, se muestra en texto plano limpio, sin comandos de LaTeX.
- La vista previa y el archivo muestran el mismo texto.

**Vista previa en vivo**
- Muestra cada tabla con la paleta elegida (cabecera, filas alternas, bordes).
- Cambiar la paleta, el ancho de columnas, el tamaño de fuente o el ajuste de texto se refleja al instante.
- Paleta personalizada con el selector visual (Fase 2.3).

**Dimensiones y fuentes**
- Ancho de columna: automático por contenido o manual por columna.
- Tamaño de fuente: el elegido se aplica a la vista previa y al `.xlsx`.
- Ajuste de texto en celdas: cuando está activo, el texto largo se envuelve dentro de la celda (en el archivo, con la propiedad de ajuste de texto de Excel; en la vista previa, con salto de línea).

**Libro y escritura**
- **Una tabla por hoja** o **todas las tablas en una hoja** (con separación de filas entre tablas y su título).
- El modo elegido debe respetarse al exportar y reflejarse en la vista previa.

**Exportación**
- `.xlsx` con la paleta, fuente, ancho, ajuste y modo de hojas elegidos.
- Copiar con formato: HTML con estilos en línea y texto plano de respaldo.

### 6.3 Criterios de aceptación
- [ ] Ninguna fórmula aparece como KaTeX crudo en vista previa ni en el `.xlsx`.
- [ ] La paleta cambia en vivo en la vista previa y se respeta en el `.xlsx`.
- [ ] Existe una paleta personalizada visual.
- [ ] El ancho de columnas y el tamaño de fuente se respetan.
- [ ] El modo de hojas se respeta (una hoja por tabla o todas en una).
- [ ] El ajuste de texto funciona.

---

## FASE 7 — Pestaña Entregables

**Objetivo:** ordenar las tarjetas de archivos generados por tipo, en formato horizontal.

### 7.1 Problema
El historial de archivos se muestra desordenado.

### 7.2 Requisitos
- Agrupa las tarjetas **por tipo de archivo**: Word, PDF, HTML, Excel, Markdown.
- Cada grupo es una **fila horizontal** con su encabezado (tipo y cantidad), y las tarjetas se desplazan horizontalmente si hay muchas.
- Cada tarjeta muestra: nombre, tamaño, fecha y hora, y botones **Ver** y **Descargar**.
- Orden dentro de cada grupo: del más reciente al más antiguo.
- Botón **Limpiar lista** que quita las entradas de la sesión sin borrar archivos del disco.
- Colores por tipo: Word azul, PDF rojo, HTML naranja, Excel verde, Markdown verde claro.

### 7.3 Criterios de aceptación
- [ ] Los archivos están agrupados por tipo.
- [ ] Cada grupo es una fila horizontal con desplazamiento si hace falta.
- [ ] Ver y Descargar funcionan con el nombre y la extensión correctos.

---

## FASE 8 — Verificación global

1. Documento de prueba con título, párrafos, lista, tabla, fórmula en bloque, imagen y el diagrama Mermaid del Anexo A.
2. Abrir cada pestaña de formato y comprobar que se ve el documento completo.
3. Cambiar un control de cada barra lateral y comprobar el cambio en vivo.
4. Exportar Word, PDF, HTML y Excel; abrir cada archivo y confirmar texto, tabla, imagen, Mermaid, fórmulas y numeración.
5. Ocultar y mostrar cada barra lateral; cambiar de pestaña y volver: las selecciones deben persistir.
6. Probar modo claro y oscuro en todas las pestañas.
7. Revisar la consola del navegador y los logs del servidor: sin errores.

---

## 9. Pestaña Plantillas y placeholders

No forma parte de estas fases de corrección. Se implementa con su propio prompt (`prompt-plantillas-placeholders.md`), una vez cerradas las fases 0 a 8.

---

## 10. Riesgos a vigilar

- **Mermaid y KaTeX en Word y PDF**: si el motor de conversión no los soporta de forma nativa, usa una imagen generada en el mismo renderizador y explica el compromiso en el reporte.
- **Vista previa de Word**: puede requerir una conversión a PDF por páginas. Elige la opción viable y justifícala.
- **Rendimiento**: documentos de hasta 200 MB con muchos diagramas pueden ser lentos. Renderiza bajo demanda y muestra el progreso.

---

## 11. Reporte que debe entregar la IA al terminar cada fase

1. **Fase** y estado: completada o pendiente.
2. **Diagnóstico**: causa encontrada de cada problema de la fase.
3. **Archivos creados y modificados**, con su función.
4. **Endpoints o funciones nuevas** del servidor.
5. **Dependencias nuevas** con justificación, o confirmación de que no hacen falta.
6. **Pruebas realizadas** y resultado de cada criterio de aceptación.
7. **Pendientes** y preguntas para el usuario.

---

## Anexo A — Diagrama Mermaid de prueba (usar en Fase 1 y Fase 8)

Pega este bloque en Docs dentro de un bloque de código ```` ```mermaid ````:

```mermaid
graph TD
classDef startFill fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
classDef calcFill fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;
classDef outFill fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;
classDef normFill fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#004d40;

A[Efluente Doméstico Rural: Pf = 250 hab | Q = 28 m3/d] :::startFill --> B[Pretratamiento: Fosa Séptica 2 Cámaras CO 10-602 | Vol = 35 m3] :::calcFill
B --> C[Efluente Clarificado: Carga = 9.0 kg DBO5/d | Conc = 321.4 mg/L] :::calcFill
C --> D{Selección de Tecnología de Humedal} :::startFill

D -- Opción 1: Gravedad / Sifón --> E[Humedal Horizontal HCFSH | As = 500 m2 | Grava 10-20mm] :::outFill
D -- Opción 2: Sifón Autosifonante --> F[Cámara Sifón 3.5 m3 + Humedal Vertical HCFV | As = 750 m2] :::outFill
D -- Opción 3: Impulsión Electromecánica --> G[Cámara Estanque 3.5 m3 + 2 Bombas 1.5 HP + Humedal Vertical HCFV | As = 750 m2] :::outFill

E --> H[Efluente HCFSH: DBO5 = 29.8 mg/L | Remoción = 93.8%] :::normFill
F --> I[Efluente HCFV Sifón: DBO5 = 20.0 mg/L | Remoción = 95.8%] :::normFill
G --> J[Efluente HCFV Bombeo: DBO5 = 20.0 mg/L | Remoción = 95.8%] :::normFill

H --> K[Cuerpo Receptor Dulce / Riego:Cumple TULSMA Tabla 3 <= 100 mg/L DBO5] :::outFill
I --> K
J --> K
```

Criterio de éxito: se ve el diagrama completo, con sus cuatro colores de `classDef`, tres ramas de decisión y el nodo final, en Docs, Word, HTML y PDF.
