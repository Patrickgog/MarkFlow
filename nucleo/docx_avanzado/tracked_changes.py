"""Generador de Control de Cambios nativo de Word (w:ins y w:del).

Permite aplicar mejoras o reescrituras sobre documentos Markdown/Word
generando etiquetas <w:ins> y <w:del> para que al abrir el .docx en Microsoft
Word los cambios puedan aceptarse o rechazase con un clic.
"""

import re
from typing import Dict, List, Optional, Tuple


class TrackedChangesGenerator:
    """Genera etiquetas de control de cambios nativo de Word."""
    
    def __init__(self, author: str = "Usuario", date: Optional[str] = None):
        self.author = author
        from datetime import datetime
        self.date = date or datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    def add_insertion(self, text: str, location_tag: str = "end") -> str:
        """
        Envuelve texto en etiqueta de inserción w:ins.
        
        Args:
            text: El texto a marcar como inserción
            location_tag: Ubicación relativa ("inicio", "final")
            
        Returns:
            String con la etiqueta w:ins completa
        """
        return f'<w:ins w:author="{self.author}" w:date="{self.date}"><w:t>{text}</w:t></w:ins>'
    
    def add_deletion(self, text: str) -> str:
        """
        Envuelve texto en etiqueta de eliminación w:del.
        
        Args:
            text: El texto a marcar como eliminación
            
        Returns:
            String con la etiqueta w:del completa
        """
        return f'<w:del w:author="{self.author}" w:date="{self.date}"><w:t>{text}</w:t></w:del>'
    
    def modify_text(self, original: str, replacement: str, 
                    insert_mark: bool = True, delete_mark: bool = True) -> str:
        """
        Modifica texto aplicando control de cambios.
        
        Si insert_mark es True, el texto nuevo se marcará como inserción.
        Si delete_mark es True, el texto original removido se marcará como eliminación.
        
        Returns:
            String XML con etiquetas de cambios
        """
        result = ""
        
        if insert_mark and replacement:
            result += self.add_insertion(replacement)
        
        if delete_mark and original:
            result += self.add_deletion(original)
        
        return result
    
    def generate_diff_markup(self, original_text: str, revised_text: str) -> str:
        """
        Genera markup de diff entre texto original y revisado.
        
        Analiza diferencias y marca qué se añadió y qué se removió.
        """
        # Dividir en palabras/elementos para comparar
        orig_parts = self._split_text(original_text)
        rev_parts = self._split_text(revised_text)
        
        result_parts = []
        i = j = 0
        
        while i < len(orig_parts) or j < len(rev_parts):
            if i < len(orig_parts) and j < len(rev_parts) and orig_parts[i] == rev_parts[j]:
                # Igual - texto sin modificar
                result_parts.append(orig_parts[i])
                i += 1
                j += 1
            elif j < len(rev_parts) and (i >= len(orig_parts) or rev_parts[j] not in orig_parts[i:]):
                # Nueva inserción
                result_parts.append(self.add_insertion(rev_parts[j]))
                j += 1
            elif i < len(orig_parts) and (j >= len(rev_parts) or orig_parts[i] not in rev_parts[j:]):
                # Eliminación existente
                result_parts.append(self.add_deletion(orig_parts[i]))
                i += 1
            else:
                # Caso por defecto - ambos cambios
                result_parts.append(self.add_insertion(rev_parts[j]))
                result_parts.append(self.add_deletion(orig_parts[i]))
                i += 1
                j += 1
        
        return ' '.join(result_parts)
    
    def _split_text(self, text: str) -> List[str]:
        """Divide el texto en unidades significativas (palabras/tokens)."""
        # Simple split by words, preserving some structure
        # En implementación real usaría tokenización más sofisticada
        return re.findall(r'\S+|\s+', text) if text else []


def apply_tracked_changes_to_xml(xml_content: str, changes_spec: List[Dict]) -> str:
    """
    Aplica cambios de control a contenido XML de documento Word.
    
    Args:
        xml_content: Contenido XML actual del documento .docx
        changes_spec: Lista de diccionarios con spec de cambios:
            {
                "type": "insertion" | "deletion" | "modify",
                "original": "texto original a remover",
                "replacement": "texto nuevo a insertar",
                "position": "start_index" | "end"
            }
    
    Returns:
        XML modificado con etiquetas w:ins y w:del
    """
    result = xml_content
    
    for change in changes_spec:
        change_type = change.get("type", "modify")
        
        if change_type == "insertion":
            text = change.get("text", "")
            result = result.replace(
                f'<w:t>{text}</w:t>',
                f'<w:ins w:author="{change.get("author", "Usuario")}" '
                f'w:date="{change.get("date", "")}"><w:t>{text}</w:t></w:ins>'
            )
        elif change_type == "deletion":
            text = change.get("text", "")
            result = result.replace(
                f'<w:t>{text}</w:t>',
                f'<w:del w:author="{change.get("author", "Usuario")}" '
                f'w:date="{change.get("date", "")}"><w:t>{text}</w:t></w:del>'
            )
        elif change_type == "modify":
            original = change.get("original", "")
            replacement = change.get("replacement", "")
            # Reemplazar original por inserción + eliminación
            result = result.replace(
                f'<w:t>{original}</w:t>',
                f'{self.add_insertion(replacement)}{self.add_deletion(original)}'
            )
    
    return result