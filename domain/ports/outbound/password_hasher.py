"""Puerto IPasswordHasher: hash y verificación de contraseñas y códigos.

Puerto de salida. Abstrae el algoritmo de hashing (la implementación concreta usa
bcrypt rounds=12). El dominio nunca depende directamente de bcrypt.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    """Contrato de hashing y verificación de secretos (contraseñas y códigos)."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Devuelve el hash de una contraseña en texto plano."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool:
        """Indica si la contraseña en texto plano corresponde al hash dado."""
        raise NotImplementedError

    @abstractmethod
    def hash_code(self, code: str) -> str:
        """Devuelve el hash de un código de verificación."""
        raise NotImplementedError

    @abstractmethod
    def verify_code(self, code: str, hashed: str) -> bool:
        """Indica si el código en texto plano corresponde al hash dado."""
        raise NotImplementedError
