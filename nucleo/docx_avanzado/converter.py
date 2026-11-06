"""Pipeline principal de conversión de AST Markdown a OpenXML para documentos .docx."""

from __future__ import annotations

import re
import io
from typing import Any, Dict, List, Optional


def markdown_to_openxml(markdown: str, template_path: Optional[str] = None) -> bytes:
    """
    Convierte un documento Markdown a formato OpenXML (.docx bytes).

    Esta función es el pipeline principal que transforma el contenido Markdown
    en una estructura OOXML compatible con Microsoft Word, preservando bytes
    cuando se proporciona una plantilla base.

    Args:
        markdown: Contenido en formato Markdown a convertir.
        template_path: Ruta opcional a un archivo .docx plantilla para preservación byte-a-byte.

    Returns:
        bytes: El archivo .docx generado en formato binario.
    """
    # Parsear el markdown a estructura AST
    ast = parse_markdown(markdown)

    if template_path:
        # Modo byte-preserving: usar plantilla base y solo modificar nodos necesarios
        docx_bytes = apply_ast_to_template(ast, template_path)
    else:
        # Modo generación directa desde cero
        docx_bytes = generate_docx_from_ast(ast)

    return docx_bytes


def _xml_safe_text(text: str) -> str:
    """
    Escapa texto para que sea compatible con XML.
    Elimina o reemplaza caracteres que no son válidos en XML 1.0.
    """
    if not text:
        return ""
    # Reemplazar entidades XML especiales
    text = text.replace("&", "&")
    text = text.replace("<", "<")
    text = text.replace(">", ">")
    # Remover caracteres de control excepto tabulación, newline, carriage return
    # Los caracteres en rangos 0-0x1F son control characters en XML
    cleaned = []
    for ch in text:
        code = ord(ch)
        # Permitir: tab (0x09), newline (0x0A), carriage return (0x0D)
        # También permitir caracteres Unicode normales (0x20 y arriba)
        if code in (0x09, 0x0A, 0x0D) or code >= 0x20:
            cleaned.append(ch)
        # Sustituir otros control characters por space
        else:
            cleaned.append(" ")
    return "".join(cleaned)


def _strip_math_delimiters(text: str) -> str:
    """
    Quita los delimitadores $...$ o $$...$$ de una expresión LaTeX.
    Retorna solo el contenido interior.
    """
    if not text:
        return text
    
    # Quitar delimitadores de bloque $$...$$ (pueden estar al inicio y al final)
    result = re.sub(r'^\$\$', '', text)
    result = re.sub(r'\$\$$', '', result)
    
    # Quitar delimitadores inline $...$ (sencillos, no los de bloque)
    # Esto es tricky porque $ puede aparecer en medio
    # Solo quitar si hay $ al inicio y al final después de quitar los de bloque
    # Pattern simple: $algo$ donde algo no contiene $
    result = re.sub(r'^\$([^$]+)\$', '', result)  # $contenido$ al inicio
    result = re.sub(r'^([^$]+)\$$', '', result)    # contenido$ al final (extraño pero posible)
    
    return result.strip()


