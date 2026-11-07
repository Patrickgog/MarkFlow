# PLAN DE IMPLEMENTACIÓN  
## Maquetación Premium PDF — MarkFlow Office

**Versión del plan:** 1.0  
**Fecha:** 2026-11-06  
**Target versión MarkFlow:** 1.23.0+  
**Autor del plan:** Análisis de repositorio Patrickgog/MarkFlow  
**Alcance:** Nueva opción de maquetación seleccionable en la pestaña PDF + motor de renderizado editorial premium.

---

## 1. Objetivo

Añadir un **modo de maquetación Premium** como opción seleccionable en la pestaña PDF (junto a los modos existentes: Estándar, Dos Columnas, Paper Científico y Revista).

El modo Premium debe producir un PDF de aspecto profesional de alto nivel, inspirado en informes de consultoría ejecutiva e ingeniería de alta gama, con:

- Tarjetas de datos principales (KPI / resumen ejecutivo)
- Gráficos e imágenes tratados de forma premium (bordes, sombras sutiles, captions tipográficos, full-width o flotantes)
- Columnas duales **selectivas** (solo en secciones puntuales, no globales)
- Jerarquía visual reforzada (callouts, separadores, bloques de highlight)
- Portada ejecutiva mejorada + página de resumen opcional
- Compatibilidad total con el pipeline actual (Chromium Headless + CSS Paged Media + PyMuPDF post-proceso)

---

## 2. Análisis del estado actual (basado en el repositorio)

### 2.1 Componentes clave ya existentes

| Componente | Ubicación | Relevancia |
|------------|-----------|----------|
| Motor PDF | `motor/a_pdf.py` | Genera HTML5 + CSS Paged Media → Chromium → post-proceso PyMuPDF |
| Registro de opciones | `motor/registro_opciones.py` | SSOT de `MODOS_COLUMNAS_PDF`, `ESTILOS_MAQUETACION_PDF`, paletas |
| Generación HTML | `_generar_html_impresion()` | Ya soporta `modo_diseno` (`estandar`, `dos_columnas`, `paper_cientifico`, `revista`) y `estilo_maquetacion` (`informe`, `academico`, `portada`) |
| UI PDF | Shell Office + barra lateral 340 px | Consume `/api/registro-opciones` y envía opciones al endpoint de exportación |
| Assets | `motor/assets/` (KaTeX, Mermaid) | Ya se renderizan como imágenes |
| Post-proceso | `_postprocesar_con_pymupdf()` | Running headers, footers, numeración, membrete, outlines |

### 2.2 Limitaciones actuales que el modo Premium debe superar

- Los modos de columnas son **globales** (todo el cuerpo o nada).
- No existe concepto de “tarjetas de datos” ni bloques de KPI.
- Los gráficos/imágenes reciben tratamiento básico (centrado + `break-inside: avoid`).
- No hay sistema de “secciones con layout mixto” (1 col + 2 col selectivas).
- La portada es funcional pero genérica.

---

## 3. Diseño funcional del modo Premium

### 3.1 Nueva opción en el registro

```python
# motor/registro_opciones.py
MODOS_COLUMNAS_PDF = {
    "estandar": "📄 Estándar (1 Columna)",
    "dos_columnas": "📰 Dos Columnas (2 Col)",
    "paper_cientifico": "🔬 Paper Científico (IEEE / Academic 2 Col)",
    "revista": "🎨 Modo Revista (Editorial Magazine)",
    "premium": "✨ Premium Ejecutivo (Tarjetas + Layout Mixto)",   # ← NUEVO
}
```

También se puede añadir un estilo de maquetación complementario:

```python
ESTILOS_MAQUETACION_PDF = {
    "informe": "Informe Técnico Moderno",
    "academico": "Académico / Booktabs",
    "portada": "Ejecutivo con Portada",
    "premium": "Premium Consultoría (Tarjetas + Resumen)",   # opcional, o se activa con el modo
}
```

**Recomendación:** Activar el layout Premium principalmente desde `modo_columnas = "premium"`. El estilo puede permanecer “informe” o “portada” según se desee.

### 3.2 Características visuales del modo Premium

#### A. Tarjetas de datos principales (KPI Cards)

- Detección automática o por marcadores Markdown de bloques de resumen / datos clave.
- Renderizado como grid de tarjetas (1–4 columnas según cantidad).
- Estilo: fondo suave de la paleta, borde izquierdo de color primario, tipografía bold para el valor, label secundario.
- Ejemplo de marcador propuesto:

