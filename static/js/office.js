/* ============================================================================
   MARKFLOW OFFICE — Lógica de la shell (vanilla, sin dependencias)
   Riel de apps · Documentos (CRUD + FTS) · Docs (editor + vista en vivo)
   Word (export núcleo GenOffice) · Configuración IA · Panel «Preguntar IA»
   ============================================================================ */
"use strict";

const $ = (sel) => document.querySelector(sel);
const API = {
  documentos: "/api/documentos",
  office: "/api/office",
  preview: "/api/render-preview",
  mdAJson: "/api/office/md-a-json",
  jsonAMd: "/api/office/json-a-md",
  sanear: "/api/office/sanear",
};

const estado = {
  documento: null,        // nombre del documento abierto (con .md)
  sucio: false,
  panelIA: false,
};

/* ─────────────────────────── Utilidades ─────────────────────────── */
async function jsonFetch(url, opciones = {}) {
  const respuesta = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  const cuerpo = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    const detalle = cuerpo?.detalle || cuerpo?.detail || cuerpo?.message || respuesta.statusText;
    throw new Error(typeof detalle === "string" ? detalle : JSON.stringify(detalle));
  }
  return cuerpo;
}

function tamanoLegible(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

window.escapeHtml = function (texto) {
  if (texto === null || texto === undefined) return "";
  return String(texto)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
};
const escapeHtml = window.escapeHtml;

function validarNombreDocumento(nombre) {
  if (!nombre || !nombre.trim()) {
    return "El nombre del documento no puede estar vacío.";
  }
  const base = nombre.trim().replace(/\.md$/i, "");
  if (!base) {
    return "El nombre del documento no puede estar vacío.";
  }
  if (!/^[\p{L}\p{N}_][\p{L}\p{N}_\s\-.]{0,90}$/u.test(base)) {
    return "Nombre de documento inválido. Debe comenzar con letra o número, y solo puede contener letras, números, espacios, guiones y puntos (máximo 90 caracteres).";
  }
  return null;
}

function sanearCodigoMermaid(codigo) {
  // Saneador Mermaid v1.20.3 — análisis por estado, simétrico con motor/a_mermaid.py
  if (!codigo || typeof codigo !== "string") return "";
  let c = codigo;

  // 1. Superíndices Unicode → ASCII
  const superindices = {
    "\u00b2": "2", "\u00b3": "3", "\u2070": "0", "\u00b9": "1",
    "\u2074": "4", "\u2075": "5", "\u2076": "6", "\u2077": "7", "\u2078": "8", "\u2079": "9"
  };
  for (const [k, v] of Object.entries(superindices)) {
    c = c.split(k).join(v);
  }

  // 2. Espacios antes de ::: (STYLE_SEPARATOR)
  c = c.replace(/(\]|\)|\}|>|\w)\s+:::/g, "$1:::").replace(/\s+:::/g, ":::");

  // 3. Operadores de comparación
  c = c.replace(/<=/g, "\u2264").replace(/>=/g, "\u2265");

  // 4. Protección de nodos [texto] con analizador por estado (respeta ["ya entrecomillados"])
  const DIRECTIVAS = /^\s*(classDef|style|click|linkStyle|subgraph|end)\b/i;

  function sanitizarInteriorNodo(texto) {
    // Flechas Unicode → ASCII (no son conectores Mermaid dentro de un nodo)
    let t = texto
      .replace(/\u2192/g, "->")
      .replace(/\u2190/g, "<-")
      .replace(/\u2194/g, "<->");
    // Corchetes anidados [unidad] → (unidad)
    t = t.replace(/\[([^\[\]]*?)\]/g, "($1)");
    // Ángulos sueltos
    t = t.replace(/<(?![=-])/g, "&lt;").replace(/(?<![=-])>/g, "&gt;");
    // Comillas dobles → simples
    t = t.replace(/"/g, "'");
    return t;
  }

  function procesarLinea(linea) {
    const resultado = [];
    let i = 0;
    const n = linea.length;
    while (i < n) {
      const ch = linea[i];
      if (ch !== "[") { resultado.push(ch); i++; continue; }

      const j = i + 1;
      // Caso 1: nodo ya entre comillas ["..."] — conservar intacto
      if (j < n && linea[j] === '"') {
        const k = linea.indexOf('"]', j + 1);
        if (k !== -1) {
          resultado.push(linea.slice(i, k + 2));
          i = k + 2;
          continue;
        }
        resultado.push(ch); i++; continue;
      }

      // Caso 2: nodo sin comillas [texto...] — manejar anidamiento con contador de nivel
      let nivel = 1;
      let k = j;
      while (k < n && nivel > 0) {
        if (linea[k] === "[") nivel++;
        else if (linea[k] === "]") nivel--;
        k++;
      }
      if (nivel === 0) {
        const interior = linea.slice(j, k - 1);
        const interiorSano = sanitizarInteriorNodo(interior);
        resultado.push(`["${interiorSano}"]`);
        i = k;
        continue;
      }
      resultado.push(ch); i++;
    }
    return resultado.join("");
  }

  return c.split("\n").map(linea =>
    DIRECTIVAS.test(linea) ? linea : procesarLinea(linea)
  ).join("\n");
}
window.sanearCodigoMermaid = sanearCodigoMermaid;

window.renderizarMermaidCompartido = async function (contenedor) {
  if (!contenedor || typeof window.mermaid === "undefined") return;
  try {
    mermaid.initialize({
      startOnLoad: false,
      theme: "default",
      securityLevel: "loose",
      fontSize: 16,
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      flowchart: { useMaxWidth: false, htmlLabels: true, nodeSpacing: 45, rankSpacing: 45 },
      sequence: { useMaxWidth: false }
    });
    const elementos = contenedor.querySelectorAll(".mermaid");
    for (let i = 0; i < elementos.length; i++) {
      const el = elementos[i];
      const estadoProc = el.getAttribute("data-processed");
      if (estadoProc === "true" || estadoProc === "processing") continue;
      let codigo = el.getAttribute("data-mermaid-raw") || (el.querySelector("svg") ? "" : (el.textContent || "").trim());
      if (!codigo) continue;
      el.setAttribute("data-mermaid-raw", codigo);
      el.setAttribute("data-processed", "processing");
      codigo = sanearCodigoMermaid(codigo);
      const id = "mermaid-comp-" + i + "-" + Math.random().toString(36).substring(2, 7);
      try {
        const res = await mermaid.render(id, codigo);
        el.innerHTML = res.svg;
        el.setAttribute("data-processed", "true");
        const svgEl = el.querySelector("svg");
        if (svgEl) {
          svgEl.style.width = "100%";
          svgEl.style.maxWidth = "100%";
          svgEl.style.minWidth = "60%";
          svgEl.style.height = "auto";
          svgEl.style.display = "block";
          svgEl.style.margin = "0 auto";
        }
      } catch (err) {
        // Limpiar inmediatamente cualquier elemento de error que mermaid inserte en el body
        document.querySelectorAll(`[id^="d${id}"], [id^="dmermaid-"]`).forEach(d => d.remove());
        el.innerHTML = `<div class="alerta-error-mermaid" style="padding:12px 16px; border:1px solid #ef4444; background:#fef2f2; color:#b91c1c; border-radius:6px; font-family:sans-serif; font-size:0.88rem; text-align:left; margin:1rem auto; max-width:90%;"><strong style="display:block; margin-bottom:4px;">⚠️ Error en la sintaxis del diagrama Mermaid:</strong><span style="font-size:0.82rem; white-space:pre-wrap;">${escapeHtml(err.message || String(err))}</span></div>`;
        el.setAttribute("data-processed", "true");
      }
    }
    // Erradicar cualquier residuo inyectado por el motor de Mermaid en el pie de página
    document.querySelectorAll('[id^="dmermaid-"]').forEach(d => d.remove());
  } catch (e) {
    console.warn("Fallo en renderizarMermaidCompartido:", e);
  }
};

function notificar(el, texto, tipo = "info") {
  if (!el) return;
  el.textContent = texto;
  el.className = `badge ${tipo === "error" ? "peligro" : tipo === "ok" ? "exito" : "neutral"}`;
  if (tipo !== "info") {
    setTimeout(() => { el.className = "badge neutral"; }, 3500);
  }
}

/* ─────────────────────────── Tema ─────────────────────────── */
function aplicarTema(tema) {
  document.documentElement.setAttribute("data-tema", tema);
  $("#btn-tema-icono").textContent = tema === "oscuro" ? "☀️" : "🌙";
  try { localStorage.setItem("mfo-tema", tema); } catch (e) { }
}

$("#btn-tema").addEventListener("click", () => {
  const actual = document.documentElement.getAttribute("data-tema");
  aplicarTema(actual === "oscuro" ? "claro" : "oscuro");
});

/* ─────────────────────────── Conmutación de apps ─────────────────────────── */
function abrirApp(nombre) {
  document.querySelectorAll(".riel-btn").forEach((b) => {
    b.classList.toggle("activo", b.dataset.app === nombre);
  });
  document.querySelectorAll(".app-panel").forEach((p) => {
    p.classList.toggle("activo", p.id === `panel-${nombre}`);
  });
  try { if (nombre === "documentos") listarDocumentos(); } catch (e) { console.error("Error en documentos:", e); }
  try { if (nombre === "docs") asegurarEditor(); } catch (e) { console.error("Error en docs:", e); }
  try { if (nombre === "word") { sincronizarAuditoriaWord(); renderizarHojaWordPreview().catch((e) => console.error("Error renderizando Word:", e)); } } catch (e) { console.error("Error en word:", e); }
  try { if (nombre === "pdf") { if (window.MFOPDF) { window.MFOPDF.abrir(); refrescarVisorPdfEnVivo(); } } } catch (e) { console.error("Error en pdf:", e); }
  try { if (nombre === "html") cargarVisorHtmlDedicado(); } catch (e) { console.error("Error en html:", e); }
  try { if (nombre === "tablas") cargarTablasExcel(); } catch (e) { console.error("Error en tablas:", e); }
  try { if (nombre === "entregables") renderizarListaEntregables(); } catch (e) { console.error("Error en entregables:", e); }
  try { if (nombre === "plantillas" && window.MFOPlantillas) window.MFOPlantillas.abrir(); } catch (e) { console.error("Error en plantillas:", e); }
}

document.querySelectorAll(".riel-btn").forEach((boton) => {
  boton.addEventListener("click", () => abrirApp(boton.dataset.app));
});

/* ─────────────────────────── Documentos (CRUD) ─────────────────────────── */
let seleccionadosDocsFusion = [];

function actualizarBarraFusion() {
  const barra = $("#barra-fusion-docs");
  const contador = $("#contador-seleccion-fusion");
  if (!barra) return;
  const total = seleccionadosDocsFusion.length;
  if (total >= 2) {
    if (contador) contador.textContent = `${total} seleccionados`;
    barra.style.display = "flex";
  } else {
    barra.style.display = "none";
  }
}

function cancelarSeleccionFusion() {
  seleccionadosDocsFusion = [];
  const checks = document.querySelectorAll(".doc-card-check");
  checks.forEach((c) => { c.checked = false; });
  const tarjetas = document.querySelectorAll(".doc-card");
  tarjetas.forEach((t) => { t.classList.remove("seleccionada"); });
  actualizarBarraFusion();
}

function sugerirNombreFusion() {
  if (!seleccionadosDocsFusion.length) return "";
  const primerDoc = (seleccionadosDocsFusion[0] || MFORegistro.ui("nombre_documento_corto")).replace(/\.md$/i, "");
  const restantes = seleccionadosDocsFusion.length - 1;
  return `Fusion - ${primerDoc} y ${restantes} mas`;
}

function actualizarNombreSugeridoSiCorresponde() {
  const inputNombre = $("#input-nombre-fusion");
  if (inputNombre && (!inputNombre.value || inputNombre.value.startsWith("Fusion - ") || inputNombre.value.startsWith("Fusión: "))) {
    inputNombre.value = sugerirNombreFusion();
  }
}

function renderizarListaOrdenFusion() {
  const lista = $("#lista-orden-fusion");
  if (!lista) return;
  lista.innerHTML = "";
  if (!seleccionadosDocsFusion.length) {
    lista.innerHTML = `<div class="item-orden-fusion"><span style="color:var(--text-muted);">No hay documentos seleccionados.</span></div>`;
    return;
  }
  seleccionadosDocsFusion.forEach((nombre, idx) => {
    const itemEl = document.createElement("div");
    itemEl.className = "item-orden-fusion";
    itemEl.setAttribute("data-idx", String(idx));
    itemEl.innerHTML = `
      <div class="item-orden-datos">
        <span class="item-orden-indice">${idx + 1}</span>
        <span class="item-orden-nombre" title="${escapeHtml(nombre)}">${escapeHtml(nombre.replace(/\.md$/i, ""))}</span>
      </div>
      <div class="item-orden-acciones">
        <button class="btn chico btn-subir" type="button" ${idx === 0 ? "disabled" : ""} title="Subir orden">▲ Subir</button>
        <button class="btn chico btn-bajar" type="button" ${idx === seleccionadosDocsFusion.length - 1 ? "disabled" : ""} title="Bajar orden">▼ Bajar</button>
      </div>
    `;

    const btnSubir = itemEl.querySelector(".btn-subir");
    const btnBajar = itemEl.querySelector(".btn-bajar");

    if (btnSubir) {
      btnSubir.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (idx > 0) {
          const item = seleccionadosDocsFusion[idx];
          seleccionadosDocsFusion.splice(idx, 1);
          seleccionadosDocsFusion.splice(idx - 1, 0, item);
          renderizarListaOrdenFusion();
          actualizarNombreSugeridoSiCorresponde();
        }
      });
    }

    if (btnBajar) {
      btnBajar.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (idx < seleccionadosDocsFusion.length - 1) {
          const item = seleccionadosDocsFusion[idx];
          seleccionadosDocsFusion.splice(idx, 1);
          seleccionadosDocsFusion.splice(idx + 1, 0, item);
          renderizarListaOrdenFusion();
          actualizarNombreSugeridoSiCorresponde();
        }
      });
    }

    lista.appendChild(itemEl);
  });
}

function abrirModalOrdenFusion() {
  if (seleccionadosDocsFusion.length < 2) {
    alert("Debes seleccionar al menos 2 documentos para fusionar.");
    return;
  }
  const checkBarra = $("#chk-fusion-capitulos") || $("#check-capitulos-fusion-barra");
  const checkModal = $("#chk-modal-fusion-capitulos") || $("#check-capitulos-fusion-modal");
  if (checkBarra && checkModal) {
    checkModal.checked = checkBarra.checked;
  }
  const inputNombre = $("#input-nombre-fusion");
  if (inputNombre) {
    inputNombre.value = sugerirNombreFusion();
  }
  renderizarListaOrdenFusion();
  const modal = $("#modal-orden-fusion");
  if (modal) modal.style.display = "flex";
}

function cerrarModalOrdenFusion() {
  const modal = $("#modal-orden-fusion");
  if (modal) modal.style.display = "none";
}

async function confirmarFusionDocs() {
  if (seleccionadosDocsFusion.length < 2) {
    alert("Debes seleccionar al menos 2 documentos para fusionar.");
    return;
  }
  const inputNombre = $("#input-nombre-fusion");
  let nombreResultado = (inputNombre?.value || "").trim();
  // Sanitizar preventivamente caracteres inválidos en Windows / rutas
  nombreResultado = nombreResultado.replace(/[:+*?"<>|\/\\]/g, " - ").replace(/\s+/g, " ").trim();
  if (!nombreResultado) {
    nombreResultado = sugerirNombreFusion();
  }

  const checkModal = $("#chk-modal-fusion-capitulos") || $("#check-capitulos-fusion-modal");
  const cadaCapitulo = checkModal ? checkModal.checked : true;

  const btnConfirmar = $("#btn-confirmar-fusion");
  if (btnConfirmar) {
    btnConfirmar.disabled = true;
    btnConfirmar.textContent = "Fusionando…";
  }

  try {
    const cuerpo = await jsonFetch(`${API.documentos}/fusionar`, {
      method: "POST",
      body: JSON.stringify({
        nombres: seleccionadosDocsFusion,
        nombre_resultado: nombreResultado,
        cada_documento_es_capitulo: cadaCapitulo,
      }),
    });
    cerrarModalOrdenFusion();
    cancelarSeleccionFusion();
    await listarDocumentos();
    const docCreado = cuerpo?.datos?.resultado || cuerpo?.datos?.nombre;
    if (docCreado) {
      notificar($("#docs-estado"), `✔ Fusión completada: ${docCreado}`, "ok");
      await abrirDocumento(docCreado);
    }
  } catch (error) {
    alert(`Error al fusionar documentos: ${error.message}`);
  } finally {
    if (btnConfirmar) {
      btnConfirmar.disabled = false;
      btnConfirmar.textContent = "✔ Confirmar y Fusionar";
    }
  }
}

async function listarDocumentos() {
  const contenedor = $("#lista-documentos");
  contenedor.innerHTML = `<div class="estado-vacio">Cargando documentos…</div>`;
  try {
    const cuerpo = await jsonFetch(API.documentos);
    const items = cuerpo.datos || [];
    // Filtrar seleccionados si alguno ya no existe
    seleccionadosDocsFusion = seleccionadosDocsFusion.filter((n) => items.some((it) => it.nombre === n));
    actualizarBarraFusion();

    if (!items.length) {
      contenedor.innerHTML = `<div class="estado-vacio">Aún no hay documentos.<br>Crea el primero con ＋ Nuevo.</div>`;
      return;
    }
    contenedor.innerHTML = "";
    for (const item of items) {
      const estaSeleccionado = seleccionadosDocsFusion.includes(item.nombre);
      const tarjeta = document.createElement("div");
      tarjeta.className = `vidrio tarjeta doc-card${estaSeleccionado ? " seleccionada" : ""}`;
      const fecha = new Date(item.modificado * 1000).toLocaleString("es");
      tarjeta.innerHTML = `
        <div class="doc-card-cabecera">
          <input type="checkbox" class="doc-card-check" data-nombre="${escapeHtml(item.nombre)}" ${estaSeleccionado ? "checked" : ""} title="Seleccionar para fusionar">
          <div class="doc-card-nombre"></div>
          ${item.en_fusion ? '<span class="chip-fusion" title="Documento incluido en una fusión">🔗 en fusión</span>' : ""}
        </div>
        <div class="doc-card-meta">${tamanoLegible(item.tamano)} · ${fecha}</div>
        <div class="doc-card-acciones">
          <button class="btn chico btn-abrir">Abrir</button>
          <button class="btn chico btn-exportar-md" title="Exportar / Descargar Markdown (.md)">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:text-bottom; margin-right:3px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>MD</span>
          </button>
          <button class="btn btn-peligro chico btn-eliminar" title="Eliminar documento">🗑</button>
        </div>`;
      tarjeta.querySelector(".doc-card-nombre").textContent = item.nombre.replace(/\.md$/i, "");

      const checkEl = tarjeta.querySelector(".doc-card-check");
      checkEl.addEventListener("click", (e) => e.stopPropagation());
      checkEl.addEventListener("change", (e) => {
        e.stopPropagation();
        if (checkEl.checked) {
          if (!seleccionadosDocsFusion.includes(item.nombre)) {
            seleccionadosDocsFusion.push(item.nombre);
          }
          tarjeta.classList.add("seleccionada");
        } else {
          seleccionadosDocsFusion = seleccionadosDocsFusion.filter((n) => n !== item.nombre);
          tarjeta.classList.remove("seleccionada");
        }
        actualizarBarraFusion();
      });

      tarjeta.querySelector(".btn-abrir").addEventListener("click", (e) => {
        e.stopPropagation();
        abrirDocumento(item.nombre);
      });
      tarjeta.querySelector(".btn-exportar-md").addEventListener("click", async (e) => {
        e.stopPropagation();
        await exportarDocumentoMd(item.nombre);
      });
      tarjeta.querySelector(".btn-eliminar").addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm(`¿Eliminar «${item.nombre}»? Esta acción no se puede deshacer.`)) return;
        await jsonFetch(`${API.documentos}/${encodeURIComponent(item.nombre)}`, { method: "DELETE" });
        listarDocumentos();
      });
      tarjeta.querySelector(".doc-card-acciones").addEventListener("click", (e) => e.stopPropagation());
      tarjeta.addEventListener("dblclick", () => abrirDocumento(item.nombre));
      contenedor.appendChild(tarjeta);
    }
  } catch (error) {
    contenedor.innerHTML = `<div class="estado-vacio">Error al cargar: ${error.message}</div>`;
  }
}

