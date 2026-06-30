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
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8012))
    uvicorn.run(main.app, host=host, port=port, log_level="info")
