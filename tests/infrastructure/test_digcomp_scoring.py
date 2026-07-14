"""Tests del motor de cálculo DigComp 2.2 (Likert 1-4) — funciones puras."""
from infrastructure.adapters.ingestion.digcomp_scoring import (
    Pregunta,
    is_correct,
    likert_value,
    nivel_for_score,
    score_row,
)


def test_likert_value():
    assert likert_value("No sé cómo hacerlo") == 1
    assert likert_value("Puedo hacerlo con ayuda") == 2
    assert likert_value("Puedo hacerlo por mi cuenta") == 3
    assert likert_value("Puedo hacerlo y ayudo a otros") == 4
    # tolerante a mayúsculas/acentos/espacios
    assert likert_value("  no se como hacerlo ") == 1
    assert likert_value("") is None
    assert likert_value("respuesta rara") is None


def test_is_correct():
    assert is_correct("c. Reporto el problema al área", "c") is True
    assert is_correct("C. Reporto...", "c") is True
    assert is_correct("b. Otra cosa", "c") is False
    assert is_correct("", "c") is False
    assert is_correct("c. algo", None) is False


def test_nivel_for_score():
    assert nivel_for_score(1.4) == "Básico"
    assert nivel_for_score(1.99) == "Básico"
    assert nivel_for_score(2.0) == "Intermedio"
    assert nivel_for_score(2.8) == "Intermedio"
    assert nivel_for_score(3.0) == "Avanzado"
    assert nivel_for_score(3.74) == "Avanzado"
    assert nivel_for_score(3.75) == "Experto"
    assert nivel_for_score(4.0) == "Experto"
    assert nivel_for_score(None) is None


def _catalogo():
    """Catálogo mínimo: comp '4.1' con 5 Likert + 2 Validación (correctas 'c')."""
    pregs = []
    for i in range(1, 6):
        pregs.append(Pregunta(f"L{i}", "comp1", "4.1", 1, f"likert_{i}"))
    pregs.append(Pregunta("V1", "comp1", "4.1", 2, "valid_1", "c"))
    pregs.append(Pregunta("V2", "comp1", "4.1", 2, "valid_2", "c"))
    return pregs


def test_score_row_reproduce_caso_real():
    # Competencia 4.1: Likert 1,4,1,4,4 -> media 2.8 ; validación 2/2 -> 1 + 1*3 = 4.0
    row = {
        "likert_1": "No sé cómo hacerlo",        # 1
        "likert_2": "Puedo hacerlo y ayudo a otros",  # 4
        "likert_3": "No sé cómo hacerlo",        # 1
        "likert_4": "Puedo hacerlo y ayudo a otros",  # 4
        "likert_5": "Puedo hacerlo y ayudo a otros",  # 4
        "valid_1": "c. Reporto el problema al área",
        "valid_2": "c. Negarme y sugerirle que use la suya",
    }
    detalle, resultados = score_row(row, _catalogo())
    assert len(detalle) == 7
    assert len(resultados) == 1
    r = resultados[0]
    assert r.codigo_competencia == "4.1"
    assert r.score_autoevaluacion == 2.8
    assert r.score_conocimiento == 4.0
    assert r.nivel == "Intermedio"


def test_score_row_conocimiento_parcial():
    row = {f"likert_{i}": "Puedo hacerlo por mi cuenta" for i in range(1, 6)}  # todos 3 -> 3.0
    row["valid_1"] = "c. correcta"
    row["valid_2"] = "a. incorrecta"
    _detalle, resultados = score_row(row, _catalogo())
    r = resultados[0]
    assert r.score_autoevaluacion == 3.0
    assert r.score_conocimiento == 2.5  # 1 + 1/2 * 3
    assert r.nivel == "Avanzado"
