"""Caso de uso: verificación de email y activación de cuenta.

Orquesta la validación del código de verificación (expiración, intentos, hash) y
la activación de la cuenta. La lógica de estado vive en las entidades.
"""
from __future__ import annotations

import logging

from application.dto.auth_dto import GenericResponse, VerifyEmailRequest
from domain.entities.verification_code import CodePurpose
from domain.exceptions.auth_exceptions import (
    MaxVerificationAttemptsError,
    VerificationCodeExpiredError,
    VerificationCodeInvalidError,
)
from domain.ports.outbound.email_service import IEmailService
from domain.ports.outbound.password_hasher import IPasswordHasher
from domain.ports.outbound.user_repository import IUserRepository
from domain.ports.outbound.verification_repository import IVerificationRepository

logger = logging.getLogger(__name__)


class VerifyEmailUseCase:
    """Caso de uso de verificación de email."""

    def __init__(
        self,
        user_repo: IUserRepository,
        verification_repo: IVerificationRepository,
        password_hasher: IPasswordHasher,
        email_service: IEmailService,
    ) -> None:
        self._user_repo = user_repo
        self._verification_repo = verification_repo
        self._hasher = password_hasher
        self._email_service = email_service

    def execute(self, request: VerifyEmailRequest) -> GenericResponse:
        """Verifica el email mediante el código y activa la cuenta."""
        email = request.email.strip().lower()
        user = self._user_repo.find_by_email(email)
        if user is None:
            # No revelar inexistencia: mismo error que un código inválido.
            raise VerificationCodeInvalidError()

        code = self._verification_repo.find_active_by_user_and_purpose(
            user.id, CodePurpose.EMAIL_VERIFICATION
        )
        if code is None:
            raise VerificationCodeExpiredError()
        if code.is_expired():
            raise VerificationCodeExpiredError()
        if not code.has_remaining_attempts():
            raise MaxVerificationAttemptsError()

        # Verificar el código.
        if not self._hasher.verify_code(request.code, code.code_hash):
            code.record_attempt()
            self._verification_repo.update(code)
            remaining = code.max_attempts - code.attempts
            raise VerificationCodeInvalidError(remaining_attempts=remaining)

        # Éxito: marcar código usado y activar la cuenta.
        code.mark_as_used()
        self._verification_repo.update(code)
        user.activate()
        self._user_repo.update(user)

        self._email_service.send_welcome_email(
            to_email=user.email, user_name=user.full_name
        )
        logger.info("Email verificado y cuenta activada: %s", email)
        return GenericResponse(
            success=True, message="Cuenta verificada correctamente. Ya puedes iniciar sesión."
        )
