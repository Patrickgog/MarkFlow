/* ═════════════════════════════════════════════════════════════════════════════
   MarkFlow Office — Visor PDF (v1.3.0)
   ─────────────────────────────────────────────────────────────────────────────
   - Biblioteca de entregables: GET /api/office/pdfs (salidas/, más recientes
     primero); el binario se sirve con GET /api/office/pdfs/archivo/<ruta>.
   - Render con pdf.js VENDORIZADO (window.pdfjsLib, build legacy 3.11.174 UMD):
     carga perezosa solo al abrir la app PDF, 100 % local (patrón window.PM).
   - Navegación de páginas y zoom REAL 25–400 % (v1.20.5): cada cambio de zoom
     re-renderiza la página con pdf.js a la nueva escala (jamás CSS transform/scale),
     la hoja crece físicamente y el lienzo muestra barras de desplazamiento.
     100 % = tamaño real de la hoja (1 pt = 96/72 px CSS). Modos «Ajustar página» y
     «Ajustar ancho». Ctrl + rueda sobre la hoja (paso 10 %, conservando el punto
     bajo el cursor), Ctrl + «+»/«−»/«0» con foco en el visor. Las miniaturas quedan
     excluidas del zoom.
   - API pública: window.MFOPDF.abrir() — llamada desde office.js al entrar
     al panel PDF (abrirApp). Sin dependencias externas ni CDN.
   ═════════════════════════════════════════════════════════════════════════════ */
"use strict";

