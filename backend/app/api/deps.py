from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.errors import AppError
from app.orm import Usuario
from app.services import drive_dev, google, integraciones_dev, sesion
from app.services.postulaciones import GuardarHV

ROLES_ESCRITURA = {"analista", "lider"}


def get_guardar_hv() -> GuardarHV:
    """Drive real (integraciones/drive.py, de Fabian) si hay carpeta; si no, simulado."""
    if not get_settings().drive_root_folder_id:
        return drive_dev.guardar_hv
    from app.integraciones import drive  # import tardío: solo se carga con Drive configurado

    return drive.guardar_hv


def get_mover_hv() -> Callable:
    """drive.mover_hv(drive_file_id, vacante) -> DriveFile (por implementar por Fabian)."""
    if not get_settings().drive_root_folder_id:
        return integraciones_dev.mover_hv
    from app.integraciones import drive

    return drive.mover_hv


def get_borrar_hv() -> Callable[[str], None]:
    """drive.borrar_hv(drive_file_id): debe tratar 'archivo ya borrado' como éxito."""
    if not get_settings().drive_root_folder_id:
        return integraciones_dev.borrar_hv
    from app.integraciones import drive

    return drive.borrar_hv


def get_enviar_reporte() -> Callable[[list[str], str], None]:
    """gmail.enviar_reporte(destinatarios, html), según el contrato (sección 3)."""
    if not get_settings().gmail_delegated_user:
        return integraciones_dev.enviar_reporte
    from app.integraciones import gmail

    return gmail.enviar_reporte


def get_verificador_google() -> Callable[[str], dict]:
    return google.verificar_id_token  # los tests lo reemplazan: no se llama a Google


def usuario_actual(request: Request, db: Annotated[Session, Depends(get_db)]) -> Usuario:
    """Protege /api/admin/*. 401 sin sesión válida; 403 si la cuenta quedó inactiva."""
    token = request.cookies.get(sesion.COOKIE)
    usuario_id = sesion.leer_token(token) if token else None
    usuario = db.get(Usuario, usuario_id) if usuario_id else None
    if usuario is None:
        raise AppError(401, "UNAUTHENTICATED", "Inicia sesión para continuar.")
    if not usuario.activo:
        raise AppError(
            403, "FORBIDDEN", "Tu cuenta está inactiva. Pide acceso al líder de selección."
        )
    return usuario


def usuario_con_escritura(usuario: Annotated[Usuario, Depends(usuario_actual)]) -> Usuario:
    """Gerencia solo consulta; analista y líder pueden modificar (decisión por confirmar)."""
    if usuario.rol not in ROLES_ESCRITURA:
        raise AppError(403, "FORBIDDEN", "Tu rol es de solo consulta.")
    return usuario


def usuario_lider(usuario: Annotated[Usuario, Depends(usuario_actual)]) -> Usuario:
    """Acciones con efecto legal (anonimizar) solo para el rol líder."""
    if usuario.rol != "lider":
        raise AppError(403, "FORBIDDEN", "Solo el líder de selección puede hacer esto.")
    return usuario
