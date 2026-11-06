# 🎯 Plan Técnico — MarkFlow Office: Suite de Documentos con IA

**Fecha:** 2026-10-25
**Autor:** Consultoría técnica (ingeniería de software + hidrosanitaria)
**Proyectos de referencia analizados:** `morluto/rea` (REA) y `genspark-ai/genoffice` (GenOffice)
**Base actual:** MarkFlow AI v1.12.0 (`D:\APPS\Apps_2026\3_App_convertir_MARKFLOW_AI`)

---

## 1. Resumen Ejecutivo

El objetivo es evolucionar **MarkFlow AI** —hoy un conversor de Markdown a HTML/Word/PDF de alta calidad con control de calidad integrado— hacia una **suite de documentos con IA al estilo GenOffice**, pero con marca, foco y características propias:

- **Núcleo de conversión ya existente** (12 módulos en `motor/`) que GenOffice no tiene como ventaja comparativa: sanear Markdown, QA con paridad MD↔HTML, temas HTML/Word editoriales, fórmulas, Mermaid, índices, firmas y encabezados PDF.
- **Distribución agnóstica del agente** aprendida de REA: el producto debe ser usable no solo desde su interfaz, sino desde **cualquier harness de IA** (Claude Code, OpenCode, Copilot CLI) mediante **CLI + servidor MCP + agent-skill**.
- **Edición en formatos reales** (patrón "byte-preserving" de GenOffice): los .docx/.xlsx/.pptx editados se guardan modificando el XML original, no re-exportándolo, preservando el 100 % del formato heredado.
- **Stack recomendado:** conservar el backend **Python/FastAPI** (dominado, ya probado, con el clon local `3_App_convertir_md_genOffice` como puente directo) y adoptar librerías de editor JS **solo** donde aporte valor (ProseMirror/Tiptap para Docs, pdf.js para PDF, Univer para Sheets/Slides), empaquetadas localmente para mantener el principio **100 % offline**.

El desarrollo se propone en **6 fases** (Fundaciones → MVP Docs → DOCX/PDF avanzado → IA local → CLI/MCP/Skills → Sheets/Slides + empaquetado), con la Fase 1 entregable en un horizonte corto y sin tocar el motor de MarkFlow.

---

## 2. Análisis de los Proyectos de Referencia

### 2.1 GenOffice — `genspark-ai/genoffice`

| Aspecto | Detalle |
|---|---|
| **Qué es** | Primera suite ofimática IA open-source completa: Docs, Sheets, Slides, PDF, Markdown y HTML, editados por el usuario y su IA, guardados en formatos reales. |
| **Licencia / tracción** | Apache-2.0 · ~10.8k estrellas. |
| **Stack** | Monorepo TypeScript (Electron de escritorio + web). TurboRepo. |
| **Editores** | Tiptap/ProseMirror (Docs) · Univer (Sheets/Slides) · PDFium (PDF) · CodeMirror (MD/HTML). |
| **Idea maestra 1** | **Edición byte-preserving:** en lugar de "cargar → re-exportar" (que destruye formato), aplica parches quirúrgicos al XML OOXML original, preservando estilos, cabeceras, numeración y objetos heredados. |
| **Idea maestra 2** | **Motores compartidos:** 7 apps comparten una capa `packages/` de motores (conversión, IA, búsqueda) — cada app es una vista fina sobre la misma API. |
| **Idea maestra 3** | **Sidecar Rust** para operaciones xlsx de alto rendimiento que JS/TS no cubre bien. |
| **Distribución IA** | CLI `genoffice` con flujo por etapas (`deck_start → deck_page → deck_build`), servidor **MCP con 29 herramientas** en 3 modos de acceso, y **skills** (`SKILL.md`) para agentes. |
| **IA** | BYO-key (el usuario trae su clave de OpenAI/Anthropic/etc.), panel "Ask AI" con **citas** al documento, búsqueda **SQLite FTS + reranker** local. |
| **⚠️ Legal** | Los nombres y logos de Genspark son marca registrada: cualquier fork **debe usar marca propia** (Apache-2.0 §6). El código sí es reutilizable con atribución. |

### 2.2 REA — `morluto/rea`

