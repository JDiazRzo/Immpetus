"""Punto de entrada de la API. Registrar aquí los routers (ver docs/CONTRATO_API.md)."""
from fastapi import FastAPI

app = FastAPI(title="Immpetus · API de selección", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
