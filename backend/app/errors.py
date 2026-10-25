"""Errores con el formato del contrato: { "error": { "code", "message", "field" } }."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, field: str | None = None):
        self.status, self.code, self.message, self.field = status, code, message, field


def _body(code: str, message: str, field: str | None = None) -> dict:
    return {"error": {"code": code, "message": message, "field": field}}


def validation_error(message: str, field: str | None = None) -> AppError:
    return AppError(400, "VALIDATION_ERROR", message, field)


def not_found(message: str = "No encontramos lo que buscas.") -> AppError:
    return AppError(404, "NOT_FOUND", message)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(_body(exc.code, exc.message, exc.field), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        err = exc.errors()[0]
        nombres = [
            str(x)
            for x in err.get("loc", ())
            if not isinstance(x, int) and x not in ("body", "query", "path", "form")
        ]
        campo = nombres[-1] if nombres else None  # en listas: el nombre del campo, no el índice
        return JSONResponse(
            _body("VALIDATION_ERROR", "Revisa los datos enviados.", campo), status_code=400
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "VALIDATION_ERROR"
        return JSONResponse(_body(code, str(exc.detail)), status_code=exc.status_code)
