# -*- coding: utf-8 -*-
"""Lanzador de la app.
- Local:  lee .env por ruta absoluta, escucha en 127.0.0.1:8012
- Render: variables de entorno ya están en el proceso; usa HOST/PORT del entorno.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")   # no falla si el archivo no existe (producción)

import main  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    # En plataformas como Render la variable PORT viene definida por el entorno y
    # el servidor debe escuchar en 0.0.0.0 para ser accesible desde fuera. En local
    # (sin PORT) se mantiene 127.0.0.1 salvo que se indique HOST explicitamente.
    default_host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    host = os.environ.get("HOST", default_host)
    port = int(os.environ.get("PORT", 8012))
    uvicorn.run(main.app, host=host, port=port, log_level="info")