async function exportarDocumentoMd(nombre) {
  try {
    const cuerpo = await jsonFetch(`${API.documentos}/${encodeURIComponent(nombre)}`);
    const contenido = cuerpo?.datos?.contenido ?? "";
    const blob = new Blob([contenido], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    const nombreMd = nombre.toLowerCase().endsWith(".md") ? nombre : `${nombre}.md`;
    enlace.href = url;
    enlace.download = nombreMd;
    document.body.appendChild(enlace);
    enlace.click();
    document.body.removeChild(enlace);
    URL.revokeObjectURL(url);
    if (typeof registrarEntregable === "function") {
      registrarEntregable("md", nombreMd, url, tamanoLegible(blob.size));
    }
    const badgeDocs = $("#docs-estado");
    if (badgeDocs) {
      notificar(badgeDocs, `✔ Exportado ${nombreMd}`, "ok");
    }
  } catch (error) {
    alert(`No se pudo exportar «${nombre}»: ${error.message}`);
  }
}

async function abrirDocumento(nombre, appDestino = "docs") {
  try {
    const cuerpo = await jsonFetch(`${API.documentos}/${encodeURIComponent(nombre)}`);
    estado.documento = cuerpo.datos.nombre;
    $("#editor-markdown").value = cuerpo.datos.contenido;
    const baseNombre = cuerpo.datos.nombre.replace(/\.md$/i, "");
    $("#titulo-documento").value = baseNombre;
    if ($("#docs-titulo-input")) $("#docs-titulo-input").value = baseNombre;
    const listo = await esperarEditor();
    if (listo && !modoFuenteActivo()) {
      try { await window.MFOEditor.setTexto(cuerpo.datos.contenido); } catch (e) { /* queda el fuente */ }
    }
    estado.sucio = false;
    notificar($("#docs-estado"), "cargado", "ok");
    abrirApp(appDestino || MFORegistro.ui("app_inicial"));
    if (appDestino === "word") {
      renderizarHojaWordPreview().catch((e) => console.error("Error renderizando Word:", e));
    } else if (appDestino === "html") {
      await cargarVisorHtmlDedicado();
    } else if (appDestino !== "pdf") {
      previsualizar();
    }
  } catch (error) {
    alert(`No se pudo abrir el documento: ${error.message}`);
  }
}

$("#btn-nuevo-doc").addEventListener("click", async () => {
  const nombre = prompt("Nombre del nuevo documento:", "Nuevo documento");
  if (!nombre) return;
  const errorVal = validarNombreDocumento(nombre);
  if (errorVal) {
    alert(errorVal);
    return;
  }
  try {
    await jsonFetch(API.documentos, {
      method: "POST",
      body: JSON.stringify({ nombre }),
    });
    await listarDocumentos();
    await abrirDocumento(nombre.toLowerCase().endsWith(".md") ? nombre : `${nombre}.md`);
  } catch (error) {
    alert(`No se pudo crear: ${error.message}`);
  }
});

$("#btn-volver-documentos").addEventListener("click", () => abrirApp("documentos"));

/* ── Event listeners para barra contextual y modal de fusión ── */
$("#btn-cancelar-seleccion-fusion")?.addEventListener("click", () => cancelarSeleccionFusion());
$("#btn-abrir-modal-fusion")?.addEventListener("click", () => abrirModalOrdenFusion());
$("#btn-cerrar-modal-fusion")?.addEventListener("click", () => cerrarModalOrdenFusion());
$("#btn-cancelar-modal-fusion")?.addEventListener("click", () => cerrarModalOrdenFusion());
$("#btn-confirmar-fusion")?.addEventListener("click", () => confirmarFusionDocs());

const checkCapBarra = $("#chk-fusion-capitulos") || $("#check-capitulos-fusion-barra");
const checkCapModal = $("#chk-modal-fusion-capitulos") || $("#check-capitulos-fusion-modal");
if (checkCapBarra && checkCapModal) {
  checkCapBarra.addEventListener("change", (e) => {
    checkCapModal.checked = e.target.checked;
  });
  checkCapModal.addEventListener("change", (e) => {
    checkCapBarra.checked = e.target.checked;
  });
}

/* ── Sincronización de título entre barra superior y cabecera Docs ── */
const inpTituloTop = $("#titulo-documento");
const inpTituloDocs = $("#docs-titulo-input");
if (inpTituloTop && inpTituloDocs) {
  inpTituloTop.addEventListener("input", () => {
    inpTituloDocs.value = inpTituloTop.value;
    estado.sucio = true;
  });
  inpTituloDocs.addEventListener("input", () => {
    inpTituloTop.value = inpTituloDocs.value;
    estado.sucio = true;
  });
}

/* ─────────────────────────── Docs: guardar + vista en vivo ─────────────── */
async function guardarDocumento(silencioso = false) {
  const contenido = await obtenerMarkdownActual();
  $("#editor-markdown").value = contenido;

  const tituloActual = ($("#docs-titulo-input")?.value || $("#titulo-documento").value || "").trim();
  const errorVal = validarNombreDocumento(tituloActual);
  if (errorVal) {
    alert(errorVal);
    notificar($("#docs-estado"), "nombre inválido", "error");
    return;
  }

  const nombreDeseado = tituloActual.toLowerCase().endsWith(".md") ? tituloActual : `${tituloActual}.md`;

  if (!estado.documento) {
    try {
      await jsonFetch(API.documentos, {
        method: "POST",
        body: JSON.stringify({ nombre: nombreDeseado, contenido }),
      });
      estado.documento = nombreDeseado;
      estado.sucio = false;
      await listarDocumentos();
      if (!silencioso) notificar($("#docs-estado"), "guardado ✓", "ok");
    } catch (error) {
      notificar($("#docs-estado"), error.message.includes("existe") ? "ya existe" : "error al crear", "error");
    }
    return;
  }

  if (estado.documento !== nombreDeseado) {
    try {
      await jsonFetch(`${API.documentos}/${encodeURIComponent(estado.documento)}/renombrar`, {
        method: "POST",
        body: JSON.stringify({ nuevo_nombre: nombreDeseado }),
      });
      estado.documento = nombreDeseado;
      await listarDocumentos();
    } catch (error) {
      alert(`No se pudo renombrar el documento: ${error.message}`);
      notificar($("#docs-estado"), "error al renombrar", "error");
      return;
    }
  }

  try {
    await jsonFetch(`${API.documentos}/${encodeURIComponent(estado.documento)}`, {
      method: "PUT",
      body: JSON.stringify({ contenido }),
    });
    estado.sucio = false;
    if (!silencioso) notificar($("#docs-estado"), "guardado ✓", "ok");
  } catch (error) {
    notificar($("#docs-estado"), `error: ${error.message}`, "error");
  }
}

async function guardarComoDocumento() {
  const baseActual = ($("#docs-titulo-input")?.value || $("#titulo-documento").value || MFORegistro.ui("nombre_documento")).trim().replace(/\.md$/i, "");
  const nuevoNombre = prompt("Guardar como (nuevo nombre o copia):", `${baseActual}-copia`);
  if (!nuevoNombre) return;

  const errorVal = validarNombreDocumento(nuevoNombre);
  if (errorVal) {
    alert(errorVal);
    return;
  }

  const contenido = await obtenerMarkdownActual();
  const nombreConExt = nuevoNombre.toLowerCase().endsWith(".md") ? nuevoNombre : `${nuevoNombre}.md`;

  try {
    await jsonFetch(API.documentos, {
      method: "POST",
      body: JSON.stringify({ nombre: nombreConExt, contenido }),
    });
    estado.documento = nombreConExt;
    const baseLimpia = nombreConExt.replace(/\.md$/i, "");
    $("#titulo-documento").value = baseLimpia;
    if ($("#docs-titulo-input")) $("#docs-titulo-input").value = baseLimpia;
    estado.sucio = false;
    await listarDocumentos();
    notificar($("#docs-estado"), "guardado como copia ✓", "ok");
  } catch (error) {
    alert(`No se pudo guardar como nuevo documento: ${error.message}`);
  }
}

$("#btn-guardar-doc").addEventListener("click", () => guardarDocumento());
$("#btn-guardar-como-doc")?.addEventListener("click", guardarComoDocumento);

let temporizadorVista = null;
function previsualizar() {
  clearTimeout(temporizadorVista);
  temporizadorVista = setTimeout(async () => {
    const visor = $("#visor-docs");
    if (!visor) return;
    const texto = $("#editor-markdown").value;
    if (!texto.trim()) {
      visor.srcdoc = "";
      return;
    }
    try {
      const cuerpo = await jsonFetch(API.preview, {
        method: "POST",
        body: JSON.stringify({ texto, titulo: "Vista previa" }),
      });
      const htmlNuevo = cuerpo.datos.html;
      const docIframe = visor.contentDocument || visor.contentWindow?.document;
      const winIframe = docIframe?.defaultView || visor.contentWindow;
      const actualContenedor = docIframe?.querySelector(".contenedor") || docIframe?.querySelector("article");

      if (actualContenedor && winIframe) {
        const docNuevo = new DOMParser().parseFromString(htmlNuevo, "text/html");
        const nuevoContenedor = docNuevo.querySelector(".contenedor") || docNuevo.querySelector("article");
        const necesitaMermaidEnIframe =
          nuevoContenedor &&
          nuevoContenedor.querySelector(".mermaid") &&
          typeof winIframe.mermaid === "undefined" &&
          typeof window.mermaid === "undefined";

        if (nuevoContenedor && !necesitaMermaidEnIframe) {
          const cacheMermaid = new Map();
          actualContenedor.querySelectorAll(".mermaid[data-processed='true']").forEach((el) => {
            const raw = (el.getAttribute("data-mermaid-raw") || "").trim();
            if (raw && el.querySelector("svg")) {
              cacheMermaid.set(raw, el.innerHTML);
            }
          });

          actualContenedor.innerHTML = nuevoContenedor.innerHTML;

          actualContenedor.querySelectorAll(".mermaid").forEach((el) => {
            const raw = (el.getAttribute("data-mermaid-raw") || el.textContent || "").trim();
            if (raw && cacheMermaid.has(raw)) {
              el.innerHTML = cacheMermaid.get(raw);
              el.setAttribute("data-mermaid-raw", raw);
              el.setAttribute("data-processed", "true");
            }
          });

          if (typeof winIframe._iniciarRenderMarkflow === "function") {
            try {
              await winIframe._iniciarRenderMarkflow();
            } catch (errFlow) {
              console.warn("Aviso _iniciarRenderMarkflow in-place:", errFlow);
            }
          }
          if (actualContenedor.querySelector(".mermaid:not([data-processed='true']):not([data-processed='processing'])") && window.renderizarMermaidCompartido) {
            await window.renderizarMermaidCompartido(actualContenedor);
          }
          return;
        }
      }
      visor.srcdoc = htmlNuevo;
    } catch (error) {
      visor.srcdoc = `<pre style="padding:16px;color:#c0392b">Error de vista previa: ${error.message}</pre>`;
    }
  }, 300);
}

$("#editor-markdown").addEventListener("input", () => {
  estado.sucio = true;
  notificar($("#docs-estado"), "editando…", "info");
  previsualizar();
});

/* ── Scroll Sincronizado Bidireccional Proporcional en Docs (v1.12.0) ──────── */
let sincronizandoScroll = false;
function vincularScrollDocs() {
  const iframe = $("#visor-docs");
  const ta = $("#editor-markdown");

  const sincronizar = (origen, destino) => {
    if (sincronizandoScroll || !origen || !destino) return;
    sincronizandoScroll = true;
    const maxOrigen = origen.scrollHeight - origen.clientHeight;
    const maxDestino = destino.scrollHeight - destino.clientHeight;
    if (maxOrigen > 0 && maxDestino > 0) {
      const porcentaje = origen.scrollTop / maxOrigen;
      destino.scrollTop = porcentaje * maxDestino;
    }
    setTimeout(() => { sincronizandoScroll = false; }, 40);
  };

  const getElementoActivoEditor = () => {
    if (modoFuenteActivo()) return ta;
    return $("#editor-docs .ProseMirror") || $("#editor-docs");
  };

  ta.addEventListener("scroll", () => {
    if (!modoFuenteActivo()) return;
    try {
      const docIframe = iframe.contentDocument || iframe.contentWindow?.document;
      const scrollDestino = docIframe?.scrollingElement || docIframe?.documentElement || docIframe?.body;
      if (scrollDestino) sincronizar(ta, scrollDestino);
    } catch (e) { }
  }, { passive: true });

  const editorVisual = $("#editor-docs");
  if (editorVisual) {
    editorVisual.addEventListener("scroll", (e) => {
      const target = e.target;
      try {
        const docIframe = iframe.contentDocument || iframe.contentWindow?.document;
        const scrollDestino = docIframe?.scrollingElement || docIframe?.documentElement || docIframe?.body;
        if (scrollDestino) sincronizar(target, scrollDestino);
      } catch (err) { }
    }, { passive: true, capture: true });
  }

  iframe.addEventListener("load", async () => {
    try {
      const docIframe = iframe.contentDocument || iframe.contentWindow?.document;
      const winIframe = docIframe?.defaultView || iframe.contentWindow;
      const scrollOrigen = docIframe?.scrollingElement || docIframe?.documentElement || docIframe?.body;
      if (winIframe && scrollOrigen) {
        winIframe.addEventListener("scroll", () => {
          const editorDestino = getElementoActivoEditor();
          if (editorDestino) sincronizar(scrollOrigen, editorDestino);
        }, { passive: true });
      }

      // Renderizado reactivo y unificado de diagramas Mermaid en Docs (Fase 1)
      if (docIframe) {
        if (typeof winIframe?._iniciarRenderMarkflow === "function") {
          try {
            await winIframe._iniciarRenderMarkflow();
          } catch (errFlow) {
            console.warn("Fallo _iniciarRenderMarkflow en iframe:", errFlow);
          }
        }
        if (docIframe.querySelector(".mermaid:not([data-processed='true']):not([data-processed='processing'])") && window.renderizarMermaidCompartido) {
          await window.renderizarMermaidCompartido(docIframe.body);
        }
      }
    } catch (e) { }
  });
}
vincularScrollDocs();

/* ─────────────────── Docs: editor visual (ProseMirror) ─────────────────── */
/* Carga perezosa del bundle vendorizado (window.PM) solo al abrir Docs.      */
let promesaPM = null;
function cargarPM() {
  if (window.PM) return Promise.resolve();
  if (promesaPM) return promesaPM;
  promesaPM = new Promise((res, rej) => {
    const s = document.createElement("script");
    s.src = "/static/vendor/prosemirror/pm_bundle.js";
    s.onload = () => res();
    s.onerror = () => rej(new Error("No se pudo cargar el bundle de ProseMirror"));
    document.head.appendChild(s);
  });
  return promesaPM;
}

let promesaEditor = null;
function esperarEditor() {
  if (promesaEditor) return promesaEditor;
  if (window.MFOEditor && window.MFOEditor.listo) return Promise.resolve(true);
  return Promise.resolve(false);
}

async function asegurarEditor() {
  if (!promesaEditor) {
    promesaEditor = (async () => {
      try {
        await cargarPM();
        await window.MFOEditor.init($("#editor-docs"), {
          texto: $("#editor-markdown").value,
          alCambiar: (md) => {
            const ta = $("#editor-markdown");
            if (ta.value !== md) ta.value = md;
            estado.sucio = true;
            notificar($("#docs-estado"), "editando…", "info");
            previsualizar();
          },
        });
        window.MFOEditor.listo = true;
        return true;
      } catch (error) {
        activarModoFuente(true);  /* fallback: el SSOT (textarea) siempre edita */
        notificar($("#docs-estado"), "modo fuente (editor visual no disponible)", "error");
        return false;
      }
    })();
  }
  return promesaEditor;
}

function modoFuenteActivo() {
  return $("#split-docs").classList.contains("modo-fuente");
}

function activarModoFuente(activo) {
  $("#split-docs").classList.toggle("modo-fuente", activo);
  const btn = $("#btn-modo-fuente");
  if (btn) {
    btn.classList.toggle("activo", activo);
    btn.innerHTML = activo ? `</> Fuente Activo` : `</> Fuente`;
  }
  if (activo) {
    $("#editor-markdown").focus();
  } else if (window.MFOEditor && window.MFOEditor.listo) {
    window.MFOEditor.setTexto($("#editor-markdown").value)
      .then(() => window.MFOEditor.foco())
      .catch(() => activarModoFuente(true));
  }
}

$("#btn-modo-fuente").addEventListener("click", () => {
  activarModoFuente(!modoFuenteActivo());
});

/* Embeber notas en modo código si se pulsa data-bd="nota" */
const btnBdNota = document.querySelector('[data-bd="nota"]');
if (btnBdNota) {
  btnBdNota.addEventListener("click", () => {
    if (modoFuenteActivo()) {
      const ta = $("#editor-markdown");
      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      const sel = ta.value.substring(start, end);
      if (sel) {
        const lineas = sel.split("\n").map(l => `> ${l}`).join("\n");
        ta.setRangeText(`> [!NOTE]\n${lineas}\n`, start, end, "end");
      } else {
        ta.setRangeText(`> [!NOTE]\n> Nota: `, start, end, "end");
      }
      estado.sucio = true;
      previsualizar();
    }
  });
}

$("#btn-sanear-pegado").addEventListener("click", async () => {
  const texto = $("#editor-markdown").value;
  if (!texto.trim()) {
    notificar($("#docs-estado"), "nada que sanear", "info");
    return;
  }
  try {
    const cuerpo = await jsonFetch(API.sanear, {
      method: "POST",
      body: JSON.stringify({ texto }),
    });
    const nuevo = cuerpo.datos.texto;
    const avisos = cuerpo.datos.avisos || [];
    $("#editor-markdown").value = nuevo;
    const listo = await esperarEditor();
    if (listo && !modoFuenteActivo()) {
      try { await window.MFOEditor.setTexto(nuevo); } catch (e) { /* fuente */ }
    }
    estado.sucio = true;
    previsualizar();
    notificar($("#docs-estado"),
      avisos.length ? `saneado · ${avisos.length} aviso(s)` : "saneado ✓", "ok");
  } catch (error) {
    notificar($("#docs-estado"), `error: ${error.message}`, "error");
  }
});

/* ── Validación y Diagnóstico de Fórmulas Matemáticas (Fase 2) ── */
const btnValidarFormulas = $("#btn-validar-formulas");
const modalValidarFormulas = $("#modal-validar-formulas");
const btnCerrarModalFormulas = $("#btn-cerrar-modal-formulas");

if (btnCerrarModalFormulas && modalValidarFormulas) {
  btnCerrarModalFormulas.addEventListener("click", () => {
    modalValidarFormulas.style.display = "none";
  });
  modalValidarFormulas.addEventListener("click", (e) => {
    if (e.target === modalValidarFormulas) {
      modalValidarFormulas.style.display = "none";
    }
  });
}

function irALineaMarkdown(numLinea) {
  if (!numLinea) return;
  activarModoFuente(true);
  const ta = $("#editor-markdown");
  if (!ta) return;
  const lineas = ta.value.split("\n");
  let charPos = 0;
  for (let i = 0; i < Math.min(numLinea - 1, lineas.length); i++) {
    charPos += lineas[i].length + 1;
  }
  ta.focus();
  ta.setSelectionRange(charPos, charPos + (lineas[numLinea - 1] ? lineas[numLinea - 1].length : 0));
  const alturaLinea = 20;
  ta.scrollTop = Math.max(0, (numLinea - 3) * alturaLinea);
  if (modalValidarFormulas) modalValidarFormulas.style.display = "none";
}

if (btnValidarFormulas) {
  btnValidarFormulas.addEventListener("click", async () => {
    const texto = await obtenerMarkdownActual();
    if (!texto.trim()) {
      notificar($("#docs-estado"), "documento vacío", "info");
      return;
    }
    notificar($("#docs-estado"), "validando fórmulas…", "info");
    try {
      const resp = await jsonFetch("/api/office/validar-formulas", {
        method: "POST",
        body: JSON.stringify({ markdown: texto }),
      });
      const resumen = resp.resumen || { total: 0, correctas: 0, con_error: 0, detalles: [] };

      const statTotal = $("#stat-total-formulas");
      const statCorr = $("#stat-correctas-formulas");
      const statErr = $("#stat-error-formulas");
      const contenedor = $("#contenedor-lista-errores-formulas");

      if (statTotal) statTotal.textContent = `Total fórmulas: ${resumen.total}`;
      if (statCorr) statCorr.textContent = `Correctas: ${resumen.correctas}`;
      if (statErr) statErr.textContent = `Con error / advertencia: ${resumen.con_error}`;

      if (contenedor) {
        contenedor.innerHTML = "";
        if (resumen.con_error === 0) {
          contenedor.innerHTML = `
            <div style="padding: 1.5rem; text-align: center; border-radius: var(--radius-sm); background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2);">
              <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✅</div>
              <strong style="color: #10b981;">¡Todas las fórmulas son válidas!</strong>
              <p style="margin: 0.4rem 0 0 0; font-size: 0.85rem; color: var(--text-muted);">
                Se analizaron ${resumen.total} expresión(es) matemática(s) y no se encontraron delimitadores rotos ni inconsistencias de llaves.
              </p>
            </div>
          `;
        } else {
          resumen.detalles.forEach(d => {
            const card = document.createElement("div");
            card.style.cssText = "padding: 0.85rem; border-radius: var(--radius-sm); background: var(--bg-card); border: 1px solid rgba(239, 68, 68, 0.3); display: flex; flex-direction: column; gap: 0.4rem;";

            const cabecera = document.createElement("div");
            cabecera.style.cssText = "display: flex; justify-content: space-between; align-items: center;";
            cabecera.innerHTML = `
              <span style="font-weight: 600; font-size: 0.85rem; color: #ef4444;">
                ⚠️ Línea ${d.linea} · [${d.tipo}] Fórmula #${d.indice}
              </span>
              <button class="btn chico" style="font-size: 0.75rem; padding: 0.15rem 0.5rem;" title="Ir a la línea en el editor Markdown">
                🔍 Ir a la línea
              </button>
            `;
            const btnIr = cabecera.querySelector("button");
            btnIr.onclick = () => irALineaMarkdown(d.linea);

            const errLista = document.createElement("ul");
            errLista.style.cssText = "margin: 0; padding-left: 1.2rem; font-size: 0.82rem; color: #ef4444;";
            d.errores.forEach(err => {
              const li = document.createElement("li");
              li.textContent = err;
              errLista.appendChild(li);
            });

            const preFrag = document.createElement("pre");
            preFrag.style.cssText = "margin: 0; padding: 0.4rem 0.6rem; background: var(--bg-input); border-radius: 4px; font-size: 0.8rem; overflow-x: auto; color: var(--text-main); font-family: var(--font-mono, monospace);";
            preFrag.textContent = d.cuerpo_original || d.cuerpo;

            card.appendChild(cabecera);
            card.appendChild(errLista);
            card.appendChild(preFrag);
            contenedor.appendChild(card);
          });
        }
      }

      if (modalValidarFormulas) {
        modalValidarFormulas.style.display = "flex";
      }
      notificar($("#docs-estado"), `Diagnóstico: ${resumen.correctas} ok, ${resumen.con_error} con error`, resumen.con_error ? "info" : "ok");
    } catch (err) {
      notificar($("#docs-estado"), `error validando: ${err.message}`, "error");
    }
  });
}

/* ── Soporte Robusto de Imágenes con Referencia Base64 al Pie (v1.13.0) ── */
async function insertarImagenReferencia(archivo, nombreAlt) {
  if (!archivo) return;

  // Validación estricta de formato: solo PNG, JPG, GIF
  const tiposValidos = ["image/png", "image/jpeg", "image/jpg", "image/gif"];
  const extValida = /\.(png|jpe?g|gif)$/i.test(archivo.name || "");
  if (!tiposValidos.includes((archivo.type || "").toLowerCase()) && !extValida) {
    alert("Formato de imagen no compatible. Solo se admiten archivos PNG, JPG y GIF.");
    return;
  }

  const TAM_MAX = 5 * 1024 * 1024; // 5 MB
  if (archivo.size > TAM_MAX) {
    const continuar = confirm(`La imagen pesa ${(archivo.size / (1024 * 1024)).toFixed(1)} MB (máximo recomendado: 5 MB). Puede ralentizar el documento. ¿Deseas insertarla de todos modos?`);
    if (!continuar) return;
  }

  const lector = new FileReader();
  lector.onload = async (e) => {
    const dataUri = e.target.result;
    const textoActual = await obtenerMarkdownActual();

    // Contar imágenes con etiqueta [img-N]
    const coincidencias = textoActual.match(/\[img-(\d+)\]/g) || [];
    let maxIdx = 0;
    for (const m of coincidencias) {
      const num = parseInt(m.replace(/\D/g, ""), 10);
      if (num > maxIdx) maxIdx = num;
    }
    const nuevoIdx = maxIdx + 1;
    const tagRef = `img-${nuevoIdx}`;
    const altLimpio = (nombreAlt || archivo.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ") || `imagen-${nuevoIdx}`).trim();

    const marcaInline = `![${altLimpio}][${tagRef}]\n\n`;
    const defPie = `\n\n[${tagRef}]: ${dataUri}\n`;

    const ta = $("#editor-markdown");
    if (modoFuenteActivo()) {
      const pos = ta.selectionStart || ta.value.length;
      ta.value = ta.value.substring(0, pos) + marcaInline + ta.value.substring(pos) + defPie;
      ta.selectionStart = ta.selectionEnd = pos + marcaInline.length;
    } else {
      const nuevoTexto = (textoActual.trim() ? textoActual + "\n\n" : "") + marcaInline + defPie;
      ta.value = nuevoTexto;
      const listo = await esperarEditor();
      if (listo) {
        try { await window.MFOEditor.setTexto(nuevoTexto); } catch (err) { }
      }
    }

    estado.sucio = true;
    previsualizar();
    notificar($("#docs-estado"), `Imagen ${altLimpio} insertada ✓`, "ok");
  };
  lector.readAsDataURL(archivo);
}

const btnDocsInsertarImg = $("#btn-docs-insertar-img");
const inputDocsImgFile = $("#input-docs-img-file");

if (btnDocsInsertarImg && inputDocsImgFile) {
  btnDocsInsertarImg.addEventListener("click", () => inputDocsImgFile.click());
  inputDocsImgFile.addEventListener("change", () => {
    const archivo = inputDocsImgFile.files && inputDocsImgFile.files[0];
    inputDocsImgFile.value = "";
    if (!archivo) return;
    const sugerido = archivo.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
    const nombreAlt = prompt("Descripción alternativa para la imagen:", sugerido);
    insertarImagenReferencia(archivo, nombreAlt || sugerido);
  });
}

function interceptarPegadoImagen(e) {
  const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type && item.type.indexOf("image") !== -1) {
      const archivo = item.getAsFile();
      if (archivo) {
        e.preventDefault();
        insertarImagenReferencia(archivo, "imagen-pegada");
        break;
      }
    }
  }
}

$("#editor-markdown")?.addEventListener("paste", interceptarPegadoImagen);
$("#editor-docs")?.addEventListener("paste", interceptarPegadoImagen);

/* ── Botón 2: Quitar todas las notas (v1.12.0) ────────────────────────────── */
const btnDocsQuitarNotas = $("#btn-docs-quitar-todas-notas");
if (btnDocsQuitarNotas) {
  btnDocsQuitarNotas.addEventListener("click", async () => {
    const textoActual = await obtenerMarkdownActual();
    if (!textoActual.trim()) {
      notificar($("#docs-estado"), "documento vacío", "info");
      return;
    }

    // Limpieza global de marcas de nota > al inicio de línea y tags de alert
    let limpio = textoActual.replace(/^\s*>\s?/gm, "");
    limpio = limpio.replace(/\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n?/gi, "");

    $("#editor-markdown").value = limpio;
    const listo = await esperarEditor();
    if (listo && !modoFuenteActivo()) {
      try { await window.MFOEditor.setTexto(limpio); } catch (err) { }
    }

    estado.sucio = true;
    previsualizar();
    notificar($("#docs-estado"), "todas las notas eliminadas ✓", "ok");
  });
}

/* Atajos: Ctrl+S guardar · Ctrl+Enter previsualizar */
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
    e.preventDefault();
    guardarDocumento();
  }
});

/* ─────────────────── Utilidad: Obtener Markdown Actual Sincronizado ─────── */
async function obtenerMarkdownActual() {
  if (window.MFOEditor && window.MFOEditor.listo && !modoFuenteActivo()) {
    try {
      const texto = await window.MFOEditor.getTexto();
      if (typeof texto === "string" && texto.trim()) {
        $("#editor-markdown").value = texto;
        return texto;
      }
    } catch (e) {
      console.warn("Fallo leyendo de MFOEditor:", e);
    }
  }
  return $("#editor-markdown") ? $("#editor-markdown").value : "";
}

