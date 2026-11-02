"""Rechaza cuerpos demasiado grandes con 413 ANTES de leerlos (middleware ASGI puro).

1) Si hay Content-Length mayor al límite: 413 sin leer nada.
2) Si no hay Content-Length (chunked) o miente: se cuentan los bytes a medida que llegan y se corta
   al pasar el límite, para que nadie evite la regla omitiendo el encabezado.
"""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import get_settings

OTROS_MAX_BYTES = 64 * 1024  # JSON de contacto y login: nunca necesitan más


class _Excedido(Exception):
    pass


def _regla(path: str) -> tuple[int, dict] | None:
    s = get_settings()
    if path == "/api/postulaciones":  # PDF de hasta MAX_PDF_MB + ~1 MB de campos del formulario
        return (s.max_pdf_mb + 1) * 1024 * 1024, {
            "code": "FILE_TOO_LARGE",
            "message": f"El PDF no debe superar {s.max_pdf_mb} MB.",
            "field": "archivo",
        }
    if path in ("/api/contacto", "/api/auth/google"):
        return OTROS_MAX_BYTES, {
            "code": "PAYLOAD_TOO_LARGE",
            "message": "La solicitud es demasiado grande.",
            "field": None,
        }
    return None


class LimiteTamanoMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        regla = (
            _regla(scope["path"]) if scope["type"] == "http" and scope["method"] == "POST" else None
        )
        if regla is None:
            await self.app(scope, receive, send)
            return
        limite, error = regla
        respuesta = JSONResponse({"error": error}, status_code=413)

        declarado = dict(scope["headers"]).get(b"content-length")
        if declarado and declarado.isdigit() and int(declarado) > limite:
            await respuesta(scope, receive, send)
            return

        recibidos = 0
        excedido = False
        empezo = False

        async def receive_limitado() -> Message:
            nonlocal recibidos, excedido
            mensaje = await receive()
            if mensaje["type"] == "http.request":
                recibidos += len(mensaje.get("body", b""))
                if recibidos > limite:
                    excedido = True
                    raise _Excedido
            return mensaje

        async def send_vigilado(mensaje: Message) -> None:
            nonlocal empezo
            if excedido:
                return  # FastAPI convierte la excepción al leer el cuerpo en un 400: se descarta
            empezo = empezo or mensaje["type"] == "http.response.start"
            await send(mensaje)

        try:
            await self.app(scope, receive_limitado, send_vigilado)
        except _Excedido:
            pass
        if excedido and not empezo:
            await respuesta(scope, receive, send)
