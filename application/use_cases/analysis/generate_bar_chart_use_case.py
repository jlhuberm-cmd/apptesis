"""Caso de uso: datos para gráfico de barras.

Calcula la media de cada competencia y arma los datos del gráfico de barras con
los colores institucionales UTPL. Las barras se etiquetan con el nombre de la
competencia.
"""
from __future__ import annotations

import logging

from application.dto.analysis_dto import UTPL_COLORS, BarChartData
from domain.ports.outbound.survey_repository import ISurveyRepository
from domain.rules.analysis_rules import COMPETENCY_CODES, COMPETENCY_NAMES
from domain.services import statistics
from domain.value_objects.demographic_filter import DemographicFilter

logger = logging.getLogger(__name__)


class GenerateBarChartUseCase:
    """Caso de uso de datos para el gráfico de barras."""

    def __init__(self, survey_repo: ISurveyRepository) -> None:
        self._survey_repo = survey_repo

    def execute(self, filters: DemographicFilter | None = None) -> BarChartData:
        """Devuelve las medias por competencia para el gráfico de barras."""
        labels: list[str] = []
        values: list[float] = []
        for code in COMPETENCY_CODES:
            scores = self._survey_repo.get_all_scores(code, filters)
            labels.append(COMPETENCY_NAMES[code])
            values.append(round(statistics.calculate_mean(scores), 2))
        return BarChartData(labels=labels, values=values, colors=list(UTPL_COLORS))
