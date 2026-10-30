from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Servicio = Literal[
    "adquisicion_talento",
    "talento_bpo",
    "gestion_estrategica",
    "formacion_liderazgo",
    "procesos",
    "otro",
]


class ContactoInput(BaseModel):
    """Formulario público de contacto. Cualquier campo extra se rechaza (extra="forbid")."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=3, max_length=120)
    empresa: str | None = Field(default=None, max_length=160)
    correo: EmailStr
    telefono: str | None = Field(default=None, max_length=30)
    servicio: Servicio | None = None
    mensaje: str = Field(min_length=10, max_length=2000)
    autorizacion_datos: bool

    @field_validator("empresa", "telefono", mode="before")
    @classmethod
    def _vacio_es_nulo(cls, v: object) -> object:
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("correo")
    @classmethod
    def _correo_largo(cls, v: str) -> str:
        if len(v) > 254:
            raise ValueError("El correo es demasiado largo.")
        return v.lower()


class ContactoCreado(BaseModel):
    id: UUID
