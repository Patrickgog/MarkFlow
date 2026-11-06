"""Motor de Plantillas y Placeholders Dinámicos para MarkFlow Office.

Permite detectar candidatos a placeholders en Markdown, normalizar nombres,
generar y leer datasets estructurados en Excel (.xlsx) y JSON, validar
consistencia de datos por proyecto y sustituir de forma segura protegiendo
bloques de código y fórmulas matemáticas.
"""

from __future__ import annotations

import io
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


@dataclass
class PlaceholderDef:
    """Definición de un placeholder detectado o configurado."""
    nombre: str
    etiqueta: str
    tipo: str = "texto"          # texto, numero, fecha, identificador, moneda
    unidad: Optional[str] = None # ej: l/s, m, US$, $
    grupo: str = "Datos generales"
    confianza: str = "alta"      # alta, media, baja
    valor_original: str = ""
    ocurrencias: int = 1


@dataclass
class CandidatoDeteccion:
    """Candidato a placeholder extraído heurísticamente del documento."""
    texto_encontrado: str
    nombre_sugerido: str
    tipo_sugerido: str
    unidad_sugerida: Optional[str] = None
    confianza: str = "alta"
    ocurrencias: int = 1
    seleccionado: bool = True
    contexto: str = ""


@dataclass
class ResultadoValidacion:
    """Resultado del contraste entre plantilla y datos de un proyecto."""
    completos: List[str] = field(default_factory=list)
    vacios: List[str] = field(default_factory=list)
    tipo_incorrecto: List[Dict[str, str]] = field(default_factory=list)
    sobrantes: List[str] = field(default_factory=list)
    desconocidos: List[str] = field(default_factory=list)

    @property
    def resumen_texto(self) -> str:
        partes = [
            f"{len(self.completos)} completos",
            f"{len(self.vacios)} vacíos",
        ]
        if self.tipo_incorrecto:
            partes.append(f"{len(self.tipo_incorrecto)} con tipo incorrecto")
        if self.sobrantes:
            partes.append(f"{len(self.sobrantes)} sobrantes")
        return " · ".join(partes)


# ---------------------------------------------------------------------------
# Normalización y nombres seguros
# ---------------------------------------------------------------------------

def normalizar_nombre_placeholder(texto: str) -> str:
    """Normaliza un texto a un identificador seguro para placeholders:

    - Minúsculas, números y guión bajo.
    - Sin tildes ni caracteres especiales (ñ -> n).
    - Máximo 60 caracteres.
    - No inicia ni termina con guión bajo repetido.
    """
    if not texto:
        return "dato"

    # Sustitución explícita de ñ/Ñ antes de normalizar
    s = texto.replace("ñ", "n").replace("Ñ", "n")
    # Descomposición unicode para retirar tildes
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    s = s.lower()
    # Reemplazar cualquier caracter no alfanumérico por guión bajo
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    # Limitar longitud a 60 caracteres
    s = s[:60].rstrip("_")
    return s or "dato"


def slug_archivo(texto: str) -> str:
    """Genera un slug seguro para nombres de archivo."""
    s = normalizar_nombre_placeholder(texto)
    return s.replace("_", "-") or "proyecto"


# ---------------------------------------------------------------------------
# Protección de zonas intocables (código y matemáticas)
# ---------------------------------------------------------------------------

RE_BLOQUES_IGNORADOS = re.compile(
    r"(```[\s\S]*?```|"        # Bloque de código cercado
    r"`[^`\n]+`|"              # Código en línea
    r"\$\$[\s\S]*?\$\$|"       # Matemáticas display $$...$$
    r"\\\[[\s\S]*?\\\]|"       # Matemáticas display \[...\]
    r"\\\([\s\S]*?\\\))",      # Matemáticas inline \(...\)
    re.MULTILINE
)


def aislar_zonas_protegidas(markdown_texto: str) -> Tuple[str, List[str]]:
    """Reemplaza bloques de código y fórmulas por marcadores seguros efímeros."""
    protegidos: List[str] = []

    def _remplazo(match: re.Match) -> str:
        idx = len(protegidos)
        protegidos.append(match.group(0))
        return f"@@PROTEGIDO_MARKFLOW_{idx}@@"

    texto_aislado = RE_BLOQUES_IGNORADOS.sub(_remplazo, markdown_texto)
    return texto_aislado, protegidos


