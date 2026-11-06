# PROMPT — Nueva pestaña "Plantillas" para Markdown Office (placeholders dinámicos)

---

## 0. Reglas para la IA

1. **Revisa primero el proyecto.** Lista la estructura de carpetas y los archivos existentes (`index.html`, `app.js`, el servidor, los CSS de `/static/css/`). Describe lo que encuentres antes de modificar nada.
2. **No cambies la lógica existente** de las pestañas "Tus datos", "Salida" y "Manual de Usuario", ni la generación actual de HTML, Word, PDF y Markdown. Solo **añade** la nueva pestaña y **reutiliza** el pipeline de generación ya existente.
3. **Mantén el estilo visual vigente**: IBM Plex Sans, paleta índigo → violeta, tarjetas `.tarjeta`, botones `.btn`, acordeones `.acordeon`, chips `.chip`, y los modos claro y oscuro. No uses Mantine ni CDNs externos (la app funciona 100 % offline).
4. **Librerías nuevas**: si necesitas una (por ejemplo para leer/escribir `.xlsx`, como `openpyxl`, o para leer `.docx`, como `python-docx`), **pide aprobación** antes de instalarla y explica por qué.
5. **Idioma**: todos los textos de la interfaz, nombres de placeholders, columnas del Excel y mensajes, en **español**.
6. Si algo no está claro en este documento, **pregunta antes de asumir**. Al final, reporta lo que hiciste y lo que quedó pendiente.

---

## 1. Objetivo

La app genera memorias técnicas que se repiten entre proyectos y solo cambian algunos datos (nombre del proyecto, caudal, responsable, fechas, etc.). Quiero una pestaña **"Plantillas"** que permita:

- **Finalidad A — Crear plantilla:** a partir de un documento de un proyecto real (`.md` en esta fase; `.docx` y `.pdf` en fases posteriores), detectar los datos que cambian, convertirlos en **placeholders con nombre** y generar una plantilla reutilizable, junto con un Excel y un JSON con los valores.
- **Finalidad B — Usar plantilla:** tomar una plantilla (la creada en A u otra compatible) y uno o varios conjuntos de datos (Excel o JSON), y generar **documentos nuevos** en HTML, Word, PDF o Markdown, usando los temas que ya tiene la app.

---

## 2. Decisiones ya confirmadas por el usuario

| Tema | Decisión |
|---|---|
| Formato de salida | Usar **los temas que ya tiene la app** (no conservar el estilo original del documento subido). |
| Idioma | **Español** en nombres de placeholders (sin tildes ni espacios) y en toda la interfaz. |
| Excel | **Datos en columnas**: cada columna es un proyecto y cada fila es un placeholder (ver sección 6.2). |
| Placeholders que faltan al generar | **Permitir generar** y marcar en **rojo** el espacio vacío. No bloquear. |
| Nombre de la pestaña | **"Plantillas"**, como prefijo de la sección y de los archivos generados (ver sección 3.4). |

---

## 3. Sintaxis y convenciones

### 3.1 Placeholder

Formato en el archivo Markdown: `{{nombre_del_dato}}`

Ejemplo:

```
Proyecto: {{proyecto_nombre}}
Ubicación: {{proyecto_ubicacion}}
Caudal de diseño: {{caudal_diseno}} l/s
Responsable: {{responsable_nombre}}, {{responsable_cargo}}
```

### 3.2 Reglas de nombre

- Solo minúsculas, números y guion bajo: `caudal_diseno`, `responsable_cargo`.
- Sin tildes, espacios ni símbolos. Ñ se escribe `n` (`anio_proyecto`).
- Máximo 60 caracteres.
- Si el nombre ya existe en la plantilla, se reutiliza. Un solo dato = un solo placeholder usado en todas sus apariciones.

### 3.3 Escape

