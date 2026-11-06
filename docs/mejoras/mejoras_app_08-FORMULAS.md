# PROMPT DE CORRECCIÓN — Fórmulas (Word, PDF, HTML, Excel) y scroll de miniaturas en PDF

Copia este documento en tu asistente de IA (Claude Code, Cursor u otro con acceso al proyecto). Este prompt **solo** corrige lo descrito aquí. No agregues funciones nuevas, no cambies diseño y no toques otras pestañas. Al terminar, entrega el reporte de la sección 9 y **espera la evaluación del usuario** antes de continuar con cualquier otra cosa.

---

## 0. Reglas

1. **Analiza antes de cambiar.** Primero describe el pipeline actual de fórmulas, de principio a fin, con nombres reales de archivos y funciones. No inventes nombres.
2. **No cambies el contenido del usuario.** El documento fuente (Markdown en Docs) no se reescribe en silencio. Si una fórmula del fuente tiene errores de sintaxis, la app debe **avisarlo**, no corregirlo sin decirlo (ver sección 3.4).
3. **Un solo pipeline de fórmulas** para todas las pestañas (Docs, Word, PDF, HTML y Excel). Ninguna pestaña debe procesar LaTeX por su cuenta.
4. **Sin CDNs.** La app funciona offline. Usa KaTeX local si ya existe en el proyecto; si no, pide aprobación para incorporarlo.
5. **Idioma:** español en todos los mensajes.
6. **Orden obligatorio:** Fase 1 → Fase 2 → Fase 3. No pases a la siguiente sin cumplir la anterior.

---

## 1. Síntoma y causa probable

En la captura, las fórmulas aparecen como texto roto. Se ven así:

- Corchetes `[ ]` donde debía haber delimitadores de bloque, y paréntesis dobles `((d_{int}))`.
- Subíndices con llaves vacías `V_{}` o `L_{}`.
- Comandos LaTeX sin procesar: `\left(`, `\right)`, `\frac`, `\text`.
- Asteriscos y guiones bajos mezclados con el contenido matemático (`**` aparece dentro de fórmulas).

