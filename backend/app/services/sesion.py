"""Cookie de sesión firmada (httpOnly). Guarda solo el id del usuario; lo demás sale de la base."""

import uuid

from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config import get_settings

COOKIE = "immpetus_sesion"
MAX_AGE_SEGUNDOS = 8 * 3600
_SALT = "immpetus-sesion-v1"


def _serializador() -> URLSafeTimedSerializer:
    secreto = get_settings().session_secret
    if len(secreto) < 32:
        raise RuntimeError(
            "SESSION_SECRET debe tener al menos 32 caracteres (openssl rand -hex 32)."
        )
    return URLSafeTimedSerializer(secreto, salt=_SALT)


def crear_token(usuario_id: uuid.UUID) -> str:
    return _serializador().dumps({"uid": str(usuario_id)})


def leer_token(token: str) -> uuid.UUID | None:
    """Devuelve el id del usuario o None si la firma es mala o la sesión venció (8 h)."""
    try:
        datos = _serializador().loads(token, max_age=MAX_AGE_SEGUNDOS)
        return uuid.UUID(datos["uid"])
    except (BadSignature, KeyError, ValueError, TypeError):
        return None