/* ─────────────────── Importador de archivos .md en Documentos ───────────── */
const btnImportarMd = $("#btn-importar-md");
const inputImportarMd = $("#input-md-importar");
if (btnImportarMd && inputImportarMd) {
  btnImportarMd.addEventListener("click", () => inputImportarMd.click());
  inputImportarMd.addEventListener("change", () => {
    const file = inputImportarMd.files && inputImportarMd.files[0];
    inputImportarMd.value = "";
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (e) => {
      const contenido = String(e.target.result || "");
      const nombreBase = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
      try {
        await jsonFetch(API.documentos, {
          method: "POST",
          body: JSON.stringify({ nombre: nombreBase, contenido }),
        });
        await listarDocumentos();
        await abrirDocumento(`${nombreBase}.md`);
        notificar($("#docs-estado"), `Importado: ${file.name}`, "ok");
      } catch (err) {
        alert(`Error al importar Markdown: ${err.message}`);
      }
    };
    reader.onerror = () => alert("Error al leer el archivo Markdown como UTF-8.");
    reader.readAsText(file, "UTF-8");
  });
}

/* ─────────────────────────────────────────────────────────────────────────────
   MEJORAS v1.13.0 — ARQUITECTURA DE DOCUMENTO ÚNICO Y BARRAS LATERALES (340 px)
   Docs SSOT · Barras Laterales (Word, HTML, PDF, Excel) · Entregables de Sesión
   ───────────────────────────────────────────────────────────────────────────── */

/* ══════════════ 1. REGISTRO DE ENTREGABLES DE LA SESIÓN ══════════════ */
const entregablesSesion = [];

function registrarEntregable(formato, archivo, url, tamano) {
  let fNorm = (formato || "").toLowerCase();
  if (fNorm === "docx") fNorm = "word";
  if (fNorm === "xlsx") fNorm = "excel";
  if (fNorm === "markdown") fNorm = "md";

  const nuevo = {
    id: "ent_" + Date.now() + "_" + Math.floor(Math.random() * 1000),
    formato: fNorm,
    archivo: archivo,
    url: url,
    tamano: tamano || MFORegistro.ui("marcador_vacio"),
    hora: new Date().toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" }),
  };
  entregablesSesion.unshift(nuevo);
  renderizarListaEntregables();
  notificar($("#docs-estado"), `Generado: ${archivo}`, "ok");
}

function renderizarListaEntregables() {
  const cuadricula = $("#cuadricula-entregables");
  const vacio = $("#entregables-vacio");
  const badgeTotal = $("#badge-total-entregables");

  if (badgeTotal) badgeTotal.textContent = `${entregablesSesion.length} entregable(s)`;
  if (!cuadricula) return;

  if (entregablesSesion.length === 0) {
    if (vacio) vacio.style.display = "block";
    cuadricula.style.display = "none";
    cuadricula.innerHTML = "";
    return;
  }

  if (vacio) vacio.style.display = "none";
  cuadricula.style.display = "grid";
  cuadricula.innerHTML = "";

  entregablesSesion.forEach((item) => {
    const card = document.createElement("article");
    card.className = "tarjeta-entregable";

    let labelApp = item.formato.toUpperCase();
    let appDestino = item.formato;
    if (item.formato === "word") labelApp = "WORD";
    if (item.formato === "pdf") labelApp = "PDF";
    if (item.formato === "html") labelApp = "HTML";
    if (item.formato === "excel") { labelApp = "EXCEL"; appDestino = "tablas"; }
    if (item.formato === "md") { labelApp = "MARKDOWN"; appDestino = "docs"; }

    card.innerHTML = `
      <div class="tarjeta-entregable-cabecera">
        <span class="badge-formato badge-formato-${item.formato}">${labelApp}</span>
        <span class="tarjeta-entregable-meta">${item.tamano} · ${item.hora}</span>
      </div>
      <div class="tarjeta-entregable-nombre" title="${item.archivo}">${item.archivo}</div>
      <div class="tarjeta-entregable-acciones">
        <a href="${item.url}" download="${item.archivo}" class="btn chico btn-primario" title="Descargar archivo">⬇ Descargar</a>
        <button type="button" class="btn chico btn-fantasma btn-ver-entregable" title="Ver en pestaña">👁️ Ver</button>
      </div>
    `;

    card.querySelector(".btn-ver-entregable").addEventListener("click", () => {
      abrirApp(appDestino);
    });

    cuadricula.appendChild(card);
  });
}

$("#btn-limpiar-entregables")?.addEventListener("click", () => {
  if (!entregablesSesion.length) return;
  if (confirm("¿Deseas vaciar la lista de entregables generados en esta sesión?")) {
    entregablesSesion.length = 0;
    renderizarListaEntregables();
  }
});

/* ══════════════ 2. CONTROLADORES DE BARRAS LATERALES Y REGISTRO ══════════════ */
function poblarSelect(selId, lista, { conservarValor = true } = {}) {
  const sel = $(selId);
  if (!sel) return;
  const previo = sel.value;
  const items = Array.isArray(lista) ? lista : [];
  if (!items.length) {
    sel.innerHTML = `<option value="">Sin datos (reintente)</option>`;
    sel.disabled = true;
    return;
  }
  sel.disabled = false;
  sel.innerHTML = items.map(item => {
    if (typeof item === "number") return `<option value="${item}">${item} pt</option>`;
    if (typeof item === "string") {
      const texto = /^\d+(\.\d+)?$/.test(item.trim()) ? `${item} pt` : item;
      return `<option value="${item}">${texto}</option>`;
    }
    const valor = item.valor ?? item.clave ?? item.id ?? "";
    const nombre = item.nombre ?? item.etiqueta ?? String(valor);
    return `<option value="${valor}">${nombre}</option>`;
  }).join("");
  if (conservarValor && previo && [...sel.options].some(o => o.value === previo)) {
    sel.value = previo;
  }
}

// Recolecta los datos de la portada premium desde el panel de la barra lateral PDF
function recolectarPortadaPremium() {
  const incluir = document.querySelector("#pdf-portada-incluir")?.checked;
  if (!incluir) return null;
  const fotos = [];
  const inputFotos = document.querySelector("#pdf-portada-fotos");
  if (inputFotos && inputFotos.files) {
    // Convertir a data URIs (base64) de forma síncrona usando FileReader
    // Se hace en el handler de exportación; aquí solo guardamos las rutas File
    // El backend acepta data URIs. Convertimos ahora:
    // (simplificado: guardamos los File objects para convertir en exportar)
  }
  return {
    incluir: true,
    tema: document.querySelector("#pdf-portada-tema")?.value || MFORegistro.ui("tema_portada"),
    datos: {
      tipo_documento: document.querySelector("#pdf-portada-tipo-doc")?.value || "",
      titulo_proyecto: document.querySelector("#pdf-portada-titulo")?.value || "",
      memoria_fase: document.querySelector("#pdf-portada-memoria")?.value || "",
      componente: document.querySelector("#pdf-portada-componente")?.value || "",
      consultor: document.querySelector("#pdf-portada-consultor")?.value || "",
      fecha: document.querySelector("#pdf-portada-fecha")?.value || "",
      codigo_proyecto: document.querySelector("#pdf-portada-codigo")?.value || "",
    },
    imagenes: [],  // se rellena de forma asíncrona antes del envío
  };
}

// Convierte los archivos seleccionados en data URIs (base64)
async function convertirFotosPortada() {
  const input = document.querySelector("#pdf-portada-fotos");
  if (!input || !input.files || input.files.length === 0) return [];
  const files = Array.from(input.files).slice(0, 6);
  const dataUris = [];
  for (const f of files) {
    const uri = await new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(r.result);
      r.onerror = reject;
      r.readAsDataURL(f);
    });
    dataUris.push(uri);
  }
  return dataUris;
}

async function inicializarBarrasLaterales() {
  if (!window.MFORegistro) return;
  try { await window.MFORegistro.cargar(); } catch (e) { console.error("Registro de opciones no disponible:", e); return; }
  cacheTemasWordDisco = window.MFORegistro.datos?.word?.temas_disco || {};
  aplicarTema(document.documentElement.getAttribute("data-tema") || MFORegistro.ui("tema_app"));
  if (!constructorColoresPaleta.length) {
    constructorColoresPaleta = [MFORegistro.ui("color_titulo_h1"), MFORegistro.ui("color_titulo_h2"), MFORegistro.ui("color_constructor_fondo")];
  }

  // 1. Poblar selects con datos del registro SSOT
  poblarSelect("#word-opt-tema", MFORegistro.TEMAS_WORD);
  poblarSelect("#word-opt-paleta-titulos", MFORegistro.PALETAS_TITULOS_WORD);
  poblarSelect("#word-opt-paleta-tablas", MFORegistro.PALETAS_TABLAS_WORD);
  poblarSelect("#word-opt-fuente", MFORegistro.FUENTES_WORD);
  poblarSelect("#word-opt-tamanio", MFORegistro.TAMANIOS_WORD);
  poblarSelect("#word-opt-interlineado", MFORegistro.INTERLINEADOS_WORD);
  poblarSelect("#word-opt-alineacion", MFORegistro.ALINEACIONES_WORD);
  poblarSelect("#word-opt-fuente-tabla", MFORegistro.FUENTES_TABLA_WORD);
  poblarSelect("#word-opt-tamanio-tabla", MFORegistro.TAMANIOS_TABLA_WORD);
  poblarSelect("#word-opt-alineacion-pie", MFORegistro.ALINEACIONES_PIE_WORD);
  poblarSelect("#word-opt-posicion-indice", MFORegistro.POSICIONES_INDICE_WORD);

  poblarSelect("#html-opt-tema", MFORegistro.TEMAS_HTML);
  poblarSelect("#html-opt-paleta", MFORegistro.PALETAS_HTML_TRICOLOR);
  poblarSelect("#html-opt-ancho", MFORegistro.ANCHOS_HTML);
  poblarSelect("#html-opt-fuente", MFORegistro.FUENTES_HTML);

  poblarSelect("#pdf-opt-paleta", MFORegistro.PALETAS_EDITORIAL_PDF);
  poblarSelect("#pdf-opt-estilo", MFORegistro.ESTILOS_MAQUETACION_PDF);
  poblarSelect("#pdf-opt-modo-diseno", MFORegistro.MODOS_COLUMNAS_PDF);
  poblarSelect("#pdf-opt-fuente", MFORegistro.FUENTES_PDF);
  poblarSelect("#pdf-opt-tamanio", MFORegistro.opciones("pdf", "tamanios"));
  poblarSelect("#pdf-opt-interlineado", MFORegistro.INTERLINEADOS_PDF);

  poblarSelect("#excel-opt-paleta", MFORegistro.PALETAS_EXCEL);
  poblarSelect("#excel-opt-ancho-col", MFORegistro.ANCHOS_COLUMNA_EXCEL);
  poblarSelect("#excel-opt-fuente-tam", MFORegistro.TAMANIOS_FUENTE_EXCEL);
  poblarSelect("#excel-opt-modo-hojas", MFORegistro.MODOS_HOJAS_EXCEL);

  // Poblar paletas personalizadas guardadas en los selects de Word, PDF, HTML y Excel
  poblarPaletasPersonalizadasEnSelects();

  // Sincronizar temas de Word reales desde templates/temas_word/
  cargarTemasWordDesdeDisco();

  // Sincronizar hojas de membrete desde storage/plantillas_word/
  cargarPlantillasWordDesdeDisco();

  // 2. Cargar valores persistidos del registro en controles de Word
  const opcWord = MFORegistro.obtenerOpciones("word");
  if ($("#word-opt-tema")) {
    const temaInicial = (opcWord.tema && opcWord.tema !== "defecto") ? opcWord.tema : MFORegistro.ui("tema_disco");
    $("#word-opt-tema").value = temaInicial;
  }
  if ($("#word-sel-modo-color-titulos")) $("#word-sel-modo-color-titulos").value = opcWord.modo_color_titulos || MFORegistro.defaults("word").modo_color_titulos;
  if ($("#word-opt-paleta-titulos")) $("#word-opt-paleta-titulos").value = opcWord.color_titulos || MFORegistro.defaults("word").color_titulos;
  if ($("#word-picker-tit-h1")) $("#word-picker-tit-h1").value = opcWord.color_tit_h1 || MFORegistro.defaults("word").color_tit_h1;
  if ($("#word-picker-tit-h2")) $("#word-picker-tit-h2").value = opcWord.color_tit_h2 || MFORegistro.defaults("word").color_tit_h2;

  if ($("#word-opt-paleta-suave-tablas")) $("#word-opt-paleta-suave-tablas").checked = opcWord.paleta_suave_tablas !== false;
  if ($("#word-opt-paleta-tablas")) $("#word-opt-paleta-tablas").value = opcWord.paleta_tablas || MFORegistro.defaults("word").paleta_tablas;
  if ($("#word-picker-tabla-cabecera")) $("#word-picker-tabla-cabecera").value = opcWord.color_tabla_cabecera || MFORegistro.defaults("word").color_tabla_cabecera;
  if ($("#word-picker-tabla-filas")) $("#word-picker-tabla-filas").value = opcWord.color_tabla_filas || MFORegistro.defaults("word").color_tabla_filas;
  if ($("#word-picker-tabla-borde")) $("#word-picker-tabla-borde").value = opcWord.color_tabla_borde || MFORegistro.defaults("word").color_tabla_borde;

  if ($("#word-opt-fuente")) $("#word-opt-fuente").value = opcWord.fuente || MFORegistro.defaults("word").fuente;
  if ($("#word-opt-tamanio")) $("#word-opt-tamanio").value = String(opcWord.tamano_pt || MFORegistro.defaults("word").tamano_pt);
  if ($("#word-opt-interlineado")) $("#word-opt-interlineado").value = String(opcWord.interlineado || MFORegistro.defaults("word").interlineado);
  if ($("#word-opt-alineacion")) $("#word-opt-alineacion").value = opcWord.alineacion || MFORegistro.defaults("word").alineacion;
  if ($("#word-opt-fuente-tabla")) $("#word-opt-fuente-tabla").value = opcWord.fuente_tabla || MFORegistro.defaults("word").fuente_tabla;
  if ($("#word-opt-tamanio-tabla")) $("#word-opt-tamanio-tabla").value = String(opcWord.tamanio_tabla || MFORegistro.defaults("word").tamanio_tabla);
  if ($("#word-opt-pie")) $("#word-opt-pie").value = opcWord.pie_pagina || MFORegistro.defaults("word").pie_pagina;
  if ($("#word-opt-alineacion-pie")) $("#word-opt-alineacion-pie").value = opcWord.alineacion_pie || MFORegistro.defaults("word").alineacion_pie;
  if ($("#word-opt-apa7")) $("#word-opt-apa7").checked = !!opcWord.normas_apa;
  if ($("#word-opt-num-eq")) $("#word-opt-num-eq").checked = !!opcWord.numerar_ecuaciones;
  if ($("#word-opt-toc")) $("#word-opt-toc").checked = !!opcWord.indice_toc;
  if ($("#word-opt-posicion-indice")) $("#word-opt-posicion-indice").value = opcWord.posicion_indice || MFORegistro.defaults("word").posicion_indice;
  if ($("#word-opt-num-pag")) $("#word-opt-num-pag").checked = opcWord.numerar_paginas !== false;
  if ($("#word-opt-hoja-membrete") && opcWord.plantilla_word) {
    $("#word-opt-hoja-membrete").value = opcWord.plantilla_word;
    consultarAnalisisMembrete(opcWord.plantilla_word);
  }

  actualizarVisibilidadTemaWord();
  conectarPickersVisualesWord();
  sincronizarPastillasWord();

  // 3. Cargar valores en HTML
  const opcHtml = MFORegistro.obtenerOpciones("html");
  if ($("#html-opt-tema")) $("#html-opt-tema").value = opcHtml.tema || MFORegistro.defaults("html").tema;
  if ($("#html-opt-paleta")) $("#html-opt-paleta").value = opcHtml.paleta_tricolor || MFORegistro.defaults("html").paleta_tricolor;
  if ($("#html-opt-ancho")) $("#html-opt-ancho").value = opcHtml.ancho_max || MFORegistro.defaults("html").ancho_max;
  if ($("#html-opt-fuente")) $("#html-opt-fuente").value = opcHtml.fuente || MFORegistro.defaults("html").fuente;
  if ($("#html-opt-justificado")) $("#html-opt-justificado").checked = opcHtml.justificado !== false;
  if ($("#html-opt-num-eq")) $("#html-opt-num-eq").checked = !!opcHtml.numerar_ecuaciones;
  if ($("#html-opt-footer-izq")) $("#html-opt-footer-izq").value = opcHtml.footer_izq || MFORegistro.defaults("html").footer_izq;
  if ($("#html-opt-footer-der")) $("#html-opt-footer-der").value = opcHtml.footer_der || MFORegistro.defaults("html").footer_der;

  // 4. Cargar valores en PDF
  const opcPdf = MFORegistro.obtenerOpciones("pdf");
  if ($("#pdf-opt-paleta")) $("#pdf-opt-paleta").value = opcPdf.paleta || MFORegistro.defaults("pdf").paleta;
  if ($("#pdf-opt-estilo")) $("#pdf-opt-estilo").value = opcPdf.estilo_maquetacion || MFORegistro.defaults("pdf").estilo_maquetacion;
  if ($("#pdf-opt-modo-diseno")) $("#pdf-opt-modo-diseno").value = opcPdf.modo_columnas || MFORegistro.defaults("pdf").modo_columnas;
  if ($("#pdf-opt-fuente")) $("#pdf-opt-fuente").value = opcPdf.fuente || MFORegistro.defaults("pdf").fuente;
  if ($("#pdf-opt-tamanio")) $("#pdf-opt-tamanio").value = String(opcPdf.tamanio ?? opcPdf.tamanio_pt ?? 11);
  if ($("#pdf-opt-interlineado")) $("#pdf-opt-interlineado").value = String(opcPdf.interlineado || MFORegistro.defaults("pdf").interlineado);
  if ($("#pdf-opt-justificado")) $("#pdf-opt-justificado").checked = opcPdf.justificado !== false;
  if ($("#pdf-opt-pie")) $("#pdf-opt-pie").value = opcPdf.pie_pagina || MFORegistro.defaults("pdf").pie_pagina;
  if ($("#pdf-opt-salto-cap")) $("#pdf-opt-salto-cap").checked = opcPdf.salto_capitulo !== false;
  if ($("#pdf-opt-running-header")) $("#pdf-opt-running-header").checked = opcPdf.running_header !== false;
  if ($("#pdf-opt-num-pag")) $("#pdf-opt-num-pag").checked = opcPdf.numerar_paginas !== false;
  if ($("#pdf-opt-toc")) $("#pdf-opt-toc").checked = opcPdf.indice_al_final !== false;
  if ($("#pdf-opt-hoja-membrete") && opcPdf.plantilla_word) {
    $("#pdf-opt-hoja-membrete").value = opcPdf.plantilla_word;
    consultarAnalisisMembretePdf(opcPdf.plantilla_word);
  }

  // 5. Cargar valores en Excel
  const opcExcel = MFORegistro.obtenerOpciones("excel");
  if ($("#excel-opt-paleta")) $("#excel-opt-paleta").value = opcExcel.paleta || MFORegistro.defaults("excel").paleta;
  if ($("#excel-opt-ancho-col")) $("#excel-opt-ancho-col").value = opcExcel.ancho_col || MFORegistro.defaults("excel").ancho_col;
  if ($("#excel-opt-fuente-tam")) $("#excel-opt-fuente-tam").value = String(opcExcel.fuente_tam || MFORegistro.defaults("excel").fuente_tam);
  if ($("#excel-opt-modo-hojas")) $("#excel-opt-modo-hojas").value = opcExcel.modo_hojas || MFORegistro.defaults("excel").modo_hojas;
  if ($("#excel-opt-gridlines")) $("#excel-opt-gridlines").checked = opcExcel.gridlines !== false;
  if ($("#excel-opt-autofit")) $("#excel-opt-autofit").checked = opcExcel.autofit !== false;

  // 6. Activar acordeón exclusivo y toggle para cada barra lateral (340 px)
  ["word", "html", "pdf", "excel"].forEach(formato => {
    configurarAcordeonExclusivo(formato);
    configurarToggleSidebar(formato);
  });

  // 7. Inicializar gestión de paletas personalizadas (localStorage)
  inicializarModalPaletasPersonalizadas();
}

function actualizarVisibilidadTemaWord() {
  const tema = $("#word-opt-tema")?.value || MFORegistro.defaults("word").tema;
  const esNativo = ["tema1", "tema2", "tema3"].includes(tema);
  const esPersonalizado = tema === "personalizado";

  const aviso = $("#aviso-tema-word-lateral");
  if (aviso) aviso.style.display = esNativo ? "block" : "none";

  const chkSuave = $("#word-opt-paleta-suave-tablas");
  const selPalTabla = $("#word-opt-paleta-tablas");
  const selModoTit = $("#word-sel-modo-color-titulos");

  if (chkSuave) chkSuave.disabled = esNativo;
  if (selPalTabla) selPalTabla.disabled = esNativo;
  if (selModoTit) selModoTit.disabled = esNativo;

  // Visibilidad títulos
  const contPalTitSelect = $("#contenedor-paleta-titulos-select");
  const contPickersTitCustom = $("#contenedor-pickers-titulos-custom");
  const modoTit = selModoTit?.value || MFORegistro.defaults("word").modo_color_titulos;

  if (esNativo) {
    if (contPalTitSelect) contPalTitSelect.style.display = "none";
    if (contPickersTitCustom) contPickersTitCustom.style.display = "none";
  } else {
    if (contPalTitSelect) contPalTitSelect.style.display = modoTit === "paleta" ? "block" : "none";
    if (contPickersTitCustom) contPickersTitCustom.style.display = modoTit === "personalizado" ? "block" : "none";
  }

  // Visibilidad cuadros y tablas
  const contSelectTablas = $("#contenedor-select-paleta-tablas");
  const contPickersTablas = $("#contenedor-pickers-tablas-custom");
  const suaveActiva = chkSuave ? chkSuave.checked : true;

  if (esNativo) {
    if (contSelectTablas) contSelectTablas.style.display = "block";
    if (contPickersTablas) contPickersTablas.style.display = "none";
  } else if (esPersonalizado) {
    if (contSelectTablas) contSelectTablas.style.display = suaveActiva ? "block" : "none";
    if (contPickersTablas) contPickersTablas.style.display = suaveActiva ? "none" : "block";
  } else {
    // defecto
    if (contSelectTablas) contSelectTablas.style.display = suaveActiva ? "block" : "none";
    if (contPickersTablas) contPickersTablas.style.display = suaveActiva ? "none" : "block";
  }
}

let pickersVisualesConectados = false;
function conectarPickersVisualesWord() {
  if (pickersVisualesConectados) return;
  pickersVisualesConectados = true;

  function enlazarVisual(idPicker, idMuestra, idCodigo) {
    const p = $(idPicker);
    const m = $(idMuestra);
    const c = $(idCodigo);
    if (!p) return;

    function sincronizarUI(colorVal) {
      if (m) m.style.backgroundColor = colorVal;
      if (c) c.textContent = colorVal.toUpperCase();
    }

    // Sincronizar valor inicial
    sincronizarUI(p.value);

    p.addEventListener("input", () => {
      sincronizarUI(p.value);
      guardarOpcionesWord();
    });

    p.addEventListener("change", () => {
      sincronizarUI(p.value);
      guardarOpcionesWord();
      renderizarHojaWordPreview();
    });
  }

  enlazarVisual("#word-picker-tit-h1", "#muestra-tit-h1", "#codigo-tit-h1");
  enlazarVisual("#word-picker-tit-h2", "#muestra-tit-h2", "#codigo-tit-h2");
  enlazarVisual("#word-picker-tabla-cabecera", "#muestra-tabla-cabecera", "#codigo-tabla-cabecera");
  enlazarVisual("#word-picker-tabla-filas", "#muestra-tabla-filas", "#codigo-tabla-filas");
  enlazarVisual("#word-picker-tabla-borde", "#muestra-tabla-borde", "#codigo-tabla-borde");
}

function sincronizarPastillasWord() {
  const mapa = [
    { p: "#word-picker-tit-h1", m: "#muestra-tit-h1", c: "#codigo-tit-h1" },
    { p: "#word-picker-tit-h2", m: "#muestra-tit-h2", c: "#codigo-tit-h2" },
    { p: "#word-picker-tabla-cabecera", m: "#muestra-tabla-cabecera", c: "#codigo-tabla-cabecera" },
    { p: "#word-picker-tabla-filas", m: "#muestra-tabla-filas", c: "#codigo-tabla-filas" },
    { p: "#word-picker-tabla-borde", m: "#muestra-tabla-borde", c: "#codigo-tabla-borde" }
  ];
  mapa.forEach(({ p, m, c }) => {
    const elP = $(p);
    const elM = $(m);
    const elC = $(c);
    if (elP && elM) elM.style.backgroundColor = elP.value;
    if (elP && elC) elC.textContent = elP.value.toUpperCase();
  });
}

