from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_verificador_google
from app.config import get_settings
from app.db import get_db
from app.errors import AppError
from app.models.admin import GoogleLogin, UsuarioAdmin
from app.orm import Usuario
from app.services import sesion

router = APIRouter(prefix="/api/auth", tags=["autenticación"])


@router.post("/google", response_model=UsuarioAdmin)
def login_google(
    body: GoogleLogin,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    verificar: Annotated[Callable[[str], dict], Depends(get_verificador_google)],
) -> Usuario:
    settings = get_settings()
    try:
        claims = verificar(body.id_token)
    except Exception as exc:  # firma, vencimiento o audiencia inválidos
        raise AppError(
            401, "UNAUTHENTICATED", "No pudimos verificar tu cuenta de Google. Intenta de nuevo."
        ) from exc

    if claims.get("email_verified") is not True:
        raise AppError(
            401, "UNAUTHENTICATED", "No pudimos verificar tu cuenta de Google. Intenta de nuevo."
        )

    dominio = settings.allowed_email_domain.lower()
    correo = str(claims.get("email", "")).strip().lower()
    if str(claims.get("hd", "")).lower() != dominio or not correo.endswith(f"@{dominio}"):
        raise AppError(403, "FORBIDDEN", f"Solo pueden entrar cuentas @{dominio}.")

    usuario = db.scalar(
        select(Usuario).where(func.lower(Usuario.correo) == correo, Usuario.activo.is_(True))
    )
    if usuario is None:
        raise AppError(
            403,
            "FORBIDDEN",
            "Tu cuenta no está registrada en el centro de mando. "
            "Pide acceso al líder de selección.",
        )

    response.set_cookie(
        sesion.COOKIE,
        sesion.crear_token(usuario.id),
        max_age=sesion.MAX_AGE_SEGUNDOS,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return usuario


@router.post("/logout", status_code=204)
def logout() -> Response:
    respuesta = Response(status_code=204)
    respuesta.delete_cookie(sesion.COOKIE, path="/")
    return respuesta
