"""Tests del caso de uso de cálculo de estadísticas."""
from uuid import uuid4

import pytest

from application.use_cases.analysis.compute_statistics_use_case import (
    ComputeStatisticsUseCase,
)
from domain.entities.survey_response import SurveyResponse
from domain.exceptions.analysis_exceptions import InsufficientDataError
from domain.ports.outbound.survey_repository import ISurveyRepository
from domain.value_objects.demographic_filter import DemographicFilter


class InMemorySurveyRepo(ISurveyRepository):
    def __init__(self): self._data = []
    def save_batch(self, responses): self._data.extend(responses); return len(responses)
    def _match(self, r, f):
        mapping = {
            "respondent_gender": r.respondent_gender,
            "respondent_age_range": r.respondent_age_range,
            "respondent_province": r.respondent_province,
            "respondent_education_level": r.respondent_education_level,
            "respondent_sector": r.respondent_sector,
        }
        return all(mapping[k] == v for k, v in f.to_dict().items())
    def find_all(self, limit, offset): return self._data[offset:offset + limit]
    def find_by_filters(self, f, limit, offset):
        return [r for r in self._data if self._match(r, f)][offset:offset + limit]
    def count_all(self): return len(self._data)
    def count_by_filters(self, f): return len([r for r in self._data if self._match(r, f)])
    def get_all_scores(self, code, f=None):
        data = self._data if not f else [r for r in self._data if self._match(r, f)]
        return [r.get_scores_dict()[code] for r in data]
    def get_unique_values(self, field):
        return sorted({getattr(r, field) for r in self._data if getattr(r, field)})


def _make_repo(n, gender_alt=True):
    repo = InMemorySurveyRepo()
    batch = uuid4()
    rows = []
    for i in range(n):
        rows.append(SurveyResponse(
            uploaded_by=uuid4(), upload_batch_id=batch,
            respondent_gender=("Femenino" if i % 2 == 0 else "Masculino") if gender_alt else "Femenino",
            comp_4_1_score=float((i % 4) + 1), comp_4_2_score=2.0,
            comp_4_3_score=3.0, comp_4_4_score=4.0,
        ))
    repo.save_batch(rows)
    return repo


def test_estadisticas_4_competencias():
    uc = ComputeStatisticsUseCase(_make_repo(10))
    result = uc.execute()
    assert len(result.competencies) == 4
    assert result.sample_size == 10
    c42 = next(c for c in result.competencies if c.competency_code == "4.2")
    assert c42.mean == pytest.approx(2.0)
    assert c42.variance == pytest.approx(0.0)
    assert c42.competency_name == "Protección de datos personales y privacidad"


def test_overall_mean_es_promedio_de_medias():
    uc = ComputeStatisticsUseCase(_make_repo(10))
    result = uc.execute()
    c41 = next(c for c in result.competencies if c.competency_code == "4.1")
    esperado = round((c41.mean + 2.0 + 3.0 + 4.0) / 4, 4)
    assert result.overall_mean == pytest.approx(esperado)


def test_filtros_reducen_muestra():
    uc = ComputeStatisticsUseCase(_make_repo(10))
    result = uc.execute(DemographicFilter(gender="Femenino"))
    assert result.sample_size == 5
    assert result.filters_applied == {"respondent_gender": "Femenino"}


def test_datos_insuficientes():
    uc = ComputeStatisticsUseCase(_make_repo(3))
    with pytest.raises(InsufficientDataError) as exc:
        uc.execute()
    assert exc.value.count == 3
    assert exc.value.minimum == 5
