"""Puerto IUserRepository: persistencia de usuarios.

Puerto de salida (interfaz abstracta). El dominio define este contrato y la capa
de infraestructura lo implementa (p. ej. SupabaseUserRepository). El dominio NO
conoce la tecnología concreta de persistencia.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.user import User


class IUserRepository(ABC):
    """Contrato de persistencia para la entidad User."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Persiste un usuario nuevo y devuelve la entidad guardada."""
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, user_id: UUID) -> User | None:
        """Busca un usuario por su id. Devuelve None si no existe."""
        raise NotImplementedError

    @abstractmethod
    def find_by_email(self, email: str) -> User | None:
        """Busca un usuario por su email (normalizado). Devuelve None si no existe."""
        raise NotImplementedError

    @abstractmethod
    def update(self, user: User) -> User:
        """Actualiza un usuario existente y devuelve la entidad actualizada."""
        raise NotImplementedError

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Indica si ya existe un usuario con el email dado."""
        raise NotImplementedError