**Causa probable**, que la IA debe confirmar en el código:
- El Markdown se procesa **antes** de proteger las fórmulas. El procesador interpreta `_`, `*`, `{`, `}` y `\` como formato y los consume o transforma.
- Un normalizador de delimitadores (`$`, `$$` → `\(`, `\(`, `\[`, `\]`) puede estar eliminando barras invertidas o cambiando delimitadores dentro de bloques.
- Cada formato (Word, PDF, HTML, Excel) tiene su propio tratamiento de fórmulas, y cada uno falla de forma distinta.

---

## 2. Fase 1 — Pipeline único de protección de fórmulas

**Objetivo:** las fórmulas deben llegar intactas desde el Markdown hasta el renderizador.

### 2.1 Diseño requerido
1. **Extraer primero.** Antes de cualquier procesamiento de Markdown, extrae todas las fórmulas y guárdalas en una lista. Reemplázalas en el texto por un marcador seguro sin caracteres especiales, por ejemplo `@@FORMULA_0001@@`.
2. **Procesar el Markdown** con el marcador, sin tocar el contenido de las fórmulas.
3. **Reinsertar** cada fórmula en su lugar, sin modificación.
4. **Renderizar** con una sola función compartida, KaTeX, en cada formato.

### 2.2 Delimitadores que debe reconocer
- Bloque: `$$ … $$`, `\[ … \]`
- En línea: `$ … $`, `\( … \)`

Las fórmulas dentro de bloques de código (```` ``` ````) no se procesan.

### 2.3 Reglas de protección
- Dentro de una fórmula **no** se aplica ninguna transformación de Markdown.
- El normalizador de delimitadores, si existe, debe convertir solo el **delimitador**, nunca el contenido. Si hoy elimina barras invertidas, eso es el error a corregir.
- Escapes: `\$` produce un signo `$` literal fuera de fórmulas.

### 2.4 Casos de prueba obligatorios (Fase 1)

Crea un documento de prueba con estas fórmulas (corresponden a las que se ven rotas en la captura) y verifica que se renderizan correctamente:

```
$$V_{real} = \frac{Q_{m3s}}{A_{int}}$$

$$j = 0.0008695 \cdot \frac{Q_{m3s}^{1.75}}{\left(\frac{d_{int}}{1000}\right)^{4.75}}$$

$$L_{total} = L_{e} + L_{tramo}$$

$$L_{e} = \left( n_{codos} \cdot \left(\frac{L_{e}}{D}\right)_{codo} + n_{tees} \cdot \left(\frac{L_{e}}{D}\right)_{tee} \right) \cdot \left(\frac{d_{int}}{1000}\right)$$

Dentro de una línea: $h_f = j \cdot L_{total}$ y $P = P_0 - h_f$.
```

Verificación: cada fórmula se ve como fórmula matemática (fracciones, subíndices, paréntesis escalados), sin corchetes sueltos, sin `**`, sin comandos LaTeX visibles.

**Nota:** estas fórmulas son reconstrucciones. **La referencia es el archivo Markdown fuente real del usuario.** Si el fuente y estas líneas difieren, prevalece el fuente.

---

## 3. Fase 2 — Validación de fórmulas y errores del fuente

**Objetivo:** que la app detecte y señale fórmulas mal escritas, en lugar de mostrar basura.

### 3.1 Requisito
Al procesar el documento, cada fórmula se valida. Si KaTeX no puede renderizarla, la app:
- Muestra en el lugar de la fórmula un recuadro de error con el mensaje de KaTeX traducido al español y el fragmento original.
- Lista todos los errores en un panel "Fórmulas con error" en Docs, con número de línea y botón para ir a la línea.
- No altera el texto fuente.

### 3.2 Errores comunes que el fuente puede contener
La IA debe detectar y reportar (no corregir automáticamente) estos casos, si aparecen en el fuente del usuario:
- Delimitador de cierre incorrecto: `\right$)` en lugar de `\right)`.
- Subíndice sin guion bajo: `{d{int}}` en lugar de `{d_{int}}`.
- Subíndice vacío: `V_{}` o `L_{}`.
- Llaves desbalanceadas.
- `\left(` sin su `\right)` correspondiente.

### 3.3 Panel de fórmulas
Dentro de Docs, un botón **Validar fórmulas** que muestre el conteo: total de fórmulas, correctas y con error. Esto permite al usuario corregir el fuente con confianza.

### 3.4 Criterio
Una fórmula con error de sintaxis en el fuente debe aparecer como error visible y no como texto roto. Si el usuario confirma el error, lo corrige en su fuente y la fórmula se renderiza.

---

## 4. Fase 3 — Aplicación en cada formato

### 4.1 Word (`.docx`)
- Las fórmulas de bloque se insertan como **ecuaciones nativas de Word** (OMML), para que se editen en Word.
- Si la conversión a OMML no es posible para alguna fórmula, insértala como imagen renderizada con KaTeX y regístralo en el reporte.
- Numeración de ecuaciones: solo las fórmulas de bloque reciben número, alineado a la derecha, según la opción activa.

**Cuadros demasiado anchos (Word)**
- Hoy, las tablas más anchas que el área de texto de la página se distorsionan: se salen del margen, se cortan o se deforman.
- Requisito: la tabla debe caber **completa** dentro del área de texto (ancho de página menos márgenes configurados).
- Cálculo: ancho disponible = ancho de página − márgenes izquierdo y derecho. La tabla usa ancho fijo igual o menor a ese valor, con diseño de columnas fijo (`fixed layout`), sin autoajuste que la expanda.
- Si el contenido no cabe con el tamaño de texto actual, **reduce el tamaño de fuente de la tabla** hasta que todo quepa, con un mínimo de 7 pt. Aplica la reducción solo a la tabla, no al resto del documento.
- El texto largo dentro de celdas se envuelve en líneas; nunca se corta ni se desborda.
- Si con 7 pt aún no cabe, la tabla se reduce proporcionalmente en ancho de columnas (las columnas con más contenido reciben más ancho) y se avisa en el panel de validación: "Tabla N reducida a 7 pt; revisa su contenido".
- La vista previa de Word y el `.docx` deben mostrar exactamente la misma tabla, con el mismo tamaño de letra.
- Para PDF y HTML solo verifica si el mismo problema existe y repórtalo; no lo corrijas en esta entrega.

### 4.2 PDF
- Las fórmulas se renderizan con KaTeX en la vista previa y en el archivo descargado. La vista previa y el PDF deben coincidir.

### 4.3 HTML
- Las fórmulas se renderizan con KaTeX, con la fuente incluida en el `.html`, para que funcionen sin internet.
- El archivo debe ser autónomo.

### 4.4 Excel (`.xlsx`)
Excel **no renderiza LaTeX** dentro de las celdas, así que hay dos capas:

**a) Vista en pantalla (pestaña Excel)**
- Las celdas con fórmulas se muestran **renderizadas con KaTeX**, igual que en la vista previa de HTML. No debe verse texto LaTeX crudo.

