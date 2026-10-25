"""Reserva Estratégica, correos sin asignar, reporte a gerencia y anonimización (Sprint 3)."""

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import (
    get_borrar_hv,
    get_enviar_reporte,
    get_mover_hv,
    usuario_actual,
    usuario_con_escritura,
    usuario_lider,
)
from app.db import get_db
from app.models.admin import (
    AsignarVacante,
    CandidatoLista,
    CorreoSinAsignarOut,
    ReporteEnviado,
    ReporteInput,
)
from app.models.common import Pagina
from app.orm import Usuario
from app.services import anonimizar, correos, reporte, reserva
from app.services import candidatos as cand

router = APIRouter(
    prefix="/api/admin", tags=["centro de mando"], dependencies=[Depends(usuario_actual)]
)
Db = Annotated[Session, Depends(get_db)]
Escritor = Annotated[Usuario, Depends(usuario_con_escritura)]
Lider = Annotated[Usuario, Depends(usuario_lider)]


# ---------- Reserva Estratégica ----------
@router.get("/reserva", response_model=Pagina[CandidatoLista])
def buscar_reserva(
    db: Db,
    habilidad_id: Annotated[list[UUID] | None, Query()] = None,
    cargo: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Pagina[CandidatoLista]:
    items, total = reserva.buscar(db, habilidad_id or [], cargo, page, page_size)
    return Pagina(items=items, total=total, page=page, page_size=page_size)


@router.post("/reserva/{candidato_id}/asociar", response_model=CandidatoLista, status_code=201)
def asociar_reserva(
    candidato_id: UUID, datos: AsignarVacante, db: Db, usuario: Escritor
) -> CandidatoLista:
    return reserva.asociar(db, cand.obtener(db, candidato_id), datos.vacante_id, usuario)


# ---------- Correos sin asignar ----------
@router.get("/correos-sin-asignar", response_model=Pagina[CorreoSinAsignarOut])
def listar_correos(
    db: Db,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Pagina[CorreoSinAsignarOut]:
    items, total = correos.listar(db, page, page_size)
    return Pagina(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/correos-sin-asignar/{correo_id}/asignar", response_model=CandidatoLista, status_code=201
)
def asignar_correo(
    correo_id: UUID,
    datos: AsignarVacante,
    db: Db,
    usuario: Escritor,
    mover_hv: Annotated[Callable, Depends(get_mover_hv)],
) -> CandidatoLista:
    return correos.asignar(db, correo_id, datos.vacante_id, usuario, mover_hv)


# ---------- Reporte a gerencia ----------
@router.post("/vacantes/{vacante_id}/reporte", response_model=ReporteEnviado, status_code=202)
def enviar_reporte(
    vacante_id: UUID,
    datos: ReporteInput,
    db: Db,
    _: Escritor,
    enviar: Annotated[Callable[[list[str], str], None], Depends(get_enviar_reporte)],
) -> ReporteEnviado:
    reporte.enviar(db, vacante_id, [str(d) for d in datos.destinatarios], enviar)
    return ReporteEnviado(enviado=True)


# ---------- Derecho de supresión ----------
@router.post("/candidatos/{candidato_id}/anonimizar", response_model=CandidatoLista)
def anonimizar_candidato(
    candidato_id: UUID,
    db: Db,
    lider: Lider,
    borrar_hv: Annotated[Callable[[str], None], Depends(get_borrar_hv)],
) -> CandidatoLista:
    return anonimizar.anonimizar_titular(db, cand.obtener(db, candidato_id), lider, borrar_hv)
