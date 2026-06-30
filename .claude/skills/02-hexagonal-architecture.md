# 02 · Arquitectura hexagonal

- `domain/`: núcleo puro (entidades, value objects, puertos, reglas, servicios). Sin dependencias externas.
- `application/`: casos de uso que orquestan el dominio; reciben puertos por constructor.
- `infrastructure/`: adaptadores concretos que implementan los puertos de salida.
- `api/`: rutas FastAPI, middleware y templates.
- `config/dependencies.py`: composition root (conecta puertos con adaptadores).

**Regla de dependencias:** todo apunta hacia el dominio.
