"""Puerto IAnalysisService: contrato de cálculo estadístico y datos de gráficos.

Puerto de entrada. Los tipos de DTO (StatisticsResult, RadarData, BarChartData,
DistributionData) pertenecen a la capa de aplicación y se referencian solo en
anotaciones (TYPE_CHECKING) para no acoplar el dominio a la aplicación en runtime.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from domain.value_objects.demographic_filter import DemographicFilter

if TYPE_CHECKING:  # pragma: no cover - solo para anotaciones de tipo
    from application.dto.analysis_dto import (
        BarChartData,
        DistributionData,
        RadarData,
        StatisticsResult,
    )


class IAnalysisService(ABC):
    """Contrato de los casos de uso de análisis estadístico y visualización."""

    @abstractmethod
    def compute_descriptive_statistics(
        self, filters: DemographicFilter | None = None
    ) -> "StatisticsResult":
        """Calcula la estadística descriptiva de las 4 competencias."""
        raise NotImplementedError

    @abstractmethod
    def get_radar_chart_data(
        self, filters: DemographicFilter | None = None
    ) -> "RadarData":
        """Devuelve los datos para el gráfico radar (4 vértices = 4 competencias)."""
        raise NotImplementedError

    @abstractmethod
    def get_bar_chart_data(
        self, filters: DemographicFilter | None = None
    ) -> "BarChartData":
        """Devuelve los datos para el gráfico de barras (medias por competencia)."""
        raise NotImplementedError

    @abstractmethod
    def get_distribution_data(
        self, competency_code: str, filters: DemographicFilter | None = None
    ) -> "DistributionData":
        """Devuelve los datos de distribución de puntajes de una competencia."""
        raise NotImplementedError
