-- ============================================================
--  001_initial_schema.sql
--  Esquema inicial — Plataforma DigComp 2.2 (Plan Maestro / AppTesis)
--  Base de datos: Supabase (PostgreSQL 15+)
--
--  Tablas: users, verification_codes, survey_responses
--  Escala de puntajes DigComp 2.2: 1.0 – 8.0
-- ============================================================

-- ------------------------------------------------------------
--  Función auxiliar: actualiza updated_at automáticamente
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
--  TABLA: users
-- ============================================================
CREATE TABLE IF NOT EXISTS public.users (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email                 VARCHAR(255) UNIQUE NOT NULL,
    hashed_password       VARCHAR(255) NOT NULL,
    full_name             VARCHAR(255) NOT NULL,
    role                  VARCHAR(50)  NOT NULL DEFAULT 'VIEWER'
                              CHECK (role IN ('ADMIN', 'RESEARCHER', 'VIEWER')),
    status                VARCHAR(50)  NOT NULL DEFAULT 'PENDING_VERIFICATION'
                              CHECK (status IN ('PENDING_VERIFICATION', 'ACTIVE', 'LOCKED', 'INACTIVE')),
    failed_login_attempts INTEGER      NOT NULL DEFAULT 0,
    locked_at             TIMESTAMPTZ,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users (email);

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.users IS
    'Usuarios de la plataforma. La contraseña se almacena hasheada con bcrypt (rounds=12).';


-- ============================================================
--  TABLA: verification_codes
-- ============================================================
CREATE TABLE IF NOT EXISTS public.verification_codes (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID         NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    code_hash    VARCHAR(255) NOT NULL,
    purpose      VARCHAR(50)  NOT NULL
                     CHECK (purpose IN ('EMAIL_VERIFICATION', 'PASSWORD_RESET', 'ACCOUNT_UNLOCK')),
    attempts     INTEGER      NOT NULL DEFAULT 0,
    max_attempts INTEGER      NOT NULL DEFAULT 3,
    expires_at   TIMESTAMPTZ  NOT NULL,
    used_at      TIMESTAMPTZ,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verification_user    ON public.verification_codes (user_id);
CREATE INDEX IF NOT EXISTS idx_verification_purpose ON public.verification_codes (user_id, purpose);
CREATE INDEX IF NOT EXISTS idx_verification_active  ON public.verification_codes (user_id, purpose, used_at);

COMMENT ON TABLE public.verification_codes IS
    'Códigos de verificación de 6 dígitos (hasheados) para email, reset y desbloqueo. '
    'Expiran en 15 minutos y permiten un máximo de 3 intentos.';


-- ============================================================
--  TABLA: survey_responses
-- ============================================================
CREATE TABLE IF NOT EXISTS public.survey_responses (
    id                         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by                UUID         NOT NULL REFERENCES public.users(id),
    upload_batch_id            UUID         NOT NULL,
    respondent_age_range       VARCHAR(100),
    respondent_gender          VARCHAR(50),
    respondent_province        VARCHAR(100),
    respondent_education_level VARCHAR(100),
    respondent_sector          VARCHAR(100),
    comp_4_1_score             DECIMAL(3,1) NOT NULL CHECK (comp_4_1_score BETWEEN 1.0 AND 8.0),
    comp_4_2_score             DECIMAL(3,1) NOT NULL CHECK (comp_4_2_score BETWEEN 1.0 AND 8.0),
    comp_4_3_score             DECIMAL(3,1) NOT NULL CHECK (comp_4_3_score BETWEEN 1.0 AND 8.0),
    comp_4_4_score             DECIMAL(3,1) NOT NULL CHECK (comp_4_4_score BETWEEN 1.0 AND 8.0),
    raw_data                   JSONB,
    created_at                 TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_survey_uploaded_by ON public.survey_responses (uploaded_by);
CREATE INDEX IF NOT EXISTS idx_survey_batch       ON public.survey_responses (upload_batch_id);
CREATE INDEX IF NOT EXISTS idx_survey_age         ON public.survey_responses (respondent_age_range);
CREATE INDEX IF NOT EXISTS idx_survey_gender      ON public.survey_responses (respondent_gender);
CREATE INDEX IF NOT EXISTS idx_survey_province    ON public.survey_responses (respondent_province);
CREATE INDEX IF NOT EXISTS idx_survey_scores      ON public.survey_responses
    (comp_4_1_score, comp_4_2_score, comp_4_3_score, comp_4_4_score);

COMMENT ON TABLE public.survey_responses IS
    'Respuestas de la encuesta DigComp 2.2 (Área 4). Una fila por encuestado. '
    'raw_data conserva la fila original del CSV de ArcGIS Survey123.';


-- ============================================================
--  ROW LEVEL SECURITY (RLS)
--  El backend usa la SERVICE_KEY (bypassa RLS); estas políticas
--  protegen el acceso con la anon key / usuarios autenticados.
-- ============================================================
ALTER TABLE public.users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.survey_responses   ENABLE ROW LEVEL SECURITY;

-- Cada usuario autenticado puede leer su propia fila.
CREATE POLICY "users_self_select"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

-- Respuestas de encuesta: lectura para usuarios autenticados.
CREATE POLICY "survey_responses_authenticated_select"
    ON public.survey_responses FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Nota: las operaciones de escritura las realiza el backend con SERVICE_KEY,
-- que omite RLS. No se exponen políticas de escritura a la anon key.
