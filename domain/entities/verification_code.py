"""Entidad VerificationCode: código de verificación de 6 dígitos con propósito,
intentos, expiración y estado de uso.

Núcleo del dominio: NO importa nada de infraestructura. El hash del código lo
calcula un adaptador externo (IPasswordHasher); aquí solo se almacena el hash y
se gestionan las reglas de intentos, expiración y uso.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class CodePurpose(str, Enum):
    """Propósito para el cual se generó un código de verificación."""

    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    PASSWORD_RESET = "PASSWORD_RESET"
    ACCOUNT_UNLOCK = "ACCOUNT_UNLOCK"


def _utcnow() -> datetime:
    """Devuelve la hora actual en UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


class VerificationCode(BaseModel):
    """Código de verificación de un solo uso.

    Atributos:
        id: Identificador único del código.
        user_id: UUID del usuario al que pertenece el código.
        code_hash: Hash del código de 6 dígitos (nunca el texto plano).
        purpose: Propósito (verificación de email, reset de contraseña, desbloqueo).
        attempts: Número de intentos de validación ya realizados.
        max_attempts: Número máximo de intentos permitidos.
        expires_at: Momento de expiración del código.
        used_at: Momento en que el código fue usado (None si sigue disponible).
        created_at: Fecha de creación.
    """

    model_config = ConfigDict(use_enum_values=False, validate_assignment=True)

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    code_hash: str
    purpose: CodePurpose
    attempts: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    # ------------------------------------------------------------------ #
    # Consultas (sin efectos secundarios)
    # ------------------------------------------------------------------ #
    def is_expired(self) -> bool:
        """Indica si el código ya expiró comparándolo con la hora actual (UTC)."""
        return _utcnow() >= self._aware(self.expires_at)

    def is_used(self) -> bool:
        """Indica si el código ya fue utilizado."""
        return self.used_at is not None

    def has_remaining_attempts(self) -> bool:
        """Indica si aún quedan intentos de validación disponibles."""
        return self.attempts < self.max_attempts

    def is_valid(self) -> bool:
        """Indica si el código está disponible: no usado, no expirado y con intentos."""
        return not self.is_used() and not self.is_expired() and self.has_remaining_attempts()

    # ------------------------------------------------------------------ #
    # Comandos (mutan el estado de la entidad)
    # ------------------------------------------------------------------ #
    def record_attempt(self) -> None:
        """Incrementa el contador de intentos de validación."""
        self.attempts += 1

    def mark_as_used(self) -> None:
        """Marca el código como usado registrando el momento."""
        self.used_at = _utcnow()

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #
    @staticmethod
    def _aware(value: datetime) -> datetime:
        """Garantiza que un datetime tenga zona horaria (asume UTC si es naïve)."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
