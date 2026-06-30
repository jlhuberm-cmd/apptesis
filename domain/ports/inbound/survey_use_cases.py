"""Puerto ISurveyService: contrato de carga y consulta de respuestas de encuesta.

Puerto de entrada. Los tipos de DTO (UploadResult, PaginatedResponses) pertenecen
a la capa de aplicación y se referencian solo en anotaciones (TYPE_CHECKING) para
no acoplar el dominio a la aplicación en tiempo de ejecución.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from domain.value_objects.demographic_filter import DemographicFilter

if TYPE_CHECKING:  # pragma: no cover - solo para anotaciones de tipo
    from application.dto.survey_dto import PaginatedResponses, UploadResult


class ISurveyService(ABC):
    """Contrato de los casos de uso de encuestas."""

    @abstractmethod
    def upload_csv(self, file_content: bytes, uploaded_by: UUID) -> "UploadResult":
        """Procesa un CSV de ArcGIS Survey123 y persiste las respuestas válidas."""
        raise NotImplementedError

    @abstractmethod
    def list_responses(self, page: int, page_size: int) -> "PaginatedResponses":
        """Devuelve las respuestas paginadas (sin filtros)."""
        raise NotImplementedError

    @abstractmethod
    def filter_responses(
        self, filters: DemographicFilter, page: int, page_size: int
    ) -> "PaginatedResponses":
        """Devuelve las respuestas paginadas aplicando filtros demográficos."""
        raise NotImplementedError

    @abstractmethod
    def get_filter_options(self) -> dict[str, list[str]]:
        """Devuelve los valores disponibles por campo demográfico para los filtros."""
        raise NotImplementedError
