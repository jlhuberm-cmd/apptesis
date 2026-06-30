"""Caso de uso: filtrado demográfico de respuestas.

Orquesta la construcción del filtro de dominio a partir del DTO de entrada, la
consulta paginada con filtros y el cálculo de los metadatos de página.
"""
from __future__ import annotations

import logging
import math

from application.dto.survey_dto import (
    PaginatedResponses,
    ResponseFilters,
    survey_response_to_dict,
)
from domain.ports.outbound.survey_repository import ISurveyRepository
from domain.value_objects.demographic_filter import DemographicFilter

logger = logging.getLogger(__name__)


class FilterResponsesUseCase:
    """Caso de uso de filtrado demográfico de respuestas."""

    def __init__(self, survey_repo: ISurveyRepository) -> None:
        self._survey_repo = survey_repo

    def execute(self, request: ResponseFilters) -> PaginatedResponses:
        """Devuelve una página de respuestas que cumplen los filtros demográficos."""
        page = max(1, request.page)
        page_size = max(1, request.page_size)
        offset = (page - 1) * page_size

        filters = DemographicFilter(
            age_range=request.age_range,
            gender=request.gender,
            province=request.province,
            education_level=request.education_level,
            sector=request.sector,
        )

        responses = self._survey_repo.find_by_filters(
            filters, limit=page_size, offset=offset
        )
        total = self._survey_repo.count_by_filters(filters)
        total_pages = math.ceil(total / page_size) if total else 0

        return PaginatedResponses(
            items=[survey_response_to_dict(r) for r in responses],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
