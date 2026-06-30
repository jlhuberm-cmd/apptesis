"""Adaptador SupabaseSurveyRepository: implementa ISurveyRepository.

Traduce entre la entidad SurveyResponse y la tabla `survey_responses` de Supabase,
incluyendo el filtrado demográfico dinámico y la extracción de puntajes.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from supabase import Client

from domain.entities.survey_response import SurveyResponse
from domain.ports.outbound.survey_repository import ISurveyRepository
from domain.value_objects.demographic_filter import DemographicFilter

logger = logging.getLogger(__name__)

_TABLE = "survey_responses"

# Mapa código de competencia -> columna de puntaje en la tabla.
_SCORE_COLUMN: dict[str, str] = {
    "4.1": "comp_4_1_score",
    "4.2": "comp_4_2_score",
    "4.3": "comp_4_3_score",
    "4.4": "comp_4_4_score",
}


class SupabaseSurveyRepository(ISurveyRepository):
    """Implementación de ISurveyRepository sobre Supabase."""

    def __init__(self, client: Client) -> None:
        self._client = client

    @property
    def _table(self):
        return self._client.table(_TABLE)

    # ------------------------------------------------------------------ #
    # Escritura
    # ------------------------------------------------------------------ #
    def save_batch(self, responses: list[SurveyResponse]) -> int:
        """Inserta un lote de respuestas; devuelve la cantidad guardada."""
        if not responses:
            return 0
        rows = [self._to_row(r) for r in responses]
        result = self._table.insert(rows).execute()
        saved = len(result.data) if result.data else 0
        logger.info("Respuestas insertadas: %d", saved)
        return saved

    # ------------------------------------------------------------------ #
    # Lectura
    # ------------------------------------------------------------------ #
    def find_all(self, limit: int, offset: int) -> list[SurveyResponse]:
        result = (
            self._table.select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return [self._to_entity(r) for r in (result.data or [])]

    def find_by_filters(
        self, filters: DemographicFilter, limit: int, offset: int
    ) -> list[SurveyResponse]:
        query = self._apply_filters(self._table.select("*"), filters)
        result = (
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return [self._to_entity(r) for r in (result.data or [])]

    def count_all(self) -> int:
        result = self._table.select("id", count="exact").execute()
        return result.count or 0

    def count_by_filters(self, filters: DemographicFilter) -> int:
        query = self._apply_filters(
            self._table.select("id", count="exact"), filters
        )
        result = query.execute()
        return result.count or 0

    def get_all_scores(
        self, competency_code: str, filters: DemographicFilter | None = None
    ) -> list[float]:
        column = _SCORE_COLUMN.get(competency_code)
        if column is None:
            return []
        query = self._table.select(column)
        if filters is not None:
            query = self._apply_filters(query, filters)
        result = query.execute()
        return [
            float(row[column])
            for row in (result.data or [])
            if row.get(column) is not None
        ]

    def get_unique_values(self, field_name: str) -> list[str]:
        result = self._table.select(field_name).execute()
        values = {
            row[field_name]
            for row in (result.data or [])
            if row.get(field_name)
        }
        return sorted(values)

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #
    @staticmethod
    def _apply_filters(query, filters: DemographicFilter):
        """Aplica los filtros demográficos definidos (igualdad) a la consulta."""
        for column, value in filters.to_dict().items():
            query = query.eq(column, value)
        return query

    @staticmethod
    def _to_row(response: SurveyResponse) -> dict[str, Any]:
        return {
            "id": str(response.id),
            "uploaded_by": str(response.uploaded_by),
            "upload_batch_id": str(response.upload_batch_id),
            "respondent_age_range": response.respondent_age_range,
            "respondent_gender": response.respondent_gender,
            "respondent_province": response.respondent_province,
            "respondent_education_level": response.respondent_education_level,
            "respondent_sector": response.respondent_sector,
            "comp_4_1_score": response.comp_4_1_score,
            "comp_4_2_score": response.comp_4_2_score,
            "comp_4_3_score": response.comp_4_3_score,
            "comp_4_4_score": response.comp_4_4_score,
            "raw_data": response.raw_data,
            "created_at": response.created_at.isoformat(),
        }

    @staticmethod
    def _to_entity(row: dict[str, Any]) -> SurveyResponse:
        return SurveyResponse(
            id=UUID(str(row["id"])),
            uploaded_by=UUID(str(row["uploaded_by"])),
            upload_batch_id=UUID(str(row["upload_batch_id"])),
            respondent_age_range=row.get("respondent_age_range"),
            respondent_gender=row.get("respondent_gender"),
            respondent_province=row.get("respondent_province"),
            respondent_education_level=row.get("respondent_education_level"),
            respondent_sector=row.get("respondent_sector"),
            comp_4_1_score=float(row["comp_4_1_score"]),
            comp_4_2_score=float(row["comp_4_2_score"]),
            comp_4_3_score=float(row["comp_4_3_score"]),
            comp_4_4_score=float(row["comp_4_4_score"]),
            raw_data=row.get("raw_data") or {},
            created_at=_parse_dt(row["created_at"]),
        )


def _parse_dt(value: str | datetime) -> datetime:
    """Parsea un timestamp ISO de Supabase a datetime (acepta sufijo 'Z')."""
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