| Aspecto | Detalle |
|---|---|
| **Qué es** | "Reverse Engineer Anything": un MCP único para ingeniería inversa de binarios, apps y comportamiento en ejecución. |
| **Licencia / tracción** | MIT · ~383k estrellas (distribución npm `rea-agents`). |
| **Idea maestra 1** | **Distribución agnóstica del agente:** el mismo producto sirve vía MCP (stdio/HTTP), CLI npm y agent-skills — funciona desde cualquier harness sin código específico. |
| **Idea maestra 2** | **Provider bridges:** en lugar de reescribir motores, adapta herramientas existentes (Hopper, Ghidra, IDA) tras una interfaz uniforme. |
| **Idea maestra 3** | **Local-first con evidencia:** todo dato/evidencia queda en disco local estructurado, auditable y reutilizable por sesiones posteriores. |
| **Idea maestra 4** | `server.json` publicado al **registro MCP** → descubrimiento e instalación en un comando. |
| **Arquitectura** | Monorepo turbo, skills declarativas, documentación multi-idioma. |

### 2.3 Clon local de GenOffice — `3_App_convertir_md_genOffice` (port Python)

Ya existe en tu disco un port Python de GenOffice, que sirve de **puente directo**:

```
backend/            server.py, ai_gateway.py, database_fts.py, file_manager.py
core_genoffice/     byte_preserver.py, converter.py, omml_math.py, tracked_changes.py
frontend/           vanilla JS (js/, styles/, index.html)
templates/          plantilla_base.docx
agents/             metodología multiagente: 6 agentes + adversarial-critic
```

**Lectura clave:** la parte más valiosa del clon es `core_genoffice/` (byte-preserver, OMML para fórmulas Word, tracked changes) — concepto poco duplicado en el ecosistema Python y naturalmente compatible con el stack de MarkFlow.

### 2.4 MarkFlow AI — base actual (v1.12.0)

```
motor/  (12 módulos)  ingesta · sanear · noise_stripper · capitulos · extraer ·
                      qa · reverse_converter · a_docx · a_html · a_pdf ·
                      a_mermaid · assets
app/                   principal.py · version.py · rutas/api.py · servicios/sesiones.py
frontend               Jinja2 + CSS tokens + JS vanilla (100 % offline, fuentes locales)
```

**Diferenciales que ningún competidor tiene combinados:** saneamiento de Markdown ruidoso (pegado de Word/ChatGPT), QA con paridad MD↔HTML, temas editoriales HTML y Word, Mermaid, fórmulas, índices con links, firma al final, numeración de páginas PDF configurable. Todo probado con 163 pruebas.

---

## 3. Producto Propuesto: **MarkFlow Office**

> *Suite de documentos con IA, local-first y 100 % offline, con foco en documentos técnicos y de ingeniería.*

**Nombre comercial sugerido:** `MarkFlow Office` (marca propia, sin referencia a Genspark).

| Aplicación | Formato | Fase | Estado base |
|---|---|---|---|
| **Docs** (MD + HTML) | .md / .html | Fase 1 | ya existe (pestaña Salida + temas) |
| **Word** | .docx | Fase 2 | conversión existe; edición = nuevo |
| **PDF** | .pdf | Fase 2 | conversión existe; visualización/edición = nueva |
| **Ingesta** (OCR/pegado/arrastre) | — | Fase 1 | ya existe en MarkFlow |
| **Sheets** | .xlsx | Fase 5 | nuevo (Univer) |
| **Slides** | .pptx | Fase 5 | nuevo (Univer) |

**Diferenciadores frente a GenOffice:**
1. Foco **documentos técnicos/de ingeniería**: fórmulas, diagramas Mermaid, tablas de cálculo, informes normados (RAS, RASANTE, etc.), memorias técnicas.
2. **Conversión Markdown de calidad superior** (motor MarkFlow) como puerta de entrada de todo el flujo.
3. **100 % offline por diseño** (fuentes, librerías y motores empaquetados localmente).
4. Español como lengua primaria de la UI y de la documentación.

---

## 4. Decisión de Stack

### Opción A — **Python/FastAPI + JS vanilla progresivo** ✅ RECOMENDADA

