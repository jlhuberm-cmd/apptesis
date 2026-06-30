"""Manejo global de excepciones → respuestas HTTP.

Traduce las excepciones del dominio en respuestas adecuadas para una app HTML:
mensaje flash + redirección a la página correspondiente. En modo DEBUG las
excepciones inesperadas se propagan; en producción se muestra un mensaje genérico.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER

from api.templating import render, set_flash
from config.settings import get_settings
from domain.exceptions.auth_exceptions import (
    AccountLockedError,
    AuthError,
    DomainError,
)

logger = logging.getLogger(__name__)


class NotAuthenticated(Exception):
    """El usuario no tiene una sesión válida en una ruta protegida."""


class NotAuthorized(Exception):
    """El usuario está autenticado pero no tiene el rol requerido."""


def _redirect(target: str) -> RedirectResponse:
    return RedirectResponse(url=target, status_code=HTTP_303_SEE_OTHER)


def register_error_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de excepciones en la app."""

    @app.exception_handler(NotAuthenticated)
    async def _handle_not_authenticated(request: Request, exc: NotAuthenticated) -> Response:
        set_flash(request, "Debes iniciar sesión para continuar.", "warning")
        return _redirect("/login")

    @app.exception_handler(NotAuthorized)
    async def _handle_not_authorized(request: Request, exc: NotAuthorized) -> Response:
        set_flash(request, "No tienes permisos para acceder a esta sección.", "error")
        return _redirect("/dashboard")

    @app.exception_handler(DomainError)
    async def _handle_domain_error(request: Request, exc: DomainError) -> Response:
        # Red de seguridad: las rutas suelen capturar estos errores localmente.
        logger.info("DomainError no capturado en ruta: %s", exc)
        set_flash(request, str(exc), "error")
        if isinstance(exc, AccountLockedError):
            return _redirect("/unlock-account")
        if isinstance(exc, AuthError):
            return _redirect("/login")
        return _redirect("/dashboard")

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> Response:
        logger.exception("Excepción no controlada en %s", request.url.path)
        if get_settings().DEBUG:
            raise exc
        return render(request, "components/alert.html", flashes=[
            {"category": "error", "message": "Ocurrió un error inesperado. Intenta más tarde."}
        ])
