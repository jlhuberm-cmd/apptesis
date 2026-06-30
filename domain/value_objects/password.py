"""Value object Password: reglas de complejidad de contraseña.

Valida una contraseña en texto plano ANTES de hashearla. El valor se mantiene
solo de forma transitoria para validar y NUNCA se expone en repr ni se persiste;
para almacenar la contraseña debe hashearse con un IPasswordHasher.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Reglas de complejidad.
MIN_LENGTH: int = 8
# Conjunto de caracteres especiales aceptados.
SPECIAL_CHARS: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"


@dataclass(frozen=True)
class Password:
    """Contraseña en texto plano sujeta a validación de complejidad.

    Reglas:
        * Mínimo 8 caracteres.
        * Al menos 1 mayúscula.
        * Al menos 1 minúscula.
        * Al menos 1 número.
        * Al menos 1 carácter especial.

    El valor se excluye de la representación (repr=False) para evitar fugas en logs.
    """

    # repr=False: el valor no aparece en repr() ni en trazas.
    value: str = field(repr=False)

    def validate(self) -> list[str]:
        """Devuelve la lista de errores de complejidad (vacía si es válida)."""
        return self._evaluate(self.value)

    def is_valid(self) -> bool:
        """Indica si la contraseña cumple todas las reglas de complejidad."""
        return not self._evaluate(self.value)

    @classmethod
    def check(cls, raw: str) -> list[str]:
        """Valida una contraseña sin construir una instancia (uso sin estado)."""
        return cls._evaluate(raw)

    @staticmethod
    def _evaluate(raw: str) -> list[str]:
        """Evalúa las reglas de complejidad sobre una contraseña en texto plano."""
        errors: list[str] = []
        if len(raw) < MIN_LENGTH:
            errors.append(f"Debe tener al menos {MIN_LENGTH} caracteres.")
        if not any(c.isupper() for c in raw):
            errors.append("Debe contener al menos una letra mayúscula.")
        if not any(c.islower() for c in raw):
            errors.append("Debe contener al menos una letra minúscula.")
        if not any(c.isdigit() for c in raw):
            errors.append("Debe contener al menos un número.")
        if not any(c in SPECIAL_CHARS for c in raw):
            errors.append("Debe contener al menos un carácter especial.")
        return errors

    def __str__(self) -> str:
        # Nunca revelar la contraseña.
        return "********"