(function () {
  /* ══════════════ Estado del visor ══════════════ */
  let pdfjs = null;          /* window.pdfjsLib tras la carga perezosa */
  let docActual = null;      /* PDFDocumentProxy activo */
  let pagina = 1;            /* página mostrada */
  let zoom = 1.0;            /* escala real (1 = 100 % = tamaño físico de la hoja) */
  let modoAjuste = "pagina"; /* "pagina" | "ancho" | null (zoom manual) */
  let renderEnCurso = null;  /* RenderTask activo (evita solapes) */
  let tokenRender = 0;       /* invalida renders obsoletos ante cambios rápidos */
  let focoPendiente = null;  /* punto a conservar bajo el cursor tras el zoom */
  let rafZoom = 0;           /* coalescencia de renders durante Ctrl + rueda */
  let rutaActual = "";       /* ruta relativa del PDF abierto */
  let renderPendiente = null;/* timer del re-render en resize */
  const ZOOM_MIN = 0.25;
  const ZOOM_MAX = 4.0;
  const ZOOM_PASO = 0.10;    /* 10 % por muesca / pulsación */
  const PX_POR_PT = 96 / 72; /* 100 % = tamaño real en pantalla */
  const MAX_PIXELES_CANVAS = 16777216; /* tope de memoria del lienzo (≈ 4096²) */

  const $ = (sel) => document.querySelector(sel);
  let listaEl, lienzoEl, canvasEl, vacioEl, pagEl, zoomEl, prevBtn, nextBtn,
      zoomInBtn, zoomOutBtn, abrirLink, estadoEl, recargarBtn,
      listaMiniaturasEl, totalMinisEl;

  /* ══════════════ Carga perezosa del vendor (window.pdfjsLib) ══════════════ */
  let promesaPdfjs = null;
  function cargarPdfjs() {
    if (window.pdfjsLib && window.pdfjsWorker) return Promise.resolve(window.pdfjsLib);
    if (promesaPdfjs) return promesaPdfjs;
    promesaPdfjs = new Promise((resolver, rechazar) => {
      const s = document.createElement("script");
      s.src = "/static/vendor/pdfjs/pdf.js";
      s.onload = () => {
        if (window.pdfjsWorker) {
          resolver(window.pdfjsLib);
          return;
        }
        const sw = document.createElement("script");
        sw.src = "/static/vendor/pdfjs/pdf.worker.js";
        sw.onload = () => resolver(window.pdfjsLib);
        sw.onerror = () => resolver(window.pdfjsLib);
        document.head.appendChild(sw);
      };
      s.onerror = () => {
        promesaPdfjs = null;
        rechazar(new Error("No se pudo cargar pdf.js (vendor local)."));
      };
      document.head.appendChild(s);
    });
    return promesaPdfjs;
  }

  function notificar(mensaje, tipo) {
    if (!estadoEl) return;
    estadoEl.textContent = mensaje;
    estadoEl.classList.toggle("nota-error", tipo === "error");
  }

  /* ══════════════ Biblioteca de PDFs ══════════════ */
  async function listarPdfs() {
    if (!listaEl) return;
    listaEl.innerHTML = `<div class="estado-vacio">Buscando PDFs…</div>`;
    try {
      const r = await fetch("/api/office/pdfs");
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const cuerpo = await r.json();
      const pdfs = (cuerpo.datos && cuerpo.datos.pdfs) || [];
      listaEl.innerHTML = "";
      if (!pdfs.length) {
        listaEl.innerHTML = `<div class="estado-vacio">Aún no hay PDFs.<br>
          Genera uno con <strong>MarkFlow clásico → PDF Editorial</strong>.</div>`;
        return;
      }
      for (const pdf of pdfs) {
        const tarjeta = document.createElement("div");
        tarjeta.className = "tarjeta-pdf";
        tarjeta.style.cssText = "display:flex; align-items:center; justify-content:space-between; gap:0.4rem; padding:0.5rem 0.6rem; cursor:pointer;";
        const fecha = new Date(pdf.modificado * 1000).toLocaleString("es");
        tarjeta.innerHTML = `
          <div style="display:flex; align-items:center; gap:0.5rem; min-width:0; flex:1;">
            <span class="tarjeta-pdf-icono">📕</span>
            <span class="tarjeta-pdf-datos" style="min-width:0;">
              <span class="tarjeta-pdf-nombre" style="font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; display:block;">${escapeHtml(pdf.archivo)}</span>
              <span class="tarjeta-pdf-meta" style="font-size:0.75rem; color:var(--text-muted);">${pdf.tamano} · ${fecha}</span>
            </span>
          </div>
          <div style="display:flex; align-items:center; gap:0.3rem;">
            <a href="/api/office/pdfs/archivo/${pdf.ruta}" download="${escapeHtml(pdf.archivo)}" class="btn chico btn-fantasma" title="Descargar PDF" style="padding:0.2rem 0.4rem; text-decoration:none;">⬇</a>
            <button type="button" class="btn chico btn-eliminar-item-pdf" data-ruta="${escapeHtml(pdf.ruta)}" title="Eliminar este PDF" style="padding:0.2rem 0.4rem; color:var(--color-error); border-color:rgba(239,68,68,0.3);">🗑️</button>
          </div>`;

        tarjeta.title = pdf.ruta;
        tarjeta.addEventListener("click", (e) => {
          if (e.target.closest(".btn-eliminar-item-pdf") || e.target.closest("a")) return;
          listaEl.querySelectorAll(".tarjeta-pdf").forEach((t) => t.classList.remove("activa"));
          tarjeta.classList.add("activa");
          abrirPdf(pdf.ruta);
        });

        const btnEliminarItem = tarjeta.querySelector(".btn-eliminar-item-pdf");
        if (btnEliminarItem) {
          btnEliminarItem.addEventListener("click", async (e) => {
            e.stopPropagation();
            if (!confirm(`¿Eliminar definitivamente el archivo "${pdf.archivo}"?`)) return;
            try {
              const resp = await fetch(`/api/office/pdfs/archivo/${pdf.ruta}`, { method: "DELETE" });
              const res = await resp.json();
              if (res.ok) {
                notificar(`PDF eliminado: ${pdf.archivo}`, "info");
                if (rutaActual === pdf.ruta) {
                  docActual = null;
                  rutaActual = "";
                  canvasEl.hidden = true;
                  vacioEl.hidden = false;
                  abrirLink.hidden = true;
                  if (descargarBtn) descargarBtn.hidden = true;
                  if (eliminarBtn) eliminarBtn.hidden = true;
                }
                listarPdfs();
              } else {
                alert(`Error al eliminar: ${res.detail || "Error desconocido"}`);
              }
            } catch (err) {
              alert(`Error de red: ${err.message}`);
            }
          });
        }

        listaEl.appendChild(tarjeta);
      }
      /* Conveniencia: solo abre el último PDF de salidas/ si no hay un documento
         activo en Docs que vaya a compilarse en vivo. */
      const mdActivo = document.querySelector("#editor-markdown")?.value?.trim();
      if (!docActual && !mdActivo && pdfs.length > 0) abrirPdf(pdfs[0].ruta);
    } catch (error) {
      listaEl.innerHTML = `<div class="estado-vacio">No se pudo listar los PDFs: ${error.message}</div>`;
    }
  }

  /* ══════════════ Render de página (re-render real con pdf.js) ══════════════ */
  function escalaDeAjuste(vpBase, modo) {
    const estilo = lienzoEl ? getComputedStyle(lienzoEl) : null;
    const padH = estilo ? parseFloat(estilo.paddingLeft) + parseFloat(estilo.paddingRight) : 32;
    const padV = estilo ? parseFloat(estilo.paddingTop) + parseFloat(estilo.paddingBottom) : 32;
    const anchoDisp = Math.max(200, (lienzoEl?.clientWidth || 750) - padH - 4);
    const altoDisp = Math.max(260, (lienzoEl?.clientHeight || 600) - padV - 4);
    const anchoCss = vpBase.width * PX_POR_PT;
    const altoCss = vpBase.height * PX_POR_PT;
    const porAncho = anchoDisp / anchoCss;
    return modo === "ancho" ? porAncho : Math.min(porAncho, altoDisp / altoCss);
  }

  async function renderPagina() {
    if (!docActual || !pdfjs) return;
    const token = ++tokenRender;
    // Cancelar y esperar el render previo ANTES de redimensionar el lienzo
    // (evita «Cannot use the same canvas during multiple render() operations»).
    if (renderEnCurso) {
      try { renderEnCurso.cancel(); } catch (_) { /* ya finalizado */ }
      try { await renderEnCurso.promise; } catch (_) { /* cancelación esperada */ }
      renderEnCurso = null;
    }
    if (token !== tokenRender) return;

    const num = Math.max(1, Math.min(pagina, docActual.numPages));
    pagina = num;
    try {
      const pag = await docActual.getPage(num);
      if (token !== tokenRender) return;
      const vpBase = pag.getViewport({ scale: 1.0 });
      if (modoAjuste) {
        zoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, escalaDeAjuste(vpBase, modoAjuste)));
      }
      actualizarIndicadorZoom();

      // Tamaño CSS real de la hoja a este zoom y densidad de píxeles física
      const escalaCss = zoom * PX_POR_PT;
      const anchoCss = Math.round(vpBase.width * escalaCss);
      const altoCss = Math.round(vpBase.height * escalaCss);
      let dpr = window.devicePixelRatio || 1;
      const pixeles = anchoCss * altoCss * dpr * dpr;
      if (pixeles > MAX_PIXELES_CANVAS) dpr = Math.sqrt(MAX_PIXELES_CANVAS / (anchoCss * altoCss));

      const viewport = pag.getViewport({ scale: escalaCss * dpr });
      const focoAntes = capturarFoco();
      canvasEl.width = Math.floor(viewport.width);
      canvasEl.height = Math.floor(viewport.height);
      canvasEl.style.setProperty("width", `${anchoCss}px`, "important");
      canvasEl.style.setProperty("height", `${altoCss}px`, "important");
      restaurarFoco(focoAntes);

      const tarea = pag.render({
        canvasContext: canvasEl.getContext("2d"),
        viewport,
      });
      renderEnCurso = tarea;
      await tarea.promise;
      if (renderEnCurso === tarea) renderEnCurso = null;
    } catch (error) {
      if (error && error.name === "RenderingCancelledException") return;
      if (error && error.name === "RenderCanceledException") return;
      notificar(`Error al renderizar la página: ${error.message || error}`, "error");
    }
    pagEl.textContent = `${pagina} / ${docActual.numPages}`;
    actualizarMiniaturaActiva();
  }

  /* ── Conservación del punto bajo el cursor durante el zoom ── */
  function capturarFoco() {
    if (!focoPendiente || !lienzoEl || !canvasEl.offsetWidth) return null;
    const f = focoPendiente;
    focoPendiente = null;
    const relX = (lienzoEl.scrollLeft + f.x - canvasEl.offsetLeft) / canvasEl.offsetWidth;
    const relY = (lienzoEl.scrollTop + f.y - canvasEl.offsetTop) / canvasEl.offsetHeight;
    return { relX, relY, x: f.x, y: f.y };
  }

  function restaurarFoco(foco) {
    if (!foco || !lienzoEl) return;
    lienzoEl.scrollLeft = canvasEl.offsetLeft + foco.relX * canvasEl.offsetWidth - foco.x;
    lienzoEl.scrollTop = canvasEl.offsetTop + foco.relY * canvasEl.offsetHeight - foco.y;
  }

  /* ── Indicador / selector de porcentaje ── */
  function actualizarIndicadorZoom() {
    if (!zoomEl) return;
    const pct = Math.round(zoom * 100);
    if (zoomEl.tagName !== "SELECT") {
      zoomEl.textContent = `${pct} %`;
      return;
    }
    const personal = zoomEl.querySelector('option[data-personal="1"]');
    if (modoAjuste) {
      zoomEl.value = modoAjuste;
      const opt = zoomEl.querySelector(`option[value="${modoAjuste}"]`);
      if (opt) opt.textContent = `${modoAjuste === "ancho" ? "Ajustar ancho" : "Ajustar página"} (${pct} %)`;
      if (personal) personal.remove();
      return;
    }
    zoomEl.querySelectorAll('option[value="pagina"],option[value="ancho"]').forEach((o) => {
      o.textContent = o.value === "ancho" ? "Ajustar ancho" : "Ajustar página";
    });
    const valor = String(Math.round(zoom * 100) / 100);
    const existente = Array.from(zoomEl.options).find(
      (o) => !o.dataset.personal && Math.abs(parseFloat(o.value) - zoom) < 0.005
    );
    if (existente) {
      if (personal) personal.remove();
      zoomEl.value = existente.value;
    } else {
      const opt = personal || document.createElement("option");
      opt.dataset.personal = "1";
      opt.value = valor;
      opt.textContent = `${pct} %`;
      if (!personal) zoomEl.insertBefore(opt, zoomEl.options[2] || null);
      zoomEl.value = valor;
    }
  }

  /** Fija un zoom manual (25–400 %) y re-renderiza; `foco` = punto del lienzo a conservar. */
  function fijarZoom(nuevo, foco) {
    const limitado = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, Math.round(nuevo * 100) / 100));
    if (!modoAjuste && Math.abs(limitado - zoom) < 0.001) return;
    modoAjuste = null;
    zoom = limitado;
    actualizarIndicadorZoom();
    if (foco) focoPendiente = foco;
    if (!docActual) return;
    cancelAnimationFrame(rafZoom);
    rafZoom = requestAnimationFrame(() => renderPagina());
  }

  function fijarModoAjuste(modo) {
    modoAjuste = modo;
    if (lienzoEl) { lienzoEl.scrollTop = 0; lienzoEl.scrollLeft = 0; }
    renderPagina();
  }

  function pasoZoom(direccion, foco) {
    fijarZoom(zoom + direccion * ZOOM_PASO, foco);
  }

  /* ══════════════ Miniaturas de páginas (panel izquierdo) ══════════════ */
  let idGeneracionMiniaturas = 0;

  async function generarMiniaturas() {
    if (!docActual || !listaMiniaturasEl) return;
    const generacionActual = ++idGeneracionMiniaturas;
    listaMiniaturasEl.innerHTML = "";
    if (totalMinisEl) totalMinisEl.textContent = String(docActual.numPages);

    const numTotal = docActual.numPages;
    const items = [];

    for (let i = 1; i <= numTotal; i++) {
      const tarjeta = document.createElement("div");
      tarjeta.className = `pdf-miniatura-tarjeta ${i === pagina ? "activa" : ""}`;
      tarjeta.dataset.pagina = String(i);
      tarjeta.title = `Ir a página ${i}`;

      const canvasMini = document.createElement("canvas");
      canvasMini.className = "pdf-miniatura-lienzo";
      canvasMini.width = 100;
      canvasMini.height = 141;

      const rotulo = document.createElement("span");
      rotulo.className = "pdf-miniatura-rotulo";
      rotulo.textContent = `Pág. ${i}`;

      tarjeta.appendChild(canvasMini);
      tarjeta.appendChild(rotulo);

      tarjeta.addEventListener("click", () => {
        if (pagina !== i) {
          pagina = i;
          renderPagina();
        }
      });

      listaMiniaturasEl.appendChild(tarjeta);
      items.push({ num: i, canvas: canvasMini });
    }

    for (const item of items) {
      if (generacionActual !== idGeneracionMiniaturas || !docActual) break;
      try {
        const pag = await docActual.getPage(item.num);
        const viewport = pag.getViewport({ scale: 0.18 });
        item.canvas.width = Math.floor(viewport.width);
        item.canvas.height = Math.floor(viewport.height);
        const ctx = item.canvas.getContext("2d");
        await pag.render({ canvasContext: ctx, viewport }).promise;
      } catch (err) {
        // Ignorar cancelaciones o fallos menores en thumbnails
      }
    }
  }

  function actualizarMiniaturaActiva() {
    if (!listaMiniaturasEl) return;
    listaMiniaturasEl.querySelectorAll(".pdf-miniatura-tarjeta").forEach((t) => {
      const esActiva = parseInt(t.dataset.pagina, 10) === pagina;
      t.classList.toggle("activa", esActiva);
      if (esActiva) {
        t.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    });
  }

  async function abrirPdf(ruta) {
    if (!pdfjs) {
      try {
        pdfjs = await cargarPdfjs();
        pdfjs.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.js";
      } catch (error) {
        notificar(error.message, "error");
        return;
      }
    }
    rutaActual = ruta;
    notificar("Cargando PDF…");
    try {
      const tarea = pdfjs.getDocument(`/api/office/pdfs/archivo/${ruta}`);
      docActual = await tarea.promise;
    } catch (error) {
      notificar(`No se pudo abrir el PDF: ${error.message || error}`, "error");
      docActual = null;
      return;
    }
    pagina = 1;
    canvasEl.hidden = false;
    vacioEl.hidden = true;
    abrirLink.href = `/api/office/pdfs/archivo/${ruta}`;
    abrirLink.hidden = false;
    if (descargarBtn) {
      descargarBtn.href = `/api/office/pdfs/archivo/${ruta}`;
      descargarBtn.download = ruta.split("/").pop() || "documento.pdf";
      descargarBtn.hidden = false;
    }
    if (eliminarBtn) {
      eliminarBtn.hidden = false;
    }
    prevBtn.disabled = false;
    nextBtn.disabled = false;
    await renderPagina();
    generarMiniaturas();
    notificar(`${rutaActual} · ${docActual.numPages} página(s) · rendered con pdf.js local`);
  }

  /* ══════════════ Controles ══════════════ */
  let descargarBtn = null;
  let eliminarBtn = null;

  function conectarControles() {
    listaEl = $("#lista-pdfs");
    lienzoEl = $("#lienzo-pdf");
    canvasEl = $("#canvas-pdf");
    vacioEl = $("#pdf-vacio");
    pagEl = $("#pdf-pag");
    zoomEl = $("#pdf-zoom");
    prevBtn = $("#pdf-prev");
    nextBtn = $("#pdf-next");
    zoomInBtn = $("#pdf-zoom-in");
    zoomOutBtn = $("#pdf-zoom-out");
    abrirLink = $("#pdf-abrir");
    descargarBtn = $("#pdf-descargar");
    eliminarBtn = $("#pdf-eliminar");
    estadoEl = $("#pdf-estado");
    recargarBtn = $("#btn-recargar-pdfs");
    listaMiniaturasEl = $("#pdf-lista-miniaturas");
    totalMinisEl = $("#pdf-total-minis");

    prevBtn.addEventListener("click", () => { pagina -= 1; renderPagina(); });
    nextBtn.addEventListener("click", () => { pagina += 1; renderPagina(); });
    zoomInBtn.addEventListener("click", () => pasoZoom(+1));
    zoomOutBtn.addEventListener("click", () => pasoZoom(-1));
    if (zoomEl && zoomEl.tagName === "SELECT") {
      zoomEl.addEventListener("change", () => {
        const v = zoomEl.value;
        if (v === "pagina" || v === "ancho") fijarModoAjuste(v);
        else fijarZoom(parseFloat(v));
      });
    }
    recargarBtn.addEventListener("click", () => { docActual = null; listarPdfs(); });

    // Miniaturas: desplazamiento aislado. Ctrl + rueda aquí NO toca el zoom del PDF
    // (no hay manejador de zoom en este panel; el evento no llega al lienzo).
    if (listaMiniaturasEl) {
      listaMiniaturasEl.addEventListener("wheel", (e) => {
        e.stopPropagation();
      }, { passive: true });
    }
    if (lienzoEl) {
      let timerRuedaPdf = null;
      lienzoEl.addEventListener("wheel", (e) => {
        // Ctrl + rueda (o pellizco del trackpad) = zoom real del PDF bajo el cursor
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();   /* bloquea el zoom nativo SOLO sobre la hoja */
          e.stopPropagation();
          if (!docActual) return;
          const unidad = e.deltaMode === 1 ? 33 : (e.deltaMode === 2 ? 400 : 1);
          let muescas = -(e.deltaY * unidad) / 100;
          if (Math.abs(muescas) > 1) muescas = Math.sign(muescas); /* 1 muesca = 10 % */
          const rect = lienzoEl.getBoundingClientRect();
          fijarZoom(zoom + muescas * ZOOM_PASO, { x: e.clientX - rect.left, y: e.clientY - rect.top });
          return;
        }
        const tieneScrollVert = lienzoEl.scrollHeight > lienzoEl.clientHeight + 4;
        if (!tieneScrollVert) {
          e.preventDefault();
          e.stopPropagation();
          if (timerRuedaPdf) return;
          if (e.deltaY > 30 && nextBtn && !nextBtn.disabled) {
            timerRuedaPdf = setTimeout(() => { timerRuedaPdf = null; }, 220);
            nextBtn.click();
          } else if (e.deltaY < -30 && prevBtn && !prevBtn.disabled) {
            timerRuedaPdf = setTimeout(() => { timerRuedaPdf = null; }, 220);
            prevBtn.click();
          }
        } else {
          e.stopPropagation();
        }
      }, { passive: false });

      // Atajos de teclado: solo cuando el visor tiene el foco
      lienzoEl.addEventListener("pointerdown", () => lienzoEl.focus({ preventScroll: true }));
      lienzoEl.addEventListener("keydown", (e) => {
        if (!docActual) return;
        if (e.ctrlKey || e.metaKey) {
          if (e.key === "+" || e.key === "=" || e.code === "NumpadAdd") {
            e.preventDefault(); pasoZoom(+1);
          } else if (e.key === "-" || e.code === "NumpadSubtract") {
            e.preventDefault(); pasoZoom(-1);
          } else if (e.key === "0" || e.code === "Numpad0") {
            e.preventDefault(); fijarModoAjuste("pagina");
          }
          return;
        }
        if (e.key === "PageDown") { e.preventDefault(); nextBtn.click(); }
        else if (e.key === "PageUp") { e.preventDefault(); prevBtn.click(); }
      });
    }

    if (eliminarBtn) {
      eliminarBtn.addEventListener("click", async () => {
        if (!rutaActual) return;
        const nombreArchivo = rutaActual.split("/").pop();
        if (!confirm(`¿Deseas eliminar definitivamente el archivo PDF "${nombreArchivo}"?`)) return;
        try {
          const resp = await fetch(`/api/office/pdfs/archivo/${rutaActual}`, { method: "DELETE" });
          const res = await resp.json();
          if (res.ok) {
            notificar(`PDF eliminado: ${nombreArchivo}`, "info");
            docActual = null;
            rutaActual = "";
            canvasEl.hidden = true;
            vacioEl.hidden = false;
            abrirLink.hidden = true;
            if (descargarBtn) descargarBtn.hidden = true;
            eliminarBtn.hidden = true;
            listarPdfs();
          } else {
            alert(`Error al eliminar: ${res.detail || "Error desconocido"}`);
          }
        } catch (err) {
          alert(`Error de red: ${err.message}`);
        }
      });
    }

    /* Re-render con debounce al redimensionar (el canvas se adapta a dpr/zoom) */
    window.addEventListener("resize", () => {
      if (!docActual || !modoAjuste) return; /* el zoom manual no depende del tamaño */
      clearTimeout(renderPendiente);
      renderPendiente = setTimeout(renderPagina, 180);
    });
  }

  /* ══════════════ Cargar buffer binario en vivo ══════════════ */
  async function cargarDesdeArrayBuffer(buffer, nombre, blobUrl) {
    if (!listaEl) conectarControles();
    if (!pdfjs) {
      try {
        pdfjs = await cargarPdfjs();
        pdfjs.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.js";
      } catch (error) {
        notificar(error.message, "error");
        return;
      }
    }
    const mismoDocumento = rutaActual === "__deeplink__" || rutaActual === (nombre || "documento.pdf");
    rutaActual = nombre || "documento.pdf";
    notificar("Renderizando vista previa PDF en vivo…");
    try {
      const tarea = pdfjs.getDocument({ data: buffer });
      docActual = await tarea.promise;
    } catch (error) {
      notificar(`No se pudo previsualizar PDF: ${error.message || error}`, "error");
      docActual = null;
      return;
    }
    // Recompilación en vivo del mismo documento: se conservan página y zoom
    pagina = mismoDocumento ? Math.min(Math.max(1, pagina), docActual.numPages) : 1;
    canvasEl.hidden = false;
    vacioEl.hidden = true;
    if (blobUrl) {
      abrirLink.href = blobUrl;
      abrirLink.hidden = false;
      if (descargarBtn) {
        descargarBtn.href = blobUrl;
        descargarBtn.download = rutaActual;
        descargarBtn.hidden = false;
      }
    }
    prevBtn.disabled = false;
    nextBtn.disabled = false;
    await renderPagina();
    generarMiniaturas();
    notificar(`${rutaActual} · ${docActual.numPages} página(s) · Vista previa en vivo`);
  }

  /* ══════════════ API pública ══════════════ */
  async function abrir() {
    if (!listaEl) conectarControles();
    listarPdfs();
  }

  /* Deep-link opcional: /?app=pdf&doc=X&pdf_zoom=2&pdf_pag=1 (zoom inicial reproducible) */
  (function aplicarDeepLink() {
    const p = new URLSearchParams(location.search);
    const z = p.get("pdf_zoom");
    if (z === "pagina" || z === "ancho") modoAjuste = z;
    else if (z && !isNaN(parseFloat(z))) {
      modoAjuste = null;
      zoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, parseFloat(z)));
    }
    const pg = parseInt(p.get("pdf_pag") || "", 10);
    if (pg > 0) { pagina = pg; rutaActual = "__deeplink__"; }
  })();

  window.MFOPDF = {
    abrir, abrirPdf, cargarDesdeArrayBuffer,
    fijarZoom: (valor) => fijarZoom(valor),
    fijarModoAjuste: (modo) => fijarModoAjuste(modo),
    obtenerZoom: () => ({ zoom, modoAjuste, pagina }),
  };
})();
