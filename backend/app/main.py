"""Punto de entrada de la API (ver docs/CONTRATO_API.md)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, postulaciones, vacantes
from app.config import get_settings
from app.errors import register_error_handlers

app = FastAPI(title="Immpetus · API de selección", version="0.3.0")

# En local el rewrite de Next mantiene el mismo origen; CORS queda por si se llama directo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)
app.include_router(vacantes.router)
app.include_router(postulaciones.router)
app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
