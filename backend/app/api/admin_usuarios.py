"""Gestión de usuarios del centro de mando. SOLO líder (tabla 2.0 del contrato). Sin DELETE."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import requiere_rol
from app.db import get_db
from app.models.admin import UsuarioCrear, UsuarioGestion, UsuarioUpdate
from app.orm import Usuario
from app.services import usuarios

router = APIRouter(
    prefix="/api/admin/usuarios",
    tags=["usuarios (solo líder)"],
    dependencies=[Depends(requiere_rol("lider"))],
)
Db = Annotated[Session, Depends(get_db)]
Lider = Annotated[Usuario, Depends(requiere_rol("lider"))]


@router.get("", response_model=list[UsuarioGestion])
def listar_usuarios(db: Db) -> list[Usuario]:
    return usuarios.listar(db)


@router.post("", response_model=UsuarioGestion, status_code=201)
def crear_usuario(datos: UsuarioCrear, db: Db) -> Usuario:
    return usuarios.crear(db, datos)


@router.patch("/{usuario_id}", response_model=UsuarioGestion)
def actualizar_usuario(usuario_id: UUID, cambios: UsuarioUpdate, db: Db, lider: Lider) -> Usuario:
    return usuarios.actualizar(db, usuario_id, cambios, lider)
