# -*- coding: utf-8 -*-
"""Servidor de DEMOSTRACIÓN de AppTesis.

Levanta la app real con datos de ejemplo en memoria y un usuario autenticado de
demostración, para mostrar el dashboard y los gráficos sin necesidad de Supabase.
NO es para producción: solo para previsualización visual.
"""
import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "demo")
os.environ.setdefault("SUPABASE_URL", "https://demo.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "demo")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "demo")
os.environ.setdefault("SMTP_HOST", "smtp.demo")
os.environ.setdefault("SMTP_USER", "demo")
os.environ.setdefault("SMTP_PASSWORD", "demo")
os.environ.setdefault("SMTP_FROM_EMAIL", "demo@utpl.edu.ec")
os.environ.setdefault("SESSION_SECRET_KEY", "demo-session")

import config.dependencies as deps
deps.get_supabase_client = lambda: object()

import main
from api.middleware.auth_middleware import require_auth
from config.dependencies import (
    get_compute_statistics_use_case, get_radar_chart_use_case, get_bar_chart_use_case,
    get_distribution_use_case, get_survey_repository, get_list_responses_use_case,
)
from application.use_cases.analysis.compute_statistics_use_case import ComputeStatisticsUseCase
from application.use_cases.analysis.generate_radar_chart_use_case import GenerateRadarChartUseCase
from application.use_cases.analysis.generate_bar_chart_use_case import GenerateBarChartUseCase
from application.use_cases.analysis.generate_distribution_use_case import GenerateDistributionUseCase
from application.use_cases.survey.list_responses_use_case import ListResponsesUseCase
from domain.entities.survey_response import SurveyResponse
from domain.entities.user import User, UserRole, AccountStatus
from domain.ports.outbound.survey_repository import ISurveyRepository


class InMemSurveyRepo(ISurveyRepository):
    def __init__(self): self.d = []
    def save_batch(self, rs): self.d.extend(rs); return len(rs)
    def _match(self, r, f):
        m = {"respondent_gender": r.respondent_gender, "respondent_age_range": r.respondent_age_range,
             "respondent_province": r.respondent_province, "respondent_education_level": r.respondent_education_level,
             "respondent_sector": r.respondent_sector}
        return all(m[k] == v for k, v in f.to_dict().items())
    def find_all(self, limit, offset): return self.d[offset:offset+limit]
    def find_by_filters(self, f, limit, offset):
        return [r for r in self.d if self._match(r, f)][offset:offset+limit]
    def count_all(self): return len(self.d)
    def count_by_filters(self, f): return len([r for r in self.d if self._match(r, f)])
    def get_all_scores(self, code, f=None):
        data = self.d if not f else [r for r in self.d if self._match(r, f)]
        return [r.get_scores_dict()[code] for r in data]
    def get_unique_values(self, field):
        return sorted({getattr(r, field) for r in self.d if getattr(r, field)})


def _seed(n=40):
    repo = InMemSurveyRepo()
    batch = uuid4()
    genders = ["Femenino", "Masculino", "Otro"]
    ages = ["18-25", "26-35", "36-45", "46-55", "56-65"]
    provinces = ["Loja", "Pichincha", "Guayas", "Azuay"]
    educ = ["Bachillerato", "Superior", "Posgrado"]
    sectors = ["Urbano", "Rural"]
    rows = []
    for i in range(n):
        rows.append(SurveyResponse(
            uploaded_by=uuid4(), upload_batch_id=batch,
            respondent_gender=genders[i % 3], respondent_age_range=ages[i % 5],
            respondent_province=provinces[i % 4], respondent_education_level=educ[i % 3],
            respondent_sector=sectors[i % 2],
            comp_4_1_score=float(1 + (i * 3) % 8),
            comp_4_2_score=float(3 + (i % 5)),
            comp_4_3_score=float(1 + (i * 5) % 8),
            comp_4_4_score=float(2 + (i % 6)),
        ))
    repo.save_batch(rows)
    return repo


repo = _seed(40)
demo_user = User(email="demo@utpl.edu.ec", hashed_password="x", full_name="Investigador Demo",
                 role=UserRole.ADMIN, status=AccountStatus.ACTIVE)

app = main.app
app.dependency_overrides[require_auth] = lambda: demo_user
app.dependency_overrides[get_survey_repository] = lambda: repo
app.dependency_overrides[get_compute_statistics_use_case] = lambda: ComputeStatisticsUseCase(repo)
app.dependency_overrides[get_radar_chart_use_case] = lambda: GenerateRadarChartUseCase(repo)
app.dependency_overrides[get_bar_chart_use_case] = lambda: GenerateBarChartUseCase(repo)
app.dependency_overrides[get_distribution_use_case] = lambda: GenerateDistributionUseCase(repo)
app.dependency_overrides[get_list_responses_use_case] = lambda: ListResponsesUseCase(repo)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8011, log_level="warning")