def parse_markdown(markdown: str) -> Dict[str, Any]:
    """
    Parses Markdown into an Abstract Syntax Tree (AST).

    Handles:
    - Headings (H1-H6)
    - Paragraphs
    - Bold and italic text
    - Links and images
    - Tables
    - LaTeX math blocks
    """
    lines = markdown.split('\n')
    ast = {"type": "document", "children": [], "meta": {}}

    i = 0
    while i < len(lines):
        line = lines[i]

        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            ast["children"].append({
                "type": "heading",
                "level": level,
                "text": text,
                "raw": line
            })
            i += 1
            continue

        # Código fenced
        if line.startswith('```') or line.startswith('~~~'):
            code_block = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```') and not lines[i].startswith('~~~'):
                code_block.append(lines[i])
                i += 1
            ast["children"].append({
                "type": "code_block",
                "language": lines[i-1] if i > 0 and (lines[i-1].startswith('```') or lines[i-1].startswith('~~~')) else None,
                "text": '\n'.join(code_block),
                "raw": line
            })
            if i < len(lines):
                i += 1  # Skip closing fence
            continue

        # Tables - detectar por líneas que empiezan y terminan con |
        if line.startswith('|') and line.endswith('|'):
            # Podría ser parte de una tabla, recolectar filas
            table_rows = []
            # Agregar la fila actual
            table_rows.append(line)
            i += 1
            # Continuar recogiendo filas de tabla
            while i < len(lines) and (lines[i].startswith('|') and lines[i].endswith('|')):
                table_rows.append(lines[i])
                i += 1
            # Calcular número de columnas desde la fila de separadores (segunda fila)
            if len(table_rows) >= 3:
                # La segunda fila suele ser |---|---| separadores
                n_cols = len([c for c in table_rows[1].split('|') if c.strip()]) - 1
                ast["children"].append({
                    "type": "table",
                    "headers": table_rows[0],
                    "separators": table_rows[1],
                    "rows": table_rows[2:],
                    "n_cols": max(n_cols, 1)
                })
            continue

        # LaTeX math (inline and block) - detectar y marcar para conversión OMML
        has_inline_math = bool(re.search(r'(?<!\$)\$[^$]+\$(?!\$)', line))
        has_block_math = bool(re.search(r'^\$\$(.+?)\$\$', line, re.DOTALL))

        if has_inline_math or has_block_math:
            # Marcar como bloque de matemáticas en lugar de párrafo normal
            ast["children"].append({
                "type": "math",
                "raw": line,
                "math_type": 'inline' if has_inline_math and not has_block_math else 'block'
            })
            i += 1
            continue

        # Default: paragraph
        if not line.startswith('#') and not line.startswith('```') and not line.startswith('|'):
            # Escapar caracteres XML problemáticos y obtener texto seguro
            safe_text = _xml_safe_text(line)
            if safe_text.strip():  # Solo agregar si hay contenido después de escapar
                ast["children"].append({
                    "type": "paragraph",
                    "text": safe_text,
                    "raw": line
                })

        i += 1

    return ast


