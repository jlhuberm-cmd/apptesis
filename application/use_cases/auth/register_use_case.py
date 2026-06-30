"""Caso de uso: registro de usuario y envío de código de verificación.

Orquesta el alta de una cuenta: valida los datos, crea el usuario en estado
PENDING_VERIFICATION, genera un código de verificación y dispara el correo.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from application.dto.auth_dto import RegisterRequest, RegisterResponse
from domain.entities.user import AccountStatus, User
from domain.entities.verification_code import CodePurpose, VerificationCode
from domain.exceptions.auth_exceptions import (
    EmailAlreadyExistsError,
    PasswordComplexityError,
)
from domain.ports.outbound.email_service import IEmailService
from domain.ports.outbound.password_hasher import IPasswordHasher
from domain.ports.outbound.user_repository import IUserRepository
from domain.ports.outbound.verification_repository import IVerificationRepository
from domain.rules.auth_rules import (
    VERIFICATION_CODE_EXPIRY_MINUTES,
    generate_verification_code,
)
from domain.value_objects.email_address import EmailAddress
from domain.value_objects.password import Password

logger = logging.getLogger(__name__)


class RegisterUseCase:
    """Caso de uso de registro de usuario."""

    def __init__(
        self,
        user_repo: IUserRepository,
        password_hasher: IPasswordHasher,
        verification_repo: IVerificationRepository,
        email_service: IEmailService,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = password_hasher
        self._verification_repo = verification_repo
        self._email_service = email_service

    def execute(self, request: RegisterRequest) -> RegisterResponse:
        """Registra un usuario nuevo y envía el código de verificación."""
        # 1. Coincidencia de contraseñas.
        if request.password != request.confirm_password:
            raise ValueError("Las contraseñas no coinciden.")

        # 2. Complejidad de la contraseña.
        errors = Password.check(request.password)
        if errors:
            raise PasswordComplexityError(errors)

        # 3. Email válido y normalizado.
        email = EmailAddress(request.email).value

        # 4. Unicidad del email.
        if self._user_repo.exists_by_email(email):
            raise EmailAlreadyExistsError(email)

        # 5-6. Crear y guardar el usuario (pendiente de verificación).
        hashed = self._hasher.hash(request.password)
        user = User(
            email=email,
            hashed_password=hashed,
            full_name=request.full_name.strip(),
            status=AccountStatus.PENDING_VERIFICATION,
        )
        user = self._user_repo.save(user)

        # 7-10. Generar, hashear y guardar el código de verificación.
        plain_code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=VERIFICATION_CODE_EXPIRY_MINUTES
        )
        code = VerificationCode(
            user_id=user.id,
            code_hash=self._hasher.hash_code(plain_code),
            purpose=CodePurpose.EMAIL_VERIFICATION,
            expires_at=expires_at,
        )
        self._verification_repo.save(code)

        # 11. Enviar el correo con el código en texto plano.
        self._email_service.send_verification_email(
            to_email=user.email, user_name=user.full_name, code=plain_code
        )

        logger.info("Usuario registrado (pendiente de verificación): %s", email)
        return RegisterResponse(user_id=user.id, email=user.email)
