"""Reporte a gerencia: ranking de una vacante enviado por correo (gmail.enviar_reporte)."""

import uuid
from collections.abc import Callable
from html import escape

from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import AppError, validation_error
from app.services import candidatos as cand
from app.services import vacantes_admin as vac

TOP = 10


def validar_destinatarios(destinatarios: list[str]) -> list[str]:
    """Los datos de candidatos solo salen hacia correos del dominio de Immpetus."""
    dominio = get_settings().allowed_email_domain.lower()
    limpios = list(dict.fromkeys(d.strip().lower() for d in destinatarios))
    if any(not d.endswith(f"@{dominio}") for d in limpios):
        raise validation_error(
            f"Solo se puede enviar el reporte a correos @{dominio}.", "destinatarios"
        )
    return limpios


def construir_html(db: Session, vacante_id: uuid.UUID) -> str:
    v = vac.obtener(db, vacante_id)
    r = cand.resumen(db, vacante_id)
    items, _ = cand.listar(db, vacante_id=vacante_id, orden="nota_desc", page_size=200)
    top = [c for c in items if c.estado != "no_apto" and c.nombre != "Titular anonimizado"][:TOP]

    def revision(c) -> str:  # noqa: ANN001
        if c.nota_validada:
            return f"Validada por {escape(c.validada_por or '')}"
        return "Sugerida por IA"

    filas = "".join(
        f"<tr><td>{i}</td><td>{escape(c.nombre)}</td><td>{c.nota or '—'}</td>"
        f"<td>{escape(c.estado)}</td><td>{revision(c)}</td></tr>"
        for i, c in enumerate(top, 1)
    )
    if not filas:
        filas = '<tr><td colspan="5">Aún no hay candidatos calificados.</td></tr>'
    titulo = f"Reporte de selección · {escape(v.cargo)} ({escape(v.codigo)})"
    return (
        f"<html><head><title>{titulo}</title></head><body>"
        f"<h2>{titulo}</h2>"
        f"<p>Recibidas: <b>{r.recibidas}</b> · Nota 4–5: <b>{r.nota_4_5}</b> · "
        f"Reserva: <b>{r.reserva}</b> · Por validar: <b>{r.por_validar}</b> · "
        f"Entrevista: <b>{r.entrevista}</b></p>"
        f"<h3>Ranking (máximo {TOP})</h3>"
        '<table border="1" cellpadding="6" cellspacing="0">'
        "<tr><th>#</th><th>Candidato</th><th>Nota</th><th>Estado</th><th>Revisión</th></tr>"
        f"{filas}</table>"
        "<p><i>Las notas son una sugerencia de la IA; "
        "la decisión final es siempre de una persona.</i></p>"
        "</body></html>"
    )


def enviar(
    db: Session,
    vacante_id: uuid.UUID,
    destinatarios: list[str],
    enviar_reporte: Callable[[list[str], str], None],
) -> None:
    para = validar_destinatarios(destinatarios)
    html = construir_html(db, vacante_id)  # 404 si la vacante no existe
    try:
        enviar_reporte(para, html)
    except Exception as exc:
        raise AppError(
            502, "EMAIL_ERROR", "No pudimos enviar el reporte. Intenta de nuevo."
        ) from exc
