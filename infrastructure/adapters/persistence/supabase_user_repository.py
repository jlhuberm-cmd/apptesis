"""Adaptador SupabaseUserRepository: implementa IUserRepository.

Traduce entre la entidad de dominio User y las filas de la tabla `users` de Supabase.
El dominio nunca ve diccionarios ni detalles de Supabase: solo entidades.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from supabase import Client

from domain.entities.user import AccountStatus, User, UserRole
from domain.ports.outbound.user_repository import IUserRepository

logger = logging.getLogger(__name__)

_TABLE = "users"


class SupabaseUserRepository(IUserRepository):
    """Implementación de IUserRepository sobre la tabla `users` de Supabase."""

    def __init__(self, client: Client) -> None:
        self._client = client

    @property
    def _table(self):
        return self._client.table(_TABLE)

    # ------------------------------------------------------------------ #
    # Operaciones
    # ------------------------------------------------------------------ #
    def save(self, user: User) -> User:
        """Inserta un usuario nuevo."""
        self._table.insert(self._to_row(user)).execute()
        logger.info("Usuario insertado: %s", user.email)
        return user

    def find_by_id(self, user_id: UUID) -> User | None:
        """Busca un usuario por su id."""
        result = self._table.select("*").eq("id", str(user_id)).limit(1).execute()
        rows = result.data or []
        return self._to_entity(rows[0]) if rows else None

    def find_by_email(self, email: str) -> User | None:
        """Busca un usuario por su email (normalizado en minúsculas)."""
        result = (
            self._table.select("*").eq("email", email.strip().lower()).limit(1).execute()
        )
        rows = result.data or []
        return self._to_entity(rows[0]) if rows else None

    def update(self, user: User) -> User:
        """Actualiza un usuario existente por id."""
        self._table.update(self._to_row(user)).eq("id", str(user.id)).execute()
        logger.info("Usuario actualizado: %s", user.email)
        return user

    def exists_by_email(self, email: str) -> bool:
        """Indica si existe un usuario con el email dado."""
        result = (
            self._table.select("id")
            .eq("email", email.strip().lower())
            .limit(1)
            .execute()
        )
        return bool(result.data)

    # ------------------------------------------------------------------ #
    # Mapeo entidad <-> fila
    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_row(user: User) -> dict[str, Any]:
        """Convierte la entidad User en una fila serializable para Supabase."""
        return {
            "id": str(user.id),
            "email": user.email,
            "hashed_password": user.hashed_password,
            "full_name": user.full_name,
            "role": user.role.value,
            "status": user.status.value,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_at": user.locked_at.isoformat() if user.locked_at else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> User:
        """Convierte una fila de Supabase en una entidad User."""
        return User(
            id=UUID(str(row["id"])),
            email=row["email"],
            hashed_password=row["hashed_password"],
            full_name=row["full_name"],
            role=UserRole(row["role"]),
            status=AccountStatus(row["status"]),
            failed_login_attempts=row.get("failed_login_attempts", 0),
            locked_at=_parse_dt(row.get("locked_at")),
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )


def _parse_dt(value: str | datetime | None) -> datetime | None:
    """Parsea un timestamp ISO de Supabase a datetime (acepta sufijo 'Z')."""
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
