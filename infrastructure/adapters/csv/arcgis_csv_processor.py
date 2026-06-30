"""ArcGISCSVProcessor: parsea CSV de ArcGIS Survey123 a entidades SurveyResponse.

Lee el CSV con pandas y mapea sus columnas (configurables) a los campos de la
entidad SurveyResponse. Valida cada fila (puntajes en rango 1.0–8.0, campos de
puntaje presentes) y conserva la fila original en `raw_data` para trazabilidad.

Contrato (esperado por UploadCSVUseCase, Paso 6):
    process(file_content: bytes, uploaded_by: UUID, batch_id: UUID)
        -> tuple[list[SurveyResponse], list[str]]

NOTA: el mapeo por defecto usa nombres de columna de EJEMPLO. Para un CSV real se
debe pasar un `column_mapping` con los encabezados exactos del archivo.
"""
from __future__ import annotations

import io
import logging
import math
from typing import Any
from uuid import UUID

import pandas as pd

from domain.entities.survey_response import MAX_SCORE, MIN_SCORE, SurveyResponse

logger = logging.getLogger(__name__)

# Mapeo por defecto: campo de la entidad -> encabezado del CSV (ejemplo).
DEFAULT_COLUMN_MAPPING: dict[str, str] = {
    "respondent_age_range": "Rango de edad",
    "respondent_gender": "Género",
    "respondent_province": "Provincia",
    "respondent_education_level": "Nivel educativo",
    "respondent_sector": "Sector",
    "comp_4_1_score": "P4.1_score",
    "comp_4_2_score": "P4.2_score",
    "comp_4_3_score": "P4.3_score",
    "comp_4_4_score": "P4.4_score",
}

_DEMOGRAPHIC_FIELDS = (
    "respondent_age_range",
    "respondent_gender",
    "respondent_province",
    "respondent_education_level",
    "respondent_sector",
)
_SCORE_FIELDS = (
    "comp_4_1_score",
    "comp_4_2_score",
    "comp_4_3_score",
    "comp_4_4_score",
)


class ArcGISCSVProcessor:
    """Procesador de archivos CSV exportados de ArcGIS Survey123."""

    def __init__(self, column_mapping: dict[str, str] | None = None) -> None:
        self._mapping = column_mapping or dict(DEFAULT_COLUMN_MAPPING)

    def process(
        self, file_content: bytes, uploaded_by: UUID, batch_id: UUID
    ) -> tuple[list[SurveyResponse], list[str]]:
        """Parsea el CSV y devuelve (respuestas_válidas, errores)."""
        try:
            df = pd.read_csv(io.BytesIO(file_content))
        except Exception as exc:
            logger.exception("No se pudo leer el CSV.")
            return [], [f"No se pudo leer el archivo CSV: {exc}"]

        # Verifica que existan las columnas de puntaje requeridas.
        missing = [
            self._mapping[f] for f in _SCORE_FIELDS if self._mapping[f] not in df.columns
        ]
        if missing:
            return [], [
                "Faltan columnas de puntaje en el CSV: " + ", ".join(missing)
            ]

        valid: list[SurveyResponse] = []
        errors: list[str] = []

        for position, (_, row) in enumerate(df.iterrows(), start=1):
            try:
                response = self._row_to_response(row, uploaded_by, batch_id)
                valid.append(response)
            except (ValueError, KeyError, TypeError) as exc:
                errors.append(f"Fila {position}: {exc}")

        logger.info(
            "CSV procesado: %d válidas, %d con error.", len(valid), len(errors)
        )
        return valid, errors

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #
    def _row_to_response(
        self, row: "pd.Series", uploaded_by: UUID, batch_id: UUID
    ) -> SurveyResponse:
        """Convierte una fila del CSV en una entidad SurveyResponse validada."""
        demographics = {
            field: self._clean_str(row.get(self._mapping[field]))
            for field in _DEMOGRAPHIC_FIELDS
            if self._mapping[field] in row.index
        }

        scores = {}
        for field in _SCORE_FIELDS:
            raw = row.get(self._mapping[field])
            score = self._parse_score(raw)
            if score is None:
                raise ValueError(
                    f"puntaje inválido o vacío en '{self._mapping[field]}'."
                )
            if not (MIN_SCORE <= score <= MAX_SCORE):
                raise ValueError(
                    f"puntaje {score} fuera del rango [{MIN_SCORE}, {MAX_SCORE}]."
                )
            scores[field] = score

        return SurveyResponse(
            uploaded_by=uploaded_by,
            upload_batch_id=batch_id,
            raw_data=self._row_to_raw(row),
            **demographics,
            **scores,
        )

    @staticmethod
    def _parse_score(value: Any) -> float | None:
        """Convierte un valor del CSV a float; devuelve None si es vacío/no numérico."""
        if value is None:
            return None
        try:
            if isinstance(value, float) and math.isnan(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clean_str(value: Any) -> str | None:
        """Normaliza un valor de texto del CSV (NaN/vacío -> None)."""
        if value is None:
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _row_to_raw(row: "pd.Series") -> dict[str, Any]:
        """Convierte la fila completa en un dict JSON-serializable (NaN -> None)."""
        raw: dict[str, Any] = {}
        for key, value in row.to_dict().items():
            if isinstance(value, float) and math.isnan(value):
                raw[str(key)] = None
            else:
                raw[str(key)] = value
        return raw
