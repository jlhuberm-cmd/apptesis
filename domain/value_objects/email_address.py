"""Value object EmailAddress: validación y normalización de email.

Inmutable. Encapsula la validación de formato (regex, sin librerías externas) y
la normalización (minúsculas + strip) de una dirección de correo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Patrón de validación de email (suficientemente estricto para el dominio).
_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


@dataclass(frozen=True)
class EmailAddress:
    """Dirección de correo electrónico validada y normalizada.

    El valor se normaliza (strip + minúsculas) y se valida en la construcción.
    Lanza ValueError si el formato es inválido.

    Atributos:
        value: Email normalizado.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not normalized:
            raise ValueError("El email no puede estar vacío.")
        if not _EMAIL_PATTERN.match(normalized):
            raise ValueError(f"Formato de email inválido: '{self.value}'.")
        # En un dataclass frozen, los atributos se asignan vía object.__setattr__.
        object.__setattr__(self, "value", normalized)

    @property
    def domain(self) -> str:
        """Parte del dominio del email (después de la @)."""
        return self.value.split("@", 1)[1]

    @property
    def local_part(self) -> str:
        """Parte local del email (antes de la @)."""
        return self.value.split("@", 1)[0]

    @staticmethod
    def is_valid(value: str) -> bool:
        """Indica si una cadena tiene formato de email válido (sin construir el VO)."""
        normalized = value.strip().lower()
        return bool(normalized) and bool(_EMAIL_PATTERN.match(normalized))

    def __str__(self) -> str:
        return self.value
