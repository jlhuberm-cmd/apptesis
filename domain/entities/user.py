"""Entidad User (usuario del sistema) con sus enums UserRole y AccountStatus
y la lógica de bloqueo/desbloqueo por intentos fallidos.

Esta entidad pertenece al núcleo del dominio: NO importa nada de infraestructura
(Supabase, bcrypt, FastAPI). Encapsula las reglas de negocio relacionadas con el
estado de la cuenta y los intentos de inicio de sesión.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

# Número máximo de intentos fallidos de login antes de bloquear la cuenta.
# (También se define en domain.rules.auth_rules; aquí se mantiene una copia
# local para que la entidad sea autosuficiente y no dependa de las reglas.)
MAX_LOGIN_ATTEMPTS: int = 3


class UserRole(str, Enum):
    """Rol del usuario dentro de la plataforma."""

    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"
    VIEWER = "VIEWER"


class AccountStatus(str, Enum):
    """Estado del ciclo de vida de una cuenta de usuario."""

    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    INACTIVE = "INACTIVE"


def _utcnow() -> datetime:
    """Devuelve la hora actual en UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


class User(BaseModel):
    """Usuario del sistema.

    Atributos:
        id: Identificador único (UUID).
        email: Correo electrónico (normalizado en minúsculas por el dominio).
        hashed_password: Hash de la contraseña (nunca el texto plano).
        full_name: Nombre completo del usuario.
        role: Rol (ADMIN, RESEARCHER, VIEWER).
        status: Estado de la cuenta (PENDING_VERIFICATION, ACTIVE, LOCKED, INACTIVE).
        failed_login_attempts: Contador de intentos fallidos consecutivos.
        locked_at: Momento en que la cuenta fue bloqueada (None si no está bloqueada).
        created_at: Fecha de creación.
        updated_at: Fecha de la última modificación.
    """

    model_config = ConfigDict(use_enum_values=False, validate_assignment=True)

    id: UUID = Field(default_factory=uuid4)
    email: str
    hashed_password: str
    full_name: str
    role: UserRole = UserRole.VIEWER
    status: AccountStatus = AccountStatus.PENDING_VERIFICATION
    failed_login_attempts: int = Field(default=0, ge=0)
    locked_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    # ------------------------------------------------------------------ #
    # Consultas (sin efectos secundarios)
    # ------------------------------------------------------------------ #
    def is_locked(self) -> bool:
        """Indica si la cuenta está bloqueada."""
        return self.status == AccountStatus.LOCKED

    def is_active(self) -> bool:
        """Indica si la cuenta está activa y puede operar normalmente."""
        return self.status == AccountStatus.ACTIVE

    def can_attempt_login(self) -> bool:
        """Indica si aún quedan intentos de login disponibles (< máximo)."""
        return self.failed_login_attempts < MAX_LOGIN_ATTEMPTS

    def remaining_login_attempts(self) -> int:
        """Número de intentos de login restantes antes del bloqueo."""
        return max(0, MAX_LOGIN_ATTEMPTS - self.failed_login_attempts)

    # ------------------------------------------------------------------ #
    # Comandos (mutan el estado de la entidad)
    # ------------------------------------------------------------------ #
    def record_failed_attempt(self) -> None:
        """Incrementa el contador de intentos fallidos de login."""
        self.failed_login_attempts += 1
        self._touch()

    def reset_failed_attempts(self) -> None:
        """Reinicia el contador de intentos fallidos (login exitoso)."""
        self.failed_login_attempts = 0
        self._touch()

    def lock_account(self) -> None:
        """Bloquea la cuenta: cambia el estado a LOCKED y registra el momento."""
        self.status = AccountStatus.LOCKED
        self.locked_at = _utcnow()
        self._touch()

    def unlock_account(self) -> None:
        """Desbloquea la cuenta: reinicia intentos, estado ACTIVE y limpia locked_at."""
        self.failed_login_attempts = 0
        self.status = AccountStatus.ACTIVE
        self.locked_at = None
        self._touch()

    def activate(self) -> None:
        """Activa una cuenta que estaba pendiente de verificación."""
        if self.status == AccountStatus.PENDING_VERIFICATION:
            self.status = AccountStatus.ACTIVE
            self._touch()

    def deactivate(self) -> None:
        """Desactiva la cuenta (estado INACTIVE)."""
        self.status = AccountStatus.INACTIVE
        self._touch()

    def change_password(self, new_hashed_password: str) -> None:
        """Actualiza el hash de la contraseña del usuario."""
        self.hashed_password = new_hashed_password
        self._touch()

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #
    def _touch(self) -> None:
        """Actualiza la marca de tiempo de última modificación."""
        self.updated_at = _utcnow()
