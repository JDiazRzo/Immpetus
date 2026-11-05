"""Conexión a PostgreSQL con SQLAlchemy. Solo por DATABASE_URL (regla 7 de CLAUDE.md)."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def get_db() -> Iterator[Session]:
    with sessionmaker(bind=get_engine(), expire_on_commit=False)() as session:
        yield session


# Hosts que se consideran "esta máquina" (incluye el host visto desde un contenedor).
_HOSTS_LOCALES = {None, "", "localhost", "127.0.0.1", "::1", "host.docker.internal"}


def es_base_local(url: str) -> bool:
    """¿La URL apunta a una base de ESTA máquina? Freno antes de escribir datos de prueba."""
    return make_url(url).host in _HOSTS_LOCALES


def host_de(url: str) -> str:
    """Solo el host (nunca usuario ni contraseña) para poder mostrarlo en mensajes."""
    return str(make_url(url).host or "socket local")
