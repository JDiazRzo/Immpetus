"""Califica una HV con IA después de la postulación (tarea en segundo plano).

Regla de oro: la IA sugiere, la persona decide. Nunca pasa a nadie a 'no_apto'.
"""

import logging
import os
import unicodedata
import uuid
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db import get_engine
from app.integraciones import drive, ia
from app.orm import (
    Calificacion,
    Candidato,
    CandidatoHabilidad,
    Estado,
    Habilidad,
    Vacante,
    VacanteHabilidad,
)

log = logging.getLogger(__name__)
NOTA_POR_VALIDAR = 2  # nota 1–2 → bandeja "Por validar"


def _norm(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto.lower())
    return " ".join("".join(c for c in t if unicodedata.category(c) != "Mn").split())


def _habilidades_de_vacante(db: Session, vacante_id: uuid.UUID) -> list[tuple[Habilidad, bool]]:
    filas = db.execute(
        select(Habilidad, VacanteHabilidad.obligatoria)
        .join(VacanteHabilidad, VacanteHabilidad.habilidad_id == Habilidad.id)
        .where(VacanteHabilidad.vacante_id == vacante_id)
    ).all()
    return [(h, oblig) for h, oblig in filas]


def _vacante_para_ia(vacante: Vacante, habilidades: list[tuple[Habilidad, bool]]) -> SimpleNamespace:
    obligatorias = [h.nombre for h, oblig in habilidades if oblig]
    criterios = "; ".join(vacante.responsabilidades or [])
    if obligatorias:
        criterios += f". Obligatorias: {', '.join(obligatorias)}"
    return SimpleNamespace(
        cargo=vacante.cargo,
        descripcion=vacante.descripcion or "",
        criterios=criterios,
        codigo=vacante.codigo,
    )


def _pasar_a_por_validar(db: Session, candidato: Candidato, motivo: str) -> None:
    candidato.estado = "por_validar"
    db.add(Estado(candidato_id=candidato.id, estado="por_validar", observacion=motivo))


def _calificar(db: Session, candidato_id: uuid.UUID, contenido_pdf: bytes) -> None:
    candidato = db.get(Candidato, candidato_id)
    if candidato is None or candidato.anonimizado_en is not None:
        return
    vacante = db.get(Vacante, candidato.vacante_id)
    habilidades = _habilidades_de_vacante(db, vacante.id)
    catalogo = [h.nombre for h, _ in habilidades]

    try:
        resultado = ia.calificar_hv(contenido_pdf, _vacante_para_ia(vacante, habilidades), catalogo)
    except Exception:
        log.exception("Fallo IA candidato=%s", candidato_id)  # solo el id: sin datos personales
        resultado = None

    if resultado is None:
        _pasar_a_por_validar(db, candidato, "La IA no pudo calificar la hoja de vida.")
        db.commit()
        return

    db.add(
        Calificacion(
            candidato_id=candidato.id,
            nota=resultado.nota,
            resumen=resultado.resumen,
            matriz=resultado.matriz.model_dump(),
            origen="ia",
            modelo_ia=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        )
    )

    por_nombre = {_norm(h.nombre): h for h, _ in habilidades}
    vistas: set[uuid.UUID] = set()
    for hab in resultado.habilidades:
        encontrada = por_nombre.get(_norm(hab.nombre))
        if encontrada and encontrada.id not in vistas:
            vistas.add(encontrada.id)
            db.add(CandidatoHabilidad(candidato_id=candidato.id, habilidad_id=encontrada.id, origen="ia"))

    sin_texto = resultado.resumen == "Por Evaluar"
    if sin_texto or resultado.nota <= NOTA_POR_VALIDAR:
        motivo = "PDF sin texto legible." if sin_texto else f"Nota sugerida por IA: {resultado.nota}."
        _pasar_a_por_validar(db, candidato, motivo)

    db.commit()

    if candidato.drive_file_id and not sin_texto:
        try:
            drive.renombrar_hv(candidato.drive_file_id, resultado.nota, candidato.nombre, vacante.cargo)
        except Exception:
            log.exception("Fallo renombrar Drive candidato=%s", candidato_id)


def calificar_en_segundo_plano(candidato_id: uuid.UUID, contenido_pdf: bytes) -> None:
    """Punto de entrada para BackgroundTasks: abre su propia sesión (la del request ya se cerró)."""
    with sessionmaker(bind=get_engine(), expire_on_commit=False)() as db:
        try:
            _calificar(db, candidato_id, contenido_pdf)
        except Exception:
            db.rollback()
            log.exception("Fallo calificando candidato=%s", candidato_id)