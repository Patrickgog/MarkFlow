# Dependencias de proveedor — Editor visual Docs (Fase 1)

Archivos oficiales de **ProseMirror** vendorizados para servir el editor visual
**100 % local** (sin CDN en runtime, requisito offline-first de MarkFlow Office).

| Archivo | Origen | Rol | Licencia |
|---|---|---|---|
| `pm_bundle.js` (254 KB) | `https://prosemirror.net/examples/prosemirror.js` (build oficial del sitio) | Bundle IIFE clásico que expone `window.PM` con los módulos `model`, `transform`, `state`, `view`, `keymap`, `inputrules`, `history`, `commands`, `schema_basic`, `schema_list`, `dropcursor`, `gapcursor`, `menu`, `example_setup` | MIT |
| `pm_editor.css` (7 KB) | `https://prosemirror.net/css/editor.css` | Estilos base `.ProseMirror` (posición, pre-wrap, cursor, gapcursor). La tipografía y los colores se redefinen en `static/css/office.css` con los tokens SSOT | MIT |

## Por qué este formato

El entorno de desarrollo corporativo bloquea toda URL con `@` en la ruta
(paquetes con scope de npm/jDelivr/unpkg/esm.sh y el CLI de npm). El bundle del
sitio oficial de ProseMirror (`prosemirror.net`) es un IIFE clásico accesible
sin `@` y equivale funcionalmente a instalar `@prosemirror/*`: se asigna a
`window.PM` y `static/js/editor_docs.js` lo consume sin import maps ni ESM.

## Carga

- El bundle **no** se incluye en el HTML: `static/js/office.js` lo inyecta de
  forma perezosa (`cargarPM()`) solo cuando el usuario abre la app **Docs**,
  con *fallback* automático al modo fuente si la carga falla.
- `static/js/editor_docs.js` (script clásico, sin módulos) construye el esquema
  y la vista leyendo `window.PM`.

## Licencia

ProseMirror es software de código abierto bajo la **Licencia MIT**:

> Copyright (C) 2015-present, Marijn Haverbeke and other contributors.
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software to deal in the Software without restriction, subject to the
> conditions of including the above copyright notice in copies or substantial
> portions of the Software.

Atribución registrada también en el `README.md` del proyecto.