| Criterio | Evaluación |
|---|---|
| Reutilización | Máxima: el motor MarkFlow ya es Python; el clon GenOffice también |
| Curva de aprendizaje | Baja: stack ya dominado en ambos proyectos |
| Coste de mantenimiento | Bajo: un solo backend, un solo lenguaje de servidor |
| Editores avanzados | Se integran como **librerías JS del frontend** (ProseMirror, pdf.js, Univer) sin exigir monorepo TS en el servidor |
| Riesgo | Medio-bajo |

**Argumento central:** los editores de GenOffice (Tiptap, Univer) son librerías *de navegador*: funcionan igual de bien sobre un backend FastAPI que sobre Node. El monorepo TS de GenOffice es una elección de su equipo, no un requisito de sus librerías.

### Opción B — Monorepo TypeScript (fidelidad GenOffice)

Máxima similitud con GenOffice (turbo, packages/, apps/), pero implica reescribir el motor MarkFlow en TS o mantenerlo como microservicio Python aparte. Se descarta como fase inicial; puede ser destino futuro si se requiere empaquetado Electron completo.

**Decisión:** **Opción A**, con arquitectura de "motores" inspirada en GenOffice (capa `nucleo/`) y de "distribución de agente" inspirada en REA (CLI + MCP + skills).

---

## 5. Arquitectura Propuesta

```
┌──────────────────────────────────────────────────────────────────────┐
│  CAPA 4 · DISTRIBUCIÓN AGNÓSTICA (patrón REA)                        │
│  CLI `markflow` (typer)  ·  Servidor MCP  ·  Skill SKILL.md          │
├──────────────────────────────────────────────────────────────────────┤
│  CAPA 3 · FRONTEND (vanilla + librerías locales)                     │
│  Docs: ProseMirror/Tiptap · PDF: pdf.js · Vista MD: resaltado propio │
│  Sheets/Slides (F5): Univer · UI: tokens.css existentes              │
├──────────────────────────────────────────────────────────────────────┤
│  CAPA 2 · API FASTAPI (versionada /api/v1)                           │
│  sesiones · documentos · editores · ia · busqueda · exportaciones    │
├──────────────────────────────────────────────────────────────────────┤
│  CAPA 1 · NÚCLEO DE MOTORES (SSOT de lógica)                         │
│  motor/ MarkFlow (12 módulos)  +  core_genoffice/ (byte_preserver,   │
│  omml_math, tracked_changes)  +  ia_gateway  +  buscador_fts         │
└──────────────────────────────────────────────────────────────────────┘
```

### Estructura de directorios objetivo (Opción A)

```
3_App_convertir_MARKFLOW_AI/
├── nucleo/                    # CAPA 1 (refactor de motor/ + core del clon)
│   ├── conversion/            # a_docx, a_html, a_pdf, a_mermaid, reverse_converter
│   ├── calidad/               # qa, sanear, noise_stripper, capitulos
│   ├── ingesta/               # ingesta, extraer, assets
│   ├── docx_avanzado/         # byte_preserver, omml_math, tracked_changes (del clon)
│   └── ia/                    # ia_gateway (BYO-key, providers intercambiables)
├── app/
│   ├── rutas/                 # api.py + nuevos: documentos, ia, busqueda
│   └── servicios/
├── interfaces/                # CAPA 4 (patrón REA)
│   ├── cli/                   # typer: markflow convertir | sanear | exportar | preguntar
│   ├── mcp/                   # servidor MCP (stdio + HTTP), server.json
│   └── skill/                 # SKILL.md del agente
├── templates/ · static/       # frontend actual (evoluciona a editores)
├── pruebas/
└── docs/
```

> **Regla de oro (heredada de GenOffice):** los 7 productos (hoy: Ingesta, Docs, Word, PDF; mañana: Sheets, Slides, Chat) son **vistas finas** sobre la Capa 1. Ninguna lógica de negocio en `rutas/` ni en el frontend.

---

## 6. Mapa de Características (MarkFlow × GenOffice)

### 6.1 Características de MarkFlow que se conservan íntegras

