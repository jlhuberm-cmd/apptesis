"""Adaptador SupabaseVerificationRepository: implementa IVerificationRepository.

Traduce entre la entidad VerificationCode y la tabla `verification_codes` de Supabase.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from supabase import Client

from domain.entities.verification_code import CodePurpose, VerificationCode
from domain.ports.outbound.verification_repository import IVerificationRepository

logger = logging.getLogger(__name__)

_TABLE = "verification_codes"


class SupabaseVerificationRepository(IVerificationRepository):
    """Implementación de IVerificationRepository sobre Supabase."""

    def __init__(self, client: Client) -> None:
        self._client = client

    @property
    def _table(self):
        return self._client.table(_TABLE)

    def save(self, code: VerificationCode) -> VerificationCode:
        self._table.insert(self._to_row(code)).execute()
        return code

    def find_active_by_user_and_purpose(
        self, user_id: UUID, purpose: CodePurpose
    ) -> VerificationCode | None:
        """Devuelve el último código no usado y no expirado del usuario/propósito."""
        now_iso = datetime.now(timezone.utc).isoformat()
        result = (
            self._table.select("*")
            .eq("user_id", str(user_id))
            .eq("purpose", purpose.value)
            .is_("used_at", "null")
            .gt("expires_at", now_iso)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        return self._to_entity(rows[0]) if rows else None

    def update(self, code: VerificationCode) -> VerificationCode:
        self._table.update(self._to_row(code)).eq("id", str(code.id)).execute()
        return code

    def invalidate_previous(self, user_id: UUID, purpose: CodePurpose) -> None:
        """Marca como usados los códigos previos no usados del usuario/propósito."""
        now_iso = datetime.now(timezone.utc).isoformat()
        (
            self._table.update({"used_at": now_iso})
            .eq("user_id", str(user_id))
            .eq("purpose", purpose.value)
            .is_("used_at", "null")
            .execute()
        )

    # ------------------------------------------------------------------ #
    # Mapeo entidad <-> fila
    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_row(code: VerificationCode) -> dict[str, Any]:
        return {
            "id": str(code.id),
            "user_id": str(code.user_id),
            "code_hash": code.code_hash,
            "purpose": code.purpose.value,
            "attempts": code.attempts,
            "max_attempts": code.max_attempts,
            "expires_at": code.expires_at.isoformat(),
            "used_at": code.used_at.isoformat() if code.used_at else None,
            "created_at": code.created_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> VerificationCode:
        return VerificationCode(
            id=UUID(str(row["id"])),
            user_id=UUID(str(row["user_id"])),
            code_hash=row["code_hash"],
            purpose=CodePurpose(row["purpose"]),
            attempts=row.get("attempts", 0),
            max_attempts=row.get("max_attempts", 3),
            expires_at=_parse_dt(row["expires_at"]),
            used_at=_parse_dt(row.get("used_at")),
            created_at=_parse_dt(row["created_at"]),
        )


def _parse_dt(value: str | datetime | None) -> datetime | None:
    """Parsea un timestamp ISO de Supabase a datetime (acepta sufijo 'Z')."""
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
