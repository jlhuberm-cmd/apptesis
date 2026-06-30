"""Rutas de autenticación: login y logout (Supabase Auth + perfiles/roles).

El login valida credenciales contra Supabase Auth y resuelve rol/permisos desde la
base (usuarios/usuario_rol/roles). La sesión guarda id, nombre, rol y permisos.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Form, Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER

from api.templating import render, set_flash
from config.dependencies import get_auth_service
from infrastructure.adapters.auth.supabase_auth_service import SupabaseAuthService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


def _redirect(target: str) -> RedirectResponse:
    return RedirectResponse(url=target, status_code=HTTP_303_SEE_OTHER)


@router.get("/login")
def login_form(request: Request) -> Response:
    return render(request, "auth/login.html")


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> Response:
    identity = auth.authenticate(email, password)
    if identity is None:
        set_flash(request, "Credenciales incorrectas o cuenta inactiva.", "error")
        return _redirect("/login")

    request.session["user_id"] = identity["id"]
    request.session["full_name"] = identity["name"]
    request.session["role"] = identity["role"]
    request.session["permisos"] = identity["permisos"]
    request.session["id_empresa"] = identity["id_empresa"]
    logger.info("Login OK (%s): %s", identity["role"], identity["email"])
    return _redirect("/dashboard")


@router.get("/logout")
def logout(request: Request) -> Response:
    request.session.clear()
    set_flash(request, "Sesión cerrada.", "info")
    return _redirect("/login")
