"""Ruta de healthcheck (/health).

Devuelve el estado del servicio y un chequeo best-effort de la conexión a Supabase.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter
from starlette.responses import JSONResponse

from config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> JSONResponse:
    """Healthcheck: estado del servicio, versión y conexión a la base de datos."""
    settings = get_settings()
    database = "connected"
    try:
        # Importación diferida para no acoplar el healthcheck al arranque.
        from config.dependencies import get_client

        get_client()
    except Exception:  # pragma: no cover - depende del entorno
        logger.warning("Healthcheck: no se pudo verificar la conexión a Supabase.")
        database = "disconnected"

    return JSONResponse(
        {
            "status": "ok",
            "version": settings.APP_VERSION,
            "database": database,
        }
    )
