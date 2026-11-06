# PROMPT — Fusión de documentos, tamaño legible de diagramas en exportación y corrección de la pestaña PDF

Copia este documento en tu asistente de IA (Claude Code, Cursor u otro con acceso al proyecto) y ejecútalo **por fases, en el orden indicado**. No avances a la siguiente fase sin cumplir los criterios de la actual y sin entregar su reporte.

---

## 0. Reglas generales

1. **Analiza antes de cambiar.** En cada fase, primero describe el código relacionado con nombres reales de archivos y funciones. No inventes nombres.
2. **No rompas lo que funciona:** ingesta de archivos, detección de codificación, sintaxis de fórmulas, pipeline de fórmulas, numeración existente, firma e índice al final, pestaña **MarkFlow Conversión Completa** (fuente de verdad de temas y opciones), cuadros anchos en Word y el visor flotante.
3. **Un solo renderizador por elemento.** Mermaid, KaTeX e imágenes se renderizan con una única función compartida. Las pestañas de vista previa y exportación usan esa misma función.
4. **Sin CDNs.** La app funciona offline. Si una librería no está en el proyecto, pide aprobación antes de incorporarla.
5. **Idioma:** español en toda la interfaz y en los mensajes.
6. **Reporte por fase.** Al terminar cada fase, entrega su reporte (sección 9) y espera confirmación del usuario.

---

## FASE 1 — Fusión de documentos en la pestaña Documentos

### 1.1 Qué debe hacer
El usuario debe poder **seleccionar dos o más tarjetas de documentos** visibles en la pestaña Documentos y **fusionarlas en un solo documento**.

### 1.2 Interfaz
- Cada tarjeta de documento tiene una casilla de selección.
- Cuando hay dos o más seleccionadas, aparece el botón **Fusionar seleccionados**.
- Junto al botón aparece la casilla **Cada documento es un capítulo distinto**.
- Antes de fusionar, un panel muestra el **orden de fusión** de los documentos seleccionados. El usuario puede reordenarlos con botones de subir y bajar, o arrastrando. El orden inicial es el orden de las tarjetas.
- Al confirmar, aparece una nueva tarjeta con el nombre **"Fusión: [nombre del primero] + N más"**, editable. Los documentos originales **se conservan** en la lista, marcados como "incluidos en fusión".

### 1.3 Reutilizar lo existente
La pestaña Tus datos ya tiene las casillas **"Modo Capítulos Continuos"** y **"Salto de página entre archivos"**. Reutiliza su lógica. No dupliques la funcionalidad. La casilla de la fusión debe usar el mismo comportamiento que esas casillas.

### 1.4 Comportamiento de la casilla "Cada documento es un capítulo distinto"

**Si está activa:**
- Cada documento de la fusión empieza en una **hoja nueva**. Cuando termina uno, el siguiente comienza en otra hoja.
- Los títulos se **numeran automáticamente** por capítulo:
  - H1 del documento 1 → `1.`; sus H2 → `1.1`, `1.2`; sus H3 → `1.1.1`…
  - H1 del documento 2 → `2.`; sus H2 → `2.1`, `2.2`…
- La numeración es **continua** entre documentos.
- Si un título ya trae número (por ejemplo `# 1. Introducción`), la app lo **reemplaza** por el número correcto, sin duplicarlo (`1. 1. Introducción` es un error).

**Si está desactivada:**
- Los documentos se unen en un flujo continuo, sin salto de hoja entre ellos.
- Igual se numeran los títulos de forma continua, salvo que el usuario haya desactivado la numeración en la pestaña de formato.

### 1.5 Reglas de numeración
- Solo se numeran H1, H2 y H3. H4 en adelante no se numeran.
- La numeración se aplica **al generar la vista previa y la exportación**, no reescribiendo el texto de los documentos originales.
- Un título sin número en el original recibe número si cae dentro de la numeración.

