# -*- coding: utf-8 -*-
"""Fija/restablece la contraseña de un usuario existente en Supabase Auth.

Útil para establecer una contraseña conocida a un usuario ya creado (p. ej.
admin@utpl.edu.ec) y poder iniciar sesión.

Uso (desde el directorio del proyecto, con el .env completado):
    .\.venv\Scripts\python.exe scripts\set_password.py correo@utpl.edu.ec "NuevaClave#2026"
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print('Uso: python scripts\\set_password.py <email> "<nueva_contraseña>"')
        return 2
    email = argv[1].strip().lower()
    password = argv[2]
    if len(password) < 6:
        print("[X] La contraseña debe tener al menos 6 caracteres.")
        return 1

    from config.dependencies import get_client

    db = get_client()
    resp = db.auth.admin.list_users()
    users = resp if isinstance(resp, list) else getattr(resp, "users", [])
    match = next((u for u in users if getattr(u, "email", "").lower() == email), None)
    if match is None:
        print(f"[X] No existe un usuario de Auth con el correo '{email}'.")
        return 1

    db.auth.admin.update_user_by_id(match.id, {"password": password})
    print(f"[OK] Contraseña actualizada para {email}.")
    print("    Ahora puedes iniciar sesión en /login con ese correo y contraseña.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