```markdown
:::kpi
**Caudal de diseño** | 125 L/s
**Población proyectada** | 2 480 hab
**Horizonte** | 20 años
**Inversión estimada** | USD 1.85 M
:::
```

o mediante un bloque especial que el saneador o el motor de HTML reconozca.

#### B. Gráficos e imágenes premium

- Contenedor con sombra sutil, radio de borde, padding y caption tipográfico.
- Opción de full-width o flotante izquierda/derecha.
- Mermaid y figuras reciben clase `.figura-premium`.
- Caption con numeración automática si se desea (“Figura 3 — Diagrama de flujo del reactor MBBR”).

#### C. Layout de dos columnas selectivo

- No se aplica `column-count: 2` al cuerpo completo.
- Se permite marcar secciones con:

```markdown
:::columns
Contenido de la columna izquierda...

---

Contenido de la columna derecha...
:::
```

- El motor convierte estos bloques en un `div.columns-premium` con CSS Grid o Flex + `break-inside: avoid`.

#### D. Otros elementos premium

- Callouts / notas técnicas con icono o borde reforzado.
- Separadores decorativos (filete con color secundario).
- Página de “Resumen Ejecutivo” opcional (después de portada).
- Mejor tipografía de títulos (tracking, peso, color primario).
- Tablas con estilo booktabs + cabecera de color primario.

### 3.3 Paletas recomendadas para Premium

Reutilizar las existentes + posiblemente añadir 1-2 nuevas orientadas a consultoría:

- `pizarra_carbon` (ya muy buena)
- `azul_prusia`
- Nueva posible: `ejecutivo_navy` o `consultoria_slate`

---

## 4. Plan de implementación por fases

### Fase 0 — Preparación (0.5 día)
- [ ] Crear rama `feature/pdf-premium-layout`
- [ ] Añadir entrada `"premium"` en `MODOS_COLUMNAS_PDF` de `registro_opciones.py`
- [ ] Actualizar defaults y documentación interna
- [ ] Verificar que la UI de la barra lateral PDF muestre la nueva opción automáticamente (consume el registro)

### Fase 1 — Motor de maquetación (2–3 días)
1. **Extender `_generar_html_impresion()`** en `motor/a_pdf.py`:
   - Añadir bloque CSS específico cuando `modo_clean == "premium"`.
   - Definir clases:
     - `.kpi-grid`, `.kpi-card`, `.kpi-valor`, `.kpi-label`
     - `.columns-premium` (CSS Grid 1fr 1fr, gap 12–16 mm)
     - `.figura-premium`, `.caption-premium`
     - `.callout-premium`, `.separador-premium`
   - Mantener `column-span: all` en tablas, figuras y títulos H1.

2. **Parser de bloques especiales** (nuevo o extensión de `sanear.py` / `a_html.py`):
   - Detectar `:::kpi ... :::` y `:::columns ... :::`.
   - Convertir a HTML semántico limpio.
   - Fallback seguro: si el bloque no se reconoce, se renderiza como texto normal.

3. **Tratamiento de imágenes/gráficos**:
   - Tras `reemplazar_mermaid_por_imagenes`, envolver las figuras en contenedor premium cuando el modo sea premium.
   - Añadir clases CSS y opcionalmente numeración de figuras.

### Fase 2 — Portada y resumen ejecutivo (1 día)
- Mejorar la portada cuando `estilo_maquetacion == "portada"` + modo premium (más espacio, mejor jerarquía, posible logo/membrete).
- Añadir generación opcional de página “Resumen Ejecutivo” (extrae los KPI + primeros párrafos o un bloque marcado).

### Fase 3 — Integración UI y API (1 día)
- Confirmar que la barra lateral PDF (registro de opciones) expone la nueva opción.
- Endpoint `/api/office/exportar-pdf` (o el que corresponda) debe recibir y reenviar `modo_columnas: "premium"`.
- Preview en el visor PDF (pdf.js) debe reflejar el nuevo estilo (el HTML intermedio ya lo tiene).

### Fase 4 — Post-proceso PyMuPDF y calidad (1 día)
- Verificar que running headers, footers, numeración y membrete no colisionan con las nuevas tarjetas/columnas.
- Ajustar márgenes o `break-inside` si es necesario.
- Generar outlines/marcadores de PDF correctos.

### Fase 5 — Tests y documentación (1–1.5 días)
- Añadir tests en `pruebas/` que generen un PDF premium con:
  - Bloque KPI
  - Sección de dos columnas
  - Figura Mermaid
  - Tabla
- Actualizar `docs/` o crear `docs/planes/PLAN_PDF_Premium.md` (este mismo documento).
- Entrada en historial de versiones.

---

## 5. Especificación técnica detallada

