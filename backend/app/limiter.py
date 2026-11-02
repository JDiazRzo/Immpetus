"""Límite de peticiones por IP (slowapi). Excedido → 429 con el formato de errores del contrato."""

from fastapi import Request
from slowapi import Limiter

from app.config import get_settings


def ip_cliente(request: Request) -> str:
    """IP real del cliente.

    Sin proxies propios se usa la IP de la conexión. Con TRUSTED_PROXY_HOPS=n se toma la n-ésima
    entrada DESDE EL FINAL de X-Forwarded-For (cada proxy propio agrega al final la IP de quien le
    habló); las entradas anteriores las puede falsificar el cliente y se ignoran.
    """
    saltos = get_settings().trusted_proxy_hops
    if saltos > 0:
        partes = [
            p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()
        ]
        if len(partes) >= saltos:
            return partes[-saltos]
    return request.client.host if request.client else "desconocida"


_s = get_settings()
limiter = Limiter(
    key_func=ip_cliente, storage_uri=_s.rate_limit_storage_uri, enabled=_s.rate_limit_enabled
)

LIMITE_POSTULACIONES = "5/hour"
LIMITE_CONTACTO = "3/hour"
LIMITE_LOGIN = "10/minute"
