"""Puerto IEmailService: envío de correos transaccionales.

Puerto de salida. El dominio solo conoce este contrato; la implementación concreta
(p. ej. SmtpEmailService con branding UTPL) vive en infraestructura.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class IEmailService(ABC):
    """Contrato de envío de correos transaccionales."""

    @abstractmethod
    def send_verification_email(self, to_email: str, user_name: str, code: str) -> bool:
        """Envía el correo con el código de verificación de email. Devuelve True si se envió."""
        raise NotImplementedError

    @abstractmethod
    def send_password_reset_email(self, to_email: str, user_name: str, code: str) -> bool:
        """Envía el correo con el código de restablecimiento de contraseña."""
        raise NotImplementedError

    @abstractmethod
    def send_unlock_account_email(self, to_email: str, user_name: str, code: str) -> bool:
        """Envía el correo con el código de desbloqueo de cuenta."""
        raise NotImplementedError

    @abstractmethod
    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Envía el correo de bienvenida tras activar la cuenta."""
        raise NotImplementedError
