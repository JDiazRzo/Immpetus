"""Tablas de la base (espejo de supabase/migrations). No crea ni migra: el esquema vive en SQL.

Los tipos tienen variante SQLite solo para poder correr los tests sin Postgres.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, SmallInteger, Text, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

ESTADOS = ("nuevo", "entrevista", "reserva", "por_validar", "no_apto", "contratado")
MODALIDADES = ("presencial", "hibrido", "remoto")
CANALES = ("web", "correo")
ROLES = ("analista", "lider", "gerencia")
ORIGENES = ("ia", "analista")
CATEGORIAS = ("tecnica", "blanda", "idioma", "herramienta", "certificacion")


def _ahora() -> datetime:
    return datetime.now(UTC)


def _enum(nombre: str, valores: tuple[str, ...]) -> Enum:
    return Enum(*valores, name=nombre, create_type=False, native_enum=True)


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    correo: Mapped[str] = mapped_column(Text, unique=True)
    nombre: Mapped[str] = mapped_column(Text)
    rol: Mapped[str] = mapped_column(_enum("rol_usuario", ROLES))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Vacante(Base):
    __tablename__ = "vacantes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(Text, unique=True)
    slug: Mapped[str] = mapped_column(Text, unique=True)
    cargo: Mapped[str] = mapped_column(Text)
    cliente: Mapped[str | None] = mapped_column(Text)
    ciudad: Mapped[str] = mapped_column(Text)
    modalidad: Mapped[str] = mapped_column(_enum("modalidad_trabajo", MODALIDADES))
    modalidad_detalle: Mapped[str | None] = mapped_column(Text)
    jornada: Mapped[str | None] = mapped_column(Text)
    salario_texto: Mapped[str | None] = mapped_column(Text)
    descripcion: Mapped[str | None] = mapped_column(Text)
    responsabilidades: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON(), "sqlite"), default=list
    )
    urgente: Mapped[bool] = mapped_column(Boolean, default=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=False)
    drive_folder_id: Mapped[str | None] = mapped_column(Text)
    creada_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_ahora, server_default=func.now()
    )
    publicada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Habilidad(Base):
    __tablename__ = "habilidades"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(Text, unique=True)
    categoria: Mapped[str] = mapped_column(_enum("categoria_habilidad", CATEGORIAS))


class VacanteHabilidad(Base):
    __tablename__ = "vacante_habilidades"
    vacante_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vacantes.id"), primary_key=True)
    habilidad_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("habilidades.id"), primary_key=True)
    obligatoria: Mapped[bool] = mapped_column(Boolean, default=False)
    peso: Mapped[int] = mapped_column(SmallInteger, default=1)


class Candidato(Base):
    __tablename__ = "candidatos"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    vacante_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vacantes.id"))
    nombre: Mapped[str] = mapped_column(Text)
    correo: Mapped[str] = mapped_column(Text)
    celular: Mapped[str | None] = mapped_column(Text)
    canal: Mapped[str] = mapped_column(_enum("canal_postulacion", CANALES))
    drive_file_id: Mapped[str | None] = mapped_column(Text)
    drive_url: Mapped[str | None] = mapped_column(Text)
    archivo_nombre: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(_enum("estado_candidato", ESTADOS), default="nuevo")
    autorizacion_datos: Mapped[bool] = mapped_column(Boolean)
    autorizacion_fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    autorizacion_version: Mapped[str] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_ahora, server_default=func.now()
    )
    anonimizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Estado(Base):
    """Historial de estados: SOLO inserciones (regla 2)."""

    __tablename__ = "estados"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidato_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidatos.id"))
    estado: Mapped[str] = mapped_column(_enum("estado_candidato", ESTADOS))
    validado_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    observacion: Mapped[str | None] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_ahora, server_default=func.now()
    )


class Calificacion(Base):
    """Calificaciones (IA o corrección del analista): SOLO inserciones."""

    __tablename__ = "calificaciones"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidato_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidatos.id"))
    nota: Mapped[int] = mapped_column(SmallInteger)
    resumen: Mapped[str | None] = mapped_column(Text)
    matriz: Mapped[dict | None] = mapped_column(JSONB().with_variant(JSON(), "sqlite"))
    origen: Mapped[str] = mapped_column(_enum("origen_dato", ORIGENES))
    modelo_ia: Mapped[str | None] = mapped_column(Text)
    motivo: Mapped[str | None] = mapped_column(Text)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_ahora, server_default=func.now()
    )


class CandidatoHabilidad(Base):
    __tablename__ = "candidato_habilidades"
    candidato_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidatos.id"), primary_key=True)
    habilidad_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("habilidades.id"), primary_key=True)
    origen: Mapped[str] = mapped_column(_enum("origen_dato", ORIGENES), default="ia")


class CorreoSinAsignar(Base):
    """HV que llegó por correo y no se pudo asociar a una vacante (la llena el job de ingesta)."""

    __tablename__ = "correos_sin_asignar"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    gmail_id: Mapped[str] = mapped_column(Text, unique=True)
    remitente: Mapped[str] = mapped_column(Text)
    asunto: Mapped[str | None] = mapped_column(Text)
    archivo_nombre: Mapped[str | None] = mapped_column(Text)  # migración 0003
    drive_file_id: Mapped[str | None] = mapped_column(Text)
    recibido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    asignado_a: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("candidatos.id"))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_ahora, server_default=func.now()
    )
