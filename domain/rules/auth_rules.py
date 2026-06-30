"""Reglas y constantes de autenticación (intentos, expiración, complejidad).

Funciones puras del dominio (sin efectos secundarios salvo la generación aleatoria
de códigos, que usa el módulo `secrets` de la stdlib). No dependen de infraestructura.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

from domain.value_objects.password import Password

# --- Constantes de autenticación ---
MAX_LOGIN_ATTEMPTS: int = 3
VERIFICATION_CODE_LENGTH: int = 6
VERIFICATION_CODE_EXPIRY_MINUTES: int = 15
VERIFICATION_CODE_MAX_ATTEMPTS: int = 3
MIN_PASSWORD_LENGTH: int = 8
BCRYPT_ROUNDS: int = 12


def should_lock_account(failed_attempts: int) -> bool:
    """Indica si la cuenta debe bloquearse según los intentos fallidos acumulados."""
    return failed_attempts >= MAX_LOGIN_ATTEMPTS


def is_code_expired(expires_at: datetime) -> bool:
    """Indica si un código ya expiró comparándolo con la hora actual (UTC)."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= expires_at


def has_code_attempts_remaining(attempts: int) -> bool:
    """Indica si aún quedan intentos de validación de un código."""
    return attempts < VERIFICATION_CODE_MAX_ATTEMPTS


def generate_verification_code() -> str:
    """Genera un código numérico aleatorio de VERIFICATION_CODE_LENGTH dígitos.

    Usa `secrets` (criptográficamente seguro). El código se devuelve como cadena,
    conservando ceros a la izquierda (p. ej. "008421").
    """
    upper = 10 ** VERIFICATION_CODE_LENGTH
    number = secrets.randbelow(upper)
    return str(number).zfill(VERIFICATION_CODE_LENGTH)


def validate_password_complexity(password: str) -> list[str]:
    """Valida la complejidad de una contraseña.

    Devuelve la lista de errores (vacía si cumple todas las reglas). Delega en el
    value object Password para mantener una única fuente de verdad.
    """
    return Password.check(password)
