# AppTesis — Evaluación de Competencias Digitales DigComp 2.2 (Área 4)

Plataforma web para evaluar competencias digitales del **Área 4 (Seguridad)** del
marco **DigComp 2.2** (competencias 4.1 a 4.4), a partir de datos exportados en CSV
desde **ArcGIS Survey123**.

## Competencias evaluadas (Área 4)

| Código | Competencia |
|--------|-------------|
| 4.1 | Protección de dispositivos |
| 4.2 | Protección de datos personales y privacidad |
| 4.3 | Protección de la salud y el bienestar |
| 4.4 | Protección del medio ambiente |

## Stack tecnológico

- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Datos:** Pandas, NumPy
- **Persistencia:** Supabase (PostgreSQL 15+)
- **Frontend:** Jinja2, HTMX, Tailwind CSS, Plotly.js, Alpine.js
- **Seguridad:** bcrypt (rounds=12)

## Arquitectura hexagonal (puertos y adaptadores)

El proyecto separa el **núcleo de negocio** de los **detalles técnicos** mediante
puertos (interfaces) y adaptadores (implementaciones concretas).

```
domain/          → Núcleo puro: entidades, value objects, puertos, reglas, servicios.
                   No depende de NADA externo (ni FastAPI, ni Supabase, ni bcrypt).
application/     → Casos de uso que orquestan el dominio. Reciben puertos por constructor.
infrastructure/  → Adaptadores concretos (Supabase, bcrypt, SMTP, CSV) que implementan
                   los puertos de salida del dominio.
api/             → Capa de interfaz: rutas HTTP (FastAPI), middleware y templates Jinja2.
config/          → Settings (.env) e inyección de dependencias (composition root).
```

### Regla de dependencias

Las dependencias **siempre apuntan hacia el dominio**. El dominio define interfaces
(`ports`) y la infraestructura las implementa. La conexión entre ambos se realiza en
`config/dependencies.py` (composition root).

## Instalación

```bash
py -3.11 -m venv .venv          # Python 3.11 (las versiones fijadas tienen wheels)
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # y completar valores
```

> **Nota (redes con proxy/TLS-inspection):** si `pip install` falla con
> `SSL: CERTIFICATE_VERIFY_FAILED`, añade
> `--trusted-host pypi.org --trusted-host files.pythonhosted.org`.

## Ejecución

```bash
python run_app.py          # carga el .env y arranca en http://localhost:8012
# o
uvicorn main:app --reload  # usa el .env del directorio actual
```

## Acceso, roles y permisos (Supabase Auth)

El login usa **Supabase Auth** (`auth.users`). El rol y los permisos se resuelven
desde las tablas `usuarios` / `usuario_rol` / `roles`. El acceso a cada función se
controla por **permiso** (RBAC):

| Permiso | Habilita | Roles |
|---------|----------|-------|
| `ver_dashboard` | Ver el dashboard | administrador, analista, consultor |
| `cargar_csv` | Subir/borrar encuestas (`/admin/encuestas`) | administrador, analista |
| `gestionar_usuarios` | Crear/activar/borrar usuarios (`/admin/usuarios`) | administrador |

### Primer ingreso (bootstrap)

Fija la contraseña de un usuario ya existente en tu base (p. ej. el administrador) y
entra en `/login`:

```powershell
python scripts\set_password.py admin@utpl.edu.ec "TuClave#2026"
```

Luego, como administrador, crea más usuarios (con su rol) desde **`/admin/usuarios`**.

## Tests

```bash
pytest                 # suite completa (dominio, aplicación, infraestructura)
pytest --cov           # con cobertura
```

Los tests no requieren conexión a Supabase: usan repositorios y servicios falsos
en memoria (mocks de los puertos).

## Base de datos

Ejecuta la migración `infrastructure/database/migrations/001_initial_schema.sql`
en tu proyecto Supabase para crear las tablas `users`, `verification_codes` y
`survey_responses`.

## Branding UTPL

- Azul `#003B71` · Naranja `#F39C12` · Verde `#27AE60` · Rojo `#E74C3C`
