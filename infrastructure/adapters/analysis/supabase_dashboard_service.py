"""Servicio de dashboard sobre datos reales (escala Likert 0–3).

Lee la vista `v_dashboard_resultados` (una fila por encuestado × competencia con
score_autoevaluacion, score_conocimiento, nivel, género y rango de edad) y construye
los datos del tablero reutilizando los DTOs de análisis y el servicio de estadística
puro del dominio.

Métrica principal del tablero: `score_autoevaluacion` (0–3). Se muestra también la
media de `score_conocimiento` en las tarjetas.
"""
from __future__ import annotations

import logging

from supabase import Client

from application.dto.analysis_dto import (
    UTPL_COLORS,
    BarChartData,
    DistributionData,
    RadarData,
    SingleCompetencyStats,
    StatisticsResult,
)
from domain.services import statistics
from infrastructure.adapters.ingestion.digcomp_scoring import nivel_for_score

logger = logging.getLogger(__name__)

_VIEW = "v_dashboard_resultados"
MAX_SCORE = 3.0
_NIVELES = ["Básico", "Intermedio", "Avanzado", "Experto"]
_NIVEL_COLOR = {
    "Básico": "danger",
    "Intermedio": "secondary",
    "Avanzado": "primary",
    "Experto": "success",
}


class SupabaseDashboardService:
    """Construye los datos del dashboard desde la vista de resultados reales."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def _fetch(self) -> list[dict]:
        return self._client.table(_VIEW).select("*").execute().data or []

    def filter_options(self) -> dict:
        rows = self._fetch()
        return {
            "genders": sorted({r["genero"] for r in rows if r.get("genero")}),
            "age_ranges": sorted({r["edad_rango"] for r in rows if r.get("edad_rango")}),
            "provinces": [],
            "education_levels": [],
            "sectors": [],
        }

    def build_context(
        self, gender: str | None, age_range: str | None, competency_code: str | None
    ) -> dict | None:
        """Construye el contexto del dashboard. Devuelve None si no hay datos."""
        rows = self._fetch()
        if not rows:
            return None

        codes = sorted({r["codigo_competencia"] for r in rows})
        names = {r["codigo_competencia"]: r["nombre_competencia"] for r in rows}

        def keep(r: dict) -> bool:
            if gender and r.get("genero") != gender:
                return False
            if age_range and r.get("edad_rango") != age_range:
                return False
            return True

        frows = [r for r in rows if keep(r)]
        if not frows:
            return None

        selected = competency_code if competency_code in codes else codes[0]

        competencies: list[SingleCompetencyStats] = []
        radar_values: list[float] = []
        bar_values: list[float] = []
        cards: list[dict] = []
        means: list[float] = []

        for code in codes:
            crows = [r for r in frows if r["codigo_competencia"] == code]
            autos = [float(r["score_autoevaluacion"]) for r in crows if r.get("score_autoevaluacion") is not None]
            conocs = [float(r["score_conocimiento"]) for r in crows if r.get("score_conocimiento") is not None]
            st = statistics.calculate_all_descriptive_stats(autos)
            mean_auto = round(st["mean"], 2)
            mean_conoc = round(statistics.calculate_mean(conocs), 2)

            competencies.append(SingleCompetencyStats(
                competency_code=code, competency_name=names[code],
                mean=mean_auto, median=st["median"], mode=st["mode"],
                std_deviation=st["std_deviation"], variance=st["variance"],
                skewness=st["skewness"], kurtosis=st["kurtosis"],
                min_value=st["min"], max_value=st["max"], count=st["count"],
                percentile_25=st["percentile_25"], percentile_50=st["percentile_50"],
                percentile_75=st["percentile_75"],
            ))
            radar_values.append(mean_auto)
            bar_values.append(mean_auto)
            means.append(mean_auto)
            categoria = nivel_for_score(mean_auto) or "Básico"
            cards.append({
                "code": code, "name": names[code], "mean": mean_auto,
                "conoc": mean_conoc, "category": categoria,
                "color": _NIVEL_COLOR.get(categoria, "primary"),
            })

        sample_size = len([r for r in frows if r["codigo_competencia"] == codes[0]])
        overall_mean = round(sum(means) / len(means), 2) if means else 0.0

        # Distribución por NIVEL para la competencia seleccionada.
        sel_rows = [r for r in frows if r["codigo_competencia"] == selected]
        nivel_counts = {n: 0 for n in _NIVELES}
        for r in sel_rows:
            if r.get("nivel") in nivel_counts:
                nivel_counts[r["nivel"]] += 1
        sel_autos = [float(r["score_autoevaluacion"]) for r in sel_rows if r.get("score_autoevaluacion") is not None]

        current_filters = {}
        if gender:
            current_filters["respondent_gender"] = gender
        if age_range:
            current_filters["respondent_age_range"] = age_range

        return {
            "stats": StatisticsResult(
                competencies=competencies, overall_mean=overall_mean,
                sample_size=sample_size, filters_applied=current_filters,
            ),
            "radar": RadarData(labels=codes, values=radar_values, max_value=MAX_SCORE),
            "bar": BarChartData(labels=[names[c] for c in codes], values=bar_values, colors=list(UTPL_COLORS)),
            "dist": DistributionData(
                competency_code=selected, competency_name=names[selected],
                bins=_NIVELES, frequencies=[nivel_counts[n] for n in _NIVELES],
                mean_line=round(statistics.calculate_mean(sel_autos), 2),
            ),
            "cards": cards,
            "competency_codes": codes,
            "competency_names": names,
            "selected_code": selected,
            "filter_options": self.filter_options(),
            "current_filters": current_filters,
            "sample_size": sample_size,
            "max_score": MAX_SCORE,
        }
