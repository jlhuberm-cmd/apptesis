"""Excepciones del dominio de análisis.

Heredan de DomainError → AnalysisError con mensajes descriptivos en español.
"""
from __future__ import annotations

from domain.exceptions.auth_exceptions import DomainError


class AnalysisError(DomainError):
    """Excepción base de los errores de análisis."""


class InvalidScoreRangeError(AnalysisError):
    """Un puntaje está fuera del rango válido [1.0, 8.0]."""

    def __init__(self, score: float) -> None:
        self.score = score
        super().__init__(
            f"El puntaje {score} está fuera del rango válido [1.0, 8.0]."
        )


class InsufficientDataError(AnalysisError):
    """No hay suficientes respuestas para realizar el análisis."""

    def __init__(self, count: int, minimum: int) -> None:
        self.count = count
        self.minimum = minimum
        super().__init__(
            f"Datos insuficientes para el análisis: se requieren al menos {minimum} "
            f"respuestas y solo hay {count}."
        )


class InvalidCompetencyCodeError(AnalysisError):
    """El código de competencia no es válido ('4.1'–'4.4')."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(
            f"Código de competencia inválido: '{code}'. "
            "Los válidos son: 4.1, 4.2, 4.3, 4.4."
        )
