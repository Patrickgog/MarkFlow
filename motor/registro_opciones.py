"""Registro único centralizado de temas, paletas y opciones de formato.

Single Source of Truth (SSOT) del backend para:
- Temas HTML, anchos de lectura y paletas tri-color.
- Temas Word, paletas suaves de tablas, paletas de títulos y opciones tipográficas/APA7.
- Temas y estilos PDF, paletas editoriales, modos de columnas, encabezados y pies.
- Opciones de exportación de tablas a Excel (paletas y modo de hojas).
"""

from __future__ import annotations

import copy

# ─────────────────────────────────────────────────────────────────────────────
# 1. TEMAS Y PALETAS HTML
# ─────────────────────────────────────────────────────────────────────────────
TEMAS_HTML = {
    "defecto": "Tema Clásico MarkFlow (Limpio y Centrado)",
    "Tema1": "Tema 1: Ejecutivo Clásico (Azul Océano)",
    "Tema2": "Tema 2: Técnico Moderno (Esmeralda Tecnológico)",
    "Tema3": "Tema 3: Editorial Académico (Pizarra Formal)",
    "Tema4": "Tema 4: Minimalista Clean (Grafito Carbón)",
    "Tema5": "Tema 5: Corporativo Vanguardia (Púrpura Editorial)",
    "Tema6": "Tema 6: Industrial Cálido (Ámbar Dorado)",
}

ANCHOS_HTML = {
    "900px": "900 px (Estándar de Lectura Centrado)",
    "860px": "860 px (Compacto)",
    "1000px": "1000 px (Ancho Amplio)",
    "1200px": "1200 px (Extendido)",
    "100%": "100 % (Ancho Completo)",
}

PALETAS_HTML_TRICOLOR = {
    "tema_default": {"nombre": "Por Defecto del Tema", "primario": "#0284c7", "secundario": "#0d9488", "fondo_suave": "#f1f5f9", "colores": ["#0284c7", "#0d9488", "#f1f5f9"]},
    "oceano_ejecutivo": {"nombre": "Océano Ejecutivo", "primario": "#1E3A8A", "secundario": "#3B82F6", "fondo_suave": "#EFF6FF", "colores": ["#1E3A8A", "#3B82F6", "#EFF6FF"]},
    "bosque_academico": {"nombre": "Bosque Académico", "primario": "#14532D", "secundario": "#22C55E", "fondo_suave": "#F0FDF4", "colores": ["#14532D", "#22C55E", "#F0FDF4"]},
    "pizarra_minimalista": {"nombre": "Pizarra Minimalista", "primario": "#1E293B", "secundario": "#64748B", "fondo_suave": "#F8FAFC", "colores": ["#1E293B", "#64748B", "#F8FAFC"]},
    "terracota_editorial": {"nombre": "Terracota Editorial", "primario": "#7C2D12", "secundario": "#EA580C", "fondo_suave": "#FFF7ED", "colores": ["#7C2D12", "#EA580C", "#FFF7ED"]},
    "vino_corporativo": {"nombre": "Vino Tinto Corporativo", "primario": "#581C87", "secundario": "#9333EA", "fondo_suave": "#FAF5FF", "colores": ["#581C87", "#9333EA", "#FAF5FF"]},
    "ambar_dorado": {"nombre": "Ámbar Dorado", "primario": "#78350F", "secundario": "#D97706", "fondo_suave": "#FFFBEB", "colores": ["#78350F", "#D97706", "#FFFBEB"]},
}