| # | Característica | Módulo |
|---|---|---|
| 1 | Ingesta (pegado, arrastre, OCR) con saneamiento | `ingesta`, `sanear`, `noise_stripper` |
| 2 | Control de calidad (fórmulas, residuos `$`, paridad MD↔HTML) | `qa` |
| 3 | Temas HTML editoriales + paleta tricolor + ancho de lectura | `a_html`, `assets` |
| 4 | Temas Word + paleta de cuadros + color de títulos | `a_docx` |
| 5 | PDF editorial (numeración X de Y, encabezados, fuentes incrustadas) | `a_pdf` |
| 6 | Fórmulas LaTeX y diagramas Mermaid | `a_mermaid`, `a_docx` (OMML) |
| 7 | Capítulos, índices con links, firma al final | `capitulos` |
| 8 | Reverse conversion (DOCX→MD) | `reverse_converter` |
| 9 | UI: pila de sliders, Plus Jakarta Sans, degradados, tema claro/oscuro | `static/` |

### 6.2 Características de GenOffice a adoptar

| # | Característica | Origen | Fase |
|---|---|---|---|
| 1 | Edición byte-preserving de .docx (parches OOXML) | GenOffice core | F2 |
| 2 | Tracked changes (control de cambios) en Word | GenOffice core | F2 |
| 3 | Fórmulas OMML nativas en .docx | GenOffice core | F2 |
| 4 | Editor visual Docs (ProseMirror) sobre el Markdown saneado | GenOffice Docs | F1/F2 |
| 5 | Visualizador PDF integrado (pdf.js) | GenOffice PDF | F2 |
| 6 | Panel "Ask AI" con citas al documento | GenOffice | F3 |
| 7 | Búsqueda local SQLite FTS + reranker | GenOffice | F3 |
| 8 | BYO-key multi-provider (OpenAI/Anthropic/local) | GenOffice | F3 |
| 9 | CLI por etapas (`doc_start → doc_edit → doc_build`) | GenOffice CLI | F4 |
| 10 | MCP con herramientas y `server.json` | GenOffice + REA | F4 |
| 11 | Skill `SKILL.md` para harnesses de agentes | REA | F4 |
| 12 | Metodología multiagente (6 agentes + adversarial-critic) | Clon local `agents/` | Todas |

---

## 7. Plan por Fases

### Fase 0 — Fundaciones (sin features visibles)
- Extraer `core_genoffice/` del clon hacia `nucleo/docx_avanzado/` (byte_preserver, omml_math, tracked_changes) con sus pruebas.
- Encapsular `motor/` en `nucleo/` manteniendo compatibilidad (imports con alias; cero cambios de comportamiento).
- Publicar la API actual como `/api/v1/*` (alias de la existente) para congelar el contrato.
- **Criterio de salida:** suite verde (163+ pruebas) y `nucleo/` importable desde un REPL sin la app.

### Fase 1 — MVP "Docs" (la app ya se siente suite)
- Nueva pestaña **Editor**: edición visual del Markdown saneado con ProseMirror/Tiptap (empaquetado local), sincronizado bidireccionalmente con el texto plano.
- La pestaña Salida actual (v1.12.0) queda intacta como panel de exportación.
- Gestor de documentos múltiples (pestañas por documento, almacenamiento en `storage/`).
- **Entregable:** escribir/editar/previsualizar/exportar un documento técnico completo sin salir de la app.

### Fase 2 — Word y PDF avanzados
- Round-trip **.docx real**: abrir un .docx existente, editarlo (texto, títulos, tablas) con byte-preserving y guardar sin destruir formato heredado.
- Tracked changes visuales (aceptar/rechazar) y fórmulas OMML nativas.
- Visualizador PDF (pdf.js local) con vista previa de la maquetación antes de exportar.
- **Entregable:** abrir el .docx de un informe de ingeniería, editarlo con control de cambios y exportar el PDF final.

### Fase 3 — Capa IA local
- `ia_gateway` BYO-key: OpenAI, Anthropic, Google, y **Ollama local** (offline puro).
- Panel "Preguntar al documento" con respuestas **citadas** (número de párrafo/sección).
- Búsqueda semántica/FTS local (SQLite FTS5 + reranker) sobre todos los documentos de `storage/`.
- **Entregable:** "¿Dónde está el cálculo de la demanda máxima?" → respuesta con citas y salto al párrafo.

