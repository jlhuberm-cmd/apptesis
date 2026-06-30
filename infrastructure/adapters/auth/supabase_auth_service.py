"""Servicio de autenticación y gestión de usuarios sobre Supabase Auth.

- Login: `sign_in_with_password` (cliente anónimo) → resuelve perfil (usuarios),
  rol(es) y permisos (usuario_rol + roles).
- Gestión (solo admin): crear/activar/desactivar/borrar usuarios vía Admin API
  (cliente con service_role).
"""
from __future__ import annotations

import logging

from supabase import Client, create_client

logger = logging.getLogger(__name__)


class SupabaseAuthService:
    """Autenticación contra Supabase Auth + perfiles/roles/permisos en la base."""

    def __init__(self, url: str, anon_key: str, db_client: Client) -> None:
        self._url = url
        self._anon_key = anon_key
        self._db = db_client

    def _anon(self) -> Client:
        """Cliente anónimo nuevo por operación (evita compartir sesión)."""
        return create_client(self._url, self._anon_key)

    # ------------------------------------------------------------------ #
    # Login
    # ------------------------------------------------------------------ #
    def authenticate(self, email: str, password: str) -> dict | None:
        """Valida credenciales y devuelve la identidad (id, email, nombre, rol,
        roles, permisos, id_empresa) o None si fallan / la cuenta está inactiva."""
        try:
            res = self._anon().auth.sign_in_with_password(
                {"email": email.strip().lower(), "password": password}
            )
        except Exception as exc:  # noqa: BLE001 - credenciales inválidas u otro
            logger.info("Login fallido (%s): %s", email, type(exc).__name__)
            return None

        if not res or not res.user:
            return None
        uid = res.user.id

        prof = self._db.table("usuarios").select("*").eq("id_usuario", uid).limit(1).execute().data
        if not prof:
            prof = (
                self._db.table("usuarios").select("*")
                .eq("email", email.strip().lower()).limit(1).execute().data
            )
        if not prof:
            logger.warning("Auth OK pero sin perfil en 'usuarios': %s", email)
            return None
        prof = prof[0]
        if not prof.get("estado", True):
            logger.info("Cuenta inactiva: %s", email)
            return None

        nombres, permisos = self._roles_and_permisos(prof["id_usuario"])
        return {
            "id": prof["id_usuario"],
            "email": prof["email"],
            "name": prof["nombre_completo"],
            "role": nombres[0] if nombres else "sin rol",
            "roles": nombres,
            "permisos": permisos,
            "id_empresa": prof["id_empresa"],
        }

    def _roles_and_permisos(self, id_usuario: str) -> tuple[list[str], list[str]]:
        ur = self._db.table("usuario_rol").select("id_rol").eq("id_usuario", id_usuario).execute().data
        role_ids = [x["id_rol"] for x in ur]
        roles = {r["id_rol"]: r for r in self._db.table("roles").select("*").execute().data}
        nombres = [roles[i]["nombre_rol"] for i in role_ids if i in roles]
        permisos = sorted({
            p for i in role_ids if i in roles for p in (roles[i].get("permisos") or [])
        })
        return nombres, permisos

    # ------------------------------------------------------------------ #
    # Gestión de usuarios (Admin API)
    # ------------------------------------------------------------------ #
    def list_roles(self) -> list[dict]:
        return self._db.table("roles").select("id_rol,nombre_rol,descripcion").order("nombre_rol").execute().data

    def list_usuarios(self) -> list[dict]:
        usuarios = self._db.table("usuarios").select("*").order("created_at").execute().data
        ur = self._db.table("usuario_rol").select("*").execute().data
        roles = {r["id_rol"]: r["nombre_rol"] for r in self._db.table("roles").select("*").execute().data}
        por_usuario: dict[str, list[str]] = {}
        for x in ur:
            por_usuario.setdefault(x["id_usuario"], []).append(roles.get(x["id_rol"], "?"))
        return [
            {
                "id": u["id_usuario"], "email": u["email"],
                "nombre": u["nombre_completo"], "estado": u["estado"],
                "roles": por_usuario.get(u["id_usuario"], []),
            }
            for u in usuarios
        ]

    def _default_empresa(self) -> str:
        emp = self._db.table("empresas").select("id_empresa").limit(1).execute().data
        if not emp:
            raise RuntimeError("No hay empresas configuradas.")
        return emp[0]["id_empresa"]

    def create_usuario(self, email: str, password: str, nombre: str, id_rol: str) -> str:
        """Crea un usuario en Supabase Auth + perfil + rol. Devuelve el id."""
        email = email.strip().lower()
        created = self._db.auth.admin.create_user(
            {"email": email, "password": password, "email_confirm": True}
        )
        uid = created.user.id
        self._db.table("usuarios").insert({
            "id_usuario": uid, "id_empresa": self._default_empresa(),
            "nombre_completo": nombre.strip(), "email": email, "estado": True,
        }).execute()
        self._db.table("usuario_rol").insert({"id_usuario": uid, "id_rol": id_rol}).execute()
        logger.info("Usuario creado: %s", email)
        return uid

    def set_estado(self, id_usuario: str, estado: bool) -> None:
        self._db.table("usuarios").update({"estado": estado}).eq("id_usuario", id_usuario).execute()

    def delete_usuario(self, id_usuario: str) -> None:
        """Borra el usuario de Auth (cascade elimina perfil y roles)."""
        self._db.auth.admin.delete_user(id_usuario)
        logger.info("Usuario borrado: %s", id_usuario)
