/* =========================================================================
   MarkFlow AI — plantillas.js
   Lógica interactiva para la suite "Plantillas y Placeholders Dinámicos"
   (Finalidad A: Crear plantilla | Finalidad B: Usar plantilla)
   Evolución v1.9.0:
   - Vista ancha y View Switcher (Dividida, Solo Código, Solo Visual).
   - Edición bidireccional directa en la pantalla renderizada (WYSIWYG).
   - Scroll vertical sincronizado simultáneo.
   - Autoreemplazo global de placeholders repetidos.
   - Etiquetas rojas discretas (sin globos invasivos).
   - Tooltip contextual interactivo para renombrar y eliminar placeholders.
   ========================================================================= */
(() => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  // Estado del flujo A (Crear plantilla)
  let candidatosDetectados = [];
  let textoOrigenMarkdown = "";
  let modoVistaActual = "split"; // "split" | "codigo" | "visual"
  let sincronizandoScroll = false;
  let sincronizandoEdicion = false;
  let placeholderActivoTooltip = null;
  const mapaValoresManuales = {};

  // Estado del flujo B (Usar plantilla)
  let plantillaCargadaMarkdown = "";
  let placeholdersPlantilla = [];
  let datosCargados = { placeholders: [], proyectos: {} };

  // Toast utilitario
  function mostrarToast(msj, tipo = "info") {
    const caja = $("#toasts");
    if (!caja) return;
    const nodo = document.createElement("div");
    nodo.className = `toast ${tipo}`;
    nodo.textContent = msj;
    caja.appendChild(nodo);
    setTimeout(() => {
      nodo.style.opacity = "0";
      setTimeout(() => nodo.remove(), 300);
    }, 4000);
  }

  // Renderizado en vivo con HTML real en la columna izquierda
  let timerRenderHtml = null;
  function actualizarRenderHtmlResultado(mdTexto) {
    const iframe = $("#iframe-preview-html-plantilla");
    if (!iframe) return;

    if (!mdTexto || !mdTexto.trim()) {
      iframe.srcdoc = `<!DOCTYPE html><html><body style="font-family: system-ui, -apple-system, sans-serif; color: #94a3b8; padding: 2.5rem; text-align: center;"><em>El resultado HTML renderizado en vivo aparecerá aquí al cargar o escribir tu documento...</em></body></html>`;
      return;
    }

    clearTimeout(timerRenderHtml);
    timerRenderHtml = setTimeout(async () => {
      try {
        const nomProy = ($("#input-nombre-proyecto-base")?.value || "Documento Base").trim();
        const resp = await fetch("/api/render-preview", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            texto: mdTexto,
            titulo: nomProy,
            tema_html: "defecto"
          })
        });
        const res = await resp.json();
        if (res.ok && res.datos?.html) {
          iframe.srcdoc = res.datos.html;
        }
      } catch (e) {
        console.warn("Aviso en render-preview de plantilla:", e);
      }
    }, 300);
  }

  // ---------------------------------------------------------------------------
  // 1. Inicialización de Sub-Pestañas (Crear vs Usar)
  // ---------------------------------------------------------------------------
  function iniciarSubpestanasPlantilla() {
    const btnCrear = $("#btn-subtab-crear-plantilla");
    const btnUsar = $("#btn-subtab-usar-plantilla");
    const panelCrear = $("#subpanel-crear-plantilla");
    const panelUsar = $("#subpanel-usar-plantilla");

    if (!btnCrear || !btnUsar || !panelCrear || !panelUsar) return;

    function activarSub(modo) {
      const esCrear = modo === "crear";
      btnCrear.classList.toggle("activo", esCrear);
      btnUsar.classList.toggle("activo", !esCrear);
      panelCrear.classList.toggle("activo", esCrear);
      panelUsar.classList.toggle("activo", !esCrear);
    }

    btnCrear.addEventListener("click", () => activarSub("crear"));
    btnUsar.addEventListener("click", () => activarSub("usar"));
  }

  // ---------------------------------------------------------------------------
  // 2. Selector de Modos de Vista (Izquierda: HTML Resultado | Derecha: Placeholders)
  // ---------------------------------------------------------------------------
  function iniciarSelectorModos() {
    const contenedorGrid = $("#grid-editor-plantilla-main");
    const btnsModo = $$(".btn-modo-vista");

    if (!contenedorGrid || btnsModo.length === 0) return;

    function aplicarModo(modo) {
      modoVistaActual = modo;
      btnsModo.forEach((b) => b.classList.toggle("activo", b.dataset.modo === modo));

      contenedorGrid.classList.remove(
        "modo-split", "modo-resultado", "modo-placeholders",
        "modo-codigo", "modo-visual"
      );
      contenedorGrid.classList.add(`modo-${modo}`);

      // Si se pasa a resultado o split, asegurar refresco del HTML renderizado
      if (modo === "split" || modo === "resultado") {
        const md = $("#textarea-plantilla-md")?.value || "";
        actualizarRenderHtmlResultado(md);
      }
    }

    btnsModo.forEach((b) => {
      b.addEventListener("click", () => aplicarModo(b.dataset.modo));
    });

    aplicarModo("split");
  }

  // ---------------------------------------------------------------------------
  // 3. Scroll Sincronizado Simultáneo (Requisito 3)
  // ---------------------------------------------------------------------------
  function iniciarScrollSincronizado() {
    const editor = $("#textarea-plantilla-md");
    const visual = $("#preview-render-plantilla-tags");

    if (!editor || !visual) return;

    editor.addEventListener("scroll", () => {
      if (sincronizandoScroll || modoVistaActual !== "split") return;
      sincronizandoScroll = true;
      sincronizarScrollDeA(editor, visual);
      requestAnimationFrame(() => { sincronizandoScroll = false; });
    });

    visual.addEventListener("scroll", () => {
      if (sincronizandoScroll || modoVistaActual !== "split") return;
      sincronizandoScroll = true;
      sincronizarScrollDeA(visual, editor);
      requestAnimationFrame(() => { sincronizandoScroll = false; });
    });
  }

  function sincronizarScrollDeA(origen, destino) {
    if (!origen || !destino) return;
    const maxOrigen = origen.scrollHeight - origen.clientHeight;
    const maxDestino = destino.scrollHeight - destino.clientHeight;
    if (maxOrigen <= 0 || maxDestino <= 0) return;

    const porcentaje = origen.scrollTop / maxOrigen;
    destino.scrollTop = porcentaje * maxDestino;
  }

  // ---------------------------------------------------------------------------
  // 4. Finalidad A: Carga y Detección de Candidatos
  // ---------------------------------------------------------------------------
  function iniciarFlujoCrear() {
    const zonaSuelta = $("#zona-suelta-plantilla");
    const inputArchivo = $("#entrada-plantilla-md");
    const btnAnalizar = $("#btn-analizar-plantilla-md");
    const textareaMd = $("#textarea-plantilla-md");
    const contadorChars = $("#caracteres-plantilla-md");
    const tarjetaCandidatos = $("#tarjeta-candidatos-plantilla");
    const tbodyCandidatos = $("#tbody-candidatos-plantilla");
    const badgeCandidatos = $("#badge-total-candidatos");
    const btnMarcarTodos = $("#btn-marcar-todos-candidatos");
    const btnSoloAlta = $("#btn-solo-alta-candidatos");
    const btnAplicarCandidatos = $("#btn-aplicar-candidatos-editor");
    const btnConvertirSeleccion = $("#btn-convertir-seleccion-ph");
    const previewTags = $("#preview-render-plantilla-tags");
    const btnGenerarPaquete = $("#btn-generar-paquete-plantilla");

    if (!zonaSuelta || !inputArchivo) return;

    // Manejo de drag and drop
    zonaSuelta.addEventListener("click", () => inputArchivo.click());
    zonaSuelta.addEventListener("dragover", (e) => {
      e.preventDefault();
      zonaSuelta.classList.add("arrastrando");
    });
    zonaSuelta.addEventListener("dragleave", () => zonaSuelta.classList.remove("arrastrando"));
    zonaSuelta.addEventListener("drop", (e) => {
      e.preventDefault();
      zonaSuelta.classList.remove("arrastrando");
      if (e.dataTransfer && e.dataTransfer.files.length > 0) {
        cargarArchivoOrigen(e.dataTransfer.files[0]);
      }
    });

    inputArchivo.addEventListener("change", () => {
      if (inputArchivo.files && inputArchivo.files.length > 0) {
        cargarArchivoOrigen(inputArchivo.files[0]);
      }
    });

    function cargarArchivoOrigen(file) {
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        textoOrigenMarkdown = String(e.target.result || "");
        if (textareaMd) {
          textareaMd.value = textoOrigenMarkdown;
          actualizarContador();
          renderizarPreviewConTags(textoOrigenMarkdown);
        }
        // Refrescar inmediatamente el visor renderizado HTML izquierdo
        actualizarRenderHtmlResultado(textoOrigenMarkdown);

        const inputNom = $("#input-nombre-proyecto-base");
        if (inputNom && file.name) {
          const base = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
          inputNom.value = base.charAt(0).toUpperCase() + base.slice(1);
        }
        ejecutarAnalisisCandidatos(textoOrigenMarkdown);
        mostrarToast(`Archivo cargado: ${file.name}`, "exito");
      };
      reader.onerror = () => {
        mostrarToast("No se pudo leer el archivo Markdown. Verifica la codificación UTF-8.", "error");
      };
      reader.readAsText(file, "UTF-8");
    }

    if (btnAnalizar) {
      btnAnalizar.addEventListener("click", () => {
        const texto = textareaMd ? textareaMd.value.trim() : textoOrigenMarkdown;
        if (!texto) {
          mostrarToast("Pega texto Markdown o carga un archivo primero.", "error");
          return;
        }
        textoOrigenMarkdown = texto;
        ejecutarAnalisisCandidatos(texto);
      });
    }

    async function ejecutarAnalisisCandidatos(markdown) {
      try {
        mostrarToast("Analizando documento con reglas heurísticas...", "info");
        const resp = await fetch("/api/plantillas/analizar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ markdown })
        });
        const res = await resp.json();
        if (!res.ok) {
          throw new Error(res.errores?.[0]?.detalle || "Error analizando documento.");
        }

        candidatosDetectados = res.datos.candidatos || [];
        renderizarTablaCandidatos();
        if (tarjetaCandidatos) tarjetaCandidatos.style.display = "block";
        mostrarToast(`Se detectaron ${candidatosDetectados.length} candidatos a placeholder.`, "exito");
      } catch (err) {
        mostrarToast(`Aviso: ${err.message}`, "error");
      }
    }

    function renderizarTablaCandidatos() {
      if (!tbodyCandidatos) return;
      tbodyCandidatos.innerHTML = "";

      if (badgeCandidatos) {
        badgeCandidatos.textContent = `${candidatosDetectados.length} candidatos`;
      }

      candidatosDetectados.forEach((c, idx) => {
        const tr = document.createElement("tr");
        const chipClase = c.confianza === "alta" ? "chip-accent" : (c.confianza === "media" ? "chip-azul" : "chip-sm");
        const confBadge = `<span class="chip ${chipClase}">${c.confianza}</span>`;

        tr.innerHTML = `
          <td style="text-align: center;">
            <input type="checkbox" data-idx="${idx}" class="chk-candidato" ${c.seleccionado ? "checked" : ""}>
          </td>
          <td><code style="font-size: 0.82rem; background: var(--bg-input); padding: 0.15rem 0.35rem; border-radius: 3px;">${escapeHtml(c.texto_encontrado)}</code></td>
          <td>
            <input type="text" data-idx="${idx}" class="input-tabla-ph input-nom-ph" value="${escapeHtml(c.nombre_sugerido)}">
          </td>
          <td>
            <select data-idx="${idx}" class="select-tabla-ph select-tipo-ph">
              <option value="texto" ${c.tipo_sugerido === "texto" ? "selected" : ""}>texto</option>
              <option value="numero" ${c.tipo_sugerido === "numero" ? "selected" : ""}>numero</option>
              <option value="fecha" ${c.tipo_sugerido === "fecha" ? "selected" : ""}>fecha</option>
              <option value="identificador" ${c.tipo_sugerido === "identificador" ? "selected" : ""}>identificador</option>
              <option value="moneda" ${c.tipo_sugerido === "moneda" ? "selected" : ""}>moneda</option>
            </select>
          </td>
          <td>
            <span style="font-size: 0.8rem; color: var(--text-muted);">${c.unidad_sugerida || "—"}</span>
          </td>
          <td>${confBadge}</td>
          <td style="text-align: center; font-weight: bold;">${c.ocurrencias}</td>
        `;

        tbodyCandidatos.appendChild(tr);
      });

      tbodyCandidatos.querySelectorAll(".chk-candidato").forEach((chk) => {
        chk.addEventListener("change", (e) => {
          const idx = parseInt(e.target.dataset.idx, 10);
          if (candidatosDetectados[idx]) {
            candidatosDetectados[idx].seleccionado = e.target.checked;
          }
        });
      });

      tbodyCandidatos.querySelectorAll(".input-nom-ph").forEach((inp) => {
        inp.addEventListener("input", (e) => {
          const idx = parseInt(e.target.dataset.idx, 10);
          if (candidatosDetectados[idx]) {
            candidatosDetectados[idx].nombre_sugerido = e.target.value.trim().toLowerCase().replace(/[^a-z0-9_]/g, "_");
          }
        });
      });

      tbodyCandidatos.querySelectorAll(".select-tipo-ph").forEach((sel) => {
        sel.addEventListener("change", (e) => {
          const idx = parseInt(e.target.dataset.idx, 10);
          if (candidatosDetectados[idx]) {
            candidatosDetectados[idx].tipo_sugerido = e.target.value;
          }
        });
      });
    }

    if (btnMarcarTodos) {
      btnMarcarTodos.addEventListener("click", () => {
        candidatosDetectados.forEach((c) => c.seleccionado = true);
        renderizarTablaCandidatos();
      });
    }

    if (btnSoloAlta) {
      btnSoloAlta.addEventListener("click", () => {
        candidatosDetectados.forEach((c) => {
          c.seleccionado = (c.confianza === "alta");
        });
        renderizarTablaCandidatos();
      });
    }

    // Aplicar candidatos seleccionados al editor Markdown (con autoreemplazo global)
    if (btnAplicarCandidatos) {
      btnAplicarCandidatos.addEventListener("click", () => {
        let md = textareaMd.value || textoOrigenMarkdown;
        const seleccionados = candidatosDetectados.filter((c) => c.seleccionado);
        if (seleccionados.length === 0) {
          mostrarToast("No hay ningún candidato marcado.", "error");
          return;
        }

        // Ordenar por longitud descendente del texto original para evitar sustituciones parciales
        seleccionados.sort((a, b) => b.texto_encontrado.length - a.texto_encontrado.length);

        let totalReemplazos = 0;
        seleccionados.forEach((c) => {
          const patron = new RegExp(escapeRegExp(c.texto_encontrado), "g");
          const matches = md.match(patron);
          if (matches) totalReemplazos += matches.length;
          md = md.replace(patron, `{{${c.nombre_sugerido}}}`);
        });

        textareaMd.value = md;
        actualizarContador();
        renderizarPreviewConTags(md);
        mostrarToast(`Placeholders aplicados (${totalReemplazos} ocurrencias totales).`, "exito");
      });
    }

    // Requisito 4: Conversión manual con autoreemplazo global de frases repetidas
    if (btnConvertirSeleccion) {
      btnConvertirSeleccion.addEventListener("click", () => {
        let selText = "";
        const selVisual = window.getSelection ? window.getSelection().toString() : "";

        if (selVisual && selVisual.trim()) {
          selText = selVisual.trim();
        } else if (textareaMd) {
          const start = textareaMd.selectionStart;
          const end = textareaMd.selectionEnd;
          selText = textareaMd.value.substring(start, end).trim();
        }

        if (!selText) {
          mostrarToast("Selecciona primero una frase o texto con el ratón (en el código o en la vista visual).", "error");
          return;
        }

        const sugerencia = selText.toLowerCase().replace(/[^a-z0-9_]/g, "_").slice(0, 40) || "nueva_variable";
        const nombreIngresado = prompt(`Convertir todas las apariciones de «${selText}» en placeholder.\nNombre de la variable:`, sugerencia);

        if (nombreIngresado) {
          const limpio = nombreIngresado.trim().toLowerCase().replace(/[^a-z0-9_]/g, "_").slice(0, 60);
          mapaValoresManuales[limpio] = selText;
          const patron = new RegExp(escapeRegExp(selText), "g");
          const coincidencias = (textareaMd.value.match(patron) || []).length;

          // Autoreemplazo global en todo el documento Markdown
          textareaMd.value = textareaMd.value.replace(patron, `{{${limpio}}}`);
          actualizarContador();
          renderizarPreviewConTags(textareaMd.value);
          mostrarToast(`Reemplazadas ${coincidencias} ocurrencias por {{${limpio}}} globalmente.`, "exito");
        }
      });
    }

    // Input en textarea para actualizar contador y render
    if (textareaMd) {
      textareaMd.addEventListener("input", () => {
        if (sincronizandoEdicion) return;
        actualizarContador();
        renderizarPreviewConTags(textareaMd.value);
      });
    }

    function actualizarContador() {
      if (contadorChars && textareaMd) {
        contadorChars.textContent = `${textareaMd.value.length.toLocaleString()} caracteres`;
      }
    }



    // Renderizado visual interactivo WYSIWYG en columna derecha con etiquetas rojas discretas
    function renderizarPreviewConTags(mdTexto) {
      if (!previewTags) return;
      if (!mdTexto) {
        previewTags.innerHTML = `<em style="color: var(--text-muted);">Pega o carga el documento para manipular sus placeholders aquí...</em>`;
        actualizarRenderHtmlResultado("");
        return;
      }

      // Convertir saltos de línea y formateo simple preservando párrafos y tablas
      const htmlEscapado = escapeHtml(mdTexto);

      // Reemplazo a etiquetas sutiles en texto rojo plano
      const conTags = htmlEscapado.replace(
        /(?<!\\)\{\{\s*([a-zA-Z0-9_]{1,60})\s*\}\}/g,
        (match, phNombre) => {
          return `<span class="placeholder-tag-sutil" data-ph="${phNombre}" title="Variable [${phNombre}] — Clic para renombrar o eliminar">${phNombre}</span>`;
        }
      );

      previewTags.innerHTML = conTags;
      iniciarEventosPlaceholdersRojos();
      actualizarRenderHtmlResultado(mdTexto);
    }

    // Edición directa en la pantalla renderizada (WYSIWYG bidireccional)
    if (previewTags) {
      previewTags.addEventListener("input", () => {
        if (sincronizandoEdicion) return;
        sincronizandoEdicion = true;

        // Clonar nodo para extraer texto limpio reconvirtiendo spans a {{nombre}}
        const clon = previewTags.cloneNode(true);
        clon.querySelectorAll(".placeholder-tag-sutil").forEach((span) => {
          const ph = span.dataset.ph || span.textContent.trim();
          span.replaceWith(`{{${ph}}}`);
        });

        const textoReconstruido = clon.innerText || clon.textContent || "";
        textareaMd.value = textoReconstruido;
        actualizarContador();
        actualizarRenderHtmlResultado(textoReconstruido);

        // Liberar bloqueo tras el ciclo
        setTimeout(() => { sincronizandoEdicion = false; }, 50);
      });
    }

    // Requisitos 6 & 7: Interacción al hacer clic en etiquetas rojas (Tooltip minimalista)
    function iniciarEventosPlaceholdersRojos() {
      const tooltip = $("#tooltip-ph-flotante");
      const tags = previewTags.querySelectorAll(".placeholder-tag-sutil");

      tags.forEach((tag) => {
        tag.addEventListener("click", (e) => {
          e.stopPropagation();
          const phNombre = tag.dataset.ph;
          abrirTooltipPlaceholder(tag, phNombre);
        });
      });
    }

    function abrirTooltipPlaceholder(elementoTag, phNombre) {
      const tooltip = $("#tooltip-ph-flotante");
      if (!tooltip) return;

      placeholderActivoTooltip = phNombre;
      const inputNombre = $("#tooltip-ph-input-nombre");
      const lblTitulo = $("#tooltip-ph-titulo-variable");

      if (inputNombre) inputNombre.value = phNombre;
      if (lblTitulo) lblTitulo.textContent = `Variable: {{${phNombre}}}`;

      // Posicionamiento flotante junto al tag
      const rect = elementoTag.getBoundingClientRect();
      const scrollY = window.scrollY || document.documentElement.scrollTop;
      const scrollX = window.scrollX || document.documentElement.scrollLeft;

      tooltip.style.display = "flex";
      tooltip.style.top = `${rect.bottom + scrollY + 6}px`;
      tooltip.style.left = `${Math.max(10, Math.min(rect.left + scrollX - 30, window.innerWidth - 300))}px`;

      if (inputNombre) {
        inputNombre.focus();
        inputNombre.select();
      }
    }

    // Cerrar tooltip al hacer clic fuera
    document.addEventListener("click", (e) => {
      const tooltip = $("#tooltip-ph-flotante");
      if (tooltip && !tooltip.contains(e.target) && !e.target.classList.contains("placeholder-tag-sutil")) {
        tooltip.style.display = "none";
      }
    });

    const btnCerrarTooltip = $("#btn-tooltip-ph-cerrar");
    if (btnCerrarTooltip) {
      btnCerrarTooltip.addEventListener("click", () => {
        $("#tooltip-ph-flotante").style.display = "none";
      });
    }

    // Requisito 7: Renombrar globalmente desde el tooltip
    const btnGuardarRenombrar = $("#btn-tooltip-ph-guardar");
    if (btnGuardarRenombrar) {
      btnGuardarRenombrar.addEventListener("click", () => {
        const inputNombre = $("#tooltip-ph-input-nombre");
        if (!inputNombre || !placeholderActivoTooltip) return;

        const nuevoNombre = inputNombre.value.trim().toLowerCase().replace(/[^a-z0-9_]/g, "_").slice(0, 60);
        if (!nuevoNombre) {
          mostrarToast("Introduce un nombre válido.", "error");
          return;
        }

        const patron = new RegExp(`\\{\\{\\s*${placeholderActivoTooltip}\\s*\\}\\}`, "g");
        const coincidencias = (textareaMd.value.match(patron) || []).length;

        textareaMd.value = textareaMd.value.replace(patron, `{{${nuevoNombre}}}`);
        actualizarContador();
        renderizarPreviewConTags(textareaMd.value);

        $("#tooltip-ph-flotante").style.display = "none";
        mostrarToast(`Variable [${placeholderActivoTooltip}] renombrada a [${nuevoNombre}] en ${coincidencias} ocurrencias.`, "exito");
      });
    }

    // Requisito 6: Eliminar / Deshacer placeholder desde el tooltip
    const btnEliminarPh = $("#btn-tooltip-ph-eliminar");
    if (btnEliminarPh) {
      btnEliminarPh.addEventListener("click", () => {
        if (!placeholderActivoTooltip) return;

        const patron = new RegExp(`\\{\\{\\s*${placeholderActivoTooltip}\\s*\\}\\}`, "g");
        const coincidencias = (textareaMd.value.match(patron) || []).length;

        // Revertir a texto plano original
        textareaMd.value = textareaMd.value.replace(patron, placeholderActivoTooltip);
        actualizarContador();
        renderizarPreviewConTags(textareaMd.value);

        $("#tooltip-ph-flotante").style.display = "none";
        mostrarToast(`Placeholder [${placeholderActivoTooltip}] revertido a texto normal en ${coincidencias} ocurrencias.`, "info");
      });
    }

    // Generar Paquete Oficial (Tarjetas Horizontales estilo Conversión Completa con Iconos Modernos)
    if (btnGenerarPaquete) {
      btnGenerarPaquete.addEventListener("click", async () => {
        const md = textareaMd.value.trim();
        if (!md) {
          mostrarToast("El contenido de la plantilla está vacío.", "error");
          return;
        }
        const nomProyecto = ($("#input-nombre-proyecto-base")?.value || "Proyecto Base").trim();

        // Verificar qué casillas de formato están seleccionadas
        const incMd = $("#chk-paquete-md")?.checked ?? true;
        const incXlsx = $("#chk-paquete-xlsx")?.checked ?? true;
        const incJson = $("#chk-paquete-json")?.checked ?? true;
        const incZip = $("#chk-paquete-zip")?.checked ?? true;

        if (!incMd && !incXlsx && !incJson && !incZip) {
          mostrarToast("Selecciona al menos una casilla de archivo para generar.", "error");
          return;
        }

        try {
          btnGenerarPaquete.disabled = true;
          btnGenerarPaquete.textContent = "⏳ Generando salidas...";

          const resp = await fetch("/api/plantillas/crear-paquete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              nombre_proyecto: nomProyecto,
              markdown: md,
              candidatos: candidatosDetectados,
              valores_manuales: mapaValoresManuales
            })
          });
          const res = await resp.json();
          if (!res.ok) {
            throw new Error(res.errores?.[0]?.detalle || "Error al crear el paquete de plantilla.");
          }

          const datos = res.datos;
          const contDescargas = $("#contenedor-descargas-plantilla");
          const listaArchivos = $("#lista-archivos-plantilla-generados");

          if (contDescargas && listaArchivos) {
            let htmlTarjetas = "";

            if (incMd && datos.plantilla_md) {
              htmlTarjetas += crearTarjetaEntregable({
                formato: "md",
                nombre: datos.plantilla_md.nombre,
                url: datos.plantilla_md.url,
                tamano: datos.plantilla_md.tamano || "4 KB",
                subtitulo: "Plantilla Markdown con variables {{nombre}}",
                permiteVer: true
              });
            }

            if (incXlsx && datos.datos_xlsx) {
              htmlTarjetas += crearTarjetaEntregable({
                formato: "xlsx",
                nombre: datos.datos_xlsx.nombre,
                url: datos.datos_xlsx.url,
                tamano: datos.datos_xlsx.tamano || "12 KB",
                subtitulo: "Hoja de cálculo con variables y columnas por proyecto",
                permiteVer: false
              });
            }

            if (incJson && datos.datos_json) {
              htmlTarjetas += crearTarjetaEntregable({
                formato: "json",
                nombre: datos.datos_json.nombre,
                url: datos.datos_json.url,
                tamano: datos.datos_json.tamano || "3 KB",
                subtitulo: "Esquema estructurado de datos JSON",
                permiteVer: true
              });
            }

            if (incZip && datos.paquete_zip) {
              htmlTarjetas += crearTarjetaEntregable({
                formato: "zip",
                nombre: datos.paquete_zip.nombre,
                url: datos.paquete_zip.url,
                tamano: datos.paquete_zip.tamano || "18 KB",
                subtitulo: "Paquete completo comprimido con todos los archivos",
                permiteVer: false
              });
            }

            listaArchivos.innerHTML = htmlTarjetas;
            contDescargas.style.display = "block";
            contDescargas.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }

          mostrarToast("¡Paquete de plantilla generado correctamente!", "exito");
        } catch (err) {
          mostrarToast(`Error: ${err.message}`, "error");
        } finally {
          btnGenerarPaquete.disabled = false;
          btnGenerarPaquete.textContent = "💾 Crear Plantilla y Generar Salidas";
        }
      });
    }
  }

  // ---------------------------------------------------------------------------
  // 5. Finalidad B: Usar Plantilla (Carga, Validación y Compilación)
  // ---------------------------------------------------------------------------
  function iniciarFlujoUsar() {
    const zonaMd = $("#zona-suelta-usar-md");
    const inputMd = $("#entrada-usar-md");
    const txtNombreMd = $("#txt-nombre-plantilla-cargada");
    const txtMetaMd = $("#txt-meta-plantilla-cargada");
    const chipsPhs = $("#contenedor-chips-placeholders-detectados");

    const zonaDatos = $("#zona-suelta-usar-datos");
    const inputDatos = $("#entrada-usar-datos");
    const txtNombreDatos = $("#txt-nombre-datos-cargados");
    const txtMetaDatos = $("#txt-meta-datos-cargados");
    const chipsProyectos = $("#contenedor-proyectos-datos-detectados");

    const selProyecto = $("#sel-proyecto-usar");
    const btnRevalidar = $("#btn-revalidar-proyecto");
    const btnEjecutar = $("#btn-ejecutar-generacion-plantilla");

    if (!zonaMd || !zonaDatos) return;

    // Carga de Plantilla .md
    zonaMd.addEventListener("click", () => inputMd.click());
    zonaMd.addEventListener("dragover", (e) => { e.preventDefault(); zonaMd.classList.add("arrastrando"); });
    zonaMd.addEventListener("dragleave", () => zonaMd.classList.remove("arrastrando"));
    zonaMd.addEventListener("drop", (e) => {
      e.preventDefault();
      zonaMd.classList.remove("arrastrando");
      if (e.dataTransfer && e.dataTransfer.files.length > 0) cargarPlantillaMd(e.dataTransfer.files[0]);
    });
    inputMd.addEventListener("change", () => {
      if (inputMd.files && inputMd.files.length > 0) cargarPlantillaMd(inputMd.files[0]);
    });

    function cargarPlantillaMd(file) {
      if (!file) return;
      const reader = new FileReader();
      reader.onload = async (e) => {
        plantillaCargadaMarkdown = String(e.target.result || "");
        if (txtNombreMd) txtNombreMd.textContent = file.name;

        try {
          const resp = await fetch("/api/plantillas/extraer-placeholders", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ markdown: plantillaCargadaMarkdown })
          });
          const res = await resp.json();
          if (res.ok) {
            placeholdersPlantilla = res.datos.placeholders || [];
            if (txtMetaMd) txtMetaMd.textContent = `${placeholdersPlantilla.length} placeholders detectados`;
            if (chipsPhs) {
              chipsPhs.innerHTML = placeholdersPlantilla.map(
                (p) => `<span class="chip chip-sm" style="font-family: var(--font-mono);">${p}</span>`
              ).join(" ");
            }
            ejecutarValidacionActual();
            mostrarToast(`Plantilla cargada: ${file.name}`, "exito");
          }
        } catch (err) {
          mostrarToast(`Aviso al leer plantilla: ${err.message}`, "error");
        }
      };
      reader.onerror = () => {
        mostrarToast("No se pudo leer la plantilla Markdown. Verifica la codificación UTF-8.", "error");
      };
      reader.readAsText(file, "UTF-8");
    }

    // Carga de Datos (.xlsx o .json)
    zonaDatos.addEventListener("click", () => inputDatos.click());
    zonaDatos.addEventListener("dragover", (e) => { e.preventDefault(); zonaDatos.classList.add("arrastrando"); });
    zonaDatos.addEventListener("dragleave", () => zonaDatos.classList.remove("arrastrando"));
    zonaDatos.addEventListener("drop", (e) => {
      e.preventDefault();
      zonaDatos.classList.remove("arrastrando");
      if (e.dataTransfer && e.dataTransfer.files.length > 0) cargarDatosArchivo(e.dataTransfer.files[0]);
    });
    inputDatos.addEventListener("change", () => {
      if (inputDatos.files && inputDatos.files.length > 0) cargarDatosArchivo(inputDatos.files[0]);
    });

    async function cargarDatosArchivo(file) {
      if (txtNombreDatos) txtNombreDatos.textContent = file.name;
      const formData = new FormData();
      formData.append("archivo", file);

      try {
        mostrarToast("Leyendo datos del proyecto...", "info");
        const resp = await fetch("/api/plantillas/leer-datos", {
          method: "POST",
          body: formData
        });
        const res = await resp.json();
        if (!res.ok) {
          throw new Error(res.errores?.[0]?.detalle || "Error al leer datos.");
        }

        datosCargados = res.datos;
        const totalProys = datosCargados.total_proyectos || 0;
        if (txtMetaDatos) txtMetaDatos.textContent = `${totalProys} proyectos · ${datosCargados.total_placeholders || 0} variables`;

        if (selProyecto) {
          selProyecto.innerHTML = `<option value="__todos__">🔄 Generar lote (${totalProys} proyectos disponibles)</option>`;
          datosCargados.nombres_proyectos.forEach((nom) => {
            const opt = document.createElement("option");
            opt.value = nom;
            opt.textContent = `📁 ${nom}`;
            selProyecto.appendChild(opt);
          });
        }

        if (chipsProyectos) {
          chipsProyectos.innerHTML = datosCargados.nombres_proyectos.map(
            (p) => `<span class="chip chip-accent chip-sm">${p}</span>`
          ).join(" ");
        }

        ejecutarValidacionActual();
        mostrarToast(`Datos cargados correctamente: ${totalProys} proyectos encontrados.`, "exito");
      } catch (err) {
        mostrarToast(`Error: ${err.message}`, "error");
      }
    }

    if (selProyecto) {
      selProyecto.addEventListener("change", () => ejecutarValidacionActual());
    }

    if (btnRevalidar) {
      btnRevalidar.addEventListener("click", () => ejecutarValidacionActual());
    }

    async function ejecutarValidacionActual() {
      if (!placeholdersPlantilla || placeholdersPlantilla.length === 0) return;
      if (!datosCargados || !datosCargados.proyectos) return;

      const selVal = selProyecto ? selProyecto.value : "__todos__";
      let proyAValidar = selVal;
      if (selVal === "__todos__") {
        proyAValidar = Object.keys(datosCargados.proyectos)[0] || "";
      }

      const datosProy = datosCargados.proyectos[proyAValidar] || {};

      try {
        const resp = await fetch("/api/plantillas/validar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            placeholders: placeholdersPlantilla,
            datos_proyecto: datosProy
          })
        });
        const res = await resp.json();
        if (res.ok) {
          const v = res.datos;
          $("#val-stat-completos").textContent = v.conteo.completos;
          $("#val-stat-vacios").textContent = v.conteo.vacios;
          $("#val-stat-tipo").textContent = v.conteo.tipo_incorrecto;
          $("#val-stat-sobrantes").textContent = v.conteo.sobrantes;

          const detalleEl = $("#detalle-validacion-texto");
          if (detalleEl) {
            let msg = `<strong>${proyAValidar ? `Auditoría para [${proyAValidar}]: ` : ""}</strong>${v.resumen}`;
            if (v.vacios.length > 0) {
              msg += `<br><span style="color: #ef4444;">⚠️ Placeholders sin valor: ${v.vacios.map(p => `<code>[${p}]</code>`).join(", ")}. Se generarán marcados en rojo en el documento final.</span>`;
            }
            detalleEl.innerHTML = msg;
          }
        }
      } catch (err) {
        console.error("Error en validación:", err);
      }
    }

    if (btnEjecutar) {
      btnEjecutar.addEventListener("click", async () => {
        if (!plantillaCargadaMarkdown) {
          mostrarToast("Por favor carga primero la plantilla Markdown (.md).", "error");
          return;
        }
        if (!datosCargados || !datosCargados.proyectos || Object.keys(datosCargados.proyectos).length === 0) {
          mostrarToast("Por favor carga el archivo Excel (.xlsx) o JSON con los datos.", "error");
          return;
        }

        const formatos = [];
        if ($("#chk-usar-formato-html")?.checked) formatos.push("html");
        if ($("#chk-usar-formato-word")?.checked) formatos.push("word");
        if ($("#chk-usar-formato-pdf")?.checked) formatos.push("pdf");
        if ($("#chk-usar-formato-md")?.checked) formatos.push("markdown");
        if ($("#chk-usar-formato-xlsx")?.checked) formatos.push("xlsx");
        if ($("#chk-usar-formato-json")?.checked) formatos.push("json");

        if (formatos.length === 0) {
          mostrarToast("Selecciona al menos un formato de salida.", "error");
          return;
        }

        const selVal = selProyecto ? selProyecto.value : "__todos__";
        const proysSeleccionados = selVal === "__todos__" ? Object.keys(datosCargados.proyectos) : [selVal];

        const opciones = {
          tema_html: $("#sel-tema-html")?.value || "defecto",
          tema_word: $("#sel-tema-word")?.value || "defecto",
          paleta: $("#sel-paleta-word")?.value || "defecto",
          tema_pdf: $("#sel-tema-pdf")?.value || "pizarra_carbon",
        };

        try {
          btnEjecutar.disabled = true;
          btnEjecutar.textContent = "⏳ Compilando documentos...";
          mostrarToast("Iniciando compilación multiformato por proyecto...", "info");

          const resp = await fetch("/api/plantillas/generar-documentos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              plantilla_markdown: plantillaCargadaMarkdown,
              proyectos: datosCargados.proyectos,
              proyectos_seleccionados: proysSeleccionados,
              formatos: formatos,
              opciones: opciones
            })
          });
          const res = await resp.json();
          if (!res.ok) {
            throw new Error(res.errores?.[0]?.detalle || "Error al generar documentos.");
          }

          const datos = res.datos;
          const contResultados = $("#contenedor-resultados-usar-plantilla");
          const listaDocs = $("#lista-documentos-generados-grid");

          if (contResultados && listaDocs) {
            let htmlTarjetas = "";
            datos.generados.forEach((doc) => {
              const subtitulo = `Proyecto: ${escapeHtml(doc.proyecto)}`;
              htmlTarjetas += crearTarjetaEntregable({
                formato: doc.formato,
                nombre: doc.archivo,
                url: doc.url,
                tamano: doc.tamano || "",
                subtitulo: subtitulo,
                permiteVer: doc.formato === "html" || doc.formato === "json"
              });
            });

            listaDocs.innerHTML = htmlTarjetas;
            contResultados.style.display = "block";
            contResultados.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }

          mostrarToast(`¡Se generaron ${datos.total_generados} documentos con éxito!`, "exito");
        } catch (err) {
          mostrarToast(`Error: ${err.message}`, "error");
        } finally {
          btnEjecutar.disabled = false;
          btnEjecutar.textContent = "🚀 Generar Documentos Finales";
        }
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Utilidades auxiliares y componentes de descarga modernos
  // ---------------------------------------------------------------------------
  const svgIconosModernos = {
    docx: `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
    pdf: `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><circle cx="10" cy="13" r="2"/><path d="M14 11v4M14 13h2"/></svg>`,
    html: `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
    md: `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M8 13v4M8 13l2 2 2-2M12 13v4M16 13v4"/></svg>`,
    xlsx: `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>`,
    json: `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6c0-1.1.9-2 2-2h2M4 18c0 1.1.9 2 2 2h2M14 4h2a2 2 0 0 1 2 2M14 20h2a2 2 0 0 0 2-2M9 12h6"/></svg>`,
    zip: `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><line x1="12" y1="11" x2="12" y2="17"/><polyline points="9 14 12 11 15 14"/></svg>`
  };

  function crearTarjetaEntregable({ formato, nombre, url, tamano, subtitulo, permiteVer }) {
    let fNorm = String(formato || "").toLowerCase();
    if (fNorm === "word") fNorm = "docx";
    if (fNorm === "markdown") fNorm = "md";
    if (fNorm === "excel") fNorm = "xlsx";

    const iconoSvg = svgIconosModernos[fNorm] || svgIconosModernos.md;
    const badgeTexto = fNorm.toUpperCase();
    const pesoTexto = tamano ? escapeHtml(tamano) : "—";
    const subTexto = subtitulo ? escapeHtml(subtitulo) : "";

    return `
      <article class="tarjeta-entregable formato-${fNorm}">
        <div class="entregable-icono-box" aria-hidden="true">
          ${iconoSvg}
        </div>
        <div class="entregable-info">
          <div class="entregable-header">
            <span class="badge-formato badge-${fNorm}">${badgeTexto}</span>
            <span class="entregable-peso">${pesoTexto}</span>
          </div>
          <h4 class="entregable-nombre" title="${escapeHtml(nombre)}">${escapeHtml(nombre)}</h4>
          <p class="entregable-desc">${subTexto}</p>
        </div>
        <div class="entregable-acciones">
          <a href="${escapeHtml(url)}" download="${escapeHtml(nombre)}" class="btn-entregable btn-descargar" title="Descargar ${escapeHtml(nombre)}">
            <svg class="icono-btn" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>Descargar</span>
          </a>
          ${permiteVer ? `
          <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="btn-entregable btn-previsualizar" title="Previsualizar">
            <svg class="icono-btn" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            <span>Ver</span>
          </a>` : ""}
        </div>
      </article>
    `;
  }
  function escapeHtml(texto) {
    if (!texto) return "";
    return String(texto)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeRegExp(cadena) {
    return cadena.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  // ---------------------------------------------------------------------------
  // Arranque e inicialización
  // ---------------------------------------------------------------------------
  function iniciarTodo() {
    iniciarSubpestanasPlantilla();
    iniciarSelectorModos();
    iniciarScrollSincronizado();
    iniciarFlujoCrear();
    iniciarFlujoUsar();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarTodo);
  } else {
    iniciarTodo();
  }

  // Exportar al objeto global para la shell Office
  window.MFOPlantillas = {
    abrir: () => {
      // Reajustar vistas
      const grid = $("#grid-editor-plantilla-main");
      if (grid && modoVistaActual === "split") {
        sincronizarScrollDeA($("#textarea-plantilla-md"), $("#preview-render-plantilla-tags"));
      }
    }
  };
})();
