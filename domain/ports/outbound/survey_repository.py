"""Puerto ISurveyRepository: persistencia y consulta de respuestas de encuesta.

Puerto de salida. Define cómo el dominio guarda y consulta respuestas, incluyendo
filtrado demográfico y extracción de puntajes para el análisis estadístico.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.survey_response import SurveyResponse
from domain.value_objects.demographic_filter import DemographicFilter


class ISurveyRepository(ABC):
    """Contrato de persistencia y consulta para las respuestas de encuesta."""

    @abstractmethod
    def save_batch(self, responses: list[SurveyResponse]) -> int:
        """Guarda un lote de respuestas y devuelve la cantidad efectivamente guardada."""
        raise NotImplementedError

    @abstractmethod
    def find_all(self, limit: int, offset: int) -> list[SurveyResponse]:
        """Devuelve respuestas paginadas (sin filtros)."""
        raise NotImplementedError

    @abstractmethod
    def find_by_filters(
        self, filters: DemographicFilter, limit: int, offset: int
    ) -> list[SurveyResponse]:
        """Devuelve respuestas que cumplen los filtros demográficos, paginadas."""
        raise NotImplementedError

    @abstractmethod
    def count_all(self) -> int:
        """Devuelve el total de respuestas almacenadas."""
        raise NotImplementedError

    @abstractmethod
    def count_by_filters(self, filters: DemographicFilter) -> int:
        """Devuelve el total de respuestas que cumplen los filtros demográficos."""
        raise NotImplementedError

    @abstractmethod
    def get_all_scores(
        self, competency_code: str, filters: DemographicFilter | None = None
    ) -> list[float]:
        """Devuelve todos los puntajes de una competencia (ej. '4.1'), opcionalmente filtrados."""
        raise NotImplementedError

    @abstractmethod
    def get_unique_values(self, field_name: str) -> list[str]:
        """Devuelve los valores distintos de un campo demográfico (para poblar dropdowns)."""
        raise NotImplementedError
