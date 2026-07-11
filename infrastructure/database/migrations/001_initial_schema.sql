-- ============================================================
--  001_initial_schema.sql
--  Esquema real de la plataforma AppTesis - DigComp 2.2 (Area 4: Seguridad)
--  Base de datos: Supabase (PostgreSQL 15+)
--
--  Escala de puntuacion: Likert 0-3 (autoevaluacion) y conocimiento 0-3.
--  Modelo normalizado de 13 tablas + 1 vista de apoyo al dashboard.
--
--  Los nombres de tablas y columnas coinciden EXACTAMENTE con los que usan
--  los adaptadores de infraestructura (ingestion/analisis) contra Supabase.
--  La autenticacion de identidades la gestiona Supabase Auth; la tabla
--  'usuarios' guarda el perfil de aplicacion (rol, empresa, estado).
-- ============================================================

-- ------------------------------------------------------------
--  Funcion auxiliar: actualiza updated_at automaticamente
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
--  ENTIDADES MAESTRAS / CATALOGO
-- ============================================================

-- Empresa / institucion a la que pertenecen los encuestados (UTPL).
CREATE TABLE IF NOT EXISTS public.empresas (
    id_empresa  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre      TEXT         NOT NULL,
    ruc         VARCHAR(13),
    ciudad      TEXT,
    sector      TEXT,
    pais        TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Roles de acceso y sus permisos (RBAC por permiso, en JSON).
CREATE TABLE IF NOT EXISTS public.roles (
    id_rol      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_rol  VARCHAR(50)  NOT NULL,
    descripcion TEXT,
    permisos    JSONB        NOT NULL DEFAULT '[]'::jsonb
);

-- Tipo de pregunta: 1 = Likert (autoevaluacion), 2 = Validacion (conocimiento).
CREATE TABLE IF NOT EXISTS public.tipo_preguntas (
    id_tipo  INTEGER      PRIMARY KEY,
    nombre   VARCHAR(50)  NOT NULL
);

-- Perfil de usuario de la aplicacion (vinculado a Supabase Auth por email/id).
CREATE TABLE IF NOT EXISTS public.usuarios (
    id_usuario  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    id_empresa  UUID         NOT NULL REFERENCES public.empresas(id_empresa) ON DELETE CASCADE,
    nombre      TEXT         NOT NULL,
    email       TEXT         UNIQUE NOT NULL,
    estado      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Competencias DigComp 2.2 del Area 4 (4.1, 4.2, 4.3, 4.4).
CREATE TABLE IF NOT EXISTS public.competencias (
    id_competencia UUID     PRIMARY KEY DEFAULT gen_random_uuid(),
    id_empresa     UUID     NOT NULL REFERENCES public.empresas(id_empresa) ON DELETE CASCADE,
    codigo         VARCHAR(5) NOT NULL,
    nombre         TEXT     NOT NULL,
    descripcion    TEXT
);

-- Tabla de cruce N:M entre usuarios y roles.
CREATE TABLE IF NOT EXISTS public.usuario_rol (
    id_usuario UUID NOT NULL REFERENCES public.usuarios(id_usuario) ON DELETE CASCADE,
    id_rol     UUID NOT NULL REFERENCES public.roles(id_rol)        ON DELETE CASCADE,
    PRIMARY KEY (id_usuario, id_rol)
);


-- ============================================================
--  INSTRUMENTO (preguntas y respuestas correctas)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.preguntas (
    id_pregunta     UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
    id_competencia  UUID       NOT NULL REFERENCES public.competencias(id_competencia) ON DELETE CASCADE,
    id_tipo         INTEGER    NOT NULL REFERENCES public.tipo_preguntas(id_tipo),
    codigo_columna  TEXT       NOT NULL,   -- encabezado exacto de la columna en el CSV
    texto           TEXT,
    orden           INTEGER
);

CREATE TABLE IF NOT EXISTS public.respuestas_correctas (
    id              UUID     PRIMARY KEY DEFAULT gen_random_uuid(),
    id_pregunta     UUID     NOT NULL REFERENCES public.preguntas(id_pregunta) ON DELETE CASCADE,
    letra_correcta  CHAR(1)  NOT NULL
);


-- ============================================================
--  DATOS DE EVALUACION (crecen con cada carga de encuesta)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.encuestas (
    id_encuesta       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    id_empresa        UUID         NOT NULL REFERENCES public.empresas(id_empresa) ON DELETE CASCADE,
    id_usuario        UUID         REFERENCES public.usuarios(id_usuario),
    nombre            TEXT         NOT NULL,
    archivo_origen    TEXT,
    estado            VARCHAR(20)  NOT NULL DEFAULT 'procesando',
    total_respuestas  INTEGER      NOT NULL DEFAULT 0,
    filas_procesadas  INTEGER      NOT NULL DEFAULT 0,
    filas_con_error   INTEGER      NOT NULL DEFAULT 0,
    log_procesamiento JSONB,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.respuestas_encuesta (
    id_respuesta      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    id_encuesta       UUID         NOT NULL REFERENCES public.encuestas(id_encuesta) ON DELETE CASCADE,
    fecha_respuesta   DATE,
    genero            VARCHAR(50),
    genero_otro       TEXT,
    edad_rango        VARCHAR(100),
    origen_id         INTEGER,     -- ObjectID de ArcGIS Survey123
    origen_global_id  TEXT,        -- GlobalID de ArcGIS Survey123
    datos_raw         JSONB        -- fila original completa del CSV
);

CREATE TABLE IF NOT EXISTS public.detalle_respuestas (
    id_detalle    UUID     PRIMARY KEY DEFAULT gen_random_uuid(),
    id_respuesta  UUID     NOT NULL REFERENCES public.respuestas_encuesta(id_respuesta) ON DELETE CASCADE,
    id_pregunta   UUID     NOT NULL REFERENCES public.preguntas(id_pregunta),
    valor_likert  INTEGER,          -- 0-3 para preguntas de autoevaluacion
    valor_texto   TEXT,             -- respuesta textual para preguntas de validacion
    es_correcta   BOOLEAN           -- resultado de la comparacion de conocimiento
);

CREATE TABLE IF NOT EXISTS public.resultados_competencia (
    id_resultado          UUID     PRIMARY KEY DEFAULT gen_random_uuid(),
    id_encuesta           UUID     NOT NULL REFERENCES public.encuestas(id_encuesta) ON DELETE CASCADE,
    id_respuesta          UUID     NOT NULL REFERENCES public.respuestas_encuesta(id_respuesta) ON DELETE CASCADE,
    id_competencia        UUID     NOT NULL REFERENCES public.competencias(id_competencia),
    score_autoevaluacion  NUMERIC(4,2),   -- promedio Likert 0-3
    score_conocimiento    NUMERIC(4,2),   -- (correctas / total) * 3, escala 0-3
    nivel                 VARCHAR(20)     -- Basico | Intermedio | Avanzado | Experto
);


-- ============================================================
--  AUDITORIA
-- ============================================================
CREATE TABLE IF NOT EXISTS public.logs (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tabla_afectada    TEXT,
    accion            TEXT,
    id_registro       UUID,
    datos_anteriores  JSONB,
    datos_nuevos      JSONB,
    fecha             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


-- ============================================================
--  INDICES de apoyo a las consultas del dashboard
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_resp_encuesta       ON public.respuestas_encuesta (id_encuesta);
CREATE INDEX IF NOT EXISTS idx_detalle_respuesta   ON public.detalle_respuestas (id_respuesta);
CREATE INDEX IF NOT EXISTS idx_result_respuesta    ON public.resultados_competencia (id_respuesta);
CREATE INDEX IF NOT EXISTS idx_result_competencia  ON public.resultados_competencia (id_competencia);


-- ============================================================
--  VISTA: v_dashboard_resultados
--  Una fila por (encuestado x competencia) con la demografia y los
--  puntajes ya calculados. Es la unica fuente que consulta el dashboard.
-- ============================================================
CREATE OR REPLACE VIEW public.v_dashboard_resultados AS
SELECT
    rc.id_resultado,
    re.id_respuesta,
    re.genero,
    re.edad_rango,
    c.codigo            AS codigo_competencia,
    c.nombre            AS nombre_competencia,
    rc.score_autoevaluacion,
    rc.score_conocimiento,
    rc.nivel
FROM public.resultados_competencia rc
JOIN public.respuestas_encuesta re ON re.id_respuesta = rc.id_respuesta
JOIN public.competencias c         ON c.id_competencia = rc.id_competencia;
