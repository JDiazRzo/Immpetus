"""ÚNICO lugar donde se cambia o se inserta un estado (CLAUDE.md, regla 2 y contrato 5.1).

Solo inserta filas en `estados`; nunca UPDATE ni DELETE sobre el historial.
"""

import uuid

from sqlalchemy.orm import Session

from app.errors import AppError
from app.orm import Candidato, Estado

# Contrato 5.1: transiciones válidas. no_apto y contratado son finales.
TRANSICIONES: dict[str, set[str]] = {
    "nuevo": {"entrevista", "reserva", "no_apto"},
    "por_validar": {"entrevista", "reserva", "no_apto"},
    "reserva": {"entrevista", "no_apto"},
    "entrevista": {"reserva", "no_apto", "contratado"},
    "no_apto": set(),
    "contratado": set(),
}


def estado_inicial_por_nota(nota: int) -> str:
    """Contrato 5.3. Nunca devuelve no_apto: 1-2 quedan por_validar (regla de oro)."""
    if not 1 <= nota <= 5:
        raise ValueError("La nota debe estar entre 1 y 5.")
    if nota >= 4:
        return "nuevo"
    return "reserva" if nota == 3 else "por_validar"


def registrar_estado_inicial(
    db: Session,
    candidato: Candidato,
    estado: str,
    *,
    usuario_id: uuid.UUID | None = None,
    observacion: str | None = None,
) -> None:
    """Primer estado de un candidato. Nunca no_apto/entrevista/contratado."""
    if estado in {"no_apto", "contratado", "entrevista"}:
        raise AppError(409, "CONFLICT", "El sistema no puede asignar ese estado.")
    candidato.estado = estado
    db.add(
        Estado(
            id=uuid.uuid4(),
            candidato_id=candidato.id,
            estado=estado,
            validado_por=usuario_id,
            observacion=observacion,
        )
    )


def registrar_evento(
    db: Session, candidato: Candidato, usuario_id: uuid.UUID, observacion: str
) -> None:
    """Deja constancia en el historial SIN cambiar el estado (p. ej. anonimización)."""
    db.add(
        Estado(
            id=uuid.uuid4(),
            candidato_id=candidato.id,
            estado=candidato.estado,
            validado_por=usuario_id,
            observacion=observacion,
        )
    )


def cambiar_estado(
    db: Session, candidato: Candidato, nuevo: str, usuario_id: uuid.UUID, observacion: str | None
) -> Candidato:
    """Cambio hecho por una persona desde /api/admin. 409 si la transición no es válida."""
    if nuevo not in TRANSICIONES.get(candidato.estado, set()):
        raise AppError(409, "CONFLICT", f"No se puede pasar de '{candidato.estado}' a '{nuevo}'.")
    candidato.estado = nuevo
    db.add(
        Estado(
            id=uuid.uuid4(),
            candidato_id=candidato.id,
            estado=nuevo,
            validado_por=usuario_id,
            observacion=observacion,
        )
    )
    return candidato
