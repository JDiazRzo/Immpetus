# Backend · FastAPI + integraciones

| Carpeta | Dueño | Qué va |
|---|---|---|
| `app/api/` | Backend | Routers públicos (`/api`) y del centro de mando (`/api/admin`) |
| `app/models/` | Backend | Esquemas Pydantic, idénticos a `docs/CONTRATO_API.md` |
| `app/services/` | Backend | Reglas de negocio. `estados.py` es el ÚNICO que cambia estados |
| `app/integraciones/` | Integraciones | `gmail.py`, `drive.py`, `ia.py` (ver sección 3 del contrato) |
| `tests/` | Ambos | Pruebas con `pytest` (sin llamar a Google: usar datos falsos) |

## Correr

```bash
uv sync                                   # instala exactamente lo de uv.lock
uv run uvicorn app.main:app --reload      # http://localhost:8000/health
uv run pytest                             # pruebas
uv run ruff check . && uv run ruff format .
```

O con Docker desde la raíz: `docker compose up api`.

Agregar una dependencia: `uv add <paquete>` y subir `pyproject.toml` + `uv.lock` en el mismo PR.
