# PLAN DE IMPLEMENTACIÓN  
## Portada Premium Configurable + Panel de Inputs (Slider)  
### MarkFlow Office — Pestaña PDF

**Versión del plan:** 1.1  
**Fecha:** 2026-11-06  
**Cambio 1.1:** Fotografías de campo soportan explícitamente de **1 a 6** imágenes con layouts automáticos.  
**Target versión MarkFlow:** 1.23.x / 1.24.0  
**Relación con plan anterior:** Complementa y extiende el plan de Maquetación Premium  
**Basado en:** Análisis de `motor/a_pdf.py`, `registro_opciones.py` + ejemplo real de portada (Memoria Técnica Fase II – Agua Potable) + investigación de portadas premium de consultoría/ingeniería.

---

## 1. Objetivo

Permitir que el usuario configure una **portada profesional de alta calidad** en la **primera hoja** del PDF, con:

1. **Varios temas/plantillas de portada premium** seleccionables (diseños inspirados en consultoría ejecutiva e ingeniería).
2. Un **nuevo panel deslizante (slider/sidebar)** en la pestaña PDF, **cerrado por defecto**, que contenga todos los inputs necesarios para rellenar la plantilla de portada.
3. Soporte nativo para el tipo de contenido del ejemplo real:
   - Título del estudio de consultoría
   - Nombre largo del proyecto (entre comillas)
   - Subtítulo de memoria / fase / componente
   - Galería de **1 a 6 fotografías** de campo (layouts automáticos según cantidad)
   - Datos del consultor / autor
   - Fecha / mes-año

El resultado debe ser un PDF A4 de primera hoja impecable, listo para entregables de ingeniería hidrosanitaria y consultoría.

---

## 2. Ejemplo de referencia (inputs reales extraídos de la imagen)

Del ejemplo proporcionado se identifican los siguientes campos de entrada:

| Campo | Valor de ejemplo | Tipo de input propuesto |
|-------|------------------|-------------------------|
| Tipo de documento | ESTUDIO DE CONSULTORÍA DEL PROYECTO: | Texto corto / select |
| Título del proyecto (largo) | “ESTUDIOS DE EVALUACIÓN, DIAGNÓSTICO Y DISEÑOS DEFINITIVOS DEL SISTEMA DE AGUA POTABLE Y SANEAMIENTO PARA LAS COMUNIDADES DE: FLOR DE LIMÓN Y GUAYAQUIL CHICO DE LA PARROQUIA GENERAL LEÓNIDAS PLAZA; SAN JORGE, MAIKUANTS Y WARINTS DE LA PARROQUIA SAN ANTONIO, CANTÓN LIMÓN INDANZA, PROVINCIA DE MORONA SANTIAGO”. | Textarea multilínea |
| Memoria / Fase | MEMORIA TÉCNICA FASE II | Texto |
| Componente | COMPONENTE AGUA POTABLE | Texto |
| Fotografías de campo | 1 a 6 imágenes (layouts automáticos) | Upload múltiple (mín. 1 – máx. 6) + reordenamiento |
| Consultor / Autor | Consultor: Ing. Patricio Sarmiento Reinoso | Texto |
| Fecha | JULIO 2024 | Texto o selector mes/año |
| (Opcional) Logo cliente / logo consultor | — | Upload imagen |
| (Opcional) Código de proyecto / Nº informe | — | Texto corto |

Estos campos se convierten en el **formulario del nuevo slider**.

---

## 3. Temas de Portada Premium (seleccionables)

Se proponen **5–6 temas** iniciales, inspirados en diseños premium de reportes técnicos y de consultoría (IEEE-style, consulting covers, architecture/engineering title blocks, minimal executive):

| ID Tema | Nombre | Estilo visual | Mejor para |
|---------|--------|---------------|------------|
| `clasica_blanca` | Clásica Blanca | Fondo blanco, tipografía centrada, fotos con sombra suave, filete inferior. Muy similar al ejemplo actual. | Memorias técnicas tradicionales |
| `ejecutiva_navy` | Ejecutiva Navy | Fondo azul profundo / navy, tipografía blanca, bloque de título con acento, title-block inferior. | Consultoría de alto nivel |
| `blueprint` | Blueprint Técnico | Fondo azul plano con grid sutil, líneas de trazado, title-block de ingeniería. | Informes de ingeniería / planos |
| `foto_hero` | Foto Hero | Una foto grande de fondo (o collage), overlay semitransparente, texto sobreimpreso. | Proyectos con fuerte componente de campo |
| `minimal_slate` | Minimal Slate | Gris pizarra, mucho espacio en blanco, tipografía elegante, fotos en franja inferior. | Estilo corporativo moderno |
| `consultoria_verde` | Consultoría Verde/Salvia | Tonos verdes profesionales (hidrosanitario), acentos naturales. | Especialmente adecuado para agua y saneamiento |

