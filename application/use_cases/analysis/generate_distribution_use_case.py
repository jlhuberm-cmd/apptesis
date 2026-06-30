"""Caso de uso: datos para gráfico de distribución.

Obtiene los puntajes de una competencia, calcula la distribución de frecuencias y
arma los datos del histograma (incluida la línea de la media).
"""
from __future__ import annotations

import logging

from application.dto.analysis_dto import DistributionData
from domain.exceptions.analysis_exceptions import InvalidCompetencyCodeError
from domain.ports.outbound.survey_repository import ISurveyRepository
from domain.rules.analysis_rules import COMPETENCY_NAMES, validate_competency_code
from domain.services import statistics
from domain.value_objects.demographic_filter import DemographicFilter

logger = logging.getLogger(__name__)


class GenerateDistributionUseCase:
    """Caso de uso de datos para el gráfico de distribución."""

    def __init__(self, survey_repo: ISurveyRepository) -> None:
        self._survey_repo = survey_repo

    def execute(
        self, competency_code: str, filters: DemographicFilter | None = None
    ) -> DistributionData:
        """Devuelve la distribución de frecuencias de una competencia."""
        if not validate_competency_code(competency_code):
            raise InvalidCompetencyCodeError(competency_code)

        scores = self._survey_repo.get_all_scores(competency_code, filters)
        distribution = statistics.calculate_frequency_distribution(scores, bins=8)

        return DistributionData(
            competency_code=competency_code,
            competency_name=COMPETENCY_NAMES[competency_code],
            bins=list(distribution.keys()),
            frequencies=list(distribution.values()),
            mean_line=round(statistics.calculate_mean(scores), 2),
        )
