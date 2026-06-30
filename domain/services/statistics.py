"""Servicio de estadística descriptiva con funciones puras.

IMPORTANTE: este módulo usa ÚNICAMENTE la librería estándar (math y statistics).
NO importa pandas ni numpy. Todas las funciones son puras (sin efectos secundarios)
y manejan los casos límite (lista vacía, un solo elemento, varianza nula).

Convenciones:
- Varianza y desviación estándar: muestrales (n-1). Con n < 2 devuelven 0.0.
- Asimetría y curtosis: coeficientes de Fisher basados en momentos poblacionales.
  La curtosis es el "exceso" (curtosis normal = 0). Con n < 2 o varianza nula
  devuelven 0.0.
"""
from __future__ import annotations

import math
import statistics
from collections import Counter


def calculate_count(values: list[float]) -> int:
    """Número de observaciones."""
    return len(values)


def calculate_mean(values: list[float]) -> float:
    """Media aritmética. Devuelve 0.0 si la lista está vacía."""
    if not values:
        return 0.0
    return statistics.fmean(values)


def calculate_median(values: list[float]) -> float:
    """Mediana. Devuelve 0.0 si la lista está vacía."""
    if not values:
        return 0.0
    return float(statistics.median(values))


def calculate_mode(values: list[float]) -> float | None:
    """Moda (valor más frecuente).

    Devuelve None si la lista está vacía o si todos los valores son distintos
    (no hay repeticiones). Ante empate, devuelve el menor de los valores modales.
    """
    if not values:
        return None
    counts = Counter(values)
    max_freq = max(counts.values())
    if max_freq == 1 and len(values) > 1:
        return None
    modal_values = [value for value, freq in counts.items() if freq == max_freq]
    return float(min(modal_values))


def calculate_variance(values: list[float]) -> float:
    """Varianza muestral (n-1). Devuelve 0.0 con menos de 2 observaciones."""
    if len(values) < 2:
        return 0.0
    return float(statistics.variance(values))


def calculate_std_deviation(values: list[float]) -> float:
    """Desviación estándar muestral (n-1). Devuelve 0.0 con menos de 2 observaciones."""
    if len(values) < 2:
        return 0.0
    return float(statistics.stdev(values))


def _central_moment(values: list[float], order: int, mean: float) -> float:
    """Momento central poblacional de orden `order`: (1/n) * Σ (x - media)^order."""
    n = len(values)
    return sum((x - mean) ** order for x in values) / n


def calculate_skewness(values: list[float]) -> float:
    """Asimetría de Fisher (coeficiente de asimetría g1).

    g1 = m3 / m2^(3/2), con m2 y m3 momentos centrales poblacionales.
    Devuelve 0.0 si n < 2 o la varianza es nula.
    """
    n = len(values)
    if n < 2:
        return 0.0
    mean = calculate_mean(values)
    m2 = _central_moment(values, 2, mean)
    if m2 == 0:
        return 0.0
    m3 = _central_moment(values, 3, mean)
    return m3 / (m2 ** 1.5)


def calculate_kurtosis(values: list[float]) -> float:
    """Curtosis de Fisher (exceso de curtosis g2).

    g2 = m4 / m2^2 - 3, con m2 y m4 momentos centrales poblacionales.
    Una distribución normal tiene exceso de curtosis 0.
    Devuelve 0.0 si n < 2 o la varianza es nula.
    """
    n = len(values)
    if n < 2:
        return 0.0
    mean = calculate_mean(values)
    m2 = _central_moment(values, 2, mean)
    if m2 == 0:
        return 0.0
    m4 = _central_moment(values, 4, mean)
    return (m4 / (m2 ** 2)) - 3.0


def calculate_percentiles(
    values: list[float], percentiles: list[int] | None = None
) -> dict[int, float]:
    """Percentiles por interpolación lineal (método tipo numpy 'linear').

    Args:
        values: Observaciones.
        percentiles: Lista de percentiles a calcular (por defecto [25, 50, 75]).

    Returns:
        Diccionario {percentil: valor}. Con lista vacía, todos los valores son 0.0.
    """
    if percentiles is None:
        percentiles = [25, 50, 75]
    if not values:
        return {p: 0.0 for p in percentiles}

    ordered = sorted(values)
    n = len(ordered)
    result: dict[int, float] = {}
    for p in percentiles:
        if n == 1:
            result[p] = float(ordered[0])
            continue
        rank = (p / 100) * (n - 1)
        lower = math.floor(rank)
        upper = math.ceil(rank)
        if lower == upper:
            result[p] = float(ordered[lower])
        else:
            frac = rank - lower
            result[p] = float(ordered[lower] + frac * (ordered[upper] - ordered[lower]))
    return result


def calculate_min_max(values: list[float]) -> tuple[float, float]:
    """Mínimo y máximo. Devuelve (0.0, 0.0) si la lista está vacía."""
    if not values:
        return (0.0, 0.0)
    return (float(min(values)), float(max(values)))


def calculate_frequency_distribution(
    values: list[float], bins: int = 8
) -> dict[str, int]:
    """Distribución de frecuencias en `bins` intervalos de igual ancho.

    Construye `bins` intervalos sobre el rango [min, max] y cuenta cuántos valores
    caen en cada uno (el último intervalo incluye el máximo). Las etiquetas tienen
    el formato "min-max" con dos decimales.

    Casos límite:
        - Lista vacía: devuelve un diccionario vacío.
        - Todos los valores iguales (min == max): un único intervalo con todos.
    """
    if not values:
        return {}
    if bins < 1:
        bins = 1

    low, high = min(values), max(values)
    if low == high:
        return {f"{low:.2f}-{high:.2f}": len(values)}

    width = (high - low) / bins
    edges = [low + i * width for i in range(bins + 1)]
    edges[-1] = high  # evita errores de redondeo en el borde superior

    distribution: dict[str, int] = {}
    counts = [0] * bins
    for x in values:
        if x >= high:
            idx = bins - 1
        else:
            idx = int((x - low) / width)
            idx = min(idx, bins - 1)
        counts[idx] += 1

    for i in range(bins):
        label = f"{edges[i]:.2f}-{edges[i + 1]:.2f}"
        distribution[label] = counts[i]
    return distribution


def calculate_all_descriptive_stats(values: list[float]) -> dict[str, float | int | None]:
    """Calcula todas las estadísticas descriptivas en un solo diccionario.

    Claves: count, mean, median, mode, variance, std_deviation, skewness,
    kurtosis, min, max, percentile_25, percentile_50, percentile_75.
    """
    percentiles = calculate_percentiles(values, [25, 50, 75])
    minimum, maximum = calculate_min_max(values)
    return {
        "count": calculate_count(values),
        "mean": calculate_mean(values),
        "median": calculate_median(values),
        "mode": calculate_mode(values),
        "variance": calculate_variance(values),
        "std_deviation": calculate_std_deviation(values),
        "skewness": calculate_skewness(values),
        "kurtosis": calculate_kurtosis(values),
        "min": minimum,
        "max": maximum,
        "percentile_25": percentiles[25],
        "percentile_50": percentiles[50],
        "percentile_75": percentiles[75],
    }
