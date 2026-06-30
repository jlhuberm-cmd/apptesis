"""Entidad SurveyResponse: una respuesta (fila del CSV) con datos demográficos
y los puntajes de las competencias 4.1–4.4.

Núcleo del dominio: NO importa pandas ni nada de infraestructura. Encapsula la
validación de que cada puntaje esté en el rango válido de DigComp (1.0–8.0).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Rango válido de puntajes según los niveles de DigComp 2.2.
MIN_SCORE: float = 1.0
MAX_SCORE: float = 8.0


def _utcnow() -> datetime:
    """Devuelve la hora actual en UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


class SurveyResponse(BaseModel):
    """Respuesta individual de la encuesta (una fila del CSV de Survey123).

    Atributos:
        id: Identificador único de la respuesta.
        uploaded_by: UUID del usuario que cargó el lote.
        upload_batch_id: UUID del lote de carga (común a todas las filas de un CSV).
        respondent_age_range: Rango de edad del encuestado.
        respondent_gender: Género del encuestado.
        respondent_province: Provincia del encuestado.
        respondent_education_level: Nivel educativo del encuestado.
        respondent_sector: Sector (p. ej. urbano/rural, público/privado).
        comp_4_1_score: Puntaje en la competencia 4.1 (1.0–8.0).
        comp_4_2_score: Puntaje en la competencia 4.2 (1.0–8.0).
        comp_4_3_score: Puntaje en la competencia 4.3 (1.0–8.0).
        comp_4_4_score: Puntaje en la competencia 4.4 (1.0–8.0).
        raw_data: Fila original completa del CSV (para trazabilidad).
        created_at: Fecha de creación del registro.
    """

    model_config = ConfigDict(validate_assignment=True)

    id: UUID = Field(default_factory=uuid4)
    uploaded_by: UUID
    upload_batch_id: UUID

    respondent_age_range: str | None = None
    respondent_gender: str | None = None
    respondent_province: str | None = None
    respondent_education_level: str | None = None
    respondent_sector: str | None = None

    comp_4_1_score: float = Field(ge=MIN_SCORE, le=MAX_SCORE)
    comp_4_2_score: float = Field(ge=MIN_SCORE, le=MAX_SCORE)
    comp_4_3_score: float = Field(ge=MIN_SCORE, le=MAX_SCORE)
    comp_4_4_score: float = Field(ge=MIN_SCORE, le=MAX_SCORE)

    raw_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)

    @field_validator(
        "comp_4_1_score",
        "comp_4_2_score",
        "comp_4_3_score",
        "comp_4_4_score",
    )
    @classmethod
    def _validate_score_range(cls, value: float) -> float:
        """Valida que el puntaje esté dentro del rango DigComp [1.0, 8.0]."""
        if not (MIN_SCORE <= value <= MAX_SCORE):
            raise ValueError(
                f"El puntaje {value} está fuera del rango válido "
                f"[{MIN_SCORE}, {MAX_SCORE}]."
            )
        return float(value)

    def get_scores_dict(self) -> dict[str, float]:
        """Devuelve los puntajes indexados por código de competencia."""
        return {
            "4.1": self.comp_4_1_score,
            "4.2": self.comp_4_2_score,
            "4.3": self.comp_4_3_score,
            "4.4": self.comp_4_4_score,
        }

    def get_average_score(self) -> float:
        """Devuelve el promedio de los puntajes de las 4 competencias."""
        scores = self.get_scores_dict().values()
        return sum(scores) / len(scores)
