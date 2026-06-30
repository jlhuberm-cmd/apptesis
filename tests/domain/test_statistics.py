"""Tests del servicio de estadística descriptiva."""
import math

import pytest

from domain.services import statistics as st


def test_mean():
    assert st.calculate_mean([1, 2, 3, 4, 5]) == 3.0
    assert st.calculate_mean([]) == 0.0


def test_median_par_e_impar():
    assert st.calculate_median([1, 2, 3, 4, 5]) == 3.0
    assert st.calculate_median([1, 2, 3, 4]) == 2.5
    assert st.calculate_median([]) == 0.0


def test_mode():
    assert st.calculate_mode([1, 2, 2, 3]) == 2.0
    assert st.calculate_mode([1, 2, 3]) is None  # todos distintos
    assert st.calculate_mode([]) is None


def test_variance_y_std_muestrales():
    assert st.calculate_variance([1, 2, 3, 4, 5]) == pytest.approx(2.5)
    assert st.calculate_std_deviation([1, 2, 3, 4, 5]) == pytest.approx(math.sqrt(2.5))
    # menos de 2 observaciones -> 0
    assert st.calculate_variance([5]) == 0.0
    assert st.calculate_std_deviation([]) == 0.0


def test_skewness():
    assert st.calculate_skewness([1, 2, 3, 4, 5]) == pytest.approx(0.0)
    assert st.calculate_skewness([1, 1, 1, 2, 5]) > 1.0  # asimetría positiva
    assert st.calculate_skewness([5]) == 0.0


def test_kurtosis_exceso_fisher():
    assert st.calculate_kurtosis([1, 2, 3, 4, 5]) == pytest.approx(-1.3)
    assert st.calculate_kurtosis([5]) == 0.0


def test_percentiles_interpolacion_lineal():
    p = st.calculate_percentiles([1, 2, 3, 4])
    assert p[25] == pytest.approx(1.75)
    assert p[50] == pytest.approx(2.5)
    assert p[75] == pytest.approx(3.25)
    assert st.calculate_percentiles([])[50] == 0.0
    assert st.calculate_percentiles([5])[50] == 5.0


def test_min_max():
    assert st.calculate_min_max([3, 1, 8, 5]) == (1.0, 8.0)
    assert st.calculate_min_max([]) == (0.0, 0.0)


def test_frequency_distribution():
    fd = st.calculate_frequency_distribution([1, 2, 3, 4, 5, 6, 7, 8], bins=8)
    assert sum(fd.values()) == 8
    assert len(fd) == 8
    assert st.calculate_frequency_distribution([3, 3, 3]) == {"3.00-3.00": 3}
    assert st.calculate_frequency_distribution([]) == {}


def test_all_descriptive_stats():
    stats = st.calculate_all_descriptive_stats([1, 2, 3, 4, 5])
    assert stats["count"] == 5
    assert stats["mean"] == pytest.approx(3.0)
    assert set(stats.keys()) == {
        "count", "mean", "median", "mode", "variance", "std_deviation",
        "skewness", "kurtosis", "min", "max",
        "percentile_25", "percentile_50", "percentile_75",
    }


def test_sin_numpy_ni_pandas():
    import inspect
    src = inspect.getsource(st)
    assert "import numpy" not in src
    assert "import pandas" not in src
