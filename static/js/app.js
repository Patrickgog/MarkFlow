/* =========================================================================
   MarkFlow AI — app.js (Lógica integral de interfaz de usuario)
   Gestión de carga hasta 200 MB, barra de progreso flotante, temas locales,
   historial persistente de rutas, reset total y opciones avanzadas APA 7.
   ========================================================================= */
(() => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const CLAVE_APP = "markflow";
  const LLAVE_HISTORIAL_RUTAS = `${CLAVE_APP}-historial-rutas`;

  let sesiónActual = null;
  let textoSaneado = null;
  let documentosEnMemoria = [];
  let tituloModificadoManualmente = false;

  // ------------------------------------------------------------------ Toasts
  function toast(mensaje, tipo = "info", ms = 4200) {
    const caja = $("#toasts");
    if (!caja) return;
    const nodo = document.createElement("div");
    nodo.className = `toast ${tipo}`;
    nodo.textContent = mensaje;
    caja.appendChild(nodo);
    setTimeout(() => {
      nodo.style.opacity = "0";
      setTimeout(() => nodo.remove(), 300);
    }, ms);
  }

  // ------------------------------------------------------------------- Tema
  const TEMA_LLAVE = `${CLAVE_APP}-tema`;

  function aplicarTema(tema) {
    document.documentElement.dataset.tema = tema;
    localStorage.setItem(TEMA_LLAVE, tema);
    const btnTema = $("#btn-tema");
    if (btnTema) {
      const proximo = tema === "oscuro" ? "claro" : "oscuro";
      btnTema.setAttribute("data-tooltip", `Cambiar a modo ${proximo}`);
      btnTema.setAttribute("aria-label", `Cambiar a modo ${proximo}`);
    }
  }

  function iniciarTema() {
    const guardado = localStorage.getItem(TEMA_LLAVE);
    if (guardado === "claro" || guardado === "oscuro") {
      aplicarTema(guardado);
    }
    const btnTema = $("#btn-tema");
    if (btnTema) {
      btnTema.addEventListener("click", () => {
        const actual = document.documentElement.dataset.tema || "oscuro";
        aplicarTema(actual === "oscuro" ? "claro" : "oscuro");
      });
    }
  }

  // ---------------------------------------------------------------- Pestañas
  function iniciarPestanas() {
    const pestañas = [...document.querySelectorAll(".pestanas .pestaña")];

    function activar(botón) {
      pestañas.forEach((p) => {
        const es = p === botón;
        p.classList.toggle("activa", es);
        p.setAttribute("aria-selected", String(es));
        p.tabIndex = es ? 0 : -1;
        const panelId = p.getAttribute("aria-controls");
        const panel = $("#" + panelId);
        if (panel) panel.classList.toggle("activo", es);
      });
    }

    pestañas.forEach((p) => {
      p.addEventListener("click", () => activar(p));
      p.addEventListener("keydown", (e) => {
        if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
        const k = pestañas.indexOf(p) + (e.key === "ArrowRight" ? 1 : -1);
        const sig = pestañas[(k + pestañas.length) % pestañas.length];
        activar(sig);
        sig.focus();
      });
    });

    // Sub-pestañas Word vs HTML vs PDF en acordeón de configuración
    const subtabs = [
      { btn: $("#btn-subtab-word"), panel: $("#subtab-panel-word") },
      { btn: $("#btn-subtab-html"), panel: $("#subtab-panel-html") },
      { btn: $("#btn-subtab-pdf"), panel: $("#subtab-panel-pdf") },
    ];

    subtabs.forEach((st) => {
      if (st.btn && st.panel) {
        st.btn.addEventListener("click", () => {
          subtabs.forEach((s) => {
            s.btn?.classList.remove("activo");
            s.panel?.classList.remove("activo");
          });
          st.btn.classList.add("activo");
          st.panel.classList.add("activo");
        });
      }
    });
  }

  // ------------------------------------------------------------------ Ripple
  function iniciarRipple() {
    document.querySelectorAll(".btn").forEach((botón) => {
      botón.addEventListener("pointerdown", (e) => {
        const r = botón.getBoundingClientRect();
        const onda = document.createElement("span");
        const lado = Math.max(r.width, r.height);
        onda.className = "ondita";
        onda.style.width = onda.style.height = `${lado}px`;
        onda.style.left = `${e.clientX - r.left - lado / 2}px`;
        onda.style.top = `${e.clientY - r.top - lado / 2}px`;
        botón.appendChild(onda);
        setTimeout(() => onda.remove(), 560);
      });
    });
  }

  // ------------------------------------------------------------- API Helpers
  async function api(ruta, opciones = {}) {
    const respuesta = await fetch(ruta, opciones);
    let cuerpo = {};
    try { cuerpo = await respuesta.json(); } catch { /* sin json */ }
    if (!respuesta.ok) {
      const detalle = cuerpo?.detail;
      const msg = typeof detalle === "object" && detalle
        ? `${detalle.codigo}: ${detalle.detalle ?? ""}`
        : (cuerpo?.detalle ?? `${respuesta.status} error`);
      throw new Error(msg);
    }
    return cuerpo;
  }

  const jsonPOST = (cuerpo) => ({
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });

  // -------------------------------------- Barra de Progreso Flotante
  const overlayProgreso = $("#progreso-flotante");
  const progresoEtapa = $("#progreso-etapa");
  const progresoDetalle = $("#progreso-detalle");
  const progresoBarra = $("#progreso-barra");
  const progresoPorcentaje = $("#progreso-porcentaje");

  function mostrarProgreso(etapa, detalle, porcentaje = 0) {
    if (!overlayProgreso) return;
    overlayProgreso.classList.add("activo");
    overlayProgreso.setAttribute("aria-hidden", "false");
    actualizarProgreso(etapa, detalle, porcentaje);
  }

  function actualizarProgreso(etapa, detalle, porcentaje) {
    if (progresoEtapa) progresoEtapa.textContent = etapa;
    if (progresoDetalle) progresoDetalle.textContent = detalle;
    if (progresoBarra) progresoBarra.style.width = `${Math.min(100, Math.max(0, porcentaje))}%`;
    if (progresoPorcentaje) progresoPorcentaje.textContent = `${Math.round(porcentaje)}%`;
  }

  function ocultarProgreso() {
    if (!overlayProgreso) return;
    overlayProgreso.classList.remove("activo");
    overlayProgreso.setAttribute("aria-hidden", "true");
  }

  // ------------------------------------------------------- Catálogo de Temas
  // ------------------------------------------------------- Catálogo de Temas
  const NOMBRES_TEMAS_HTML = {
    defecto: "Tema Clásico MarkFlow (Limpio y Centrado)",
    Tema1: "Tema 1: Ejecutivo Clásico (Azul Océano)",
    Tema2: "Tema 2: Técnico Moderno (Esmeralda Tecnológico)",
    Tema3: "Tema 3: Editorial Académico (Pizarra Formal)",
    Tema4: "Tema 4: Minimalista Clean (Grafito Carbón)",
    Tema5: "Tema 5: Corporativo Vanguardia (Púrpura Editorial)",
    Tema6: "Tema 6: Industrial Cálido (Ámbar Dorado)",
  };

  const PALETAS_TITULOS_BASE = [
    { valor: "negro", nombre: "Negro Absoluto", colores: ["#000000", "#111111", "#333333"] },
    { valor: "azul", nombre: "Azul Institucional", colores: ["#1E3A8A", "#2563EB", "#3B82F6"] },
    { valor: "corporate-blue", nombre: "Azul Ejecutivo", colores: ["#003366", "#205081", "#4682B4"] },
    { valor: "emerald-tech", nombre: "Esmeralda Académico", colores: ["#046A38", "#1F8A53", "#50C878"] },
    { valor: "slate-modern", nombre: "Pizarra Minimalista", colores: ["#2F4F4F", "#4A6B6B", "#708090"] },
    { valor: "burgundy-classic", nombre: "Vino Tinto Editorial", colores: ["#6B1426", "#85223A", "#A3334D"] },
  ];

  const PALETAS_HTML_BASE = [
    { clave: "tema_default", nombre: "Por Defecto del Tema", colores: ["#0284c7", "#0d9488", "#f1f5f9"] },
    { clave: "oceano_ejecutivo", nombre: "Océano Ejecutivo", colores: ["#1E3A8A", "#3B82F6", "#EFF6FF"] },
    { clave: "bosque_academico", nombre: "Bosque Académico", colores: ["#14532D", "#22C55E", "#F0FDF4"] },
    { clave: "pizarra_minimalista", nombre: "Pizarra Minimalista", colores: ["#1E293B", "#64748B", "#F8FAFC"] },
    { clave: "terracota_editorial", nombre: "Terracota Editorial", colores: ["#7C2D12", "#EA580C", "#FFF7ED"] },
    { clave: "vino_corporativo", nombre: "Vino Tinto Corporativo", colores: ["#581C87", "#9333EA", "#FAF5FF"] },
    { clave: "ambar_dorado", nombre: "Ámbar Dorado", colores: ["#78350F", "#D97706", "#FFFBEB"] },
  ];

  const PALETAS_PDF_BASE = [
    { clave: "pizarra_carbon", nombre: "Pizarra & Carbón", colores: ["#1E293B", "#475569", "#F8FAFC"] },
    { clave: "azul_prusia", nombre: "Azul Prusia & Acero", colores: ["#1E3A5F", "#2B547E", "#F0F4F8"] },
    { clave: "grafito_salvia", nombre: "Grafito & Salvia", colores: ["#1C2E24", "#3F5E4D", "#F4F7F5"] },
    { clave: "onix_burdeos", nombre: "Ónix & Burdeos Imperial", colores: ["#2D1B22", "#5C2C38", "#FAF6F7"] },
    { clave: "negro_papel", nombre: "Negro Puro & Papel", colores: ["#0F172A", "#334155", "#F3F4F6"] },
  ];

  function obtenerPaletasGuardadas() {
    try {
      const raw = localStorage.getItem("markflow_paletas_personalizadas");
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function guardarPaletasGuardadas(lista) {
    try {
      localStorage.setItem("markflow_paletas_personalizadas", JSON.stringify(lista));
    } catch (e) {
      console.warn("No se pudo guardar en localStorage", e);
    }
  }

  function renderizarSwatchesHtml(paletasServidor = null) {
    const contenedor = $("#swatches-html-grid");
    const selOculto = $("#sel-paleta-tricolor");
    if (!contenedor || !selOculto) return;

    const valorActual = selOculto.value || "tema_default";
    let lista = PALETAS_HTML_BASE;
    if (Array.isArray(paletasServidor) && paletasServidor.length > 0) {
      lista = paletasServidor.map((p) => ({
        clave: p.clave,
        nombre: p.nombre.replace(/\s*\([^)]*\)/g, "").trim(),
        colores: [p.primario, p.secundario, p.fondo_suave || "#f1f5f9"],
      }));
    }

    const personalizadas = obtenerPaletasGuardadas();
    const personalizadasHtml = personalizadas.map((p) => ({
      clave: p.valor,
      nombre: p.nombre,
      colores: p.colores.length >= 3 ? [p.colores[0], p.colores[1], p.colores[2]] : [p.colores[0], p.colores[1], "#f8fafc"],
      personalizada: true,
    }));

    const todas = [...lista, ...personalizadasHtml];
    contenedor.innerHTML = "";

    selOculto.innerHTML = "";
    todas.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.clave;
      opt.textContent = p.nombre;
      if (p.clave === valorActual) opt.selected = true;
      selOculto.appendChild(opt);
    });

    todas.forEach((p) => {
      const card = document.createElement("button");
      card.type = "button";
      const esActiva = p.clave === selOculto.value;
      card.className = `swatch-card${esActiva ? " activa" : ""}`;
      card.dataset.clave = p.clave;
      card.title = `${p.nombre}: ${p.colores.join(" / ")}`;

      const dots = document.createElement("span");
      dots.className = "swatch-dots";
      p.colores.forEach((c) => {
        const dot = document.createElement("span");
        dot.className = "swatch-dot";
        dot.style.backgroundColor = c;
        dots.appendChild(dot);
      });

      const label = document.createElement("span");
      label.className = "swatch-label";
      label.textContent = p.nombre;

      card.appendChild(dots);
      card.appendChild(label);

      card.addEventListener("click", () => {
        selOculto.value = p.clave;
        contenedor.querySelectorAll(".swatch-card").forEach((c) => c.classList.remove("activa"));
        card.classList.add("activa");
        selOculto.dispatchEvent(new Event("change"));
      });

      contenedor.appendChild(card);
    });
  }

  function renderizarSwatchesPdf(paletasServidor = null) {
    const contenedor = $("#swatches-pdf-grid");
    const selOculto = $("#sel-paleta-pdf");
    if (!contenedor || !selOculto) return;

    const valorActual = selOculto.value || "pizarra_carbon";
    let lista = PALETAS_PDF_BASE;
    if (Array.isArray(paletasServidor) && paletasServidor.length > 0) {
      lista = paletasServidor.map((p) => ({
        clave: p.clave,
        nombre: p.nombre.replace(/^[^\wáéíóúÁÉÍÓÚñÑ]+/, "").replace(/\s*\([^)]*\)/g, "").trim(),
        colores: [p.primario, p.secundario, p.fondo_suave || "#F8FAFC"],
      }));
    }

    const personalizadas = obtenerPaletasGuardadas();
    const personalizadasPdf = personalizadas.map((p) => ({
      clave: p.valor,
      nombre: p.nombre,
      colores: p.colores.length >= 3 ? [p.colores[0], p.colores[1], p.colores[2]] : [p.colores[0], p.colores[1], "#F8FAFC"],
      personalizada: true,
    }));

    const todas = [...lista, ...personalizadasPdf];
    contenedor.innerHTML = "";

    selOculto.innerHTML = "";
    todas.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.clave;
      opt.textContent = p.nombre;
      if (p.clave === valorActual) opt.selected = true;
      selOculto.appendChild(opt);
    });

    todas.forEach((p) => {
      const card = document.createElement("button");
      card.type = "button";
      const esActiva = p.clave === selOculto.value;
      card.className = `swatch-card${esActiva ? " activa" : ""}`;
      card.dataset.clave = p.clave;
      card.title = `${p.nombre}: ${p.colores.join(" / ")}`;

      const dots = document.createElement("span");
      dots.className = "swatch-dots";
      p.colores.forEach((c) => {
        const dot = document.createElement("span");
        dot.className = "swatch-dot";
        dot.style.backgroundColor = c;
        dots.appendChild(dot);
      });

      const label = document.createElement("span");
      label.className = "swatch-label";
      label.textContent = p.nombre;

      card.appendChild(dots);
      card.appendChild(label);

      card.addEventListener("click", () => {
        selOculto.value = p.clave;
        contenedor.querySelectorAll(".swatch-card").forEach((c) => c.classList.remove("activa"));
        card.classList.add("activa");
        selOculto.dispatchEvent(new Event("change"));
      });

      contenedor.appendChild(card);
    });
  }

  function renderizarSwatchesTitulos() {
    const contenedor = $("#swatches-titulos-grid");
    const selOculto = $("#sel-color-titulos-word");
    if (!contenedor || !selOculto) return;

    const valorActual = (selOculto.value || "negro").toLowerCase();
    const personalizadas = obtenerPaletasGuardadas();
    const todas = [...PALETAS_TITULOS_BASE, ...personalizadas];

    contenedor.innerHTML = "";

    // Sincronizar options del select oculto si hay personalizadas
    Array.from(selOculto.querySelectorAll("option.opcion-personalizada")).forEach((o) => o.remove());
    personalizadas.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.valor;
      opt.textContent = `${p.nombre} (${p.colores[0]})`;
      opt.className = "opcion-personalizada";
      selOculto.appendChild(opt);
    });

    todas.forEach((p) => {
      const card = document.createElement("button");
      card.type = "button";
      const esActiva = p.valor.toLowerCase() === valorActual;
      card.className = `swatch-card${esActiva ? " activa" : ""}`;
      card.dataset.valor = p.valor;
      card.title = `${p.nombre}: ${p.colores.join(" / ")}`;

      const dots = document.createElement("span");
      dots.className = "swatch-dots";
      p.colores.forEach((c) => {
        const dot = document.createElement("span");
        dot.className = "swatch-dot";
        dot.style.backgroundColor = c;
        dots.appendChild(dot);
      });

      const label = document.createElement("span");
      label.className = "swatch-label";
      label.textContent = p.nombre;

      card.appendChild(dots);
      card.appendChild(label);

      // Si es personalizada, permitir borrar
      if (p.personalizada) {
        const btnDel = document.createElement("button");
        btnDel.type = "button";
        btnDel.className = "swatch-btn-del";
        btnDel.textContent = "×";
        btnDel.title = "Eliminar paleta";
        btnDel.addEventListener("click", (e) => {
          e.stopPropagation();
          const restantes = personalizadas.filter((x) => x.valor !== p.valor);
          guardarPaletasGuardadas(restantes);
          if (selOculto.value.toLowerCase() === p.valor.toLowerCase()) {
            selOculto.value = "negro";
          }
          renderizarSwatchesTitulos();
        });
        card.appendChild(btnDel);
      }

      card.addEventListener("click", () => {
        selOculto.value = p.valor;
        contenedor.querySelectorAll(".swatch-card").forEach((c) => c.classList.remove("activa"));
        card.classList.add("activa");
      });

      contenedor.appendChild(card);
    });
  }

  function inicializarCreadorPaleta() {
    const btnToggle = $("#btn-toggle-creador-paleta");
    const panel = $("#panel-creador-paleta");
    const inputNombre = $("#input-nombre-paleta");
    const pickPrim = $("#picker-color-primario");
    const hexPrim = $("#hex-color-primario");
    const pickSec = $("#picker-color-secundario");
    const hexSec = $("#hex-color-secundario");
    const pickAce = $("#picker-color-acento");
    const hexAce = $("#hex-color-acento");
    const btnGuardar = $("#btn-guardar-paleta");

    if (btnToggle && panel) {
      btnToggle.addEventListener("click", () => {
        const abierto = panel.style.display !== "none";
        panel.style.display = abierto ? "none" : "block";
        btnToggle.textContent = abierto ? "＋ Nueva Paleta" : "✕ Cancelar";
      });
    }

    if (pickPrim && hexPrim) {
      pickPrim.addEventListener("input", () => { hexPrim.value = pickPrim.value.toUpperCase(); });
      hexPrim.addEventListener("input", () => {
        const v = hexPrim.value.trim();
        if (/^#[0-9A-Fa-f]{6}$/.test(v)) pickPrim.value = v;
      });
    }

    if (pickSec && hexSec) {
      pickSec.addEventListener("input", () => { hexSec.value = pickSec.value.toUpperCase(); });
      hexSec.addEventListener("input", () => {
        const v = hexSec.value.trim();
        if (/^#[0-9A-Fa-f]{6}$/.test(v)) pickSec.value = v;
      });
    }

    if (pickAce && hexAce) {
      pickAce.addEventListener("input", () => { hexAce.value = pickAce.value.toUpperCase(); });
      hexAce.addEventListener("input", () => {
        const v = hexAce.value.trim();
        if (/^#[0-9A-Fa-f]{6}$/.test(v)) pickAce.value = v;
      });
    }

    if (btnGuardar) {
      btnGuardar.addEventListener("click", () => {
        const nombre = (inputNombre?.value || "").trim() || "Paleta Personalizada";
        const c1 = (pickPrim?.value || "#003366").toUpperCase();
        const c2 = (pickSec?.value || "#4682B4").toUpperCase();
        const c3 = (pickAce?.value || "#10B981").toUpperCase();
        const nueva = {
          valor: `${c1}|${c2}|${c3}`,
          nombre,
          colores: [c1, c2, c3],
          personalizada: true,
        };

        const lista = obtenerPaletasGuardadas();
        lista.push(nueva);
        guardarPaletasGuardadas(lista);

        const selOculto = $("#sel-color-titulos-word");
        if (selOculto) {
          selOculto.value = nueva.valor;
        }

        renderizarSwatchesTitulos();
        renderizarSwatchesHtml();
        renderizarSwatchesPdf();
        toast(`Paleta "${nombre}" de 3 colores creada y aplicada`, "ok");

        if (inputNombre) inputNombre.value = "";
        if (panel) panel.style.display = "none";
        if (btnToggle) btnToggle.textContent = "＋ Nueva Paleta";
      });
    }
  }

  function inicializarControlCuadros() {
    const chkSuave = $("#chk-paleta-suave-tablas");
    const lblSuave = $("#lbl-paleta-tabla");
    const contenedorCustom = $("#contenedor-paleta-cuadros-custom");
    const pickCab = $("#picker-color-tabla-cabecera");
    const hexCab = $("#hex-color-tabla-cabecera");
    const pickFil = $("#picker-color-tabla-filas");
    const hexFil = $("#hex-color-tabla-filas");
    const btnGuardar = $("#btn-guardar-paleta-cuadros");
    const inputNombre = $("#input-nombre-paleta-cuadros");

    function actualizarVisibilidad() {
      const suaveActivo = chkSuave ? chkSuave.checked : true;
      if (lblSuave) lblSuave.style.display = suaveActivo ? "block" : "none";
      if (contenedorCustom) contenedorCustom.style.display = suaveActivo ? "none" : "block";
    }

    if (chkSuave) {
      chkSuave.addEventListener("change", actualizarVisibilidad);
      actualizarVisibilidad();
    }

    if (pickCab && hexCab) {
      pickCab.addEventListener("input", () => { hexCab.value = pickCab.value.toUpperCase(); });
      hexCab.addEventListener("input", () => {
        const v = hexCab.value.trim();
        if (/^#[0-9A-Fa-f]{6}$/.test(v)) pickCab.value = v;
      });
    }

    if (pickFil && hexFil) {
      pickFil.addEventListener("input", () => { hexFil.value = pickFil.value.toUpperCase(); });
      hexFil.addEventListener("input", () => {
        const v = hexFil.value.trim();
        if (/^#[0-9A-Fa-f]{6}$/.test(v)) pickFil.value = v;
      });
    }

    if (btnGuardar) {
      btnGuardar.addEventListener("click", () => {
        const nombre = (inputNombre?.value || "").trim() || "Cuadros Personalizados";
        const cCab = (pickCab?.value || "#1E3A8A").toUpperCase();
        const cFil = (pickFil?.value || "#F0F4F8").toUpperCase();
        try {
          const guardadas = JSON.parse(localStorage.getItem("markflow_paletas_cuadros") || "[]");
          guardadas.push({ nombre, cabecera: cCab, filas: cFil });
          localStorage.setItem("markflow_paletas_cuadros", JSON.stringify(guardadas));
          toast(`Paleta de cuadros "${nombre}" guardada`, "ok");
        } catch (e) {
          console.warn("No se pudo guardar paleta de cuadros", e);
        }
      });
    }

    const selModoTit = $("#sel-modo-color-titulos");
    const seccionSwatches = $("#seccion-swatches-titulos");
    if (selModoTit) {
      selModoTit.addEventListener("change", () => {
        const esPaleta = selModoTit.value === "paleta";
        if (seccionSwatches) {
          seccionSwatches.style.opacity = esPaleta ? "1" : "0.7";
        }
      });
    }
  }

  async function cargarCatalogoTemas() {
    try {
      const respuesta = await api("/api/temas");
      const { temas_html, temas_word, paletas, paletas_tricolor } = respuesta.datos || {};

      // Temas HTML
      const selHtml = $("#sel-tema-html");
      if (selHtml && Array.isArray(temas_html)) {
        selHtml.innerHTML = "";
        temas_html.forEach((t) => {
          const opt = document.createElement("option");
          opt.value = t;
          opt.textContent = NOMBRES_TEMAS_HTML[t] || `Plantilla local: ${t}`;
          selHtml.appendChild(opt);
        });
      }

      // Paletas Tri-Color HTML
      const selTricolor = $("#sel-paleta-tricolor");
      if (selTricolor && Array.isArray(paletas_tricolor) && paletas_tricolor.length > 0) {
        selTricolor.innerHTML = "";
        paletas_tricolor.forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p.clave;
          opt.textContent = `${p.nombre}`;
          selTricolor.appendChild(opt);
        });
      }

      // Temas Word
      const selWord = $("#sel-tema-word");
      const selPaleta = $("#sel-paleta-tabla");
      const avisoWord = $("#aviso-tema-word");

      const actualizarEstadoPaletaWord = () => {
        const val = (selWord?.value || "defecto").toLowerCase();
        const esNativo = ["tema1", "tema2", "tema3"].includes(val);
        const esPersonalizado = val === "personalizado";
        if (selPaleta) {
          selPaleta.disabled = esNativo;
          selPaleta.style.opacity = esNativo ? "0.5" : "1";
        }
        if (avisoWord) {
          avisoWord.style.display = esNativo ? "block" : "none";
        }
        const contColorTitulos = $("#contenedor-color-titulos");
        if (contColorTitulos) {
          contColorTitulos.style.display = esPersonalizado ? "block" : "none";
          if (esPersonalizado) {
            renderizarSwatchesTitulos();
          }
        }
      };

      if (selWord && Array.isArray(temas_word)) {
        selWord.innerHTML = "";
        temas_word.forEach((t) => {
          const opt = document.createElement("option");
          opt.value = t;
          if (t === "defecto") {
            opt.textContent = "Estilo Formal Base (Sobrio sin azul)";
          } else if (t === "personalizado") {
            opt.textContent = "🎨 Tema Personalizado (Habilita paleta y colores)";
          } else {
            opt.textContent = `Tema Nativo: ${t}`;
          }
          selWord.appendChild(opt);
        });
        selWord.addEventListener("change", actualizarEstadoPaletaWord);
      }

      // Paletas suaves
      if (selPaleta && Array.isArray(paletas)) {
        selPaleta.innerHTML = "";
        paletas.forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p.clave;
          opt.textContent = p.nombre;
          selPaleta.appendChild(opt);
        });
      }

      renderizarSwatchesTitulos();
      renderizarSwatchesHtml(paletas_tricolor);
      renderizarSwatchesPdf(respuesta.datos?.paletas_pdf || null);
      inicializarCreadorPaleta();
      inicializarControlCuadros();
      actualizarEstadoPaletaWord();
    } catch (err) {
      console.warn("No se pudo cargar el catálogo de temas:", err);
    }
  }

  // ---------------------------------------- Historial de Rutas de Salida
  function cargarHistorialRutas() {
    const listado = $("#historial-rutas");
    if (!listado) return;
    try {
      const rutas = JSON.parse(localStorage.getItem(LLAVE_HISTORIAL_RUTAS) || "[]");
      listado.innerHTML = "";
      rutas.forEach((r) => {
        const opt = document.createElement("option");
        opt.value = r;
        listado.appendChild(opt);
      });
      if (rutas.length > 0 && !$("#opt-ruta-salida").value) {
        $("#opt-ruta-salida").value = rutas[0];
      }
    } catch { /* ignorar */ }
  }

  function guardarRutaEnHistorial(ruta) {
    if (!ruta || !ruta.trim()) return;
    try {
      let rutas = JSON.parse(localStorage.getItem(LLAVE_HISTORIAL_RUTAS) || "[]");
      rutas = [ruta.trim(), ...rutas.filter((r) => r !== ruta.trim())].slice(0, 10);
      localStorage.setItem(LLAVE_HISTORIAL_RUTAS, JSON.stringify(rutas));
      cargarHistorialRutas();
    } catch { /* ignorar */ }
  }

  async function abrirCarpetaActual() {
    const ruta = $("#opt-ruta-salida").value.trim();
    try {
      await api("/api/abrir-carpeta", jsonPOST({ ruta }));
      toast(ruta ? `Carpeta abierta: ${ruta}` : "Carpeta de salidas abierta", "ok");
      if (ruta) guardarRutaEnHistorial(ruta);
    } catch (err) {
      toast(`No se pudo abrir la carpeta: ${err.message}`, "error");
    }
  }

  // ------------------------------------------------------------------ Editor
  const editor = $("#editor");
  const chipEditor = $("#chip-editor");
  const inputTitulo = $("#opt-titulo");

  function abrirAcordeonEditor() {
    const acordeon = $("#acordeon-editor");
    if (acordeon && !acordeon.open) {
      acordeon.open = true;
    }
  }

  function contarCaracteres() {
    if (editor && chipEditor) {
      chipEditor.textContent = `${editor.value.length} caracteres`;
    }
  }

  if (editor) {
    editor.addEventListener("input", () => {
      contarCaracteres();
      if (editor.value.trim().length > 0) {
        abrirAcordeonEditor();
      }
    });
    editor.addEventListener("paste", () => {
      setTimeout(() => {
        if (editor.value.trim().length > 0) {
          abrirAcordeonEditor();
        }
      }, 50);
    });
  }

  if (inputTitulo) {
    inputTitulo.addEventListener("input", () => {
      tituloModificadoManualmente = inputTitulo.value.trim().length > 0;
    });
  }

  function restablecerSalida() {
    textoSaneado = null;
    const vista = $("#vista-saneado");
    if (vista) vista.textContent = "—";
    const estado = $("#qa-estado");
    if (estado) {
      estado.textContent = "en espera";
      estado.className = "badge neutral";
    }
    const qaf = $("#qa-formulas");
    if (qaf) qaf.textContent = "–";
    const qar = $("#qa-residuo");
    if (qar) qar.textContent = "–";
    const qap = $("#qa-paridad");
    if (qap) qap.textContent = "–";
    const ent = $("#entregables");
    if (ent) ent.innerHTML = "";
  }

  function irASalida() {
    const tabSalida = $("#tab-salida");
    if (tabSalida) tabSalida.click();
  }

  // ----------------------------------------------------------- Drag & Drop
  function iniciarZona() {
    const zona = $("#zona-suelta");
    const entrada = $("#entrada-archivos");
    if (!zona || !entrada) return;

    zona.addEventListener("click", () => entrada.click());
    zona.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); entrada.click(); }
    });
    entrada.addEventListener("change", () => {
      ingestarArchivos([...entrada.files]);
      entrada.value = "";
    });
    ["dragover", "dragenter"].forEach((lote) => zona.addEventListener(lote, (e) => {
      e.preventDefault();
      zona.classList.add("sobre");
    }));
    ["dragleave", "drop"].forEach((lote) => zona.addEventListener(lote, (e) => {
      e.preventDefault();
      zona.classList.remove("sobre");
      if (lote === "drop" && e.dataTransfer?.files?.length) {
        ingestarArchivos([...e.dataTransfer.files]);
      }
    }));
  }

  async function ingestarArchivos(archivos) {
    if (!archivos.length) return;

    mostrarProgreso("Ingestando archivos...", `Cargando ${archivos.length} archivo(s) hasta 200 MB`, 20);

    const formulario = new FormData();
    for (const f of archivos) formulario.append("archivos", f, f.name);

    let datos;
    try {
      actualizarProgreso("Analizando codificación...", "Detectando UTF-8/BOM y reparando mojibake", 50);
      const cuerpo = await api("/api/ingesta", { method: "POST", body: formulario });
      datos = cuerpo.datos;
      sesiónActual = datos.sesion;
    } catch (error) {
      ocultarProgreso();
      toast(error.message, "error", 6000);
      return;
    }

    actualizarProgreso("Estructurando documentos...", "Procesando metadatos y consolidación", 80);

    // Renderizar tarjetas de metadatos por documento
    const docLista = $("#doc-lista");
    if (docLista) {
      for (const doc of datos.documentos) {
        const nodo = document.createElement("div");
        nodo.className = "doc";
        const chips = [];
        chips.push(`<span class="chip">${doc.codificacion}</span>`);
        if (doc.mojibake_reparado) {
          chips.push('<span class="chip">mojibake ✔ reparado</span>');
        }
        nodo.innerHTML =
          `<div class="doc-info"><span class="nombre">📄 ${escapar(doc.nombre)}</span>${chips.join("")}</div>` +
          `<span class="chip">${Math.round(doc.tamano_bytes / 1024)} KB</span>`;
        docLista.appendChild(nodo);

        const avisos = doc.avisos || [];
        avisos.forEach((a) => toast(`${doc.nombre}: ${a}`, "info", 5000));
      }
    }

    // Actualizar nombre inteligente si no fue personalizado
    if (!tituloModificadoManualmente && datos.nombre_sugerido && inputTitulo) {
      inputTitulo.value = datos.nombre_sugerido;
    }

    // Cargar texto combinado en editor
    if (datos.texto_combinado) {
      editor.value = datos.texto_combinado;
      contarCaracteres();
      restablecerSalida();
      abrirAcordeonEditor();
    }

    actualizarProgreso("¡Carga completa!", "Documentos listos para formateo", 100);
    setTimeout(ocultarProgreso, 500);
    toast(`${datos.documentos.length} documento(s) cargados con éxito`, "ok");
  }

  const escapar = (texto) => texto.replace(/[&<>"']/g,
    (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

  // ------------------------------------------------------- Formatear Ahora
  async function formatear() {
    const texto = editor.value;
    if (!texto.trim()) {
      toast("El editor está vacío: pega o arrastra Markdown primero.", "error");
      return;
    }
    const botón = $("#btn-formatear");
    botón.disabled = true;
    mostrarProgreso("Saneando Markdown...", "Normalizando fórmulas y delimitadores matemáticos", 35);
    try {
      const cuerpo = await api("/api/formatear", jsonPOST({ texto }));
      const { datos } = cuerpo;
      textoSaneado = datos.texto;
      editor.value = datos.texto;
      contarCaracteres();
      pintarQA(datos);
      const vista = $("#vista-saneado");
      if (vista) vista.textContent = datos.texto;
      actualizarProgreso("Auditoría completada", "Paridad y calidad verificadas con éxito", 100);
      setTimeout(ocultarProgreso, 450);
      irASalida();
      toast(
        `Formateado: ${datos.formulas} fórmula(s) envuelta(s), residuo ${datos.qa.residuo_dolares}`,
        "ok",
      );
    } catch (error) {
      ocultarProgreso();
      toast(error.message, "error", 5500);
    } finally {
      botón.disabled = false;
    }
  }

  function pintarQA(datos) {
    const ok = datos.qa.ok;
    const estado = $("#qa-estado");
    if (estado) {
      estado.textContent = ok ? "QA aprobado" : "revisar avisos";
      estado.className = `badge ${ok ? "ok" : "error"}`;
    }
    const qaf = $("#qa-formulas");
    if (qaf) qaf.textContent = String(datos.qa.formulas);
    const qar = $("#qa-residuo");
    if (qar) qar.textContent = String(datos.qa.residuo_dolares);
    const qap = $("#qa-paridad");
    if (qap) qap.textContent = ok ? "✔" : "▲";
  }

  // ------------------------------------------------------ Generar Entregables
  async function transformar() {
    if (!textoSaneado || !textoSaneado.trim()) {
      // Si el editor tiene texto pero no se ejecutó "Formatear", usar el texto actual
      if (editor.value.trim()) {
        textoSaneado = editor.value;
      } else {
        toast("Formatea el documento primero o ingresa texto en el editor.", "error");
        return;
      }
    }
    const formatos = [];
    if ($("#fmt-html")?.checked) formatos.push("html");
    if ($("#fmt-docx")?.checked) formatos.push("docx");
    if ($("#fmt-pdf")?.checked) formatos.push("pdf");
    if ($("#fmt-md")?.checked) formatos.push("md");
    if (!formatos.length) {
      toast("Elige al menos un formato (HTML, DOCX, PDF o MD).", "error");
      return;
    }

    const botón = $("#btn-transformar");
    botón.disabled = true;

    const rutaSalida = $("#opt-ruta-salida")?.value.trim() || "";
    if (rutaSalida) guardarRutaEnHistorial(rutaSalida);

    mostrarProgreso("Generando entregables...", "Iniciando compilación de formatos", 15);

    try {
      const payload = {
        texto: textoSaneado,
        titulo: $("#opt-titulo")?.value.trim() || "Documento",
        formatos,
        // Configuración Word
        fuente: $("#opt-fuente")?.value || "Calibri",
        tamanio_pt: parseFloat($("#opt-tamanio")?.value || 11.0),
        interlineado: parseFloat($("#opt-inter")?.value || 1.0),
        alineacion: $("#opt-alineacion")?.value || "justificado",
        fuente_tabla: $("#opt-fuente-tabla")?.value || "heredar",
        normas_apa: $("#chk-apa7")?.checked || false,
        numerar_ecuaciones: $("#chk-numerar-eq")?.checked || false,
        crear_indice: $("#chk-crear-indice")?.checked || false,
        posicion_indice: $("#sel-posicion-indice")?.value || "inicio",
        pie_pagina: $("#opt-pie-pagina")?.value.trim() || "",
        alineacion_pie: $("#sel-alineacion-pie")?.value || "derecha",
        numerar_paginas: $("#chk-numerar-pag")?.checked ?? true,
        tema_word: $("#sel-tema-word")?.value || "defecto",
        color_titulos_word: $("#sel-color-titulos-word")?.value || "negro",
        modo_color_titulos: $("#sel-modo-color-titulos")?.value || "negro",
        paleta_suave_tablas: $("#chk-paleta-suave-tablas") ? $("#chk-paleta-suave-tablas").checked : true,
        color_tabla_cabecera: $("#hex-color-tabla-cabecera")?.value || "",
        color_tabla_filas: $("#hex-color-tabla-filas")?.value || "",
        paleta_tabla: $("#sel-paleta-tabla")?.value || "defecto",
        tamanio_tabla_pt: $("#opt-tamanio-tabla")?.value || "auto",
        // Configuración HTML
        tema_html: $("#sel-tema-html")?.value || "defecto",
        paleta_tricolor: $("#sel-paleta-tricolor")?.value || "defecto",
        ancho_maximo: $("#sel-ancho-html")?.value || "900px",
        footer_izq: $("#opt-footer-izq-html")?.value.trim() || "MarkFlow AI 2026",
        footer_der: $("#opt-footer-der-html")?.value.trim() || "Ing. Patricio Sarmiento Reinoso, Mgst.",
        // Configuración PDF Editorial
        tema_pdf: $("#sel-paleta-pdf")?.value || "pizarra_carbon",
        estilo_maquetacion_pdf: $("#sel-estilo-pdf")?.value || "informe",
        fuente_pdf: $("#opt-fuente-pdf")?.value || "Calibri",
        tamanio_pdf: parseFloat($("#opt-tamanio-pdf")?.value || 11.0),
        interlineado_pdf: parseFloat($("#opt-inter-pdf")?.value || 1.15),
        justificado_pdf: $("#chk-justificado-pdf")?.checked ?? true,
        pie_pagina_pdf: $("#opt-pie-pagina-pdf")?.value.trim() || "",
        alineacion_pie_pdf: $("#sel-alineacion-pie-pdf")?.value || "izquierda",
        numerar_paginas_pdf: $("#chk-numerar-pag-pdf")?.checked ?? true,
        formato_num_pdf: $("#sel-formato-num-pdf")?.value || "pagina_x_de_y",
        alineacion_num_pdf: $("#sel-alineacion-num-pdf")?.value || "derecha",
        running_header_pdf: $("#chk-running-header-pdf")?.checked ?? true,
        running_header_texto: $("#opt-running-header-pdf")?.value?.trim() || "",
        salto_capitulo_pdf: $("#chk-salto-capitulo-pdf")?.checked ?? true,
        modo_diseno_pdf: $("#sel-modo-diseno-pdf")?.value || "estandar",
        firma_nombre: $("#input-firma-nombre")?.value?.trim() || "Ing. Patricio Sarmiento Reinoso, Mgst.",
        firma_cargo: $("#input-firma-cargo")?.value?.trim() || "CONSULTOR",
        indice_al_final: $("#chk-indice-al-final")?.checked ?? true,
        // Rutas
        ruta_salida: rutaSalida,
      };

      actualizarProgreso("Aplicando estilos...", "Procesando ecuaciones vectoriales, tablas y maquetación", 55);

      const cuerpo = await api("/api/transformar", jsonPOST(payload));
      const { datos } = cuerpo;
      sesiónActual = datos.sesion;

      actualizarProgreso("Finalizando entregables...", "Verificando paridad y guardando archivos", 90);

      if (datos.qa && typeof datos.qa.paridad_html === "boolean") {
        const qap = $("#qa-paridad");
        if (qap) qap.textContent = datos.qa.paridad_html ? "✔" : "▲";
      }

      const caja = $("#entregables");
      if (caja) {
        caja.innerHTML = "";
        const svgIconos = {
          docx: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M9 13l1.5 6 2-4 2 4 1.5-6" stroke-linecap="round" stroke-linejoin="round"></path></svg>`,
          pdf: `<svg viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M9 13h2a2 2 0 0 1 0 4H9v-4z" stroke-linecap="round" stroke-linejoin="round"></path><path d="M9 17v2" stroke-linecap="round"></path><path d="M15 13v6" stroke-linecap="round"></path><path d="M15 16h2" stroke-linecap="round"></path></svg>`,
          html: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline><line x1="14" y1="4" x2="10" y2="20"></line></svg>`,
          md: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M7 15V9l3 3 3-3v6M17 11v4M15 13l2 2 2-2"></path></svg>`,
        };
        const badges = {
          docx: "DOCX",
          pdf: "PDF",
          html: "HTML5",
          md: "MARKDOWN",
        };

        for (const g of datos.generados) {
          const nodo = document.createElement("div");
          nodo.className = `tarjeta-entregable formato-${g.formato}`;
          const svg = svgIconos[g.formato] || `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path></svg>`;
          const badgeTxt = badges[g.formato] || g.formato.toUpperCase();
          const tamanoTxt = g.tamano ? ` · ${escapar(g.tamano)}` : "";

          const urlVer = `/api/ver/${datos.sesion}/${g.archivo}`;
          const permiteVisor = g.formato === "html" || g.formato === "pdf";
          nodo.innerHTML = `
            <div class="entregable-icono-box">${svg}</div>
            <div class="entregable-cuerpo">
              <div class="entregable-meta">
                <span class="badge-formato badge-${g.formato}">${badgeTxt}</span>
                <span class="entregable-tamano">${tamanoTxt}</span>
              </div>
              <div class="entregable-nombre" title="${escapar(g.archivo)}">${escapar(g.archivo)}</div>
              <div class="entregable-acciones">
                <a href="${g.url}" download class="btn btn-primario chico" title="Descargar entregable">
                  ⭳ Descargar
                </a>
                ${permiteVisor ? `<button type="button" class="btn btn-fantasma chico btn-ver-modal" data-url="${urlVer}" data-titulo="${escapar(g.archivo)}" title="Previsualizar en visor flotante">👁️ Ver</button>` : ""}
              </div>
            </div>
          `;
          caja.appendChild(nodo);
        }

        // Conectar eventos de visor flotante
        caja.querySelectorAll(".btn-ver-modal").forEach((btn) => {
          btn.addEventListener("click", () => {
            const u = btn.getAttribute("data-url");
            const t = btn.getAttribute("data-titulo");
            abrirVisorFlotante(u, t);
          });
        });
      }

      actualizarProgreso("¡Entregables listos!", "Descarga disponible", 100);
      setTimeout(ocultarProgreso, 500);
      toast(`${datos.generados.length} entregable(s) generados exitosamente`, "ok");
    } catch (error) {
      ocultarProgreso();
      toast(error.message, "error", 6000);
    } finally {
      botón.disabled = false;
    }
  }

  // ---------------------------------------------------- Reset Total (Limpiar)
  function limpiarTodo() {
    editor.value = "";
    textoSaneado = null;
    documentosEnMemoria = [];
    tituloModificadoManualmente = false;

    if (inputTitulo) inputTitulo.value = "";
    contarCaracteres();
    restablecerSalida();

    const docLista = $("#doc-lista");
    if (docLista) docLista.innerHTML = "";

    ocultarProgreso();
    const tabDatos = $("#tab-datos");
    if (tabDatos) tabDatos.click();

    toast("Sesión y datos restablecidos por completo", "info");
  }

  async function copiar() {
    if (!textoSaneado) {
      toast("Aún no hay texto saneado para copiar.", "info");
      return;
    }
    await navigator.clipboard.writeText(textoSaneado);
    toast("Markdown saneado copiado al portapapeles", "ok");
  }

  // ---------------------------------------------------- Modal Visor Flotante
  function abrirVisorFlotante(url, titulo) {
    const modal = $("#modal-visor");
    const iframe = $("#modal-visor-iframe");
    const titEl = $("#modal-visor-titulo");
    const linkExt = $("#modal-visor-link-externo");

    if (!modal || !iframe) return;

    if (titEl) titEl.textContent = titulo || "Vista previa del entregable";
    if (linkExt) linkExt.href = url;
    iframe.src = url;

    modal.classList.add("activo");
    modal.setAttribute("aria-hidden", "false");
  }

  function cerrarVisorFlotante() {
    const modal = $("#modal-visor");
    const iframe = $("#modal-visor-iframe");
    if (!modal) return;

    modal.classList.remove("activo");
    modal.setAttribute("aria-hidden", "true");
    if (iframe) iframe.src = "about:blank";
  }

  // ---------------------------------------------------------------- Arranque
  document.addEventListener("DOMContentLoaded", () => {
    iniciarTema();
    iniciarPestanas();
    iniciarRipple();
    iniciarZona();
    cargarCatalogoTemas();
    cargarHistorialRutas();

    // Eventos del visor flotante
    $("#modal-visor-cerrar")?.addEventListener("click", cerrarVisorFlotante);
    $("#modal-visor")?.addEventListener("click", (e) => {
      if (e.target.id === "modal-visor") {
        cerrarVisorFlotante();
      }
    });
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        cerrarVisorFlotante();
      }
    });

    // Eventos de botones
    $("#btn-formatear")?.addEventListener("click", formatear);
    $("#btn-limpiar")?.addEventListener("click", () => {
      editor.value = "";
      contarCaracteres();
      toast("Editor limpio", "info");
    });
    $("#btn-transformar")?.addEventListener("click", transformar);
    $("#btn-reset")?.addEventListener("click", limpiarTodo);
    $("#btn-reset-global")?.addEventListener("click", limpiarTodo);
    $("#btn-copiar")?.addEventListener("click", copiar);
    $("#btn-abrir-carpeta")?.addEventListener("click", abrirCarpetaActual);

    // Reinicio seguro del servidor backend
    const btnReiniciar = $("#btn-reiniciar-servidor");
    if (btnReiniciar) {
      btnReiniciar.addEventListener("click", async () => {
        if (!confirm("¿Deseas reiniciar el servidor backend de MarkFlow AI?")) return;
        try {
          toast("Reiniciando servidor backend...", "info", 3000);
          await api("/api/reiniciar", { method: "POST" });
        } catch (e) {
          // El cierre de conexión inmediato es normal durante el reinicio
        }
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      });
    }

    // Toggle de contenedor de posición de índice
    const chkIndice = $("#chk-crear-indice");
    const contPosIndice = $("#contenedor-posicion-indice");
    if (chkIndice && contPosIndice) {
      chkIndice.addEventListener("change", () => {
        contPosIndice.style.display = chkIndice.checked ? "block" : "none";
      });
    }

    // Toggle de Running Header en PDF
    const chkRunningHeader = $("#chk-running-header-pdf");
    const contRunningHeader = $("#contenedor-running-header-pdf");
    const inputRunningHeader = $("#opt-running-header-pdf");
    if (chkRunningHeader && contRunningHeader) {
      chkRunningHeader.addEventListener("change", () => {
        contRunningHeader.style.display = chkRunningHeader.checked ? "block" : "none";
        if (chkRunningHeader.checked && inputRunningHeader && !inputRunningHeader.value.trim()) {
          inputRunningHeader.value = $("#opt-titulo")?.value.trim() || "Documento";
        }
      });
    }

    // Modales de Firma e Índice al Final
    const modalFirma = $("#modal-firma");
    const btnAbrirFirma = $("#btn-abrir-modal-firma");
    const btnCerrarFirma = $("#modal-firma-cerrar");
    const btnGuardarFirma = $("#btn-firma-guardar");
    const btnLimpiarFirma = $("#btn-firma-limpiar");

    if (btnAbrirFirma && modalFirma) {
      btnAbrirFirma.addEventListener("click", () => {
        modalFirma.classList.add("activo");
      });
    }
    if (btnCerrarFirma && modalFirma) {
      btnCerrarFirma.addEventListener("click", () => {
        modalFirma.classList.remove("activo");
      });
    }
    if (btnGuardarFirma && modalFirma) {
      btnGuardarFirma.addEventListener("click", () => {
        modalFirma.classList.remove("activo");
        const nom = $("#input-firma-nombre")?.value.trim();
        toast(nom ? `Firma guardada: ${nom}` : "Datos de firma actualizados", "ok");
      });
    }
    if (btnLimpiarFirma) {
      btnLimpiarFirma.addEventListener("click", () => {
        if ($("#input-firma-nombre")) $("#input-firma-nombre").value = "";
        if ($("#input-firma-cargo")) $("#input-firma-cargo").value = "";
        toast("Datos de firma borrados", "info");
      });
    }

    const modalIndice = $("#modal-indice-final");
    const btnAbrirIndice = $("#btn-abrir-modal-indice-final");
    const btnCerrarIndice = $("#modal-indice-cerrar");
    const btnGuardarIndice = $("#btn-indice-guardar");

    if (btnAbrirIndice && modalIndice) {
      btnAbrirIndice.addEventListener("click", () => {
        modalIndice.classList.add("activo");
      });
    }
    if (btnCerrarIndice && modalIndice) {
      btnCerrarIndice.addEventListener("click", () => {
        modalIndice.classList.remove("activo");
      });
    }
    if (btnGuardarIndice && modalIndice) {
      btnGuardarIndice.addEventListener("click", () => {
        modalIndice.classList.remove("activo");
        const activo = $("#chk-indice-al-final")?.checked;
        toast(activo ? "Índice al final activado" : "Índice al final desactivado", "ok");
      });
    }

    // Modal Split-View (Editor Interactivo + Render en Vivo con Barra Estilo Word)
    const modalSplitview = $("#modal-splitview");
    const btnAbrirSplitview = $("#btn-abrir-splitview");
    const btnCerrarSplitview = $("#modal-splitview-cerrar");
    const splitviewTextarea = $("#splitview-textarea");
    const splitviewEditorVisual = $("#splitview-editor-visual");
    const splitviewContenedorRender = $("#splitview-contenedor-render");
    const splitviewSelectorVista = $("#splitview-selector-vista");
    const splitviewPanelEditor = $("#splitview-panel-editor");
    const splitviewPanelPreview = $("#splitview-panel-preview");
    const splitviewCaracteres = $("#splitview-caracteres");
    const splitviewEstadoRender = $("#splitview-estado-render");
    const btnSplitviewGuardar = $("#btn-splitview-guardar");
    const btnSplitviewExportar = $("#btn-splitview-exportar-md");

    // Controles de Barra de Herramientas Estilo Word
    const tbEstiloParrafo = $("#tb-estilo-parrafo");
    const tbBtnNegrita = $("#tb-btn-negrita");
    const tbBtnCursiva = $("#tb-btn-cursiva");
    const tbBtnTachado = $("#tb-btn-tachado");
    const tbBtnCodigo = $("#tb-btn-codigo");
    const tbBtnEnlace = $("#tb-btn-enlace");
    const tbBtnListaVinetas = $("#tb-btn-lista-vinetas");
    const tbBtnListaNum = $("#tb-btn-lista-num");
    const tbBtnListaTareas = $("#tb-btn-lista-tareas");
    const tbBtnNota = $("#tb-btn-nota");
    const tbBtnLimpiarNotas = $("#tb-btn-limpiar-notas");
    const tbBtnTabla = $("#tb-btn-tabla");
    const tbBtnImagen = $("#tb-btn-imagen");

    let markdownContent = "";
    let timerRenderSplitview = null;
    let abortControllerRender = null;
    let sincronizandoDesdeCodigo = false;

    // Función auxiliar para contar figuras existentes en el documento
    function calcularSiguienteNumeroFigura(texto) {
      const figurasEncontradas = texto.match(/Figura\s+(\d+)/gi);
      if (!figurasEncontradas || figurasEncontradas.length === 0) return 1;
      let maxNum = 0;
      figurasEncontradas.forEach((f) => {
        const m = f.match(/Figura\s+(\d+)/i);
        if (m) {
          const val = parseInt(m[1], 10);
          if (val > maxNum) maxNum = val;
        }
      });
      return maxNum + 1;
    }

    // Inserción de imagen con referencia compacta en el cuerpo y Base64 al final del documento
    function insertarImagenBase64EnEditor(dataUri) {
      if (!splitviewTextarea) return;
      const textoDoc = splitviewTextarea.value || "";
      const numFig = calcularSiguienteNumeroFigura(textoDoc);
      const refId = `fig${numFig}`;
      const refEnCuerpo = `\n\n![Figura ${numFig}: [Descripción o título de la figura]][${refId}]\n\n`;
      const defAlFinal = `\n\n[${refId}]: ${dataUri}\n`;

      const start = splitviewTextarea.selectionStart || splitviewTextarea.value.length;
      const end = splitviewTextarea.selectionEnd || splitviewTextarea.value.length;
      const antes = splitviewTextarea.value.substring(0, start);
      const despues = splitviewTextarea.value.substring(end);
      splitviewTextarea.value = (antes + refEnCuerpo + despues).trimEnd() + defAlFinal;
      markdownContent = splitviewTextarea.value;
      splitviewTextarea.selectionStart = splitviewTextarea.selectionEnd = start + refEnCuerpo.length;
      splitviewTextarea.dispatchEvent(new Event("input"));

      clearTimeout(timerRenderSplitview);
      actualizarRenderEnVivo();
      toast(`Figura ${numFig} referenciada limpiamente en el texto; código Base64 alojado al final del archivo`, "ok");
    }

    // Manejador del evento 'paste' para interceptar imágenes del portapapeles
    function manejarPegadoImagen(e) {
      const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
          e.preventDefault();
          const file = items[i].getAsFile();
          const reader = new FileReader();
          reader.onload = (event) => {
            insertarImagenBase64EnEditor(event.target.result);
          };
          reader.readAsDataURL(file);
          break;
        }
      }
    }

    if (splitviewTextarea) {
      splitviewTextarea.addEventListener("paste", manejarPegadoImagen);
    }
    if (editor) {
      editor.addEventListener("paste", (e) => {
        const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items;
        if (!items) return;
        for (let i = 0; i < items.length; i++) {
          if (items[i].type.indexOf("image") !== -1) {
            e.preventDefault();
            const file = items[i].getAsFile();
            const reader = new FileReader();
            reader.onload = (event) => {
              const numFig = calcularSiguienteNumeroFigura(editor.value);
              const refId = `fig${numFig}`;
              const refEnCuerpo = `\n\n![Figura ${numFig}: [Descripción o título de la figura]][${refId}]\n\n`;
              const defAlFinal = `\n\n[${refId}]: ${event.target.result}\n`;
              const start = editor.selectionStart || editor.value.length;
              const antes = editor.value.substring(0, start);
              const despues = editor.value.substring(editor.selectionEnd || start);
              editor.value = (antes + refEnCuerpo + despues).trimEnd() + defAlFinal;
              editor.selectionStart = editor.selectionEnd = start + refEnCuerpo.length;
              editor.dispatchEvent(new Event("input"));
              toast(`Figura ${numFig} referenciada limpiamente en el texto; código Base64 alojado al final del archivo`, "ok");
            };
            reader.readAsDataURL(file);
            break;
          }
        }
      });
    }

    // Aplicar transformación universal en el textarea Markdown (SSOT)
    function aplicarFormato(prefijo, sufijo = "", comandoVisual = null, argVisual = null, envolverLineas = false) {
      if (!splitviewTextarea) return;
      const t = splitviewTextarea;
      const start = t.selectionStart;
      const end = t.selectionEnd;
      const sel = t.value.substring(start, end);

      if (envolverLineas) {
        const lineas = (sel || "Texto de ejemplo").split("\n");
        const transformado = lineas.map((l) => `${prefijo}${l}${sufijo}`).join("\n");
        t.value = t.value.substring(0, start) + transformado + t.value.substring(end);
        t.selectionStart = start;
        t.selectionEnd = start + transformado.length;
      } else {
        const reemplazo = `${prefijo}${sel || "texto"}${sufijo}`;
        t.value = t.value.substring(0, start) + reemplazo + t.value.substring(end);
        t.selectionStart = start + prefijo.length;
        t.selectionEnd = start + reemplazo.length - sufijo.length;
      }
      markdownContent = t.value;
      t.focus();
      t.dispatchEvent(new Event("input"));
      clearTimeout(timerRenderSplitview);
      timerRenderSplitview = setTimeout(actualizarRenderEnVivo, 80);
    }



    // Sincronización de Scroll Simultáneo entre Código y Visual
    let esScrollBloqueado = false;
    if (splitviewTextarea && splitviewContenedorRender) {
      splitviewTextarea.addEventListener("scroll", () => {
        if (esScrollBloqueado) return;
        esScrollBloqueado = true;
        const maxText = splitviewTextarea.scrollHeight - splitviewTextarea.clientHeight;
        if (maxText > 0) {
          const ratio = splitviewTextarea.scrollTop / maxText;
          const maxRender = splitviewContenedorRender.scrollHeight - splitviewContenedorRender.clientHeight;
          splitviewContenedorRender.scrollTop = ratio * maxRender;
        }
        setTimeout(() => { esScrollBloqueado = false; }, 30);
      });

      splitviewContenedorRender.addEventListener("scroll", () => {
        if (esScrollBloqueado) return;
        esScrollBloqueado = true;
        const maxRender = splitviewContenedorRender.scrollHeight - splitviewContenedorRender.clientHeight;
        if (maxRender > 0) {
          const ratio = splitviewContenedorRender.scrollTop / maxRender;
          const maxText = splitviewTextarea.scrollHeight - splitviewTextarea.clientHeight;
          splitviewTextarea.scrollTop = ratio * maxText;
        }
        setTimeout(() => { esScrollBloqueado = false; }, 30);
      });
    }

    // Actualización de Render en Vivo (Código -> Visual de Solo Lectura)
    async function actualizarRenderEnVivo() {
      if (!splitviewTextarea) return;
      sincronizandoDesdeCodigo = true;
      const texto = splitviewTextarea.value;
      markdownContent = texto;
      if (splitviewCaracteres) splitviewCaracteres.textContent = `${texto.length} caracteres`;
      if (splitviewEstadoRender) splitviewEstadoRender.textContent = "Compilando...";

      if (abortControllerRender) {
        abortControllerRender.abort();
      }
      abortControllerRender = new AbortController();
      const currentSignal = abortControllerRender.signal;

      try {
        const tit = $("#opt-titulo")?.value.trim() || "Documento";
        const payload = {
          texto,
          titulo: tit,
          tema_html: $("#sel-tema-html")?.value || "defecto",
          paleta_tricolor: $("#sel-paleta-tricolor")?.value || "tema_default",
          fuente: $("#opt-fuente")?.value || "system-ui",
          numerar_ecuaciones: $("#chk-numerar-eq")?.checked || false,
        };
        const res = await api("/api/render-preview", {
          ...jsonPOST(payload),
          signal: currentSignal,
        });
        if (res.ok && res.datos) {
          if (splitviewEditorVisual) {
            const parser = new DOMParser();
            const docHTML = parser.parseFromString(res.datos.html, "text/html");
            const cuerpoContenido = docHTML.body ? docHTML.body.innerHTML : res.datos.html;
            splitviewEditorVisual.innerHTML = cuerpoContenido;

            // Renderizado dinámico de KaTeX
            if (window.renderMathInElement) {
              window.renderMathInElement(splitviewEditorVisual, {
                delimiters: [
                  { left: "$$", right: "$$", display: true },
                  { left: "$", right: "$", display: false },
                  { left: "\\(", right: "\\)", display: false },
                  { left: "\\[", right: "\\]", display: true },
                ],
                throwOnError: false,
              });
            }

            // Renderizado dinámico de diagramas Mermaid
            if (window.mermaid) {
              try {
                const nodosMermaid = splitviewEditorVisual.querySelectorAll(".mermaid, pre.mermaid");
                nodosMermaid.forEach((n) => {
                  let c = (n.textContent || "").trim();
                  if (c) {
                    if (window.sanearCodigoMermaid) {
                      n.textContent = window.sanearCodigoMermaid(c);
                    } else {
                      c = c.replace(/(\]|\)|\}|>|\w)\s+:::/g, "$1:::").replace(/\s+:::/g, ":::");
                      c = c.replace(/<=/g, "≤").replace(/>=/g, "≥");
                      n.textContent = c;
                    }
                  }
                });
                window.mermaid.run({ nodes: nodosMermaid }).catch(() => {});
                document.querySelectorAll('[id^="dmermaid-"], .error-icon').forEach(d => d.remove());
              } catch (eMermaid) {
                document.querySelectorAll('[id^="dmermaid-"], .error-icon').forEach(d => d.remove());
              }
            }
          }
          document.querySelectorAll('[id^="dmermaid-"], .error-icon').forEach(d => d.remove());
          if (splitviewEstadoRender) splitviewEstadoRender.textContent = `✔ Sincronizado (${res.datos.formulas} eq)`;
        }
      } catch (e) {
        if (e.name === "AbortError") {
          return; // Solicitud reemplazada por otra más reciente
        }
        if (splitviewEstadoRender) splitviewEstadoRender.textContent = "⚠ Error renderizando";
      } finally {
        sincronizandoDesdeCodigo = false;
      }
    }

    // Conectar Botones de la Barra Estilo Word
    if (tbEstiloParrafo) {
      tbEstiloParrafo.addEventListener("change", () => {
        const val = tbEstiloParrafo.value;
        if (val === "p") aplicarFormato("", "");
        else if (val === "h1") aplicarFormato("# ", "", null, null, true);
        else if (val === "h2") aplicarFormato("## ", "", null, null, true);
        else if (val === "h3") aplicarFormato("### ", "", null, null, true);
        else if (val === "h4") aplicarFormato("#### ", "", null, null, true);
        else if (val === "h5") aplicarFormato("##### ", "", null, null, true);
        else if (val === "h6") aplicarFormato("###### ", "", null, null, true);
        else if (val === "quote") aplicarFormato("> ", "", null, null, true);
        else if (val === "code") aplicarFormato("```\n", "\n```");
        tbEstiloParrafo.value = "p";
      });
    }

    if (tbBtnNegrita) tbBtnNegrita.addEventListener("click", () => aplicarFormato("**", "**"));
    if (tbBtnCursiva) tbBtnCursiva.addEventListener("click", () => aplicarFormato("*", "*"));
    if (tbBtnTachado) tbBtnTachado.addEventListener("click", () => aplicarFormato("~~", "~~"));
    if (tbBtnCodigo) tbBtnCodigo.addEventListener("click", () => aplicarFormato("`", "`"));
    if (tbBtnEnlace) {
      tbBtnEnlace.addEventListener("click", () => {
        const url = prompt("Introduce el enlace (URL):", "https://");
        if (url) {
          aplicarFormato("[", `](${url})`);
        }
      });
    }

    if (tbBtnListaVinetas) tbBtnListaVinetas.addEventListener("click", () => aplicarFormato("- ", "", null, null, true));
    if (tbBtnListaNum) tbBtnListaNum.addEventListener("click", () => aplicarFormato("1. ", "", null, null, true));
    if (tbBtnListaTareas) tbBtnListaTareas.addEventListener("click", () => aplicarFormato("- [ ] ", "", null, null, true));

    if (tbBtnNota) {
      tbBtnNota.addEventListener("click", () => {
        if (!splitviewTextarea) return;
        const start = splitviewTextarea.selectionStart;
        const end = splitviewTextarea.selectionEnd;
        const sel = splitviewTextarea.value.substring(start, end);
        if (sel) {
          aplicarFormato("> ", "", null, null, true);
        } else {
          aplicarFormato("\n> Nota técnica: [Escriba aquí la nota...]\n\n", "");
        }
      });
    }

    if (tbBtnLimpiarNotas) {
      tbBtnLimpiarNotas.addEventListener("click", () => {
        const regexNotas = /^\s*>\s?/gm;
        if (splitviewTextarea) {
          const antes = splitviewTextarea.value;
          const limpio = antes.replace(regexNotas, "");
          splitviewTextarea.value = limpio;
          markdownContent = limpio;
        }
        if (editor) {
          editor.value = editor.value.replace(regexNotas, "");
          contarCaracteres();
        }
        clearTimeout(timerRenderSplitview);
        actualizarRenderEnVivo();
        if (splitviewCaracteres && splitviewTextarea) {
          splitviewCaracteres.textContent = `${splitviewTextarea.value.length} caracteres`;
        }
        toast("Todas las notas (>) del documento han sido eliminadas exitosamente", "ok");
      });
    }

    if (tbBtnTabla) {
      tbBtnTabla.addEventListener("click", () => {
        const tablaMd = 
          "\n| Columna 1 | Columna 2 | Columna 3 |\n" +
          "| :--- | :--- | :--- |\n" +
          "| Dato 1.1 | Dato 1.2 | Dato 1.3 |\n" +
          "| Dato 2.1 | Dato 2.2 | Dato 2.3 |\n\n";
        aplicarFormato(tablaMd, "");
      });
    }

    if (tbBtnImagen) {
      tbBtnImagen.addEventListener("click", async () => {
        try {
          if (navigator.clipboard && navigator.clipboard.read) {
            const items = await navigator.clipboard.read();
            for (const item of items) {
              const imageType = item.types.find((t) => t.startsWith("image/"));
              if (imageType) {
                const blob = await item.getType(imageType);
                const reader = new FileReader();
                reader.onload = (event) => {
                  insertarImagenBase64EnEditor(event.target.result);
                };
                reader.readAsDataURL(blob);
                return;
              }
            }
          }
        } catch (err) {
          // Permisos o falta de soporte portapapeles
        }

        // Si no se encontró imagen en el portapapeles, abrir selector de archivos de imagen
        const inputArchivo = document.createElement("input");
        inputArchivo.type = "file";
        inputArchivo.accept = "image/*";
        inputArchivo.style.display = "none";
        inputArchivo.addEventListener("change", (e) => {
          const file = e.target.files && e.target.files[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (ev) => {
              insertarImagenBase64EnEditor(ev.target.result);
            };
            reader.readAsDataURL(file);
          }
          inputArchivo.remove();
        });
        document.body.appendChild(inputArchivo);
        inputArchivo.click();
      });
    }

    if (btnAbrirSplitview && modalSplitview) {
      btnAbrirSplitview.addEventListener("click", () => {
        const textoActual = editor ? editor.value : (textoSaneado || "");
        if (splitviewTextarea) splitviewTextarea.value = textoActual;
        modalSplitview.classList.add("activo");
        actualizarRenderEnVivo();
      });
    }

    if (btnCerrarSplitview && modalSplitview) {
      btnCerrarSplitview.addEventListener("click", () => {
        modalSplitview.classList.remove("activo");
      });
    }

    if (splitviewTextarea) {
      splitviewTextarea.addEventListener("input", () => {
        markdownContent = splitviewTextarea.value;
        if (splitviewCaracteres) splitviewCaracteres.textContent = `${markdownContent.length} caracteres`;
        clearTimeout(timerRenderSplitview);
        timerRenderSplitview = setTimeout(actualizarRenderEnVivo, 80);
      });
    }

    if (splitviewSelectorVista) {
      splitviewSelectorVista.addEventListener("change", () => {
        const vista = splitviewSelectorVista.value;
        if (vista === "split") {
          if (splitviewPanelEditor) splitviewPanelEditor.style.display = "flex";
          if (splitviewPanelPreview) splitviewPanelPreview.style.display = "flex";
        } else if (vista === "preview") {
          if (splitviewPanelEditor) splitviewPanelEditor.style.display = "none";
          if (splitviewPanelPreview) splitviewPanelPreview.style.display = "flex";
        } else if (vista === "editor") {
          if (splitviewPanelEditor) splitviewPanelEditor.style.display = "flex";
          if (splitviewPanelPreview) splitviewPanelPreview.style.display = "none";
        }
      });
    }

    if (btnSplitviewGuardar) {
      btnSplitviewGuardar.addEventListener("click", () => {
        const nuevoTexto = splitviewTextarea ? splitviewTextarea.value : "";
        if (editor) editor.value = nuevoTexto;
        textoSaneado = nuevoTexto;
        contarCaracteres();
        toast("Versión corregida consolidada con éxito en la aplicación", "ok");
      });
    }

    if (btnSplitviewExportar) {
      btnSplitviewExportar.addEventListener("click", () => {
        const textoDescarga = splitviewTextarea ? splitviewTextarea.value : "";
        const blob = new Blob([textoDescarga], { type: "text/markdown;charset=utf-8" });
        const enlace = document.createElement("a");
        enlace.href = URL.createObjectURL(blob);
        const tit = ($("#opt-titulo")?.value.trim() || "documento").replace(/\s+/g, "_");
        enlace.download = `${tit}.md`;
        enlace.click();
        URL.revokeObjectURL(enlace.href);
        toast("Documento Markdown exportado", "ok");
      });
    }

    // Cerrar modales con tecla Escape
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        if (modalFirma && modalFirma.classList.contains("activo")) modalFirma.classList.remove("activo");
        if (modalIndice && modalIndice.classList.contains("activo")) modalIndice.classList.remove("activo");
        if (modalSplitview && modalSplitview.classList.contains("activo")) modalSplitview.classList.remove("activo");
      }
    });

    contarCaracteres();
  });
})();
