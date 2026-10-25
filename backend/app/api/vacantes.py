from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.common import Modalidad, Pagina
from app.models.vacantes import VacanteDetalle, VacanteResumen
from app.services import vacantes as svc

router = APIRouter(prefix="/api/vacantes", tags=["vacantes (público)"])


@router.get("", response_model=Pagina[VacanteResumen])
def listar(
    db: Annotated[Session, Depends(get_db)],
    q: str | None = None,
    modalidad: Modalidad | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Pagina[VacanteResumen]:
    items, total = svc.listar_activas(db, q, modalidad, page, page_size)
    return Pagina(items=items, total=total, page=page, page_size=page_size)


@router.get("/{slug}", response_model=VacanteDetalle)
def detalle(slug: str, db: Annotated[Session, Depends(get_db)]) -> VacanteDetalle:
    return svc.obtener_activa_por_slug(db, slug)