**b) Archivo `.xlsx`**
- En la celda se escribe la fórmula en **texto legible** traducido a notación Unicode: subíndices (`Q₍ₘ₃ₛ₎`), superíndices (`x²`), fracciones como `a/b` o `(a)/(b)`, raíces `√`, y `·` para multiplicación.
- Si una fórmula no se puede traducir a texto legible, se escribe su versión plana y se marca en la celda con un comentario de Excel que diga "Fórmula compleja: ver imagen".
- **Opcional, configurable**: una columna adicional con una imagen PNG de la fórmula renderizada, anclada a la celda. Por defecto **desactivada**.

Indica en el reporte cuál de estas opciones implementaste y por qué.

---

## 5. Fase 4 — Scroll de miniaturas en PDF

### 5.1 Problema
Al hacer scroll sobre el panel de miniaturas, también se desplaza la página principal del PDF. Debe ser al revés: la página principal permanece fija y solo las miniaturas se desplazan.

### 5.2 Requisitos
- El **visor principal** tiene altura fija dentro del área de la pestaña y su contenedor no tiene desplazamiento propio que responda a la rueda del ratón mientras el cursor está sobre las miniaturas.
- El **panel de miniaturas** tiene su propio contenedor con desplazamiento vertical independiente.
- Usa `overscroll-behavior: contain` en el contenedor de miniaturas, para que el desplazamiento no se propague a la página principal al llegar al final.
- Si el visor principal tiene desplazamiento vertical para ver las páginas, el scroll de la rueda sobre el visor debe cambiar de página o desplazar solo el visor, sin mover las miniaturas.
- Clic en una miniatura lleva el visor a esa página, y la miniatura activa queda resaltada.

### 5.3 Criterio
Con el cursor sobre las miniaturas, la rueda solo mueve las miniaturas. Con el cursor sobre la página principal, la rueda solo mueve la página principal.

---

## 6. Fase 5 — Verificación

Ejecuta y registra el resultado de:

1. Documento de prueba con las fórmulas de la sección 2.4 y una fórmula con error intencional.
2. Word: abrir el `.docx` y confirmar que las ecuaciones son editables y se ven correctas.
3. PDF: abrir el archivo descargado y confirmar el render de fórmulas.
4. HTML: abrir el `.html` sin conexión y confirmar el render.
5. Excel: confirmar que la pestaña muestra fórmulas renderizadas, y que el `.xlsx` abre con texto legible y sin comandos LaTeX.
6. PDF: hacer scroll en miniaturas y verificar que la página principal no se mueve.
7. Revisar la consola del navegador y los logs del servidor: sin errores.

---

## 7. Criterios de aceptación

- [ ] Ninguna fórmula aparece con corchetes sueltos, `**`, `_{}` vacíos ni comandos LaTeX visibles, en ningún formato.
- [ ] Las fórmulas de bloque se renderizan en Word (nativas o imagen), PDF, HTML y la vista de Excel.
- [ ] El `.xlsx` contiene texto legible, sin LaTeX crudo.
- [ ] Las fórmulas con error de sintaxis aparecen con un aviso y se listan en el panel de validación.
- [ ] El scroll de miniaturas no mueve la página principal del PDF.
- [ ] Las tablas anchas caben completas dentro del área de texto en Word, sin distorsión, con reducción de fuente mínima de 7 pt cuando sea necesario.
- [ ] La vista previa de Word y el `.docx` muestran la misma tabla con el mismo tamaño.
- [ ] Ninguna otra función cambió.

---

## 8. Pendientes que el usuario debe confirmar (la IA debe preguntar)

1. **Excel:** ¿prefieres solo texto Unicode en la celda (por defecto), o también una columna con imagen de la fórmula?
2. **Errores del fuente:** ¿la app debe sugerir la corrección (por ejemplo `\right$)` → `\right)`), o solo señalar el error?
3. **Word:** ¿las ecuaciones deben ser nativas y editables en Word (OMML), o basta con imagen?

---

## 9. Reporte obligatorio al terminar

1. **Pipeline actual**: descripción del flujo de fórmulas encontrado, con archivos y funciones reales.
2. **Causa confirmada** del síntoma en cada formato (Word, PDF, HTML, Excel).
3. **Cambios realizados**: archivo y función, una línea por cambio.
4. **Resultado de cada caso de prueba** (sección 2.4 y sección 6).
5. **Errores del fuente detectados** en el documento del usuario, con su línea.
6. **Decisiones tomadas** en Excel y Word, y por qué.
7. **Cuadros anchos en Word**: causa de la distorsión, tamaño de fuente final aplicado a cada tabla, y si alguna tabla llegó al mínimo de 7 pt. Estado de PDF y HTML respecto al mismo problema.
8. **Preguntas pendientes** (sección 8).

Después de entregar el reporte, **detente**. No continúes con otras correcciones hasta que el usuario lo evalúe.