### 5.1 CSS clave del modo Premium (extracto)

```css
/* ===== MODO PREMIUM ===== */
.cuerpo-editorial.modo-premium {
  /* sin column-count global */
}

/* Tarjetas KPI */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  margin: 1.4em 0 1.8em 0;
  break-inside: avoid;
  page-break-inside: avoid;
}
.kpi-card {
  background: var(--fondo-suave);
  border-left: 3.5pt solid var(--primario);
  border-radius: 0 6px 6px 0;
  padding: 12px 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.kpi-valor {
  font-size: 1.35em;
  font-weight: 800;
  color: var(--primario);
  line-height: 1.15;
}
.kpi-label {
  font-size: 0.78em;
  color: var(--secundario);
  margin-top: 3px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

/* Columnas selectivas */
.columns-premium {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14mm;
  margin: 1.3em 0;
  break-inside: avoid;
  page-break-inside: avoid;
}
.columns-premium > div {
  /* contenido de cada columna */
}

/* Figuras premium */
.figura-premium {
  margin: 1.6em auto;
  text-align: center;
  break-inside: avoid;
  page-break-inside: avoid;
}
.figura-premium img {
  max-width: 100%;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.caption-premium {
  font-size: 8.5pt;
  color: #64748b;
  font-style: italic;
  margin-top: 6px;
}
```

### 5.2 Flujo de datos

```
Markdown (Docs / SSOT)
    ↓
sanear + detección de bloques :::kpi / :::columns
    ↓
a_html / motor de conversión → HTML semántico + clases premium
    ↓
_generar_html_impresion(modo_diseno="premium", ...)
    ↓
Chromium Headless (CSS Paged Media)
    ↓
_postprocesar_con_pymupdf (headers, footers, membrete, outlines)
    ↓
PDF final en storage/salidas/
```

### 5.3 Compatibilidad

- El modo Premium **no rompe** los modos anteriores.
- Si el usuario no usa los marcadores `:::kpi` / `:::columns`, el PDF sigue siendo un informe limpio de 1 columna con tipografía y tratamiento de figuras mejorados.
- Funciona con o sin membrete, con o sin portada.

---

## 6. Criterios de aceptación

1. La opción “✨ Premium Ejecutivo (Tarjetas + Layout Mixto)” aparece en la barra lateral de la pestaña PDF.
2. Al exportar con modo Premium se genera un PDF A4 profesional.
3. Los bloques `:::kpi` se convierten en tarjetas visuales.
4. Los bloques `:::columns` generan dos columnas locales.
5. Figuras y Mermaid reciben contenedor premium (sombra + caption).
6. Tablas, ecuaciones y títulos mantienen `break-inside: avoid`.
7. Running header / footer / numeración y membrete funcionan correctamente.
8. Tests automatizados pasan y existe al menos un PDF de ejemplo en `pruebas/`.
9. Documentación actualizada (este plan + entrada en historial).

---

## 7. Estimación de esfuerzo

| Fase | Esfuerzo estimado |
|------|-------------------|
| Fase 0 – Preparación | 0.5 día |
| Fase 1 – Motor + parser | 2.5 días |
| Fase 2 – Portada / resumen | 1 día |
| Fase 3 – UI / API | 1 día |
| Fase 4 – Post-proceso + polish | 1 día |
| Fase 5 – Tests + docs | 1.5 días |
| **Total** | **≈ 7.5 días** |

---

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| CSS Grid en Chromium Headless se comporta distinto | Probar exhaustivamente con el mismo Chromium que usa el motor; usar flex como fallback |
| Bloques `:::` no reconocidos rompen el flujo | Parser defensivo + fallback a texto plano |
| Colisión de márgenes con membrete | Reutilizar la lógica ya existente de `zona_cm` y `elementos_membrete` |
| Aumento de tamaño del PDF | Las tarjetas y sombras son CSS puro (vectorial); no se añaden imágenes extra |

---

## 9. Próximos pasos inmediatos

1. Confirmar el nombre exacto de la opción en la UI (“Premium Ejecutivo”, “Premium Consultoría”, etc.).
2. Decidir si los marcadores `:::kpi` y `:::columns` se documentan como extensión oficial de Markdown de MarkFlow.
3. Crear la rama e implementar Fase 0 + esqueleto de CSS de Fase 1.
4. Generar un documento de prueba real (memoria técnica hidrosanitaria) para validar el resultado visual.

---

**Archivo generado para descarga:**  
`PLAN_PDF_Premium_Maquetacion_v1.md`

*MarkFlow Office — Suite de documentos con IA, local-first y 100 % offline.*
