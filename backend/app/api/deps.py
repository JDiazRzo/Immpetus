from app.config import get_settings
from app.services import drive_dev
from app.services.postulaciones import GuardarHV


def get_guardar_hv() -> GuardarHV:
    """Drive real (integraciones/drive.py, de Fabian) si hay carpeta; si no, simulado."""
    if not get_settings().drive_root_folder_id:
        return drive_dev.guardar_hv
    from app.integraciones import drive  # import tardío: solo se carga con Drive configurado

    return drive.guardar_hv