### 1.6 Criterios de aceptación (Fase 1)
- [ ] Se pueden seleccionar dos o más tarjetas y fusionarlas.
- [ ] Se puede reordenar el orden de fusión antes de confirmar.
- [ ] Con la casilla activa, cada documento empieza en hoja nueva en la vista previa y en la exportación.
- [ ] Los títulos H1, H2 y H3 se numeran de forma continua y sin duplicar números existentes.
- [ ] Con la casilla desactivada, los documentos se unen sin salto de hoja.
- [ ] Los documentos originales se conservan.

---

## FASE 2 — Tamaño legible de diagramas y figuras en todas las exportaciones

### 2.1 Problema
- Los diagramas Mermaid se ven muy pequeños al exportar a **Word, PDF y HTML**. El texto dentro del diagrama no se puede leer. La vista previa de la pestaña Word también se ve pequeña, pero ese detalle es secundario: lo importante es el **archivo exportado**.
- Las figuras que envuelven el texto no se adaptan bien.
- En **HTML**, el diagrama o la figura aparece con una **barra de desplazamiento vertical**. Eso no debe ocurrir.

### 2.2 Requisitos de tamaño

**Texto del diagrama**
- El texto dentro de cualquier diagrama Mermaid debe tener un tamaño **equivalente a no menos de 9 pt** en la hoja impresa. Esto significa que la fuente del diagrama debe calcularse en función del ancho real que ocupa en la página, no dejarse en el tamaño por defecto de Mermaid.
- Configura Mermaid con un tamaño de fuente base suficiente (por ejemplo 16 px) y desactiva el escalado automático que reduce el texto. Ajusta el diagrama al ancho de la columna de texto, no al revés.

**Tamaño del diagrama**
- Ancho máximo: el ancho de la columna de texto (ancho de página menos márgenes).
- Ancho mínimo: no menos de 60 % del ancho de la columna de texto, para que no quede diminuto cuando el diagrama es simple.
- Alto máximo: 22 cm en A4, para que quepa en una hoja con encabezado y pie. Si el diagrama supera ese alto, reduce la escala **solo si** el texto del diagrama sigue cumpliendo el mínimo de 9 pt; si no, divide el diagrama en dos partes y avisa en el panel de validación.

**Formato de salida de diagramas**
- **HTML y PDF**: vector SVG, nítido en cualquier zoom.
- **Word**: imagen PNG de al menos 300 ppp en el ancho final, o SVG con PNG de respaldo si Word lo admite en el proyecto.
- La vista previa de la pestaña Word puede seguir mostrando el diagrama pequeño, pero debe coincidir en **proporciones** con la exportación.

### 2.3 Requisitos de figuras y texto envolvente
- Una imagen o diagrama **en línea** se centra en la columna de texto, con su número de figura y leyenda si existe.
- Una figura **flotante** (si el documento lo indica o el usuario lo activa) envuelve el texto:
  - Su ancho nunca supera el 50 % del ancho de la columna.
  - El texto se acomoda alrededor sin cortar palabras ni dejar espacios vacíos grandes.
  - En **Word**: posicionamiento flotante con envoltura cuadrada.
  - En **PDF**: el layout reserva el espacio de la figura y mueve el texto alrededor.
  - En **HTML**: `float` con `max-width` del 50 %, y el texto alrededor con margen de 1 cm.
- Ningún elemento puede desbordar la columna de texto.

### 2.4 Reglas de HTML
- Prohibido el scroll interno en diagramas, figuras, tablas o imágenes. El desplazamiento solo lo hace la página.
- Todas las imágenes y SVG: `max-width: 100%; height: auto;`.
- Ningún contenedor del diagrama debe tener `overflow: auto` ni `overflow: scroll`.
- Si un cuadro es más ancho que la columna, se reduce el texto de la tabla (como en Word), sin barra de desplazamiento.

### 2.5 Verificación con el diagrama de prueba
Usa el diagrama del Anexo A (sección final de este documento) y verifica:
- En Word: el texto del diagrama se lee sin lupa, al nivel de un texto normal de 9 a 10 pt.
- En PDF: al hacer zoom en el visor, el texto sigue nítido.
- En HTML: no aparece ninguna barra de desplazamiento alrededor del diagrama.
- El diagrama no ocupa más de una hoja A4.

