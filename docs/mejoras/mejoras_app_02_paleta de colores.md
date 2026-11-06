# Guía Técnica de Correcciones y Mejoras para MarkFlow Office

Este documento recopila las pautas, requerimientos y soluciones técnicas para optimizar los motores de exportación (**PDF, HTML y Word**) de **MarkFlow Office**, incorporando personalizaciones avanzadas de paletas de colores, gestión de tablas, firmas corporativas y saltos de página por capítulo.

---

## 1. Correcciones y Mejoras en la Configuración de PDF

### A. Saltos de Página Automáticos por Capítulo
- **Requerimiento:** Al activar el check de saltos de página en capítulos, el motor de renderizado debe forzar un salto de página antes de cada título de nivel principal (Capítulos H1, por ejemplo: `1. `, `2. `, `3. `).
- **Implementación técnica (CSS/Python):**
  ```css
  /* Asegurar salto de página en elementos de capítulo principal */
  h1, .chapter-title {
    page-break-before: always;
    break-before: page;
  }
  /* Evitar salto en el primer h1 del documento si es la portada */
  h1:first-of-type {
    page-break-before: avoid;
    break-before: avoid;
  }
  ```

### B. Paleta Editorial PDF y Valores por Defecto
- **Paleta Editorial PDF (Documentos de Alta Gama):** Debe incluir la opción de seleccionar un juego de colores personalizado al igual que en los demás formatos.
- **Valores por Default Obligatorios (Pre-checkados):**
  1. Activar salto de página por capítulo (`True`).
  2. Numerar página (`True`).
  3. Running header / Encabezado móvil (`True`).

### C. Firma al Final del Documento e Índice
- **Firma Institucional:** Al final del documento PDF generado, se debe insertar automáticamente un bloque de firma formateado con los siguientes datos exactos:
  - **Nombre:** `Ing. Patricio Sarmiento Reinoso, Mgst.`
  - **Puesto:** `CONSULTOR`
- **Índice / Tabla de Contenidos:** Habilitar obligatoriamente la generación automática del índice de contenidos al final (o al inicio según configuración del documento) del archivo PDF.

---

## 2. Integración de Colores Personalizados en HTML

- **Problema actual:** Los temas predefinidos en HTML ignoran o no aplican correctamente la paleta personalizada de colores seleccionada por el usuario.
- **Solución técnica:** Inyectar las variables CSS dinámicas de color directamente en la etiqueta `<style>` raíz del HTML exportado en función de la paleta elegida o creada:
  ```html
  <style>
    :root {
      --primary-color: /* Color 1 seleccionado por el usuario */;
      --secondary-color: /* Color 2 seleccionado por el usuario */;
      --accent-color: /* Color 3 o secundario */;
    }
    body.custom-theme h1, body.custom-theme h2 {
      color: var(--primary-color) !important;
    }
    body.custom-theme h3, body.custom-theme .subtitle {
      color: var(--secondary-color) !important;
    }
  </style>
  ```

---

## 3. Configuración Avanzada para Word (.docx)

### A. Paleta Personalizada de 3 Colores
- En la sección de temas personalizados para Word, el selector debe permitir configurar **3 colores** en lugar de 2:
  1. **Color Primario:** Títulos principales (H1).
  2. **Color Secundario:** Subtítulos (H2 / H3).
  3. **Color de Acentos / Bordes:** Líneas divisorias, llamadas o elementos destacados.

### B. Control de Paleta Suave para Tablas / Cuadros

- **Check de Control:** Añadir un interruptor (*checkbox*) etiquetado como **"Activar Paleta Suave para Tablas / Cuadros"**.
  - **Si está activo:** Los cuadros y tablas utilizarán automáticamente la paleta de colores suaves predefinida para tablas de la aplicación.
  - **Si está inactivo:** Los cuadros y tablas ignorarán la paleta suave y se activara un selector solo para los cuadros (con 2 colores, fondos de encabezados y de filas de los cuadros y se podra colocar un nombre para guardarlo)

### C. Selector de Color para Títulos y Subtítulos (Negro vs Paleta)
- Añadir un control tipo `Select` o `Combobox` con dos opciones operativas para el texto de los encabezados:
  1. **"Todos en Negro" (`#000000` o `#111111`):** Fuerza a que todos los títulos y subtítulos del documento Word se rendericen en color negro formal.
  2. **"Usar Color de la Paleta":** Aplica de forma dinámica los colores definidos en la paleta activa (primario y secundario) a los encabezados.