Cada tema define:
- Paleta de colores
- Posición y tamaño de textos
- Layout de la galería de fotos **adaptativo según cantidad (1 a 6)**:
  - 1 foto → centrada grande
  - 2 fotos → lado a lado
  - 3 fotos → 2 arriba + 1 centrada abajo (o fila de 3)
  - 4 fotos → grid 2×2
  - 5 fotos → 2×2 + 1 centrada abajo (como el ejemplo)
  - 6 fotos → grid 3×2 o 2×3
- Estilo de filetes, sombras y title-block

---

## 4. Nuevo UI: Slider / Panel de Portada (cerrado por defecto)

### 4.1 Ubicación y comportamiento

- Aparece en la **pestaña PDF** de la shell Office.
- Es un **panel deslizante lateral** (o sección colapsable dentro de la barra lateral de 340 px existente).
- **Estado por defecto: cerrado / colapsado**.
- Título del panel: **“Portada Premium”** o **“Configurar Portada”**.
- Al abrirlo se muestran:
  1. Selector de **Tema de Portada** (radio buttons o cards visuales pequeños).
  2. Formulario de inputs (plantilla).
  3. Vista previa en miniatura de la portada (opcional, pero muy recomendable).
  4. Toggle “Incluir portada en el PDF” (activado por defecto cuando se abre el panel).

### 4.2 Estructura del formulario (inputs)

```
┌─────────────────────────────────────────────┐
│  PORTADA PREMIUM                      [×]   │
├─────────────────────────────────────────────┤
│  Tema de portada                            │
│  ○ Clásica Blanca  ○ Ejecutiva Navy         │
│  ○ Blueprint       ○ Foto Hero              │
│  ○ Minimal Slate   ○ Consultoría Verde      │
├─────────────────────────────────────────────┤
│  Tipo de documento                          │
│  [ ESTUDIO DE CONSULTORÍA DEL PROYECTO: ]   │
│                                             │
│  Título del proyecto (largo)                │
│  [_____________________________________]    │
│  [_____________________________________]    │
│  [_____________________________________]    │
│                                             │
│  Memoria / Fase                             │
│  [ MEMORIA TÉCNICA FASE II            ]     │
│                                             │
│  Componente                                 │
│  [ COMPONENTE AGUA POTABLE            ]     │
│                                             │
│  Fotografías de campo (1 a 6)               │
│  [ + Subir imágenes ]  (mín. 1 – máx. 6)    │
│  (drag & drop + reordenar)                  │
│                                             │
│  Consultor / Autor                          │
│  [ Ing. Patricio Sarmiento Reinoso    ]     │
│                                             │
│  Fecha                                      │
│  [ JULIO 2024 ]                             │
│                                             │
│  Logo cliente (opcional)   [ Subir ]        │
│  Logo consultor (opcional) [ Subir ]        │
│  Código de proyecto (opcional)              │
│  [________________]                         │
├─────────────────────────────────────────────┤
│  ☑ Incluir esta portada como primera hoja   │
│  [ Guardar plantilla ]  [ Restablecer ]     │
└─────────────────────────────────────────────┘
```

Los valores se guardan en el registro de opciones de la sesión (o en `storage/`) para reutilizarlos.

---

## 5. Integración técnica con el motor PDF

### 5.1 Extensión de `registro_opciones.py`

```python
# Nuevo bloque dentro de REGISTRO_OPCIONES["pdf"]
"portada_premium": {
    "temas": {
        "clasica_blanca": "Clásica Blanca (ejemplo actual)",
        "ejecutiva_navy": "Ejecutiva Navy",
        "blueprint": "Blueprint Técnico",
        "foto_hero": "Foto Hero",
        "minimal_slate": "Minimal Slate",
        "consultoria_verde": "Consultoría Verde / Agua",
    },
    "defaults": {
        "tema": "clasica_blanca",
        "incluir": False,          # por defecto no se fuerza
        "tipo_documento": "ESTUDIO DE CONSULTORÍA DEL PROYECTO:",
        "titulo_proyecto": "",
        "memoria_fase": "",
        "componente": "",
        "consultor": "",
        "fecha": "",
        "codigo_proyecto": "",
        # las imágenes se manejan por separado (rutas o base64 temporales)
    }
}
```

### 5.2 Flujo en `motor/a_pdf.py`

1. Si `opciones["portada_premium"]["incluir"] == True`:
   - Generar HTML de portada **completo** según el tema seleccionado + los inputs.
   - Insertar como **primera página** (`page-break-after: always`).
2. El resto del documento sigue el modo de maquetación elegido (Premium, Estándar, etc.).
3. En el post-proceso PyMuPDF:
   - Omitir running header / numeración en la página 1 (portada).
   - Aplicar membrete solo a partir de la página 2 si está configurado.

### 5.3 Generación de la portada

Nueva función recomendada:

```python
def _generar_html_portada_premium(
    tema: str,
    datos: dict,          # todos los inputs del slider
    imagenes: list[Path | str],  # rutas o data-uri
    paleta: dict,
) -> str:
    ...
```

Cada tema tendrá su propio template HTML + CSS (o un único template parametrizado con clases CSS distintas).

