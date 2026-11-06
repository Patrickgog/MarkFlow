/* ============================================================================
   MARKFLOW OFFICE — REGISTRO ÚNICO DE TEMAS Y OPCIONES (v1.13.0)
   Single Source of Truth (SSOT) del cliente para:
   HTML · Word (.docx) · PDF (.pdf) · Excel (.xlsx)
   Alimentado directamente de las especificaciones del motor clásico.
   ============================================================================ */
"use strict";

(function (window) {
  const REGISTRO = {
    html: {
      temas: [
        { valor: "defecto", nombre: "Tema Clásico MarkFlow (Limpio y Centrado)", descripcion: "Diseño sobrio y limpio optimizado para lectura técnica", compatible_con: ["html"] },
        { valor: "Tema1", nombre: "Tema 1: Ejecutivo Clásico (Azul Océano)", descripcion: "Estilo corporativo formal con tonos azules", compatible_con: ["html", "word"] },
        { valor: "Tema2", nombre: "Tema 2: Técnico Moderno (Esmeralda Tecnológico)", descripcion: "Paleta esmeralda técnica y moderna", compatible_con: ["html", "word"] },
        { valor: "Tema3", nombre: "Tema 3: Editorial Académico (Pizarra Formal)", descripcion: "Tipografía sobria y pizarra para artículos formales", compatible_con: ["html", "word", "pdf"] },
        { valor: "Tema4", nombre: "Tema 4: Minimalista Clean (Grafito Carbón)", descripcion: "Líneas puras y contraste óptimo sobre fondo blanco", compatible_con: ["html"] },
        { valor: "Tema5", nombre: "Tema 5: Corporativo Vanguardia (Púrpura Editorial)", descripcion: "Elegancia y creatividad para memorias", compatible_con: ["html"] },
        { valor: "Tema6", nombre: "Tema 6: Industrial Cálido (Ámbar Dorado)", descripcion: "Tonos cálidos y ámbar de alto impacto visual", compatible_con: ["html"] }
      ],
      anchos: [
        { valor: "900px", nombre: "900 px (Estándar de Lectura Centrado)" },
        { valor: "860px", nombre: "860 px (Compacto)" },
        { valor: "1000px", nombre: "1000 px (Ancho Amplio)" },
        { valor: "1200px", nombre: "1200 px (Extendido)" },
        { valor: "100%", nombre: "100 % (Ancho Completo)" }
      ],
      paletas_tricolor: [
        { clave: "tema_default", nombre: "Por Defecto del Tema", primario: "#0284c7", secundario: "#0d9488", fondo_suave: "#f1f5f9", colores: ["#0284c7", "#0d9488", "#f1f5f9"] },
        { clave: "oceano_ejecutivo", nombre: "Océano Ejecutivo", primario: "#1E3A8A", secundario: "#3B82F6", fondo_suave: "#EFF6FF", colores: ["#1E3A8A", "#3B82F6", "#EFF6FF"] },
        { clave: "bosque_academico", nombre: "Bosque Académico", primario: "#14532D", secundario: "#22C55E", fondo_suave: "#F0FDF4", colores: ["#14532D", "#22C55E", "#F0FDF4"] },
        { clave: "pizarra_minimalista", nombre: "Pizarra Minimalista", primario: "#1E293B", secundario: "#64748B", fondo_suave: "#F8FAFC", colores: ["#1E293B", "#64748B", "#F8FAFC"] },
        { clave: "terracota_editorial", nombre: "Terracota Editorial", primario: "#7C2D12", secundario: "#EA580C", fondo_suave: "#FFF7ED", colores: ["#7C2D12", "#EA580C", "#FFF7ED"] },
        { clave: "vino_corporativo", nombre: "Vino Tinto Corporativo", primario: "#581C87", secundario: "#9333EA", fondo_suave: "#FAF5FF", colores: ["#581C87", "#9333EA", "#FAF5FF"] },
        { clave: "ambar_dorado", nombre: "Ámbar Dorado", primario: "#78350F", secundario: "#D97706", fondo_suave: "#FFFBEB", colores: ["#78350F", "#D97706", "#FFFBEB"] }
      ],
      fuentes: [
        { valor: "system-ui, -apple-system, sans-serif", nombre: "Sistema Moderno (Sans-serif)" },
        { valor: "'Plus Jakarta Sans', sans-serif", nombre: "Plus Jakarta Sans" },
        { valor: "'Segoe UI', Tahoma, sans-serif", nombre: "Segoe UI" },
        { valor: "Georgia, serif", nombre: "Georgia (Elegante)" }
      ],
      tamanios: ["10", "11", "12"],
      interlineados: [
        { valor: "1.4", nombre: "1.4 (Compacto)" },
        { valor: "1.6", nombre: "1.6 (Lectura óptima)" },
        { valor: "1.8", nombre: "1.8 (Holgado)" }
      ],
      defaults: {
        tema: "defecto",
        ancho: "900px",
        paleta_tricolor: "tema_default",
        fuente: "system-ui, -apple-system, sans-serif",
        tamanio: "11",
        interlineado: "1.6",
        footer_izq: "MarkFlow AI 2026",
        footer_der: "Ing. Patricio Sarmiento Reinoso, Mgst.",
        justificado: true,
        numerar_ecuaciones: false
      }
    },

    word: {
      temas: [
        { valor: "tema1", nombre: "Tema 1: Memoria Técnica Clásica (tema1.docx)", descripcion: "Estilos nativos leídos de templates/temas_word/tema1.docx", compatible_con: ["word", "html"] },
        { valor: "tema2", nombre: "Tema 2: Ingeniería Sobria Sin Laterales (tema2.docx)", descripcion: "Estilos nativos leídos de templates/temas_word/tema2.docx", compatible_con: ["word", "html"] },
        { valor: "tema3", nombre: "Tema 3: Editorial Azul Acero (tema3.docx)", descripcion: "Estilos nativos leídos de templates/temas_word/tema3.docx", compatible_con: ["word", "html", "pdf"] },
        { valor: "personalizado", nombre: "🎨 Tema Personalizado (Habilita paleta y colores)", descripcion: "Permite seleccionar paleta de colores para títulos y tablas", compatible_con: ["word"] }
      ],
      paletas_tablas: [
        { valor: "defecto", nombre: "Gris Sobrio / Clásico", cabecera: "#E2E8F0", par: "#F8FAFC", borde: "#CBD5E1", colores: ["#E2E8F0", "#F8FAFC", "#CBD5E1"] },
        { valor: "gris_ejecutivo", nombre: "Gris Ejecutivo Formal", cabecera: "#334155", par: "#F1F5F9", borde: "#94A3B8", colores: ["#334155", "#F1F5F9", "#94A3B8"] },
        { valor: "salvia_suave", nombre: "Verde Salvia Apagado", cabecera: "#D1FAE5", par: "#F0FDF4", borde: "#A7F3D0", colores: ["#D1FAE5", "#F0FDF4", "#A7F3D0"] },
        { valor: "crema_neutro", nombre: "Crema Marfil Neutro", cabecera: "#FEF3C7", par: "#FFFBEB", borde: "#FDE68A", colores: ["#FEF3C7", "#FFFBEB", "#FDE68A"] },
        { valor: "ceniza_formal", nombre: "Ceniza Grafito Suave", cabecera: "#E5E7EB", par: "#F9FAFB", borde: "#D1D5DB", colores: ["#E5E7EB", "#F9FAFB", "#D1D5DB"] },
        { valor: "azul_acero_suave", nombre: "Azul Acero Apagado (Pastel)", cabecera: "#E0E7FF", par: "#EEF2FF", borde: "#C7D2FE", colores: ["#E0E7FF", "#EEF2FF", "#C7D2FE"] }
      ],
      paletas_titulos: [
        { valor: "negro", nombre: "Negro Absoluto / Formal (#000000)", colores: ["#000000", "#111111", "#333333"] },
        { valor: "azul", nombre: "Azul Institucional / Ejecutivo (#1E3A8A)", colores: ["#1E3A8A", "#2563EB", "#3B82F6"] },
        { valor: "corporate-blue", nombre: "Azul Ejecutivo (#003366)", colores: ["#003366", "#205081", "#4682B4"] },
        { valor: "emerald-tech", nombre: "Esmeralda Académico (#046A38)", colores: ["#046A38", "#1F8A53", "#50C878"] },
        { valor: "slate-modern", nombre: "Pizarra Minimalista (#2F4F4F)", colores: ["#2F4F4F", "#4A6B6B", "#708090"] },
        { valor: "burgundy-classic", nombre: "Vino Tinto Editorial (#6B1426)", colores: ["#6B1426", "#85223A", "#A3334D"] }
      ],
      fuentes: ["Calibri", "Arial", "Times New Roman", "Georgia", "Aptos", "Garamond", "Century Gothic"],
      tamanios: ["10", "11", "12"],
      interlineados: [
        { valor: "1.0", nombre: "Sencillo 1.0 (Por defecto)" },
        { valor: "1.15", nombre: "1.15 líneas" },
        { valor: "1.5", nombre: "1.5 líneas" },
        { valor: "2.0", nombre: "Doble 2.0" }
      ],
      alineaciones: [
        { valor: "justificado", nombre: "Justificado" },
        { valor: "izquierda", nombre: "Izquierda" },
        { valor: "centrado", nombre: "Centrado" },
        { valor: "derecha", nombre: "Derecha" }
      ],
      tamanios_tabla: [
        { valor: "auto", nombre: "Automático / Adaptativo" },
        { valor: "7", nombre: "7 pt" },
        { valor: "8", nombre: "8 pt" },
        { valor: "9", nombre: "9 pt" },
        { valor: "10", nombre: "10 pt" },
        { valor: "11", nombre: "11 pt" },
        { valor: "12", nombre: "12 pt" }
      ],
      defaults: {
        tema: "tema1",
        paleta_suave: true,
        paleta_tabla: "defecto",
        modo_color_titulos: "negro",
        color_titulos: "negro",
        fuente: "Calibri",
        tamanio: "11",
        interlineado: "1.0",
        alineacion: "justificado",
        fuente_tabla: "heredar",
        tamanio_tabla: "10",
        pie_pagina: "",
        alineacion_pie: "derecha",
        numerar_ecuaciones: false,
        apa7: false,
        crear_indice: false,
        posicion_indice: "inicio",
        numerar_paginas: true
      }
    },

    pdf: {
      paletas: [
        { valor: "pizarra_carbon", nombre: "Pizarra & Carbón", primario: "#1E293B", secundario: "#475569", fondo_suave: "#F8FAFC", colores: ["#1E293B", "#475569", "#F8FAFC"] },
        { valor: "azul_prusia", nombre: "Azul Prusia & Acero", primario: "#1E3A5F", secundario: "#2B547E", fondo_suave: "#F0F4F8", colores: ["#1E3A5F", "#2B547E", "#F0F4F8"] },
        { valor: "grafito_salvia", nombre: "Grafito & Salvia", primario: "#1C2E24", secundario: "#3F5E4D", fondo_suave: "#F4F7F5", colores: ["#1C2E24", "#3F5E4D", "#F4F7F5"] },
        { valor: "onix_burdeos", nombre: "Ónix & Burdeos Imperial", primario: "#2D1B22", secundario: "#5C2C38", fondo_suave: "#FAF6F7", colores: ["#2D1B22", "#5C2C38", "#FAF6F7"] },
        { valor: "negro_papel", nombre: "Negro Puro & Papel", primario: "#0F172A", secundario: "#334155", fondo_suave: "#F3F4F6", colores: ["#0F172A", "#334155", "#F3F4F6"] }
      ],
      estilos: [
        { valor: "informe", nombre: "Informe Técnico Moderno" },
        { valor: "academico", nombre: "Académico / Booktabs" },
        { valor: "portada", nombre: "Ejecutivo con Portada" }
      ],
      modos_columnas: [
        { valor: "estandar", nombre: "📄 Estándar (1 Columna)" },
        { valor: "dos_columnas", nombre: "📰 Dos Columnas (2 Col)" },
        { valor: "paper_cientifico", nombre: "🔬 Paper Científico (IEEE / Academic 2 Col)" },
        { valor: "revista", nombre: "🎨 Modo Revista (Editorial Magazine)" }
      ],
      fuentes: ["Calibri", "Inter", "Roboto", "Georgia", "Times New Roman", "Garamond"],
      tamanios: ["10", "10.5", "11", "12"],
      interlineados: [
        { valor: "1.0", nombre: "Sencillo 1.0" },
        { valor: "1.15", nombre: "1.15 líneas (Óptimo editorial)" },
        { valor: "1.5", nombre: "1.5 líneas" },
        { valor: "2.0", nombre: "Doble 2.0" }
      ],
      formatos_num: [
        { valor: "pagina_x_de_y", nombre: "Página X de Y (ej. Página 1 de 24)" },
        { valor: "x_de_y", nombre: "X / Y (ej. 1 / 24)" },
        { valor: "x", nombre: "Solo número (ej. 1)" }
      ],
      defaults: {
        paleta: "pizarra_carbon",
        estilo: "informe",
        modo_columnas: "estandar",
        fuente: "Calibri",
        tamanio: "11",
        interlineado: "1.15",
        pie_pagina: "",
        alineacion_pie: "izquierda",
        salto_capitulo: true,
        justificado: true,
        numerar_paginas: true,
        running_header: true,
        texto_running_header: "",
        formato_num: "pagina_x_de_y",
        alineacion_num: "derecha"
      }
    },

    excel: {
      paletas: [
        { valor: "clasico", nombre: "Verde Clásico (Excel)", cabecera: "#107C41", par: "#F4FAF5", borde: "#D1D5DB", colores: ["#107C41", "#F4FAF5", "#D1D5DB"] },
        { valor: "azul", nombre: "Azul Ejecutivo", cabecera: "#1E3A8A", par: "#F0F4F8", borde: "#CBD5E1", colores: ["#1E3A8A", "#F0F4F8", "#CBD5E1"] },
        { valor: "gris", nombre: "Gris Moderno", cabecera: "#334155", par: "#F8FAFC", borde: "#E2E8F0", colores: ["#334155", "#F8FAFC", "#E2E8F0"] },
        { valor: "esmeralda", nombre: "Esmeralda Académico", cabecera: "#046A38", par: "#F0FDF4", borde: "#D1FAE5", colores: ["#046A38", "#F0FDF4", "#D1FAE5"] },
        { valor: "monocromo", nombre: "Monocromo Formal", cabecera: "#18181B", par: "#FAFAFA", borde: "#E4E4E7", colores: ["#18181B", "#FAFAFA", "#E4E4E7"] }
      ],
      modos_hojas: [
        { valor: "multi_hoja", nombre: "Una hoja por tabla (Recomendado)" },
        { valor: "hoja_unica", nombre: "Todas las tablas en una sola hoja" }
      ],
      defaults: {
        estilo: "clasico",
        fuente: "Calibri",
        tamanio: "10",
        modo_hojas: "multi_hoja"
      }
    }
  };

  function obtenerOpciones(formato) {
    const claveStorage = `mfo_opciones_${formato}`;
    const def = REGISTRO[formato]?.defaults || {};
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
    const def = REGISTRO[formato]?.defaults || {};
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
    datos: REGISTRO,
    obtenerOpciones,
    guardarOpciones,
    restablecerOpciones,

    // Gestión de paletas personalizadas en localStorage
    obtenerPaletasPersonalizadas,
    guardarPaletaPersonalizada,
    eliminarPaletaPersonalizada,

    // Acceso directo a listas de Word
    TEMAS_WORD: REGISTRO.word.temas,
    PALETAS_TABLAS_WORD: REGISTRO.word.paletas_tablas,
    PALETAS_TITULOS_WORD: REGISTRO.word.paletas_titulos,
    FUENTES_WORD: REGISTRO.word.fuentes,
    TAMANIOS_WORD: REGISTRO.word.tamanios,
    INTERLINEADOS_WORD: REGISTRO.word.interlineados,
    ALINEACIONES_WORD: REGISTRO.word.alineaciones,
    TAMANIOS_TABLA_WORD: REGISTRO.word.tamanios_tabla,

    // Acceso directo a listas de HTML
    TEMAS_HTML: REGISTRO.html.temas,
    ANCHOS_HTML: REGISTRO.html.anchos,
    PALETAS_HTML_TRICOLOR: REGISTRO.html.paletas_tricolor,
    FUENTES_HTML: REGISTRO.html.fuentes,
    TAMANIOS_HTML: REGISTRO.html.tamanios,
    INTERLINEADOS_HTML: REGISTRO.html.interlineados,

    // Acceso directo a listas de PDF
    PALETAS_EDITORIAL_PDF: REGISTRO.pdf.paletas,
    ESTILOS_MAQUETACION_PDF: REGISTRO.pdf.estilos,
    MODOS_COLUMNAS_PDF: REGISTRO.pdf.modos_columnas,
    FUENTES_PDF: REGISTRO.pdf.fuentes,
    TAMANIOS_PDF: REGISTRO.pdf.tamanios,
    INTERLINEADOS_PDF: REGISTRO.pdf.interlineados,
    FORMATOS_NUM_PDF: REGISTRO.pdf.formatos_num,

    // Acceso directo a listas de Excel
    PALETAS_EXCEL: REGISTRO.excel.paletas,
    MODOS_HOJAS_EXCEL: REGISTRO.excel.modos_hojas
  };
})(window);

