"""Tests del procesador de CSV de ArcGIS."""
from uuid import uuid4

from infrastructure.adapters.csv.arcgis_csv_processor import ArcGISCSVProcessor

_HEADER = (
    "Rango de edad,Género,Provincia,Nivel educativo,Sector,"
    "P4.1_score,P4.2_score,P4.3_score,P4.4_score"
)


def _csv(*rows: str) -> bytes:
    return ("\n".join([_HEADER, *rows]) + "\n").encode("utf-8")


def test_csv_valido():
    proc = ArcGISCSVProcessor()
    data = _csv(
        "26-35,Femenino,Loja,Superior,Urbano,4,3,2,1",
        "18-25,Masculino,Quito,Media,Rural,1,1,1,1",
    )
    valid, errors = proc.process(data, uuid4(), uuid4())
    assert len(valid) == 2
    assert errors == []
    assert valid[0].respondent_gender == "Femenino"
    assert valid[0].comp_4_1_score == 4.0
    assert valid[0].raw_data.get("Género") == "Femenino"


def test_csv_con_filas_invalidas():
    proc = ArcGISCSVProcessor()
    data = _csv(
        "26-35,Femenino,Loja,Superior,Urbano,4,3,2,1",   # válida
        "30-40,Otro,Cuenca,Superior,Urbano,5,1,1,1",      # score 5 fuera de rango
        "30-40,Otro,Cuenca,Superior,Urbano,,1,1,1",       # score vacío
    )
    valid, errors = proc.process(data, uuid4(), uuid4())
    assert len(valid) == 1
    assert len(errors) == 2


def test_csv_uploaded_by_y_batch():
    proc = ArcGISCSVProcessor()
    uploader, batch = uuid4(), uuid4()
    valid, _ = proc.process(_csv("26-35,Femenino,Loja,Superior,Urbano,3,3,3,3"), uploader, batch)
    assert valid[0].uploaded_by == uploader
    assert valid[0].upload_batch_id == batch


def test_csv_columnas_faltantes():
    proc = ArcGISCSVProcessor()
    valid, errors = proc.process(b"a,b,c\n1,2,3\n", uuid4(), uuid4())
    assert valid == []
    assert len(errors) == 1
    assert "Faltan columnas" in errors[0]


def test_csv_ilegible():
    proc = ArcGISCSVProcessor()
    valid, errors = proc.process(b"", uuid4(), uuid4())
    assert valid == []
    assert len(errors) == 1


def test_mapeo_personalizado():
    proc = ArcGISCSVProcessor(column_mapping={
        "respondent_gender": "sexo", "respondent_age_range": "edad",
        "respondent_province": "prov", "respondent_education_level": "educ",
        "respondent_sector": "sec",
        "comp_4_1_score": "c1", "comp_4_2_score": "c2",
        "comp_4_3_score": "c3", "comp_4_4_score": "c4",
    })
    data = b"sexo,edad,c1,c2,c3,c4\nFemenino,26-35,3,3,3,3\n"
    valid, errors = proc.process(data, uuid4(), uuid4())
    assert len(valid) == 1
    assert valid[0].comp_4_1_score == 3.0