### 2.6 Criterios de aceptación (Fase 2)
- [ ] El texto de los diagramas en Word, PDF y HTML tiene al menos 9 pt equivalente.
- [ ] Los diagramas ocupan el ancho de la columna de texto sin ser gigantes.
- [ ] Las figuras flotantes envuelven el texto y no superan el 50 % del ancho.
- [ ] El HTML no muestra barras de desplazamiento en diagramas, figuras, imágenes ni tablas.
- [ ] El diagrama de prueba se ve legible en Word, PDF y HTML.
- [ ] Ninguna exportación rompe las fórmulas, cuadros anchos ni la fusión de la fase 1.

---

## FASE 3 — Pestaña PDF Editorial: velocidad, zoom y salto por capítulo

### 3.1 Problema A: carga lenta
Al abrir la vista previa del PDF, el documento tarda demasiado en aparecer.

**Requisitos**
- Renderiza solo las páginas visibles (y una o dos de margen). Las demás se renderizan al acercarse con el desplazamiento.
- Usa miniaturas de baja resolución para el panel izquierdo, y renderiza la versión completa solo para la página activa.
- Cachea las páginas ya renderizadas y invalida la caché solo cuando cambia una opción.
- Muestra un indicador de progreso por página mientras se genera. Nunca dejes la pantalla en blanco sin mensaje.
- Las actualizaciones por cambio de opción se hacen con retardo de 300 ms y sin bloquear la interfaz; si es posible, usa un proceso aparte.

### 3.2 Problema B: el zoom no funciona como en un visor de PDF
Al aumentar el zoom por encima de 100 %, el canvas no se expande en tiempo real y la hoja mantiene el mismo tamaño, lo que dificulta leer.

**Requisitos**
- El zoom debe **volver a renderizar la página a la nueva escala** (no estirar la imagen con CSS). Así el texto se mantiene nítido.
- La hoja crece en tamaño visible al aumentar el zoom, y aparecen barras de desplazamiento de la página cuando se excede el área visible.
- Controles: botones **+** y **−**, un selector de zoom (50 %, 75 %, 100 %, 125 %, 150 %, 200 %, 300 %, ajustar a ancho, ajustar a página).
- **Ctrl + rueda del ratón** sobre el canvas de la página principal cambia el zoom del PDF en tiempo real, igual que en un visor de PDF normal:
  - Ctrl + rueda hacia arriba aumenta el zoom; hacia abajo lo reduce.
  - El cambio se aplica paso a paso (por ejemplo 10 % por cada muesca de la rueda), dentro de los límites de 25 % a 400 %.
  - El navegador **no debe hacer zoom de toda la página web** al usar Ctrl + rueda: hay que bloquear ese comportamiento por defecto (`preventDefault`) solo cuando el cursor está sobre el visor de PDF.
  - Ctrl + rueda **sobre el panel de miniaturas** no cambia el zoom del PDF; las miniaturas solo se desplazan.
  - Al cambiar el zoom con la rueda, el selector de zoom muestra el porcentaje actual y se actualiza en el mismo instante.
- Sin Ctrl, la rueda sobre el canvas desplaza la página principal, y no cambia el zoom.
- Atajos de teclado: Ctrl + "+" aumenta el zoom, Ctrl + "−" lo reduce, Ctrl + 0 vuelve a 100 %. Estos atajos actúan solo cuando el visor de PDF tiene el foco, para no interferir con el zoom general del navegador en el resto de la app.
- El zoom responde en tiempo real: el cambio de escala se ve al instante, sin esperar a soltar el control.
- El zoom aplica a la página principal. El panel de miniaturas no cambia de tamaño con el zoom.

### 3.3 Problema C: salto de página por capítulo
El chec **"Salto de página en capítulos: H1 / 1, 2, 3… en página nueva"** hoy hace salto en **todos** los títulos, incluidos los subtítulos 2.1, 2.2, etc. Esto es un error.

