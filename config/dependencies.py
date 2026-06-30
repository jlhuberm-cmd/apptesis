"""Composition root: inyección de dependencias.

Conecta los puertos del dominio con sus adaptadores concretos y construye los casos
de uso. Único lugar donde se "conoce" la infraestructura: aquí se decide qué
implementación concreta cumple cada puerto.

Convención:
- Los singletons (settings, cliente, repos, servicios) se cachean con lru_cache.
- Los casos de uso se construyen bajo demanda (son baratos y sin estado propio).
- Las factories devuelven el TIPO DE PUERTO (interfaz), no la implementación, para
  reforzar que el resto del sistema depende de abstracciones.
"""
from __future__ import annotations

from functools import lru_cache

from supabase import Client

# --- Configuración / cliente ---
from config.settings import Settings, get_settings
from infrastructure.adapters.persistence.supabase_client import get_supabase_client

# --- Puertos (interfaces) ---
from domain.ports.outbound.email_service import IEmailService
from domain.ports.outbound.password_hasher import IPasswordHasher
from domain.ports.outbound.survey_repository import ISurveyRepository
from domain.ports.outbound.user_repository import IUserRepository
from domain.ports.outbound.verification_repository import IVerificationRepository

# --- Adaptadores (implementaciones) ---
from infrastructure.adapters.csv.arcgis_csv_processor import ArcGISCSVProcessor
from infrastructure.adapters.email.smtp_email_service import SmtpEmailService
from infrastructure.adapters.persistence.supabase_survey_repository import (
    SupabaseSurveyRepository,
)
from infrastructure.adapters.persistence.supabase_user_repository import (
    SupabaseUserRepository,
)
from infrastructure.adapters.persistence.supabase_verification_repository import (
    SupabaseVerificationRepository,
)
from infrastructure.adapters.security.bcrypt_password_hasher import BcryptPasswordHasher

# --- Casos de uso: auth ---
from application.use_cases.auth.forgot_password_use_case import ForgotPasswordUseCase
from application.use_cases.auth.login_use_case import LoginUseCase
from application.use_cases.auth.register_use_case import RegisterUseCase
from application.use_cases.auth.reset_password_use_case import ResetPasswordUseCase
from application.use_cases.auth.unlock_account_use_case import UnlockAccountUseCase
from application.use_cases.auth.verify_email_use_case import VerifyEmailUseCase

# --- Casos de uso: survey ---
from application.use_cases.survey.filter_responses_use_case import FilterResponsesUseCase
from application.use_cases.survey.list_responses_use_case import ListResponsesUseCase
from application.use_cases.survey.upload_csv_use_case import UploadCSVUseCase

# --- Casos de uso: analysis ---
from application.use_cases.analysis.compute_statistics_use_case import (
    ComputeStatisticsUseCase,
)
from application.use_cases.analysis.generate_bar_chart_use_case import (
    GenerateBarChartUseCase,
)
from application.use_cases.analysis.generate_distribution_use_case import (
    GenerateDistributionUseCase,
)
from application.use_cases.analysis.generate_radar_chart_use_case import (
    GenerateRadarChartUseCase,
)


# ====================================================================== #
# Infraestructura (singletons)
# ====================================================================== #
@lru_cache
def get_client() -> Client:
    """Cliente Supabase singleton."""
    return get_supabase_client()


@lru_cache
def get_password_hasher() -> IPasswordHasher:
    """Adaptador de hashing (bcrypt)."""
    return BcryptPasswordHasher(rounds=get_settings().BCRYPT_ROUNDS)


@lru_cache
def get_user_repository() -> IUserRepository:
    return SupabaseUserRepository(client=get_client())


@lru_cache
def get_survey_repository() -> ISurveyRepository:
    return SupabaseSurveyRepository(client=get_client())


@lru_cache
def get_verification_repository() -> IVerificationRepository:
    return SupabaseVerificationRepository(client=get_client())


@lru_cache
def get_email_service() -> IEmailService:
    settings: Settings = get_settings()
    return SmtpEmailService(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        user=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        from_email=settings.SMTP_FROM_EMAIL,
        from_name=settings.SMTP_FROM_NAME,
    )


