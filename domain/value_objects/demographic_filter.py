"""Value object DemographicFilter: filtros demográficos opcionales e inmutables.

Representa una combinación de filtros (edad, género, provincia, nivel educativo,
sector) aplicable a las respuestas de la encuesta. Todos los campos son opcionales;
un filtro vacío significa "sin filtrar".
"""
from __future__ import annotations

from dataclasses import dataclass

# Rangos de edad predefinidos aceptados por el filtro.
VALID_AGE_RANGES: tuple[str, ...] = (
    "18-25",
    "26-35",
    "36-45",
    "46-55",
    "56-65",
    "66+",
)


@dataclass(frozen=True)
class DemographicFilter:
    """Filtros demográficos para acotar las respuestas analizadas.

    Atributos:
        age_range: Rango de edad (debe pertenecer a VALID_AGE_RANGES si se indica).
        gender: Género del encuestado.
        province: Provincia del encuestado.
        education_level: Nivel educativo del encuestado.
        sector: Sector del encuestado.

    Es inmutable y hashable, por lo que puede usarse como clave de caché o en sets.
    """

    age_range: str | None = None
    gender: str | None = None
    province: str | None = None
    education_level: str | None = None
    sector: str | None = None

    def __post_init__(self) -> None:
        # Normaliza cadenas vacías a None para tratarlas como "sin filtro".
        for name in ("age_range", "gender", "province", "education_level", "sector"):
            raw = getattr(self, name)
            if isinstance(raw, str):
                stripped = raw.strip()
                object.__setattr__(self, name, stripped or None)

        if self.age_range is not None and self.age_range not in VALID_AGE_RANGES:
            raise ValueError(
                f"Rango de edad inválido: '{self.age_range}'. "
                f"Valores permitidos: {', '.join(VALID_AGE_RANGES)}."
            )

    def has_any_filter(self) -> bool:
        """Indica si al menos un filtro está definido."""
        return any(
            value is not None
            for value in (
                self.age_range,
                self.gender,
                self.province,
                self.education_level,
                self.sector,
            )
        )

    def to_dict(self) -> dict[str, str]:
        """Devuelve solo los filtros definidos (los None se omiten)."""
        return {
            key: value
            for key, value in {
                "respondent_age_range": self.age_range,
                "respondent_gender": self.gender,
                "respondent_province": self.province,
                "respondent_education_level": self.education_level,
                "respondent_sector": self.sector,
            }.items()
            if value is not None
        }
