"""DTOs de encuestas (carga, filtros, paginación, opciones de filtro).

Objetos de transferencia (Pydantic v2) entre la API y los casos de uso de encuestas.
Incluye un mapeador de la entidad SurveyResponse a un dict serializable.
"""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from domain.entities.survey_response import SurveyResponse


class UploadCSVRequest(BaseModel):
    """Entrada para la carga de un archivo CSV."""

    model_config = {"arbitrary_types_allowed": True}

    file_content: bytes
    filename: str
    uploaded_by: UUID


class UploadResult(BaseModel):
    """Resultado del procesamiento de un CSV."""

    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[str] = Field(default_factory=list)
    batch_id: UUID


class ResponseFilters(BaseModel):
    """Filtros demográficos + paginación para listar respuestas."""

    age_range: str | None = None
    gender: str | None = None
    province: str | None = None
    education_level: str | None = None
    sector: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


class PaginatedResponses(BaseModel):
    """Página de respuestas con metadatos de paginación."""

    items: list[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


class FilterOptions(BaseModel):
    """Valores disponibles por campo demográfico para poblar los filtros."""

    age_ranges: list[str] = Field(default_factory=list)
    genders: list[str] = Field(default_factory=list)
    provinces: list[str] = Field(default_factory=list)
    education_levels: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)


def survey_response_to_dict(response: SurveyResponse) -> dict:
    """Convierte una entidad SurveyResponse en un dict serializable para la vista."""
    return {
        "id": str(response.id),
        "age_range": response.respondent_age_range,
        "gender": response.respondent_gender,
        "province": response.respondent_province,
        "education_level": response.respondent_education_level,
        "sector": response.respondent_sector,
        "comp_4_1": response.comp_4_1_score,
        "comp_4_2": response.comp_4_2_score,
        "comp_4_3": response.comp_4_3_score,
        "comp_4_4": response.comp_4_4_score,
        "average": round(response.get_average_score(), 2),
        "created_at": response.created_at.isoformat(),
    }
