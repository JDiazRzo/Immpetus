from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.common import EstadoCandidato, Modalidad

Rol = Literal["analista", "lider", "gerencia"]
Canal = Literal["web", "correo"]
TipoEvento = Literal[
    "postulacion_recibida",
    "hv_guardada",
    "calificacion_ia",
    "calificacion_analista",
    "cambio_estado",
]


class GoogleLogin(BaseModel):
    id_token: str = Field(min_length=1)


class UsuarioAdmin(BaseModel):
    id: UUID
    correo: str
    nombre: str
    rol: Rol


# ---------- Vacantes ----------
class CriterioInput(BaseModel):
    """CriterioAdmin de entrada (sección 5.7): con id de habilidad y peso."""

    habilidad_id: UUID
    obligatoria: bool = False
    peso: int = Field(default=1, ge=1, le=5)


class CriterioAdmin(BaseModel):
    habilidad_id: UUID
    habilidad: str
    obligatoria: bool
    peso: int


class VacanteInput(BaseModel):
    cargo: str = Field(min_length=3, max_length=150)
    cliente: str | None = None
    ciudad: str = Field(min_length=2, max_length=100)
    modalidad: Modalidad
    modalidad_detalle: str | None = None
    jornada: str | None = None
    salario_texto: str | None = None
    descripcion: str | None = None
    responsabilidades: list[str] = []
    urgente: bool = False
    activa: bool = False
    criterios: list[CriterioInput] = []

    @field_validator("responsabilidades")
    @classmethod
    def _sin_vacias(cls, v: list[str]) -> list[str]:
        return [r.strip() for r in v if r.strip()]


class VacanteUpdate(BaseModel):
    """PATCH parcial: solo se aplican los campos enviados."""

    cargo: str | None = Field(default=None, min_length=3, max_length=150)
    cliente: str | None = None
    ciudad: str | None = Field(default=None, min_length=2, max_length=100)
    modalidad: Modalidad | None = None
    modalidad_detalle: str | None = None
    jornada: str | None = None
    salario_texto: str | None = None
    descripcion: str | None = None
    responsabilidades: list[str] | None = None
    urgente: bool | None = None
    activa: bool | None = None
    criterios: list[CriterioInput] | None = None


class VacanteAdmin(BaseModel):
    id: UUID
    codigo: str
    slug: str
    cargo: str
    cliente: str | None
    ciudad: str
    modalidad: Modalidad
    modalidad_detalle: str | None
    jornada: str | None
    salario_texto: str | None
    descripcion: str | None
    responsabilidades: list[str]
    urgente: bool
    activa: bool
    publicada_en: datetime | None
    criterios: list[CriterioAdmin]


class ResumenVacante(BaseModel):
    recibidas: int
    nota_4_5: int
    reserva: int
    por_validar: int
    entrevista: int


# ---------- Candidatos ----------
class HabilidadCandidato(BaseModel):
    nombre: str
    coincide: bool


class CandidatoLista(BaseModel):
    id: UUID
    vacante_id: UUID
    nombre: str
    correo: str
    celular: str | None
    canal: Canal
    drive_url: str | None
    archivo_nombre: str | None
    nota: int | None
    nota_validada: bool
    validada_por: str | None
    estado: EstadoCandidato
    habilidades: list[HabilidadCandidato]
    creado_en: datetime


class EventoHistorial(BaseModel):
    fecha: datetime
    evento: TipoEvento
    detalle: str
    usuario: str | None


class CandidatoDetalle(CandidatoLista):
    resumen_ia: str | None
    matriz: dict[str, Any] | None
    historial: list[EventoHistorial]


class CambioEstado(BaseModel):
    estado: EstadoCandidato
    observacion: str | None = Field(default=None, max_length=500)


class CorreccionNota(BaseModel):
    nota: int = Field(ge=1, le=5)
    motivo: str = Field(min_length=5, max_length=500)

    @field_validator("motivo")
    @classmethod
    def _motivo(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("El motivo es obligatorio.")
        return v


class HabilidadOut(BaseModel):
    id: UUID
    nombre: str
    categoria: str


class AsignarVacante(BaseModel):
    vacante_id: UUID


class CorreoSinAsignarOut(BaseModel):
    id: UUID
    remitente: str
    asunto: str | None
    archivo_nombre: str
    recibido_en: datetime


class ReporteInput(BaseModel):
    destinatarios: list[EmailStr] = Field(min_length=1, max_length=10)


class ReporteEnviado(BaseModel):
    enviado: bool
