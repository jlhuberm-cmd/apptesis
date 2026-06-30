"""Caso de uso: solicitud de recuperación de contraseña.

Genera y envía un código de restablecimiento. Por seguridad, SIEMPRE responde con
éxito para no revelar si el email está registrado (evita enumeración de cuentas).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from application.dto.auth_dto import ForgotPasswordRequest, GenericResponse
from domain.entities.verification_code import CodePurpose, VerificationCode
from domain.ports.outbound.email_service import IEmailService
from domain.ports.outbound.password_hasher import IPasswordHasher
from domain.ports.outbound.user_repository import IUserRepository
from domain.ports.outbound.verification_repository import IVerificationRepository
from domain.rules.auth_rules import (
    VERIFICATION_CODE_EXPIRY_MINUTES,
    generate_verification_code,
)

logger = logging.getLogger(__name__)

# Mensaje genérico independiente de si el email existe o no.
_GENERIC_MESSAGE = "Si el email está registrado, recibirás un código de recuperación."


class ForgotPasswordUseCase:
    """Caso de uso de solicitud de recuperación de contraseña."""

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

    def execute(self, request: ForgotPasswordRequest) -> GenericResponse:
        """Genera y envía un código de restablecimiento (respuesta siempre genérica)."""
        email = request.email.strip().lower()
        user = self._user_repo.find_by_email(email)

        if user is None:
            logger.info("Recuperación solicitada para email inexistente (silenciado).")
            return GenericResponse(success=True, message=_GENERIC_MESSAGE)

        # Invalidar códigos previos de reset y emitir uno nuevo.
        self._verification_repo.invalidate_previous(user.id, CodePurpose.PASSWORD_RESET)

        plain_code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=VERIFICATION_CODE_EXPIRY_MINUTES
        )
        code = VerificationCode(
            user_id=user.id,
            code_hash=self._hasher.hash_code(plain_code),
            purpose=CodePurpose.PASSWORD_RESET,
            expires_at=expires_at,
        )
        self._verification_repo.save(code)

        self._email_service.send_password_reset_email(
            to_email=user.email, user_name=user.full_name, code=plain_code
        )
        logger.info("Código de recuperación enviado: %s", email)
        return GenericResponse(success=True, message=_GENERIC_MESSAGE)
