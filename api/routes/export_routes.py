"""Rutas de exportacion del dashboard a Excel y PDF.

Opcion adicional del tablero, disponible para TODOS los usuarios con sesion
valida (los mismos que pueden ver el dashboard). Genera un archivo descargable a
partir del MISMO contexto que alimenta el tablero en pantalla, respetando los
filtros activos (genero, rango de edad, competencia) e incrustando los graficos
que el usuario tiene renderizados en ese momento (capturados con Plotly.toImage).

Se usa POST para poder transportar las imagenes (PNG en base64) junto con los
filtros. No altera datos ni la logica existente: reutiliza
`SupabaseDashboardService.build_context` en modo solo lectura.
"""
from __future__ import annotations

import base64
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER

from api.middleware.auth_middleware import require_login
from api.templating import set_flash
from config.dependencies import get_dashboard_service
from infrastructure.adapters.analysis.supabase_dashboard_service import (
    SupabaseDashboardService,
)
from infrastructure.adapters.export import dashboard_exporter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["export"])

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_PDF_MIME = "application/pdf"


def _decode_data_url(data_url: str) -> bytes | None:
    """Decodifica un data URL 'data:image/png;base64,...' a bytes PNG."""
    if not data_url or "," not in data_url:
        return None
    try:
        return base64.b64decode(data_url.split(",", 1)[1])
    except Exception:
        logger.warning("No se pudo decodificar una imagen de grafico para exportar.")
        return None


def _collect_images(radar_img: str, bar_img: str, dist_img: str) -> dict[str, bytes]:
    """Construye {clave: png_bytes} omitiendo las imagenes ausentes/invalidas."""
    crudas = {"radar": radar_img, "bar": bar_img, "dist": dist_img}
    imagenes: dict[str, bytes] = {}
    for clave, data_url in crudas.items():
        png = _decode_data_url(data_url)
        if png:
            imagenes[clave] = png
    return imagenes


def _filename(extension: str) -> str:
    """Nombre de archivo con marca de tiempo."""
    sello = datetime.now().strftime("%Y%m%d_%H%M")
    return f"dashboard_digcomp_{sello}.{extension}"


@router.post("/dashboard/export/excel")
def export_excel(
    request: Request,
    gender: str = Form(""),
    age_range: str = Form(""),
    competency_code: str = Form(""),
    radar_img: str = Form(""),
    bar_img: str = Form(""),
    dist_img: str = Form(""),
    identity: dict = Depends(require_login),
    service: SupabaseDashboardService = Depends(get_dashboard_service),
) -> Response:
    """Descarga el dashboard actual (filtros + graficos) como archivo Excel."""
    context = service.build_context(
        gender or None, age_range or None, competency_code or None
    )
    if context is None:
        set_flash(request, "No hay datos para exportar con los filtros seleccionados.",
                  "warning")
        return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)

    imagenes = _collect_images(radar_img, bar_img, dist_img)
    contenido = dashboard_exporter.to_excel(context, imagenes)
    return Response(
        content=contenido,
        media_type=_XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{_filename("xlsx")}"'},
    )


@router.post("/dashboard/export/pdf")
def export_pdf(
    request: Request,
    gender: str = Form(""),
    age_range: str = Form(""),
    competency_code: str = Form(""),
    radar_img: str = Form(""),
    bar_img: str = Form(""),
    dist_img: str = Form(""),
    identity: dict = Depends(require_login),
    service: SupabaseDashboardService = Depends(get_dashboard_service),
) -> Response:
    """Descarga el dashboard actual (filtros + graficos) como archivo PDF."""
    context = service.build_context(
        gender or None, age_range or None, competency_code or None
    )
    if context is None:
        set_flash(request, "No hay datos para exportar con los filtros seleccionados.",
                  "warning")
        return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)

    imagenes = _collect_images(radar_img, bar_img, dist_img)
    contenido = dashboard_exporter.to_pdf(context, imagenes)
    return Response(
        content=contenido,
        media_type=_PDF_MIME,
        headers={"Content-Disposition": f'attachment; filename="{_filename("pdf")}"'},
    )
