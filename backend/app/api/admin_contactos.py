from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import usuario_actual, usuario_con_escritura
from app.db import get_db
from app.models.admin import ContactoAdmin, ContactoUpdate
from app.models.common import Pagina
from app.orm import Usuario
from app.services import contactos

router = APIRouter(
    prefix="/api/admin/contactos",
    tags=["centro de mando"],
    dependencies=[Depends(usuario_actual)],
)
Db = Annotated[Session, Depends(get_db)]


@router.get("", response_model=Pagina[ContactoAdmin])
def listar_contactos(
    db: Db,
    atendido: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Pagina[ContactoAdmin]:
    items, total = contactos.listar(db, atendido, page, page_size)
    return Pagina(items=items, total=total, page=page, page_size=page_size)


@router.patch("/{contacto_id}", response_model=ContactoAdmin)
def actualizar_contacto(
    contacto_id: UUID,
    datos: ContactoUpdate,
    db: Db,
    _: Annotated[Usuario, Depends(usuario_con_escritura)],
) -> ContactoAdmin:
    return contactos.marcar_atendido(db, contacto_id, datos.atendido)