### Fase 4 — Distribución agnóstica de agente (patrón REA)
- **CLI `markflow`** (typer): `markflow sanear entrada.md`, `markflow convertir --a docx,pdf --tema ingenieria`, `markflow preguntar "..."`.
- **Servidor MCP** con herramientas: `sanea`, `convierte`, `qa`, `listar_temas`, `pregunta`, `exporta`… + `server.json` para el registro MCP.
- **Skill `SKILL.md`** documentando flujos para Claude Code/OpenCode/Copilot CLI.
- **Entregable:** un agente IA externo ejecuta el flujo completo de MarkFlow Office sin abrir la UI.

### Fase 5 — Sheets, Slides y empaquetado
- Editor de hojas (Univer local) con lectura/escritura .xlsx byte-preserving (sidecar opcional).
- Editor de presentaciones .pptx.
- Empaquetado de escritorio (Tauri o Electron) + instalador portable Windows.
- **Entregable:** suite instalable completa.

### Estimación orientativa de esfuerzo

| Fase | Contenido | Duración orientativa* |
|---|---|---|
| 0 | Fundaciones | 1–2 semanas |
| 1 | MVP Docs | 2–3 semanas |
| 2 | DOCX/PDF avanzado | 3–4 semanas |
| 3 | IA local | 2–3 semanas |
| 4 | CLI/MCP/Skills | 1–2 semanas |
| 5 | Sheets/Slides/Empaquetado | 4–6 semanas |

\* Ritmo actual de trabajo (iteraciones v1.11→v1.12 en una jornada), a validar en Fase 1.

---

## 8. Riesgos y Mitigaciones

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| 1 | Sobre-alcance (GenOffice son 7 apps y años de desarrollo) | Alta | Alto | Fases con entregables independientes; cada fase es útil por sí sola |
| 2 | Complejidad del byte-preserving OOXML | Media | Alto | Partir del clon `core_genoffice/` ya portado; pruebas de round-trip sobre documentos reales de ingeniería |
| 3 | Violación de marca (fork GenOffice) | Baja | Alto | Marca propia "MarkFlow Office"; atribución Apache-2.0 en NOTICE; cero logos/nombres de Genspark |
| 4 | Peso de librerías JS (Univer ~MBs, pdf.js) vs. offline | Media | Medio | Empaquetado local en `static/vendor/`; carga diferida por pestaña |
| 5 | Doble estándar de calidad entre la app y el CLI/MCP | Media | Medio | La Capa 1 (`nucleo/`) es el SSOT; CLI/MCP/API son envoltorios delgados |
| 6 | Regresiones en el motor MarkFlow al refactorizar | Media | Alto | Fase 0 con alias de imports + suite de 163 pruebas como red de seguridad; QA MarkFlow como verificación en cadena |
| 7 | Dependencia de APIs de IA de pago | Media | Medio | Ollama local como proveedor offline por defecto |

---

## 9. Siguientes Pasos Inmediatos

1. **Aprobar** el nombre comercial y el alcance de la Fase 1 (este documento).
2. **Fase 0**: migración de `core_genoffice/` → `nucleo/docx_avanzado/` con pruebas de round-trip DOCX.
3. Definir el contrato `/api/v1` (documentos, sesiones, exportaciones) y congelarlo.
4. Elegir la librería de editor Docs (ProseMirror *headless* recomendado sobre Tiptap UI completa) y descargar su build para `static/vendor/`.
5. Prototipo de la pestaña Editor con round-trip MD ⇄ ProseMirror sobre un informe real de ingeniería.

---

## 10. Principios de Diseño (heredados de los 3 proyectos)

1. **Local-first** (REA): todo dato, evidencia y documento vive en disco local estructurado; la nube es opcional (BYO-key).
2. **Formatos reales** (GenOffice): nunca "re-exportar" un documento; editar el original preservando todo.
3. **Motores como SSOT** (GenOffice): apps = vistas finas; sin lógica de negocio en UI ni rutas.
4. **Agnóstico del agente** (REA): CLI + MCP + skills desde el día 1 de la Fase 4; cualquier harness puede operar el producto.
5. **QA como ciudadano de primera** (MarkFlow): la paridad y los controles de calidad acompañan cada transformación.
6. **100 % offline por defecto**: fuentes, librerías y modelos locales; sin CDNs.
7. **Español primero**: UI, documentación y skills en español latinoamericano técnico.

---

*Documento generado como insumo de planificación. No altera el estado funcional de MarkFlow AI v1.12.0 (no requiere bump de versión).*