function guardarOpcionesWord() {
  if (!window.MFORegistro) return;
  MFORegistro.guardarOpciones("word", {
    tema: $("#word-opt-tema")?.value,
    modo_color_titulos: $("#word-sel-modo-color-titulos")?.value,
    color_titulos: $("#word-opt-paleta-titulos")?.value,
    color_tit_h1: $("#word-picker-tit-h1")?.value,
    color_tit_h2: $("#word-picker-tit-h2")?.value,
    paleta_suave_tablas: $("#word-opt-paleta-suave-tablas")?.checked,
    paleta_tablas: $("#word-opt-paleta-tablas")?.value,
    color_tabla_cabecera: $("#word-picker-tabla-cabecera")?.value,
    color_tabla_filas: $("#word-picker-tabla-filas")?.value,
    color_tabla_borde: $("#word-picker-tabla-borde")?.value,
    fuente: $("#word-opt-fuente")?.value,
    tamano_pt: parseInt($("#word-opt-tamanio")?.value || MFORegistro.defaults("word").tamanio, 10),
    interlineado: parseFloat($("#word-opt-interlineado")?.value || MFORegistro.defaults("word").interlineado),
    alineacion: $("#word-opt-alineacion")?.value || MFORegistro.defaults("word").alineacion,
    fuente_tabla: $("#word-opt-fuente-tabla")?.value || MFORegistro.defaults("word").fuente_tabla,
    tamanio_tabla: $("#word-opt-tamanio-tabla")?.value || MFORegistro.defaults("word").tamanio_tabla,
    pie_pagina: $("#word-opt-pie")?.value,
    alineacion_pie: $("#word-opt-alineacion-pie")?.value || MFORegistro.defaults("word").alineacion_pie,
    normas_apa: $("#word-opt-apa7")?.checked,
    numerar_ecuaciones: $("#word-opt-num-eq")?.checked,
    indice_toc: $("#word-opt-toc")?.checked,
    posicion_indice: $("#word-opt-posicion-indice")?.value || MFORegistro.defaults("word").posicion_indice,
    numerar_paginas: $("#word-opt-num-pag")?.checked,
    plantilla_word: $("#word-opt-hoja-membrete")?.value || "",
  });
  actualizarVisibilidadTemaWord();
  sincronizarPastillasWord();
  debouncedWordPreview(() => renderizarHojaWordPreview());
}

/* ─────────────────── Acordeón Exclusivo y Barras Laterales (Fase 2) ─────────────────── */
function configurarAcordeonExclusivo(formato) {
  const sidebar = $(`#sidebar-${formato}-opciones`);
  if (!sidebar) return;

  const secciones = Array.from(sidebar.querySelectorAll("details.sidebar-seccion"));
  if (!secciones.length) return;

  const seccionAbiertaGuardada = sessionStorage.getItem(`mfo-sidebar-open-${formato}`);

  secciones.forEach((sec, idx) => {
    const secId = sec.dataset.seccionId || `sec-${idx}`;
    sec.dataset.seccionId = secId;

    // Todas cerradas por defecto al inicio a menos que esté en sessionStorage
    if (seccionAbiertaGuardada && seccionAbiertaGuardada === secId) {
      sec.open = true;
    } else {
      sec.open = false;
    }

    // Regla de oro: interacción interna NO debe cerrar la sección bajo ninguna circunstancia
    const contenido = sec.querySelector(".sidebar-seccion-contenido");
    if (contenido) {
      contenido.addEventListener("click", (e) => e.stopPropagation());
      contenido.addEventListener("change", (e) => e.stopPropagation());
      const controles = contenido.querySelectorAll("input, select, button, textarea, label");
      controles.forEach(ctrl => {
        ctrl.addEventListener("click", (e) => e.stopPropagation());
      });
    }

    const summary = sec.querySelector("summary");
    if (summary) {
      summary.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const yaAbierta = sec.open;

        // Acordeón exclusivo: cerrar cualquier otra sección abierta de este sidebar
        secciones.forEach(s => {
          if (s !== sec) s.open = false;
        });

        // Alternar estado de la sección clickeada
        sec.open = !yaAbierta;

        if (sec.open) {
          sessionStorage.setItem(`mfo-sidebar-open-${formato}`, secId);
        } else {
          sessionStorage.removeItem(`mfo-sidebar-open-${formato}`);
        }
      };
    }
  });
}

function configurarToggleSidebar(formato) {
  const btnToggle = $(`#btn-toggle-sidebar-${formato}`);
  const btnCerrar = $(`#btn-cerrar-sidebar-${formato}`);
  const sidebar = $(`#sidebar-${formato}-opciones`);
  if (!sidebar) return;

  function setSidebar(abrir) {
    if (abrir) {
      sidebar.classList.remove("colapsada");
    } else {
      sidebar.classList.add("colapsada");
    }
    try {
      sessionStorage.setItem(`mfo-sidebar-colapsada-${formato}`, abrir ? "0" : "1");
      localStorage.setItem(`mfo-sidebar-${formato}-abierta`, abrir ? "1" : "0");
    } catch (e) { }
  }

  // Estado recordado en sessionStorage por pestaña de sesión
  const sesionColapsada = sessionStorage.getItem(`mfo-sidebar-colapsada-${formato}`);
  const localAbierta = localStorage.getItem(`mfo-sidebar-${formato}-abierta`);

  if (sesionColapsada === "1" || (sesionColapsada === null && localAbierta === "0")) {
    sidebar.classList.add("colapsada");
  } else {
    sidebar.classList.remove("colapsada");
  }

  if (btnToggle) {
    btnToggle.onclick = (e) => {
      e.stopPropagation();
      const estaColapsada = sidebar.classList.contains("colapsada");
      setSidebar(estaColapsada);
    };
  }

  if (btnCerrar) {
    btnCerrar.onclick = (e) => {
      e.stopPropagation();
      setSidebar(false);
    };
  }
}

/* ─────────────────── Modal de Paletas Personalizadas (Fase 2) ─────────────────── */
let constructorColoresPaleta = [];

function inicializarModalPaletasPersonalizadas() {
  const modal = $("#modal-paletas-personalizadas");
  const btnCerrar = $("#btn-cerrar-modal-paletas");
  if (!modal) return;

  // Botones para abrir modal en cada sidebar
  const btnsAbrir = document.querySelectorAll(".btn-abrir-modal-paletas");
  btnsAbrir.forEach(btn => {
    btn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      abrirModalPaletas();
    };
  });

  if (btnCerrar) {
    btnCerrar.onclick = () => cerrarModalPaletas();
  }

  modal.onclick = (e) => {
    if (e.target === modal) cerrarModalPaletas();
  };

  // Botones agregar / quitar color en el constructor
  const btnAdd = $("#btn-paleta-agregar-color");
  const btnQuitar = $("#btn-paleta-quitar-color");
  const btnGuardar = $("#btn-guardar-nueva-paleta");

  if (btnAdd) {
    btnAdd.onclick = () => {
      if (constructorColoresPaleta.length >= 6) {
        alert("Una paleta personalizada puede tener como máximo 6 colores.");
        return;
      }
      constructorColoresPaleta.push("#10B981");
      renderizarConstructorColores();
    };
  }

  if (btnQuitar) {
    btnQuitar.onclick = () => {
      if (constructorColoresPaleta.length <= 2) {
        alert("Una paleta personalizada debe tener al menos 2 colores.");
        return;
      }
      constructorColoresPaleta.pop();
      renderizarConstructorColores();
    };
  }

  if (btnGuardar) {
    btnGuardar.onclick = () => {
      const inputNombre = $("#input-nombre-paleta-custom");
      const nombre = inputNombre ? inputNombre.value.trim() : "";
      if (!nombre) {
        alert("Por favor ingresa un nombre para la paleta.");
        inputNombre?.focus();
        return;
      }
      try {
        if (!window.MFORegistro || typeof window.MFORegistro.guardarPaletaPersonalizada !== "function") {
          const guardadas = JSON.parse(localStorage.getItem("mfo_paletas_personalizadas") || "[]");
          const nueva = {
            id: "pal_custom_" + Date.now().toString(36) + "_" + Math.random().toString(36).substring(2, 6),
            nombre: nombre.trim(),
            formato: "universal",
            colores: constructorColoresPaleta.map(c => String(c).trim()),
            fecha: new Date().toISOString()
          };
          guardadas.push(nueva);
          localStorage.setItem("mfo_paletas_personalizadas", JSON.stringify(guardadas));
        } else {
          MFORegistro.guardarPaletaPersonalizada(nombre, "universal", constructorColoresPaleta);
        }
        if (inputNombre) inputNombre.value = "";
        renderizarListaPaletasGuardadas();
        poblarPaletasPersonalizadasEnSelects();
        notificar($("#docs-estado"), `Paleta «${nombre}» guardada`, "ok");
      } catch (err) {
        alert(`Error: ${err.message}`);
      }
    };
  }

  function abrirModalPaletas() {
    modal.style.display = "flex";
    renderizarConstructorColores();
    renderizarListaPaletasGuardadas();
  }

  function cerrarModalPaletas() {
    modal.style.display = "none";
  }

  function renderizarConstructorColores() {
    const contenedor = $("#contenedor-colores-nueva-paleta");
    if (!contenedor) return;
    contenedor.innerHTML = "";

    constructorColoresPaleta.forEach((colHex, idx) => {
      const div = document.createElement("div");
      div.className = "pastilla-color-visual";
      div.title = `Color ${idx + 1}: Clic para cambiar`;
      div.style.minWidth = "95px";

      div.innerHTML = `
        <span class="muestra-color-circulo" style="background-color: ${colHex};"></span>
        <span class="muestra-color-codigo">${colHex.toUpperCase()}</span>
        <input type="color" class="input-color-nativo" value="${colHex}" aria-label="Color ${idx + 1}">
      `;

      const input = div.querySelector("input[type='color']");
      const circulo = div.querySelector(".muestra-color-circulo");
      const texto = div.querySelector(".muestra-color-codigo");

      input.oninput = () => {
        constructorColoresPaleta[idx] = input.value;
        circulo.style.backgroundColor = input.value;
        texto.textContent = input.value.toUpperCase();
      };

      contenedor.appendChild(div);
    });
  }

  function renderizarListaPaletasGuardadas() {
    const lista = $("#lista-paletas-guardadas");
    if (!lista) return;

    let paletas = [];
    try {
      paletas = window.MFORegistro?.obtenerPaletasPersonalizadas() || JSON.parse(localStorage.getItem("mfo_paletas_personalizadas") || "[]");
    } catch {
      paletas = [];
    }

    if (!paletas || paletas.length === 0) {
      lista.innerHTML = `<p style="font-size: 0.85rem; color: var(--text-muted); margin: 0;">No hay paletas guardadas aún en el almacenamiento local.</p>`;
      return;
    }

    lista.innerHTML = paletas.map(p => {
      const chipsHtml = (p.colores || []).map(c => `
        <span class="paleta-custom-chip-color" style="background-color: ${c};" title="${c}"></span>
      `).join("");

      return `
        <div class="tarjeta-paleta-custom" data-pal-id="${p.id}">
          <div style="display: flex; flex-direction: column; gap: 0.35rem; min-width: 0;">
            <strong style="font-size: 0.88rem; color: var(--text-heading); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(p.nombre)}</strong>
            <div class="paleta-custom-colores">
              ${chipsHtml}
            </div>
          </div>
          <div style="display: flex; gap: 0.35rem; flex-shrink: 0;">
            <button type="button" class="btn chico btn-primario btn-aplicar-paleta-custom" data-pal-id="${p.id}" title="Aplicar colores a toda la suite">Aplicar</button>
            <button type="button" class="btn chico btn-peligro btn-eliminar-paleta-custom" data-pal-id="${p.id}" title="Eliminar paleta">🗑️</button>
          </div>
        </div>
      `;
    }).join("");

    // Listeners para aplicar o eliminar
    lista.querySelectorAll(".btn-aplicar-paleta-custom").forEach(btn => {
      btn.onclick = () => {
        const id = btn.dataset.palId;
        const pal = paletas.find(x => x.id === id);
        if (!pal || !pal.colores || pal.colores.length < 2) return;

        const c1 = pal.colores[0];
        const c2 = pal.colores[1];
        const c3 = pal.colores[2] || pal.colores[1];
        const c4 = pal.colores[3] || MFORegistro.ui("color_relleno_4");
        const c5 = pal.colores[4] || MFORegistro.ui("color_relleno_5");
        const tricolorCadena = `${c1}|${c2}|${c3}`;

        // 1. Aplicar a Word
        if ($("#word-picker-tit-h1")) $("#word-picker-tit-h1").value = c1;
        if ($("#word-picker-tit-h2")) $("#word-picker-tit-h2").value = c2;
        if ($("#word-picker-tabla-cabecera")) $("#word-picker-tabla-cabecera").value = c1;
        if ($("#word-picker-tabla-filas")) $("#word-picker-tabla-filas").value = c3;
        if ($("#word-picker-tabla-borde")) $("#word-picker-tabla-borde").value = c5;

        if ($("#word-opt-tema")) $("#word-opt-tema").value = "personalizado";
        if ($("#word-sel-modo-color-titulos")) $("#word-sel-modo-color-titulos").value = "personalizado";
        if ($("#word-opt-paleta-suave-tablas")) $("#word-opt-paleta-suave-tablas").checked = false;

        guardarOpcionesWord();
        renderizarHojaWordPreview();

        // 2. Aplicar a PDF
        const selectPdf = $("#pdf-opt-paleta");
        if (selectPdf) {
          let optPdf = selectPdf.querySelector(`option[value="${tricolorCadena}"]`);
          if (!optPdf) {
            optPdf = document.createElement("option");
            optPdf.value = tricolorCadena;
            optPdf.textContent = `🎨 ${pal.nombre}`;
            selectPdf.appendChild(optPdf);
          }
          selectPdf.value = tricolorCadena;
        }
        if (window.MFORegistro) {
          const opcPdf = MFORegistro.obtenerOpciones("pdf");
          opcPdf.paleta = tricolorCadena;
          MFORegistro.guardarOpciones("pdf", opcPdf);
        }
        refrescarVisorPdfEnVivo();

        // 3. Aplicar a HTML
        const selectHtml = $("#html-opt-paleta");
        if (selectHtml) {
          let optHtml = selectHtml.querySelector(`option[value="${tricolorCadena}"]`);
          if (!optHtml) {
            optHtml = document.createElement("option");
            optHtml.value = tricolorCadena;
            optHtml.textContent = `🎨 ${pal.nombre}`;
            selectHtml.appendChild(optHtml);
          }
          selectHtml.value = tricolorCadena;
        }
        if (window.MFORegistro) {
          const opcHtml = MFORegistro.obtenerOpciones("html");
          opcHtml.paleta_tricolor = tricolorCadena;
          MFORegistro.guardarOpciones("html", opcHtml);
        }
        cargarVisorHtmlDedicado();
        // 4. Aplicar a Excel
        const selectExcel = $("#excel-opt-paleta");
        const paletaExcelCadena = `${c1}|${c2}|${c3}|${c4}|${c5}`;
        if (selectExcel) {
          let optExcel = selectExcel.querySelector(`option[value="${paletaExcelCadena}"]`);
          if (!optExcel) {
            optExcel = document.createElement("option");
            optExcel.value = paletaExcelCadena;
            optExcel.textContent = `🎨 ${pal.nombre}`;
            selectExcel.appendChild(optExcel);
          }
          selectExcel.value = paletaExcelCadena;
        }
        if (window.MFORegistro) {
          const opcExcel = MFORegistro.obtenerOpciones("excel");
          opcExcel.paleta = paletaExcelCadena;
          MFORegistro.guardarOpciones("excel", opcExcel);
        }

        cerrarModalPaletas();
        notificar($("#docs-estado"), `Paleta «${pal.nombre}» aplicada en toda la suite`, "ok");
      };
    });

    lista.querySelectorAll(".btn-eliminar-paleta-custom").forEach(btn => {
      btn.onclick = () => {
        const id = btn.dataset.palId;
        if (window.MFORegistro?.eliminarPaletaPersonalizada) {
          MFORegistro.eliminarPaletaPersonalizada(id);
        } else {
          const filtradas = paletas.filter(x => x.id !== id);
          localStorage.setItem("mfo_paletas_personalizadas", JSON.stringify(filtradas));
        }
        renderizarListaPaletasGuardadas();
        poblarPaletasPersonalizadasEnSelects();
      };
    });
  }
}

let cacheTemasWordDisco = {}; // se rellena desde el registro al inicializar (word.temas_disco)

async function consultarAnalisisMembrete(nombreArchivo) {
  const contZona = $("#contenedor-zona-membrete");
  if (!nombreArchivo) {
    if (contZona) contZona.style.display = "none";
    return;
  }
  if (contZona) contZona.style.display = "block";
  const badge = $("#badge-origen-zona");
  const estado = $("#estado-zona-membrete");
  const avisoBox = $("#aviso-membrete-geometria");
  const avisoTxt = $("#texto-aviso-membrete");

  if (estado) estado.textContent = "Analizando hoja de membrete…";

  try {
    const resp = await fetch(`/api/office/plantillas-word/${encodeURIComponent(nombreArchivo)}/analisis`);
    if (!resp.ok) {
      if (estado) estado.textContent = "No se pudo analizar la plantilla";
      return;
    }
    const json = await resp.json();
    const datos = json?.datos;
    if (!datos) return;

    const zona = datos.zona_sugerida_cm || {};
    if ($("#word-membrete-top")) $("#word-membrete-top").value = zona.top ?? 2.5;
    if ($("#word-membrete-bottom")) $("#word-membrete-bottom").value = zona.bottom ?? 2.0;
    if ($("#word-membrete-left")) $("#word-membrete-left").value = zona.left ?? 2.5;
    if ($("#word-membrete-right")) $("#word-membrete-right").value = zona.right ?? 2.5;

    if (badge) {
      if (datos.origen_zona === "archivo_zona") {
        badge.textContent = "💾 Personalizada";
        badge.title = "Márgenes cargados desde archivo .zona.json";
        badge.style.background = "rgba(16, 185, 129, 0.2)";
        badge.style.color = "#10b981";
      } else {
        badge.textContent = "📐 Analizada";
        badge.title = "Calculada automáticamente por análisis geométrico";
        badge.style.background = "rgba(59, 130, 246, 0.2)";
        badge.style.color = "#60a5fa";
      }
    }

    if (datos.advertencias && datos.advertencias.length > 0) {
      if (avisoBox) avisoBox.style.display = "block";
      if (avisoTxt) avisoTxt.textContent = datos.advertencias.join(" ");
    } else {
      if (avisoBox) avisoBox.style.display = "none";
    }

    if (estado) estado.textContent = "";
    debouncedWordPreview(() => renderizarHojaWordPreview());
  } catch (err) {
    console.warn("Error al analizar membrete:", err);
    if (estado) estado.textContent = "Error de conexión";
  }
}

async function guardarZonaMembreteActual() {
  const selHoja = $("#word-opt-hoja-membrete");
  const nombre = selHoja?.value;
  const estado = $("#estado-zona-membrete");
  const badge = $("#badge-origen-zona");

  if (!nombre) {
    if (estado) estado.textContent = "Seleccione una plantilla primero";
    return;
  }

  const payload = {
    top: parseFloat($("#word-membrete-top")?.value) || 2.5,
    bottom: parseFloat($("#word-membrete-bottom")?.value) || 2.0,
    left: parseFloat($("#word-membrete-left")?.value) || 2.5,
    right: parseFloat($("#word-membrete-right")?.value) || 2.5,
  };

  if (estado) estado.textContent = "Guardando zona…";

  try {
    const resp = await fetch(`/api/office/plantillas-word/${encodeURIComponent(nombre)}/zona`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      throw new Error(`Error HTTP ${resp.status}`);
    }
    const res = await resp.json();
    if (res?.ok) {
      if (estado) {
        estado.textContent = "✅ Zona guardada en disco (.zona.json)";
        setTimeout(() => { if (estado.textContent.includes("✅")) estado.textContent = ""; }, 3500);
      }
      if (badge) {
        badge.textContent = "💾 Personalizada";
        badge.title = "Márgenes cargados desde archivo .zona.json";
        badge.style.background = "rgba(16, 185, 129, 0.2)";
        badge.style.color = "#10b981";
      }
    }
  } catch (err) {
    console.error("Error al guardar zona:", err);
    if (estado) estado.textContent = "❌ Error al guardar";
  }
}

async function consultarAnalisisMembretePdf(nombreArchivo) {
  const contZona = $("#contenedor-zona-membrete-pdf");
  if (!nombreArchivo) {
    if (contZona) contZona.style.display = "none";
    return;
  }
  if (contZona) contZona.style.display = "block";
  const badge = $("#badge-origen-zona-pdf");

  try {
    const resp = await fetch(`/api/office/plantillas-word/${encodeURIComponent(nombreArchivo)}/analisis`);
    if (!resp.ok) return;
    const json = await resp.json();
    const datos = json?.datos;
    if (!datos) return;

    const zona = datos.zona_sugerida_cm || {};
    if ($("#pdf-membrete-top")) $("#pdf-membrete-top").value = zona.top ?? 2.5;
    if ($("#pdf-membrete-bottom")) $("#pdf-membrete-bottom").value = zona.bottom ?? 2.0;
    if ($("#pdf-membrete-left")) $("#pdf-membrete-left").value = zona.left ?? 2.5;
    if ($("#pdf-membrete-right")) $("#pdf-membrete-right").value = zona.right ?? 2.5;

    if (badge) {
      if (datos.origen_zona === "archivo_zona") {
        badge.textContent = "💾 Personalizada";
        badge.title = "Márgenes cargados desde archivo .zona.json";
        badge.style.background = "rgba(16, 185, 129, 0.2)";
        badge.style.color = "#10b981";
      } else {
        badge.textContent = "📐 Analizada";
        badge.title = "Calculada automáticamente por análisis geométrico";
        badge.style.background = "rgba(59, 130, 246, 0.2)";
        badge.style.color = "#60a5fa";
      }
    }
  } catch (err) {
    console.warn("Error al analizar membrete PDF:", err);
  }
}

async function cargarPlantillasWordDesdeDisco() {
  try {
    const resp = await fetch("/api/office/plantillas-word");
    if (!resp.ok) return;
    const json = await resp.json();
    const lista = json?.datos?.plantillas || [];

    // 1. Selector en Word
    const selHoja = $("#word-opt-hoja-membrete");
    if (selHoja) {
      const valActual = selHoja.value || "";
      let html = '<option value="">Sin plantilla (predeterminada)</option>';
      lista.forEach((p) => {
        html += `<option value="${escapeHtml(p.archivo)}">📄 ${escapeHtml(p.etiqueta)} (${escapeHtml(p.tamano)})</option>`;
      });
      selHoja.innerHTML = html;
      if (valActual && selHoja.querySelector(`option[value="${valActual}"]`)) {
        selHoja.value = valActual;
      } else {
        selHoja.value = "";
      }
      consultarAnalisisMembrete(selHoja.value);
    }

    // 2. Selector en PDF
    const selHojaPdf = $("#pdf-opt-hoja-membrete");
    if (selHojaPdf) {
      const valActualPdf = selHojaPdf.value || "";
      let htmlPdf = '<option value="">Sin plantilla (predeterminada)</option>';
      lista.forEach((p) => {
        htmlPdf += `<option value="${escapeHtml(p.archivo)}">📄 ${escapeHtml(p.etiqueta)} (${escapeHtml(p.tamano)})</option>`;
      });
      selHojaPdf.innerHTML = htmlPdf;
      if (valActualPdf && selHojaPdf.querySelector(`option[value="${valActualPdf}"]`)) {
        selHojaPdf.value = valActualPdf;
      } else {
        selHojaPdf.value = "";
      }
      consultarAnalisisMembretePdf(selHojaPdf.value);
    }
  } catch (err) {
    console.warn("Aviso al sincronizar plantillas de membrete:", err);
  }
}

async function cargarTemasWordDesdeDisco() {
  try {
    const resp = await fetch("/api/office/temas-word");
    if (!resp.ok) return;
    const json = await resp.json();
    const lista = json?.datos?.temas;
    if (!Array.isArray(lista) || lista.length === 0) return;

    const nuevoMapa = {};
    lista.forEach((t) => {
      if (t && t.id) nuevoMapa[t.id.toLowerCase()] = t;
    });
    cacheTemasWordDisco = { ...cacheTemasWordDisco, ...nuevoMapa };

    const selTema = $("#word-opt-tema");
    if (selTema) {
      const valActual = selTema.value || MFORegistro.ui("tema_disco");
      selTema.innerHTML = lista.map((t) => `<option value="${t.id}">${escapeHtml(t.nombre)}</option>`).join("") +
        `<option value="personalizado">🎨 Tema Personalizado (Habilita paleta y colores)</option>`;
      if (selTema.querySelector(`option[value="${valActual}"]`)) {
        selTema.value = valActual;
      } else {
        selTema.value = lista[0].id;
      }
      actualizarVisibilidadTemaWord();
      renderizarHojaWordPreview();
    }
  } catch (err) {
    console.warn("Aviso al sincronizar temas de Word desde disco:", err);
  }
}

