"""Cliente Supabase (singleton).

Crea y cachea un único cliente de Supabase usando la SERVICE_KEY (rol de servicio,
para operaciones del backend). Maneja errores de conexión/configuración.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from supabase import Client, create_client

from config.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_supabase_client() -> Client:
    """Devuelve el cliente Supabase singleton.

    Raises:
        RuntimeError: si faltan las credenciales o falla la creación del cliente.
    """
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "Faltan SUPABASE_URL o SUPABASE_SERVICE_KEY en la configuración."
        )
    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("Cliente Supabase inicializado.")
        return client
    except Exception as exc:  # pragma: no cover - depende del entorno
        logger.exception("No se pudo crear el cliente Supabase.")
        raise RuntimeError(f"Error al conectar con Supabase: {exc}") from exc
