"""Formulario de contacto de empresas (landing) y su bandeja en el centro de mando."""

import logging
import uuid
from collections.abc import Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import not_found, validation_error
from app.models.admin import ContactoAdmin
from app.models.contacto import ContactoInput
from app.orm import Contacto

log = logging.getLogger("immpetus.contacto")


def crear(db: Session, datos: ContactoInput) -> Contacto:
    if not datos.autorizacion_datos:
        raise validation_error(
            "Debes autorizar el tratamiento de tus datos personales para contactarnos.",
            "autorizacion_datos",
        )
    contacto = Contacto(
        nombre=datos.nombre,
        empresa=datos.empresa,
        correo=datos.correo,
        telefono=datos.telefono,
        servicio=datos.servicio,
        mensaje=datos.mensaje,
        autorizacion_datos=True,
    )
    db.add(contacto)
    db.commit()
    return contacto


def avisar(enviar: Callable[[dict], None], contacto: Contacto) -> None:
    """Aviso al correo comercial. Nunca rompe el formulario: ya quedó guardado."""
    try:
        enviar(
            {
                "nombre": contacto.nombre,
                "empresa": contacto.empresa,
                "correo": contacto.correo,
                "telefono": contacto.telefono,
                "servicio": contacto.servicio,
                "mensaje": contacto.mensaje,
            }
        )
    except Exception:  # sin datos personales en el log
        log.exception("No se pudo enviar el aviso de contacto (id=%s).", contacto.id)


def listar(
    db: Session, atendido: bool | None, page: int, page_size: int
) -> tuple[list[ContactoAdmin], int]:
    filtros = [] if atendido is None else [Contacto.atendido.is_(atendido)]
    total = db.scalar(select(func.count()).select_from(Contacto).where(*filtros)) or 0
    filas = db.scalars(
        select(Contacto)
        .where(*filtros)
        .order_by(Contacto.creado_en.desc(), Contacto.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    return [ContactoAdmin.model_validate(c) for c in filas], total


def marcar_atendido(db: Session, contacto_id: uuid.UUID, atendido: bool) -> ContactoAdmin:
    c = db.get(Contacto, contacto_id)
    if c is None:
        raise not_found("El contacto no existe.")
    c.atendido = atendido
    db.commit()
    return ContactoAdmin.model_validate(c)
