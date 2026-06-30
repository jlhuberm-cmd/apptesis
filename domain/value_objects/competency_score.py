"""Value object CompetencyScore: puntaje 1.0–8.0 con nivel y categoría DigComp.

Inmutable. Encapsula la validación de rango y la traducción de un puntaje a su
nivel y categoría según el marco DigComp 2.2.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_SCORE: float = 1.0
MAX_SCORE: float = 8.0

# Categoría DigComp por nivel (1–8).
_CATEGORY_BY_LEVEL: dict[int, str] = {
    1: "Básico",
    2: "Básico",
    3: "Intermedio",
    4: "Intermedio",
    5: "Avanzado",
    6: "Avanzado",
    7: "Altamente especializado",
    8: "Altamente especializado",
}


@dataclass(frozen=True)
class CompetencyScore:
    """Puntaje de competencia en la escala DigComp 2.2 (1.0–8.0).

    Lanza ValueError si el valor está fuera del rango [1.0, 8.0].

    Atributos:
        value: Puntaje en el rango [1.0, 8.0].
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

    @property
    def level(self) -> int:
        """Nivel entero (1–8) correspondiente al puntaje (redondeo al más cercano)."""
        return min(8, max(1, round(self.value)))

    def get_level_category(self) -> str:
        """Devuelve la categoría DigComp del puntaje.

        ("Básico", "Intermedio", "Avanzado" o "Altamente especializado").
        """
        return _CATEGORY_BY_LEVEL[self.level]

    def get_level_name(self) -> str:
        """Devuelve el nombre completo del nivel (categoría + número), p. ej. 'Intermedio 3'."""
        return f"{self.get_level_category()} {self.level}"

    @staticmethod
    def is_valid(value: float) -> bool:
        """Indica si un valor está dentro del rango válido sin construir el VO."""
        try:
            return MIN_SCORE <= float(value) <= MAX_SCORE
        except (TypeError, ValueError):
            return False

    def __str__(self) -> str:
        return f"{self.value} ({self.get_level_name()})"
