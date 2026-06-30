"""Caso de uso: datos para gráfico radar (4 vértices).

Calcula la media de cada competencia y arma los datos del gráfico radar.
Los vértices se etiquetan con el código de competencia (4.1–4.4).
"""
from __future__ import annotations

import logging

from application.dto.analysis_dto import RadarData
from domain.ports.outbound.survey_repository import ISurveyRepository
from domain.rules.analysis_rules import COMPETENCY_CODES, MAX_SCORE
from domain.services import statistics
from domain.value_objects.demographic_filter import DemographicFilter

logger = logging.getLogger(__name__)


class GenerateRadarChartUseCase:
    """Caso de uso de datos para el gráfico radar."""

    def __init__(self, survey_repo: ISurveyRepository) -> None:
        self._survey_repo = survey_repo

    def execute(self, filters: DemographicFilter | None = None) -> RadarData:
        """Devuelve las medias por competencia para el gráfico radar."""
        labels: list[str] = []
        values: list[float] = []
        for code in COMPETENCY_CODES:
            scores = self._survey_repo.get_all_scores(code, filters)
            labels.append(code)
            values.append(round(statistics.calculate_mean(scores), 2))
        return RadarData(labels=labels, values=values, max_value=MAX_SCORE)
