"""Configuración de la aplicación.

Define Settings (Pydantic BaseSettings) que carga variables desde .env: datos de la
app, Supabase, SMTP, seguridad y sesión. Nunca se hardcodean credenciales.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros de configuración cargados desde variables de entorno (.env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Aplicación ---
    APP_NAME: str = "DigComp 2.2 - Evaluación de Competencias Digitales"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str

    # --- Supabase ---
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str

    # --- SMTP (correo) ---
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str = "UTPL - Evaluación DigComp"

    # --- Seguridad ---
    BCRYPT_ROUNDS: int = 12

    # --- Sesión ---
    SESSION_SECRET_KEY: str
    SESSION_MAX_AGE: int = 3600

    # --- Acceso por rol (gating temporal por correo) ---
    # Listas de correos separadas por coma + contraseña compartida por rol.
    # ADMIN: dashboard + gestión de encuestas. VISOR: solo dashboard.
    ADMIN_EMAILS: str = ""
    ADMIN_PASSWORD: str = ""
    VIEWER_EMAILS: str = ""
    VIEWER_PASSWORD: str = ""

    @staticmethod
    def _emails(raw: str) -> list[str]:
        return [e.strip().lower() for e in raw.split(",") if e.strip()]

    @property
    def admin_emails_list(self) -> list[str]:
        """Correos de administrador normalizados (minúsculas)."""
        return self._emails(self.ADMIN_EMAILS)

    @property
    def viewer_emails_list(self) -> list[str]:
        """Correos de visor normalizados (minúsculas)."""
        return self._emails(self.VIEWER_EMAILS)

    def is_admin(self, email: str, password: str) -> bool:
        """Valida credenciales de administrador (correo en lista + contraseña)."""
        if not self.ADMIN_PASSWORD:
            return False
        return email.strip().lower() in self.admin_emails_list and password == self.ADMIN_PASSWORD

    def authenticate(self, email: str, password: str) -> str | None:
        """Devuelve el rol ('ADMIN' o 'VIEWER') si las credenciales son válidas, o None."""
        normalized = email.strip().lower()
        if self.ADMIN_PASSWORD and normalized in self.admin_emails_list and password == self.ADMIN_PASSWORD:
            return "ADMIN"
        if self.VIEWER_PASSWORD and normalized in self.viewer_emails_list and password == self.VIEWER_PASSWORD:
            return "VIEWER"
        return None


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia única (cacheada) de Settings."""
    return Settings()  # type: ignore[call-arg]
