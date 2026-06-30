"""Puerto IVerificationRepository: persistencia de códigos de verificación.

Puerto de salida. Gestiona el almacenamiento de códigos de verificación y la
invalidación de los anteriores cuando se emite uno nuevo.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.verification_code import CodePurpose, VerificationCode


class IVerificationRepository(ABC):
    """Contrato de persistencia para los códigos de verificación."""

    @abstractmethod
    def save(self, code: VerificationCode) -> VerificationCode:
        """Persiste un código de verificación y devuelve la entidad guardada."""
        raise NotImplementedError

    @abstractmethod
    def find_active_by_user_and_purpose(
        self, user_id: UUID, purpose: CodePurpose
    ) -> VerificationCode | None:
        """Devuelve el código activo (no usado y no expirado) para un usuario y propósito."""
        raise NotImplementedError

    @abstractmethod
    def update(self, code: VerificationCode) -> VerificationCode:
        """Actualiza un código existente (p. ej. intentos o marca de uso)."""
        raise NotImplementedError

    @abstractmethod
    def invalidate_previous(self, user_id: UUID, purpose: CodePurpose) -> None:
        """Invalida los códigos anteriores del usuario para el propósito indicado."""
        raise NotImplementedError
