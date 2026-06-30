"""Reglas y constantes de análisis (rangos de score, niveles, datos mínimos).

Funciones puras del dominio. No dependen de infraestructura.
"""
from __future__ import annotations

# --- Constantes de análisis ---
MIN_SCORE: float = 1.0
MAX_SCORE: float = 8.0
MIN_RESPONSES_FOR_ANALYSIS: int = 5

COMPETENCY_CODES: list[str] = ["4.1", "4.2", "4.3", "4.4"]

COMPETENCY_NAMES: dict[str, str] = {
    "4.1": "Protección de dispositivos",
    "4.2": "Protección de datos personales y privacidad",
    "4.3": "Protección de la salud y el bienestar",
    "4.4": "Protección del medio ambiente",
}

# Rangos (inclusivos) de puntaje por categoría DigComp 2.2.
LEVEL_RANGES: dict[str, tuple[float, float]] = {
    "Básico": (1.0, 2.0),
    "Intermedio": (3.0, 4.0),
    "Avanzado": (5.0, 6.0),
    "Altamente especializado": (7.0, 8.0),
}


def is_valid_score(score: float) -> bool:
    """Indica si un puntaje está dentro del rango válido [1.0, 8.0]."""
    try:
        return MIN_SCORE <= float(score) <= MAX_SCORE
    except (TypeError, ValueError):
        return False


def get_level_for_score(score: float) -> str:
    """Devuelve la categoría DigComp correspondiente a un puntaje.

    El puntaje se redondea al nivel entero más cercano (1–8) y se mapea a su
    categoría. Lanza ValueError si el puntaje está fuera de rango.
    """
    if not is_valid_score(score):
        raise ValueError(
            f"El puntaje {score} está fuera del rango válido "
            f"[{MIN_SCORE}, {MAX_SCORE}]."
        )
    level = min(8, max(1, round(float(score))))
    for category, (low, high) in LEVEL_RANGES.items():
        if low <= level <= high:
            return category
    # Inalcanzable: todos los niveles 1–8 están cubiertos por LEVEL_RANGES.
    raise ValueError(f"No se encontró categoría para el nivel {level}.")


def has_sufficient_data(count: int) -> bool:
    """Indica si hay suficientes respuestas para realizar el análisis."""
    return count >= MIN_RESPONSES_FOR_ANALYSIS


def validate_competency_code(code: str) -> bool:
    """Indica si un código de competencia es válido ('4.1'–'4.4')."""
    return code in COMPETENCY_CODES
