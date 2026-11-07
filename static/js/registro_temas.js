/* ============================================================================
   MARKFLOW OFFICE — REGISTRO ÚNICO DE TEMAS Y OPCIONES (v1.23.2)
   Cargador dinámico: los datos provienen de /api/registro-opciones.
   No contiene datos hardcodeados.
   ============================================================================ */
"use strict";

(function (window) {
  const estado = { datos: null, promesa: null };

  function aLista(v) {
    if (Array.isArray(v)) return v;
    if (v && typeof v === "object") {
      return Object.entries(v).map(([valor, o]) =>
        o && typeof o === "object" ? { valor, ...o } : { valor, nombre: o });
    }
    return [];
  }

  // Solo estas claves son listas de opciones; el resto (defaults, temas_disco,
  // ui) conserva su forma de objeto tal como la entrega el servidor.
  const CLAVES_NO_LISTA = new Set(["defaults", "temas_disco", "ui"]);

  function normalizarArbol(arbol) {
    const salida = {};
    for (const [formato, seccion] of Object.entries(arbol || {})) {
      if (formato === "ui") { salida[formato] = seccion; continue; }
      if (!seccion || typeof seccion !== "object") { salida[formato] = seccion; continue; }
      const s = {};
      for (const [clave, valor] of Object.entries(seccion)) {
        s[clave] = CLAVES_NO_LISTA.has(clave) ? valor
                 : (Array.isArray(valor) || (valor && typeof valor === "object") ? aLista(valor) : valor);
      }
      salida[formato] = s;
    }
    return salida;
  }

  function cargar() {
    if (estado.datos) return Promise.resolve(estado.datos);
    if (!estado.promesa) {
      estado.promesa = fetch("/api/registro-opciones", { cache: "no-store" })
        .then(r => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(cuerpo => {
          estado.datos = normalizarArbol(cuerpo.datos || cuerpo);
          return estado.datos;
        })
        .catch(err => { estado.promesa = null; throw err; });
    }
    return estado.promesa;
  }

  function opciones(seccion, clave) {
    const v = estado.datos?.[seccion]?.[clave];
    return Array.isArray(v) ? v : [];
  }

  function defaults(formato) {
    return estado.datos?.[formato]?.defaults || {};
  }

  /* ─────────────────── Opciones guardadas (localStorage) ─────────────────── */
  function obtenerOpciones(formato) {
    const claveStorage = `mfo_opciones_${formato}`;
    const def = defaults(formato);
    try {
      const guardado = localStorage.getItem(claveStorage);
      return guardado ? { ...def, ...JSON.parse(guardado) } : { ...def };
    } catch {
      return { ...def };
    }
  }

  function guardarOpciones(formato, valores) {
    const claveStorage = `mfo_opciones_${formato}`;
    try {
      localStorage.setItem(claveStorage, JSON.stringify(valores));
    } catch (e) {
      console.warn("No se pudo guardar opciones de", formato, e);
    }
  }

  function restablecerOpciones(formato) {
    const def = defaults(formato);
    guardarOpciones(formato, def);
    return { ...def };
  }

  /* ─────────────────── Paletas Personalizadas (localStorage) ─────────────────── */
  function obtenerPaletasPersonalizadas() {
    try {
      const guardado = localStorage.getItem("mfo_paletas_personalizadas");
      return guardado ? JSON.parse(guardado) : [];
    } catch (e) {
      console.warn("Error leyendo paletas personalizadas:", e);
      return [];
    }
  }

  function guardarPaletaPersonalizada(nombre, formato, colores) {
    if (!nombre || !nombre.trim()) {
      throw new Error("El nombre de la paleta personalizada no puede estar vacío.");
    }
    if (!Array.isArray(colores) || colores.length < 2 || colores.length > 6) {
      throw new Error("Una paleta personalizada debe contener entre 2 y 6 colores.");
    }
    const paletas = obtenerPaletasPersonalizadas();
    const id = "pal_custom_" + Date.now().toString(36) + "_" + Math.random().toString(36).substring(2, 6);
    const nueva = {
      id,
      nombre: nombre.trim(),
      formato: formato || "universal",
      colores: colores.map(c => String(c).trim()),
      fecha: new Date().toISOString()
    };
    paletas.push(nueva);
    try {
      localStorage.setItem("mfo_paletas_personalizadas", JSON.stringify(paletas));
    } catch (e) {
      console.warn("No se pudo guardar la paleta personalizada:", e);
    }
    return nueva;
  }

  function eliminarPaletaPersonalizada(id) {
    const paletas = obtenerPaletasPersonalizadas().filter(p => p.id !== id);
    try {
      localStorage.setItem("mfo_paletas_personalizadas", JSON.stringify(paletas));
    } catch (e) {
      console.warn("No se pudo eliminar la paleta:", e);
    }
    return paletas;
  }

  window.MFORegistro = {
    cargar,
    opciones,
    defaults,
    ui: (clave) => { const v = estado.datos?.ui?.[clave]; return v === undefined || v === null ? "" : v; },
    get datos() { return estado.datos; },
    // Acceso directo (getters dinámicos desde la API, sin hardcodeo)
    get TEMAS_WORD() { return opciones("word", "temas"); },
    get PALETAS_TABLAS_WORD() { return opciones("word", "paletas_tablas"); },
    get PALETAS_TITULOS_WORD() { return opciones("word", "paletas_titulos"); },
    get FUENTES_WORD() { return opciones("word", "fuentes"); },
    get TAMANIOS_WORD() { return opciones("word", "tamanios"); },
    get INTERLINEADOS_WORD() { return opciones("word", "interlineados"); },
    get ALINEACIONES_WORD() { return opciones("word", "alineaciones"); },
    get FUENTES_TABLA_WORD() { return opciones("word", "fuentes_tabla"); },
    get TAMANIOS_TABLA_WORD() { return opciones("word", "tamanios_tabla"); },
    get ALINEACIONES_PIE_WORD() { return opciones("word", "alineaciones_pie"); },
    get POSICIONES_INDICE_WORD() { return opciones("word", "posiciones_indice"); },
    get TEMAS_HTML() { return opciones("html", "temas"); },
    get ANCHOS_HTML() { return opciones("html", "anchos"); },
    get PALETAS_HTML_TRICOLOR() { return opciones("html", "paletas_tricolor"); },
    get FUENTES_HTML() { return opciones("html", "fuentes"); },
    get PALETAS_EDITORIAL_PDF() { return opciones("pdf", "paletas"); },
    get ESTILOS_MAQUETACION_PDF() { return opciones("pdf", "estilos"); },
    get MODOS_COLUMNAS_PDF() { return opciones("pdf", "modos_columnas"); },
    get FUENTES_PDF() { return opciones("pdf", "fuentes"); },
    get INTERLINEADOS_PDF() { return opciones("pdf", "interlineados"); },
    get PALETAS_EXCEL() { return opciones("excel", "paletas"); },
    get MODOS_HOJAS_EXCEL() { return opciones("excel", "modos_hojas"); },
    get ANCHOS_COLUMNA_EXCEL() { return opciones("excel", "anchos_columna"); },
    get TAMANIOS_FUENTE_EXCEL() { return opciones("excel", "tamanios_fuente"); },
    obtenerOpciones,
    guardarOpciones,
    restablecerOpciones,
    obtenerPaletasPersonalizadas,
    guardarPaletaPersonalizada,
    eliminarPaletaPersonalizada,
  };
})(window);