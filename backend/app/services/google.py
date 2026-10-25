"""Verificación del id_token de Google con la librería oficial google-auth (no a mano)."""

from app.config import get_settings


def verificar_id_token(token: str) -> dict:
    """Valida firma, vencimiento y `aud` = GOOGLE_OAUTH_CLIENT_ID. Lanza ValueError si falla."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    client_id = get_settings().google_oauth_client_id
    if not client_id:
        raise RuntimeError("Falta GOOGLE_OAUTH_CLIENT_ID en el .env.")
    return id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