def restaurar_zonas_protegidas(texto_aislado: str, protegidos: List[str]) -> str:
    """Restaura los bloques de código y fórmulas matemáticas originales."""
    for idx, original in enumerate(protegidos):
        texto_aislado = texto_aislado.replace(f"@@PROTEGIDO_MARKFLOW_{idx}@@", original)
    return texto_aislado


# ---------------------------------------------------------------------------
# Detección heurística de candidatos a placeholder
# ---------------------------------------------------------------------------

PATRONES_DETECCION = [
    # 1. Etiqueta seguida de valor: "Proyecto: Hidrosanitario Norte"
    (
        "etiqueta_valor",
        re.compile(
            r"^(?:[-*]\s*)?(?P<etiqueta>[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,30}):\s*(?P<valor>[^\n\r]+)$",
            re.MULTILINE
        ),
        "alta",
        "texto"
    ),
    # 2. Número con unidad (caudal, longitud, etc.): "12.5 l/s", "3.20 m", "45.00 m3/h"
    (
        "numero_unidad",
        re.compile(
            r"\b(?P<valor>\d+(?:[.,]\d+)?)\s*(?P<unidad>l/s|L/s|m3/s|m3/h|m3|m2|m|km|ha|kg|ton|hab|mg/l|NTU|%)\b"
        ),
        "alta",
        "numero"
    ),
    # 3. Moneda: "US$ 4500", "$ 1200.50", "USD 4500.00"
    (
        "moneda",
        re.compile(
            r"\b(?P<unidad>US\$|\$|USD)\s*(?P<valor>\d+(?:[.,]\d{2,3})*(?:[.,]\d{1,2})?)\b"
        ),
        "alta",
        "moneda"
    ),
    # 4. RUC ecuatoriano (13 dígitos)
    (
        "ruc",
        re.compile(r"\b(?P<valor>\d{13})\b"),
        "alta",
        "identificador"
    ),
    # 5. Cédula ecuatoriana (10 dígitos)
    (
        "cedula",
        re.compile(r"\b(?P<valor>\d{10})\b"),
        "alta",
        "identificador"
    ),
    # 6. Correo electrónico
    (
        "email",
        re.compile(r"\b(?P<valor>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b"),
        "alta",
        "texto"
    ),
    # 7. Teléfono
    (
        "telefono",
        re.compile(r"\b(?P<valor>(?:\+593|0)\s*(?:9\d{8}|[2-7]\d{7}))\b"),
        "alta",
        "texto"
    ),
    # 8. Fechas estándar (dd/mm/aaaa, dd-mm-aaaa, 25 de octubre de 2026)
    (
        "fecha",
        re.compile(
            r"\b(?P<valor>\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+de\s+[a-zA-Záéíóú]+\s+de\s+\d{4})\b",
            re.IGNORECASE
        ),
        "alta",
        "fecha"
    ),
    # 9. Coordenadas geográficas simples: -0.2201, -78.5123
    (
        "coordenadas",
        re.compile(r"\b(?P<valor>-?\d{1,3}\.\d{3,7}\s*,\s*-?\d{1,3}\.\d{3,7})\b"),
        "alta",
        "texto"
    ),
    # 10. Número suelto sin unidad (baja confianza)
    (
        "numero_suelto",
        re.compile(r"(?<![A-Za-z0-9_.-])(?P<valor>\d{2,6})(?![A-Za-z0-9_.-])"),
        "baja",
        "numero"
    )
]


