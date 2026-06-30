"""Caso de uso: restablecimiento de contraseña con código.

Valida el código de recuperación y cambia la contraseña. Si la cuenta estaba
bloqueada, también la desbloquea.
"""
from __future__ import annotations

import logging

from application.dto.auth_dto import GenericResponse, ResetPasswordRequest
from domain.entities.verification_code import CodePurpose
from domain.exceptions.auth_exceptions import (
    MaxVerificationAttemptsError,
    PasswordComplexityError,
    VerificationCodeExpiredError,
    VerificationCodeInvalidError,
)
from domain.ports.outbound.password_hasher import IPasswordHasher
from domain.ports.outbound.user_repository import IUserRepository
from domain.ports.outbound.verification_repository import IVerificationRepository
from domain.value_objects.password import Password

logger = logging.getLogger(__name__)


class ResetPasswordUseCase:
    """Caso de uso de restablecimiento de contraseña."""

    def __init__(
        self,
        user_repo: IUserRepository,
        verification_repo: IVerificationRepository,
        password_hasher: IPasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._verification_repo = verification_repo
        self._hasher = password_hasher

    def execute(self, request: ResetPasswordRequest) -> GenericResponse:
        """Restablece la contraseña validando el código de recuperación."""
        # 1-2. Validaciones de la nueva contraseña.
        if request.new_password != request.confirm_password:
            raise ValueError("Las contraseñas no coinciden.")
        errors = Password.check(request.new_password)
        if errors:
            raise PasswordComplexityError(errors)

        # 3. Usuario (no revelar inexistencia).
        email = request.email.strip().lower()
        user = self._user_repo.find_by_email(email)
        if user is None:
            raise VerificationCodeInvalidError()

        # 4-5. Código de reset y su validación.
        code = self._verification_repo.find_active_by_user_and_purpose(
            user.id, CodePurpose.PASSWORD_RESET
        )
        if code is None or code.is_expired():
            raise VerificationCodeExpiredError()
        if not code.has_remaining_attempts():
            raise MaxVerificationAttemptsError()
        if not self._hasher.verify_code(request.code, code.code_hash):
            code.record_attempt()
            self._verification_repo.update(code)
            remaining = code.max_attempts - code.attempts
            raise VerificationCodeInvalidError(remaining_attempts=remaining)

        # 6-9. Cambiar la contraseña, consumir el código y desbloquear si procede.
        user.change_password(self._hasher.hash(request.new_password))
        code.mark_as_used()
        if user.is_locked():
            user.unlock_account()

        self._user_repo.update(user)
        self._verification_repo.update(code)
        logger.info("Contraseña restablecida: %s", email)
        return GenericResponse(
            success=True, message="Contraseña restablecida. Ya puedes iniciar sesión."
        )