FUENTES_HTML = [
    {"valor": "system-ui, -apple-system, sans-serif", "nombre": "Sistema Moderno (Sans-serif)"},
    {"valor": "'Plus Jakarta Sans', sans-serif", "nombre": "Plus Jakarta Sans"},
    {"valor": "'Segoe UI', Tahoma, sans-serif", "nombre": "Segoe UI"},
    {"valor": "Georgia, serif", "nombre": "Georgia (Elegante)"},
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. TEMAS Y PALETAS WORD (.docx)
# ─────────────────────────────────────────────────────────────────────────────
TEMAS_WORD = {
    "defecto": "Estilo Formal Base (Sobrio sin azul)",
    "tema1": "Tema 1: Ejecutivo Clásico (Nativo)",
    "tema2": "Tema 2: Técnico Moderno (Nativo)",
    "tema3": "Tema 3: Editorial Académico (Nativo)",
    "personalizado": "🎨 Tema Personalizado (Habilita paleta y colores)",
}

PALETAS_TABLAS_WORD = {
    "defecto": {"nombre": "Gris Sobrio / Clásico", "cabecera": "#E2E8F0", "par": "#F8FAFC", "borde": "#CBD5E1", "colores": ["#E2E8F0", "#F8FAFC", "#CBD5E1"]},
    "gris_ejecutivo": {"nombre": "Gris Ejecutivo Formal", "cabecera": "#334155", "par": "#F1F5F9", "borde": "#94A3B8", "colores": ["#334155", "#F1F5F9", "#94A3B8"]},
    "salvia_suave": {"nombre": "Verde Salvia Apagado", "cabecera": "#D1FAE5", "par": "#F0FDF4", "borde": "#A7F3D0", "colores": ["#D1FAE5", "#F0FDF4", "#A7F3D0"]},
    "crema_neutro": {"nombre": "Crema Marfil Neutro", "cabecera": "#FEF3C7", "par": "#FFFBEB", "borde": "#FDE68A", "colores": ["#FEF3C7", "#FFFBEB", "#FDE68A"]},
    "ceniza_formal": {"nombre": "Ceniza Grafito Suave", "cabecera": "#E5E7EB", "par": "#F9FAFB", "borde": "#D1D5DB", "colores": ["#E5E7EB", "#F9FAFB", "#D1D5DB"]},
    "azul_acero_suave": {"nombre": "Azul Acero Apagado (Pastel)", "cabecera": "#E0E7FF", "par": "#EEF2FF", "borde": "#C7D2FE", "colores": ["#E0E7FF", "#EEF2FF", "#C7D2FE"]},
}

PALETAS_TITULOS_WORD = {
    "negro": {"nombre": "Negro Absoluto / Formal (#000000)", "colores": ["#000000", "#111111", "#333333"]},
    "azul": {"nombre": "Azul Institucional / Ejecutivo (#1E3A8A)", "colores": ["#1E3A8A", "#2563EB", "#3B82F6"]},
    "corporate-blue": {"nombre": "Azul Ejecutivo (#003366)", "colores": ["#003366", "#205081", "#4682B4"]},
    "emerald-tech": {"nombre": "Esmeralda Académico (#046A38)", "colores": ["#046A38", "#1F8A53", "#50C878"]},
    "slate-modern": {"nombre": "Pizarra Minimalista (#2F4F4F)", "colores": ["#2F4F4F", "#4A6B6B", "#708090"]},
    "burgundy-classic": {"nombre": "Vino Tinto Editorial (#6B1426)", "colores": ["#6B1426", "#85223A", "#A3334D"]},
}

FUENTES_WORD = ["Calibri", "Arial", "Times New Roman", "Georgia", "Aptos", "Garamond", "Century Gothic"]
TAMANIOS_WORD = [10, 11, 12]
INTERLINEADOS_WORD = [
    {"valor": 1.0, "nombre": "Sencillo 1.0 (Por defecto)"},
    {"valor": 1.15, "nombre": "1.15 líneas"},
    {"valor": 1.5, "nombre": "1.5 líneas"},
    {"valor": 2.0, "nombre": "Doble 2.0"},
]
ALINEACIONES_WORD = ["justificado", "izquierda", "centrado", "derecha"]
TAMANIOS_TABLA_WORD = [
    {"valor": "auto", "nombre": "Automático / Adaptativo"},
    {"valor": "7", "nombre": "7 pt"},
    {"valor": "8", "nombre": "8 pt"},
    {"valor": "9", "nombre": "9 pt"},
    {"valor": "10", "nombre": "10 pt (Recomendado)"},
    {"valor": "11", "nombre": "11 pt"},
    {"valor": "12", "nombre": "12 pt"},
]
FUENTES_TABLA_WORD = [
    {"valor": "heredar", "nombre": "Heredar del documento"},
    {"valor": "Calibri", "nombre": "Calibri"},
    {"valor": "Arial", "nombre": "Arial"},
    {"valor": "Times New Roman", "nombre": "Times New Roman"},
    {"valor": "Georgia", "nombre": "Georgia"},
    {"valor": "Aptos", "nombre": "Aptos"},
    {"valor": "Century Gothic", "nombre": "Century Gothic"},
]
ALINEACIONES_PIE_WORD = [
    {"valor": "derecha", "nombre": "Derecha"},
    {"valor": "centro", "nombre": "Centro"},
    {"valor": "izquierda", "nombre": "Izquierda"},
]
POSICIONES_INDICE_WORD = [
    {"valor": "inicio", "nombre": "Al inicio del documento"},
    {"valor": "final", "nombre": "Al final del documento"},
]
ANCHOS_COLUMNA_EXCEL = [
    {"valor": "compacto", "nombre": "Compacto (130 px)"},
    {"valor": "estandar", "nombre": "Estándar (160 px)"},
    {"valor": "amplio", "nombre": "Amplio (220 px)"},
]
TAMANIOS_FUENTE_EXCEL = [
    {"valor": "9", "nombre": "9 pt"},
    {"valor": "10", "nombre": "10 pt (Estándar)"},
    {"valor": "11", "nombre": "11 pt"},
]

# ─────────────────────────────────────────────────────────────────────────────
# 3. TEMAS Y PALETAS PDF (.pdf)
# ─────────────────────────────────────────────────────────────────────────────
PALETAS_EDITORIAL_PDF = {
    "pizarra_carbon": {"nombre": "Pizarra & Carbón", "primario": "#1E293B", "secundario": "#475569", "fondo_suave": "#F8FAFC", "colores": ["#1E293B", "#475569", "#F8FAFC"]},
    "azul_prusia": {"nombre": "Azul Prusia & Acero", "primario": "#1E3A5F", "secundario": "#2B547E", "fondo_suave": "#F0F4F8", "colores": ["#1E3A5F", "#2B547E", "#F0F4F8"]},
    "grafito_salvia": {"nombre": "Grafito & Salvia", "primario": "#1C2E24", "secundario": "#3F5E4D", "fondo_suave": "#F4F7F5", "colores": ["#1C2E24", "#3F5E4D", "#F4F7F5"]},
    "onix_burdeos": {"nombre": "Ónix & Burdeos Imperial", "primario": "#2D1B22", "secundario": "#5C2C38", "fondo_suave": "#FAF6F7", "colores": ["#2D1B22", "#5C2C38", "#FAF6F7"]},
    "negro_papel": {"nombre": "Negro Puro & Papel", "primario": "#0F172A", "secundario": "#334155", "fondo_suave": "#F3F4F6", "colores": ["#0F172A", "#334155", "#F3F4F6"]},
}

ESTILOS_MAQUETACION_PDF = {
    "informe": "Informe Técnico Moderno",
    "academico": "Académico / Booktabs",
    "portada": "Ejecutivo con Portada",
}

MODOS_COLUMNAS_PDF = {
    "estandar": "📄 Estándar (1 Columna)",
    "dos_columnas": "📰 Dos Columnas (2 Col)",
    "paper_cientifico": "🔬 Paper Científico (IEEE / Academic 2 Col)",
    "revista": "🎨 Modo Revista (Editorial Magazine)",
    "premium": "✨ Premium Ejecutivo (Tarjetas + Layout Mixto)",
}

ESTILOS_MAQUETACION_PDF = {
    "informe": "Informe Técnico Moderno",
    "academico": "Académico / Booktabs",
    "portada": "Ejecutivo con Portada",
    "premium": "Premium Consultoría (Tarjetas + Resumen)",
}

FUENTES_PDF = ["Calibri", "Inter", "Roboto", "Georgia", "Times New Roman", "Garamond"]
TAMANIOS_PDF = [10.0, 10.5, 11.0, 12.0]
INTERLINEADOS_PDF = [
    {"valor": 1.0, "nombre": "Sencillo 1.0"},
    {"valor": 1.15, "nombre": "1.15 líneas (Óptimo editorial)"},
    {"valor": 1.5, "nombre": "1.5 líneas"},
    {"valor": 2.0, "nombre": "Doble 2.0"},
]

FORMATOS_NUM_PAGINA_PDF = {
    "pagina_x_de_y": "Página X de Y (ej. Página 1 de 24)",
    "x_de_y": "X / Y (ej. 1 / 24)",
    "x": "Solo número (ej. 1)",
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. PALETAS Y OPCIONES EXCEL (.xlsx)
# ─────────────────────────────────────────────────────────────────────────────
PALETAS_EXCEL = {
    "clasico": {"nombre": "Verde Clásico (Excel)", "cabecera": "107C41", "texto_cab": "FFFFFF", "par": "F4FAF5", "borde": "D1D5DB", "colores": ["#107C41", "#F4FAF5", "#D1D5DB"]},
    "azul": {"nombre": "Azul Ejecutivo", "cabecera": "1E3A8A", "texto_cab": "FFFFFF", "par": "F0F4F8", "borde": "CBD5E1", "colores": ["#1E3A8A", "#F0F4F8", "#CBD5E1"]},
    "gris": {"nombre": "Gris Moderno", "cabecera": "334155", "texto_cab": "FFFFFF", "par": "F8FAFC", "borde": "E2E8F0", "colores": ["#334155", "#F8FAFC", "#E2E8F0"]},
    "esmeralda": {"nombre": "Esmeralda Académico", "cabecera": "046A38", "texto_cab": "FFFFFF", "par": "F0FDF4", "borde": "D1FAE5", "colores": ["#046A38", "#F0FDF4", "#D1FAE5"]},
    "monocromo": {"nombre": "Monocromo Formal", "cabecera": "18181B", "texto_cab": "FFFFFF", "par": "FAFAFA", "borde": "E4E4E7", "colores": ["#18181B", "#FAFAFA", "#E4E4E7"]},
}

MODOS_HOJAS_EXCEL = {
    "multi_hoja": "Una hoja por cada tabla (Recomendado)",
    "hoja_unica": "Todas las tablas en una sola hoja continua",
}


REGISTRO_OPCIONES = {
    "html": {
        "temas": TEMAS_HTML,
        "anchos": ANCHOS_HTML,
        "paletas_tricolor": PALETAS_HTML_TRICOLOR,
        "fuentes": FUENTES_HTML,
        "tamanios": [10, 11, 12],
        "interlineados": [1.4, 1.6, 1.8],
        "defaults": {
            "tema": "defecto",
            "ancho": "900px",
            "paleta_tricolor": "tema_default",
            "fuente": "system-ui, -apple-system, sans-serif",
            "tamanio": 11,
            "interlineado": 1.6,
            "footer_izq": "MarkFlow AI 2026",
            "footer_der": "Ing. Patricio Sarmiento Reinoso, Mgst.",
            "justificado": True,
            "numerar_ecuaciones": False,
        },
    },
    "word": {
        "temas": TEMAS_WORD,
        "paletas_tablas": PALETAS_TABLAS_WORD,
        "paletas_titulos": PALETAS_TITULOS_WORD,
        "fuentes": FUENTES_WORD,
        "tamanios": TAMANIOS_WORD,
        "interlineados": INTERLINEADOS_WORD,
        "alineaciones": ALINEACIONES_WORD,
        "tamanios_tabla": TAMANIOS_TABLA_WORD,
        "fuentes_tabla": FUENTES_TABLA_WORD,
        "alineaciones_pie": ALINEACIONES_PIE_WORD,
        "posiciones_indice": POSICIONES_INDICE_WORD,
        "defaults": {
            "tema": "defecto",
            "paleta_suave": True,
            "paleta_tabla": "defecto",
            "modo_color_titulos": "negro",
            "color_titulos": "negro",
            "fuente": "Calibri",
            "tamanio": 11,
            "interlineado": 1.0,
            "alineacion": "justificado",
            "fuente_tabla": "heredar",
            "tamanio_tabla": "10",
            "pie_pagina": "",
            "alineacion_pie": "derecha",
            "numerar_ecuaciones": False,
            "apa7": False,
            "crear_indice": False,
            "posicion_indice": "inicio",
            "numerar_paginas": True,
        },
    },
    "pdf": {
        "paletas": PALETAS_EDITORIAL_PDF,
        "estilos": ESTILOS_MAQUETACION_PDF,
        "modos_columnas": MODOS_COLUMNAS_PDF,
        "portada_premium": {
            "temas": {
                "clasica_blanca": "Clásica Blanca (ejemplo actual)",
                "ejecutiva_navy": "Ejecutiva Navy",
                "consultoria_verde": "Consultoría Verde / Agua",
                "blueprint": "Blueprint Técnico",
                "foto_hero": "Foto Hero",
                "minimal_slate": "Minimal Slate",
            },
            "layouts_fotos": {
                "1": "1 foto centrada grande",
                "2": "2 fotos lado a lado",
                "3": "2 arriba + 1 centrada abajo",
                "4": "Grid 2x2",
                "5": "2x2 + 1 centrada abajo",
                "6": "Grid 3x2",
            },
            "defaults": {
                "incluir": False,
                "tema": "clasica_blanca",
                "tipo_documento": "ESTUDIO DE CONSULTORÍA DEL PROYECTO:",
                "titulo_proyecto": "",
                "memoria_fase": "",
                "componente": "",
                "consultor": "",
                "fecha": "",
                "codigo_proyecto": "",
            },
        },
        "fuentes": FUENTES_PDF,
        "tamanios": TAMANIOS_PDF,
        "interlineados": INTERLINEADOS_PDF,
        "formatos_num": FORMATOS_NUM_PAGINA_PDF,
        "defaults": {
            "paleta": "pizarra_carbon",
            "estilo": "informe",
            "modo_columnas": "estandar",
            "fuente": "Calibri",
            "tamanio": 11.0,
            "interlineado": 1.15,
            "pie_pagina": "",
            "alineacion_pie": "izquierda",
            "salto_capitulo": True,
            "justificado": True,
            "numerar_paginas": True,
            "running_header": True,
            "texto_running_header": "",
            "formato_num": "pagina_x_de_y",
            "alineacion_num": "derecha",
        },
    },
    "excel": {
        "paletas": PALETAS_EXCEL,
        "modos_hojas": MODOS_HOJAS_EXCEL,
        "anchos_columna": ANCHOS_COLUMNA_EXCEL,
        "tamanios_fuente": TAMANIOS_FUENTE_EXCEL,
        "defaults": {
            "estilo": "clasico",
            "fuente": "Calibri",
            "tamanio": 10,
            "modo_hojas": "multi_hoja",
        },
    },
}


_CLAVES_OPCIONES = {
    "temas", "anchos", "paletas", "paletas_tricolor", "paletas_titulos",
    "paletas_tablas", "estilos", "modos_columnas", "formatos_num",
    "modos_hojas", "alineaciones", "fuentes_tabla", "tamanios_tabla",
    "alineaciones_pie", "posiciones_indice", "anchos_columna",
    "tamanios_fuente", "interlineados", "fuentes", "tamanios",
}


def _a_lista_opciones(valor):
    if isinstance(valor, list):
        return valor
    if isinstance(valor, dict):
        salida = []
        for clave, dato in valor.items():
            if isinstance(dato, dict):
                salida.append({"valor": clave, **dato})
            else:
                salida.append({"valor": clave, "nombre": dato})
        return salida
    return valor


def _normalizar_arbol_registro(arbol: dict) -> dict:
    arbol = copy.deepcopy(arbol)
    for formato, seccion in arbol.items():
        if not isinstance(seccion, dict):
            continue
        for clave in list(seccion.keys()):
            if clave in _CLAVES_OPCIONES:
                seccion[clave] = _a_lista_opciones(seccion[clave])
    return arbol


def obtener_registro_completo() -> dict:
    """Devuelve el árbol completo del registro único serializable a JSON."""
    return _normalizar_arbol_registro(REGISTRO_OPCIONES)


def obtener_arbol_opciones() -> dict:
    """Alias para obtener el árbol de opciones registrado."""
    return REGISTRO_OPCIONES


def obtener_defaults(formato: str) -> dict:
    """Obtiene el diccionario de valores por defecto para un formato."""
    formato_k = str(formato).lower().strip()
    if formato_k in REGISTRO_OPCIONES:
        return dict(REGISTRO_OPCIONES[formato_k].get("defaults", {}))
    return {}

