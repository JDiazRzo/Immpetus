from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import usuario_actual, usuario_con_escritura
from app.db import get_db
from app.models.admin import (
    CambioEstado,
    CandidatoDetalle,
    CandidatoLista,
    CorreccionNota,
    HabilidadOut,
    ResumenVacante,
    UsuarioAdmin,
    VacanteAdmin,
    VacanteInput,
    VacanteUpdate,
)
from app.models.common import EstadoCandidato, Pagina
from app.orm import Usuario
from app.services import candidatos as cand
from app.services import estados
from app.services import vacantes_admin as vac

# Todo /api/admin/* exige sesión válida (401/403). Las escrituras piden además rol analista o líder.
router = APIRouter(
    prefix="/api/admin", tags=["centro de mando"], dependencies=[Depends(usuario_actual)]
)
Db = Annotated[Session, Depends(get_db)]
Escritor = Annotated[Usuario, Depends(usuario_con_escritura)]


@router.get("/me", response_model=UsuarioAdmin)
def me(usuario: Annotated[Usuario, Depends(usuario_actual)]) -> Usuario:
    return usuario


# ---------- Vacantes ----------
@router.get("/vacantes", response_model=Pagina[VacanteAdmin])
def listar_vacantes(
    db: Db,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 100,
) -> Pagina[VacanteAdmin]:
    items, total = vac.listar(db, page, page_size)
    return Pagina(items=items, total=total, page=page, page_size=page_size)


@router.post("/vacantes", response_model=VacanteAdmin, status_code=201)
def crear_vacante(datos: VacanteInput, db: Db, usuario: Escritor) -> VacanteAdmin:
    return vac.crear(db, usuario, datos)


@router.get("/vacantes/{vacante_id}", response_model=VacanteAdmin)
def obtener_vacante(vacante_id: UUID, db: Db) -> VacanteAdmin:
    return vac.a_admin(db, vac.obtener(db, vacante_id))


@router.patch("/vacantes/{vacante_id}", response_model=VacanteAdmin)
def editar_vacante(vacante_id: UUID, cambios: VacanteUpdate, db: Db, _: Escritor) -> VacanteAdmin:
    return vac.actualizar(db, vacante_id, cambios)


@router.get("/vacantes/{vacante_id}/resumen", response_model=ResumenVacante)
def resumen_vacante(vacante_id: UUID, db: Db) -> ResumenVacante:
    return cand.resumen(db, vacante_id)


# ---------- Candidatos ----------
@router.get("/vacantes/{vacante_id}/candidatos", response_model=Pagina[CandidatoLista])
def listar_candidatos(
    vacante_id: UUID,
    db: Db,
    estado: EstadoCandidato | None = None,
    orden: Literal["nota_desc", "nota_asc", "reciente"] = "reciente",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Pagina[CandidatoLista]:
    items, total = cand.listar(
        db, vacante_id=vacante_id, estado=estado, orden=orden, page=page, page_size=page_size
    )
    return Pagina(items=items, total=total, page=page, page_size=page_size)


@router.get("/candidatos", response_model=Pagina[CandidatoLista])
def listar_todos_los_candidatos(
    db: Db,
    estado: EstadoCandidato | None = None,
    orden: Literal["nota_desc", "nota_asc", "reciente"] = "reciente",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Pagina[CandidatoLista]:
    """Candidatos de TODAS las vacantes (p. ej. `?estado=por_validar`), paginados desde la base."""
    items, total = cand.listar(db, estado=estado, orden=orden, page=page, page_size=page_size)
    return Pagina(items=items, total=total, page=page, page_size=page_size)


@router.get("/candidatos/{candidato_id}", response_model=CandidatoDetalle)
def obtener_candidato(candidato_id: UUID, db: Db) -> CandidatoDetalle:
    return cand.detalle(db, cand.obtener(db, candidato_id))


@router.post("/candidatos/{candidato_id}/estado", response_model=CandidatoLista)
def cambiar_estado(
    candidato_id: UUID, datos: CambioEstado, db: Db, usuario: Escritor
) -> CandidatoLista:
    c = cand.obtener(db, candidato_id)
    cand.exigir_no_anonimizado(c)
    observacion = datos.observacion.strip() if datos.observacion else None
    estados.cambiar_estado(db, c, datos.estado, usuario.id, observacion or None)
    db.commit()
    return cand.armar_listas(db, [c])[0]


@router.post("/candidatos/{candidato_id}/calificacion", response_model=CandidatoLista)
def corregir_calificacion(
    candidato_id: UUID, datos: CorreccionNota, db: Db, usuario: Escritor
) -> CandidatoLista:
    return cand.corregir_nota(db, cand.obtener(db, candidato_id), usuario, datos.nota, datos.motivo)


# ---------- Habilidades ----------
@router.get("/habilidades", response_model=list[HabilidadOut])
def habilidades(db: Db, q: str | None = None) -> list[HabilidadOut]:
    return [
        HabilidadOut(id=h.id, nombre=h.nombre, categoria=h.categoria)
        for h in vac.buscar_habilidades(db, q)
    ]
