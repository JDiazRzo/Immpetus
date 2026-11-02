"""Punto de entrada de la API (ver docs/CONTRATO_API.md)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, admin_contactos, admin_gestion, auth, contacto, postulaciones, vacantes
from app.config import get_settings
from app.errors import register_error_handlers
from app.limiter import limiter
from app.middleware import LimiteTamanoMiddleware

app = FastAPI(title="Immpetus · API de selección", version="0.5.0")

app.state.limiter = limiter  # lo exige slowapi
# Se agrega ANTES que CORS para quedar por dentro y que un 413 también lleve los encabezados CORS.
app.add_middleware(LimiteTamanoMiddleware)

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
app.include_router(contacto.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(admin_gestion.router)
app.include_router(admin_contactos.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
