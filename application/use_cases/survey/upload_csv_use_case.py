"""Caso de uso: carga y procesamiento de CSV de ArcGIS Survey123.

Orquesta: parsear el CSV (vía csv_processor), validar los puntajes, persistir las
respuestas válidas y devolver un resumen de la carga.

Contrato esperado del csv_processor (implementado en infraestructura, Paso 7):
    process(file_content: bytes, uploaded_by: UUID, batch_id: UUID)
        -> tuple[list[SurveyResponse], list[str]]
    Devuelve (respuestas_válidas, errores). El use case controla el batch_id para
    poder informarlo aun cuando no haya filas válidas.
"""
from __future__ import annotations

import logging
from typing import Protocol
from uuid import UUID, uuid4

from application.dto.survey_dto import UploadCSVRequest, UploadResult
from domain.entities.survey_response import SurveyResponse
from domain.ports.outbound.survey_repository import ISurveyRepository
from domain.rules.analysis_rules import is_valid_score

logger = logging.getLogger(__name__)


class ICSVProcessor(Protocol):
    """Contrato mínimo del procesador de CSV (puerto informal vía Protocol)."""

    def process(
        self, file_content: bytes, uploaded_by: UUID, batch_id: UUID
    ) -> tuple[list[SurveyResponse], list[str]]:
        ...


class UploadCSVUseCase:
    """Caso de uso de carga de CSV."""

    def __init__(
        self, survey_repo: ISurveyRepository, csv_processor: ICSVProcessor
    ) -> None:
        self._survey_repo = survey_repo
        self._csv_processor = csv_processor

    def execute(self, request: UploadCSVRequest) -> UploadResult:
        """Procesa el CSV y persiste las respuestas válidas."""
        batch_id = uuid4()
        responses, errors = self._csv_processor.process(
            request.file_content, request.uploaded_by, batch_id
        )

        # Validación defensiva: descartar respuestas con puntajes fuera de rango.
        valid_responses: list[SurveyResponse] = []
        for index, response in enumerate(responses, start=1):
            scores = response.get_scores_dict().values()
            if all(is_valid_score(s) for s in scores):
                valid_responses.append(response)
            else:
                errors.append(f"Fila {index}: puntaje fuera del rango [1.0, 4.0].")

        saved = (
            self._survey_repo.save_batch(valid_responses) if valid_responses else 0
        )

        valid_rows = saved
        invalid_rows = len(errors)
        total_rows = valid_rows + invalid_rows
        logger.info(
            "Carga CSV (batch %s): %d válidas, %d inválidas.",
            batch_id, valid_rows, invalid_rows,
        )
        return UploadResult(
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            errors=errors,
            batch_id=batch_id,
        )