function poblarPaletasPersonalizadasEnSelects() {
  let paletas = [];
  try {
    paletas = window.MFORegistro?.obtenerPaletasPersonalizadas() || JSON.parse(localStorage.getItem("mfo_paletas_personalizadas") || "[]");
  } catch {
    paletas = [];
  }
  if (!Array.isArray(paletas)) return;

  // Agregar a selects de Word (Paleta de Títulos y Paleta de Tablas)
  const selWordTit = $("#word-opt-paleta-titulos");
  if (selWordTit) {
    paletas.forEach(pal => {
      if (!pal.colores || pal.colores.length < 2) return;
      const val = `${pal.colores[0]}|${pal.colores[1]}|${pal.colores[2] || pal.colores[1]}`;
      if (!selWordTit.querySelector(`option[value="${val}"]`)) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = `🎨 ${pal.nombre}`;
        selWordTit.appendChild(opt);
      }
    });
  }

  const selWordTab = $("#word-opt-paleta-tablas");
  if (selWordTab) {
    paletas.forEach(pal => {
      if (!pal.colores || pal.colores.length < 2) return;
      const c1 = pal.colores[0];
      const c2 = pal.colores[1];
      const c3 = pal.colores[2] || pal.colores[1];
      const c4 = pal.colores[3] || MFORegistro.ui("color_relleno_4");
      const c5 = pal.colores[4] || MFORegistro.ui("color_relleno_5");
      const val = `${c1}|${c2}|${c3}|${c4}|${c5}`;
      if (!selWordTab.querySelector(`option[value="${val}"]`)) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = `🎨 ${pal.nombre}`;
        selWordTab.appendChild(opt);
      }
    });
  }

  // Agregar a select de PDF
  const selPdf = $("#pdf-opt-paleta");
  if (selPdf) {
    paletas.forEach(pal => {
      if (!pal.colores || pal.colores.length < 2) return;
      const val = `${pal.colores[0]}|${pal.colores[1]}|${pal.colores[2] || pal.colores[1]}`;
      if (!selPdf.querySelector(`option[value="${val}"]`)) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = `🎨 ${pal.nombre}`;
        selPdf.appendChild(opt);
      }
    });
  }

  // Agregar a select de HTML
  const selHtml = $("#html-opt-paleta");
  if (selHtml) {
    paletas.forEach(pal => {
      if (!pal.colores || pal.colores.length < 2) return;
      const val = `${pal.colores[0]}|${pal.colores[1]}|${pal.colores[2] || pal.colores[1]}`;
      if (!selHtml.querySelector(`option[value="${val}"]`)) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = `🎨 ${pal.nombre}`;
        selHtml.appendChild(opt);
      }
    });
  }

  // Agregar a select de Excel
  const selExcel = $("#excel-opt-paleta");
  if (selExcel) {
    paletas.forEach(pal => {
      if (!pal.colores || pal.colores.length < 2) return;
      const c1 = pal.colores[0];
      const c2 = pal.colores[1];
      const c3 = pal.colores[2] || pal.colores[1];
      const c4 = pal.colores[3] || MFORegistro.ui("color_relleno_4");
      const c5 = pal.colores[4] || MFORegistro.ui("color_relleno_5");
      const val = `${c1}|${c2}|${c3}|${c4}|${c5}`;
      if (!selExcel.querySelector(`option[value="${val}"]`)) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = `🎨 ${pal.nombre}`;
        selExcel.appendChild(opt);
      }
    });
  }
}

/* Guardado reactivo con debounce de 300 ms */
let timerDebounceOpciones = null;
function debouncedAction(fn, delay = 300) {
  clearTimeout(timerDebounceOpciones);
  timerDebounceOpciones = setTimeout(fn, delay);
}

/* Debounce dedicado para la previsualización en vivo de Word (evita cancelación cruzada) */
let timerWordPreview = null;
function debouncedWordPreview(fn, delay = 300) {
  clearTimeout(timerWordPreview);
  timerWordPreview = setTimeout(fn, delay);
}

function registrarListenersReactivos() {
  // Listeners Word
  const inputsWord = [
    "#word-opt-tema", "#word-sel-modo-color-titulos", "#word-opt-paleta-titulos",
    "#word-opt-paleta-suave-tablas", "#word-opt-paleta-tablas",
    "#word-opt-fuente", "#word-opt-tamanio", "#word-opt-interlineado", "#word-opt-alineacion",
    "#word-opt-fuente-tabla", "#word-opt-tamanio-tabla",
    "#word-opt-pie", "#word-opt-alineacion-pie", "#word-opt-apa7", "#word-opt-num-eq", "#word-opt-toc",
    "#word-opt-posicion-indice", "#word-opt-num-pag"
  ];
  inputsWord.forEach(sel => {
    $(sel)?.addEventListener("change", () => {
      try {
        guardarOpcionesWord();
        renderizarHojaWordPreview().catch((e) => console.error("Error renderizando Word:", e));
        notificar($("#word-estado"), "Vista Word actualizada", "ok");
      } catch (e) {
        console.error("Error en cambio de opción Word:", e);
        notificar($("#word-estado"), "Error al actualizar vista Word", "error");
      }
    });
  });

  // Actualización en vivo mientras se escribe en campos de texto de Word
  ["#word-opt-pie"].forEach(sel => {
    $(sel)?.addEventListener("input", () => {
      guardarOpcionesWord();
      debouncedWordPreview(() => renderizarHojaWordPreview());
    });
  });

  $("#word-opt-hoja-membrete")?.addEventListener("change", (e) => {
    consultarAnalisisMembrete(e.target.value);
    if (window.MFORegistro) {
      MFORegistro.guardarOpciones("word", { plantilla_word: e.target.value });
    }
    debouncedWordPreview(() => renderizarHojaWordPreview());
  });

  $("#btn-guardar-zona-membrete")?.addEventListener("click", () => {
    guardarZonaMembreteActual();
  });

  ["#word-membrete-top", "#word-membrete-bottom", "#word-membrete-left", "#word-membrete-right"].forEach(sel => {
    $(sel)?.addEventListener("input", () => {
      debouncedWordPreview(() => renderizarHojaWordPreview());
    });
  });

  $("#btn-refrescar-plantillas-word")?.addEventListener("click", async () => {
    await cargarPlantillasWordDesdeDisco();
    notificar($("#word-estado"), "Lista de hojas de membrete actualizada", "ok");
  });

  $("#pdf-opt-hoja-membrete")?.addEventListener("change", (e) => {
    consultarAnalisisMembretePdf(e.target.value);
    if (window.MFORegistro) {
      MFORegistro.guardarOpciones("pdf", { plantilla_word: e.target.value });
    }
    debouncedAction(() => refrescarVisorPdfEnVivo());
  });

  ["#pdf-membrete-top", "#pdf-membrete-bottom", "#pdf-membrete-left", "#pdf-membrete-right"].forEach(sel => {
    $(sel)?.addEventListener("input", () => {
      debouncedAction(() => refrescarVisorPdfEnVivo());
    });
  });

  $("#btn-refrescar-plantillas-pdf")?.addEventListener("click", async () => {
    await cargarPlantillasWordDesdeDisco();
    notificar($("#pdf-estado"), "Lista de hojas de membrete actualizada", "ok");
  });

  $("#btn-reset-word-sidebar")?.addEventListener("click", () => {
    if (!window.MFORegistro) return;
    MFORegistro.restablecerOpciones("word");
    inicializarBarrasLaterales();
    renderizarHojaWordPreview();
    notificar($("#docs-estado"), "Opciones de Word restablecidas", "ok");
  });

  // Listeners HTML
  function guardarOpcionesHtml() {
    if (!window.MFORegistro) return;
    MFORegistro.guardarOpciones("html", {
      tema: $("#html-opt-tema")?.value,
      paleta_tricolor: $("#html-opt-paleta")?.value,
      ancho_max: $("#html-opt-ancho")?.value,
      fuente: $("#html-opt-fuente")?.value,
      justificado: $("#html-opt-justificado")?.checked,
      numerar_ecuaciones: $("#html-opt-num-eq")?.checked,
      footer_izq: $("#html-opt-footer-izq")?.value,
      footer_der: $("#html-opt-footer-der")?.value,
    });
    debouncedAction(() => cargarVisorHtmlDedicado());
  }

  const inputsHtml = [
    "#html-opt-tema", "#html-opt-paleta", "#html-opt-ancho",
    "#html-opt-fuente", "#html-opt-justificado", "#html-opt-num-eq",
    "#html-opt-footer-izq", "#html-opt-footer-der"
  ];
  inputsHtml.forEach(sel => {
    $(sel)?.addEventListener("change", () => guardarOpcionesHtml());
  });
  ["#html-opt-footer-izq", "#html-opt-footer-der"].forEach(sel => {
    $(sel)?.addEventListener("input", () => guardarOpcionesHtml());
  });

  $("#btn-reset-html-sidebar")?.addEventListener("click", () => {
    if (!window.MFORegistro) return;
    MFORegistro.restablecerOpciones("html");
    inicializarBarrasLaterales();
    cargarVisorHtmlDedicado();
    notificar($("#docs-estado"), "Opciones de HTML restablecidas", "ok");
  });

  // Listeners PDF
  const inputsPdf = [
    "#pdf-opt-paleta", "#pdf-opt-estilo", "#pdf-opt-modo-diseno",
    "#pdf-opt-fuente", "#pdf-opt-tamanio", "#pdf-opt-interlineado", "#pdf-opt-pie",
    "#pdf-opt-salto-cap", "#pdf-opt-running-header", "#pdf-opt-num-pag", "#pdf-opt-toc",
    "#pdf-opt-justificado",
    "#pdf-portada-incluir", "#pdf-portada-tema", "#pdf-portada-tipo-doc",
    "#pdf-portada-titulo", "#pdf-portada-memoria", "#pdf-portada-componente",
    "#pdf-portada-consultor", "#pdf-portada-fecha", "#pdf-portada-codigo",
    "#pdf-portada-fotos"
  ];
  inputsPdf.forEach(sel => {
    const alCambiar = () => {
      if (!window.MFORegistro) return;
      MFORegistro.guardarOpciones("pdf", {
        paleta: $("#pdf-opt-paleta")?.value,
        estilo_maquetacion: $("#pdf-opt-estilo")?.value,
        modo_columnas: $("#pdf-opt-modo-diseno")?.value,
        fuente: $("#pdf-opt-fuente")?.value,
        tamanio_pt: parseFloat($("#pdf-opt-tamanio")?.value || MFORegistro.defaults("pdf").tamanio),
        justificado: $("#pdf-opt-justificado")?.checked ?? true,
        interlineado: parseFloat($("#pdf-opt-interlineado")?.value || MFORegistro.defaults("pdf").interlineado),
        pie_pagina: $("#pdf-opt-pie")?.value,
        salto_capitulo: $("#pdf-opt-salto-cap")?.checked,
        running_header: $("#pdf-opt-running-header")?.checked,
        numerar_paginas: $("#pdf-opt-num-pag")?.checked,
        indice_al_final: $("#pdf-opt-toc")?.checked,
      });
      // Fase 3: refrescarVisorPdfEnVivo aplica un único debounce de ~300 ms
      refrescarVisorPdfEnVivo();
    };
    $(sel)?.addEventListener("change", alCambiar);
    // Campos de texto (pie de página): actualización mientras se escribe
    if ($(sel)?.tagName === "INPUT" && $(sel).type === "text") {
      $(sel).addEventListener("input", alCambiar);
    }
  });

  $("#btn-reset-pdf-sidebar")?.addEventListener("click", () => {
    if (!window.MFORegistro) return;
    MFORegistro.restablecerOpciones("pdf");
    inicializarBarrasLaterales();
    refrescarVisorPdfEnVivo();
    notificar($("#docs-estado"), "Opciones de PDF restablecidas", "ok");
  });

  // Listeners Excel
  const inputsExcel = [
    "#excel-opt-paleta", "#excel-opt-ancho-col", "#excel-opt-fuente-tam",
    "#excel-opt-modo-hojas", "#excel-opt-gridlines", "#excel-opt-autofit"
  ];
  inputsExcel.forEach(sel => {
    $(sel)?.addEventListener("change", () => {
      if (!window.MFORegistro) return;
      MFORegistro.guardarOpciones("excel", {
        paleta: $("#excel-opt-paleta")?.value,
        ancho_col: $("#excel-opt-ancho-col")?.value,
        fuente_tam: parseInt($("#excel-opt-fuente-tam")?.value || MFORegistro.defaults("excel").fuente_tam, 10),
        modo_hojas: $("#excel-opt-modo-hojas")?.value,
        gridlines: $("#excel-opt-gridlines")?.checked,
        autofit: $("#excel-opt-autofit")?.checked,
      });
      debouncedAction(() => {
        if (tablasDetectadas.length > 0) {
          renderizarCuadriculaExcel(tablasDetectadas[tablaActivaIndice]);
        }
      });
    });
  });

  $("#btn-reset-excel-sidebar")?.addEventListener("click", () => {
    if (!window.MFORegistro) return;
    MFORegistro.restablecerOpciones("excel");
    inicializarBarrasLaterales();
    if (tablasDetectadas.length > 0) {
      renderizarCuadriculaExcel(tablasDetectadas[tablaActivaIndice]);
    }
    notificar($("#docs-estado"), "Opciones de Excel restablecidas", "ok");
  });
}

/* ══════════════ 3. APP: WORD (.DOCX) — VISOR Y EXPORTACIÓN ══════════════ */
async function sincronizarAuditoriaWord() {
  const md = await obtenerMarkdownActual();
  const palabras = (md.match(/\S+/g) || []).length;
  const chipResumen = $("#word-stats-resumen");
  if (chipResumen) chipResumen.textContent = `${palabras} palabras`;
}

