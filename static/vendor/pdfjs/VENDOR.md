# Vendor: pdf.js (visor PDF local)

- **Componente:** Mozilla pdf.js — build *legacy dist* (UMD, `window.pdfjsLib`)
- **Versión:** 3.11.174 (noviembre 2023, última con build UMD clásico)
- **Origen:** https://github.com/mozilla/pdf.js/releases/tag/v3.11.174
- **Licencia:** Apache-2.0 (ver `LICENSE`)

## Archivos

| Archivo | Papel |
|---|---|
| `pdf.js` (695 KB) | API principal (`window.pdfjsLib`) |
| `pdf.worker.js` (2 MB) | Worker de parseo/render (servido local) |

## Motivo del vendor

Entorno corporativo offline: los paquetes npm con `@` (scoped) y los CDN
(jsDelivr/unpkg/esm.sh) están bloqueados por el proxy. El patrón es el mismo
que el de ProseMirror (`window.PM`): script clásico servido localmente y
cargado con pereza solo al abrir la app PDF.

## Configuración

`GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.js"`
(establecido por `static/js/visor_pdf.js` antes del primer `getDocument`).

## Sin incluir

- `cmaps/` y `standard_fonts/` (solo necesarios para CJK/fuentes no embebidas;
  documentos de ingeniería en español no los requieren — añadibles si surge).
- `web/viewer.*` (la UI del visor es propia de MarkFlow Office).
