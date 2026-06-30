"""Motor de plantillas y utilidades de mensajes flash.

Centraliza la instancia de Jinja2Templates y el manejo de mensajes flash en la
sesión, para que las rutas y el manejador de errores compartan el mismo render.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

_FLASH_KEY = "_flashes"


def set_flash(request: Request, message: str, category: str = "error") -> None:
    """Agrega un mensaje flash a la sesión (category: success|error|warning|info)."""
    flashes = request.session.get(_FLASH_KEY, [])
    flashes.append({"category": category, "message": message})
    request.session[_FLASH_KEY] = flashes


def pop_flashes(request: Request) -> list[dict[str, str]]:
    """Devuelve y limpia los mensajes flash pendientes de la sesión."""
    return request.session.pop(_FLASH_KEY, [])


def render(request: Request, template_name: str, **context: Any) -> HTMLResponse:
    """Renderiza una plantilla inyectando flashes y datos de sesión comunes."""
    base_context = {
        "request": request,
        "flashes": pop_flashes(request),
        "current_user_id": request.session.get("user_id"),
        "current_user_name": request.session.get("full_name"),
        "current_user_role": request.session.get("role"),
        "current_permisos": request.session.get("permisos", []),
    }
    base_context.update(context)
    return templates.TemplateResponse(template_name, base_context)