async function renderizarHojaWordPreview() {
  const contenedorPaginas = $("#hoja-word-contenedor-paginas");
  if (!contenedorPaginas) return;

  const md = await obtenerMarkdownActual();
  const nombreDoc = $("#titulo-documento").value.trim() || MFORegistro.ui("nombre_documento");

  if (!md.trim()) {
    contenedorPaginas.innerHTML = `
      <article class="hoja-word-pagina" style="display:flex; flex-direction:column; align-items:center; justify-content:center; color:var(--text-muted);">
        <div style="font-size:2.5rem; margin-bottom:0.75rem;">📄</div>
        <h3 style="margin:0 0 0.5rem 0;">Documento activo en blanco</h3>
        <p style="margin:0;">Escribe o carga un documento en Docs para previsualizar aquí su maquetación Word A4.</p>
      </article>
    `;
    const paginacionEl = $("#word-hoja-paginacion");
    if (paginacionEl) paginacionEl.textContent = "0 páginas";
    return;
  }

  const opc = window.MFORegistro ? MFORegistro.obtenerOpciones("word") : {};
  const temaWord = $("#word-opt-tema")?.value || opc.tema || MFORegistro.defaults("word").tema;
  const fuenteWord = $("#word-opt-fuente")?.value || opc.fuente || MFORegistro.defaults("word").fuente;
  const tamanoPt = parseFloat($("#word-opt-tamanio")?.value || opc.tamano_pt || MFORegistro.defaults("word").tamano_pt);
  const interlineado = parseFloat($("#word-opt-interlineado")?.value || opc.interlineado || MFORegistro.defaults("word").interlineado);
  const alineacion = $("#word-opt-alineacion")?.value || opc.alineacion || MFORegistro.defaults("word").alineacion;
  const pieTexto = $("#word-opt-pie")?.value || opc.pie_pagina || MFORegistro.defaults("word").pie_pagina;
  const alineacionPie = $("#word-opt-alineacion-pie")?.value || opc.alineacion_pie || MFORegistro.defaults("word").alineacion_pie;
  const normasApa = $("#word-opt-apa7")?.checked ?? !!opc.normas_apa;
  const numerarEcuaciones = $("#word-opt-num-eq")?.checked ?? !!opc.numerar_ecuaciones;
  const crearIndice = $("#word-opt-toc")?.checked ?? !!opc.indice_toc;
  const posicionIndice = $("#word-opt-posicion-indice")?.value || opc.posicion_indice || MFORegistro.defaults("word").posicion_indice;
  const numerarPaginas = $("#word-opt-num-pag")?.checked ?? (opc.numerar_paginas !== false);
  const fuenteTabla = $("#word-opt-fuente-tabla")?.value || opc.fuente_tabla || MFORegistro.defaults("word").fuente_tabla;
  const tamanioTabla = $("#word-opt-tamanio-tabla")?.value || opc.tamanio_tabla || MFORegistro.defaults("word").tamanio_tabla;

  // Validar existencia del tema cuando no es personalizado ni defecto
  const temaClean = (temaWord || "").toLowerCase();
  const infoTemaDisco = cacheTemasWordDisco[temaClean] || null;
  if (temaClean && !["defecto", "personalizado"].includes(temaClean) && !infoTemaDisco) {
    const estadoWordEl = $("#word-estado");
    if (estadoWordEl) {
      estadoWordEl.textContent = `⚠ Tema "${temaWord}" no encontrado en templates/temas_word`;
    }
  }

  // 1. Cálculo del color y tamaño de títulos fiel a templates/temas_word/*.docx y motor/a_docx.py
  let hexH1 = MFORegistro.ui("color_h1_defecto");
  let hexH2H3 = MFORegistro.ui("color_h1_defecto");
  let h1Pt = 15.0;
  let h2Pt = 14.0;
  let h3Pt = 12.0;
  const modoTit = $("#word-sel-modo-color-titulos")?.value || opc.modo_color_titulos || MFORegistro.defaults("word").modo_color_titulos;

  if (infoTemaDisco) {
    hexH1 = infoTemaDisco.h1_color || MFORegistro.ui("color_h1_defecto");
    hexH2H3 = infoTemaDisco.h2_color || infoTemaDisco.h1_color || MFORegistro.ui("color_h1_defecto");
    h1Pt = infoTemaDisco.h1_pt || MFORegistro.ui("tamanio_h1_pt");
    h2Pt = infoTemaDisco.h2_pt || MFORegistro.ui("tamanio_h2_pt");
    h3Pt = infoTemaDisco.h3_pt || MFORegistro.ui("tamanio_h3_pt");
  } else {
    if (modoTit === "personalizado") {
      hexH1 = $("#word-picker-tit-h1")?.value || opc.color_tit_h1 || MFORegistro.defaults("word").color_tit_h1;
      hexH2H3 = $("#word-picker-tit-h2")?.value || opc.color_tit_h2 || MFORegistro.defaults("word").color_tit_h2;
    } else if (modoTit === "paleta") {
      const palTit = $("#word-opt-paleta-titulos")?.value || opc.color_titulos || MFORegistro.defaults("word").color_titulos;
      const paletaTit = MFORegistro.opciones("word", "paletas_titulos").find(p => p.valor === palTit);
      if (paletaTit && Array.isArray(paletaTit.colores) && paletaTit.colores.length >= 2) {
        hexH1 = paletaTit.colores[0];
        hexH2H3 = paletaTit.colores[1];
      } else if (palTit.includes("|")) {
        const partes = palTit.split("|").map(s => s.trim());
        hexH1 = partes[0] || MFORegistro.ui("color_titulo_h1");
        hexH2H3 = partes[1] || hexH1;
      }
    } else {
      hexH1 = MFORegistro.ui("color_negro_h1");
      hexH2H3 = MFORegistro.ui("color_negro_h2");
    }
  }

  // 2. Cálculo de paleta y estilos de tablas/cuadros fiel a motor/a_docx.py
  const paletasTablaRegistro = Object.fromEntries(
    MFORegistro.opciones("word", "paletas_tablas").map(p => [p.valor, { cabecera: p.cabecera, par: p.par, borde: p.borde }])
  );

  const paletaSuaveActiva = $("#word-opt-paleta-suave-tablas")?.checked ?? (opc.paleta_suave_tablas !== false);
  const clavePaleta = $("#word-opt-paleta-tablas")?.value || opc.paleta_tablas || MFORegistro.defaults("word").paleta_tablas;

  let cabeceraBg = MFORegistro.ui("color_cabecera_defecto");
  let filaParBg = MFORegistro.ui("color_fila_par_defecto");
  let bordeTabla = MFORegistro.ui("color_borde_defecto");
  let cabeceraTxt = MFORegistro.ui("color_texto_oscuro");
  let estiloBordesTabla = "completo";

  function calcularTextoContraste(hexColor) {
    const hexNum = (hexColor || "").replace("#", "").trim();
    if (hexNum.length === 6) {
      const r = parseInt(hexNum.substring(0, 2), 16);
      const g = parseInt(hexNum.substring(2, 4), 16);
      const b = parseInt(hexNum.substring(4, 6), 16);
      return (r * 0.299 + g * 0.587 + b * 0.114 < 145) ? MFORegistro.ui("color_texto_claro") : MFORegistro.ui("color_texto_oscuro");
    }
    return MFORegistro.ui("color_texto_oscuro");
  }

  if (infoTemaDisco && infoTemaDisco.tabla) {
    cabeceraBg = infoTemaDisco.tabla.cabecera_bg;
    cabeceraTxt = infoTemaDisco.tabla.cabecera_txt || calcularTextoContraste(cabeceraBg);
    filaParBg = infoTemaDisco.tabla.fila_par_bg;
    bordeTabla = infoTemaDisco.tabla.borde;
    estiloBordesTabla = infoTemaDisco.tabla.estilo_bordes || MFORegistro.ui("estilo_bordes");
  } else if (!paletaSuaveActiva) {
    cabeceraBg = $("#word-picker-tabla-cabecera")?.value || opc.color_tabla_cabecera || MFORegistro.defaults("word").color_tabla_cabecera;
    filaParBg = $("#word-picker-tabla-filas")?.value || opc.color_tabla_filas || MFORegistro.defaults("word").color_tabla_filas;
    bordeTabla = $("#word-picker-tabla-borde")?.value || opc.color_tabla_borde || MFORegistro.defaults("word").color_tabla_borde;
    cabeceraTxt = calcularTextoContraste(cabeceraBg);
  } else if (clavePaleta.includes("|")) {
    const partesT = clavePaleta.split("|").map(s => s.trim());
    cabeceraBg = partesT[0] || MFORegistro.ui("color_titulo_h1");
    filaParBg = partesT[2] || partesT[1] || MFORegistro.ui("color_fila_par");
    bordeTabla = partesT[4] || MFORegistro.ui("color_borde");
    cabeceraTxt = calcularTextoContraste(cabeceraBg);
  } else if (paletasTablaRegistro[clavePaleta]) {
    const p = paletasTablaRegistro[clavePaleta];
    cabeceraBg = p.cabecera;
    filaParBg = p.par;
    bordeTabla = p.borde;
    cabeceraTxt = calcularTextoContraste(p.cabecera);
  }

  const cssFuenteTabla = (fuenteTabla && fuenteTabla !== "heredar") ? `'${fuenteTabla}', Calibri, sans-serif` : "inherit";
  const cssTamanoTabla = (tamanioTabla && tamanioTabla !== "auto") ? `${tamanioTabla}pt` : "0.92em";

  try {
    const resp = await fetch("/api/render-preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto: md, markdown: md, titulo: nombreDoc, tema_html: MFORegistro.ui("tema_html_preview") }),
    });
    const res = await resp.json();
    if (res.ok && res.datos && res.datos.html) {
      const parser = new DOMParser();
      const docHtml = parser.parseFromString(res.datos.html, "text/html");
      const contenido = docHtml.querySelector(".contenido-principal") || docHtml.querySelector("article") || docHtml.body;

      // Numerar ecuaciones si está activado
      if (numerarEcuaciones) {
        const eqBlocks = contenido.querySelectorAll(".mformula.display, .katex-display, pre.katex, .eq-bloque");
        eqBlocks.forEach((eq, i) => {
          const numSpan = document.createElement("span");
          numSpan.className = "eq-numero-word";
          numSpan.textContent = `(${i + 1})`;
          eq.appendChild(numSpan);
        });
      }

      // Generar bloque de Índice (TOC) si está activado
      let bloqueTocHtml = "";
      if (crearIndice) {
        const titulos = Array.from(contenido.querySelectorAll("h1, h2, h3"));
        if (titulos.length > 0) {
          const itemsToc = titulos.map((t, idx) => {
            const nivel = parseInt(t.tagName.substring(1), 10);
            const sangria = (nivel - 1) * 1.2;
            const texto = t.textContent.trim();
            const id = t.id || `toc-head-${idx}`;
            t.id = id;
            return `
              <li style="margin-left:${sangria}rem; margin-bottom:0.35rem; display:flex; align-items:baseline; justify-content:space-between; gap:0.5rem;">
                <a href="#${id}" style="color:${nivel === 1 ? hexH1 : hexH2H3}; text-decoration:none; font-weight:${nivel === 1 ? '700' : '400'};">${escapeHtml(texto)}</a>
                <span style="flex:1; border-bottom:1px dotted #94a3b8; margin:0 0.4rem; height:0.9em;"></span>
                <span style="color:#64748b; font-size:0.88em; font-weight:600;">${Math.min(idx + 1, 12)}</span>
              </li>`;
          }).join("\n");

          bloqueTocHtml = `
            <div class="hoja-word-toc-bloque" style="margin-bottom:2rem; padding:1.2rem 1.4rem; background:rgba(241,245,249,0.5); border-radius:6px; border:1px solid #cbd5e1;">
              <h2 style="color:${hexH1}; font-size:1.15rem; margin-top:0; margin-bottom:0.8rem; text-transform:uppercase; border-bottom:2px solid ${hexH1}; padding-bottom:0.4rem;">ÍNDICE GENERAL</h2>
              <ul style="list-style:none; padding-left:0; margin:0;">
                ${itemsToc}
              </ul>
            </div>`;
        }
      }

      // 1. Filtrado de elementos y saneamiento de nodos vacíos
      function tieneContenidoReal(htmlStr) {
        if (!htmlStr) return false;
        const sinHtml = htmlStr.replace(/<[^>]+>/g, "").trim();
        if (sinHtml.length > 0) return true;
        return /<(img|svg|table|canvas|iframe|hr)/i.test(htmlStr);
      }

      const esElementoVisible = (el) => {
        if (!el || !el.tagName) return false;
        const tag = el.tagName.toLowerCase();
        if (tag === "p") {
          const txt = (el.textContent || "").trim();
          const tieneMedios = !!el.querySelector("img, svg, canvas, iframe, video, .mformula, .katex, code");
          return txt.length > 0 || tieneMedios;
        }
        return true;
      };

      const elementosCrudos = Array.from(contenido ? contenido.children : []).filter(esElementoVisible);

      // 2. Medición real en DOM (Two-Pass Measurement) en caja A4 útil de 602px
      const divMedicion = document.createElement("div");
      divMedicion.className = "hoja-word-medicion-sandbox";
      divMedicion.style.cssText = `
        position: absolute;
        left: -99999px;
        top: 0;
        width: 602px; /* Ancho útil A4: 794px - 2 * 96px (2.54 cm) */
        visibility: hidden;
        pointer-events: none;
        font-family: '${fuenteWord}', Calibri, sans-serif;
        font-size: ${tamanoPt}pt;
        line-height: ${normasApa ? 2.0 : interlineado};
        box-sizing: border-box;
        padding: 0;
        margin: 0;
      `;
      document.body.appendChild(divMedicion);

      function calcularAlturaRespaldo(el) {
        if (!el || !el.tagName) return 30;
        const tag = el.tagName.toLowerCase();
        const factorInter = normasApa ? 2.0 : interlineado;
        const hLinea = Math.round(tamanoPt * 1.33 * factorInter);
        if (tag === "h1") return 80;
        if (tag === "h2") return 55;
        if (tag === "h3") return 45;
        if (tag === "table") {
          const filas = el.querySelectorAll("tr").length || 3;
          return Math.max(120, filas * 36);
        }
        if (tag === "pre" || el.classList?.contains("mermaid") || el.querySelector(".mermaid")) {
          return 320;
        }
        if (el.classList?.contains("hoja-word-toc-bloque")) {
          const items = el.querySelectorAll("li").length || 4;
          return 70 + items * 26;
        }
        if (tag === "ul" || tag === "ol") {
          const items = el.querySelectorAll("li").length || 2;
          return Math.max(50, items * Math.max(26, hLinea));
        }
        const chars = (el.textContent || "").length;
        const lineasEst = Math.max(1, Math.ceil(chars / 75));
        return Math.max(28, lineasEst * hLinea + 16);
      }

      function medirElemento(el) {
        if (!el || !el.tagName) return 30;
        const clon = el.cloneNode(true);
        divMedicion.appendChild(clon);
        let h = Math.ceil(clon.getBoundingClientRect().height);
        if (h > 0) {
          const st = window.getComputedStyle(clon);
          h += (parseFloat(st.marginTop) || 0) + (parseFloat(st.marginBottom) || 0);
        } else {
          h = calcularAlturaRespaldo(el);
        }
        divMedicion.removeChild(clon);
        return h;
      }

      // Preparar bloque TOC si corresponde
      let elemToc = null;
      let altToc = 0;
      if (bloqueTocHtml) {
        const divTemp = document.createElement("div");
        divTemp.innerHTML = bloqueTocHtml;
        elemToc = divTemp.firstElementChild;
        altToc = medirElemento(elemToc);
      }

      // 3. Partición estricta de páginas A4 (Altura útil: 840 px)
      const ALTURA_UTIL_A4 = normasApa ? 815 : 845;
      const paginas = [];
      let paginaActual = [];
      let alturaActual = 0;

      // Si el índice va al inicio, colocarlo en la primera página
      if (elemToc && posicionIndice === "inicio") {
        paginaActual.push(elemToc.outerHTML);
        alturaActual += altToc;
        if (elementosCrudos.length > 0) {
          // Salto de página limpio tras el índice al inicio
          paginas.push(paginaActual);
          paginaActual = [];
          alturaActual = 0;
        }
      }

      // Paginación de los elementos de contenido
      elementosCrudos.forEach((el) => {
        const tag = el.tagName.toLowerCase();
        const alt = medirElemento(el);

        // Salto de página para capítulos principales H1 si la página ya tiene contenido
        if (tag === "h1" && alturaActual > 160 && paginaActual.length > 0) {
          paginas.push(paginaActual);
          paginaActual = [];
          alturaActual = 0;
        }

        // Si excede la altura útil disponible y la página ya tiene elementos
        if (alturaActual + alt > ALTURA_UTIL_A4 && paginaActual.length > 0) {
          paginas.push(paginaActual);
          paginaActual = [];
          alturaActual = 0;
        }

        // Si un solo párrafo excede la altura útil de una página completa, se subdivide por oraciones
        if (tag === "p" && alt > ALTURA_UTIL_A4 && (el.textContent || "").length > 400) {
          const texto = el.textContent.trim();
          const oraciones = texto.match(/[^.!?]+[.!?]+(\s|$)|[^.!?]+$/g) || [texto];
          let subParrafo = "";
          oraciones.forEach((oracion) => {
            if ((subParrafo + oracion).length > 350 && subParrafo.length > 0) {
              paginaActual.push(`<p>${escapeHtml(subParrafo.trim())}</p>`);
              paginas.push(paginaActual);
              paginaActual = [];
              alturaActual = 0;
              subParrafo = oracion;
            } else {
              subParrafo += oracion;
            }
          });
          if (subParrafo.trim()) {
            paginaActual.push(`<p>${escapeHtml(subParrafo.trim())}</p>`);
            alturaActual += 60;
          }
        } else {
          paginaActual.push(el.outerHTML);
          alturaActual += alt;
        }
      });

      // Si el índice va al final: cerrar la página de contenido previa e iniciar página nueva limpia
      if (elemToc && posicionIndice === "final") {
        if (paginaActual.length > 0 && paginaActual.some(tieneContenidoReal)) {
          paginas.push(paginaActual);
          paginaActual = [];
          alturaActual = 0;
        }
        paginaActual.push(elemToc.outerHTML);
        alturaActual += altToc;
      }

      if (paginaActual.length > 0 && paginaActual.some(tieneContenidoReal)) {
        paginas.push(paginaActual);
      }

      // Limpiar contenedor temporal de medición
      try { divMedicion.remove(); } catch (eMed) { }

      // Filtrar páginas en blanco residuales
      const paginasFiltradas = paginas.filter((bloques) => bloques.some(tieneContenidoReal));
      const totalPags = Math.max(1, paginasFiltradas.length);

      // 4. Renderizar páginas consecutivas A4 exactas
      const mapaAlineacionCss = {
        justificado: "justify",
        izquierda: "left",
        centrado: "center",
        derecha: "right",
        justify: "justify",
        left: "left",
        center: "center",
        right: "right"
      };
      const textoAlineacion = mapaAlineacionCss[(alineacion || "justificado").toLowerCase()] || "justify";

      const cssBordesTablaTema = estiloBordesTabla === "horizontal"
        ? `
          .hoja-word-pagina table { border-top: 1.5px solid ${bordeTabla} !important; border-bottom: 1.5px solid ${bordeTabla} !important; border-left: none !important; border-right: none !important; }
          .hoja-word-pagina th { border-top: none !important; border-left: none !important; border-right: none !important; border-bottom: 1.5px solid ${bordeTabla} !important; }
          .hoja-word-pagina td { border: none !important; }
        `
        : (estiloBordesTabla === "exterior"
          ? `
            .hoja-word-pagina table { border: 1.5px solid ${bordeTabla} !important; }
            .hoja-word-pagina th { border-top: none !important; border-left: none !important; border-right: none !important; border-bottom: 1.5px solid ${bordeTabla} !important; }
            .hoja-word-pagina td { border: none !important; }
          `
          : `
            .hoja-word-pagina table { border: 1px solid ${bordeTabla} !important; }
            .hoja-word-pagina th { border: 1px solid ${bordeTabla} !important; ${temaClean === "tema3" ? "text-align: center !important;" : ""} }
            .hoja-word-pagina td { border: 1px solid ${bordeTabla} !important; }
          `);

      const hayMembrete = Boolean($("#word-opt-hoja-membrete")?.value);
      let estiloPaddingWord = normasApa ? 'padding:2.54cm !important;' : '';
      if (hayMembrete) {
        const tCm = $("#word-membrete-top") ? parseFloat($("#word-membrete-top").value) || 2.5 : 2.5;
        const bCm = $("#word-membrete-bottom") ? parseFloat($("#word-membrete-bottom").value) || 2.0 : 2.0;
        const lCm = $("#word-membrete-left") ? parseFloat($("#word-membrete-left").value) || 2.5 : 2.5;
        const rCm = $("#word-membrete-right") ? parseFloat($("#word-membrete-right").value) || 2.5 : 2.5;
        estiloPaddingWord = `padding: ${tCm}cm ${rCm}cm ${bCm}cm ${lCm}cm !important;`;
      }

      contenedorPaginas.innerHTML = paginasFiltradas.map((bloques, idx) => {
        const numPag = idx + 1;
        const justifyPie = alineacionPie === "izquierda" ? "flex-start" : (alineacionPie === "centro" ? "center" : "space-between");

        return `
          <article class="hoja-word-pagina" data-tema-word="${escapeHtml(temaClean)}" data-alineacion-word="${escapeHtml(textoAlineacion)}" style="font-family:'${fuenteWord}', Calibri, sans-serif; font-size:${tamanoPt}pt; line-height:${normasApa ? 2.0 : interlineado}; ${estiloPaddingWord}">
            <style>
              .hoja-word-pagina h1 { color: ${hexH1} !important; font-size: ${h1Pt}pt !important; font-weight: 700 !important; border-bottom: none !important; }
              .hoja-word-pagina h2 { color: ${hexH2H3} !important; font-size: ${h2Pt}pt !important; font-weight: 700 !important; border-bottom: none !important; }
              .hoja-word-pagina h3 { color: ${hexH2H3} !important; font-size: ${h3Pt}pt !important; font-weight: 700 !important; }
              .hoja-word-pagina p { text-align: ${textoAlineacion} !important; ${normasApa ? 'text-indent: 1.27cm !important;' : ''} }
              
              ${normasApa ? `
                .hoja-word-pagina table {
                  width: 100% !important;
                  border-collapse: collapse !important;
                  margin: 1rem 0 !important;
                  border-top: 2px solid #000000 !important;
                  border-bottom: 2px solid #000000 !important;
                  font-family: ${cssFuenteTabla} !important;
                  font-size: ${cssTamanoTabla} !important;
                }
                .hoja-word-pagina th {
                  border: none !important;
                  border-bottom: 1px solid #000000 !important;
                  padding: 0.5rem 0.65rem !important;
                  text-align: left !important;
                  background: transparent !important;
                  color: #000000 !important;
                  font-weight: 700 !important;
                }
                .hoja-word-pagina td {
                  border: none !important;
                  padding: 0.45rem 0.65rem !important;
                  background: transparent !important;
                  color: #111827 !important;
                }
              ` : `
                .hoja-word-pagina table {
                  width: 100% !important;
                  border-collapse: collapse !important;
                  margin: 0.9rem 0 !important;
                  font-family: ${cssFuenteTabla} !important;
                  font-size: ${cssTamanoTabla} !important;
                }
                .hoja-word-pagina th {
                  background-color: ${cabeceraBg} !important;
                  color: ${cabeceraTxt} !important;
                  padding: 0.55rem 0.75rem !important;
                  font-weight: 700 !important;
                  text-align: left !important;
                }
                .hoja-word-pagina td {
                  padding: 0.45rem 0.75rem !important;
                  color: #1f2937 !important;
                }
                .hoja-word-pagina tbody tr:nth-child(odd) td {
                  background-color: ${filaParBg} !important;
                }
                .hoja-word-pagina tbody tr:nth-child(even) td {
                  background-color: #ffffff !important;
                }
                ${cssBordesTablaTema}
              `}

              ${numerarEcuaciones ? `
                .hoja-word-pagina .mformula.display, .hoja-word-pagina .katex-display, .hoja-word-pagina .eq-bloque {
                  position: relative !important;
                  display: flex !important;
                  justify-content: center !important;
                  align-items: center !important;
                  width: 100% !important;
                  margin: 1.1rem 0 !important;
                  padding-right: 3.5rem !important;
                  box-sizing: border-box !important;
                }
                .hoja-word-pagina .eq-numero-word {
                  position: absolute !important;
                  right: 0.5rem !important;
                  top: 50% !important;
                  transform: translateY(-50%) !important;
                  color: #475569 !important;
                  font-weight: 600 !important;
                  font-size: 0.9em !important;
                }
              ` : ''}
            </style>
            <div class="hoja-word-pagina-cuerpo">
              ${bloques.join("\n")}
            </div>
            <div class="hoja-word-pagina-footer" style="display:flex; justify-content:${justifyPie}; align-items:center;">
              ${pieTexto ? `<span class="hoja-word-pie-texto">${escapeHtml(pieTexto)}</span>` : '<span></span>'}
              ${numerarPaginas ? `<span class="hoja-word-num-pag">Página ${numPag} de ${totalPags}</span>` : ''}
            </div>
          </article>
        `;
      }).join("\n");

      const paginacionEl = $("#word-hoja-paginacion");
      if (paginacionEl) paginacionEl.textContent = `${totalPags} página${totalPags > 1 ? 's' : ''}`;

      // 5. Renderizar elementos KaTeX y Mermaid
      if (typeof window.katex !== "undefined") {
        contenedorPaginas.querySelectorAll(".mformula").forEach((el) => {
          const tex = el.getAttribute("data-latex");
          if (!tex) return;
          try {
            window.katex.render(tex, el, {
              displayMode: el.classList.contains("display"),
              throwOnError: false,
            });
          } catch (errK) {
            el.textContent = tex;
          }
        });
      }

      if (typeof window.renderMathInElement !== "undefined") {
        try {
          window.renderMathInElement(contenedorPaginas, {
            delimiters: [
              { left: "$$", right: "$$", display: true },
              { left: "$", right: "$", display: false },
              { left: "\\[", right: "\\]", display: true },
              { left: "\\(", right: "\\)", display: false }
            ],
            throwOnError: false
          });
        } catch (eMath) {
          console.warn("Aviso renderizando KaTeX en Word:", eMath);
        }
      }

      if (numerarEcuaciones) {
        const eqDisplays = contenedorPaginas.querySelectorAll(".mformula.display, .katex-display, .eq-bloque");
        eqDisplays.forEach((eq, idx) => {
          if (!eq.querySelector(".eq-numero-word")) {
            const spanNum = document.createElement("span");
            spanNum.className = "eq-numero-word";
            spanNum.textContent = `(${idx + 1})`;
            eq.appendChild(spanNum);
          }
        });
      }

      // Renderizar diagramas Mermaid en la vista previa de Word y acotar sus SVG sin barras de desplazamiento
      if (window.renderizarMermaidCompartido) {
        await window.renderizarMermaidCompartido(contenedorPaginas);
        // Garantizar que no haya overflow-x ni scrollbars en contenedores mermaid de Word
        contenedorPaginas.querySelectorAll(".hoja-word-pagina .mermaid, .hoja-word-pagina pre.mermaid").forEach((el) => {
          el.style.overflow = "visible";
          el.style.overflowX = "visible";
          el.style.maxWidth = "100%";
          el.style.width = "100%";
        });
        contenedorPaginas.querySelectorAll(".hoja-word-pagina svg").forEach((svg) => {
          svg.style.maxWidth = "100%";
          svg.style.width = "100%";
          svg.style.height = "auto";
          svg.style.maxHeight = "none";
          svg.style.margin = "0 auto";
          svg.style.display = "block";
          svg.style.overflow = "visible";
        });
        // Erradicar cualquier residuo o bomba que Mermaid haya inyectado en el DOM
        document.querySelectorAll('[id^="dmermaid-"], .error-icon, [aria-roledescription="error"]').forEach(d => d.remove());
      }
    }
  } catch (err) {
    console.warn("Error renderizando hoja word:", err);
  }
}

let timerRenderPdfEnVivo = null;
let secuenciaPdfEnVivo = 0;
let blobUrlPdfActual = null;
async function refrescarVisorPdfEnVivo() {
  if (!window.MFOPDF) return;
  const md = await obtenerMarkdownActual();
  const nombreDoc = ($("#titulo-documento").value.trim() || MFORegistro.ui("nombre_documento")).replace(/\.pdf$/i, "");
  const opc = window.MFORegistro ? MFORegistro.obtenerOpciones("pdf") : {};
  const estadoEl = $("#pdf-estado");
  const vacioTexto = $("#pdf-vacio-texto");

  if (!md.trim()) {
    if (vacioTexto) vacioTexto.textContent = "Escribe o carga un documento en Docs para previsualizar aquí su PDF.";
    return;
  }

  if (vacioTexto) vacioTexto.textContent = "Compilando vista previa PDF en vivo…";
  if (estadoEl) estadoEl.textContent = "Compilando PDF en vivo con opciones de la barra lateral…";

  clearTimeout(timerRenderPdfEnVivo);
  timerRenderPdfEnVivo = setTimeout(async () => {
    const idPeticion = ++secuenciaPdfEnVivo;
    try {
      const plantillaPdfSel = $("#pdf-opt-hoja-membrete")?.value || "";
      let zonaPdfTop = null;
      let zonaPdfBottom = null;
      let zonaPdfLeft = null;
      let zonaPdfRight = null;
      if (plantillaPdfSel) {
        zonaPdfTop = $("#pdf-membrete-top") ? parseFloat($("#pdf-membrete-top").value) : null;
        zonaPdfBottom = $("#pdf-membrete-bottom") ? parseFloat($("#pdf-membrete-bottom").value) : null;
        zonaPdfLeft = $("#pdf-membrete-left") ? parseFloat($("#pdf-membrete-left").value) : null;
        zonaPdfRight = $("#pdf-membrete-right") ? parseFloat($("#pdf-membrete-right").value) : null;
      }

      const resp = await fetch("/api/office/exportar-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: nombreDoc,
          markdown: md,
          tema_pdf: $("#pdf-opt-paleta")?.value || opc.paleta || MFORegistro.defaults("pdf").paleta,
          plantilla_word: plantillaPdfSel,
          zona_top: zonaPdfTop,
          zona_bottom: zonaPdfBottom,
          zona_left: zonaPdfLeft,
          zona_right: zonaPdfRight,
          estilo_maquetacion: $("#pdf-opt-estilo")?.value || opc.estilo_maquetacion || MFORegistro.defaults("pdf").estilo_maquetacion,
          modo_columnas: $("#pdf-opt-modo-diseno")?.value || opc.modo_columnas || MFORegistro.defaults("pdf").modo_columnas,
          tamanio_pt: parseFloat($("#pdf-opt-tamanio")?.value || opc.tamanio_pt || MFORegistro.defaults("pdf").tamanio_pt),
          justificado: $("#pdf-opt-justificado") ? $("#pdf-opt-justificado").checked : (opc.justificado !== false),
          portada_premium: await (async () => { const _pp = recolectarPortadaPremium(); if (_pp) _pp.imagenes = await convertirFotosPortada(); return _pp; })(),
          fuente: $("#pdf-opt-fuente")?.value || opc.fuente || MFORegistro.defaults("pdf").fuente,
          interlineado: parseFloat($("#pdf-opt-interlineado")?.value || opc.interlineado || MFORegistro.defaults("pdf").interlineado),
          pie_pagina: $("#pdf-opt-pie") ? $("#pdf-opt-pie").value : (opc.pie_pagina || MFORegistro.defaults("pdf").pie_pagina),
          salto_capitulo: $("#pdf-opt-salto-cap") ? $("#pdf-opt-salto-cap").checked : (opc.salto_capitulo !== false),
          running_header: $("#pdf-opt-running-header") ? $("#pdf-opt-running-header").checked : (opc.running_header !== false),
          numerar_paginas: $("#pdf-opt-num-pag") ? $("#pdf-opt-num-pag").checked : (opc.numerar_paginas !== false),
          indice_al_final: $("#pdf-opt-toc") ? $("#pdf-opt-toc").checked : (opc.indice_al_final !== false),
        }),
      });

      if (!resp.ok) {
        let detalle = "";
        try { detalle = (await resp.json()).detail || ""; } catch (_) { /* respuesta no JSON */ }
        throw new Error(`Error ${resp.status} al compilar PDF${detalle ? ": " + detalle : ""}`);
      }

      const blob = await resp.blob();
      // Descarta respuestas obsoletas si el usuario cambió opciones durante la compilación
      if (idPeticion !== secuenciaPdfEnVivo) return;
      const ab = await blob.arrayBuffer();
      if (blobUrlPdfActual) URL.revokeObjectURL(blobUrlPdfActual);
      blobUrlPdfActual = URL.createObjectURL(blob);

      if (window.MFOPDF.cargarDesdeArrayBuffer) {
        await window.MFOPDF.cargarDesdeArrayBuffer(ab, `${nombreDoc}.pdf`, blobUrlPdfActual);
      }
    } catch (err) {
      console.warn("Aviso en visor PDF en vivo:", err);
      if (estadoEl) estadoEl.textContent = `Previsualización PDF: ${err.message}`;
    }
  }, 300);
}

$("#btn-refrescar-vista-word")?.addEventListener("click", () => renderizarHojaWordPreview());

