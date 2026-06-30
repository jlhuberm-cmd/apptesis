"""Tests de las reglas de autenticación."""
from datetime import datetime, timedelta, timezone

from domain.rules import auth_rules as ar


def test_constantes():
    assert ar.MAX_LOGIN_ATTEMPTS == 3
    assert ar.VERIFICATION_CODE_LENGTH == 6
    assert ar.VERIFICATION_CODE_EXPIRY_MINUTES == 15
    assert ar.BCRYPT_ROUNDS == 12


def test_should_lock_account():
    assert ar.should_lock_account(3) is True
    assert ar.should_lock_account(4) is True
    assert ar.should_lock_account(2) is False
    assert ar.should_lock_account(0) is False


def test_generate_verification_code():
    code = ar.generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()
    # Aleatorio: muy improbable que 50 códigos sean idénticos.
    assert len({ar.generate_verification_code() for _ in range(50)}) > 1


def test_has_code_attempts_remaining():
    assert ar.has_code_attempts_remaining(0) is True
    assert ar.has_code_attempts_remaining(2) is True
    assert ar.has_code_attempts_remaining(3) is False


def test_is_code_expired():
    pasado = datetime.now(timezone.utc) - timedelta(minutes=1)
    futuro = datetime.now(timezone.utc) + timedelta(minutes=5)
    assert ar.is_code_expired(pasado) is True
    assert ar.is_code_expired(futuro) is False
    # naïve se asume UTC
    naive_pasado = datetime.utcnow() - timedelta(minutes=1)
    assert ar.is_code_expired(naive_pasado) is True


def test_validate_password_complexity():
    assert ar.validate_password_complexity("Abcdef1!") == []
    errores = ar.validate_password_complexity("abc")
    assert len(errores) == 4  # falta longitud, mayúscula, número, especial
    assert ar.validate_password_complexity("NoNumber!") != []
