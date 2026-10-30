"""Correos sin asignar: HV que llegaron por correo sin código de vacante (contrato 5.6)."""

import uuid
from collections.abc import Callable
from email.utils import parseaddr

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import AppError, not_found, validation_error
from app.models.admin import CandidatoLista, CorreoSinAsignarOut
from app.orm import Candidato, CorreoSinAsignar, Usuario, Vacante
from app.services import candidatos as cand
from app.services import estados


def listar(db: Session, page: int, page_size: int) -> tuple[list[CorreoSinAsignarOut], int]:
    pendientes = select(CorreoSinAsignar).where(CorreoSinAsignar.asignado_a.is_(None))
    total = db.scalar(select(func.count()).select_from(pendientes.subquery())) or 0
    filas = db.scalars(
        pendientes.order_by(CorreoSinAsignar.recibido_en.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    items = [
        CorreoSinAsignarOut(
            id=m.id,
            remitente=m.remitente,
            asunto=m.asunto,
            archivo_nombre=m.archivo_nombre or "hoja_de_vida.pdf",
            recibido_en=m.recibido_en,
        )
        for m in filas
    ]
    return items, total


def asignar(
    db: Session,
    correo_id: uuid.UUID,
    vacante_id: uuid.UUID,
    usuario: Usuario,
    mover_hv: Callable,
) -> CandidatoLista:
    m = db.get(CorreoSinAsignar, correo_id)
    if m is None or m.asignado_a is not None:
        raise not_found("El correo ya fue asignado o no existe.")
    vacante = db.get(Vacante, vacante_id)
    if vacante is None:
        raise not_found("La vacante no existe.")
    if not m.drive_file_id:
        raise AppError(409, "CONFLICT", "Este correo no tiene un PDF guardado.")

    nombre, correo = parseaddr(m.remitente)
    correo = correo.strip().lower()
    if "@" not in correo:
        raise validation_error("El remitente no tiene un correo válido.", "remitente")
    nombre = nombre.strip() or correo.split("@")[0]

    if cand.existe_postulacion_activa(db, vacante.id, correo):
        raise AppError(409, "CONFLICT", "Esa persona ya está postulada a esa vacante.")

    try:
        subido = mover_hv(m.drive_file_id, vacante)  # a la carpeta de la vacante
    except Exception as exc:  # no registrar datos del candidato en logs
        raise AppError(
            502, "STORAGE_ERROR", "No pudimos mover la hoja de vida en Drive. Intenta de nuevo."
        ) from exc

    candidato = Candidato(
        vacante_id=vacante.id,
        nombre=nombre,
        correo=correo,
        celular=None,
        canal="correo",
        drive_file_id=subido.id,
        drive_url=subido.url,
        archivo_nombre=m.archivo_nombre or "hoja_de_vida.pdf",
        autorizacion_datos=True,
        autorizacion_fecha=m.recibido_en,
        autorizacion_version="correo-1.0",  # autorización por conducta inequívoca [VERIFICAR legal]
    )
    db.add(candidato)
    db.flush()
    estados.registrar_estado_inicial(
        db,
        candidato,
        "nuevo",
        usuario_id=usuario.id,
        observacion="Asignado desde correos sin asignar",
    )
    m.asignado_a = candidato.id
    db.commit()
    return cand.armar_listas(db, [candidato])[0]
