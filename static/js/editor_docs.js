/* ============================================================================
   MARKFLOW OFFICE — Editor visual Docs (ProseMirror, v1.1.0)
   Script clásico: consume `window.PM` (bundle oficial vendorizado en
   static/vendor/prosemirror/pm_bundle.js, cargado perezosamente por office.js).

   - Esquema Docs: doc/paragraph/heading/blockquote/bullet_list/ordered_list/
     list_item/code_block{params}/hard_break/horizontal_rule/image +
     marcas strong/em/s/code/link.
   - Serializador local `doc → Markdown`: ESPEJO de la referencia canónica en
     Python (app/servicios/editor_markdown.py · doc_a_md). Mantener ambos en
     paridad estricta (misma reglas, mismas envolturas, misma agrupación).
   - El SSOT del texto sigue siendo `#editor-markdown` (textarea): guardar,
     exportar, IA y preview siempre lo leen.
   Desde v1.2.0: tablas GFM nativas (table/table_row/table_header/table_cell)
   con comandos propios y serializador tablaAMd en paridad con Python.
   ============================================================================ */
"use strict";

(function () {

  /* ══════════════ Estado del módulo ══════════════ */
  let esquema = null;
  let vista = null;
  let plugins = [];
  let barra = null;
  let statsEl = null;
  let opciones = {};
  let preparado = false;

  const MFO = {
    listo: false,
    init,
    setTexto,
    getTexto,
    foco,
    /* Accesores de integración/pruebas (solo lectura): estado del editor. */
    estado: () => (vista ? vista.state : null),
    vista: () => vista,
  };
  window.MFOEditor = MFO;

  function ventana() { return window.PM; }

  async function pedirJSON(url, cuerpo) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((j && j.detalle) || "HTTP " + r.status);
    return j;
  }

  /* ══════════════ Esquema (paridad con el conversor Python) ══════════════ */
  function construirEsquema(PM) {
    const niveles = [1, 2, 3, 4, 5, 6];
    /* Atributos de celda (v1.2.0): colspan/rowspan/colwidth + alineación GFM */
    const attrsCelda = {
      colspan: { default: 1, validate: "number" },
      rowspan: { default: 1, validate: "number" },
      colwidth: { default: null },
      alignment: { default: "" },
    };
    const attrsCeldaDOM = (dom) => ({
      colspan: +dom.getAttribute("colspan") || 1,
      rowspan: +dom.getAttribute("rowspan") || 1,
      colwidth: dom.getAttribute("data-colwidth")
        ? dom.getAttribute("data-colwidth").split(",").map((w) => +w)
        : null,
      alignment: dom.getAttribute("data-align") || "",
    });
    const toDOMCelda = (etiqueta) => (n) => {
      const at = {};
      if (n.attrs.colspan !== 1) at.colspan = n.attrs.colspan;
      if (n.attrs.rowspan !== 1) at.rowspan = n.attrs.rowspan;
      if (n.attrs.alignment) at["data-align"] = n.attrs.alignment;
      return [etiqueta, at, 0];
    };
    esquema = new PM.model.Schema({
      nodes: {
        /* `group: "inline"` es obligatorio: `content: "inline*"` de párrafos y
           títulos casa con el grupo, no con el tipo. Sin él, cualquier
           transacción sobre párrafos con texto es inválida (doc.check()). */
        text: { group: "inline" },
        doc: { content: "block+" },
        paragraph: {
          group: "block", content: "inline*",
          parseDOM: [{ tag: "p" }], toDOM: () => ["p", 0],
        },
        heading: {
          group: "block", content: "inline*", defining: true,
          attrs: { level: { default: 1, validate: "number" } },
          parseDOM: niveles.map((l) => ({ tag: "h" + l, attrs: { level: l }, defining: true })),
          toDOM: (n) => ["h" + Math.max(1, Math.min(6, n.attrs.level)), 0],
        },
        blockquote: {
          content: "block+", group: "block", defining: true,
          parseDOM: [{ tag: "blockquote" }], toDOM: () => ["blockquote", 0],
        },
        bullet_list: {
          content: "list_item+", group: "block",
          parseDOM: [{ tag: "ul" }], toDOM: () => ["ul", 0],
        },
        ordered_list: {
          content: "list_item+", group: "block",
          attrs: { start: { default: 1, validate: "number" } },
          parseDOM: [{
            tag: "ol",
            getAttrs: (dom) => ({ start: dom.hasAttribute("start") ? +dom.getAttribute("start") : 1 }),
          }],
          toDOM: (n) => ["ol", { start: n.attrs.start }, 0],
        },
        list_item: {
          content: "paragraph block*",
          parseDOM: [{ tag: "li" }], toDOM: () => ["li", 0],
        },
        table: {
          content: "table_row+", tableRole: "table", isolating: true, group: "block",
          parseDOM: [{ tag: "table" }], toDOM: () => ["table", ["tbody", 0]],
        },
        table_row: {
          content: "(table_cell | table_header)*", tableRole: "row",
          parseDOM: [{ tag: "tr" }], toDOM: () => ["tr", 0],
        },
        table_cell: {
          content: "block+", tableRole: "cell",
          attrs: attrsCelda,
          parseDOM: [{ tag: "td", getAttrs: attrsCeldaDOM }],
          toDOM: toDOMCelda("td"),
        },
        table_header: {
          content: "block+", tableRole: "header_cell",
          attrs: attrsCelda,
          parseDOM: [{ tag: "th", getAttrs: attrsCeldaDOM }],
          toDOM: toDOMCelda("th"),
        },
        code_block: {
          content: "text*", code: true, defining: true, marks: "",
          attrs: { params: { default: null } },
          parseDOM: [{
            tag: "pre", preserveWhitespace: "full",
            getAttrs: (dom) => ({ params: dom.getAttribute("data-params") || null }),
          }],
          toDOM: (n) => ["pre", (n.attrs.params ? { "data-params": n.attrs.params } : {}), ["code", 0]],
        },
        hard_break: {
          inline: true, group: "inline", selectable: false,
          parseDOM: [{ tag: "br" }], toDOM: () => ["br"],
        },
        horizontal_rule: {
          group: "block",
          parseDOM: [{ tag: "hr" }], toDOM: () => ["hr"],
        },
        image: {
          inline: true, group: "inline", draggable: true,
          attrs: { src: { default: "" }, alt: { default: "" }, title: { default: null } },
          parseDOM: [{
            tag: "img[src]",
            getAttrs: (dom) => ({
              src: dom.getAttribute("src"),
              alt: dom.getAttribute("alt") || "",
              title: dom.getAttribute("title"),
            }),
          }],
          toDOM: (n) => ["img", { src: n.attrs.src, alt: n.attrs.alt, title: n.attrs.title }],
        },
      },
      marks: {
        strong: {
          parseDOM: [{ tag: "strong" }, { tag: "b" }],
          toDOM: () => ["strong", 0],
        },
        em: {
          parseDOM: [{ tag: "em" }, { tag: "i" }],
          toDOM: () => ["em", 0],
        },
        s: {
          parseDOM: [{ tag: "s" }, { tag: "strike" }],
          toDOM: () => ["s", 0],
        },
        code: { code: true, parseDOM: [{ tag: "code" }], toDOM: () => ["code", 0] },
        ins: {
          parseDOM: [{ tag: "ins" }],
          toDOM: () => ["ins", 0],
        },
        del: {
          parseDOM: [{ tag: "del" }],
          toDOM: () => ["del", 0],
        },
        link: {
          attrs: { href: { default: "" }, title: { default: null } },
          inclusive: false,
          parseDOM: [{
            tag: "a[href]",
            getAttrs: (dom) => ({
              href: dom.getAttribute("href"),
              title: dom.getAttribute("title"),
            }),
          }],
          toDOM: (n) => {
            const at = { href: n.attrs.href };
            if (n.attrs.title) at.title = n.attrs.title;
            return ["a", at, 0];
          },
        },
      },
    });
  }

  /* ══════════════ Plugins: reglas de entrada + atajos ══════════════ */
  const RE_CABECERA_MERMAID = /^(?:graph\s+(?:TD|TB|BT|RL|LR)|flowchart\s+(?:TD|TB|BT|RL|LR)|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram|gantt|pie|mindmap|timeline|gitGraph)\b/i;

  function reglasEntrada(PM) {
    const { InputRule, wrappingInputRule, textblockTypeInputRule } = PM.inputrules;
    const N = esquema.nodes;
    const M = esquema.marks;
    const reglas = [
      /* ``` o ```mermaid + espacio → bloque de código con params */
      textblockTypeInputRule(/^```([a-zA-Z0-9_-]+)?\s$/, N.code_block, (m) => ({ params: m[1] || null })),
      /* #…######+espacio → títulos */
      textblockTypeInputRule(/^(#{1,6})\s$/, N.heading, (m) => ({ level: m[1].length })),
      /* >+espacio → cita */
      wrappingInputRule(/^\s*>\s$/, N.blockquote),
      /* - * + → viñetas */
      wrappingInputRule(/^\s*([-*+])\s$/, N.bullet_list),
      /* 1. 2. → numerada (conserva el número inicial) */
      wrappingInputRule(/^\s*(\d+)\.\s$/, N.ordered_list, (m) => ({ start: +m[1] })),
      /* **texto** → negrita en vivo */
      new InputRule(/\*\*([^*\n]+)\*\*$/, (estado, match, start, end) => {
        if (estado.selection.$from.parent.type.spec.code) return null;
        const texto = match[1];
        if (!texto) return null;
        let tr = estado.tr.replaceWith(start, end, esquema.text(texto, [M.strong.create()]));
        tr = tr.removeStoredMark(M.strong);
        return tr;
      }),
      /* *texto* → cursiva en vivo */
      new InputRule(/(?:^|[^*])\*([^*\n]+)\*$/, (estado, match, start, end) => {
        if (estado.selection.$from.parent.type.spec.code) return null;
        const texto = match[1];
        if (!texto) return null;
        const offset = match[0].startsWith("*") ? 0 : 1;
        let tr = estado.tr.replaceWith(start + offset, end, esquema.text(texto, [M.em.create()]));
        tr = tr.removeStoredMark(M.em);
        return tr;
      }),
    ];
    return reglas;
  }

  function cmdCodigoAParrafo(estado, despachar) {
    const { $from, empty } = estado.selection;
    if (!empty) return false;
    if ($from.parent.type === esquema.nodes.code_block && $from.parent.content.size === 0) {
      if (despachar) despachar(estado.tr.setBlockType($from.pos, $from.pos, esquema.nodes.paragraph));
      return true;
    }
    return false;
  }

  function cmdEnlace() {
    const PM = ventana();
    const estado = vista.state;
    const marcasActuales = estado.storedMarks || estado.selection.$from.marks();
    const yaEnlace = marcasActuales.some((m) => m.type === esquema.marks.link);
    if (yaEnlace) {
      PM.commands.toggleMark(esquema.marks.link)(estado, (t) => vista.dispatch(t), vista);
      vista.focus();
      return;
    }
    const href = prompt("URL del enlace:", "https://");
    if (!href) return;
    let tr = estado.tr;
    if (estado.selection.empty) {
      const texto = href.replace(/^https?:\/\//, "").trim() || href;
      tr = tr.replaceSelectionWith(esquema.text(texto))
             .addMark(estado.selection.from, estado.selection.from + texto.length,
                      esquema.marks.link.create({ href }));
    } else {
      tr = tr.addMark(estado.selection.from, estado.selection.to,
                      esquema.marks.link.create({ href }));
    }
    vista.dispatch(tr);
    vista.focus();
  }

  function cmdImagen() {
    const src = prompt("URL de la imagen:", "");
    if (!src) return;
    const alt = prompt("Texto alternativo (alt):", "") || "";
    const titulo = prompt("Título (opcional):", "");
    const attrs = { src, alt };
    if (titulo) attrs.title = titulo;
    vista.dispatch(vista.state.tr.replaceSelectionWith(esquema.nodes.image.create(attrs)));
    vista.focus();
  }

  function cmdSeparador() {
    vista.dispatch(vista.state.tr
      .replaceSelectionWith(esquema.nodes.horizontal_rule.create())
      .scrollIntoView());
    vista.focus();
  }

  function cmdNota() {
    const PM = ventana();
    const C = PM.commands;
    const wrap = C.wrapIn(esquema.nodes.blockquote);
    const exito = wrap(vista.state, (t) => vista.dispatch(t), vista);
    if (!exito) {
      const tr = vista.state.tr.replaceSelectionWith(
        esquema.nodes.blockquote.create(null, [
          esquema.nodes.paragraph.create(null, [esquema.text("Nota: ")])
        ])
      ).scrollIntoView();
      vista.dispatch(tr);
    }
    vista.focus();
    return true;
  }

  /* ── Control de cambios (v1.5.0): marcar, aceptar y rechazar ──────────── */
  function cmdMarcarCambio(tipo) {
    const PM = ventana();
    const marca = esquema.marks[tipo];
    const estado = vista.state;
    if (estado.selection.empty) {
      if (tipo === "del") {
        alert("Selecciona el texto a borrar para marcarlo como cambio.");
        return;
      }
      const texto = prompt("Texto insertado (control de cambios):", "");
      if (!texto) return;
      vista.dispatch(estado.tr
        .replaceSelectionWith(esquema.text(texto))
        .addMark(estado.selection.from, estado.selection.from + texto.length, marca));
    } else {
      PM.commands.toggleMark(marca)(estado, (t) => vista.dispatch(t), vista);
    }
    vista.focus();
  }

  /* Acepta o rechaza las marcas ins/del. Con selección activa opera solo en
     ella; sin selección, en todo el documento. Aceptar una inserción (o
     rechazar un borrado) conserva el texto quitando la marca; el caso
     contrario elimina el texto. */
  function cmdResolverCambio(aceptar) {
    const estado = vista.state;
    const { from, to, empty } = estado.selection;
    const desde = empty ? 0 : from;
    const hasta = empty ? estado.doc.content.size : to;
    const acciones = [];
    estado.doc.nodesBetween(desde, hasta, (nodo, pos) => {
      if (!nodo.isText) return;
      const marca = nodo.marks.find(
        (m) => m.type === esquema.marks.ins || m.type === esquema.marks.del);
      if (marca) acciones.push({ desde: pos, hasta: pos + nodo.nodeSize, tipo: marca.type.name });
    });
    if (!acciones.length) {
      alert(aceptar
        ? "No hay cambios marcados que aceptar."
        : "No hay cambios marcados que rechazar.");
      return;
    }
    const tr = estado.tr;
    /* De atrás hacia adelante: las posiciones de las acciones previas no se mueven */
    for (const a of acciones.reverse()) {
      const esInsercion = a.tipo === "ins";
      if ((esInsercion && aceptar) || (!esInsercion && !aceptar)) {
        tr.removeMark(a.desde, a.hasta, esquema.marks[a.tipo]);
      } else {
        tr.delete(a.desde, a.hasta);
      }
    }
    vista.dispatch(tr);
    vista.focus();
  }

  /* ══════════════ Tablas (v1.2.0) — comandos propios (sin @prosemirror/tables) ══ */
  function tablaDe(estado) {
    const $f = estado.selection.$from;
    for (let d = $f.depth; d > 0; d--) {
      if ($f.node(d).type.name === "table") {
        return {
          pos: $f.before(d),
          nodo: $f.node(d),
          profundidad: d,
          filaIdx: $f.index(d),
          celdaIdx: $f.index(d + 1),
        };
      }
    }
    return null;
  }

  function tipoCeldaDe(fila) {
    return fila.firstChild && fila.firstChild.type.name === "table_header"
      ? esquema.nodes.table_header
      : esquema.nodes.table_cell;
  }

  function insertarTabla(estado, despachar) {
    const PM = ventana();
    const respuesta = prompt("Tamaño de la tabla (filas x columnas):", "3x3");
    if (!respuesta) return true;
    const m = String(respuesta).match(/(\d+)\s*[x×*]\s*(\d+)/i);
    const filas = Math.max(1, Math.min(12, m ? +m[1] : 3));
    const columnas = Math.max(1, Math.min(8, m ? +m[2] : 3));
    const filaDe = (cabecera) => esquema.nodes.table_row.create({}, Array.from(
      { length: columnas },
      () => (cabecera ? esquema.nodes.table_header : esquema.nodes.table_cell)
        .create({}, esquema.nodes.paragraph.create())
    ));
    const tabla = esquema.nodes.table.create({},
      [filaDe(true)].concat(Array.from({ length: filas - 1 }, () => filaDe(false))));
    let tr = estado.tr.replaceSelectionWith(tabla);
    /* Cursor dentro de la primera celda: tabla+1 fila · +2 celda · +3 párrafo · +4 texto */
    const $t = tr.doc.resolve(tr.selection.from);
    for (let d = $t.depth; d > 0; d--) {
      if ($t.node(d).type.name === "table") {
        tr = tr.setSelection(
          PM.state.TextSelection.near(tr.doc.resolve($t.before(d) + 4))
        );
        break;
      }
    }
    despachar(tr.scrollIntoView());
    vista.focus();
    return true;
  }

  function filaNuevaDe(filaRef) {
    const celdas = [];
    filaRef.forEach((celda) => {
      const tipo = celda.type.name === "table_header"
        ? esquema.nodes.table_header : esquema.nodes.table_cell;
      celdas.push(tipo.create(celda.attrs, esquema.nodes.paragraph.create()));
    });
    return esquema.nodes.table_row.create({}, celdas);
  }

  function insertarFila(estado, despachar) {
    const PM = ventana();
    const ctx = tablaDe(estado);
    if (!ctx) return false;
    const nueva = filaNuevaDe(ctx.nodo.child(ctx.filaIdx));
    const despues = estado.selection.$from.after(ctx.profundidad + 1);
    let tr = estado.tr.insert(despues, nueva);
    tr = tr.setSelection(PM.state.TextSelection.near(tr.doc.resolve(despues + 3)));
    despachar(tr.scrollIntoView());
    return true;
  }

  function convertirPrimeraFilaACabecera(tr, posTabla) {
    const tabla = tr.doc.nodeAt(posTabla);
    if (!tabla || !tabla.childCount) return tr;
    const primera = tabla.child(0);
    if (!primera.childCount || primera.firstChild.type.name === "table_header") return tr;
    let pos = posTabla + 2; /* primera celda: fila abierta +1 */
    primera.forEach((celda) => {
      const tam = celda.nodeSize;
      if (celda.type.name !== "table_header") {
        tr = tr.replaceWith(pos, pos + tam,
          esquema.nodes.table_header.create(celda.attrs, celda.content));
      }
      pos += tam; /* mismo tamaño: las posiciones siguientes no cambian */
    });
    return tr;
  }

  function eliminarFila(estado, despachar) {
    const ctx = tablaDe(estado);
    if (!ctx) return false;
    const $f = estado.selection.$from;
    let tr = estado.tr.delete($f.before(ctx.profundidad + 1), $f.after(ctx.profundidad + 1));
    const restante = tr.doc.nodeAt(ctx.pos);
    if (!restante || !restante.childCount) {
      tr = tr.delete(ctx.pos, ctx.pos + (restante ? restante.nodeSize : 0));
    } else if (ctx.filaIdx === 0) {
      tr = convertirPrimeraFilaACabecera(tr, ctx.pos); /* GFM: primera fila = cabecera */
    }
    despachar(tr.scrollIntoView());
    return true;
  }

  function insertarColumna(estado, despachar, derecha) {
    const ctx = tablaDe(estado);
    if (!ctx) return false;
    let tr = estado.tr;
    const filasPos = [];
    let p = ctx.pos + 1;
    ctx.nodo.forEach((fila) => { filasPos.push(p); p += fila.nodeSize; });
    /* De la última fila a la primera: las posiciones previas no se alteran */
    for (let f = filasPos.length - 1; f >= 0; f--) {
      const fila = ctx.nodo.child(f);
      const inicio = filasPos[f] + 1;
      const nueva = tipoCeldaDe(fila).create({}, esquema.nodes.paragraph.create());
      let pos = inicio;
      const limite = derecha ? Math.min(ctx.celdaIdx + 1, fila.childCount) : ctx.celdaIdx;
      for (let c = 0; c < limite; c++) pos += fila.child(c).nodeSize;
      tr = tr.insert(pos, nueva);
    }
    despachar(tr.scrollIntoView());
    return true;
  }

  function eliminarColumna(estado, despachar) {
    const ctx = tablaDe(estado);
    if (!ctx) return false;
    let minimo = Infinity;
    ctx.nodo.forEach((fila) => { minimo = Math.min(minimo, fila.childCount); });
    if (minimo <= 1) return eliminarTabla(estado, despachar);
    let tr = estado.tr;
    const filasPos = [];
    let p = ctx.pos + 1;
    ctx.nodo.forEach((fila) => { filasPos.push(p); p += fila.nodeSize; });
    for (let f = filasPos.length - 1; f >= 0; f--) {
      const fila = ctx.nodo.child(f);
      const inicio = filasPos[f] + 1;
      const c = Math.min(ctx.celdaIdx, fila.childCount - 1);
      let desde = inicio;
      for (let k = 0; k < c; k++) desde += fila.child(k).nodeSize;
      tr = tr.delete(desde, desde + fila.child(c).nodeSize);
    }
    despachar(tr.scrollIntoView());
    return true;
  }

  function eliminarTabla(estado, despachar) {
    const ctx = tablaDe(estado);
    if (!ctx) return false;
    despachar(estado.tr.delete(ctx.pos, ctx.pos + ctx.nodo.nodeSize));
    return true;
  }

  function celdaSiguiente(estado, despachar, adelante) {
    const PM = ventana();
    const ctx = tablaDe(estado);
    if (!ctx) return false;
    let f = ctx.filaIdx;
    let c = ctx.celdaIdx;
    let tr = estado.tr;
    if (adelante) {
      if (f >= ctx.nodo.childCount) return false;
      c += 1;
      if (c >= ctx.nodo.child(f).childCount) {
        f += 1;
        c = 0;
        if (f >= ctx.nodo.childCount) {
          /* Última celda de la tabla: Tab crea una fila nueva al final */
          tr = tr.insert(ctx.pos + ctx.nodo.nodeSize - 1,
                         filaNuevaDe(ctx.nodo.child(ctx.nodo.childCount - 1)));
        }
      }
    } else {
      c -= 1;
      if (c < 0) {
        f -= 1;
        if (f < 0) return false;
        c = ctx.nodo.child(f).childCount - 1;
      }
    }
    /* Posición de la celda destino (f, c) sobre el doc vigente del tr */
    const tabla = tr.doc.nodeAt(ctx.pos);
    if (!tabla || f >= tabla.childCount) return false;
    let pos = ctx.pos + 1;
    for (let r = 0; r < f; r++) pos += tabla.child(r).nodeSize;
    pos += 1;
    const fila = tabla.child(f);
    for (let cc = 0; cc < c; cc++) pos += fila.child(cc).nodeSize;
    pos += 2; /* celda abierta + párrafo abierto → posición de texto */
    tr = tr.setSelection(PM.state.TextSelection.near(tr.doc.resolve(Math.min(pos, tr.doc.content.size))));
    despachar(tr.scrollIntoView());
    return true;
  }

  function teclas(PM) {
    const C = PM.commands, L = PM.schema_list, H = PM.history;
    const N = esquema.nodes;
    const bt = (cmd) => (estado, despachar, v) => cmd(estado, despachar, v);
    return {
      "Mod-b": bt(C.toggleMark(esquema.marks.strong)),
      "Mod-i": bt(C.toggleMark(esquema.marks.em)),
      "Mod-`": bt(C.toggleMark(esquema.marks.code)),
      "Mod-k": () => { cmdEnlace(); return true; },
      "Shift-Enter": (estado, despachar) => {
        if (estado.selection.$from.parent.type.spec.code) return false;
        despachar(estado.tr.replaceSelectionWith(esquema.nodes.hard_break.create()).scrollIntoView());
        return true;
      },
      "Tab": (estado, despachar) => celdaSiguiente(estado, despachar, true),
      "Shift-Tab": (estado, despachar) => celdaSiguiente(estado, despachar, false),
      "Shift-Ctrl-0": bt(C.setBlockType(N.paragraph)),
      "Shift-Ctrl-1": bt(C.setBlockType(N.heading, { level: 1 })),
      "Shift-Ctrl-2": bt(C.setBlockType(N.heading, { level: 2 })),
      "Shift-Ctrl-3": bt(C.setBlockType(N.heading, { level: 3 })),
      "Shift-Ctrl-8": bt(L.wrapInList(N.bullet_list)),
      "Shift-Ctrl-9": bt(L.wrapInList(N.ordered_list)),
      "Shift-Ctrl-\\": bt(C.setBlockType(N.code_block)),
      "Ctrl->": bt(C.wrapIn(N.blockquote)),
      "Mod-[": bt(L.liftListItem(N.list_item)),
      "Mod-]": bt(L.sinkListItem(N.list_item)),
      "Backspace": PM.commands.chainCommands(cmdCodigoAParrafo),
      "Enter": L.splitListItem(N.list_item),
      "Mod-z": bt(H.undo),
      "Shift-Mod-z": bt(H.redo),
      "Mod-y": bt(H.redo),
    };
  }

  function pluginPlaceholder(PM, texto) {
    return new PM.state.Plugin({
      props: {
        decorations(estado) {
          const doc = estado.doc;
          const vacio = doc.childCount === 0 ||
            (doc.childCount === 1 && doc.firstChild.isTextblock &&
             doc.firstChild.content.size === 0);
          if (!vacio || !estado.selection.empty) return null;
          const span = document.createElement("span");
          span.className = "pm-placeholder";
          span.textContent = texto;
          return PM.view.DecorationSet.create(doc, [PM.view.Decoration.widget(0, span)]);
        },
      },
    });
  }

  /* ══════════════ Toolbar + estadísticas ══════════════ */
  function comando(nombre) {
    const PM = ventana();
    const C = PM.commands, L = PM.schema_list, H = PM.history;
    const run = (cmd) => cmd(vista.state, (t) => vista.dispatch(t), vista);
    switch (nombre) {
      case "strong": return run(C.toggleMark(esquema.marks.strong));
      case "em": return run(C.toggleMark(esquema.marks.em));
      case "s": return run(C.toggleMark(esquema.marks.s));
      case "code": return run(C.toggleMark(esquema.marks.code));
      case "p": return run(C.setBlockType(esquema.nodes.paragraph));
      case "h1": return run(C.setBlockType(esquema.nodes.heading, { level: 1 }));
      case "h2": return run(C.setBlockType(esquema.nodes.heading, { level: 2 }));
      case "h3": return run(C.setBlockType(esquema.nodes.heading, { level: 3 }));
      case "bullet": return run(L.wrapInList(esquema.nodes.bullet_list));
      case "ordered": return run(L.wrapInList(esquema.nodes.ordered_list));
      case "quote": return run(C.wrapIn(esquema.nodes.blockquote));
      case "nota": return cmdNota();
      case "codeblock": return run(C.setBlockType(esquema.nodes.code_block));
      case "link": return cmdEnlace();
      case "image": return cmdImagen();
      case "hr": return cmdSeparador();
      case "cc-ins": return cmdMarcarCambio("ins");
      case "cc-del": return cmdMarcarCambio("del");
      case "cc-aceptar": return cmdResolverCambio(true);
      case "cc-rechazar": return cmdResolverCambio(false);
      case "tabla": return insertarTabla(vista.state, (t) => vista.dispatch(t));
      case "fila+": return insertarFila(vista.state, (t) => vista.dispatch(t));
      case "fila-": return eliminarFila(vista.state, (t) => vista.dispatch(t));
      case "col+": return insertarColumna(vista.state, (t) => vista.dispatch(t), true);
      case "col-": return insertarColumna(vista.state, (t) => vista.dispatch(t), false);
      case "tabla-del": return eliminarTabla(vista.state, (t) => vista.dispatch(t));
      case "undo": return run(H.undo);
      case "redo": return run(H.redo);
      default: return false;
    }
  }

  function conectarBarra() {
    barra = document.getElementById("barra-docs");
    statsEl = document.getElementById("docs-stats");
    if (!barra) return;
    /* Evita que el clic quite el foco/la selección del editor */
    barra.addEventListener("mousedown", (e) => {
      if (e.target.closest(".bd-btn")) e.preventDefault();
    });
    barra.addEventListener("click", (e) => {
      const btn = e.target.closest(".bd-btn");
      if (!btn) return;
      e.preventDefault();
      comando(btn.dataset.bd);
      if (vista) vista.focus();
    });
  }

  function refrescar() {
    if (!vista || !barra) return;
    const estado = vista.state;
    const $desde = estado.selection.$from;
    const marcas = estado.storedMarks || $desde.marks();
    const setClase = (nombre, activo) => {
      const btn = barra.querySelector(`[data-bd="${nombre}"]`);
      if (btn) btn.classList.toggle("activo", Boolean(activo));
    };
    const tiene = (n) => marcas.some((m) => m.type.name === n);
    setClase("strong", tiene("strong"));
    setClase("em", tiene("em"));
    setClase("s", tiene("s"));
    setClase("code", tiene("code"));
    setClase("cc-ins", tiene("ins"));
    setClase("cc-del", tiene("del"));
    const padre = $desde.parent;
    const nivel = padre.type.name === "heading" ? padre.attrs.level : 0;
    setClase("p", padre.type.name === "paragraph");
    setClase("h1", nivel === 1);
    setClase("h2", nivel === 2);
    setClase("h3", nivel === 3);
    setClase("codeblock", padre.type.name === "code_block");
    let lista = null;
    for (let d = $desde.depth; d >= 0; d--) {
      const n = $desde.node(d);
      if (n.type.name === "bullet_list" || n.type.name === "ordered_list") { lista = n.type.name; break; }
    }
    setClase("bullet", lista === "bullet_list");
    setClase("ordered", lista === "ordered_list");
    if (statsEl) {
      const texto = estado.doc.textBetween(0, estado.doc.content.size, " ", " ");
      const palabras = (texto.match(/\S+/g) || []).length;
      statsEl.textContent = `${palabras} ${palabras === 1 ? "palabra" : "palabras"} · ${texto.length} caracteres`;
    }
  }

  /* ══════════════ Ciclo de vida ══════════════ */
  function docVacio() {
    return { type: "doc", content: [{ type: "paragraph" }] };
  }

  function despacharTransaccion(tr) {
    const nuevo = vista.state.apply(tr);
    vista.updateState(nuevo);
    if (tr.docChanged) {
      sincronizarFuente(nuevo.doc);
      refrescar();
      if (opciones.alCambiar) opciones.alCambiar(getTexto());
    } else {
      refrescar();
    }
  }

  function sincronizarFuente(docActual) {
    const ta = document.getElementById("editor-markdown");
    if (!ta || !docActual) return;
    const md = docAMd(docActual.toJSON());
    if (ta.value !== md) ta.value = md;
  }

  function init(contenedor, opc) {
    const PM = ventana();
    if (!PM) throw new Error("El bundle de ProseMirror (window.PM) no está cargado.");
    opciones = opc || {};
    /* El EditorView se añade al contenedor: limpia el mensaje de carga */
    contenedor.innerHTML = "";
    construirEsquema(PM);
    plugins = [
      PM.inputrules.inputRules({ rules: reglasEntrada(PM) }),
      PM.keymap.keymap(teclas(PM)),
      PM.keymap.keymap(PM.commands.baseKeymap),
      PM.history.history(),
      PM.dropcursor.dropCursor(),
      PM.gapcursor.gapCursor(),
      pluginPlaceholder(PM, "# Escribe tu Markdown aquí…  ·  Pega de Word o ChatGPT y pulsa 🧹 Sanear"),
    ];
    conectarBarra();
    vista = new PM.view.EditorView(contenedor, {
      state: PM.state.EditorState.create({ doc: PM.model.Node.fromJSON(esquema, docVacio()), plugins }),
      attributes: { spellcheck: "false" },
      dispatchTransaction: despacharTransaccion,
      handlePaste(view, event) {
        const textoPlano = event.clipboardData ? event.clipboardData.getData("text/plain") : "";
        if (!textoPlano || !textoPlano.trim()) return false;
        const $from = view.state.selection.$from;
        /* Si pega dentro de un code_block y el texto es Mermaid, asegurar params="mermaid" */
        if ($from.parent.type.spec.code) {
          let limpio = textoPlano.replace(/\r\n?/g, "\n");
          const cercoMatch = limpio.trim().match(/^`{3,}\s*([a-zA-Z0-9_-]+)?[^\n]*\n([\s\S]*?)\n?`{3,}\s*$/);
          let lang = $from.parent.attrs.params;
          if (cercoMatch) {
            lang = cercoMatch[1] || lang || null;
            limpio = cercoMatch[2];
          } else if (!lang && RE_CABECERA_MERMAID.test(limpio.trim())) {
            lang = "mermaid";
          }
          let tr = view.state.tr.insertText(limpio);
          if (lang && lang !== $from.parent.attrs.params) {
            const posBloque = $from.before($from.depth);
            tr = tr.setNodeMarkup(posBloque, null, { params: lang });
          }
          view.dispatch(tr.scrollIntoView());
          return true;
        }
        /* Si pega fuera de code_block un diagrama Mermaid crudo o bloque Markdown estructurado */
        const recortado = textoPlano.replace(/\r\n?/g, "\n").trim();
        if (RE_CABECERA_MERMAID.test(recortado)) {
          const nodoMermaid = esquema.nodes.code_block.create(
            { params: "mermaid" },
            esquema.text(recortado)
          );
          view.dispatch(view.state.tr.replaceSelectionWith(nodoMermaid).scrollIntoView());
          return true;
        }
        const tieneMarkdownEstructurado = /(?:^|\n)[ \t]*`{3,}|(?:^|\n)[ \t]*#{1,6}\s|\*\*[^*\n]+\*\*|(?:^|\n)[ \t]*\|.+\|[ \t]*\n[ \t]*\|[\s:|-]+\|/.test(recortado);
        if (tieneMarkdownEstructurado) {
          pedirJSON("/api/office/md-a-json", { texto: recortado })
            .then((cuerpo) => {
              if (!cuerpo || !cuerpo.datos || !cuerpo.datos.doc) return;
              const docPegado = PM.model.Node.fromJSON(esquema, cuerpo.datos.doc);
              const slice = new PM.model.Slice(docPegado.content, 0, 0);
              view.dispatch(view.state.tr.replaceSelection(slice).scrollIntoView());
            })
            .catch(() => {});
          return true;
        }
        return false;
      },
    });
    preparado = true;
    refrescar();
    return setTexto(opciones.texto || "");
  }

  async function setTexto(md) {
    const PM = ventana();
    if (!PM || !preparado) throw new Error("El editor aún no está inicializado.");
    const cuerpo = await pedirJSON("/api/office/md-a-json", { texto: md || "" });
    const doc = PM.model.Node.fromJSON(esquema, cuerpo.datos.doc);
    vista.updateState(PM.state.EditorState.create({ doc, plugins }));
    /* Muestra en el textarea la versión normalizada (idempotente) */
    sincronizarFuente(vista.state.doc);
    refrescar();
    if (opciones.alCambiar) opciones.alCambiar(getTexto());
  }

  function getTexto() {
    const ta = document.getElementById("editor-markdown");
    return ta ? ta.value : "";
  }

  function foco() {
    if (vista) vista.focus();
  }

  /* ════════════════════════════════════════════════════════════════════════
     ESPEJO JS del serializador `doc → Markdown`
     Referencia canónica: app/servicios/editor_markdown.py · doc_a_md
     ════════════════════════════════════════════════════════════════════════ */
  const ORDEN_MARCAS = ["ins", "del", "strong", "em", "s"];
  const ENVOLTURA = {
    strong: ["**", "**"], em: ["*", "*"], s: ["~~", "~~"],
    ins: ["{++", "++}"], del: ["{--", "--}"],
  };

  function entero(valor, defecto) {
    const n = parseInt(valor, 10);
    return isNaN(n) ? defecto : n;
  }

  function limpiarReferenciasImagenesHuerfanas(texto) {
    if (!texto) return texto;
    const patronRef = /!\[.*?\]\[([^\]]+)\]/g;
    const activas = new Set();
    let m;
    while ((m = patronRef.exec(texto)) !== null) {
      activas.add(m[1].trim());
    }
    const lineas = texto.split(/\r?\n/);
    const patronDef = /^\s*\[([^\]]+)\]:\s*(data:image\/[^\s]+|\S+)/;
    const filtradas = [];
    for (const linea of lineas) {
      const match = patronDef.exec(linea);
      if (match) {
        const etiqueta = match[1].trim();
        if (match[2].startsWith("data:image/") || etiqueta.startsWith("img-")) {
          if (!activas.has(etiqueta)) {
            continue;
          }
        }
      }
      filtradas.push(linea);
    }
    return filtradas.join("\n");
  }

  function docAMd(doc) {
    const contenido = (doc && doc.content) || [];
    const lineas = [];
    const imagenesBase64 = [];
    for (const nodo of contenido) {
      if (lineas.length) lineas.push("");
      lineas.push(...bloqueAMd(nodo, 0, imagenesBase64));
    }
    if (imagenesBase64.length) {
      lineas.push("");
      for (const [tag, src] of imagenesBase64) {
        lineas.push(`[${tag}]: ${src}`);
      }
    }
    if (!lineas.length) return "";
    const salida = lineas.join("\n").replace(/^\n+|\n+$/g, "") + "\n";
    return limpiarReferenciasImagenesHuerfanas(salida);
  }

  function bloqueAMd(nodo, nivelLista, imagenesBase64) {
    const tipo = nodo.type || "";
    const contenido = nodo.content || [];
    if (tipo === "paragraph") {
      const texto = inlineAMd(contenido, imagenesBase64);
      return texto ? [texto] : [];
    }
    if (tipo === "heading") {
      const nivel = entero((nodo.attrs || {}).level, 1);
      const hashes = "#".repeat(Math.max(1, Math.min(6, nivel)));
      return [`${hashes} ${inlineAMd(contenido, imagenesBase64)}`.trimEnd()];
    }
    if (tipo === "code_block") {
      let params = (nodo.attrs || {}).params || "";
      let cuerpo = contenido.map((h) => h.text || "").join("");
      const cercoInterno = cuerpo.trim().match(/^`{3,}\s*([a-zA-Z0-9_-]+)?[^\n]*\n([\s\S]*?)\n?`{3,}\s*$/);
      if (cercoInterno) {
        if (!params && cercoInterno[1]) params = cercoInterno[1];
        cuerpo = cercoInterno[2];
      }
      if (!params && RE_CABECERA_MERMAID.test(cuerpo.trim())) {
        params = "mermaid";
      }
      const lineas = cuerpo ? cuerpo.split("\n") : [""];
      return ["```" + params].concat(lineas, ["```"]);
    }
    if (tipo === "horizontal_rule") return ["---"];
    if (tipo === "blockquote") {
      const internas = [];
      for (const hijo of contenido) {
        if (internas.length) internas.push("");
        internas.push(...bloqueAMd(hijo, nivelLista, imagenesBase64));
      }
      return (internas.length ? internas : [""]).map((l) => (l ? "> " + l : ">"));
    }
    if (tipo === "bullet_list" || tipo === "ordered_list") return listaAMd(nodo, nivelLista, imagenesBase64);
    if (tipo === "table") return tablaAMd(nodo, imagenesBase64);
    const sueltos = [];
    for (const hijo of contenido) sueltos.push(...bloqueAMd(hijo, nivelLista, imagenesBase64));
    return sueltos;
  }

  function listaAMd(nodo, nivelLista, imagenesBase64) {
    const lineas = [];
    const numerada = nodo.type === "ordered_list";
    let contador = entero((nodo.attrs || {}).start, 1);
    const sangria = "  ".repeat(nivelLista);
    for (const item of nodo.content || []) {
      const marca = numerada ? `${contador}. ` : "- ";
      if (numerada) contador += 1;
      let primera = true;
      for (const hijo of item.content || []) {
        if (hijo.type === "bullet_list" || hijo.type === "ordered_list") {
          lineas.push(...listaAMd(hijo, nivelLista + 1, imagenesBase64));
          continue;
        }
        const lineasHijo = bloqueAMd(hijo, nivelLista + 1, imagenesBase64);
        lineasHijo.forEach((linea, k) => {
          if (primera) {
            lineas.push(`${sangria}${marca}${linea}`.trimEnd());
            primera = false;
          } else {
            lineas.push(linea ? "  ".repeat(nivelLista + 1) + linea : "");
          }
        });
      }
      if (primera) lineas.push(`${sangria}${marca}`.trimEnd());
    }
    return lineas;
  }

  /* ══════════════ Tablas → Markdown (espejo de _tabla_a_md en Python) ══════ */
  const SEPARADOR_ALINEACION = { "": "---", left: ":---", center: ":---:", right: "---:" };

  function celdaATexto(celda, imagenesBase64) {
    /* Aplana el contenido de una celda a una línea (GFM) escapando pipes */
    const partes = [];
    for (const hijo of celda.content || []) {
      if (hijo.type === "paragraph") {
        partes.push(inlineAMd(hijo.content || [], imagenesBase64));
      } else {
        partes.push(...bloqueAMd(hijo, 0, imagenesBase64));
      }
    }
    let plano = partes.map((p) => p.trim()).filter(Boolean).join(" ");
    /* El salto de línea rompería la fila GFM: hardbreaks y \n se aplanan a espacios */
    plano = plano.replace("\\\n", " ").replace(/\n/g, " ");
    return plano.replace(/\|/g, "\\|");
  }

  function tablaAMd(nodo, imagenesBase64) {
    const filas = nodo.content || [];
    if (!filas.length) return ["| |", "|---|"];
    const columnas = Math.max(1, filas.reduce(
      (n, f) => Math.max(n, (f.content || []).length), 0));

    const textosDe = (fila) => {
      const celdas = (fila.content || []).map((c) => celdaATexto(c, imagenesBase64) || " ");
      while (celdas.length < columnas) celdas.push(" ");
      return celdas;
    };
    const alineacionesDe = (fila) => {
      const al = (fila.content || []).map((c) => ((c.attrs || {}).alignment || ""));
      while (al.length < columnas) al.push("");
      return al;
    };

    const lineas = ["| " + textosDe(filas[0]).join(" | ") + " |"];
    const separadores = alineacionesDe(filas[0]).map((a) => SEPARADOR_ALINEACION[a] || "---");
    lineas.push("|" + separadores.join("|") + "|");
    for (const fila of filas.slice(1)) {
      lineas.push("| " + textosDe(fila).join(" | ") + " |");
    }
    return lineas;
  }

  function inlineAMd(nodos, imagenesBase64) {
    const segmentos = [];
    for (const nodo of nodos || []) {
      const marcas = (nodo.marks || []).filter((m) => m && m.type);
      if (nodo.type === "text") {
        segmentos.push({ texto: nodo.text || "", marcas });
      } else if (nodo.type === "hard_break") {
        segmentos.push({ texto: "\\\n", marcas });
      } else if (nodo.type === "image") {
        const a = nodo.attrs || {};
        const alt = String(a.alt || "").replace(/\n/g, " ");
        const src = a.src || "";
        const sufijo = a.title ? ` "${a.title}"` : "";
        if (src.startsWith("data:image/") && imagenesBase64) {
          const tag = `img-${imagenesBase64.length + 1}`;
          imagenesBase64.push([tag, src]);
          segmentos.push({ texto: `![${alt}][${tag}]`, marcas: [] });
        } else {
          segmentos.push({ texto: `![${alt}](${src}${sufijo})`, marcas: [] });
        }
      }
    }
    if (!segmentos.length) return "";
    const salida = [];
    let i = 0;
    while (i < segmentos.length) {
      const firma = JSON.stringify(segmentos[i].marcas.map((m) => m.type));
      let j = i;
      const partes = [];
      while (j < segmentos.length &&
             JSON.stringify(segmentos[j].marcas.map((m) => m.type)) === firma) {
        partes.push(segmentos[j].texto);
        j += 1;
      }
      salida.push(envolver(partes.join(""), segmentos[i].marcas));
      i = j;
    }
    return salida.join("");
  }

  function envolver(texto, marcas) {
    if (!texto || !marcas.length) return texto;
    const tipos = marcas.map((m) => m.type);
    if (tipos.includes("code")) return envolverCode(texto);
    let prefijo = "";
    let sufijo = "";
    for (const nombre of ORDEN_MARCAS) {
      if (tipos.includes(nombre)) {
        prefijo += ENVOLTURA[nombre][0];
        sufijo = ENVOLTURA[nombre][1] + sufijo;
      }
    }
    let envuelto = prefijo + texto + sufijo;
    const enlace = marcas.find((m) => m.type === "link");
    if (enlace) {
      const a = enlace.attrs || {};
      const destino = a.title ? `${a.href || ""} "${a.title}"` : (a.href || "");
      envuelto = `[${envuelto}](${destino})`;
    }
    return envuelto;
  }

  function envolverCode(texto) {
    let comillas = "`";
    while (texto.includes(comillas)) comillas += "`";
    const relleno = (texto.startsWith("`") || texto.endsWith("`")) ? " " : "";
    return `${comillas}${relleno}${texto}${relleno}${comillas}`;
  }

})();
