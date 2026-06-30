"""Caso de uso: solicitud y verificación de desbloqueo de cuenta.

Dos operaciones:
- execute_request: emite y envía un código de desbloqueo (respuesta genérica).
- execute_unlock: valida el código y reactiva la cuenta.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from application.dto.auth_dto import GenericResponse, UnlockAccountRequest
from domain.entities.verification_code import CodePurpose, VerificationCode
from domain.exceptions.auth_exceptions import (
    MaxVerificationAttemptsError,
    VerificationCodeExpiredError,
    VerificationCodeInvalidError,
)
from domain.ports.outbound.email_service import IEmailService
from domain.ports.outbound.password_hasher import IPasswordHasher
from domain.ports.outbound.user_repository import IUserRepository
from domain.ports.outbound.verification_repository import IVerificationRepository
from domain.rules.auth_rules import (
    VERIFICATION_CODE_EXPIRY_MINUTES,
    generate_verification_code,
)

logger = logging.getLogger(__name__)

_GENERIC_MESSAGE = (
    "Si la cuenta existe y está bloqueada, recibirás un código de desbloqueo."
)


class UnlockAccountUseCase:
    """Caso de uso de desbloqueo de cuenta."""

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

    def execute_request(self, email: str) -> GenericResponse:
        """Emite un código de desbloqueo si la cuenta existe y está bloqueada."""
        normalized = email.strip().lower()
        user = self._user_repo.find_by_email(normalized)

        if user is not None and user.is_locked():
            self._verification_repo.invalidate_previous(
                user.id, CodePurpose.ACCOUNT_UNLOCK
            )
            plain_code = generate_verification_code()
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=VERIFICATION_CODE_EXPIRY_MINUTES
            )
            code = VerificationCode(
                user_id=user.id,
                code_hash=self._hasher.hash_code(plain_code),
                purpose=CodePurpose.ACCOUNT_UNLOCK,
                expires_at=expires_at,
            )
            self._verification_repo.save(code)
            self._email_service.send_unlock_account_email(
                to_email=user.email, user_name=user.full_name, code=plain_code
            )
            logger.info("Código de desbloqueo enviado: %s", normalized)

        return GenericResponse(success=True, message=_GENERIC_MESSAGE)

    def execute_unlock(self, request: UnlockAccountRequest) -> GenericResponse:
        """Valida el código de desbloqueo y reactiva la cuenta."""
        email = request.email.strip().lower()
        user = self._user_repo.find_by_email(email)
        if user is None:
            raise VerificationCodeInvalidError()

        code = self._verification_repo.find_active_by_user_and_purpose(
            user.id, CodePurpose.ACCOUNT_UNLOCK
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

        # Éxito: desbloquear la cuenta y consumir el código.
        user.unlock_account()
        code.mark_as_used()
        self._user_repo.update(user)
        self._verification_repo.update(code)
        logger.info("Cuenta desbloqueada: %s", email)
        return GenericResponse(
            success=True, message="Cuenta desbloqueada. Ya puedes iniciar sesión."
        )
