"""Drive simulado SOLO para desarrollo local, mientras Fabian entrega integraciones/drive.py.

Se usa cuando DRIVE_ROOT_FOLDER_ID está vacío. No guarda nada: devuelve un id falso.
"""

import uuid

from app.models.postulaciones import DriveFile


def guardar_hv(pdf_bytes: bytes, vacante, nombre: str) -> DriveFile:  # noqa: ANN001
    fake = uuid.uuid4().hex
    return DriveFile(id=f"dev-{fake}", url=f"https://drive.invalid/dev/{fake}")
