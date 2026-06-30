"""Entry point de la aplicación.

Construye la app FastAPI, monta rutas, templates y archivos estáticos, configura el
middleware de sesión y los manejadores de errores, y lanza Uvicorn.
"""
from __future__ import annotations

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from api.middleware.error_handler import register_error_handlers
from api.routes import (
    admin_routes,
    analysis_routes,
    auth_routes,
    dashboard_routes,
    health_routes,
)
from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
_STATIC_DIR = BASE_DIR / "api" / "static"


def create_app() -> FastAPI:
    """Construye y configura la instancia de FastAPI (application factory)."""
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Plataforma de evaluación de competencias digitales DigComp 2.2.",
        debug=settings.DEBUG,
    )

    # Sesión basada en cookie firmada.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        max_age=settings.SESSION_MAX_AGE,
        same_site="lax",
    )

    # Archivos estáticos.
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # Rutas.
    app.include_router(health_routes.router)
    app.include_router(auth_routes.router)
    app.include_router(dashboard_routes.router)
    app.include_router(analysis_routes.router)
    app.include_router(admin_routes.router)

    # Manejo global de errores.
    register_error_handlers(app)

    @app.on_event("startup")
    def _verify_connection() -> None:
        """Verifica (best-effort) la conexión a Supabase al arrancar."""
        try:
            from config.dependencies import get_client

            get_client()
            logger.info("Conexión a Supabase verificada.")
        except Exception:
            logger.warning(
                "No se pudo verificar la conexión a Supabase en el arranque. "
                "Revisa las variables de entorno SUPABASE_*."
            )

    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
