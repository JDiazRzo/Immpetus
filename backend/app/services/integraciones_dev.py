"""Simulaciones SOLO para desarrollo local (hasta que existan integraciones/drive.py y gmail.py).

No tocan Google y no registran datos personales.
"""

import logging
import uuid

from app.models.postulaciones import DriveFile

log = logging.getLogger("immpetus.dev")


def mover_hv(drive_file_id: str, vacante) -> DriveFile:  # noqa: ANN001
    return DriveFile(id=drive_file_id, url=f"https://drive.invalid/dev/{uuid.uuid4().hex}")


def borrar_hv(drive_file_id: str) -> None:
    log.warning("Drive simulado: no se borró ningún archivo real.")


def enviar_reporte(destinatarios: list[str], html: str) -> None:
    log.warning("Gmail simulado: reporte NO enviado (%d destinatarios).", len(destinatarios))


def enviar_aviso_contacto(datos: dict) -> None:
    log.warning("Gmail simulado: aviso de contacto NO enviado.")
