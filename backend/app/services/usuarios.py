"""Gestión de usuarios del centro de mando (solo líder). Nunca se borran: se desactivan."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import AppError, not_found, validation_error
from app.models.admin import UsuarioCrear, UsuarioUpdate
from app.orm import Usuario

SIN_LIDER = "Debe quedar al menos un líder activo. Asigne otro líder antes."
YA_EXISTE = "Este correo ya tiene acceso. Si está desactivado, actívelo."


def listar(db: Session) -> list[Usuario]:
    return list(db.scalars(select(Usuario).order_by(Usuario.activo.desc(), Usuario.nombre)))


def crear(db: Session, datos: UsuarioCrear) -> Usuario:
    dominio = get_settings().allowed_email_domain.lower()
    if not datos.correo.endswith(f"@{dominio}"):
        raise validation_error(f"El correo debe terminar en @{dominio}.", "correo")
    if db.scalar(select(Usuario.id).where(func.lower(Usuario.correo) == datos.correo)):
        raise AppError(409, "CONFLICT", YA_EXISTE)
    usuario = Usuario(correo=datos.correo, nombre=datos.nombre, rol=datos.rol, activo=True)
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError as exc:  # dos peticiones a la vez con el mismo correo
        db.rollback()
        raise AppError(409, "CONFLICT", YA_EXISTE) from exc
    return usuario


def _otros_lideres_activos(db: Session, usuario_id: uuid.UUID) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Usuario)
            .where(Usuario.rol == "lider", Usuario.activo.is_(True), Usuario.id != usuario_id)
        )
        or 0
    )


def actualizar(
    db: Session, usuario_id: uuid.UUID, cambios: UsuarioUpdate, actor: Usuario
) -> Usuario:
    u = db.get(Usuario, usuario_id)
    if u is None:
        raise not_found("El usuario no existe.")
    datos = cambios.model_dump(exclude_unset=True)
    nuevo_rol, nuevo_activo = datos.get("rol", u.rol), datos.get("activo", u.activo)

    if u.rol == "lider" and u.activo and (nuevo_rol != "lider" or not nuevo_activo):
        if _otros_lideres_activos(db, u.id) == 0:
            raise AppError(409, "CONFLICT", SIN_LIDER)

    if (nuevo_rol, nuevo_activo) == (u.rol, u.activo):
        return u  # nada que cambiar: no se ensucia la trazabilidad
    u.rol, u.activo = nuevo_rol, nuevo_activo
    u.actualizado_en, u.actualizado_por = datetime.now(UTC), actor.id
    try:
        db.commit()
    except DBAPIError as exc:
        db.rollback()
        # El trigger de la base (0007) es la última barrera si dos líderes se quitan a la vez.
        if "al menos un líder activo" in str(exc.orig):
            raise AppError(409, "CONFLICT", SIN_LIDER) from exc
        raise
    return u
