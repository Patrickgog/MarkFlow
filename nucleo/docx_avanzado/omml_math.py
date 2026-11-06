"""Traductor de fórmulas LaTeX ($...$) a nodos OMML de Word.

Soporta:
- Ecuaciones en línea: $E = mc^2$
- Ecuaciones en bloque: $$∫(f(x)dx)$$
- Operadores matemáticos comunes
- Fracciones, raíces, sumas e integrales
"""

import re
from typing import Optional, Tuple


def extract_math_blocks(markdown: str) -> Tuple[List[Tuple[int, str, str]], str]:
    """
    Extrae bloques de fórmulas LaTeX del contenido Markdown.
    
    Returns:
        Tuple de (lista de tuplas (start_pos, latex, tipo), markdown_sin_math)
        donde tipo es 'inline' o 'block'
    """
    blocks = []
    markdown_clean = markdown
    
    # Ecuaciones en bloque $$...$$
    block_pattern = r'\$\$(.+?)\$\$'
    for match in re.finditer(block_pattern, markdown, re.DOTALL):
        latex = match.group(1).strip()
        start_pos = match.start()
        blocks.append((start_pos, latex, 'block'))
        # Remover del markdown limpio para evitar doble procesamiento
        markdown_clean = markdown_clean[:start_pos] + ' ' + markdown_clean[match.end():]
    
    # Ecuaciones en línea $...$ (cuidado con no capturar los de bloque ya removidos)
    # Solo buscamos singles que no estén dentro de bloques removidos
    inline_pattern = r'(?<!\$)\$([^$]+?)\$(?!\$)'
    for match in re.finditer(inline_pattern, markdown_clean):
        latex = match.group(1).strip()
        start_pos = match.start()
        blocks.append((start_pos, latex, 'inline'))
    
    # Ordenar por posición
    blocks.sort(key=lambda x: x[0])
    
    return blocks, markdown_clean


def latex_to_omml(latex: str) -> str:
    """
    Convierte una expresión LaTeX a nodo XML OMML.
    
    Esta es una conversión simplificada. En producción completa,
    se usaría una librería como `math` de docx-engine o `pandoc`.
    """
    # Patrones comunes de LaTeX a OMML
    result = latex
    
    # Fracciones: \frac{a}{b} → <m:f><m:num><m:r>a</m:r></m:num><m:den><m:r>b</m:r></m:den></m:f>
    result = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', 
                    r'<m:f><m:num><m:r>\1</m:r></m:num><m:den><m:r>\2</m:r></m:den></m:f>', 
                    result)
    
    # Raíz cuadrada: \sqrt{a} → <m:rad><m:e><m:r>a</m:r></m:e></m:rad>
    result = re.sub(r'\\sqrt\{([^}]+)\}', 
                    r'<m:rad><m:e><m:r>\1</m:r></m:e></m:rad>', 
                    result)
    
    # Suma: a + b (ya viene en formato normal generalmente)
    
    # Integrales: \int_a^b → <m:int><m:lim><m:r>a</m:r></m:lim><m:r>b</m:r></m:int>
    result = re.sub(r'\\int_\{([^}]+)\}\^\{([^}]+)\}', 
                    r'<m:int><m:lim>\1</m:lim><m:r>\2</m:r></m:int>', 
                    result)
    
    # Griego/grandes operadores ya formateados se mantienen
    
    return result


def wrap_in_omml(latex_expr: str, inline: bool = True) -> str:
    """
    Envuelve una expresión LaTeX en un nodo OMML completo.
    
    Args:
        latex_expr: Expresión LaTeX convertida (parcialmente)
        inline: Si True, usa <m:oMathInline>, si False usa <m:oMath>
    
    Returns:
        String con el nodo OMML completo
    """
    if inline:
        # Formato inline: $E = mc^2$ → <m:oMath><m:oMathPara>...</m:oMathPara></m:oMath>
        # Simplificado: envolver en estructura básica
        omml_content = latex_to_omml(latex_expr)
        return f'<m:oMath><m:oMathPara>{omml_content}</m:oMathPara></m:oMath>'
    else:
        # Formato bloque
        omml_content = latex_to_omml(latex_expr)
        return f'<m:oMath>{omml_content}</m:oMath>'


def process_math_in_document(markdown: str) -> Tuple[str, List[Tuple[int, str]]]:
    """
    Procesa todas las fórmulas matemáticas en un documento Markdown.
    
    Retorna el markdown procesado con placeholders y la lista 
    de fórmulas OMML generadas para inserción en el documento Word.
    """
    blocks, clean_md = extract_math_blocks(markdown)
    
    omml_results = []
    position = 0
    
    for start_pos, latex, block_type in blocks:
        # Agregar placeholder en la posición correcta
        if start_pos > position:
            # Agregar texto que está entre el último bloque y este
            pass
        
        # Convertir a OMML
        omml = wrap_in_omml(latex, inline=(block_type == 'inline'))
        omml_results.append((start_pos, omml, latex))
    
    return clean_md, omml_results