@lru_cache
def get_csv_processor() -> ArcGISCSVProcessor:
    return ArcGISCSVProcessor()


@lru_cache
def get_ingestion_service() -> "SupabaseSurveyIngestion":
    """Servicio de carga/borrado de encuestas en el esquema real (Likert 0–3)."""
    from infrastructure.adapters.ingestion.supabase_ingestion_service import (
        SupabaseSurveyIngestion,
    )

    return SupabaseSurveyIngestion(client=get_client())


@lru_cache
def get_dashboard_service() -> "SupabaseDashboardService":
    """Servicio de dashboard sobre datos reales (vista v_dashboard_resultados, 0–3)."""
    from infrastructure.adapters.analysis.supabase_dashboard_service import (
        SupabaseDashboardService,
    )

    return SupabaseDashboardService(client=get_client())


@lru_cache
def get_auth_service() -> "SupabaseAuthService":
    """Servicio de autenticación contra Supabase Auth + perfiles/roles/permisos."""
    from infrastructure.adapters.auth.supabase_auth_service import SupabaseAuthService

    settings = get_settings()
    return SupabaseAuthService(
        url=settings.SUPABASE_URL,
        anon_key=settings.SUPABASE_KEY,
        db_client=get_client(),
    )


# ====================================================================== #
# Casos de uso: autenticación
# ====================================================================== #
def get_login_use_case() -> LoginUseCase:
    return LoginUseCase(
        user_repo=get_user_repository(),
        password_hasher=get_password_hasher(),
    )


def get_register_use_case() -> RegisterUseCase:
    return RegisterUseCase(
        user_repo=get_user_repository(),
        password_hasher=get_password_hasher(),
        verification_repo=get_verification_repository(),
        email_service=get_email_service(),
    )


def get_verify_email_use_case() -> VerifyEmailUseCase:
    return VerifyEmailUseCase(
        user_repo=get_user_repository(),
        verification_repo=get_verification_repository(),
        password_hasher=get_password_hasher(),
        email_service=get_email_service(),
    )


def get_forgot_password_use_case() -> ForgotPasswordUseCase:
    return ForgotPasswordUseCase(
        user_repo=get_user_repository(),
        verification_repo=get_verification_repository(),
        password_hasher=get_password_hasher(),
        email_service=get_email_service(),
    )


def get_reset_password_use_case() -> ResetPasswordUseCase:
    return ResetPasswordUseCase(
        user_repo=get_user_repository(),
        verification_repo=get_verification_repository(),
        password_hasher=get_password_hasher(),
    )


def get_unlock_account_use_case() -> UnlockAccountUseCase:
    return UnlockAccountUseCase(
        user_repo=get_user_repository(),
        verification_repo=get_verification_repository(),
        password_hasher=get_password_hasher(),
        email_service=get_email_service(),
    )


# ====================================================================== #
# Casos de uso: encuestas
# ====================================================================== #
def get_upload_csv_use_case() -> UploadCSVUseCase:
    return UploadCSVUseCase(
        survey_repo=get_survey_repository(),
        csv_processor=get_csv_processor(),
    )


def get_list_responses_use_case() -> ListResponsesUseCase:
    return ListResponsesUseCase(survey_repo=get_survey_repository())


def get_filter_responses_use_case() -> FilterResponsesUseCase:
    return FilterResponsesUseCase(survey_repo=get_survey_repository())


# ====================================================================== #
# Casos de uso: análisis
# ====================================================================== #
def get_compute_statistics_use_case() -> ComputeStatisticsUseCase:
    return ComputeStatisticsUseCase(survey_repo=get_survey_repository())


def get_radar_chart_use_case() -> GenerateRadarChartUseCase:
    return GenerateRadarChartUseCase(survey_repo=get_survey_repository())


def get_bar_chart_use_case() -> GenerateBarChartUseCase:
    return GenerateBarChartUseCase(survey_repo=get_survey_repository())


def get_distribution_use_case() -> GenerateDistributionUseCase:
    return GenerateDistributionUseCase(survey_repo=get_survey_repository())
