from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_guardar_hv
from app.config import get_settings
from app.db import get_db
from app.errors import AppError, validation_error
from app.models.postulaciones import PostulacionCreada
from app.services import postulaciones as svc

router = APIRouter(prefix="/api/postulaciones", tags=["postulaciones (público)"])
_email = TypeAdapter(EmailStr)


@router.post("", response_model=PostulacionCreada, status_code=201)
async def crear(
    db: Annotated[Session, Depends(get_db)],
    guardar_hv: Annotated[svc.GuardarHV, Depends(get_guardar_hv)],
    vacante_id: Annotated[UUID, Form()],
    nombre: Annotated[str, Form(min_length=2, max_length=120)],
    correo: Annotated[str, Form()],
    celular: Annotated[str, Form(min_length=7, max_length=20)],
    archivo: Annotated[UploadFile, File()],
    autorizacion_datos: Annotated[bool, Form()],
    autorizacion_version: Annotated[str, Form()] = "1.0",
) -> PostulacionCreada:
    try:
        correo_ok = str(_email.validate_python(correo))
    except ValidationError as exc:
        raise validation_error("El correo no es válido.", "correo") from exc

    max_mb = get_settings().max_pdf_mb
    # Se lee un byte de más para detectar archivos que superan el límite sin cargarlos completos.
    contenido = await archivo.read(max_mb * 1024 * 1024 + 1)
    svc.validar_pdf(contenido, archivo.content_type, max_mb)

    if not autorizacion_datos:  # antes de tocar Drive o la base
        raise AppError(
            400,
            "VALIDATION_ERROR",
            "Debes autorizar el tratamiento de tus datos personales para postularte.",
            "autorizacion_datos",
        )
    return svc.crear_postulacion_web(
        db,
        vacante_id=vacante_id,
        nombre=nombre,
        correo=correo_ok,
        celular=celular,
        contenido_pdf=contenido,
        autorizacion_datos=autorizacion_datos,
        autorizacion_version=autorizacion_version,
        guardar_hv=guardar_hv,
    )
