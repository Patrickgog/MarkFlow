# Guía Técnica de Correcciones y Mejoras para MarkFlow Office

Este documento recopila las pautas y soluciones técnicas discutidas para resolver los problemas de temas, formato de tablas en Word (.docx) y visualización de imágenes en PDF y DOCX en la aplicación **MarkFlow Office**

---

## 1. Inclusión de Todos los Temas (HTML y Word) en la Interfaz

Para asegurar que todos los temas de HTML y Word estén disponibles en el selector de la aplicación (asemejándose a las opciones avanzadas de formato editorial), asegúrate de actualizar el componente de selección (`Select` de Mantine) y el backend asociado:

### Ejemplo en Frontend (React / Mantine UI)
```jsx
<Select
  label="Sistema de Temas HTML / Word"
  placeholder="Selecciona un tema profesional"
  data={[
    { value: 'default', label: 'Tema Estándar Profesional' },
    { value: 'corporate', label: 'Corporativo / Ejecutivo' },
    { value: 'academic', label: 'Académico / Técnico (APA/IEEE)' },
    { value: 'modern', label: 'Moderno / Minimalista (Clean)' },
    { value: 'soft', label: 'Paleta Suave para Cuadros' }
  ]}
  defaultValue="default"
/>
```

---

## 2. Corrección de Tablas en Word (.docx): Centradas y Ancho Dinámico

Por defecto, `python-docx` fuerza a que las tablas ocupen el 100% del ancho de la hoja y estira las celdas de forma rígida. Para solucionar esto y lograr que las tablas se centren y se adapten al contenido, implementa la siguiente función en tu generador de Word:

```python
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def aplicar_estilo_tabla_profesional(table, col_widths=None):
    """
    Centra la tabla y ajusta el comportamiento para que no ocupe 
    forzosamente el 100% del ancho de la página si el contenido es menor.
    """
    # 1. Centrar la tabla en la hoja
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False  # Desactiva el estiramiento automático rígido

    # 2. Configurar propiedades de las filas para evitar saltos partidos
    for i, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        
        # Evitar que una fila se divida torpemente entre páginas
        cantSplit = OxmlElement('w:cantSplit')
        trPr.append(cantSplit)
        
        # Repetir cabecera si la tabla pasa de página
        if i == 0:
            tblHeader = OxmlElement('w:tblHeader')
            trPr.append(tblHeader)

        # 3. Ajustar anchos de celda basados en el contenido
        for j, cell in enumerate(row.cells):
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = OxmlElement('w:tcMar')
            for margin_type in ['top', 'bottom']:
                m = OxmlElement(f'w:{margin_type}')
                m.set(qn('w:w'), '120') # ~6pt de padding vertical
                m.set(qn('w:type'), 'dxa')
                tcMar.append(m)
            tcPr.append(tcMar)

            if col_widths and j < len(col_widths):
                cell.width = col_widths[j]
```

---

## 3. Visualización de Imágenes en PDF y DOCX

El problema de las imágenes rotas en DOCX y PDF se debe a rutas relativas no resueltas. 

### Solución para DOCX (`python-docx`)
Convierte las rutas relativas en **rutas absolutas** usando el directorio base del archivo de origen:

```python
import os
from docx.shared import Inches

def insertar_imagen_segura(doc, image_path, base_dir, width_inches=5.0):
    """
    Resuelve la ruta absoluta de la imagen a partir del directorio base del archivo .md
    y la inserta correctamente en el documento Word.
    """
    ruta_absoluta = os.path.normpath(os.path.join(base_dir, image_path))
    
    if os.path.exists(ruta_absoluta):
        try:
            doc.add_picture(ruta_absoluta, width=Inches(width_inches))
        except Exception as e:
            print(f"Error al incrustar imagen en Word: {e}")
    else:
        print(f"Advertencia: No se encontró la imagen en {ruta_absoluta}")
```

### Solución para PDF (Incrustación Base64)
Convierte las imágenes a formato Base64 para que el motor HTML->PDF las procese de forma totalmente autónoma:

```python
import base64
import pathlib

def convertir_imagen_a_base64(image_path, base_dir):
    ruta_absoluta = pathlib.Path(base_dir) / image_path
    if ruta_absoluta.exists():
        with open(ruta_absoluta, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode('utf-8')
            ext = ruta_absoluta.suffix.lower().replace('.', '')
            if ext == 'jpg': ext = 'jpeg'
            return f"data:image/{ext};base64,{encoded}"
    return ""
```

