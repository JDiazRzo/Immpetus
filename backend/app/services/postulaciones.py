import re
import unicodedata
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import func, select  # NUEVO: func
from sqlalchemy.exc import IntegrityError  # NUEVO
from sqlalchemy.orm import Session

from app.errors import AppError, not_found, validation_error
from app.models.postulaciones import DriveFile, PostulacionCreada
from app.orm import Candidato, Vacante
from app.services import estados

GuardarHV = Callable[[bytes, Vacante, str], DriveFile]
PDF_MAGIC = b"%PDF-"

# NUEVO
MENSAJE_DUPLICADO = (
    "Ya recibimos tu hoja de vida para esta vacante. "
    "Si necesitas actualizarla, escríbenos a seleccion@immpetus.co."
)


def validar_pdf(contenido: bytes, content_type: str | None, max_mb: int) -> None:
    if len(contenido) > max_mb * 1024 * 1024:
        raise AppError(413, "FILE_TOO_LARGE", f"El PDF no debe superar {max_mb} MB.", "archivo")
    if content_type != "application/pdf" or not contenido.startswith(PDF_MAGIC):
        raise validation_error(f"El archivo debe ser PDF de máximo {max_mb} MB.", "archivo")


def _limpio(texto: str) -> str:
    """Quita caracteres que molestan en nombres de archivo de Drive."""
    t = unicodedata.normalize("NFC", texto)
    return re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", t).strip()[:80]


def nombre_archivo_inicial(nombre: str, cargo: str) -> str:
    # Aún sin nota; Fabian lo renombra a '[NOTA] - [NOMBRE] - [CARGO].pdf' tras calificar.
    return f"SN - {_limpio(nombre)} - {_limpio(cargo)}.pdf"


# NUEVO
def ya_postulado(db: Session, vacante_id: uuid.UUID, correo: str) -> bool:
    """Una postulación activa por correo y vacante (los anonimizados no cuentan)."""
    return (
        db.scalar(
            select(Candidato.id).where(
                Candidato.vacante_id == vacante_id,
                func.lower(Candidato.correo) == correo.strip().lower(),
                Candidato.anonimizado_en.is_(None),
            )
        )
        is not None
    )


def crear_postulacion_web(
    db: Session,
    *,
    vacante_id: uuid.UUID,
    nombre: str,
    correo: str,
    celular: str,
    contenido_pdf: bytes,
    autorizacion_datos: bool,
    autorizacion_version: str,
    guardar_hv: GuardarHV,
) -> PostulacionCreada:
    if not autorizacion_datos:
        raise validation_error(
            "Debes autorizar el tratamiento de tus datos personales para postularte.",
            "autorizacion_datos",
        )
    vacante = db.scalar(select(Vacante).where(Vacante.id == vacante_id, Vacante.activa.is_(True)))
    if vacante is None:
        raise not_found("Esta vacante no existe o ya no está disponible.")

    # NUEVO: se revisa antes de subir a Drive para no guardar un PDF que se va a rechazar.
    if ya_postulado(db, vacante.id, correo):
        raise AppError(409, "CONFLICT", MENSAJE_DUPLICADO, "correo")

    archivo = nombre_archivo_inicial(nombre, vacante.cargo)
    try:
        subido = guardar_hv(contenido_pdf, vacante, archivo)
    except Exception as exc:  # no registrar datos del candidato en logs
        raise AppError(
            502, "STORAGE_ERROR", "No pudimos guardar tu hoja de vida. Intenta de nuevo."
        ) from exc

    candidato = Candidato(
        id=uuid.uuid4(),
        vacante_id=vacante.id,
        nombre=nombre.strip(),
        correo=correo.strip().lower(),
        celular=celular.strip(),
        canal="web",
        drive_file_id=subido.id,
        drive_url=subido.url,
        archivo_nombre=archivo,
        estado="nuevo",
        autorizacion_datos=True,
        autorizacion_fecha=datetime.now(UTC),
        autorizacion_version=autorizacion_version.strip() or "1.0",
    )
    db.add(candidato)
    # NUEVO: si llegan dos envíos iguales al mismo tiempo, el índice único de la base frena el segundo.
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "CONFLICT", MENSAJE_DUPLICADO, "correo") from exc
    estados.registrar_estado_inicial(db, candidato, "nuevo")
    db.commit()
    return PostulacionCreada(id=candidato.id, estado="nuevo")