**Regla correcta**
- El salto de página se aplica **solo** a los títulos **H1** (1, 2, 3…).
- Los títulos H2 (2.1, 2.2…) y H3 **no** generan salto de página.
- **Excepción de la primera hoja:** si antes del primer H1 hay un título general o una introducción breve, esa parte queda en la primera hoja y el primer H1 (el "1.") **no** fuerza salto de página, para que siga en la misma hoja. A partir del segundo H1 sí se aplica el salto.

**Ejemplo esperado**
```
Hoja 1: Título del documento
        Introducción breve
        1. Primer capítulo          ← sin salto de página (excepción de primera hoja)
        1.1 Subtítulo               ← sin salto
        1.2 Subtítulo               ← sin salto
Hoja 2: 2. Segundo capítulo         ← salto de página (es H1)
        2.1 Subtítulo               ← sin salto
Hoja 3: 3. Tercer capítulo          ← salto de página (es H1)
```

**Requisito adicional**
- La misma regla se aplica al chec de capítulos de la fusión (Fase 1) y, si existe, a la opción equivalente en Word y HTML. Un solo criterio para todas las exportaciones.

### 3.4 Criterios de aceptación (Fase 3)
- [ ] La vista previa del PDF muestra la primera página en menos de 2 segundos con un documento de tamaño medio, y el resto carga bajo demanda.
- [ ] El zoom vuelve a renderizar la página en tiempo real, con texto nítido y la hoja creciendo.
- [ ] Los controles de zoom (+, −, selector, Ctrl + rueda) funcionan.
- [ ] El salto de página por capítulo se aplica solo a H1.
- [ ] Los H2 y H3 no generan salto.
- [ ] La excepción de primera hoja funciona: la introducción y el primer H1 quedan en la misma hoja.

---

## 4. Pruebas obligatorias (al final de las tres fases)

1. Fusionar tres documentos con la casilla de capítulo activa y verificar hoja nueva por documento y numeración continua.
2. Fusionar los mismos tres documentos con la casilla desactivada y verificar flujo continuo.
3. Exportar a Word, PDF y HTML el documento de prueba con el diagrama del Anexo A; verificar legibilidad, figura flotante y ausencia de barras de desplazamiento en HTML.
4. Abrir la vista previa PDF: medir el tiempo hasta la primera página.
5. Hacer zoom al 200 % y al 300 %: verificar nitidez y crecimiento de la hoja.
6. Verificar que el salto de página solo ocurre antes de H1 (excepto el primer H1 si hay introducción en primera hoja).
7. Revisar consola del navegador y logs del servidor: sin errores.

---

## 5. Reporte obligatorio por fase

1. **Fase** y estado: completada, parcial o pendiente.
2. **Diagnóstico** de cada problema de la fase, con su causa.
3. **Archivos creados y modificados**, con su función.
4. **Funciones o endpoints nuevos o cambiados.**
5. **Dependencias nuevas** con justificación, o confirmación de que no hacen falta.
6. **Resultado de cada criterio de aceptación.**
7. **Pendientes y preguntas** para el usuario.

Después de entregar el reporte de cada fase, **detente** y espera la evaluación del usuario.

---

## 6. Preguntas que la IA debe hacer si no puede decidir

1. **Fusión:** ¿el documento fusionado se guarda como nuevo archivo al exportar, o solo existe en la pestaña Documentos?
2. **Figuras flotantes:** ¿el usuario decide cuáles envuelven el texto, o el documento lo indica con una marca? Propón una forma de marcarlas en el Markdown.
3. **Excepción de primera hoja:** confirma qué cuenta como "introducción breve" (por ejemplo, todo el texto antes del primer H1, o solo un número máximo de líneas).
4. **Word y HTML:** ¿la regla de salto por H1 también debe aplicarse allí? (Por defecto, sí.)

---

## Anexo A — Diagrama Mermaid de prueba

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