---

## 4. Inclusión de Todos los Temas (HTML y Word) en la Interfaz

Para asegurar que todos los temas de HTML y Word estén disponibles en el selector principal:

```jsx
<Select
  label="Sistema de Temas HTML / Word"
  placeholder="Selecciona un tema profesional"
  data={[
    { value: 'default', label: 'Tema Estándar Profesional' },
    { value: 'corporate', label: 'Corporativo / Ejecutivo' },
    { value: 'academic', label: 'Académico / Técnico (APA/IEEE)' },
    { value: 'modern', label: 'Moderno / Minimalista (Clean)' },
    { value: 'soft', label: 'Paleta Suave para Cuadros' }
  ]}
  defaultValue="default"
/>
```

---

## 5. Selector Visual de Colores de Títulos y Creador de Paletas Personalizadas

En el módulo de **Tema Personalizado**, se reemplazan los códigos de color en formato texto por **muestras visuales reales (swatches)** tanto para las salidas HTML como Word, permitiendo además que el usuario cree y guarde sus propios juegos de colores.

### A. Componente Select con Muestras Visuales de Color (Mantine)

```jsx
import { Select, Group, Box, Text } from '@mantine/core';

const colorPalettes = [
  { value: 'corporate-blue', label: 'Azul Ejecutivo', colors: ['#003366', '#4682B4'] },
  { value: 'emerald-tech', label: 'Esmeralda Académico', colors: ['#046A38', '#50C878'] },
  { value: 'slate-modern', label: 'Pizarra Minimalista', colors: ['#2F4F4F', '#708090'] },
  { value: 'burgundy-classic', label: 'Vino Tinto Editorial', colors: ['#6b1426', '#a3334d'] }
];

export function TitleColorSelector({ value, onChange }) {
  return (
    <Select
      label="Color de Títulos (Tema Personalizado)"
      placeholder="Elige un juego de colores"
      data={colorPalettes}
      value={value}
      onChange={onChange}
      renderOption={({ option }) => {
        const palette = colorPalettes.find(p => p.value === option.value);
        return (
          <Group justify="space-between" w="100%">
            <Text size="sm">{option.label}</Text>
            {palette && (
              <Group gap={4}>
                {palette.colors.map((color, idx) => (
                  <Box
                    key={idx}
                    w={16}
                    h={16}
                    bg={color}
                    style={{ 
                      borderRadius: '50%', 
                      border: '1px solid rgba(255,255,255,0.3)',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)' 
                    }}
                  />
                ))}
              </Group>
            )}
          </Group>
        );
      }}
    />
  );
}
```

### B. Creador de Juegos de Colores Personalizados para el Usuario

Este componente permite al usuario definir dinámicamente sus propias paletas de colores (aplicables de forma uniforme a las exportaciones HTML y Word):

```jsx
import { useState } from 'react';
import { ColorInput, Button, Stack, Title, TextInput, Group, Paper } from '@mantine/core';

export function CustomPaletteCreator({ onSavePalette }) {
  const [paletteName, setPaletteName] = useState('');
  const [primaryColor, setPrimaryColor] = useState('#1e3a8a'); // Títulos H1/H2
  const [secondaryColor, setSecondaryColor] = useState('#3b82f6'); // Subtítulos / Acentos

  const handleSave = () => {
    if (!paletteName.trim()) return;
    const newPalette = {
      value: `custom-${Date.now()}`,
      label: paletteName,
      colors: [primaryColor, secondaryColor]
    };
    onSavePalette(newPalette);
    setPaletteName('');
  };

  return (
    <Paper withBorder p="md" radius="md" bg="dark.7">
      <Stack spacing="xs">
        <Title order={5} c="white">Crear Juego de Colores Personalizado</Title>
        <TextInput
          label="Nombre de la paleta"
          placeholder="Ej. Mi Tema Institucional"
          value={paletteName}
          onChange={(e) => setPaletteName(e.currentTarget.value)}
        />
        <Group grow>
          <ColorInput 
            label="Color Primario (Títulos)" 
            value={primaryColor} 
            onChange={setPrimaryColor} 
          />
          <ColorInput 
            label="Color Secundario (Subtítulos)" 
            value={secondaryColor} 
            onChange={setSecondaryColor} 
          />
        </Group>
        <Button onClick={handleSave} variant="gradient" gradient={{ from: 'blue', to: 'cyan' }} mt="xs">
          Guardar y Aplicar Paleta
        </Button>
      </Stack>
    </Paper>
  );
}
