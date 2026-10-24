from uuid import UUID

from pydantic import BaseModel

from app.models.common import EstadoCandidato


class PostulacionCreada(BaseModel):
    id: UUID
    estado: EstadoCandidato
    mensaje: str = "Postulación enviada."


class DriveFile(BaseModel):
    """Lo que devuelve integraciones/drive.guardar_hv (sección 3 del contrato)."""

    id: str
    url: str
