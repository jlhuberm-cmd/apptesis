"""Rutas de administración: gestión de encuestas y de usuarios.

Gating por permiso (RBAC):
- Encuestas (subir/borrar): permiso 'cargar_csv' (administrador y analista).
- Usuarios (crear/activar/borrar): permiso 'gestionar_usuarios' (administrador).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER

from api.middleware.auth_middleware import (
    PERM_CARGAR_CSV,
    PERM_GESTIONAR_USUARIOS,
    require_perm,
)
from api.templating import render, set_flash
from config.dependencies import get_auth_service, get_ingestion_service
from infrastructure.adapters.auth.supabase_auth_service import SupabaseAuthService
from infrastructure.adapters.ingestion.supabase_ingestion_service import (
    SupabaseSurveyIngestion,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])

require_csv = require_perm(PERM_CARGAR_CSV)
require_users = require_perm(PERM_GESTIONAR_USUARIOS)


def _redirect(target: str) -> RedirectResponse:
    return RedirectResponse(url=target, status_code=HTTP_303_SEE_OTHER)


def _identity(user: dict) -> dict:
    return {
        "current_user_id": user["id"],
        "current_user_name": user["name"],
        "current_user_role": user["role"],
        "current_permisos": user["permisos"],
    }


@router.get("/admin")
def admin_home(user: dict = Depends(require_csv)) -> Response:
    return _redirect("/admin/encuestas")


# ====================================================================== #
# Gestión de encuestas (permiso cargar_csv)
# ====================================================================== #
@router.get("/admin/encuestas")
def admin_encuestas(
    request: Request,
    user: dict = Depends(require_csv),
    service: SupabaseSurveyIngestion = Depends(get_ingestion_service),
) -> Response:
    encuestas = service.list_encuestas()
    total_respuestas = service.count_respuestas()
    return render(request, "admin/encuestas.html", encuestas=encuestas,
                  total_respuestas=total_respuestas, **_identity(user))


@router.post("/admin/encuestas/upload")
async def admin_upload(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(require_csv),
    service: SupabaseSurveyIngestion = Depends(get_ingestion_service),
) -> Response:
    content = await file.read()
    if not content:
        set_flash(request, "El archivo está vacío.", "error")
        return _redirect("/admin/encuestas")
    nombre = (file.filename or "encuesta.csv").rsplit(".", 1)[0]
    try:
        summary = service.ingest(content, nombre=nombre, archivo_origen=file.filename or "encuesta.csv")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error al cargar la encuesta.")
        set_flash(request, f"No se pudo cargar la encuesta: {exc}", "error")
        return _redirect("/admin/encuestas")
    if summary["procesadas"]:
        set_flash(request, f"Encuesta cargada: {summary['procesadas']} respuestas procesadas"
                  + (f", {summary['errores']} con error." if summary["errores"] else "."), "success")
    else:
        set_flash(request, "No se procesó ninguna respuesta. Revisa el archivo.", "warning")
    return _redirect("/admin/encuestas")


@router.post("/admin/encuestas/delete-all")
def admin_delete_all(
    request: Request,
    user: dict = Depends(require_csv),
    service: SupabaseSurveyIngestion = Depends(get_ingestion_service),
) -> Response:
    try:
        result = service.delete_all()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error al borrar encuestas.")
        set_flash(request, f"No se pudieron borrar los datos: {exc}", "error")
        return _redirect("/admin/encuestas")
    set_flash(request, f"Se borraron {result['encuestas_borradas']} encuesta(s) y sus datos.", "success")
    return _redirect("/admin/encuestas")


# ====================================================================== #
# Gestión de usuarios (permiso gestionar_usuarios)
# ====================================================================== #
@router.get("/admin/usuarios")
def admin_usuarios(
    request: Request,
    user: dict = Depends(require_users),
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> Response:
    usuarios = auth.list_usuarios()
    roles = auth.list_roles()
    return render(request, "admin/usuarios.html", usuarios=usuarios, roles=roles,
                  current_id=user["id"], **_identity(user))


@router.post("/admin/usuarios")
def admin_crear_usuario(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    id_rol: str = Form(...),
    user: dict = Depends(require_users),
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> Response:
    if len(password) < 6:
        set_flash(request, "La contraseña debe tener al menos 6 caracteres.", "error")
        return _redirect("/admin/usuarios")
    try:
        auth.create_usuario(email=email, password=password, nombre=nombre, id_rol=id_rol)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error al crear usuario.")
        set_flash(request, f"No se pudo crear el usuario: {exc}", "error")
        return _redirect("/admin/usuarios")
    set_flash(request, f"Usuario '{email}' creado correctamente.", "success")
    return _redirect("/admin/usuarios")


@router.post("/admin/usuarios/{id_usuario}/estado")
def admin_toggle_estado(
    request: Request,
    id_usuario: str,
    estado: str = Form(...),
    user: dict = Depends(require_users),
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> Response:
    auth.set_estado(id_usuario, estado == "true")
    set_flash(request, "Estado del usuario actualizado.", "success")
    return _redirect("/admin/usuarios")


@router.post("/admin/usuarios/{id_usuario}/delete")
def admin_delete_usuario(
    request: Request,
    id_usuario: str,
    user: dict = Depends(require_users),
    auth: SupabaseAuthService = Depends(get_auth_service),
) -> Response:
    if id_usuario == user["id"]:
        set_flash(request, "No puedes borrar tu propia cuenta.", "warning")
        return _redirect("/admin/usuarios")
    try:
        auth.delete_usuario(id_usuario)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error al borrar usuario.")
        set_flash(request, f"No se pudo borrar el usuario: {exc}", "error")
        return _redirect("/admin/usuarios")
    set_flash(request, "Usuario borrado.", "success")
    return _redirect("/admin/usuarios")
