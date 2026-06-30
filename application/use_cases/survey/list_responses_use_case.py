"""Caso de uso: listado paginado de respuestas.

Orquesta la obtención de respuestas con paginación y el cálculo de los metadatos
de página.
"""
from __future__ import annotations

import logging
import math

from application.dto.survey_dto import PaginatedResponses, survey_response_to_dict
from domain.ports.outbound.survey_repository import ISurveyRepository

logger = logging.getLogger(__name__)


class ListResponsesUseCase:
    """Caso de uso de listado paginado de respuestas."""

    def __init__(self, survey_repo: ISurveyRepository) -> None:
        self._survey_repo = survey_repo

    def execute(self, page: int = 1, page_size: int = 20) -> PaginatedResponses:
        """Devuelve una página de respuestas (sin filtros)."""
        page = max(1, page)
        page_size = max(1, page_size)
        offset = (page - 1) * page_size

        responses = self._survey_repo.find_all(limit=page_size, offset=offset)
        total = self._survey_repo.count_all()
        total_pages = math.ceil(total / page_size) if total else 0

        return PaginatedResponses(
            items=[survey_response_to_dict(r) for r in responses],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
