"""Fábrica de la aplicación MarkFlow Office.

Ensambla: router de API clásica de MarkFlow (motor de conversión), routers de
la suite (documentos + office), estáticos, plantillas Jinja2 y el ciclo de vida
(purga de sesiones al arrancar y al apagar). Puntos de entrada:

    uvicorn app.principal:app --port 8320   → shell Office (/) + clásico (/clasico)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.rutas.api import router as router_api
from app.rutas.documentos import router as router_documentos
from app.rutas.office import router as router_office
from app.rutas.plantillas import router as router_plantillas
from app.servicios import sesiones
from app.version import APP_NOMBRE, APP_VERSION

RAIZ = Path(__file__).resolve().parents[1]
DIR_STATIC = RAIZ / "static"
DIR_TEMPLATES = RAIZ / "templates"
PUERTO = 8320


@asynccontextmanager
async def _ciclo(app: FastAPI):
    """Purga de sesiones al arrancar y al apagar (higiene R3)."""
    sesiones.limpiar_todo()
    yield
    sesiones.limpiar_todo()


def crear_app() -> FastAPI:
    """Crea y ensambla la aplicación completa de MarkFlow Office."""
    app = FastAPI(title=APP_NOMBRE, version=APP_VERSION, lifespan=_ciclo)

    # Capa 2 · API (motor MarkFlow + suite)
    app.include_router(router_api)
    app.include_router(router_documentos)
    app.include_router(router_office)
    app.include_router(router_plantillas)

    app.mount("/static", StaticFiles(directory=DIR_STATIC), name="static")
    app.mount("/assets", StaticFiles(directory=RAIZ / "motor" / "assets"), name="assets")

    plantillas = Jinja2Templates(directory=str(DIR_TEMPLATES))

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def inicio(request: Request) -> HTMLResponse:
        """Shell Office: riel de apps + lienzo + panel de IA (estilo GenOffice)."""
        return plantillas.TemplateResponse(
            request=request,
            name="office.html",
            context={"nombre": APP_NOMBRE, "version": APP_VERSION},
        )

    @app.get("/clasico", response_class=HTMLResponse, include_in_schema=False)
    async def clasico(request: Request) -> HTMLResponse:
        """UI clásica de MarkFlow (conversor completo), embebida en la app MarkFlow."""
        return plantillas.TemplateResponse(
            request=request,
            name="index.html",
            context={"nombre": APP_NOMBRE, "version": APP_VERSION},
        )

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Sirve el favicon oficial para todas las pestañas de navegador."""
        from fastapi.responses import FileResponse
        return FileResponse(DIR_STATIC / "img" / "favicon.svg", media_type="image/svg+xml")

    return app


app = crear_app()
