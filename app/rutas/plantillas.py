"""Router API para la gestión de Plantillas y Placeholders Dinámicos en MarkFlow Office.

Rutas:
- POST /api/plantillas/analizar: Detecta candidatos a placeholders en un Markdown.
- POST /api/plantillas/crear-paquete: Genera plantilla .md, datos .xlsx y .json.
- POST /api/plantillas/leer-datos: Parsea archivos Excel (.xlsx) o JSON de datos.
- POST /api/plantillas/extraer-placeholders: Lista los placeholders presentes en un Markdown.
- POST /api/plantillas/validar: Valida datos de un proyecto contra la plantilla.
- POST /api/plantillas/generar-documentos: Fusión y compilación a HTML/DOCX/PDF/MD.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.servicios import sesiones
from motor.a_docx import a_docx
from motor.a_html import a_html
from motor.a_pdf import a_pdf
from motor.ingesta import leer_ingesta
from motor.plantillas import (
    CandidatoDeteccion,
    PlaceholderDef,
    aplicar_placeholders_a_markdown,
    detectar_candidatos,
    extraer_placeholders_de_markdown,
    fusionar_plantilla_con_datos,
    generar_excel_plantilla,
    generar_json_plantilla,
    leer_excel_plantilla,
    leer_json_plantilla,
    normalizar_nombre_placeholder,
    slug_archivo,
    validar_proyecto,
)

router = APIRouter(prefix="/api/plantillas", tags=["plantillas"])


def _sobre(datos=None, ok: bool = True, errores: list[dict] | None = None) -> dict:
    return {"ok": ok, "datos": datos, "errores": errores or []}


def _fallo(codigo: str, detalle: str, estado: int = 400) -> HTTPException:
    return HTTPException(status_code=estado, detail={"codigo": codigo, "detalle": detalle})


@router.post("/analizar")
async def analizar_candidatos(request: Request) -> dict:
    """Analiza un texto Markdown y extrae candidatos a placeholders clasificados por confianza."""
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "Se esperaba un objeto JSON con 'markdown'.")

    md_texto = str(cuerpo.get("markdown", "")).strip()
    if not md_texto:
        raise _fallo("TEXTO_VACIO", "El contenido Markdown proporcionado está vacío.")

    candidatos = detectar_candidatos(md_texto)
    datos_candidatos = [
        {
            "texto_encontrado": c.texto_encontrado,
            "nombre_sugerido": c.nombre_sugerido,
            "tipo_sugerido": c.tipo_sugerido,
            "unidad_sugerida": c.unidad_sugerida,
            "confianza": c.confianza,
            "ocurrencias": c.ocurrencias,
            "seleccionado": c.seleccionado,
            "contexto": c.contexto,
        }
        for c in candidatos
    ]

    return _sobre(datos={"candidatos": datos_candidatos, "total": len(datos_candidatos)})


@router.post("/crear-paquete")
async def crear_paquete(request: Request) -> dict:
    """Genera los 3 archivos oficiales de la plantilla:

    - plantilla_<proyecto>.md
    - plantilla_<proyecto>_datos.xlsx
    - plantilla_<proyecto>_datos.json
    """
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "Se esperaba un objeto JSON.")

    nombre_proy_raw = str(cuerpo.get("nombre_proyecto", "proyecto")).strip()
    md_texto = str(cuerpo.get("markdown", "")).strip()
    candidatos_raw = cuerpo.get("candidatos", [])

    if not md_texto:
        raise _fallo("TEXTO_VACIO", "El documento Markdown está vacío.")

    slug_proy = slug_archivo(nombre_proy_raw)
    nombre_md = f"plantilla_{slug_proy}.md"
    nombre_xlsx = f"plantilla_{slug_proy}_datos.xlsx"
    nombre_json = f"plantilla_{slug_proy}_datos.json"

    # Preparar reemplazos y definiciones
    reemplazos: List[tuple[str, str]] = []
    placeholders_def: List[PlaceholderDef] = []
    valores_proyecto_1: Dict[str, Any] = {}

    for c in candidatos_raw:
        if not c.get("seleccionado", True):
            continue
        texto_orig = str(c.get("texto_encontrado", "")).strip()
        nombre_ph = normalizar_nombre_placeholder(str(c.get("nombre_sugerido", "")))
        tipo = str(c.get("tipo_sugerido", "texto"))
        unidad = c.get("unidad_sugerida")

        if not texto_orig or not nombre_ph:
            continue

        reemplazos.append((texto_orig, nombre_ph))
        placeholders_def.append(
            PlaceholderDef(
                nombre=nombre_ph,
                etiqueta=nombre_ph.replace("_", " ").capitalize(),
                tipo=tipo,
                unidad=unidad,
                grupo="Datos generales",
                valor_original=texto_orig
            )
        )
        valores_proyecto_1[nombre_ph] = texto_orig

    # Generar Markdown con placeholders automáticos si aún hay texto sin convertir
    md_plantilla = aplicar_placeholders_a_markdown(md_texto, reemplazos)

    # 1. Extraer TODOS los placeholders presentes en el Markdown final
    phs_totales = extraer_placeholders_de_markdown(md_plantilla)

    # Diccionario de definiciones preexistentes
    mapa_defs = {p.nombre: p for p in placeholders_def}
    valores_manuales_in = cuerpo.get("valores_manuales", {})

    placeholders_finales: List[PlaceholderDef] = []
    valores_finales: Dict[str, Any] = {}

    for ph in phs_totales:
        ph_norm = normalizar_nombre_placeholder(ph)
        if ph_norm in mapa_defs:
            placeholders_finales.append(mapa_defs[ph_norm])
            valores_finales[ph_norm] = valores_proyecto_1.get(ph_norm, "")
        else:
            # Placeholder creado manualmente por el usuario
            val_orig = str(valores_manuales_in.get(ph_norm, "")).strip()
            def_manual = PlaceholderDef(
                nombre=ph_norm,
                etiqueta=ph_norm.replace("_", " ").capitalize(),
                tipo="texto",
                unidad=None,
                grupo="Personalizados",
                valor_original=val_orig
            )
            placeholders_finales.append(def_manual)
            valores_finales[ph_norm] = val_orig

    # Si no se detectaron en md_plantilla pero había candidatos seleccionados
    for p in placeholders_def:
        if p.nombre not in [pf.nombre for pf in placeholders_finales]:
            placeholders_finales.append(p)
            valores_finales[p.nombre] = valores_proyecto_1.get(p.nombre, "")

    # Estructurar proyectos
    proyectos = {
        f"Proyecto 1 ({nombre_proy_raw or 'Base'})": valores_finales
    }

    # Generar Excel y JSON con la lista exhaustiva
    excel_bytes = generar_excel_plantilla(placeholders_finales, proyectos)
    json_str = generar_json_plantilla(slug_proy, placeholders_finales, proyectos)

    # Generar paquete ZIP comprimido
    import io
    import zipfile

    buffer_zip = io.BytesIO()
    with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(nombre_md, md_plantilla.encode("utf-8"))
        zf.writestr(nombre_xlsx, excel_bytes)
        zf.writestr(nombre_json, json_str.encode("utf-8"))
    zip_bytes = buffer_zip.getvalue()
    nombre_zip = f"paquete_{slug_proy}.zip"

    # Guardar en sesión efímera
    sesion = sesiones.crear_sesion()
    sesiones.guardar(sesion, nombre_md, md_plantilla.encode("utf-8"))
    sesiones.guardar(sesion, nombre_xlsx, excel_bytes)
    sesiones.guardar(sesion, nombre_json, json_str.encode("utf-8"))
    sesiones.guardar(sesion, nombre_zip, zip_bytes)

    return _sobre(
        datos={
            "sesion": sesion,
            "plantilla_md": {
                "nombre": nombre_md,
                "url": f"/api/descargar/{sesion}/{nombre_md}",
                "contenido": md_plantilla,
                "tamano": f"{max(1, len(md_plantilla.encode('utf-8')) // 1024)} KB",
            },
            "datos_xlsx": {
                "nombre": nombre_xlsx,
                "url": f"/api/descargar/{sesion}/{nombre_xlsx}",
                "tamano": f"{max(1, len(excel_bytes) // 1024)} KB",
            },
            "datos_json": {
                "nombre": nombre_json,
                "url": f"/api/descargar/{sesion}/{nombre_json}",
                "contenido": json_str,
                "tamano": f"{max(1, len(json_str.encode('utf-8')) // 1024)} KB",
            },
            "paquete_zip": {
                "nombre": nombre_zip,
                "url": f"/api/descargar/{sesion}/{nombre_zip}",
                "tamano": f"{max(1, len(zip_bytes) // 1024)} KB",
            },
            "total_placeholders": len(placeholders_finales),
        }
    )


@router.post("/leer-datos")
async def leer_datos_archivo(archivo: UploadFile = File(...)) -> dict:
    """Parsea un archivo .xlsx o .json y devuelve los datos estructurados por proyecto."""
    nombre = archivo.filename or "datos.xlsx"
    contenido = await archivo.read()

    if nombre.lower().endswith(".xlsx"):
        try:
            placeholders, proyectos = leer_excel_plantilla(contenido)
        except Exception as exc:
            raise _fallo("EXCEL_INVALIDO", f"Error al procesar el archivo Excel: {exc}")
    elif nombre.lower().endswith(".json"):
        try:
            texto_json = contenido.decode("utf-8")
            phs_obj, proyectos = leer_json_plantilla(texto_json)
            placeholders = [p.nombre for p in phs_obj]
        except Exception as exc:
            raise _fallo("JSON_INVALIDO", f"Error al procesar el archivo JSON: {exc}")
    else:
        raise _fallo("FORMATO_NO_SOPORTADO", "Solo se admiten archivos .xlsx o .json.", 415)

    return _sobre(
        datos={
            "archivo": nombre,
            "placeholders": placeholders,
            "proyectos": proyectos,
            "nombres_proyectos": list(proyectos.keys()),
            "total_proyectos": len(proyectos),
            "total_placeholders": len(placeholders),
        }
    )


@router.post("/extraer-placeholders")
async def extraer_placeholders(request: Request) -> dict:
    """Extrae los nombres de placeholders {{...}} presentes en el Markdown provisto."""
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "Se esperaba un objeto JSON.")

    md = str(cuerpo.get("markdown", "")).strip()
    phs = extraer_placeholders_de_markdown(md)
    return _sobre(datos={"placeholders": phs, "total": len(phs)})


@router.post("/validar")
async def validar_datos_proyecto(request: Request) -> dict:
    """Valida un proyecto contra los placeholders de una plantilla."""
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "Se esperaba un objeto JSON.")

    placeholders = cuerpo.get("placeholders", [])
    datos_proy = cuerpo.get("datos_proyecto", {})
    tipos = cuerpo.get("tipos", {})

    res = validar_proyecto(placeholders, datos_proy, tipos)
    return _sobre(
        datos={
            "completos": res.completos,
            "vacios": res.vacios,
            "tipo_incorrecto": res.tipo_incorrecto,
            "sobrantes": res.sobrantes,
            "desconocidos": res.desconocidos,
            "resumen": res.resumen_texto,
            "conteo": {
                "completos": len(res.completos),
                "vacios": len(res.vacios),
                "tipo_incorrecto": len(res.tipo_incorrecto),
                "sobrantes": len(res.sobrantes),
            }
        }
    )


@router.post("/generar-documentos")
async def generar_documentos(request: Request) -> dict:
    """Genera documentos finales en HTML, Word, PDF y Markdown aplicando datos por proyecto."""
    try:
        cuerpo = await request.json()
    except Exception:
        raise _fallo("JSON_INVALIDO", "Se esperaba un objeto JSON.")

    plantilla_md = str(cuerpo.get("plantilla_markdown", "")).strip()
    if not plantilla_md:
        raise _fallo("PLANTILLA_VACIA", "La plantilla Markdown está vacía.")

    todos_proyectos = cuerpo.get("proyectos", {})
    seleccionados = cuerpo.get("proyectos_seleccionados", [])
    formatos = cuerpo.get("formatos", ["html"])
    opciones = cuerpo.get("opciones", {})

    # Si no se especificaron proyectos seleccionados, usar todos los disponibles
    if not seleccionados and todos_proyectos:
        seleccionados = list(todos_proyectos.keys())

    if not seleccionados:
        raise _fallo("SIN_PROYECTOS", "No se especificó ningún proyecto para generar.")

    sesion = sesiones.crear_sesion()
    carpeta_sesion = sesiones._carpeta(sesion)
    documentos_generados = []
    avisos_totales = []

    tema_html = opciones.get("tema_html", "defecto")
    tema_word = opciones.get("tema_word", "consultor_moderno")
    paleta_word = opciones.get("paleta", "editorial")
    tema_pdf = opciones.get("tema_pdf", "informe_tecnico")

    for nom_proy in seleccionados:
        datos_proy = todos_proyectos.get(nom_proy, {})
        slug_p = slug_archivo(nom_proy)

        # 1. Markdown
        if "markdown" in formatos:
            md_fusionado = fusionar_plantilla_con_datos(plantilla_md, datos_proy, formato_salida="markdown")
            nombre_arch = f"documento_{slug_p}.md"
            datos_bytes = md_fusionado.encode("utf-8")
            sesiones.guardar(sesion, nombre_arch, datos_bytes)
            documentos_generados.append({
                "proyecto": nom_proy,
                "formato": "markdown",
                "archivo": nombre_arch,
                "url": f"/api/descargar/{sesion}/{nombre_arch}",
                "tamano": f"{max(1, len(datos_bytes) // 1024)} KB"
            })

        # 2. HTML
        if "html" in formatos:
            md_fusionado = fusionar_plantilla_con_datos(plantilla_md, datos_proy, formato_salida="html")
            nombre_arch = f"documento_{slug_p}.html"
            html_res, _, avisos_h = a_html(
                md_fusionado,
                titulo=f"Documento - {nom_proy}",
                tema_html=tema_html
            )
            datos_bytes = html_res.encode("utf-8")
            sesiones.guardar(sesion, nombre_arch, datos_bytes)
            avisos_totales.extend(avisos_h)
            documentos_generados.append({
                "proyecto": nom_proy,
                "formato": "html",
                "archivo": nombre_arch,
                "url": f"/api/descargar/{sesion}/{nombre_arch}",
                "tamano": f"{max(1, len(datos_bytes) // 1024)} KB"
            })

        # 3. Word (DOCX)
        if "word" in formatos:
            md_fusionado = fusionar_plantilla_con_datos(plantilla_md, datos_proy, formato_salida="word")
            nombre_arch = f"documento_{slug_p}.docx"
            ruta_docx = carpeta_sesion / nombre_arch
            try:
                ruta_res, _, avisos_w = a_docx(
                    md_fusionado,
                    destino=ruta_docx,
                    tema_word=tema_word,
                    titulo=f"Documento - {nom_proy}"
                )
                avisos_totales.extend(avisos_w)
                tam = f"{max(1, ruta_docx.stat().st_size // 1024)} KB" if ruta_docx.exists() else "—"
                documentos_generados.append({
                    "proyecto": nom_proy,
                    "formato": "word",
                    "archivo": nombre_arch,
                    "url": f"/api/descargar/{sesion}/{nombre_arch}",
                    "tamano": tam
                })
            except Exception as exc:
                avisos_totales.append(f"Error generando Word para {nom_proy}: {exc}")

        # 4. PDF
        if "pdf" in formatos:
            md_fusionado = fusionar_plantilla_con_datos(plantilla_md, datos_proy, formato_salida="pdf")
            nombre_arch = f"documento_{slug_p}.pdf"
            ruta_pdf = carpeta_sesion / nombre_arch
            try:
                ruta_res, _, avisos_p = a_pdf(
                    md_fusionado,
                    destino=ruta_pdf,
                    tema_pdf=tema_pdf,
                    titulo=f"Documento - {nom_proy}"
                )
                avisos_totales.extend(avisos_p)
                tam = f"{max(1, ruta_pdf.stat().st_size // 1024)} KB" if ruta_pdf.exists() else "—"
                documentos_generados.append({
                    "proyecto": nom_proy,
                    "formato": "pdf",
                    "archivo": nombre_arch,
                    "url": f"/api/descargar/{sesion}/{nombre_arch}",
                    "tamano": tam
                })
            except Exception as exc:
                avisos_totales.append(f"Error generando PDF para {nom_proy}: {exc}")

        # 5. JSON estructurado del proyecto
        if "json" in formatos:
            phs_proy = [
                PlaceholderDef(nombre=k, etiqueta=k.replace("_", " ").capitalize(), valor_original=str(v))
                for k, v in datos_proy.items()
            ]
            json_proy_str = generar_json_plantilla(slug_p, phs_proy, {nom_proy: datos_proy})
            nombre_arch = f"documento_{slug_p}_datos.json"
            datos_bytes = json_proy_str.encode("utf-8")
            sesiones.guardar(sesion, nombre_arch, datos_bytes)
            documentos_generados.append({
                "proyecto": nom_proy,
                "formato": "json",
                "archivo": nombre_arch,
                "url": f"/api/descargar/{sesion}/{nombre_arch}",
                "tamano": f"{max(1, len(datos_bytes) // 1024)} KB"
            })

        # 6. Excel (.xlsx) estructurado del proyecto
        if "xlsx" in formatos or "excel" in formatos:
            phs_proy = [
                PlaceholderDef(nombre=k, etiqueta=k.replace("_", " ").capitalize(), valor_original=str(v))
                for k, v in datos_proy.items()
            ]
            excel_proy_bytes = generar_excel_plantilla(phs_proy, {nom_proy: datos_proy})
            nombre_arch = f"documento_{slug_p}_datos.xlsx"
            sesiones.guardar(sesion, nombre_arch, excel_proy_bytes)
            documentos_generados.append({
                "proyecto": nom_proy,
                "formato": "xlsx",
                "archivo": nombre_arch,
                "url": f"/api/descargar/{sesion}/{nombre_arch}",
                "tamano": f"{max(1, len(excel_proy_bytes) // 1024)} KB"
            })

    return _sobre(
        datos={
            "sesion": sesion,
            "generados": documentos_generados,
            "total_generados": len(documentos_generados),
            "avisos": avisos_totales,
        }
    )
