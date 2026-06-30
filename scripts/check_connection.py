# -*- coding: utf-8 -*-
"""Verifica la conexión a Supabase y que las tablas existan.

Uso (desde el directorio del proyecto, con el .env ya completado):
    .\.venv\Scripts\python.exe scripts\check_connection.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    try:
        from config.settings import get_settings
        settings = get_settings()
    except Exception as exc:  # noqa: BLE001
        print("[X] No se pudo leer el .env:", exc)
        print("    Revisa que C:\\Users\\User\\AppTesis\\.env tenga todas las variables.")
        return 1

    if "TU-PROYECTO" in settings.SUPABASE_URL or "TU_" in settings.SUPABASE_SERVICE_KEY:
        print("[X] El .env todavía tiene valores de ejemplo.")
        print("    Reemplaza SUPABASE_URL / SUPABASE_KEY / SUPABASE_SERVICE_KEY con los reales.")
        return 1

    try:
        from config.dependencies import get_client
        client = get_client()
    except Exception as exc:  # noqa: BLE001
        print("[X] No se pudo crear el cliente Supabase:", exc)
        print("    Suele significar que la SUPABASE_SERVICE_KEY no es un JWT válido.")
        return 1

    print("[OK] Cliente Supabase creado. URL:", settings.SUPABASE_URL)

    for tabla in ("empresas", "usuarios", "roles", "competencias", "preguntas",
                  "encuestas", "respuestas_encuesta", "resultados_competencia"):
        try:
            client.table(tabla).select("*", count="exact").limit(1).execute()
            print(f"[OK] Tabla '{tabla}' accesible.")
        except Exception as exc:  # noqa: BLE001
            print(f"[X] Tabla '{tabla}' no accesible:", exc)
            print("    ¿Ejecutaste tu esquema (nuevo_schema.sql) en el SQL Editor de Supabase?")
            return 1

    print("\n[OK] Todo en orden: conexión y tablas verificadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
