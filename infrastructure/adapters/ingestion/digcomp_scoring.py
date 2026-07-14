"""Motor de cálculo DigComp 2.2 (escala Likert 1–4) — funciones puras.

Replica EXACTAMENTE la lógica del esquema real del usuario:

- Likert (texto → valor 1–4):
    "No sé cómo hacerlo"            → 1  (Básico)
    "Puedo hacerlo con ayuda"       → 2  (Intermedio)
    "Puedo hacerlo por mi cuenta"   → 3  (Avanzado)
    "Puedo hacerlo y ayudo a otros" → 4  (Experto)

- score_autoevaluacion = promedio de los valores Likert de la competencia.
- score_conocimiento   = 1 + (nº respuestas correctas / nº preguntas de validación) × 3.
    Una respuesta de validación es correcta si (en minúsculas) empieza por
    "<letra_correcta>." (p. ej. "c. ...").
- nivel (sobre score_autoevaluacion):
    1.00–1.99 → Básico · 2.00–2.99 → Intermedio · 3.00–3.74 → Avanzado · 3.75–4.00 → Experto

No depende de infraestructura: solo recibe la fila del CSV y el catálogo de preguntas.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

# Tipos de pregunta (tabla tipo_preguntas).
TIPO_LIKERT = 1
TIPO_VALIDACION = 2


def _norm(text: object) -> str:
    """Normaliza texto: sin acentos, en minúsculas y sin espacios sobrantes."""
    if text is None:
        return ""
    s = unicodedata.normalize("NFKD", str(text))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


# Mapa Likert normalizado → valor 1–4.
_LIKERT_MAP = {
    _norm("No sé cómo hacerlo"): 1,
    _norm("Puedo hacerlo con ayuda"): 2,
    _norm("Puedo hacerlo por mi cuenta"): 3,
    _norm("Puedo hacerlo y ayudo a otros"): 4,
}


def likert_value(text: object) -> int | None:
    """Convierte el texto Likert a 1–4; None si está vacío o no reconocido."""
    key = _norm(text)
    if not key:
        return None
    return _LIKERT_MAP.get(key)


def is_correct(answer: object, letra_correcta: str | None) -> bool:
    """Indica si una respuesta de validación es correcta (empieza por '<letra>.')."""
    if not letra_correcta:
        return False
    return _norm(answer).startswith(letra_correcta.strip().lower() + ".")


def nivel_for_score(score: float | None) -> str | None:
    """Clasifica un score de autoevaluación (1–4) en el nivel DigComp."""
    if score is None:
        return None
    if score < 2.0:
        return "Básico"
    if score < 3.0:
        return "Intermedio"
    if score < 3.75:
        return "Avanzado"
    return "Experto"


@dataclass(frozen=True)
class Pregunta:
    """Pregunta del catálogo (subconjunto necesario para el cálculo)."""

    id_pregunta: str
    id_competencia: str
    codigo_competencia: str
    id_tipo: int
    codigo_columna: str
    letra_correcta: str | None = None


@dataclass
class DetalleRespuesta:
    """Respuesta normalizada a una pregunta (fila de detalle_respuestas)."""

    id_pregunta: str
    valor_likert: int | None
    valor_texto: str | None
    es_correcta: bool | None


@dataclass
class ResultadoCompetencia:
    """Resultado por competencia de un encuestado (fila de resultados_competencia)."""

    id_competencia: str
    codigo_competencia: str
    score_autoevaluacion: float | None
    score_conocimiento: float | None
    nivel: str | None


def _mean(values: list[int]) -> float:
    return sum(values) / len(values)


def score_row(
    row: dict[str, object], preguntas: list[Pregunta]
) -> tuple[list[DetalleRespuesta], list[ResultadoCompetencia]]:
    """Calcula el detalle y los resultados por competencia de una fila del CSV.

    Args:
        row: fila del CSV como dict {encabezado: valor}.
        preguntas: catálogo de preguntas (con competencia, tipo y respuesta correcta).

    Returns:
        (detalle, resultados) listos para insertar en la base de datos.
    """
    detalle: list[DetalleRespuesta] = []
    # Agrupa preguntas por competencia preservando su id/código.
    por_comp: dict[str, dict] = {}

    for p in preguntas:
        comp = por_comp.setdefault(
            p.id_competencia,
            {"codigo": p.codigo_competencia, "likert": [], "valid_total": 0, "valid_ok": 0},
        )
        raw = row.get(p.codigo_columna)
        if p.id_tipo == TIPO_LIKERT:
            v = likert_value(raw)
            detalle.append(DetalleRespuesta(p.id_pregunta, v, None, None))
            if v is not None:
                comp["likert"].append(v)
        elif p.id_tipo == TIPO_VALIDACION:
            ok = is_correct(raw, p.letra_correcta)
            texto = None if raw is None else str(raw)
            detalle.append(DetalleRespuesta(p.id_pregunta, None, texto, ok))
            comp["valid_total"] += 1
            if ok:
                comp["valid_ok"] += 1

    resultados: list[ResultadoCompetencia] = []
    for id_comp, data in por_comp.items():
        auto = round(_mean(data["likert"]), 2) if data["likert"] else None
        conoc = (
            round(1 + (data["valid_ok"] / data["valid_total"]) * 3, 2)
            if data["valid_total"]
            else None
        )
        resultados.append(
            ResultadoCompetencia(
                id_competencia=id_comp,
                codigo_competencia=data["codigo"],
                score_autoevaluacion=auto,
                score_conocimiento=conoc,
                nivel=nivel_for_score(auto),
            )
        )
    return detalle, resultados
