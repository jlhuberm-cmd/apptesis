"""DTOs de autenticación (login, registro, verificación, reset, unlock).

Objetos de transferencia de datos (Pydantic v2) que cruzan la frontera entre la
capa de interfaz (API) y los casos de uso. No contienen lógica de negocio.
"""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

# Patrón de código de verificación: exactamente 6 dígitos.
_CODE_PATTERN = r"^\d{6}$"


class LoginRequest(BaseModel):
    """Datos de entrada para iniciar sesión."""

    email: str
    password: str


class LoginResponse(BaseModel):
    """Resultado de un inicio de sesión exitoso."""

    user_id: UUID
    email: str
    full_name: str
    role: str
    message: str = "Inicio de sesión exitoso."


class RegisterRequest(BaseModel):
    """Datos de entrada para registrar una cuenta."""

    email: str
    password: str
    confirm_password: str
    full_name: str


class RegisterResponse(BaseModel):
    """Resultado de un registro exitoso."""

    user_id: UUID
    email: str
    message: str = "Cuenta creada. Revisa tu correo para verificarla."


class VerifyEmailRequest(BaseModel):
    """Datos de entrada para verificar el email con un código."""

    email: str
    code: str = Field(min_length=6, max_length=6, pattern=_CODE_PATTERN)


class ForgotPasswordRequest(BaseModel):
    """Datos de entrada para solicitar la recuperación de contraseña."""

    email: str


class ResetPasswordRequest(BaseModel):
    """Datos de entrada para restablecer la contraseña con un código."""

    email: str
    code: str = Field(min_length=6, max_length=6, pattern=_CODE_PATTERN)
    new_password: str
    confirm_password: str


class UnlockAccountRequest(BaseModel):
    """Datos de entrada para desbloquear una cuenta con un código."""

    email: str
    code: str = Field(min_length=6, max_length=6, pattern=_CODE_PATTERN)


class GenericResponse(BaseModel):
    """Respuesta genérica de éxito/mensaje para operaciones sin payload propio."""

    success: bool
    message: str
