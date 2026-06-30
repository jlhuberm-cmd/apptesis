"""Entidad Competency y enum CompetencyLevel (niveles 1–8 de DigComp 2.2).
Incluye las 4 competencias predefinidas del Área 4 (Seguridad).

Núcleo del dominio: sin dependencias externas.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class CompetencyLevel(IntEnum):
    """Niveles de competencia del marco DigComp 2.2 (1 a 8)."""

    FOUNDATION_1 = 1
    FOUNDATION_2 = 2
    INTERMEDIATE_3 = 3
    INTERMEDIATE_4 = 4
    ADVANCED_5 = 5
    ADVANCED_6 = 6
    HIGHLY_SPECIALISED_7 = 7
    HIGHLY_SPECIALISED_8 = 8


@dataclass(frozen=True)
class Competency:
    """Competencia digital del marco DigComp 2.2.

    Atributos:
        code: Código de la competencia ("4.1", "4.2", "4.3", "4.4").
        name: Nombre corto de la competencia.
        description: Descripción de la competencia.
    """

    code: str
    name: str
    description: str


# Competencias predefinidas del Área 4 — Seguridad (DigComp 2.2).
_AREA4_COMPETENCIES: tuple[Competency, ...] = (
    Competency(
        code="4.1",
        name="Protección de dispositivos",
        description=(
            "Proteger los dispositivos y los contenidos digitales, y comprender "
            "los riesgos y amenazas en los entornos digitales."
        ),
    ),
    Competency(
        code="4.2",
        name="Protección de datos personales y privacidad",
        description=(
            "Proteger los datos personales y la privacidad en los entornos "
            "digitales."
        ),
    ),
    Competency(
        code="4.3",
        name="Protección de la salud y el bienestar",
        description=(
            "Evitar riesgos para la salud y amenazas para el bienestar físico y "
            "psicológico en el uso de las tecnologías digitales."
        ),
    ),
    Competency(
        code="4.4",
        name="Protección del medio ambiente",
        description=(
            "Tomar conciencia del impacto ambiental de las tecnologías digitales "
            "y de su uso."
        ),
    ),
)


def get_area4_competencies() -> list[Competency]:
    """Devuelve las 4 competencias predefinidas del Área 4 de DigComp 2.2."""
    return list(_AREA4_COMPETENCIES)


def get_competency_by_code(code: str) -> Competency | None:
    """Devuelve la competencia con el código indicado, o None si no existe."""
    for competency in _AREA4_COMPETENCIES:
        if competency.code == code:
            return competency
    return None
