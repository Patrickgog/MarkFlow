/* ============================================================================
   MARKFLOW OFFICE — Transformaciones puras de Markdown (v1.21.0)
   ESPEJO JS del módulo canónico en Python `motor/notas.py`.
   Mantener ambos en paridad estricta (mismas reglas, mismos tipos, mismos
   protectores). No toca el DOM: funciones puras sobre cadenas, testeables.
   ============================================================================ */
"use strict";

(function () {
  // Tipos de nota soportados (GitHub canonical + aliases en español)
  var TIPOS_NOTA = {
    NOTE: { icono: "📝", etiqueta: "Nota", clase: "note" },
    TIP: { icono: "💡", etiqueta: "Consejo", clase: "tip" },
    IMPORTANT: { icono: "❗", etiqueta: "Importante", clase: "important" },
    WARNING: { icono: "⚠️", etiqueta: "Advertencia", clase: "warning" },
    CAUTION: { icono: "⛔", etiqueta: "Precaución", clase: "caution" },
  };

  var ALIASES = {
    note: "NOTE", nota: "NOTE",
    tip: "TIP", consejo: "TIP",
    important: "IMPORTANT", importante: "IMPORTANT",
    warning: "WARNING", advertencia: "WARNING",
    caution: "CAUTION", precaucion: "CAUTION",
  };

  var PATRON_TIPOS = Object.keys(ALIASES).sort().join("|");

  // Cabecera de bloque de nota en Markdown: línea `> [!TIPO]`
  // Nota: se usa [ \t]* (nunca \s*) para no cruzar saltos de línea (bug v1.20.x).
  // JS no soporta grupos con nombre (?P<...>): se usan posicionales.
  var RE_CABECERA_NOTA = new RegExp(
    "^[ \\t]*(>[ \\t]*)\\[!\\s*(" + PATRON_TIPOS + ")\\s*\\]([^\\n]*)$", "i"
  );

  var RE_LINEA_CITA = /^\s*>/;

  // Bloques protegidos durante quitarNotas (LaTeX display y cercos de código)
  var RE_BLOQUE_CODIGO = /^[ \t]*`{3,}[^\n]*\n[\s\S]*?^[ \t]*`{3,}[ \t]*$/gm;
  var RE_BLOQUE_LATEX = new RegExp(
    "^[ \\t]*\\$\\$[^\\n]*\\n[\\s\\S]*?^[ \\t]*\\$\\$[ \\t]*$" +     // $$ display multilínea
      "|^[ \\t]*\\\\\\[[^\\n]*\\n[\\s\\S]*?^[ \\t]*\\\\\\][ \\t]*$" + // \[ display multilínea
      "|^[ \\t]*\\\\begin\\{[a-zA-Z*]+\\}[\\s\\S]*?\\\\end\\{[a-zA-Z*]+\\}[ \\t]*$", // entornos TeX
    "gm"
  );

  function canonicalizarTipo(tipo) {
    if (!tipo) return null;
    return ALIASES[String(tipo).trim().toLowerCase()] || null;
  }

  /** Canonicaliza variantes ([!NOTA] → [!NOTE]…) CONSERVANDO el marcador. */
  function normalizarEtiquetasNota(texto) {
    if (!texto) return "";
    return texto.replace(
      /\[!\s*([A-Za-z]+)\s*\]/gi,
      function (m, t) {
        var canon = canonicalizarTipo(t);
        return canon ? "[!" + canon + "]" : m;
      }
    );
  }

  /** Enmascara bloques LaTeX y de código con placeholders únicos. */
  function protegerBloques(texto) {
    var restituciones = {};
    var n = 0;
    function ph(m) {
      n += 1;
      restituciones[n] = m;
      return "\x00MFOQT" + n + "\x00";
    }
    texto = texto.replace(RE_BLOQUE_LATEX, ph);
    texto = texto.replace(RE_BLOQUE_CODIGO, ph);
    return { texto: texto, restituciones: restituciones };
  }

  function restaurarBloques(texto, restituciones) {
    return texto.replace(/\x00MFOQT(\d+)\x00/g, function (m, num) {
      return restituciones[parseInt(num, 10)] || "";
    });
  }

  /**
   * Elimina únicamente los bloques de nota/callout (cabecera `> [!TIPO]`).
   * Preserva: LaTeX, bloques de código, tablas, imágenes, HTML embebido y
   * citas normales sin `[!TIPO]`.
   */
  function quitarNotas(texto) {
    if (!texto) return "";
    texto = normalizarEtiquetasNota(texto);
    var protegido = protegerBloques(texto);
    var lineas = protegido.texto.split("\n");
    var salida = [];
    var i = 0;
    while (i < lineas.length) {
      var m = RE_CABECERA_NOTA.exec(lineas[i]);
      if (m) {
        // Bloque de nota: cabecera + todas las líneas `>` contiguas
        var cuerpo = [m[3].trim()];
        i += 1;
        while (i < lineas.length && RE_LINEA_CITA.test(lineas[i])) {
          cuerpo.push(lineas[i].replace(/^\s*>\s?/, ""));
          i += 1;
        }
        var bloque = cuerpo.join("\n").trim();
        if (bloque) {
          salida.push(bloque, "");
        }
        continue;
      }
      salida.push(lineas[i]);
      i += 1;
    }
    var resultado = salida.join("\n").replace(/\n{3,}/g, "\n\n");
    return restaurarBloques(resultado, protegido.restituciones);
  }

  /** Expone la API pública en window.MFOTransforms (paridad con Python). */
  window.MFOTransforms = {
    TIPOS_NOTA: TIPOS_NOTA,
    ALIASES: ALIASES,
    canonicalizarTipo: canonicalizarTipo,
    normalizarEtiquetasNota: normalizarEtiquetasNota,
    quitarNotas: quitarNotas,
  };
})();