async function ejecutarExportarWord() {
  const btnHeader = $("#btn-exportar-word");
  const btnSidebar = $("#btn-exportar-word-sidebar");
  const estadoEl = $("#word-estado");
  const md = await obtenerMarkdownActual();

  if (!md.trim()) {
    alert("No hay contenido Markdown en Docs para exportar.");
    return;
  }

  const nombreBase = ($("#titulo-documento").value.trim() || MFORegistro.ui("nombre_documento")).replace(/\.docx$/i, "");
  const opc = window.MFORegistro ? MFORegistro.obtenerOpciones("word") : {};

  [btnHeader, btnSidebar].forEach(b => {
    if (b) { b.disabled = true; b.textContent = "⏳ Convirtiendo…"; }
  });
  if (estadoEl) estadoEl.textContent = "Generando archivo .docx con motor profesional…";

  try {
    const modoColorTit = $("#word-sel-modo-color-titulos")?.value || opc.modo_color_titulos || MFORegistro.defaults("word").modo_color_titulos;
    let colorTitulosVal = MFORegistro.defaults("word").color_titulos;
    let colH1 = MFORegistro.ui("color_tinta_negra");
    let colH2 = MFORegistro.ui("color_tinta_negra");

    if (modoColorTit === "paleta") {
      colorTitulosVal = $("#word-opt-paleta-titulos")?.value || opc.color_titulos || MFORegistro.defaults("word").color_titulos;
      colH1 = "";
      colH2 = "";
    } else if (modoColorTit === "personalizado") {
      colorTitulosVal = "personalizado";
      colH1 = $("#word-picker-tit-h1")?.value || opc.color_tit_h1 || MFORegistro.defaults("word").color_tit_h1;
      colH2 = $("#word-picker-tit-h2")?.value || opc.color_tit_h2 || MFORegistro.defaults("word").color_tit_h2;
    }

    const temaSeleccionado = $("#word-opt-tema")?.value || opc.tema || MFORegistro.defaults("word").tema;
    const esTemaNativo = ["tema1", "tema2", "tema3"].includes(temaSeleccionado.toLowerCase());
    const paletaSuaveChecked = $("#word-opt-paleta-suave-tablas") ? $("#word-opt-paleta-suave-tablas").checked : true;
    const usarColoresTablaCustom = !esTemaNativo && !paletaSuaveChecked;

    const plantillaWordSel = $("#word-opt-hoja-membrete")?.value || "";
    let zonaTop = null;
    let zonaBottom = null;
    let zonaLeft = null;
    let zonaRight = null;
    if (plantillaWordSel) {
      zonaTop = $("#word-membrete-top") ? parseFloat($("#word-membrete-top").value) : null;
      zonaBottom = $("#word-membrete-bottom") ? parseFloat($("#word-membrete-bottom").value) : null;
      zonaLeft = $("#word-membrete-left") ? parseFloat($("#word-membrete-left").value) : null;
      zonaRight = $("#word-membrete-right") ? parseFloat($("#word-membrete-right").value) : null;
    }

    const payload = {
      nombre: nombreBase,
      markdown: md,
      tema_word: temaSeleccionado,
      plantilla_word: plantillaWordSel,
      zona_top: zonaTop,
      zona_bottom: zonaBottom,
      zona_left: zonaLeft,
      zona_right: zonaRight,
      color_titulos_word: colorTitulosVal,
      modo_color_titulos: modoColorTit,
      color_tit_h1: colH1,
      color_tit_h2: colH2,
      paleta_suave_tablas: paletaSuaveChecked,
      paleta_tabla: $("#word-opt-paleta-tablas")?.value || opc.paleta_tablas || opc.paleta_tabla || MFORegistro.defaults("word").paleta_tabla,
      con_plantilla: $("#word-plantilla") ? $("#word-plantilla").checked : true,
      fuente: $("#word-opt-fuente")?.value || opc.fuente || MFORegistro.defaults("word").fuente,
      tamanio_pt: parseFloat($("#word-opt-tamanio")?.value || opc.tamano_pt || opc.tamanio || MFORegistro.defaults("word").tamanio),
      interlineado: parseFloat($("#word-opt-interlineado")?.value || opc.interlineado || MFORegistro.defaults("word").interlineado),
      alineacion: $("#word-opt-alineacion")?.value || opc.alineacion || MFORegistro.defaults("word").alineacion,
      fuente_tabla: $("#word-opt-fuente-tabla")?.value || opc.fuente_tabla || MFORegistro.defaults("word").fuente_tabla,
      tamanio_tabla_pt: $("#word-opt-tamanio-tabla")?.value && $("#word-opt-tamanio-tabla")?.value !== "auto" ? parseFloat($("#word-opt-tamanio-tabla").value) : null,
      pie_pagina: $("#word-opt-pie")?.value || opc.pie_pagina || MFORegistro.defaults("word").pie_pagina,
      alineacion_pie: $("#word-opt-alineacion-pie")?.value || opc.alineacion_pie || MFORegistro.defaults("word").alineacion_pie,
      normas_apa: $("#word-opt-apa7") ? $("#word-opt-apa7").checked : false,
      numerar_ecuaciones: $("#word-opt-num-eq") ? $("#word-opt-num-eq").checked : false,
      crear_indice: $("#word-opt-toc") ? $("#word-opt-toc").checked : false,
      posicion_indice: $("#word-opt-posicion-indice")?.value || opc.posicion_indice || MFORegistro.defaults("word").posicion_indice,
      numerar_paginas: $("#word-opt-num-pag") ? $("#word-opt-num-pag").checked : true,
      color_tabla_cabecera: usarColoresTablaCustom ? ($("#word-picker-tabla-cabecera")?.value || opc.color_tabla_cabecera || MFORegistro.defaults("word").color_tabla_cabecera) : "",
      color_tabla_filas: usarColoresTablaCustom ? ($("#word-picker-tabla-filas")?.value || opc.color_tabla_filas || MFORegistro.defaults("word").color_tabla_filas) : "",
      color_tabla_borde: usarColoresTablaCustom ? ($("#word-picker-tabla-borde")?.value || opc.color_tabla_borde || MFORegistro.defaults("word").color_tabla_borde) : "",
    };

    const respuesta = await fetch(`${API.office}/exportar-docx`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!respuesta.ok) {
      const detalle = await respuesta.json().catch(() => ({}));
      throw new Error(detalle?.detalle || respuesta.statusText);
    }
    const blob = await respuesta.blob();
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = `${nombreBase}.docx`;
    document.body.appendChild(enlace);
    enlace.click();
    document.body.removeChild(enlace);

    const tamanoKB = `${Math.max(1, Math.round(blob.size / 1024))} KB`;
    registrarEntregable("word", `${nombreBase}.docx`, url, tamanoKB);
    if (estadoEl) estadoEl.textContent = `✔ Exportado con éxito: ${nombreBase}.docx (${tamanoKB})`;
  } catch (error) {
    if (estadoEl) estadoEl.textContent = `✖ Error: ${error.message}`;
    alert(`Error al exportar Word: ${error.message}`);
  } finally {
    if (btnHeader) { btnHeader.disabled = false; btnHeader.textContent = "📄 Exportar .docx"; }
    if (btnSidebar) { btnSidebar.disabled = false; btnSidebar.textContent = "📄 Exportar .docx"; }
  }
}

$("#btn-exportar-word")?.addEventListener("click", ejecutarExportarWord);
$("#btn-exportar-word-sidebar")?.addEventListener("click", ejecutarExportarWord);

/* ══════════════ 4. APP: HTML DEDICADO — VISOR Y EXPORTACIÓN ══════════════ */
let htmlCompiladoBlobUrl = "";

function construirPayloadHtml(md, nombreDoc) {
  const opc = window.MFORegistro ? MFORegistro.obtenerOpciones("html") : {};
  const temaHtml = $("#html-opt-tema")?.value || opc.tema || MFORegistro.defaults("html").tema;
  const paletaTri = $("#html-opt-paleta")?.value || opc.paleta_tricolor || MFORegistro.defaults("html").paleta_tricolor;
  const anchoMaximo = $("#html-opt-ancho")?.value || opc.ancho_max || MFORegistro.defaults("html").ancho_max;
  const fuente = $("#html-opt-fuente")?.value || opc.fuente || MFORegistro.defaults("html").fuente;
  const justificado = $("#html-opt-justificado") ? $("#html-opt-justificado").checked : (opc.justificado !== false);
  const numerarEcuaciones = $("#html-opt-num-eq") ? $("#html-opt-num-eq").checked : !!opc.numerar_ecuaciones;
  const footerIzq = $("#html-opt-footer-izq") ? $("#html-opt-footer-izq").value : (opc.footer_izq || MFORegistro.defaults("html").footer_izq);
  const footerDer = $("#html-opt-footer-der") ? $("#html-opt-footer-der").value : (opc.footer_der || MFORegistro.defaults("html").footer_der);

  return {
    nombre: nombreDoc,
    titulo: nombreDoc,
    markdown: md || "# Sin contenido en el documento",
    texto: md || "# Sin contenido en el documento",
    tema_html: temaHtml,
    paleta_tricolor: paletaTri !== "tema_default" ? paletaTri : undefined,
    fuente: fuente,
    ancho_maximo: anchoMaximo,
    justificado: justificado,
    numerar_ecuaciones: numerarEcuaciones,
    footer_izq: footerIzq,
    footer_der: footerDer,
  };
}

