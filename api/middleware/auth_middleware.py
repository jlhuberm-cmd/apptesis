"""Middleware de autenticación basado en sesión + permisos (RBAC).

La sesión guarda id, nombre, rol y la lista de permisos del usuario (resueltos al
iniciar sesión desde usuarios/usuario_rol/roles). Provee dependencias para exigir
sesión o un permiso concreto.
"""
from __future__ import annotations

from collections.abc import Callable

from fastapi import Request

from api.middleware.error_handler import NotAuthenticated, NotAuthorized

# Permisos usados por la app (deben coincidir con roles.permisos en la base).
PERM_VER_DASHBOARD = "ver_dashboard"
PERM_CARGAR_CSV = "cargar_csv"
PERM_GESTIONAR_USUARIOS = "gestionar_usuarios"


def current_identity(request: Request) -> dict | None:
    """Devuelve {id, name, role, permisos} de la sesión, o None si no hay sesión."""
    if not request.session.get("user_id"):
        return None
    return {
        "id": request.session.get("user_id"),
        "name": request.session.get("full_name"),
        "role": request.session.get("role"),
        "permisos": request.session.get("permisos", []),
    }


def require_login(request: Request) -> dict:
    """Dependencia: exige sesión válida. Redirige a /login si no la hay."""
    identity = current_identity(request)
    if identity is None:
        raise NotAuthenticated()
    return identity


def require_perm(permiso: str) -> Callable[[Request], dict]:
    """Crea una dependencia que exige un permiso concreto."""

    def _dependency(request: Request) -> dict:
        identity = require_login(request)
        if permiso not in identity.get("permisos", []):
            raise NotAuthorized()
        return identity

    return _dependency
