"""Reglas y constantes para el análisis de resultados.

Son funciones puras del dominio: no dependen de la base de datos ni de nada
externo, así que se pueden probar por separado.
"""
from __future__ import annotations

# El puntaje va de 1 a 4, la misma escala de autonomía que usa DigComp 2.2.
MIN_SCORE: float = 1.0
MAX_SCORE: float = 4.0

# Cuántas respuestas hacen falta como mínimo para que el análisis tenga sentido.
MIN_RESPONSES_FOR_ANALYSIS: int = 5

COMPETENCY_CODES: list[str] = ["4.1", "4.2", "4.3", "4.4"]

COMPETENCY_NAMES: dict[str, str] = {
    "4.1": "Protección de dispositivos",
    "4.2": "Protección de datos personales y privacidad",
    "4.3": "Protección de la salud y el bienestar",
    "4.4": "Protección del medio ambiente",
}

# Tope superior (no incluido) de cada nivel. Coinciden con los cortes del motor
# de cálculo: hasta 2 es Básico, hasta 3 Intermedio, hasta 3.75 Avanzado y a
# partir de ahí Experto.
_NIVELES: tuple[tuple[float, str], ...] = (
    (2.0, "Básico"),
    (3.0, "Intermedio"),
    (3.75, "Avanzado"),
)


def is_valid_score(score: float) -> bool:
    """Indica si un puntaje cae dentro del rango válido [1.0, 4.0]."""
    try:
        return MIN_SCORE <= float(score) <= MAX_SCORE
    except (TypeError, ValueError):
        return False


def get_level_for_score(score: float) -> str:
    """Devuelve el nivel de dominio que le corresponde a un puntaje.

    Lanza ValueError si el puntaje está fuera de rango.
    """
    if not is_valid_score(score):
        raise ValueError(
            f"El puntaje {score} está fuera del rango válido "
            f"[{MIN_SCORE}, {MAX_SCORE}]."
        )
    value = float(score)
    for tope, nivel in _NIVELES:
        if value < tope:
            return nivel
    return "Experto"


def has_sufficient_data(count: int) -> bool:
    """Indica si hay suficientes respuestas para hacer el análisis."""
    return count >= MIN_RESPONSES_FOR_ANALYSIS


def validate_competency_code(code: str) -> bool:
    """Indica si el código de competencia es uno de los válidos ('4.1'–'4.4')."""
    return code in COMPETENCY_CODES
