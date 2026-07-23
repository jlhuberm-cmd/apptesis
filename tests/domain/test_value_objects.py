"""Tests de los value objects del dominio."""
import pytest

from domain.value_objects.competency_score import CompetencyScore
from domain.value_objects.demographic_filter import DemographicFilter
from domain.value_objects.email_address import EmailAddress
from domain.value_objects.password import Password


class TestEmailAddress:
    def test_normaliza(self):
        e = EmailAddress("  Ada.Lovelace@UTPL.edu.EC ")
        assert e.value == "ada.lovelace@utpl.edu.ec"
        assert str(e) == "ada.lovelace@utpl.edu.ec"
        assert e.domain == "utpl.edu.ec"
        assert e.local_part == "ada.lovelace"

    @pytest.mark.parametrize("bad", ["", "a@b", "a@@b.com", "a b@c.com", "@c.com"])
    def test_rechaza_invalidos(self, bad):
        with pytest.raises(ValueError):
            EmailAddress(bad)

    def test_igualdad_y_hash(self):
        assert EmailAddress("x@y.com") == EmailAddress("X@Y.COM")
        assert len({EmailAddress("x@y.com"), EmailAddress("X@Y.com")}) == 1

    def test_is_valid_estatico(self):
        assert EmailAddress.is_valid("a@b.com")
        assert not EmailAddress.is_valid("no-arroba")


class TestPassword:
    def test_valida(self):
        assert Password("Abcdef1!").is_valid()
        assert Password("Abcdef1!").validate() == []

    def test_debil(self):
        assert len(Password("abc").validate()) == 4

    @pytest.mark.parametrize("pw", ["alllower1!", "NOLOWER1!", "NoNumber!", "NoSpecial1"])
    def test_reglas_individuales(self, pw):
        assert not Password(pw).is_valid()

    def test_no_revela_valor(self):
        p = Password("Abcdef1!")
        assert str(p) == "********"
        assert "Abcdef1!" not in repr(p)


class TestCompetencyScore:
    def test_niveles(self):
        assert CompetencyScore(1).get_level_category() == "Básico"
        assert CompetencyScore(2.5).get_level_category() == "Intermedio"
        assert CompetencyScore(3).get_level_category() == "Avanzado"
        assert CompetencyScore(4).get_level_category() == "Experto"
        assert CompetencyScore(3).get_level_name() == "Avanzado 3"

    @pytest.mark.parametrize("bad", [0.5, 4.5, -1, 100])
    def test_fuera_de_rango(self, bad):
        with pytest.raises(ValueError):
            CompetencyScore(bad)

    def test_nivel_y_igualdad(self):
        assert CompetencyScore(2.4).level == 2
        assert CompetencyScore(4) == CompetencyScore(4.0)


class TestDemographicFilter:
    def test_vacio(self):
        f = DemographicFilter()
        assert not f.has_any_filter()
        assert f.to_dict() == {}

    def test_to_dict_omite_none_y_vacios(self):
        f = DemographicFilter(age_range="26-35", gender="F", province="  ")
        assert f.has_any_filter()
        assert f.to_dict() == {"respondent_age_range": "26-35", "respondent_gender": "F"}
        assert f.province is None

    def test_rango_edad_invalido(self):
        with pytest.raises(ValueError):
            DemographicFilter(age_range="99-100")

    def test_hashable(self):
        assert DemographicFilter(gender="F") == DemographicFilter(gender="F")
        assert len({DemographicFilter(gender="F"), DemographicFilter(gender="F")}) == 1
