from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.common import Modalidad


class VacanteResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str
    cargo: str
    ciudad: str
    modalidad: Modalidad
    modalidad_detalle: str | None
    jornada: str | None
    salario_texto: str | None
    urgente: bool
    publicada_en: datetime | None


class CriterioPublico(BaseModel):
    """Público: nunca expone IDs de habilidades ni pesos (sección 5.7)."""

    habilidad: str
    obligatoria: bool


class VacanteDetalle(BaseModel):
    id: UUID
    slug: str
    cargo: str
    ciudad: str
    modalidad: Modalidad
    modalidad_detalle: str | None
    jornada: str | None
    salario_texto: str | None
    descripcion: str | None
    responsabilidades: list[str]
    criterios: list[CriterioPublico]
    publicada_en: datetime | None  # el frontend lo usa para JobPosting (SEO)
