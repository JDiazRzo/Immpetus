"""El índice único de postulaciones (candidatos_correo_vacante_unico) como última barrera."""

import uuid
from datetime import UTC, datetime

import pytest

from app.orm import Candidato, CorreoSinAsignar, Estado
from app.services import candidatos as cand

T0 = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
CORREO = "carrera@x.co"


def _cand(db, vacante, estado, correo=CORREO, futuras=False):
    c = Candidato(
        vacante_id=vacante.id,
        nombre="Cand",
        correo=correo,
        canal="web",
        estado=estado,
        autorizacion_datos=True,
        autorizacion_fecha=T0,
        autorizacion_version="1.0",
        acepta_futuras=futuras,
        acepta_futuras_fecha=T0 if futuras else None,
    )
    db.add(c)
    db.flush()
    db.add(Estado(candidato_id=c.id, estado=estado))
    db.commit()
    return c


@pytest.fixture
def sin_prechequeo(db, monkeypatch):
    """Simula que dos peticiones llegan a la vez: el chequeo de Python no ve el duplicado."""
    if db.get_bind().dialect.name != "postgresql":
        pytest.skip("El índice único solo existe en Postgres (TEST_DATABASE_URL).")
    monkeypatch.setattr(cand, "existe_postulacion_activa", lambda *a, **k: False)


def test_asociar_con_carrera_responde_409_y_no_500(client, login, vacantes, db, sin_prechequeo):
    login("analista")
    origen = _cand(db, vacantes["activa"], "reserva", futuras=True)
    _cand(db, vacantes["otra"], "nuevo")  # ya está en la vacante destino
    r = client.post(
        f"/api/admin/reserva/{origen.id}/asociar", json={"vacante_id": str(vacantes["otra"].id)}
    )
    db.rollback()
    assert r.status_code == 409 and r.json()["error"]["code"] == "CONFLICT"
    assert CORREO not in r.text  # el mensaje de la base (con el correo) nunca sale al cliente


def test_asignar_con_carrera_responde_409_y_no_500(client, login, vacantes, db, sin_prechequeo):
    login("analista")
    _cand(db, vacantes["activa"], "nuevo", correo="laura@mail.com")
    m = CorreoSinAsignar(
        gmail_id=uuid.uuid4().hex,
        remitente="Laura <laura@mail.com>",
        drive_file_id="d1",
        recibido_en=T0,
    )
    db.add(m)
    db.commit()
    r = client.post(
        f"/api/admin/correos-sin-asignar/{m.id}/asignar",
        json={"vacante_id": str(vacantes["activa"].id)},
    )
    db.rollback()
    assert r.status_code == 409 and r.json()["error"]["code"] == "CONFLICT"
    assert "laura@mail.com" not in r.text


def test_quien_fue_no_apto_no_choca_con_el_indice(client, login, vacantes, db):
    """El índice excluye a los `no_apto`: pueden volver a postularse (decisión 5.9)."""
    if db.get_bind().dialect.name != "postgresql":
        pytest.skip("El índice único solo existe en Postgres (TEST_DATABASE_URL).")
    from tests.helpers import validador

    c = _cand(db, vacantes["activa"], "nuevo")
    c.estado = "no_apto"
    db.add(Estado(candidato_id=c.id, estado="no_apto", validado_por=validador(db, "no_apto")))
    db.commit()
    _cand(db, vacantes["activa"], "nuevo")  # misma persona, misma vacante: permitido
