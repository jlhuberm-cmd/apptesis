"""Caso de uso: cálculo de estadística descriptiva por competencia.

Orquesta la obtención de puntajes por competencia y el cálculo de toda la
estadística descriptiva mediante el servicio de dominio `statistics`.
"""
from __future__ import annotations

import logging

from application.dto.analysis_dto import SingleCompetencyStats, StatisticsResult
from domain.exceptions.analysis_exceptions import InsufficientDataError
from domain.ports.outbound.survey_repository import ISurveyRepository
from domain.rules.analysis_rules import (
    COMPETENCY_CODES,
    COMPETENCY_NAMES,
    MIN_RESPONSES_FOR_ANALYSIS,
    has_sufficient_data,
)
from domain.services import statistics
from domain.value_objects.demographic_filter import DemographicFilter

logger = logging.getLogger(__name__)


class ComputeStatisticsUseCase:
    """Caso de uso de cálculo de estadística descriptiva."""

    def __init__(self, survey_repo: ISurveyRepository) -> None:
        self._survey_repo = survey_repo

    def execute(self, filters: DemographicFilter | None = None) -> StatisticsResult:
        """Calcula la estadística descriptiva de las 4 competencias del Área 4."""
        competencies: list[SingleCompetencyStats] = []
        means: list[float] = []
        sample_size = 0

        for code in COMPETENCY_CODES:
            scores = self._survey_repo.get_all_scores(code, filters)
            sample_size = max(sample_size, len(scores))

            stats = statistics.calculate_all_descriptive_stats(scores)
            competencies.append(
                SingleCompetencyStats(
                    competency_code=code,
                    competency_name=COMPETENCY_NAMES[code],
                    mean=stats["mean"],
                    median=stats["median"],
                    mode=stats["mode"],
                    std_deviation=stats["std_deviation"],
                    variance=stats["variance"],
                    skewness=stats["skewness"],
                    kurtosis=stats["kurtosis"],
                    min_value=stats["min"],
                    max_value=stats["max"],
                    count=stats["count"],
                    percentile_25=stats["percentile_25"],
                    percentile_50=stats["percentile_50"],
                    percentile_75=stats["percentile_75"],
                )
            )
            means.append(stats["mean"])

        if not has_sufficient_data(sample_size):
            raise InsufficientDataError(sample_size, MIN_RESPONSES_FOR_ANALYSIS)

        overall_mean = round(sum(means) / len(means), 4) if means else 0.0
        logger.info("Estadísticas calculadas para %d respuestas.", sample_size)
        return StatisticsResult(
            competencies=competencies,
            overall_mean=overall_mean,
            sample_size=sample_size,
            filters_applied=filters.to_dict() if filters else {},
        )
