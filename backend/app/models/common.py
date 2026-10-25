from typing import Literal

from pydantic import BaseModel

Modalidad = Literal["presencial", "hibrido", "remoto"]
EstadoCandidato = Literal["nuevo", "entrevista", "reserva", "por_validar", "no_apto", "contratado"]


class Pagina[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
