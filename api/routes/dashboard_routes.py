"""Rutas del dashboard principal con gráficos (datos reales, escala 1–4).

Lee los resultados reales desde SupabaseDashboardService (vista
v_dashboard_resultados) y muestra tarjetas, gráficos y la tabla de estadísticas.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER

from api.middleware.auth_middleware import require_login
from api.templating import render
from config.dependencies import get_dashboard_service
from infrastructure.adapters.analysis.supabase_dashboard_service import (
    SupabaseDashboardService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


@router.get("/")
def index() -> Response:
    """Raíz: redirige al dashboard."""
    return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)


@router.get("/dashboard")
def dashboard(
    request: Request,
    gender: str = "",
    age_range: str = "",
    competency_code: str = "",
    identity: dict = Depends(require_login),
    service: SupabaseDashboardService = Depends(get_dashboard_service),
) -> Response:
    """Página principal del dashboard con datos reales (requiere sesión)."""
    ident = {
        "current_user_id": identity["id"],
        "current_user_name": identity["name"],
        "current_user_role": identity["role"],
    }
    context = service.build_context(
        gender or None, age_range or None, competency_code or None
    )
    if context is None:
        return render(request, "dashboard/index.html", has_data=False,
                      reason="Aún no hay encuestas cargadas.", **ident)
    return render(request, "dashboard/index.html", has_data=True, **ident, **context)
