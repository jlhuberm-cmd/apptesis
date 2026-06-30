"""Adaptador BcryptPasswordHasher: implementa IPasswordHasher con bcrypt (rounds=12).

Encapsula el algoritmo bcrypt para hashear y verificar contraseñas y códigos de
verificación. Es el único punto del sistema que depende de la librería bcrypt.
"""
from __future__ import annotations

import bcrypt

from domain.ports.outbound.password_hasher import IPasswordHasher

# bcrypt opera sobre como máximo 72 bytes; se truncan entradas más largas.
_BCRYPT_MAX_BYTES = 72


class BcryptPasswordHasher(IPasswordHasher):
    """Implementación de IPasswordHasher basada en bcrypt."""

    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    # ------------------------------------------------------------------ #
    # Contraseñas
    # ------------------------------------------------------------------ #
    def hash(self, password: str) -> str:
        """Devuelve el hash bcrypt de una contraseña en texto plano."""
        salt = bcrypt.gensalt(rounds=self._rounds)
        digest = bcrypt.hashpw(self._encode(password), salt)
        return digest.decode("utf-8")

    def verify(self, password: str, hashed: str) -> bool:
        """Indica si la contraseña corresponde al hash dado."""
        try:
            return bcrypt.checkpw(self._encode(password), hashed.encode("utf-8"))
        except (ValueError, TypeError):
            return False

    # ------------------------------------------------------------------ #
    # Códigos de verificación (mismo mecanismo bcrypt)
    # ------------------------------------------------------------------ #
    def hash_code(self, code: str) -> str:
        """Devuelve el hash bcrypt de un código de verificación."""
        return self.hash(code)

    def verify_code(self, code: str, hashed: str) -> bool:
        """Indica si el código corresponde al hash dado."""
        return self.verify(code, hashed)

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #
    @staticmethod
    def _encode(value: str) -> bytes:
        """Codifica a bytes y trunca al límite de 72 bytes de bcrypt."""
        return value.encode("utf-8")[:_BCRYPT_MAX_BYTES]
