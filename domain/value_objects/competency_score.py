"""Puntaje de una competencia en la escala DigComp 2.2 (de 1 a 4).

Es un objeto de valor inmutable: guarda el puntaje, comprueba que caiga dentro
del rango permitido y sabe traducirlo al nivel de dominio que le corresponde.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_SCORE: float = 1.0
MAX_SCORE: float = 4.0

# Cortes de nivel. Son los mismos que aplica el motor de cálculo real
# (digcomp_scoring): por debajo de 2 es Básico, hasta 3 Intermedio, hasta 3.75
# Avanzado y de ahí en adelante Experto.
_BASICO_HASTA: float = 2.0
_INTERMEDIO_HASTA: float = 3.0
_AVANZADO_HASTA: float = 3.75

# Número de orden de cada nivel (1 el más bajo, 4 el más alto).
_ORDEN_NIVEL: dict[str, int] = {
    "Básico": 1,
    "Intermedio": 2,
    "Avanzado": 3,
    "Experto": 4,
}


@dataclass(frozen=True)
class CompetencyScore:
    """Puntaje de una competencia, entre 1.0 y 4.0.

    Si el valor se sale de ese rango, lanza ValueError.

    Atributos:
        value: Puntaje en el rango [1.0, 4.0].
    """

    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise ValueError("El puntaje debe ser numérico.")
        value = float(self.value)
        if not (MIN_SCORE <= value <= MAX_SCORE):
            raise ValueError(
                f"El puntaje {value} está fuera del rango válido "
                f"[{MIN_SCORE}, {MAX_SCORE}]."
            )
        object.__setattr__(self, "value", value)

    def get_level_category(self) -> str:
        """Devuelve el nivel del puntaje: Básico, Intermedio, Avanzado o Experto."""
        if self.value < _BASICO_HASTA:
            return "Básico"
        if self.value < _INTERMEDIO_HASTA:
            return "Intermedio"
        if self.value < _AVANZADO_HASTA:
            return "Avanzado"
        return "Experto"

    @property
    def level(self) -> int:
        """Número de orden del nivel: 1 (Básico) a 4 (Experto)."""
        return _ORDEN_NIVEL[self.get_level_category()]

    def get_level_name(self) -> str:
        """Nombre del nivel con su número, por ejemplo 'Avanzado 3'."""
        return f"{self.get_level_category()} {self.level}"

    @staticmethod
    def is_valid(value: float) -> bool:
        """Comprueba si un valor cae en el rango válido sin llegar a crear el objeto."""
        try:
            return MIN_SCORE <= float(value) <= MAX_SCORE
        except (TypeError, ValueError):
            return False

    def __str__(self) -> str:
        return f"{self.value} ({self.get_level_name()})"
