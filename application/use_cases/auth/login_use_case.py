"""Caso de uso: inicio de sesión (login).

Orquesta la autenticación: valida credenciales, controla el estado de la cuenta y
gestiona el bloqueo por intentos fallidos. La lógica de negocio (incrementar
intentos, decidir el bloqueo) vive en la entidad User y en las reglas del dominio.
"""
from __future__ import annotations

import logging

from application.dto.auth_dto import LoginRequest, LoginResponse
from domain.entities.user import AccountStatus
from domain.exceptions.auth_exceptions import (
    AccountInactiveError,
    AccountLockedError,
    AccountNotVerifiedError,
    InvalidCredentialsError,
)
from domain.ports.outbound.password_hasher import IPasswordHasher
from domain.ports.outbound.user_repository import IUserRepository
from domain.rules.auth_rules import should_lock_account

logger = logging.getLogger(__name__)


class LoginUseCase:
    """Caso de uso de inicio de sesión."""

    def __init__(
        self, user_repo: IUserRepository, password_hasher: IPasswordHasher
    ) -> None:
        self._user_repo = user_repo
        self._hasher = password_hasher

    def execute(self, request: LoginRequest) -> LoginResponse:
        """Autentica al usuario o lanza una excepción de dominio si falla."""
        email = request.email.strip().lower()
        user = self._user_repo.find_by_email(email)

        # No revelar si el email existe: mismo error genérico.
        if user is None:
            logger.info("Login fallido: email no encontrado.")
            raise InvalidCredentialsError()

        # Verificar el estado de la cuenta antes de comprobar la contraseña.
        if user.status == AccountStatus.PENDING_VERIFICATION:
            raise AccountNotVerifiedError(email)
        if user.status == AccountStatus.LOCKED:
            raise AccountLockedError(email)
        if user.status == AccountStatus.INACTIVE:
            raise AccountInactiveError(email)

        # Comprobar la contraseña.
        if not self._hasher.verify(request.password, user.hashed_password):
            user.record_failed_attempt()
            if should_lock_account(user.failed_login_attempts):
                user.lock_account()
                self._user_repo.update(user)
                logger.warning("Cuenta bloqueada por intentos fallidos: %s", email)
                raise AccountLockedError(email)
            self._user_repo.update(user)
            logger.info("Login fallido: contraseña incorrecta para %s", email)
            raise InvalidCredentialsError(
                remaining_attempts=user.remaining_login_attempts()
            )

        # Éxito: reiniciar el contador de intentos si fuese necesario.
        if user.failed_login_attempts > 0:
            user.reset_failed_attempts()
            self._user_repo.update(user)

        logger.info("Login exitoso: %s", email)
        return LoginResponse(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
        )
