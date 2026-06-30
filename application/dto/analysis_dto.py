"""DTOs de análisis (estadísticas, datos de radar/barras/distribución).

Objetos de transferencia (Pydantic v2) que llevan los resultados del análisis a la
capa de presentación (tablas y gráficos Plotly.js).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.value_objects.demographic_filter import DemographicFilter

# Colores institucionales UTPL (orden: 4.1, 4.2, 4.3, 4.4).
UTPL_COLORS: list[str] = ["#003B71", "#F39C12", "#27AE60", "#E74C3C"]


class StatisticsRequest(BaseModel):
    """Entrada para el cálculo de estadísticas."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    competency_code: str | None = None
    filters: DemographicFilter | None = None


class SingleCompetencyStats(BaseModel):
    """Estadística descriptiva completa de una competencia."""

    competency_code: str
    competency_name: str
    mean: float
    median: float
    mode: float | None
    std_deviation: float
    variance: float
    skewness: float
    kurtosis: float
    min_value: float
    max_value: float
    count: int
    percentile_25: float
    percentile_50: float
    percentile_75: float


class StatisticsResult(BaseModel):
    """Resultado agregado de la estadística de las 4 competencias."""

    competencies: list[SingleCompetencyStats]
    overall_mean: float
    sample_size: int
    filters_applied: dict = Field(default_factory=dict)


class RadarData(BaseModel):
    """Datos para el gráfico radar (4 vértices = 4 competencias)."""

    labels: list[str]
    values: list[float]
    max_value: float = 8.0


class BarChartData(BaseModel):
    """Datos para el gráfico de barras (media por competencia)."""

    labels: list[str]
    values: list[float]
    colors: list[str] = Field(default_factory=lambda: list(UTPL_COLORS))


class DistributionData(BaseModel):
    """Datos para el histograma de distribución de una competencia."""

    competency_code: str
    competency_name: str
    bins: list[str]
    frequencies: list[int]
    mean_line: float