- Para escribir `{{` literal en el documento, usar `\{{`. Al generar, se muestra como `{{` sin reemplazo.
- **No** convertir texto dentro de bloques matemáticos (`$$ ... $$`, `\[ ... \]`, `\( ... \)`) ni dentro de bloques de código (```` ``` ````). Las fórmulas no deben romperse.

### 3.4 Prefijo "Plantillas"

- El nombre de la pestaña es **"Plantillas"**.
- Los archivos generados por esta sección empiezan con el prefijo `plantilla_`:
  - `plantilla_<nombre_proyecto>.md`
  - `plantilla_<nombre_proyecto>_datos.xlsx`
  - `plantilla_<nombre_proyecto>_datos.json`
- Los documentos finales generados desde una plantilla usan el prefijo `documento_` seguido del nombre del proyecto (por ejemplo `documento_hidrosanitario_norte.docx`).

---

## 4. Ubicación en la interfaz

### 4.1 Nueva pestaña

Agrega una nueva pestaña vertical en la parte inferior del resto de pestañas

- Texto: `🧩 Plantillas`
- Mismo patrón de atributos que las demás pestañas (`role="tab"`, `aria-controls`, `aria-selected`, `tabindex`).
- Panel: `<section id="panel-plantillas" class="panel-tab" role="tabpanel">`, siguiendo el mismo patrón de los demás paneles.

### 4.2 Sub-pestañas dentro de "Plantillas"

Usa el mismo componente `.sub-tabs-nav` que ya existe en "Opciones de Formato":

- **✏️ Crear plantilla** (Finalidad A)
- **📄 Usar plantilla** (Finalidad B)

---

## 5. Finalidad A — Crear plantilla

### 5.1 Flujo

1. **Cargar origen.** Zona de arrastre (reutiliza `.zona-suelta`) que acepta uno o varios `.md`. Muestra la lista con `.doc` como en "Tus datos".
2. **Detección automática.** Al cargar, la app busca candidatos (ver sección 5.2) y los muestra en una tabla de revisión.
3. **Revisar candidatos.** Tabla con: casilla para usar o descartar, texto encontrado, nombre sugerido (editable), tipo, veces que aparece y nivel de confianza (alta, media, baja).
4. **Conversión manual.** En el editor de la sub-pestaña, el usuario selecciona cualquier texto con el ratón y aparece el botón **"🧩 Convertir en placeholder"**. Al pulsarlo, se abre un pequeño cuadro para escribir el nombre (con sugerencia automática) y el tipo. El texto se reemplaza visualmente por una etiqueta (ver sección 5.4).
5. **Generar salidas.** Botón **"Crear plantilla"** que produce los tres archivos de la sección 6.

### 5.2 Detección automática: reglas

Clasifica cada candidato con un nivel de confianza:

| Patrón | Ejemplo | Tipo sugerido | Confianza |
|---|---|---|---|
| Etiqueta seguida de valor | `Proyecto: Hidrosanitario Norte` | texto | alta |
| Número con unidad | `12.5 l/s`, `3.20 m`, `US$ 4500` | numero (con unidad) | alta |
| RUC ecuatoriano (13 dígitos) | `1790012345001` | identificador | alta |
| Cédula ecuatoriana (10 dígitos) | `1712345678` | identificador | alta |
| Correo electrónico | `ing@correo.com` | texto | alta |
| Teléfono | `+593 99 123 4567` | texto | alta |
| Fecha | `25/10/2026`, `25 de octubre de 2026` | fecha | alta |
| Coordenadas | `-0.2201, -78.5123` | texto | alta |
| Valor repetido 3 o más veces | el nombre del proyecto | texto | media |
| Celda de tabla con cabecera conocida | columna "Caudal (l/s)" | numero | media |
| Número suelto sin unidad | `2026` | numero | baja |

Reglas adicionales:
- No marcar como candidatos los títulos (`#`), los números de capítulo (`1.`, `2.1`), ni el texto dentro de bloques de código o matemáticas.
- Los candidatos de confianza **alta** vienen marcados por defecto. Los de **baja** vienen desmarcados.
- Si dos candidatos son el mismo valor, se sugiere el mismo nombre.

### 5.3 Tipos de dato

| Tipo | Uso | Validación al usar la plantilla |
|---|---|---|
| `texto` | nombres, descripciones | cualquier texto |
| `numero` | caudales, dimensiones, cantidades | número válido (coma o punto decimal) |
| `fecha` | fechas de entrega | fecha válida, formato dd/mm/aaaa |
| `identificador` | RUC, cédula | 10 o 13 dígitos |
| `moneda` | presupuestos | número, con símbolo opcional |

El campo **unidad** (`l/s`, `m`, `US$`) es opcional y se guarda aparte del valor.

### 5.4 Visualización de placeholders en el editor

- En el editor Markdown (textarea), el placeholder se escribe como `{{nombre}}`.
- En el **render visual** (split-view y vista previa), se muestra como una etiqueta: fondo `var(--gradient-ai-soft)`, borde `rgba(99, 102, 241, 0.35)`, texto `var(--accent-indigo)`, fuente `var(--font-mono)`, radio `var(--radius-full)`, y el contenido `[nombre]`.
- Un clic sobre la etiqueta permite **renombrar** o **volver a texto normal** (deshace la conversión).
- En la conversión de vuelta a Markdown, la etiqueta siempre se traduce a `{{nombre}}`.

---

## 6. Archivos que genera "Crear plantilla"

### 6.1 `plantilla_<proyecto>.md`

El documento Markdown con todos los datos convertidos en placeholders. Es la plantilla reutilizable.

### 6.2 `plantilla_<proyecto>_datos.xlsx`

Una sola hoja llamada **"Datos"**. La estructura es **una columna para el nombre del placeholder y una columna por cada proyecto**:

| A: `placeholder` | B: `Proyecto 1` | C: `Proyecto 2` |
|---|---|---|
| proyecto_nombre | Hidrosanitario Norte | |
| caudal_diseno | 12.5 | |
| responsable_nombre | Ing. Patricio Sarmiento | |

Ejemplo: para **2 proyectos** el Excel tiene **3 columnas** (A, B y C). Para 5 proyectos tendría 6 columnas.

Reglas:
- **Columna A (`placeholder`)**: contiene solo los nombres de los placeholders de la plantilla, en el mismo orden en que aparecen en el documento. Es de solo lectura para el usuario: no debe editarse ni reordenarse, porque se usa para unir los datos con la plantilla.
- **Columnas B en adelante**: una por proyecto. La **primera columna de proyecto** (B) viene llena con los valores extraídos del documento de origen; las demás quedan vacías para que el usuario las llene.
- **Encabezados de proyecto** (`Proyecto 1`, `Proyecto 2`…): son editables. Al importar, el nombre de la columna es el nombre del proyecto.
- **Sin columnas extra** (ni etiqueta, tipo, unidad ni grupo): esa información vive en el JSON y en la propia plantilla, no en el Excel, para que el archivo sea simple de llenar.
- Si una celda queda vacía, el placeholder se considera vacío para ese proyecto (sección 7.2).
- No se usan hojas adicionales. Un solo archivo, una sola hoja.
- Formato: cabecera en negrita con fondo `#eef0fa`, bordes sutiles, columna A con ancho automático, columnas de proyecto con ancho suficiente para leer los valores.
- Al importar un Excel, la app debe tomar el **tipo** de cada placeholder desde la plantilla (o desde el JSON si está disponible). Si no hay tipo, se asume `texto`.

### 6.3 `plantilla_<proyecto>_datos.json`

```json
{
  "plantilla": "plantilla_hidrosanitario_norte",
  "version": 1,
  "placeholders": [
    { "nombre": "proyecto_nombre", "etiqueta": "Nombre del proyecto", "tipo": "texto", "unidad": null, "grupo": "Datos generales" },
    { "nombre": "caudal_diseno", "etiqueta": "Caudal de diseño", "tipo": "numero", "unidad": "l/s", "grupo": "Hidráulica" }
  ],
  "proyectos": {
    "Proyecto 1": {
      "proyecto_nombre": "Hidrosanitario Norte",
      "caudal_diseno": 12.5
    }
  }
}
```

- `placeholders` describe el diccionario de datos.
- `proyectos` tiene una clave por proyecto (equivale a una columna del Excel). Cada uno guarda sus valores.
- Al importar un JSON o un Excel, la app debe aceptar ambos y convertirlos a este mismo modelo interno.

---

## 7. Finalidad B — Usar plantilla

### 7.1 Flujo

1. **Subir plantilla.** Acepta un `.md` (incluye los creados en la sección A). Muestra cuántos placeholders encontró y su lista.
2. **Subir datos.** Acepta `.xlsx` (con el formato de la sección 6.2) o `.json` (sección 6.3).
3. **Elegir proyecto.** Si el Excel o JSON tiene varios proyectos (varias columnas), un selector permite elegir uno, o **generar uno por cada proyecto** en lote.
4. **Revisar validación** (sección 7.2).
5. **Elegir salidas.** Casillas HTML, Word, PDF y Markdown, igual que en "Generación de Salidas". Las opciones de tema, paleta y formato se toman de los **Temas** y las **Opciones de Formato** que ya existen.
6. **Generar.** Reemplaza los placeholders y pasa el documento al mismo pipeline de salidas que ya existe.

### 7.2 Validación antes de generar

Muestra un panel de resumen con estos grupos:

| Estado | Qué significa | Tratamiento |
|---|---|---|
| ✅ Completo | Placeholder con valor válido | Se reemplaza sin aviso |
| 🟥 Vacío | Placeholder sin valor en el proyecto elegido | Se **permite generar**; el espacio queda **marcado en rojo** en el documento con el texto `[nombre]` |
| ⚠️ Tipo incorrecto | Valor que no cumple el tipo (texto en campo numérico) | Se avisa y se permite generar; se marca en ámbar |
| ℹ️ Sobrante | Dato en el Excel/JSON que la plantilla no usa | Se informa, no se borra |
| ❓ Desconocido | Placeholder en la plantilla sin dato en el Excel/JSON | Igual que "Vacío" |

Muestra un contador: "18 completos · 2 vacíos · 1 con tipo incorrecto · 3 sobrantes".

### 7.3 Marcado en rojo

Al generar en HTML o en PDF, el espacio vacío se muestra con fondo rojo suave (`var(--color-danger-bg)`), texto rojo (`var(--color-danger)`) y el nombre del placeholder entre corchetes: `[caudal_diseno]`.

En Word y en Markdown, el mismo espacio se marca con el texto `[caudal_diseno]` en color rojo (o con resaltado rojo si el formato lo permite).

---

## 8. Reglas técnicas

- **Reemplazo solo en texto.** No reemplazar dentro de bloques de código ni de matemáticas (sección 3.3).
- **Un solo reemplazo por aparición.** Si un placeholder aparece 20 veces, se reemplaza las 20.
- **Espacios alrededor**: `{{ nombre }}` y `{{nombre}}` son el mismo placeholder. Normalizar al leer.
- **Números**: aceptar coma o punto decimal al importar; guardar siempre con punto en el JSON; mostrar según la configuración regional del documento.
- **Codificación**: UTF-8 en todos los archivos (el Excel y el JSON deben abrirse sin caracteres rotos).
- **Nombres de archivo seguros**: quitar tildes y caracteres no válidos al generar el nombre de archivo.
- **Sin pérdida de datos**: al importar un Excel, nunca borrar columnas de proyectos que no se usen; solo avisar.
- **Rendimiento**: el procesamiento de un documento de hasta 200 MB debe mostrar la barra de progreso flotante existente (`.progreso-flotante-overlay`).

---

## 9. Fases de trabajo

### Fase 1 (alcance de esta entrega)

- Pestaña "Plantillas" con sus dos sub-pestañas.
- Origen **Markdown** solamente.
- Detección automática (alta y media confianza) con tabla de revisión.
- Conversión manual con el ratón y etiqueta visual.
- Generación de `plantilla_<proyecto>.md`, `.xlsx` y `.json`.
- Carga de plantilla `.md` y datos `.xlsx` o `.json`.
- Validación completa con estados de la sección 7.2.
- Generación en **HTML, Word, PDF y Markdown** usando los temas existentes.
- Marcado en rojo para datos faltantes.

### Fase 2 (no implementar todavía; deja el diseño preparado)

- Origen `.docx` y `.pdf` (cuidado: Word separa el texto en fragmentos internos; el extractor debe unirlos antes de buscar placeholders).
- Detección de confianza baja.

### Fase 3 (no implementar todavía)

- Listas y tablas repetitivas (por ejemplo, un bloque por cada tubería), con una sintaxis como `{{#tuberias}} ... {{/tuberias}}`.
- Historial de versiones de plantillas.

---

## 10. Criterios de aceptación (Fase 1)

- [ ] Existe la pestaña "🧩 Plantillas" con dos sub-pestañas, con el mismo estilo visual que el resto de la app, en modo claro y oscuro.
- [ ] Al cargar un `.md` con datos de proyecto, aparece la tabla de candidatos con nombre sugerido, tipo y confianza.
- [ ] Seleccionar texto y usar "Convertir en placeholder" lo muestra como etiqueta visual, y al generar se guarda como `{{nombre}}`.
- [ ] Un clic sobre una etiqueta permite renombrarla o devolverla a texto normal.
- [ ] Se generan `plantilla_<proyecto>.md`, `plantilla_<proyecto>_datos.xlsx` y `plantilla_<proyecto>_datos.json`, con la estructura exacta de la sección 6.
- [ ] El Excel generado puede editarse en Excel, volver a subirse y dar el mismo resultado.
- [ ] Al subir una plantilla y un Excel con varios proyectos, se puede elegir uno o generar uno por proyecto.
- [ ] El panel de validación muestra completos, vacíos, tipos incorrectos y sobrantes.
- [ ] Un dato vacío no bloquea la generación y aparece en rojo en el documento final.
- [ ] Las fórmulas matemáticas y los bloques de código no se modifican al reemplazar.
- [ ] La generación en HTML, Word, PDF y Markdown usa los temas y opciones existentes.
- [ ] Ningún cambio altera el funcionamiento de "Tus datos", "Salida" y "Manual de Usuario".
- [ ] Sin errores en la consola del navegador ni en el servidor.

---

## 11. Entregables que debe reportar la IA

1. Lista de archivos creados y modificados, con una línea por archivo.
2. Rutas nuevas (endpoints) del servidor, si las hay, con su función.
3. Dependencias nuevas que se requieren (con justificación), o confirmación de que no hacen falta.
4. Qué se probó y qué no se pudo probar.
5. Preguntas pendientes para el usuario.

---

## 12. Preguntas que la IA debe hacer si no puede resolver algo

1. ¿Qué archivo del proyecto contiene el servidor (Flask, FastAPI u otro) y dónde están las rutas actuales de generación?
2. ¿Ya existe una librería para leer y escribir `.xlsx` en el proyecto? Si no, ¿se aprueba `openpyxl`?
3. ¿El pipeline actual de Markdown a HTML, Word y PDF acepta texto ya procesado, o hay que pasar por un paso previo?
4. ¿El editor actual es un `textarea` simple o hay otro componente que deba integrarse con el split-view?

---

# ANEXO — Ejemplo de flujo completo (para validar la implementación)

**Entrada:** `memoria_norte.md` con este texto:

```
Proyecto: Hidrosanitario Norte
El caudal de diseño es 12.5 l/s y el responsable es Ing. Patricio Sarmiento.
Presupuesto referencial: US$ 4500.
```

**Paso A (crear):** la app detecta `Hidrosanitario Norte` (alta, texto), `12.5 l/s` (alta, numero, unidad l/s), `Ing. Patricio Sarmiento` (media, texto) y `US$ 4500` (alta, moneda, unidad US$). El usuario confirma los nombres.

**Salida A:**

```
Proyecto: {{proyecto_nombre}}
El caudal de diseño es {{caudal_diseno}} l/s y el responsable es {{responsable_nombre}}.
Presupuesto referencial: {{presupuesto_referencial}}.
```

Más el Excel con una columna **Proyecto 1** llena con `Hidrosanitario Norte`, `12.5`, `Ing. Patricio Sarmiento` y `4500`.

**Paso B (usar):** se sube la plantilla y un Excel con dos columnas (**Proyecto 1** y **Proyecto 2**). El usuario elige "generar uno por proyecto". Si **Proyecto 2** no tiene valor para `caudal_diseno`, el documento de ese proyecto muestra `[caudal_diseno]` en rojo y el resumen indica "1 vacío".

**Resultado esperado:** dos documentos `documento_hidrosanitario_norte.html` y `documento_<proyecto_2>.html`, con sus datos correctos y el espacio vacío en rojo.
