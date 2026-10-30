"""Reserva Estratégica: candidatos en estado `reserva` reutilizables para nuevas vacantes."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import AppError, not_found
from app.models.admin import CandidatoLista
from app.orm import Candidato, CandidatoHabilidad, Usuario, Vacante
from app.services import candidatos as cand
from app.services import estados


def buscar(
    db: Session, habilidad_ids: list[uuid.UUID], cargo: str | None, page: int, page_size: int
) -> tuple[list[CandidatoLista], int]:
    consulta = (
        select(Candidato)
        .join(Vacante, Vacante.id == Candidato.vacante_id)
        .where(
            Candidato.estado == "reserva",
            Candidato.acepta_futuras.is_(True),  # la autorización para futuras vacantes es aparte
            Candidato.anonimizado_en.is_(None),
        )
    )
    for hid in set(habilidad_ids):  # debe tener TODAS las habilidades pedidas
        consulta = consulta.where(
            Candidato.id.in_(
                select(CandidatoHabilidad.candidato_id).where(
                    CandidatoHabilidad.habilidad_id == hid
                )
            )
        )
    if cargo and cargo.strip():
        consulta = consulta.where(Vacante.cargo.ilike(f"%{cargo.strip()}%"))

    todos = cand.armar_listas(db, list(db.scalars(consulta)))
    todos.sort(key=lambda x: (x.nota is None, -(x.nota or 0), -x.creado_en.timestamp()))
    inicio = (page - 1) * page_size
    return todos[inicio : inicio + page_size], len(todos)


def asociar(
    db: Session, origen: Candidato, vacante_id: uuid.UUID, usuario: Usuario
) -> CandidatoLista:
    """Crea una nueva postulación (fila) del mismo titular en otra vacante.

    No copia la nota: fue contra otros criterios; la IA debe calificar para la nueva vacante.
    El original permanece en la Reserva. Exige que el titular haya autorizado conservar su HV para
    futuras vacantes (acepta_futuras); si no, 409.
    """
    cand.exigir_no_anonimizado(origen)
    if origen.estado != "reserva":
        raise AppError(
            409, "CONFLICT", "Solo se pueden asociar candidatos de la Reserva Estratégica."
        )
    if not origen.acepta_futuras:
        raise AppError(
            409,
            "CONFLICT",
            "El candidato no autorizó que su hoja de vida se considere para otras vacantes.",
        )
    destino = db.get(Vacante, vacante_id)
    if destino is None:
        raise not_found("La vacante no existe.")
    if not destino.activa:
        raise AppError(409, "CONFLICT", "La vacante no está activa.")
    if destino.id == origen.vacante_id:
        raise AppError(409, "CONFLICT", "El candidato ya pertenece a esa vacante.")
    if cand.existe_postulacion_activa(db, destino.id, origen.correo):
        raise AppError(409, "CONFLICT", "El candidato ya está postulado a esa vacante.")

    nuevo = Candidato(
        vacante_id=destino.id,
        nombre=origen.nombre,
        correo=origen.correo,
        celular=origen.celular,
        canal=origen.canal,
        drive_file_id=origen.drive_file_id,
        drive_url=origen.drive_url,
        archivo_nombre=origen.archivo_nombre,
        autorizacion_datos=True,
        autorizacion_fecha=origen.autorizacion_fecha,
        autorizacion_version=origen.autorizacion_version,
        acepta_futuras=True,  # ya la dio: se conserva con su fecha original
        acepta_futuras_fecha=origen.acepta_futuras_fecha,
    )
    db.add(nuevo)
    db.flush()
    for h in db.scalars(
        select(CandidatoHabilidad).where(CandidatoHabilidad.candidato_id == origen.id)
    ):
        db.add(
            CandidatoHabilidad(candidato_id=nuevo.id, habilidad_id=h.habilidad_id, origen=h.origen)
        )
    estados.registrar_estado_inicial(
        db,
        nuevo,
        "nuevo",
        usuario_id=usuario.id,
        observacion="Asociado desde la Reserva Estratégica",
    )
    db.commit()
    return cand.armar_listas(db, [nuevo])[0]