### 5.4 Manejo de imágenes (1 a 6 fotos)

- Las fotos se suben temporalmente a `storage/temp_portada/` o se convierten a base64.
- **Rango permitido: mínimo 1 – máximo 6** fotografías.
- Disposición automática según la **cantidad** de fotos y el tema seleccionado:

| Cantidad | Layout recomendado (Clásica / Verde / Minimal) | Variante Foto Hero / Navy |
|----------|------------------------------------------------|---------------------------|
| 1        | 1 foto centrada grande                         | Fondo hero completo       |
| 2        | 2 fotos lado a lado                            | 2 columnas                |
| 3        | 2 arriba + 1 centrada abajo                    | Fila de 3 o 1+2           |
| 4        | Grid 2×2                                       | Grid 2×2                  |
| 5        | 2×2 + 1 centrada abajo (ejemplo real)          | 2×2 + 1                   |
| 6        | Grid 3×2 o 2×3                                 | Grid 3×2                  |

- Validación en frontend y backend: rechazar 0 fotos o más de 6.
- Cada foto mantiene sombra sutil y bordes redondeados leves.

---

## 6. Plan de implementación por fases

### Fase A — Modelo de datos y registro (0.5–1 día)
- Extender `registro_opciones.py` con el bloque `portada_premium`.
- Definir esquema de datos (Pydantic o dict tipado) para los inputs.
- Guardar / cargar valores de sesión.

### Fase B — UI del Slider (1.5–2 días)
- Crear el panel colapsable “Portada Premium” en la barra lateral PDF.
- Formulario completo con validación básica.
- Selector visual de temas (cards o radio con preview pequeño).
- Upload de imágenes con reordenamiento (drag & drop simple).
- Toggle “Incluir portada”.
- Guardar estado en el frontend y enviarlo en el payload de exportación.

### Fase C — Motor de generación de portada (2–2.5 días)
- Implementar `_generar_html_portada_premium()`.
- Desarrollar al menos 3 temas completos primero (`clasica_blanca`, `ejecutiva_navy`, `consultoria_verde`).
- Integrar en el flujo de `_generar_html_impresion()` o como página previa.
- Soporte de galería de fotos con CSS Grid / Flex responsive a A4.

### Fase D — Post-proceso y calidad (1 día)
- Excluir numeración y running header de la portada.
- Verificar márgenes, sombras de fotos y saltos de página.
- Asegurar que el membrete (si existe) no se solape con la portada.

### Fase E — Tests, plantillas de ejemplo y documentación (1 día)
- Test automatizado que genere un PDF con la portada del ejemplo real.
- Guardar una plantilla de ejemplo pre-rellenada (Memoria Técnica Agua Potable).
- Actualizar este plan y el historial de versiones.

**Esfuerzo total estimado:** 6–7.5 días.

---

## 7. Criterios de aceptación

1. Existe un panel “Portada Premium” en la pestaña PDF, **cerrado por defecto**.
2. El usuario puede elegir entre varios temas premium.
3. Todos los campos del ejemplo real se pueden rellenar (título largo, fase, componente, fotos, consultor, fecha).
4. Al exportar con “Incluir portada” activado, la primera hoja del PDF es la portada configurada.
5. Se aceptan de **1 a 6 fotografías**; el layout se adapta automáticamente según la cantidad (1→centrada, 5→2×2+1, 6→3×2, etc.).
6. La numeración de páginas empieza en 1 a partir de la segunda hoja (o se puede configurar).
7. Los valores del formulario se recuerdan durante la sesión.
8. Al menos 3 temas visualmente distintos están implementados y documentados.

---

## 8. Prioridad de temas a implementar

**MVP (Fase C):**
1. `clasica_blanca` (reproduce el ejemplo actual)
2. `ejecutiva_navy`
3. `consultoria_verde` (especialmente útil para hidrosanitaria)

**Siguiente iteración:**
4. `blueprint`
5. `foto_hero`
6. `minimal_slate`

---

## 9. Notas de diseño y UX

- El slider debe sentirse nativo de la shell Office (mismo lenguaje visual, tokens CSS, 340 px).
- Las previews de temas deben ser pequeñas pero reconocibles.
- El título largo del proyecto debe soportar 4–6 líneas sin romper el layout.
- Las fotos deben tener sombra sutil y bordes redondeados leves (como en el ejemplo).
- Permitir “Guardar como plantilla de portada” para reutilizar en futuros proyectos del mismo cliente.

---

## 10. Próximos pasos recomendados

1. Confirmar la lista de campos exactos del formulario (¿falta algún input del ejemplo?).
2. Decidir si el panel vive dentro de la barra lateral actual o es un drawer independiente.
3. Empezar por el tema `clasica_blanca` para validar el flujo completo con el ejemplo real que envió el usuario.
4. Una vez validado, expandir a los demás temas.

---

**Archivo generado:**  
`PLAN_PDF_Portada_Premium_Configurable_v1.md`

*MarkFlow Office — Suite de documentos con IA, local-first y 100 % offline.*