def detectar_candidatos(markdown_texto: str) -> List[CandidatoDeteccion]:
    """Detecta candidatos a placeholders en el texto Markdown protegiendo matemáticas y código."""
    texto_aislado, _ = aislar_zonas_protegidas(markdown_texto)

    candidatos_map: Dict[str, CandidatoDeteccion] = {}
    nombres_usados: Set[str] = set()

    # Pre-limpieza: ignorar líneas de encabezados (# Título) para evitar capturar números de capítulo
    lineas_limpias: List[str] = []
    for linea in texto_aislado.splitlines():
        if re.match(r"^\s*#{1,6}\s+", linea):
            # Línea de título Markdown: no buscar candidatos
            continue
        lineas_limpias.append(linea)
    texto_filtrado = "\n".join(lineas_limpias)

    # 1. Etiquetas seguidas de valor (mayor precisión semántica)
    for match in PATRONES_DETECCION[0][1].finditer(texto_filtrado):
        etiqueta = match.group("etiqueta").strip()
        valor = match.group("valor").strip()
        if not valor or len(valor) > 120:
            continue
        # Descartar si el valor es solo puntuación o markdown
        if valor.startswith(("|", "```", "#", ">")):
            continue

        nombre_sug = normalizar_nombre_placeholder(etiqueta)
        if nombre_sug not in nombres_usados:
            nombres_usados.add(nombre_sug)

        clave = valor.strip().lower()
        if clave not in candidatos_map:
            candidatos_map[clave] = CandidatoDeteccion(
                texto_encontrado=valor,
                nombre_sugerido=nombre_sug,
                tipo_sugerido="texto",
                unidad_sugerida=None,
                confianza="alta",
                ocurrencias=1,
                seleccionado=True,
                contexto=f"{etiqueta}: {valor}"
            )
        else:
            candidatos_map[clave].ocurrencias += 1

    # 2. Otros patrones específicos (moneda, número con unidad, RUC, fechas, etc.)
    for nombre_patron, regex, confianza_def, tipo_def in PATRONES_DETECCION[1:]:
        for match in regex.finditer(texto_filtrado):
            valor = match.group("valor").strip()
            if not valor:
                continue

            # Evitar capturar años de 4 dígitos como números sueltos de alta prioridad
            if nombre_patron == "numero_suelto" and re.match(r"^(19|20)\d{2}$", valor):
                confianza_actual = "baja"
                seleccionado = False
            else:
                confianza_actual = confianza_def
                seleccionado = (confianza_actual != "baja")

            unidad = None
            if "unidad" in match.groupdict() and match.group("unidad"):
                unidad = match.group("unidad").strip()

            clave = valor.lower()
            if clave in candidatos_map:
                candidatos_map[clave].ocurrencias += 1
                if unidad and not candidatos_map[clave].unidad_sugerida:
                    candidatos_map[clave].unidad_sugerida = unidad
                continue

            # Generar sugerencia de nombre
            if nombre_patron == "moneda":
                nombre_sug = "presupuesto_referencial"
            elif nombre_patron == "numero_unidad":
                nombre_sug = f"valor_{unidad.lower().replace('/', '_')}" if unidad else "medida"
            elif nombre_patron == "ruc":
                nombre_sug = "numero_ruc"
            elif nombre_patron == "cedula":
                nombre_sug = "numero_cedula"
            elif nombre_patron == "email":
                nombre_sug = "correo_electronico"
            elif nombre_patron == "telefono":
                nombre_sug = "telefono_contacto"
            elif nombre_patron == "fecha":
                nombre_sug = "fecha_documento"
            elif nombre_patron == "coordenadas":
                nombre_sug = "coordenadas_sitio"
            else:
                nombre_sug = "dato_numerico"

            # Resolver colisión de nombre
            base_sug = normalizar_nombre_placeholder(nombre_sug)
            final_sug = base_sug
            sufijo = 1
            while final_sug in nombres_usados:
                sufijo += 1
                final_sug = f"{base_sug}_{sufijo}"
            nombres_usados.add(final_sug)

            candidatos_map[clave] = CandidatoDeteccion(
                texto_encontrado=valor,
                nombre_sugerido=final_sug,
                tipo_sugerido=tipo_def,
                unidad_sugerida=unidad,
                confianza=confianza_actual,
                ocurrencias=1,
                seleccionado=seleccionado,
                contexto=match.group(0)
            )

    # Ordenar candidatos: primero alta confianza, luego media, luego baja
    orden_conf = {"alta": 0, "media": 1, "baja": 2}
    candidatos_ordenados = sorted(
        candidatos_map.values(),
        key=lambda c: (orden_conf.get(c.confianza, 3), -c.ocurrencias, c.nombre_sugerido)
    )
    return candidatos_ordenados


# ---------------------------------------------------------------------------
# Creación de Plantilla Markdown (.md)
# ---------------------------------------------------------------------------

def aplicar_placeholders_a_markdown(
    markdown_texto: str,
    reemplazos: List[Tuple[str, str]]  # Lista de (texto_original, nombre_placeholder)
) -> str:
    """Convierte ocurrencias de texto original en placeholders {{nombre}}

    protegiendo intactos los bloques de código y fórmulas matemáticas.
    """
    texto_aislado, protegidos = aislar_zonas_protegidas(markdown_texto)

    # Ordenar por longitud descendente para evitar reemplazos parciales
    reemplazos_ordenados = sorted(reemplazos, key=lambda r: len(r[0]), reverse=True)

    for texto_orig, nombre_ph in reemplazos_ordenados:
        if not texto_orig or not nombre_ph:
            continue
        nombre_limpio = normalizar_nombre_placeholder(nombre_ph)
        # Sustituir con límite de palabra si es alfanumérico, o literal con re.escape
        patron = re.escape(texto_orig)
        texto_aislado = re.sub(patron, f"{{{{{nombre_limpio}}}}}", texto_aislado)

    return restaurar_zonas_protegidas(texto_aislado, protegidos)


