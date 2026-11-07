# MarkFlow Office

> **Suite de documentos con IA, local-first y 100 % offline.**
> Motor de conversión **MarkFlow** + núcleo DOCX **byte-preserving de GenOffice**,
> con distribución agnóstica del agente (CLI · MCP · Skill) al estilo REA.

![Versión](https://img.shields.io/badge/versi%C3%B3n-1.23.4-4c6ef5) ![Licencia](https://img.shields.io/badge/licencia-Apache--2.0-green) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)

---

## Índice

1. [Qué es](#qué-es)
2. [Características principales](#características-principales)
3. [Arquitectura en capas](#arquitectura-en-capas)
4. [Requisitos](#requisitos)
5. [Instalación desde cero](#instalación-desde-cero)
6. [Arranque](#arranque)
7. [CLI (sin UI)](#cli-sin-ui)
8. [Servidor MCP](#servidor-mcp)
9. [API HTTP (resumen de endpoints)](#api-http-resumen-de-endpoints)
10. [Estructura del proyecto](#estructura-del-proyecto)
11. [Configuración de IA](#configuración-de-ia)
12. [Plantillas y placeholders](#plantillas-y-placeholders)
13. [Pruebas](#pruebas)
14. [Versionado](#versionado)
15. [Licencias y atribuciones](#licencias-y-atribuciones)
16. [Autor](#autor)

---

## Qué es

**MarkFlow Office** es una aplicación web local (FastAPI) que transforma Markdown defectuoso
(procedente de asistentes de IA como ChatGPT, Claude o NotebookLM) en documentos profesionales
(MD limpio, HTML, DOCX y PDF), con una shell de oficina estilo GenOffice y un panel de IA
local (Ollama) o BYO-key (OpenAI/Anthropic/Gemini). Todo funciona 100 % offline por defecto.

## Características principales

- 📄 **Documentos** — almacén local con búsqueda de texto completo (SQLite FTS5).
- 📝 **Docs** — editor visual ProseMirror + visor dual con sincronización de scroll, saneamiento y soporte de inserción de imágenes por referencia Markdown `![nombre][img-N]` con paste y drag-and-drop. Docs opera como el Single Source of Truth (SSOT) de contenido para todas las exportaciones.
- 📘 **Word** — visor amplio de páginas continuas A4 maquetadas y barra lateral deslizable (340 px) conectada al registro único de opciones (paletas, tipografía, interlineado y opciones avanzadas).
- 📕 **PDF** — visor de documentos PDF con barra lateral deslizable (340 px) y exportación limpia sin descarga de archivos `.htm`.
- 🌐 **HTML** — visor interactivo con previsualización responsive y barra lateral deslizable (340 px) para configuración de temas y paletas.
- 📊 **Excel (Tablas)** — mesa de trabajo interactiva de hojas de cálculo con soporte para exportación multi-hoja / hoja única, copiado enriquecido al portapapeles y barra lateral deslizable (340 px).
- 📦 **Entregables** — pestaña independiente en el riel de navegación principal para auditar, gestionar y descargar directamente todos los artefactos generados en la sesión.
- ⚡ **MarkFlow** — motor clásico completo embebido (`/clasico`): ingesta → QA → salidas HTML/DOCX/PDF/MD.
- 📕 **PDF** — visor local con pdf.js vendorizado (biblioteca de entregables en `salidas/`, navegación de páginas y zoom, 100 % offline).
- ✅ **Control de cambios (tracked changes)** — marcas visuales de inserción (verde) y borrado (rojo) en Docs con botones **aceptar/rechazar**; representación Markdown con CriticMarkup (`{++insertado++}`/`{--borrado--}`) y redline `w:ins`/`w:del` nativo de Word en el round-trip .docx.
- ✨ **Panel IA** — "Preguntar IA" con Ollama local (offline) o BYO-key (OpenAI/Anthropic/Gemini).
- 🧩 **Plantillas y placeholders** — detección de candidatos, generación de paquetes (MD + XLSX + JSON + ZIP) y fusión masiva por proyecto.
- 🔄 **Round-trip .docx** — importar un .docx a Markdown y reguardarlo conservando el resto del paquete OOXML byte a byte (estilos, cabeceras, medios).

## Arquitectura en capas

| Capa | Componente | Origen |
|---|---|---|
| **Capa 4 · Agente** | CLI `python -m interfaces.cli` · MCP `python -m interfaces.mcp` · `SKILL.md` | patrón REA |
| **Capa 3 · Frontend** | Shell Office (riel de apps + panel IA) + barras laterales dedicadas (340 px) | estética GenOffice + identidad MarkFlow |
| **Capa 2 · API** | FastAPI `/api/*` (MarkFlow) + `/api/documentos` + `/api/office` + `/api/registro-opciones` + `/api/plantillas` | FastAPI |
| **Capa 1 · Núcleo** | `motor/` MarkFlow (saneamiento, QA, temas, PDF, Excel) + `nucleo/docx_avanzado` (byte-preserving, OMML) + `nucleo/ia` + `nucleo/busqueda` FTS5 | MarkFlow AI + clon GenOffice |

## Requisitos

- **Python 3.10+** (probado en 3.13/3.14).
- **pandoc** (opcional pero recomendado para el motor DOCX completo).
- **Chromium/Chrome** (opcional, para exportación PDF editorial de alta gama).
- **Ollama** (opcional, para el panel IA local).
- Sistema operativo: Windows (lanzadores `.bat`); el backend es multiplataforma.

## Instalación desde cero

```powershell
# 1. Clonar el repositorio
git clone https://github.com/Patrickgog/MarkFlow.git
cd MarkFlow

# 2. Crear entorno virtual
python -m venv .venv

# 3. Instalar dependencias
.venv\Scripts\pip install -r requirements.txt
```

Dependencias principales (ver `requirements.txt`):

- **Web:** `fastapi`, `uvicorn`, `jinja2`, `python-multipart`, `pydantic`
- **Pruebas:** `httpx`, `pytest`
- **Motor MarkFlow:** `markdown-it-py`, `mdit-py-plugins`, `python-docx`, `Pillow`, `pymupdf`, `openpyxl`
- **Núcleo DOCX (GenOffice):** `lxml`
- **Gateway IA:** `requests`

## Arranque

```bat
lanza_MarkFlowOffice.bat      :: puerto 8320, abre el navegador
```

o manual:

```powershell
.venv\Scripts\python.exe -m uvicorn app.principal:app --port 8320
```

- Shell Office: `http://127.0.0.1:8320/`
- Motor clásico MarkFlow: `http://127.0.0.1:8320/clasico`
- Documentación OpenAPI: `http://127.0.0.1:8320/docs`

El lanzador (`start_MFO.bat` / `lanza_MarkFlowOffice.bat`) detecta dinámicamente el intérprete
Python (3.10–3.15), crea el `.venv` si no existe, instala dependencias si faltan y busca un
puerto libre a partir de 8320.

## CLI (sin UI)

```bash
python -m interfaces.cli version
python -m interfaces.cli sanear entrada.md -o salida.md
python -m interfaces.cli convertir entrada.md -o informe.docx --plantilla
python -m interfaces.cli documentos
python -m interfaces.cli buscar "demanda máxima"
python -m interfaces.cli servir --puerto 8320
```

## Servidor MCP

```bash
python -m interfaces.mcp        # stdio, JSON-RPC; registro: interfaces/mcp/server.json
```

Herramientas expuestas: `version`, `listar_documentos`, `leer_documento`, `sanear_texto`,
`exportar_docx`, `buscar`.

## API HTTP (resumen de endpoints)

Todos los endpoints de la API clásica usan el sobre estándar
`{"ok": bool, "datos": {...} | null, "errores": [{"codigo", "detalle"}]}`.

| Prefijo | Recursos principales |
|---|---|
| `/api` | `GET /version`, `GET /temas`, `GET /registro-opciones`, `POST /ingesta`, `POST /consolidar`, `POST /formatear`, `POST /transformar`, `POST /extraer-inverso`, `POST /render-preview`, `GET/POST /descargar|ver` |
| `/api/documentos` | `GET ""` (listar), `POST ""` (crear), `GET/PUT/DELETE /{nombre}`, `POST /fusionar`, `POST /{nombre}/renombrar`, `GET /{nombre}/descargar`, `POST /buscar` |
| `/api/office` | `GET /salud`, `GET/POST /ia/config`, `POST /ia/pregunta`, `POST /exportar-docx`, `POST /exportar-html`, `POST /exportar-pdf`, `POST /compilar-completo`, `POST /exportar-tablas-excel`, `POST /extraer-tablas`, `POST /md-a-json`, `POST /json-a-md`, `POST /sanear`, `POST /docx-importar`, `POST /docx-reguardar`, `GET /pdfs`, `GET/DELETE /pdfs/archivo/{ruta}` |
| `/api/plantillas` | `POST /analizar`, `POST /crear-paquete`, `POST /leer-datos`, `POST /extraer-placeholders`, `POST /validar`, `POST /generar-documentos` |
| `/api/office/plantillas-word` | `GET ""` (listar membrete), `GET/POST /{archivo}/analisis|zona` |

## Estructura del proyecto

```
MarkFlow/
├── app/                    FastAPI (principal, rutas: api · documentos · office · plantillas + servicios)
│   ├── principal.py       Fábrica de la app (lifespan, routers, estáticos)
│   ├── version.py         SSOT de la versión (APP_VERSION)
│   ├── rutas/             Routers por dominio
│   └── servicios/         sesiones, editor_markdown, roundtrip_docx
├── motor/                 Motor MarkFlow (conversión y QA)
│   ├── sanear.py          Saneamiento de Markdown
│   ├── qa.py              Auditoría de calidad
│   ├── a_html.py          Exportación HTML
│   ├── a_docx.py          Exportación DOCX
│   ├── a_pdf.py           Exportación PDF editorial
│   ├── membrete.py        Hojas de membrete (Word/PDF)
│   ├── plantillas.py      Placeholders y fusión por proyecto
│   ├── ingesta.py         Ingesta de archivos
│   ├── extraer.py         Extracción DOCX→MD (pandoc)
│   ├── reverse_converter.py Conversión inversa DOCX/PDF→MD con imágenes
│   ├── registro_opciones.py Registro único de opciones
│   ├── capitulos.py       Consolidación de documentos
│   ├── formulas.py        Fórmulas LaTeX
│   ├── notas.py           Notas y anotaciones
│   └── assets/            mermaid, katex (vendorizados, 100 % local)
├── nucleo/                Capa 1
│   ├── docx_avanzado/     Núcleo DOCX byte-preserving (GenOffice): converter, omml_math, tracked_changes, byte_preserver
│   ├── ia/                Gateway IA (Ollama local + BYO-key externo)
│   └── busqueda/          Índice FTS5 (SQLite)
├── interfaces/            Capa 4
│   ├── cli/               CLI markflow
│   ├── mcp/               Servidor MCP (stdio, JSON-RPC)
│   └── skill/SKILL.md     Skill para agentes
├── templates/             office.html (shell) · index.html (clásico) · temas_html/ · temas_word/
├── static/                css (tokens/base/components/office) · fonts locales · js · vendor (prosemirror, pdfjs)
├── storage/               documentos/ · salidas/ · busqueda/ · plantillas_word/ · config_ia.json
├── plantillas/            plantilla_base.docx (byte-preserving)
├── docs/                  PLAN_Suite_Documentos_IA.md · planes/ · metodologia_agentes/
├── pruebas/               Suite de tests (pytest)
├── requirements.txt
├── pytest.ini
├── GEMINI.md              Reglas de desarrollo del proyecto
└── lanza_MarkFlowOffice.bat
```

## Configuración de IA

El panel "Preguntar IA" soporta dos proveedores:

1. **Ollama local (offline)** — por defecto en `http://localhost:11434`, modelo `llama3`.
   Instala Ollama y ejecuta `ollama pull llama3`.
2. **BYO-key externo** — OpenAI, Anthropic o Gemini. Las claves se guardan en
   `storage/config_ia.json` (excluido del repositorio) y se enmascaran en la UI.

La configuración se gestiona desde la UI (`/api/office/ia/config`) o editando el JSON.

## Plantillas y placeholders

MarkFlow Office incluye un sistema de plantillas con placeholders `{{ nombre }}`:

- **Detectar candidatos** (`/api/plantillas/analizar`) — analiza un Markdown y propone
  candidatos a placeholder clasificados por confianza.
- **Crear paquete** (`/api/plantillas/crear-paquete`) — genera `plantilla_<proyecto>.md`,
  `plantilla_<proyecto>_datos.xlsx`, `plantilla_<proyecto>_datos.json` y un `.zip`.
- **Leer datos** (`/api/plantillas/leer-datos`) — parsea XLSX/JSON de datos por proyecto.
- **Validar** (`/api/plantillas/validar`) — valida un proyecto contra los placeholders.
- **Generar documentos** (`/api/plantillas/generar-documentos`) — fusión y compilación
  a HTML/DOCX/PDF/MD para uno o varios proyectos.

## Pruebas

```powershell
.venv\Scripts\python.exe -m pytest -q
```

La suite vive en `pruebas/` (más de 40 archivos de test) y cubre el motor, la API,
las fases de membrete (Word/PDF), la paridad de renderizado y el round-trip.

## Versionado

El proyecto sigue **SemVer** (`X.Y.Z`). El SSOT de la versión es `app/version.py`
(`APP_VERSION`); la UI y los planes leen esa constante (nunca se hardcodea).
Cada incremento se registra en `historial-resumenes/` (archivo `AAAA-MM-DD_vX.Y.Z_titulo.md`).
Versión vigente: **1.23.4**.

## Licencias y atribuciones

- **Código propio del proyecto:** Apache-2.0 (ver `LICENSE`).
- **Núcleo DOCX (`nucleo/docx_avanzado/`):** adaptado de
  [genspark-ai/genoffice](https://github.com/genspark-ai/genoffice) (Apache-2.0).
  Nombres y logos de Genspark/GenOffice son marca registrada: este proyecto usa marca propia.
- **Patrón CLI/MCP/Skill:** inspirado en [morluto/rea](https://github.com/morluto/rea) (MIT).
- **Motor MarkFlow:** código propio del proyecto MarkFlow AI.
- **Editor visual (`static/vendor/prosemirror/`):** [ProseMirror](https://prosemirror.net)
  — bundle oficial del sitio y CSS base (MIT, © Marijn Haverbeke y colaboradores),
  vendorizados y servidos 100 % local (ver `static/vendor/prosemirror/VENDOR.md`).
- **Visor PDF (`static/vendor/pdfjs/`):** pdf.js (Apache-2.0), vendorizado y servido 100 % local
  (ver `static/vendor/pdfjs/VENDOR.md`).
- **Render matemático (`motor/assets/katex/`):** KaTeX (MIT).
- **Diagramas (`motor/assets/mermaid/`):** Mermaid (MIT).

## Autor

**Patricio Sarmiento Reinoso** (GitHub: [@Patrickgog](https://github.com/Patrickgog))
— Ing. Civil, Mgst. en Ingeniería Hidrosanitaria.

---

*MarkFlow Office — Suite de documentos con IA, local-first y 100 % offline.*
