"""Derecho de supresión (Ley 1581, art. 8) · contrato 5.5. Nunca se borran filas: se anonimizan.

Se anonimizan TODAS las postulaciones del mismo titular (mismo correo) y sus correos sin asignar,
porque comparten el PDF en Drive y un titular que pide supresión la pide para todo.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parseaddr

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.admin import CandidatoLista
from app.orm import Candidato, CorreoSinAsignar, Usuario
from app.services import candidatos as cand
from app.services import estados

MOTIVO = "Datos anonimizados por solicitud del titular (Ley 1581, art. 8)"


def anonimizar_titular(
    db: Session, c: Candidato, lider: Usuario, borrar_hv: Callable[[str], None]
) -> CandidatoLista:
    if c.anonimizado_en is not None:
        raise AppError(409, "CONFLICT", "El candidato ya fue anonimizado.")
    correo = c.correo.strip().lower()

    postulaciones = list(
        db.scalars(
            select(Candidato).where(
                func.lower(Candidato.correo) == correo, Candidato.anonimizado_en.is_(None)
            )
        )
    )
    correos = [
        m
        for m in db.scalars(select(CorreoSinAsignar))
        if parseaddr(m.remitente)[1].strip().lower() == correo
    ]

    # 1) Primero el PDF en Drive: si falla, no se anonimiza nada y se puede reintentar.
    archivos = {x.drive_file_id for x in [*postulaciones, *correos] if x.drive_file_id}
    try:
        for archivo in archivos:
            borrar_hv(archivo)
    except Exception as exc:
        raise AppError(
            502,
            "STORAGE_ERROR",
            "No pudimos borrar el PDF en Drive. No se anonimizó nada; intenta de nuevo.",
        ) from exc

    # 2) Después la base. El historial queda, pero sin datos personales.
    ahora = datetime.now(UTC)
    for p in postulaciones:
        p.nombre = "Titular anonimizado"
        p.correo = f"anonimizado+{p.id}@invalid.local"
        p.celular = None
        p.drive_file_id = p.drive_url = p.archivo_nombre = None
        p.anonimizado_en = ahora
        estados.registrar_evento(db, p, lider.id, MOTIVO)
    for m in correos:
        m.remitente = "anonimizado@invalid.local"
        m.asunto = m.archivo_nombre = m.drive_file_id = None
    db.commit()
    return cand.armar_listas(db, [c])[0]
