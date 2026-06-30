"""Rutas de análisis y endpoint HTMX para filtros y gráficos dinámicos.

Leen los datos REALES (esquema Likert 0–3) desde SupabaseDashboardService. El
endpoint `/analysis/data` recalcula y devuelve el partial `dashboard_content` para
que HTMX lo intercambie, actualizando todo el tablero al aplicar filtros.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from api.middleware.auth_middleware import require_login
from api.templating import render
from config.dependencies import get_dashboard_service
from infrastructure.adapters.analysis.supabase_dashboard_service import (
    SupabaseDashboardService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])


@router.get("/analysis/data")
def analysis_data(
    request: Request,
    gender: str = "",
    age_range: str = "",
    competency_code: str = "",
    identity: dict = Depends(require_login),
    service: SupabaseDashboardService = Depends(get_dashboard_service),
) -> Response:
    """Endpoint HTMX: devuelve el contenido del dashboard según los filtros."""
    context = service.build_context(
        gender or None, age_range or None, competency_code or None
    )
    if context is None:
        return render(request, "dashboard/empty_state.html",
                      reason="No hay datos para los filtros seleccionados.")
    return render(request, "dashboard/partials/dashboard_content.html", **context)
