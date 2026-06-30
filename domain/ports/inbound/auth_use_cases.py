"""Puerto IAuthService: contrato de los casos de uso de autenticación.

Puerto de entrada. Define las operaciones de autenticación que la capa de interfaz
(API) puede solicitar al núcleo. La implementación orquesta entidades, reglas y
puertos de salida.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.user import User


class IAuthService(ABC):
    """Contrato de los casos de uso de autenticación."""

    @abstractmethod
    def login(self, email: str, password: str) -> User:
        """Autentica a un usuario. Lanza excepciones de dominio si falla."""
        raise NotImplementedError

    @abstractmethod
    def register(self, email: str, password: str, full_name: str) -> User:
        """Registra un usuario nuevo (estado PENDING_VERIFICATION) y envía el código."""
        raise NotImplementedError

    @abstractmethod
    def verify_email(self, email: str, code: str) -> bool:
        """Verifica el email mediante el código y activa la cuenta."""
        raise NotImplementedError

    @abstractmethod
    def request_password_reset(self, email: str) -> bool:
        """Genera y envía un código para restablecer la contraseña."""
        raise NotImplementedError

    @abstractmethod
    def reset_password(self, email: str, code: str, new_password: str) -> bool:
        """Restablece la contraseña validando el código de recuperación."""
        raise NotImplementedError

    @abstractmethod
    def request_account_unlock(self, email: str) -> bool:
        """Genera y envía un código para desbloquear la cuenta."""
        raise NotImplementedError

    @abstractmethod
    def unlock_account(self, email: str, code: str) -> bool:
        """Desbloquea la cuenta validando el código de desbloqueo."""
        raise NotImplementedError
