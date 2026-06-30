"""Excepciones del dominio de autenticación.

Todas heredan de DomainError → AuthError y llevan mensajes descriptivos en español.
La capa de API las traduce a respuestas HTTP (ver api/middleware/error_handler.py).
"""
from __future__ import annotations


class DomainError(Exception):
    """Excepción base de todos los errores de dominio."""


class AuthError(DomainError):
    """Excepción base de los errores de autenticación."""


class InvalidCredentialsError(AuthError):
    """Credenciales incorrectas (email o contraseña)."""

    def __init__(self, remaining_attempts: int | None = None) -> None:
        self.remaining_attempts = remaining_attempts
        if remaining_attempts is not None:
            message = (
                "Credenciales incorrectas. "
                f"Te quedan {remaining_attempts} intento(s) antes del bloqueo."
            )
        else:
            message = "Credenciales incorrectas."
        super().__init__(message)


class AccountLockedError(AuthError):
    """La cuenta está bloqueada por demasiados intentos fallidos."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(
            f"La cuenta '{email}' está bloqueada por demasiados intentos fallidos. "
            "Solicita el desbloqueo por correo electrónico."
        )


class AccountNotVerifiedError(AuthError):
    """La cuenta existe pero aún no ha verificado su email."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(
            f"La cuenta '{email}' no ha sido verificada. "
            "Revisa tu correo e ingresa el código de verificación."
        )


class AccountInactiveError(AuthError):
    """La cuenta está desactivada."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"La cuenta '{email}' está desactivada.")


class EmailAlreadyExistsError(AuthError):
    """Ya existe un usuario registrado con ese email."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Ya existe una cuenta registrada con el email '{email}'.")


class VerificationCodeExpiredError(AuthError):
    """El código de verificación ha expirado."""

    def __init__(self) -> None:
        super().__init__("El código de verificación ha expirado. Solicita uno nuevo.")


class VerificationCodeInvalidError(AuthError):
    """El código de verificación es incorrecto."""

    def __init__(self, remaining_attempts: int | None = None) -> None:
        self.remaining_attempts = remaining_attempts
        if remaining_attempts is not None:
            message = (
                "El código de verificación es incorrecto. "
                f"Te quedan {remaining_attempts} intento(s)."
            )
        else:
            message = "El código de verificación es incorrecto."
        super().__init__(message)


class MaxVerificationAttemptsError(AuthError):
    """Se alcanzó el número máximo de intentos para un código de verificación."""

    def __init__(self) -> None:
        super().__init__(
            "Se alcanzó el número máximo de intentos para este código. "
            "Solicita un código nuevo."
        )


class PasswordComplexityError(AuthError):
    """La contraseña no cumple los requisitos de complejidad."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        detail = " ".join(errors) if errors else ""
        super().__init__(
            f"La contraseña no cumple los requisitos de seguridad. {detail}".strip()
        )