# ---------------------------------------------------------------------------
# Generación y Lectura de Excel (.xlsx) estructurado
# ---------------------------------------------------------------------------

def generar_excel_plantilla(
    placeholders: List[PlaceholderDef],
    proyectos: Dict[str, Dict[str, Any]]
) -> bytes:
    """Genera el archivo Excel estructurado (columna A: placeholder, columnas B+: proyectos).

    - Hoja única: 'Datos'
    - Cabecera en negrita, fondo #eef0fa, bordes sutiles
    - Ancho automático en columna A y espacioso para proyectos.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Datos"
    ws.views.sheetView[0].showGridLines = True

    # Estilos
    fuente_cabecera = Font(name="Segoe UI", size=11, bold=True, color="1E293B")
    relleno_cabecera = PatternFill(start_color="EEF0FA", end_color="EEF0FA", fill_type="solid")
    fuente_datos = Font(name="Segoe UI", size=10, color="0F172A")
    fuente_placeholder = Font(name="Consolas", size=10, bold=True, color="4338CA")
    relleno_placeholder = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    borde_fino = Side(border_style="thin", color="CBD5E1")
    borde_celda = Border(left=borde_fino, right=borde_fino, top=borde_fino, bottom=borde_fino)

    # Encabezados: Columna A siempre 'placeholder', Columnas B+ nombres de proyectos
    nombres_proyectos = list(proyectos.keys()) if proyectos else ["Proyecto 1"]
    cabeceras = ["placeholder"] + nombres_proyectos
    ws.append(cabeceras)

    # Filas de datos
    for ph in placeholders:
        fila = [ph.nombre]
        for p_nombre in nombres_proyectos:
            val = proyectos.get(p_nombre, {}).get(ph.nombre, "")
            fila.append(val if val is not None else "")
        ws.append(fila)

    # Aplicar estilos
    # Cabecera
    for col_idx in range(1, len(cabeceras) + 1):
        celda = ws.cell(row=1, column=col_idx)
        celda.font = fuente_cabecera
        celda.fill = relleno_cabecera
        celda.alignment = Alignment(horizontal="center" if col_idx > 1 else "left", vertical="center")
        celda.border = borde_celda

    # Cuerpo
    for row_idx in range(2, len(placeholders) + 2):
        # Columna A (placeholder)
        celda_a = ws.cell(row=row_idx, column=1)
        celda_a.font = fuente_placeholder
        celda_a.fill = relleno_placeholder
        celda_a.border = borde_celda
        celda_a.alignment = Alignment(horizontal="left", vertical="center")

        # Columnas de proyecto
        for col_idx in range(2, len(cabeceras) + 1):
            celda = ws.cell(row=row_idx, column=col_idx)
            celda.font = fuente_datos
            celda.border = borde_celda
            celda.alignment = Alignment(horizontal="left", vertical="center")

    # Ajuste automático de anchos de columna
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 18)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def leer_excel_plantilla(contenido_bytes: bytes) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
    """Lee un libro Excel (.xlsx) con la estructura:

    Columna A: placeholder
    Columnas B+: proyectos
    Devuelve: (lista_ordenada_placeholders, dict_proyectos)
    """
    wb = openpyxl.load_workbook(io.BytesIO(contenido_bytes), data_only=True)
    # Preferir hoja llamada "Datos" o tomar la primera
    if "Datos" in wb.sheetnames:
        ws = wb["Datos"]
    else:
        ws = wb.active

    placeholders: List[str] = []
    proyectos: Dict[str, Dict[str, Any]] = {}

    max_col = ws.max_column
    max_row = ws.max_row

    if max_col < 1 or max_row < 2:
        return ([], {})

    # Leer encabezados de proyectos (columnas 2 en adelante)
    proyectos_cols: List[Tuple[int, str]] = []
    for c in range(2, max_col + 1):
        nombre_proj = ws.cell(row=1, column=c).value
        nombre_proj_str = str(nombre_proj).strip() if nombre_proj is not None else f"Proyecto {c-1}"
        proyectos_cols.append((c, nombre_proj_str))
        proyectos[nombre_proj_str] = {}

    # Si solo hay columna A, crear un "Proyecto 1" vacío
    if not proyectos_cols:
        proyectos["Proyecto 1"] = {}
        proyectos_cols.append((2, "Proyecto 1"))

    # Leer filas
    for r in range(2, max_row + 1):
        val_ph = ws.cell(row=r, column=1).value
        if val_ph is None:
            continue
        nombre_ph = normalizar_nombre_placeholder(str(val_ph))
        if not nombre_ph:
            continue
        placeholders.append(nombre_ph)

        for col_idx, nombre_proj in proyectos_cols:
            val_celda = ws.cell(row=r, column=col_idx).value
            if val_celda is not None:
                val_limpio = str(val_celda).strip()
                proyectos[nombre_proj][nombre_ph] = val_limpio
            else:
                proyectos[nombre_proj][nombre_ph] = ""

    return (placeholders, proyectos)


# ---------------------------------------------------------------------------
# Generación y Lectura de JSON
# ---------------------------------------------------------------------------

def generar_json_plantilla(
    nombre_plantilla: str,
    placeholders: List[PlaceholderDef],
    proyectos: Dict[str, Dict[str, Any]]
) -> str:
    """Genera la especificación JSON estructurada."""
    payload = {
        "plantilla": normalizar_nombre_placeholder(nombre_plantilla),
        "version": 1,
        "placeholders": [
            {
                "nombre": ph.nombre,
                "etiqueta": ph.etiqueta or ph.nombre.replace("_", " ").capitalize(),
                "tipo": ph.tipo,
                "unidad": ph.unidad,
                "grupo": ph.grupo
            }
            for ph in placeholders
        ],
        "proyectos": proyectos
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def leer_json_plantilla(contenido_json: str) -> Tuple[List[PlaceholderDef], Dict[str, Dict[str, Any]]]:
    """Parsea una especificación JSON de plantilla y datos."""
    data = json.loads(contenido_json)
    phs: List[PlaceholderDef] = []
    for p in data.get("placeholders", []):
        phs.append(
            PlaceholderDef(
                nombre=normalizar_nombre_placeholder(p.get("nombre", "")),
                etiqueta=p.get("etiqueta", ""),
                tipo=p.get("tipo", "texto"),
                unidad=p.get("unidad"),
                grupo=p.get("grupo", "Datos generales")
            )
        )
    proyectos = data.get("proyectos", {})
    return (phs, proyectos)


# ---------------------------------------------------------------------------
# Extracción de Placeholders desde un archivo Markdown existente
# ---------------------------------------------------------------------------

RE_PLACEHOLDER = re.compile(r"(?<!\\)\{\{\s*([a-zA-Z0-9_]{1,60})\s*\}\}")


def extraer_placeholders_de_markdown(markdown_texto: str) -> List[str]:
    """Extrae todos los nombres de placeholders {{nombre}} en el documento,

    respetando escapes \\{{ y aislando bloques de código y fórmulas.
    Mantiene el orden de aparición sin duplicados.
    """
    texto_aislado, _ = aislar_zonas_protegidas(markdown_texto)
    encontrados: List[str] = []
    vistos: Set[str] = set()

    for match in RE_PLACEHOLDER.finditer(texto_aislado):
        ph = normalizar_nombre_placeholder(match.group(1))
        if ph and ph not in vistos:
            vistos.add(ph)
            encontrados.append(ph)

    return encontrados


# ---------------------------------------------------------------------------
# Validación de Datos vs. Plantilla
# ---------------------------------------------------------------------------

def validar_tipo_dato(valor: Any, tipo_esperado: str) -> bool:
    """Valida si un valor cumple con el tipo de dato asignado."""
    if valor is None or str(valor).strip() == "":
        return False
    val_str = str(valor).strip()

    if tipo_esperado == "numero":
        val_norm = val_str.replace(",", ".")
        try:
            float(val_norm)
            return True
        except ValueError:
            return False

    elif tipo_esperado == "moneda":
        # Remover símbolos de moneda y espacios
        val_norm = re.sub(r"^[^\d.,-]+", "", val_str).strip()
        val_norm = val_norm.replace(",", ".")
        try:
            float(val_norm)
            return True
        except ValueError:
            return False

    elif tipo_esperado == "identificador":
        # RUC (13 dígitos) o Cédula (10 dígitos)
        return bool(re.match(r"^\d{10}(\d{3})?$", val_str))

    elif tipo_esperado == "fecha":
        # Formatos dd/mm/aaaa, aaaa-mm-dd o fecha en texto
        return bool(
            re.match(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$", val_str) or
            re.match(r"^\d{4}-\d{2}-\d{2}$", val_str) or
            re.search(r"\bde\b", val_str, re.IGNORECASE)
        )

    # Por defecto, cualquier cadena no vacía es texto válido
    return True


def validar_proyecto(
    placeholders_plantilla: List[str],
    datos_proyecto: Dict[str, Any],
    diccionario_tipos: Optional[Dict[str, str]] = None
) -> ResultadoValidacion:
    """Valida un proyecto contra la plantilla según la sección 7.2:

    - ✅ Completo: placeholder con valor válido.
    - 🟥 Vacío: placeholder sin valor en el proyecto.
    - ⚠️ Tipo incorrecto: valor que no cumple el tipo esperado.
    - ℹ️ Sobrante: dato en el dataset que la plantilla no usa.
    - ❓ Desconocido: placeholder en plantilla sin dato en el dataset.
    """
    res = ResultadoValidacion()
    tipos = diccionario_tipos or {}

    set_plantilla = set(placeholders_plantilla)
    set_datos = set(datos_proyecto.keys())

    # Sobrantes
    for d in set_datos:
        if d not in set_plantilla:
            res.sobrantes.append(d)

    # Placeholders de la plantilla
    for ph in placeholders_plantilla:
        if ph not in datos_proyecto:
            res.desconocidos.append(ph)
            res.vacios.append(ph)
            continue

        val = datos_proyecto.get(ph)
        if val is None or str(val).strip() == "":
            res.vacios.append(ph)
            continue

        tipo_esp = tipos.get(ph, "texto")
        if tipo_esp != "texto" and not validar_tipo_dato(val, tipo_esp):
            res.tipo_incorrecto.append({
                "placeholder": ph,
                "valor": str(val),
                "tipo_esperado": tipo_esp
            })
        else:
            res.completos.append(ph)

    return res


# ---------------------------------------------------------------------------
# Motor de Fusión y Sustitución de Placeholders
# ---------------------------------------------------------------------------

def fusionar_plantilla_con_datos(
    markdown_plantilla: str,
    datos_proyecto: Dict[str, Any],
    formato_salida: str = "html"  # html, word, pdf, markdown
) -> str:
    """Sustituye placeholders {{nombre}} por los valores provistos.

    Reglas técnicas aplicadas:
    - No reemplaza dentro de bloques matemáticos ($$...$$, \\(...\\)) ni código.
    - Tolera espacios: {{ nombre }} y {{nombre}} son equivalentes.
    - Vacíos: marca en rojo el espacio con [nombre] sin bloquear la generación (Sección 7.3).
    - Des-escapa \\{{ a {{ literal.
    """
    texto_aislado, protegidos = aislar_zonas_protegidas(markdown_plantilla)

    def _sustituir_ph(match: re.Match) -> str:
        ph_crudo = match.group(1).strip()
        ph_norm = normalizar_nombre_placeholder(ph_crudo)
        val = datos_proyecto.get(ph_norm)

        # Si no existe o es vacío, aplicar marcado en rojo
        if val is None or str(val).strip() == "":
            if formato_salida in ("html", "pdf"):
                return (
                    f'<span class="placeholder-vacio" '
                    f'style="background: #fee2e2; color: #dc2626; padding: 0.1rem 0.35rem; '
                    f'border-radius: 4px; font-weight: 600; font-family: monospace;">[{ph_norm}]</span>'
                )
            elif formato_salida == "word":
                # En Word, HTML inline con span de color rojo es interpretado por el motor
                return f'<span style="color: #dc2626; font-weight: bold;">[{ph_norm}]</span>'
            else:
                # Markdown puro
                return f'<span style="color:red">[{ph_norm}]</span>'

        return str(val)

    # Sustitución de placeholders
    texto_reemplazado = RE_PLACEHOLDER.sub(_sustituir_ph, texto_aislado)

    # Des-escapar \{{ a {{
    texto_reemplazado = texto_reemplazado.replace(r"\{{", "{{")

    return restaurar_zonas_protegidas(texto_reemplazado, protegidos)