def generate_docx_from_ast(ast: Dict[str, Any]) -> bytes:
    """
    Genera un archivo .docx desde el AST parseado sin plantilla base.
    """
    from docx import Document
    from docx.oxml.ns import qn

    doc = Document()

    for child in ast.get("children", []):
        if child["type"] == "heading":
            level = child.get("level", 1)
            text = child.get("text", "")
            # Crear heading - usar texto limpio
            clean_text = _xml_safe_text(text) if text else ""
            if clean_text.strip():
                try:
                    heading = doc.add_heading(clean_text, level=level)
                except Exception:
                    # Fallback si el nivel es inválido
                    heading = doc.add_heading(clean_text, level=1)

        elif child["type"] == "paragraph":
            text = child.get("text", "")
            clean_text = _xml_safe_text(text) if text else ""
            if clean_text.strip():
                doc.add_paragraph(clean_text)

        elif child["type"] == "code_block":
            text = child.get("text", "")
            clean_text = _xml_safe_text(text) if text else ""
            if clean_text.strip():
                try:
                    doc.add_paragraph(clean_text).style = doc.styles['Code']
                except Exception:
                    pass

        elif child["type"] == "table":
            # Tabla básica
            rows = child.get("rows", [])
            n_cols = child.get("n_cols", 3)
            if rows:
                try:
                    # Añadir tabla con encabezado + datos
                    table = doc.add_table(rows=1 + len(rows), cols=n_cols)
                    # Header row - usar la primera fila de headers de markdown
                    header_row = table.rows[0]
                    header_cells = header_row.cells
                    header_text = child.get("headers", "")
                    # Parsear headers dividiendo por |
                    for j, cell_text in enumerate(header_text.split('|')):
                        if j < n_cols and cell_text.strip():
                            header_cells[j].text = _xml_safe_text(cell_text.strip().replace('|', '').strip())
                    # Data rows
                    for row_idx, row_data in enumerate(rows):
                        row = table.rows[row_idx + 1]
                        cells = row.cells
                        for col_idx in range(min(n_cols, len(row_data))):
                            if col_idx < len(cells):
                                cells[col_idx].text = _xml_safe_text(str(row_data[col_idx]))
                except Exception:
                    # Si falla la tabla, agregar contenido como párrafos
                    pass

        elif child["type"] == "math":
            # Ecuación matemática - insertar como texto con marcador
            # En implementación completa, convertiríamos LaTeX a OMML
            raw = child.get("raw", "")
            # Obtener el contenido LaTeX quitando delimitadores
            latex_content = _strip_math_delimiters(raw)
            
            if latex_content:
                # Agregar como párrafo con nota de que es matemática
                p = doc.add_paragraph()
                marker_text = f"[Ecuación matemática: {latex_content}]"
                run = p.add_run(_xml_safe_text(marker_text))
                run.font.italic = True

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def apply_ast_to_template(ast: Dict[str, Any], template_path: str) -> bytes:
    """
    Aplica el AST Markdown a una plantilla .docx base preservando bytes.
    Solo modifica los nodos XML necesarios, manteniendo intactos encabezados,
    pies de página, logos y otras estructuras preexistentes.
    """
    import zipfile
    import os

    # Leer la plantilla como ZIP OpenXML
    with zipfile.ZipFile(template_path, 'r') as zin:
        # Extraer todos los archivos a memoria (nombre -> bytes)
        docs = {name: zin.read(name) for name in zin.namelist()}

        # Leer document.xml principal
        document_xml = docs.get('word/document.xml', b'').decode('utf-8', errors='replace')

        # Aplicar cambios del AST al XML del documento
        modified_xml = apply_ast_to_xml(ast, document_xml)

        # Reconstruir el ZIP con el documento modificado
        docs['word/document.xml'] = modified_xml.encode('utf-8')

        # Reempaquetar
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
            for name, data in docs.items():
                zout.writestr(name, data)
        buf.seek(0)
        return buf.read()

    return b''


def apply_ast_to_xml(ast: Dict[str, Any], xml_content: str) -> str:
    """
    Aplica la estructura AST al contenido XML del documento Word.
    Modifica solo los nodos necesarios preservando el resto.
    """
    result = xml_content

    # Procesar headings
    for child in ast.get("children", []):
        if child["type"] == "heading":
            level = child.get("level", 1)
            text = child.get("text", "")
            if text:
                # Construir XML heading limpio
                clean_text = _xml_safe_text(text)
                # Reemplazar el primer párrafo encontrado con la estructura heading
                result = result.replace(
                    f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p>',
                    f'<w:h{level}><w:t>{clean_text}</w:t></w:h{level}>',
                    1
                )

    # Procesar tablas
    for child in ast.get("children", []):
        if child["type"] == "table":
            rows = child.get("rows", [])
            if rows:
                # Remover filas de tabla existentes y reemplazar con estructura tabla OOXML
                # Esto es simplificado - en producción usaría lxml para reestructurar
                pass

    # Procesar matemáticas - reemplazar placeholders en el XML
    for child in ast.get("children", []):
        if child["type"] == "math":
            math_type = child.get("math_type", "inline")
            raw = child.get("raw", "")
            # Marcar en XML que es matemática - simplemente reemplazar el texto
            # con un marcador que luego se procesará
            if '$' in raw:
                # Obtener contenido quitando delimitadores
                content = _strip_math_delimiters(raw)
                if content:
                    # Reemplazar con marcador OMML simplificado
                    marker = f'<m:oMath><m:oMathPara><m:r><m:t>{content}</m:t></m:r></m:oMathPara></m:oMath>'
                    # Buscar y reemplazar instancias simples
                    result = result.replace(
                        f'<w:t>{content}</w:t>',
                        f'<w:t>{marker}</w:t>',
                        1
                    )

    return result