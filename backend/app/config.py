"""Configuración desde variables de entorno (.env). Nunca poner secretos en el código."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:54322/postgres"
    max_pdf_mb: int = 5
    cors_origins: str = "http://localhost:3000"
    drive_root_folder_id: str = ""  # vacío = Drive simulado (solo desarrollo)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
