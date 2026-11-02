from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_enviar_aviso_contacto
from app.db import get_db
from app.limiter import LIMITE_CONTACTO, limiter
from app.models.contacto import ContactoCreado, ContactoInput
from app.services import contactos

router = APIRouter(prefix="/api/contacto", tags=["contacto (público)"])


@router.post("", response_model=ContactoCreado, status_code=201)
@limiter.limit(LIMITE_CONTACTO)
def crear_contacto(
    request: Request,
    datos: ContactoInput,
    segundo_plano: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    enviar_aviso: Annotated[Callable[[dict], None], Depends(get_enviar_aviso_contacto)],
) -> ContactoCreado:
    contacto = contactos.crear(db, datos)
    segundo_plano.add_task(contactos.avisar, enviar_aviso, contacto)  # después de responder
    return ContactoCreado(id=contacto.id)