async function cargarVisorHtmlDedicado() {
  const iframe = $("#visor-html-dedicado");
  const linkAbrir = $("#btn-abrir-html-dedicado");
  const md = await obtenerMarkdownActual();
  const nombreDoc = $("#titulo-documento").value.trim() || MFORegistro.ui("nombre_documento");

  if (!iframe) return;

  // Erradicar inmediatamente cualquier bomba residual en el DOM principal
  document.querySelectorAll('[id^="dmermaid-"], .error-icon, [aria-roledescription="error"]').forEach(d => d.remove());

  try {
    const payload = construirPayloadHtml(md, nombreDoc);
    const resp = await fetch("/api/render-preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const res = await resp.json();
    if (res.ok && res.datos && res.datos.html) {
      iframe.srcdoc = res.datos.html;
      iframe.onload = () => {
        try {
          // Limpiar residuos en el iframe si Mermaid llegase a inyectar algo
          if (iframe.contentDocument) {
            iframe.contentDocument.querySelectorAll('[id^="dmermaid-"], .error-icon').forEach(d => d.remove());
          }
          if (iframe.contentWindow && typeof iframe.contentWindow._iniciarRenderMarkflow === "function") {
            iframe.contentWindow._iniciarRenderMarkflow();
          }
        } catch (e) { }
      };
      if (htmlCompiladoBlobUrl) URL.revokeObjectURL(htmlCompiladoBlobUrl);
      const blob = new Blob([res.datos.html], { type: "text/html;charset=utf-8" });
      htmlCompiladoBlobUrl = URL.createObjectURL(blob);
      if (linkAbrir) linkAbrir.href = htmlCompiladoBlobUrl;
    }
  } catch (err) {
    console.warn("Error cargando HTML dedicado:", err);
  }
}

async function ejecutarExportarHtml() {
  const btnHeader = $("#btn-exportar-html");
  const btnSidebar = $("#btn-exportar-html-sidebar");
  const md = await obtenerMarkdownActual();
  if (!md.trim()) {
    alert("No hay contenido Markdown en Docs para exportar.");
    return;
  }
  const nombreDoc = ($("#titulo-documento").value.trim() || MFORegistro.ui("nombre_documento")).replace(/\.html$/i, "");

  [btnHeader, btnSidebar].forEach((b) => {
    if (b) {
      b.disabled = true;
      b.dataset.textoOriginal = b.textContent;
      b.textContent = "⏳ Generando HTML…";
    }
  });

  try {
    const payload = construirPayloadHtml(md, nombreDoc);
    const respuesta = await fetch(`${API.office}/exportar-html`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!respuesta.ok) {
      const detalle = await respuesta.json().catch(() => ({}));
      throw new Error(detalle?.detalle || respuesta.statusText);
    }

    const blob = await respuesta.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${nombreDoc}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    const tamanoKB = `${Math.max(1, Math.round(blob.size / 1024))} KB`;
    registrarEntregable("html", `${nombreDoc}.html`, url, tamanoKB);
  } catch (err) {
    alert(`Error al exportar HTML: ${err.message}`);
  } finally {
    [btnHeader, btnSidebar].forEach((b) => {
      if (b) {
        b.disabled = false;
        b.textContent = b.dataset.textoOriginal || MFORegistro.ui("etiqueta_exportar_html");
      }
    });
  }
}

$("#btn-refrescar-html-dedicado")?.addEventListener("click", () => cargarVisorHtmlDedicado());
$("#btn-exportar-html")?.addEventListener("click", ejecutarExportarHtml);
$("#btn-exportar-html-sidebar")?.addEventListener("click", ejecutarExportarHtml);

/* ══════════════ 5. APP: PDF EDITORIAL — VISOR Y EXPORTACIÓN ══════════════ */
async function ejecutarExportarPdf() {
  const btnHeader = $("#btn-exportar-pdf");
  const btnSidebar = $("#btn-exportar-pdf-sidebar");
  const estadoEl = $("#pdf-estado");
  const md = await obtenerMarkdownActual();

  if (!md.trim()) {
    alert("No hay contenido Markdown en Docs para compilar.");
    return;
  }

  const nombreDoc = ($("#titulo-documento").value.trim() || MFORegistro.ui("nombre_documento")).replace(/\.pdf$/i, "");
  const opc = window.MFORegistro ? MFORegistro.obtenerOpciones("pdf") : {};

  [btnHeader, btnSidebar].forEach(b => {
    if (b) { b.disabled = true; b.textContent = "⏳ Compilando PDF…"; }
  });
  if (estadoEl) estadoEl.textContent = "Compilando PDF con Chromium Headless y CSS Paged Media…";

  try {
    const plantillaPdfSel = $("#pdf-opt-hoja-membrete")?.value || "";
    let zonaPdfTop = null;
    let zonaPdfBottom = null;
    let zonaPdfLeft = null;
    let zonaPdfRight = null;
    if (plantillaPdfSel) {
      zonaPdfTop = $("#pdf-membrete-top") ? parseFloat($("#pdf-membrete-top").value) : null;
      zonaPdfBottom = $("#pdf-membrete-bottom") ? parseFloat($("#pdf-membrete-bottom").value) : null;
      zonaPdfLeft = $("#pdf-membrete-left") ? parseFloat($("#pdf-membrete-left").value) : null;
      zonaPdfRight = $("#pdf-membrete-right") ? parseFloat($("#pdf-membrete-right").value) : null;
    }

    const resp = await fetch("/api/office/exportar-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nombre: nombreDoc,
        markdown: md,
        tema_pdf: $("#pdf-opt-paleta")?.value || opc.paleta || MFORegistro.defaults("pdf").paleta,
        plantilla_word: plantillaPdfSel,
        zona_top: zonaPdfTop,
        zona_bottom: zonaPdfBottom,
        zona_left: zonaPdfLeft,
        zona_right: zonaPdfRight,
        estilo_maquetacion: $("#pdf-opt-estilo")?.value || opc.estilo_maquetacion || MFORegistro.defaults("pdf").estilo_maquetacion,
        modo_columnas: $("#pdf-opt-modo-diseno")?.value || opc.modo_columnas || MFORegistro.defaults("pdf").modo_columnas,
        tamanio_pt: parseFloat($("#pdf-opt-tamanio")?.value || opc.tamanio_pt || MFORegistro.defaults("pdf").tamanio_pt),
        justificado: $("#pdf-opt-justificado") ? $("#pdf-opt-justificado").checked : (opc.justificado !== false),
        portada_premium: await (async () => { const _pp = recolectarPortadaPremium(); if (_pp) _pp.imagenes = await convertirFotosPortada(); return _pp; })(),
        fuente: $("#pdf-opt-fuente")?.value || opc.fuente || MFORegistro.defaults("pdf").fuente,
        interlineado: parseFloat($("#pdf-opt-interlineado")?.value || opc.interlineado || MFORegistro.defaults("pdf").interlineado),
        pie_pagina: $("#pdf-opt-pie") ? $("#pdf-opt-pie").value : (opc.pie_pagina || MFORegistro.defaults("pdf").pie_pagina),
        salto_capitulo: $("#pdf-opt-salto-cap") ? $("#pdf-opt-salto-cap").checked : (opc.salto_capitulo !== false),
        running_header: $("#pdf-opt-running-header") ? $("#pdf-opt-running-header").checked : (opc.running_header !== false),
        numerar_paginas: $("#pdf-opt-num-pag") ? $("#pdf-opt-num-pag").checked : (opc.numerar_paginas !== false),
        indice_al_final: $("#pdf-opt-toc") ? $("#pdf-opt-toc").checked : (opc.indice_al_final !== false),
      }),
    });

    if (!resp.ok) {
      const errJson = await resp.json().catch(() => ({}));
      throw new Error(errJson.detail || `Error en compilación HTTP ${resp.status}`);
    }

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${nombreDoc}.pdf`;
    a.click();

    const tamanoKB = `${Math.max(1, Math.round(blob.size / 1024))} KB`;
    registrarEntregable("pdf", `${nombreDoc}.pdf`, url, tamanoKB);
    if (estadoEl) estadoEl.textContent = `✔ PDF descargado con éxito: ${nombreDoc}.pdf`;
  } catch (err) {
    if (estadoEl) estadoEl.textContent = `✖ Error: ${err.message}`;
    alert(`Error al compilar PDF: ${err.message}`);
  } finally {
    if (btnHeader) { btnHeader.disabled = false; btnHeader.textContent = "📕 Exportar PDF"; }
    if (btnSidebar) { btnSidebar.disabled = false; btnSidebar.textContent = "📕 Exportar PDF"; }
  }
}

$("#btn-exportar-pdf")?.addEventListener("click", ejecutarExportarPdf);
$("#btn-exportar-pdf-sidebar")?.addEventListener("click", ejecutarExportarPdf);
$("#btn-refrescar-pdf")?.addEventListener("click", () => {
  if (window.MFOPDF) window.MFOPDF.abrir();
});

/* ══════════════ 6. APP: TABLAS EXCEL — VISOR, COPIA Y EXPORTACIÓN ══════════════ */
let tablasDetectadas = [];
let tablaActivaIndice = 0;

async function cargarTablasExcel() {
  const md = await obtenerMarkdownActual();
  const badgeTotal = $("#badge-total-tablas");
  const selTabla = $("#sel-tabla-activa");
  const avisoSinTablas = $("#excel-sin-tablas-aviso");
  const cuadriculaPrincipal = $("#excel-contenedor-cuadricula-principal");

  try {
    const resp = await fetch("/api/office/extraer-tablas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto: md, markdown: md }),
    });
    const res = await resp.json();
    tablasDetectadas = (res.datos && res.datos.tablas) || [];

    if (badgeTotal) badgeTotal.textContent = `${tablasDetectadas.length} tablas detectadas`;

    if (tablasDetectadas.length === 0) {
      if (avisoSinTablas) avisoSinTablas.style.display = "block";
      if (cuadriculaPrincipal) cuadriculaPrincipal.style.display = "none";
      if (selTabla) selTabla.style.display = "none";
      return;
    }

    if (avisoSinTablas) avisoSinTablas.style.display = "none";
    if (cuadriculaPrincipal) cuadriculaPrincipal.style.display = "block";

    if (selTabla) {
      if (tablasDetectadas.length > 1) {
        selTabla.style.display = "inline-block";
        selTabla.innerHTML = tablasDetectadas.map((t, idx) =>
          `<option value="${idx}">Hoja ${idx + 1}: ${t.titulo || `Tabla ${idx + 1}`}</option>`
        ).join("");
      } else {
        selTabla.style.display = "none";
      }
    }

    tablaActivaIndice = 0;
    renderizarCuadriculaExcel(tablasDetectadas[0]);
  } catch (err) {
    console.error("Error al extraer tablas:", err);
  }
}

function renderizarCuadriculaExcel(tabla) {
  const thead = $("#thead-excel");
  const tbody = $("#tbody-excel");
  const formulaBar = $("#excel-barra-formula");
  const cuadroNombre = $(".excel-cuadro-nombre");
  const tableEl = $("#tabla-excel-render");

  if (!thead || !tbody || !tabla) return;
  if (tableEl) tableEl.style.display = "table";
  thead.innerHTML = "";
  tbody.innerHTML = "";

  const cabeceras = tabla.cabeceras || [];
  const cabecerasHtml = tabla.cabeceras_html || cabeceras;
  const cabecerasLimpias = tabla.cabeceras_limpias || cabeceras;

  const filas = tabla.filas || [];
  const filasHtml = tabla.filas_html || filas;
  const filasLimpias = tabla.filas_limpias || filas;

  const numColsReales = cabeceras.length;
  const numColsTotal = Math.max(numColsReales, 8);

  // Fila de letras de columnas (A, B, C...)
  const trLetras = document.createElement("tr");
  const thEsquina = document.createElement("th");
  thEsquina.className = "col-esquina-vacia";
  thEsquina.textContent = "№";
  trLetras.appendChild(thEsquina);

  for (let cIdx = 0; cIdx < numColsTotal; cIdx++) {
    const thLetra = document.createElement("th");
    thLetra.className = "col-indice-letra";
    thLetra.textContent = String.fromCharCode(65 + (cIdx % 26));
    trLetras.appendChild(thLetra);
  }
  thead.appendChild(trLetras);

  // Fila de cabeceras de la tabla
  const trTitulos = document.createElement("tr");
  const thIdxTit = document.createElement("td");
  thIdxTit.className = "col-indice-fila";
  thIdxTit.textContent = "1";
  trTitulos.appendChild(thIdxTit);

  for (let cIdx = 0; cIdx < numColsTotal; cIdx++) {
    if (cIdx < numColsReales) {
      const th = document.createElement("th");
      th.className = "col-cabecera-dato";
      th.innerHTML = cabecerasHtml[cIdx];
      const letraCol = String.fromCharCode(65 + (cIdx % 26));
      th.dataset.col = letraCol;
      th.dataset.row = "1";
      th.addEventListener("click", () => {
        document.querySelectorAll("#tabla-excel-render td, #tabla-excel-render th").forEach(el => el.classList.remove("celda-activa"));
        th.classList.add("celda-activa");
        if (cuadroNombre) cuadroNombre.textContent = `${letraCol}1`;
        if (formulaBar) formulaBar.textContent = cabecerasLimpias[cIdx];
      });
      trTitulos.appendChild(th);
    } else {
      const thVacia = document.createElement("th");
      thVacia.className = "col-cabecera-vacia";
      thVacia.textContent = "—";
      trTitulos.appendChild(thVacia);
    }
  }
  thead.appendChild(trTitulos);

  // Filas del cuerpo de la tabla
  const numFilasTotal = Math.max(filas.length, 12);
  for (let fIdx = 0; fIdx < numFilasTotal; fIdx++) {
    const tr = document.createElement("tr");
    const numFila = fIdx + 2;
    const tdIdx = document.createElement("td");
    tdIdx.className = "col-indice-fila";
    tdIdx.textContent = numFila;
    tr.appendChild(tdIdx);

    const filaDatosHtml = fIdx < filasHtml.length ? filasHtml[fIdx] : null;
    const filaDatosLimpios = fIdx < filasLimpias.length ? filasLimpias[fIdx] : null;

    for (let cIdx = 0; cIdx < numColsTotal; cIdx++) {
      const letraCol = String.fromCharCode(65 + (cIdx % 26));
      if (filaDatosHtml && cIdx < numColsReales) {
        const td = document.createElement("td");
        td.className = "col-celda-dato";
        td.innerHTML = filaDatosHtml[cIdx] || "";
        td.dataset.coord = `${letraCol}${numFila}`;
        const valLimpio = (filaDatosLimpios && filaDatosLimpios[cIdx]) || "";
        td.addEventListener("click", () => {
          document.querySelectorAll("#tabla-excel-render td, #tabla-excel-render th").forEach(el => el.classList.remove("celda-activa"));
          td.classList.add("celda-activa");
          if (cuadroNombre) cuadroNombre.textContent = td.dataset.coord;
          if (formulaBar) formulaBar.textContent = valLimpio;
        });
        tr.appendChild(td);
      } else {
        const tdVacia = document.createElement("td");
        tdVacia.className = "col-celda-vacia";
        tdVacia.textContent = "";
        tdVacia.dataset.coord = `${letraCol}${numFila}`;
        tdVacia.addEventListener("click", () => {
          document.querySelectorAll("#tabla-excel-render td, #tabla-excel-render th").forEach(el => el.classList.remove("celda-activa"));
          tdVacia.classList.add("celda-activa");
          if (cuadroNombre) cuadroNombre.textContent = tdVacia.dataset.coord;
          if (formulaBar) formulaBar.textContent = "";
        });
        tr.appendChild(tdVacia);
      }
    }
    tbody.appendChild(tr);
  }

  if (cuadroNombre) cuadroNombre.textContent = "A1";
  if (formulaBar) formulaBar.textContent = cabecerasLimpias[0] || "Tabla lista";

  // Renderizar fórmulas KaTeX en celdas y cabeceras de Excel
  if (window.katex && tableEl) {
    tableEl.querySelectorAll(".mformula").forEach((el) => {
      const tex = el.getAttribute("data-latex");
      if (!tex) return;
      try {
        window.katex.render(tex, el, {
          displayMode: el.classList.contains("display"),
          throwOnError: false,
        });
      } catch (e) {
        el.textContent = tex;
      }
    });
  }
}

$("#sel-tabla-activa")?.addEventListener("change", (e) => {
  const idx = parseInt(e.target.value, 10);
  if (tablasDetectadas[idx]) {
    tablaActivaIndice = idx;
    renderizarCuadriculaExcel(tablasDetectadas[idx]);
  }
});

$("#btn-extraer-tablas-docs")?.addEventListener("click", () => cargarTablasExcel());

/* Copia con formato enriquecido (HTML + TSV) */
async function ejecutarCopiarTablaExcel() {
  const t = tablasDetectadas[tablaActivaIndice];
  if (!t) {
    alert("No hay ninguna tabla para copiar en este documento.");
    return;
  }
  const cabs = t.cabeceras_limpias || t.cabeceras;
  const fils = t.filas_limpias || t.filas;

  // 1. Formato texto plano TSV
  let tsv = cabs.join("\t") + "\n";
  fils.forEach(f => { tsv += f.join("\t") + "\n"; });

  // 2. Formato HTML inline estilizado para portapapeles
  let html = `<table style="border-collapse:collapse; font-family:Calibri,sans-serif; font-size:10pt;"><thead><tr style="background:#107C41; color:#ffffff; font-weight:bold;">`;
  cabs.forEach(c => { html += `<th style="border:1px solid #d1d5db; padding:6px 10px;">${c}</th>`; });
  html += `</tr></thead><tbody>`;
  fils.forEach((f, idx) => {
    const bg = idx % 2 === 0 ? "#ffffff" : "#f4faf5";
    html += `<tr style="background:${bg};">`;
    f.forEach(celda => { html += `<td style="border:1px solid #d1d5db; padding:5px 8px;">${celda}</td>`; });
    html += `</tr>`;
  });
  html += `</tbody></table>`;

  try {
    if (navigator.clipboard && window.ClipboardItem) {
      const blobText = new Blob([tsv], { type: "text/plain" });
      const blobHtml = new Blob([html], { type: "text/html" });
      await navigator.clipboard.write([
        new ClipboardItem({
          "text/plain": blobText,
          "text/html": blobHtml,
        })
      ]);
    } else {
      await navigator.clipboard.writeText(tsv);
    }
    notificar($("#docs-estado"), "Tabla copiada con formato para Excel ✓", "ok");
    alert("✔ ¡Tabla copiada con éxito!\n\nPégala directamente en Microsoft Excel o Google Sheets con Ctrl+V conservando su estructura y colores.");
  } catch (err) {
    prompt("Copia manualmente los datos de la tabla:", tsv);
  }
}

$("#btn-copiar-tabla-excel")?.addEventListener("click", ejecutarCopiarTablaExcel);
$("#btn-copiar-tabla-excel-sidebar")?.addEventListener("click", ejecutarCopiarTablaExcel);

/* Exportar libro .xlsx con modo de hojas, cuadrícula y autoajuste del DOM y registro */
async function ejecutarExportarExcel() {
  const btnSidebar = $("#btn-exportar-excel-sidebar");
  const btnDescargar = $("#btn-descargar-tabla-xlsx");
  const md = await obtenerMarkdownActual();
  if (!md.trim()) {
    alert("No hay contenido Markdown en Docs.");
    return;
  }
  const nombreDoc = ($("#titulo-documento").value.trim() || "tablas_documento").replace(/\.xlsx$/i, "");
  const opc = window.MFORegistro ? MFORegistro.obtenerOpciones("excel") : {};

  let estiloExcel = $("#excel-opt-paleta")?.value || opc.paleta || MFORegistro.defaults("excel").paleta;
  if (estiloExcel.startsWith("pal_custom_") || estiloExcel.startsWith("custom_")) {
    const pals = window.MFORegistro?.obtenerPaletasPersonalizadas() || [];
    const pEncontrada = pals.find(p => p.id === estiloExcel);
    if (pEncontrada && pEncontrada.colores && pEncontrada.colores.length >= 2) {
      const c1 = pEncontrada.colores[0];
      const c2 = pEncontrada.colores[1];
      const c3 = pEncontrada.colores[2] || pEncontrada.colores[1];
      const c4 = pEncontrada.colores[3] || MFORegistro.ui("color_relleno_4");
      const c5 = pEncontrada.colores[4] || MFORegistro.ui("color_relleno_5");
      estiloExcel = `${c1}|${c2}|${c3}|${c4}|${c5}`;
    }
  }

  const modoHojas = $("#excel-opt-modo-hojas")?.value || opc.modo_hojas || MFORegistro.defaults("excel").modo_hojas;
  const tamFuente = parseInt($("#excel-opt-fuente-tam")?.value || opc.fuente_tam || MFORegistro.defaults("excel").fuente_tam, 10);
  const gridlines = $("#excel-opt-gridlines") ? $("#excel-opt-gridlines").checked : (opc.gridlines !== false);
  const autofit = $("#excel-opt-autofit") ? $("#excel-opt-autofit").checked : true;
  const anchoCol = $("#excel-opt-ancho-col")?.value || opc.ancho_col || MFORegistro.defaults("excel").ancho_col;

  [btnSidebar, btnDescargar].forEach(b => {
    if (b) { b.disabled = true; b.dataset.textoOriginal = b.textContent; b.textContent = "⏳ Exportando Excel…"; }
  });

  try {
    const resp = await fetch("/api/office/exportar-tablas-excel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nombre: `${nombreDoc}_tablas`,
        markdown: md,
        estilo_excel: estiloExcel,
        paleta_id: estiloExcel,
        modo_hojas: modoHojas,
        tamano_fuente: tamFuente,
        mostrar_gridlines: gridlines,
        autofit: autofit,
        ancho_col: anchoCol,
      }),
    });
    if (!resp.ok) throw new Error("Error generando archivo Excel.");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${nombreDoc}_tablas.xlsx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    const tamanoKB = `${Math.max(1, Math.round(blob.size / 1024))} KB`;
    registrarEntregable("excel", `${nombreDoc}_tablas.xlsx`, url, tamanoKB);
  } catch (err) {
    alert(`Error al descargar Excel: ${err.message}`);
  } finally {
    [btnSidebar, btnDescargar].forEach(b => {
      if (b) { b.disabled = false; b.textContent = b.dataset.textoOriginal || MFORegistro.ui("etiqueta_exportar_xlsx"); }
    });
  }
}

$("#btn-descargar-tabla-xlsx")?.addEventListener("click", ejecutarExportarExcel);
$("#btn-exportar-excel-sidebar")?.addEventListener("click", ejecutarExportarExcel);

// Inicializar barras laterales y listeners al cargar
setTimeout(async () => {
  try {
    await inicializarBarrasLaterales();
  } catch (e) {
    console.error("Error inicializando barras laterales:", e);
  }
  registrarListenersReactivos();
}, 100);

// Seguro: re-renderizar la hoja Word al recuperar el foco si la pestaña Word está activa
window.addEventListener("focus", () => {
  try {
    const panelWord = document.getElementById("panel-word");
    if (panelWord && panelWord.classList.contains("activo")) {
      renderizarHojaWordPreview().catch((e) => console.error("Error renderizando Word:", e));
    }
  } catch (e) {
    console.error("Error en seguro de foco Word:", e);
  }
});

/* ─────────────────── Round-trip .docx real (v1.4.0) ─────────────────────── */
/* 1) Importar .docx → nuevo documento Markdown en Documentos.               */
$("#btn-importar-docx").addEventListener("click", () => $("#input-docx-importar").click());

$("#input-docx-importar").addEventListener("change", async () => {
  const entrada = $("#input-docx-importar");
  const archivo = entrada.files && entrada.files[0];
  entrada.value = ""; /* permite reimportar el mismo archivo */
  if (!archivo) return;
  try {
    const formulario = new FormData();
    formulario.append("archivo", archivo);
    const respuesta = await fetch(`${API.office}/docx-importar`, {
      method: "POST",
      body: formulario,
    });
    if (!respuesta.ok) {
      const detalle = await respuesta.json().catch(() => ({}));
      throw new Error(detalle?.detalle || respuesta.statusText);
    }
    const cuerpo = await respuesta.json();
    const datos = cuerpo.datos;
    const aviso = datos.avisos.length
      ? `\n\nAvisos del motor:\n• ${datos.avisos.join("\n• ")}` : "";
    if (!confirm(`Importar «${archivo.name}» como documento Markdown?\n` +
      `Títulos: ${datos.stats.titulos} · Párrafos: ${datos.stats.parrafos} · ` +
      `Ítems de lista: ${datos.stats.items} · Tablas: ${datos.stats.tablas}${aviso}`)) return;

    const nombre = datos.nombre_sugerido;
    await jsonFetch(API.documentos, {
      method: "POST",
      body: JSON.stringify({ nombre, contenido: datos.texto }),
    });
    await listarDocumentos();
    await abrirDocumento(`${nombre}.md`);
  } catch (error) {
    alert(`No se pudo importar el .docx: ${error.message}`);
  }
});

/* 2) Round-trip en la app Word: extraer → editar → reguardar.               */
let rtNombreOriginal = "";

$("#btn-rt-extraer").addEventListener("click", () => $("#input-rt-docx").click());

$("#input-rt-docx").addEventListener("change", async () => {
  const entrada = $("#input-rt-docx");
  const archivo = entrada.files && entrada.files[0];
  entrada.value = "";
  if (!archivo) return;
  const estadoEl = $("#rt-estado");
  const boton = $("#btn-rt-extraer");
  boton.disabled = true;
  boton.textContent = "⏳ Extrayendo…";
  try {
    const formulario = new FormData();
    formulario.append("archivo", archivo);
    const respuesta = await fetch(`${API.office}/docx-importar`, {
      method: "POST",
      body: formulario,
    });
    if (!respuesta.ok) {
      const detalle = await respuesta.json().catch(() => ({}));
      throw new Error(detalle?.detalle || respuesta.statusText);
    }
    const datos = (await respuesta.json()).datos;
    rtNombreOriginal = archivo.name;
    $("#rt-texto").value = datos.texto;
    $("#rt-texto").style.display = "block";
    $("#btn-rt-reguardar").disabled = false;

    const btnDescargarMd = $("#btn-rt-descargar-md");
    const btnCargarDocs = $("#btn-rt-cargar-docs");
    if (btnDescargarMd) btnDescargarMd.style.display = "inline-block";
    if (btnCargarDocs) btnCargarDocs.style.display = "inline-block";

    const resumen = `títulos ${datos.stats.titulos} · párrafos ${datos.stats.parrafos} · ` +
      `ítems ${datos.stats.items} · tablas ${datos.stats.tablas}`;
    estadoEl.textContent = `✔ Extraído «${archivo.name}» (${resumen}).` +
      (datos.avisos.length ? ` Avisos: ${datos.avisos.join(" ")}` : "") +
      " Puedes descargar el .md, cargarlo en Docs o pulsar ♻ Reguardar.";
  } catch (error) {
    estadoEl.textContent = `✖ ${error.message}`;
  } finally {
    boton.disabled = false;
    boton.textContent = "📥 Cargar .docx";
  }
});

/* Descargar Markdown extraído del .docx */
$("#btn-rt-descargar-md")?.addEventListener("click", () => {
  const texto = $("#rt-texto").value;
  if (!texto.trim()) return;
  const blob = new Blob([texto], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  const nombreMd = (rtNombreOriginal || MFORegistro.ui("nombre_documento")).replace(/\.docx$/i, "") + ".md";
  enlace.href = url;
  enlace.download = nombreMd;
  enlace.click();
  URL.revokeObjectURL(url);
  $("#rt-estado").textContent = `✔ Markdown descargado como «${nombreMd}».`;
  registrarEntregable("md", nombreMd, url, `${Math.max(1, Math.round(blob.size / 1024))} KB`);
});

/* Cargar el Markdown extraído directamente en el editor Docs */
$("#btn-rt-cargar-docs")?.addEventListener("click", async () => {
  const texto = $("#rt-texto").value;
  if (!texto.trim()) return;
  const baseNombre = (rtNombreOriginal || MFORegistro.ui("nombre_documento")).replace(/\.docx$/i, "");
  $("#titulo-documento").value = baseNombre;
  $("#editor-markdown").value = texto;
  if (window.MFOEditor && typeof window.MFOEditor.setTexto === "function") {
    window.MFOEditor.setTexto(texto);
  }
  abrirApp("docs");
  if (typeof previsualizar === "function") previsualizar();
  notificar($("#docs-estado"), "cargado desde .docx", "ok");
});

$("#btn-rt-reguardar").addEventListener("click", async () => {
  const markdown = $("#rt-texto").value;
  if (!markdown.trim() || !rtNombreOriginal) return;
  const boton = $("#btn-rt-reguardar");
  const estadoEl = $("#rt-estado");
  boton.disabled = true;
  boton.textContent = "⏳ Reguardando…";
  try {
    const formulario = new FormData();
    formulario.append("archivo", new Blob([markdown]), rtNombreOriginal);
    formulario.append("markdown", markdown);
    const respuesta = await fetch(`${API.office}/docx-reguardar`, {
      method: "POST",
      body: formulario,
    });
    if (!respuesta.ok) {
      const detalle = await respuesta.json().catch(() => ({}));
      throw new Error(detalle?.detalle || respuesta.statusText);
    }
    const blob = await respuesta.blob();
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = rtNombreOriginal.replace(/\.docx$/i, "") + "-editado.docx";
    enlace.click();
    URL.revokeObjectURL(url);
    estadoEl.textContent = `✔ Reguardado: ${enlace.download} (cuerpo nuevo, estilos y cabeceras del original conservados).`;
  } catch (error) {
    estadoEl.textContent = `✖ ${error.message}`;
  } finally {
    boton.disabled = false;
    boton.textContent = "♻ Reguardar .docx";
  }
});

/* ─────────────────────────── Búsqueda FTS ─────────────────────────── */
let temporizadorBusqueda = null;
$("#buscador-fts").addEventListener("input", () => {
  clearTimeout(temporizadorBusqueda);
  temporizadorBusqueda = setTimeout(async () => {
    const consulta = $("#buscador-fts").value.trim();
    const panel = $("#resultados-busqueda");
    if (consulta.length < 2) { panel.hidden = true; panel.innerHTML = ""; return; }
    try {
      const cuerpo = await jsonFetch(`${API.documentos}/buscar`, {
        method: "POST",
        body: JSON.stringify({ consulta }),
      });
      const filas = cuerpo.datos || [];
      panel.hidden = false;
      panel.innerHTML = filas.length
        ? `<strong>${filas.length} coincidencia(s):</strong>` + filas.map((f) => `
            <div class="resultado-item" data-nombre="${f.nombre}">
              <strong>📄 ${f.nombre}</strong>
              <span class="fragmento">${(f.fragmento || "").replace(/[<>&]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" }[c]))}</span>
            </div>`).join("")
        : "Sin coincidencias.";
      panel.querySelectorAll(".resultado-item").forEach((item) => {
        item.addEventListener("click", () => abrirDocumento(item.dataset.nombre));
      });
    } catch (error) {
      panel.hidden = false;
      panel.textContent = `Error de búsqueda: ${error.message}`;
    }
  }, 350);
});

/* ─────────────────────────── Panel de IA ─────────────────────────── */
function alternarPanelIA(abierto) {
  estado.panelIA = abierto ?? !estado.panelIA;
  $("#panel-ia").hidden = !estado.panelIA;
}
$("#btn-panel-ia").addEventListener("click", () => alternarPanelIA(true));
$("#btn-cerrar-ia").addEventListener("click", () => alternarPanelIA(false));

function agregarMensajeIA(texto, clase) {
  const div = document.createElement("div");
  div.className = `ia-mensaje ${clase || ""}`;
  div.textContent = texto;
  $("#ia-mensajes").appendChild(div);
  $("#ia-mensajes").scrollTop = $("#ia-mensajes").scrollHeight;
  return div;
}

$("#btn-enviar-ia").addEventListener("click", async () => {
  const entrada = $("#ia-entrada");
  const texto = entrada.value.trim();
  if (!texto) return;
  entrada.value = "";
  agregarMensajeIA(texto, "usuario");
  const burbuja = agregarMensajeIA("Pensando…", "ia-ayuda");

  const usarContexto = $("#ia-usar-contexto").checked;
  const contexto = usarContexto && estado.documento ? $("#editor-markdown").value : "";

  try {
    const cuerpo = await jsonFetch(`${API.office}/ia/pregunta`, {
      method: "POST",
      body: JSON.stringify({
        texto,
        contexto,
        usar_local: !$("#ia-proveedor-chip").dataset.externo,
      }),
    });
    burbuja.className = "ia-mensaje";
    burbuja.textContent = cuerpo.datos.respuesta || MFORegistro.ui("sin_respuesta");
    if (!cuerpo.ok) burbuja.classList.add("error");
  } catch (error) {
    burbuja.className = "ia-mensaje error";
    burbuja.textContent = error.message;
  }
});

$("#ia-entrada").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("#btn-enviar-ia").click();
  }
});

/* ─────────────────────────── Configuración IA ─────────────────────────── */
const PROVEEDORES = {
  openai: { modelo: "gpt-4o" },
  anthropic: { modelo: "claude-3-opus" },
  gemini: { modelo: "gemini-1.5-pro" },
};

async function cargarConfigIA() {
  try {
    const cuerpo = await jsonFetch(`${API.office}/ia/config`);
    const cfg = cuerpo.datos;
    $("#ia-base-url").value = cfg.local?.base_url || MFORegistro.ui("ruta_ia_local");
    $("#ia-modelo").value = cfg.local?.default_model || MFORegistro.ui("modelo_ia_local");
    const activos = Object.entries(cfg.external?.providers || {})
      .filter(([, p]) => (p.api_key || "").trim());
    if (activos.length) {
      const [nombre, prov] = activos[0];
      $("#ia-proveedor").value = nombre;
      $("#ia-modelo-ext").value = prov.model || PROVEEDORES[nombre]?.modelo || "";
      $("#ia-clave").value = prov.api_key || "";
    }
    actualizarChipIA();
  } catch (error) { /* config por defecto */ }
}

function actualizarChipIA() {
  const chip = $("#ia-proveedor-chip");
  const proveedor = $("#ia-proveedor").value;
  if (proveedor) {
    chip.textContent = `externo · ${proveedor}`;
    chip.dataset.externo = "1";
  } else {
    chip.textContent = "ollama-local";
    delete chip.dataset.externo;
  }
}
$("#ia-proveedor").addEventListener("change", () => {
  const proveedor = $("#ia-proveedor").value;
  if (proveedor && !$("#ia-modelo-ext").value.trim()) {
    $("#ia-modelo-ext").value = PROVEEDORES[proveedor]?.modelo || "";
  }
  actualizarChipIA();
});

$("#btn-guardar-ia").addEventListener("click", async () => {
  const proveedor = $("#ia-proveedor").value;
  const config = {
    local: {
      enabled: true,
      base_url: $("#ia-base-url").value.trim() || MFORegistro.ui("ruta_ia_local"),
      default_model: $("#ia-modelo").value.trim() || MFORegistro.ui("modelo_ia_local"),
    },
    external: {
      enabled: Boolean(proveedor),
      providers: {},
    },
  };
  if (proveedor) {
    config.external.providers[proveedor] = {
      api_key: $("#ia-clave").value.trim(),
      model: $("#ia-modelo-ext").value.trim() || PROVEEDORES[proveedor]?.modelo,
    };
  }
  try {
    await jsonFetch(`${API.office}/ia/config`, {
      method: "POST",
      body: JSON.stringify({ config }),
    });
    $("#ia-estado").textContent = "✔ Configuración guardada (storage/config_ia.json).";
  } catch (error) {
    $("#ia-estado").textContent = `✖ ${error.message}`;
  }
});

$("#btn-probar-ia").addEventListener("click", async () => {
  try {
    const cuerpo = await jsonFetch(`${API.office}/salud`);
    const ia = cuerpo.datos.ia;
    $("#ia-estado").textContent =
      `Ollama local: ${ia.local ? "✔ disponible" : "✖ no detectado"} · ` +
      `Externo (BYO-key): ${ia.external ? "✔ clave configurada" : "— sin clave"}`;
  } catch (error) {
    $("#ia-estado").textContent = `✖ ${error.message}`;
  }
});

/* ─────────────────────────── Arranque ─────────────────────────── */
function arranque() {
  /* Deep-links: /?app=docs · /?app=word&doc=Nombre&tema=tema3&alin=justificado */
  const params = new URLSearchParams(location.search);
  const APPS = ["documentos", "docs", "word", "pdf", "html", "tablas", "plantillas", "config"];
  const app = params.get("app");
  const doc = params.get("doc");
  const temaParam = params.get("tema");
  const alinParam = params.get("alin");
  const paletaCustomParam = params.get("paleta_custom");
  const seccionParam = params.get("seccion");

  listarDocumentos();
  cargarConfigIA();
  const appInicial = APPS.includes(app) ? app : "documentos";
  if (!doc) {
    abrirApp(appInicial);
  }

  if (doc) {
    abrirDocumento(doc.toLowerCase().endsWith(".md") ? doc : `${doc}.md`, appInicial).then(async () => {
      if (temaParam && $("#word-opt-tema")) {
        $("#word-opt-tema").value = temaParam;
      }
      if (alinParam && $("#word-opt-alineacion")) {
        $("#word-opt-alineacion").value = alinParam;
      }
      if (paletaCustomParam) {
        const cols = paletaCustomParam.split("|");
        if ($("#word-opt-tema")) $("#word-opt-tema").value = "personalizado";
        if ($("#word-sel-modo-color-titulos")) $("#word-sel-modo-color-titulos").value = "personalizado";
        if ($("#word-picker-tit-h1") && cols[0]) $("#word-picker-tit-h1").value = cols[0];
        if ($("#word-picker-tit-h2") && cols[1]) $("#word-picker-tit-h2").value = cols[1];
        if ($("#word-opt-paleta-suave-tablas")) $("#word-opt-paleta-suave-tablas").checked = false;
        if ($("#word-picker-tabla-cabecera") && cols[0]) $("#word-picker-tabla-cabecera").value = cols[0];
        if ($("#word-picker-tabla-filas") && cols[2]) $("#word-picker-tabla-filas").value = cols[2];
        if ($("#word-picker-tabla-borde") && cols[3]) $("#word-picker-tabla-borde").value = cols[3];
      }
      if (seccionParam) {
        const det = document.querySelector(`#sidebar-word-opciones details[data-seccion-id="${seccionParam}"]`);
        if (det) det.open = true;
      }
      if (temaParam || alinParam || paletaCustomParam) {
        guardarOpcionesWord();
        await renderizarHojaWordPreview();
      }
      const pdfPaletaParam = params.get("pdf_paleta");
      if (pdfPaletaParam && $("#pdf-opt-paleta")) {
        const detPdf = document.querySelector("#sidebar-pdf-opciones details.sidebar-seccion");
        if (detPdf) detPdf.open = true;
        $("#pdf-opt-paleta").value = pdfPaletaParam;
        $("#pdf-opt-paleta").dispatchEvent(new Event("change", { bubbles: true }));
      }
      const htmlTemaParam = params.get("html_tema");
      const htmlPaletaParam = params.get("html_paleta");
      const htmlAnchoParam = params.get("html_ancho");
      const htmlFuenteParam = params.get("html_fuente");
      const htmlJustParam = params.get("html_justificado");
      const htmlNumEqParam = params.get("html_num_eq");
      const htmlFooterIzqParam = params.get("html_footer_izq");
      const htmlFooterDerParam = params.get("html_footer_der");
      const htmlSeccionParam = params.get("seccion_html");
      if (htmlSeccionParam) {
        htmlSeccionParam.split(",").forEach((secId) => {
          const detHtml = document.querySelector(`#sidebar-html-opciones details[data-seccion-id="${secId.trim()}"]`);
          if (detHtml) detHtml.open = true;
        });
      }
      let htmlModificado = false;
      if (htmlTemaParam && $("#html-opt-tema")) {
        $("#html-opt-tema").value = htmlTemaParam;
        htmlModificado = true;
      }
      if (htmlPaletaParam && $("#html-opt-paleta")) {
        let optP = $("#html-opt-paleta").querySelector(`option[value="${htmlPaletaParam}"]`);
        if (!optP) {
          optP = document.createElement("option");
          optP.value = htmlPaletaParam;
          optP.textContent = `🎨 ${params.get("html_paleta_nombre") || "Paleta Personalizada"}`;
          $("#html-opt-paleta").appendChild(optP);
        }
        $("#html-opt-paleta").value = htmlPaletaParam;
        htmlModificado = true;
      }
      if (htmlAnchoParam && $("#html-opt-ancho")) {
        $("#html-opt-ancho").value = htmlAnchoParam;
        htmlModificado = true;
      }
      if (htmlFuenteParam && $("#html-opt-fuente")) {
        $("#html-opt-fuente").value = htmlFuenteParam;
        htmlModificado = true;
      }
      if (htmlJustParam !== null && $("#html-opt-justificado")) {
        $("#html-opt-justificado").checked = htmlJustParam === "1" || htmlJustParam === "true";
        htmlModificado = true;
      }
      if (htmlNumEqParam !== null && $("#html-opt-num-eq")) {
        $("#html-opt-num-eq").checked = htmlNumEqParam === "1" || htmlNumEqParam === "true";
        htmlModificado = true;
      }
      if (htmlFooterIzqParam !== null && $("#html-opt-footer-izq")) {
        $("#html-opt-footer-izq").value = htmlFooterIzqParam;
        htmlModificado = true;
      }
      if (htmlFooterDerParam !== null && $("#html-opt-footer-der")) {
        $("#html-opt-footer-der").value = htmlFooterDerParam;
        htmlModificado = true;
      }
      if (htmlModificado) {
        if (window.MFORegistro) {
          MFORegistro.guardarOpciones("html", {
            tema: $("#html-opt-tema")?.value,
            paleta_tricolor: $("#html-opt-paleta")?.value,
            ancho_max: $("#html-opt-ancho")?.value,
            fuente: $("#html-opt-fuente")?.value,
            justificado: $("#html-opt-justificado")?.checked,
            numerar_ecuaciones: $("#html-opt-num-eq")?.checked,
            footer_izq: $("#html-opt-footer-izq")?.value,
            footer_der: $("#html-opt-footer-der")?.value,
          });
        }
        await cargarVisorHtmlDedicado();
      }
    });
  }
}

arranque();
