import logging
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.orm import Vacante

T0 = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
CORREO_PRIVADO = "maria.perez@ejemplo.com"


def _v(db, slug, urgente=False, dias=0, activa=True, cargo=None):
    v = Vacante(
        codigo=slug.upper(),
        slug=slug,
        cargo=cargo or slug,
        ciudad="Bogotá",
        modalidad="remoto",
        activa=activa,
        urgente=urgente,
        responsabilidades=[],
        publicada_en=T0 + timedelta(days=dias),
    )
    db.add(v)
    db.commit()
    return v


# ---------- lista pública: urgentes primero, luego las más recientes ----------
def test_lista_publica_ordena_urgentes_y_luego_por_fecha(client, db):
    _v(db, "vieja", dias=1)
    _v(db, "reciente", dias=9)
    _v(db, "urgente-vieja", urgente=True, dias=2)
    _v(db, "urgente-reciente", urgente=True, dias=8)
    slugs = [v["slug"] for v in client.get("/api/vacantes").json()["items"]]
    assert slugs == ["urgente-reciente", "urgente-vieja", "reciente", "vieja"]


def test_el_total_es_real_y_no_depende_de_la_pagina(client, db):
    for i in range(7):
        _v(db, f"v{i}", dias=i)
    _v(db, "inactiva", activa=False)  # no cuenta
    p = client.get("/api/vacantes?page=2&page_size=3").json()
    assert p["total"] == 7 and len(p["items"]) == 3 and p["page"] == 2
    ultima = client.get("/api/vacantes?page=3&page_size=3").json()
    assert ultima["total"] == 7 and len(ultima["items"]) == 1
    assert client.get("/api/vacantes?q=v1").json()["total"] == 1  # el total respeta los filtros


def test_el_orden_se_conserva_entre_paginas(client, db):
    _v(db, "a", dias=1)
    _v(db, "b", urgente=True, dias=0)
    _v(db, "c", dias=5)
    pag1 = [v["slug"] for v in client.get("/api/vacantes?page=1&page_size=2").json()["items"]]
    pag2 = [v["slug"] for v in client.get("/api/vacantes?page=2&page_size=2").json()["items"]]
    assert pag1 + pag2 == ["b", "c", "a"]


# ---------- urgente en el detalle ----------
def test_el_detalle_publico_trae_urgente(client, db):
    _v(db, "con-urgencia", urgente=True)
    _v(db, "normal")
    assert client.get("/api/vacantes/con-urgencia").json()["urgente"] is True
    assert client.get("/api/vacantes/normal").json()["urgente"] is False


# ---------- manejador global de 500 ----------
def test_error_inesperado_responde_con_el_formato_del_contrato_y_sin_datos_personales(caplog):
    def boom():
        raise RuntimeError(f"falló insertando a {CORREO_PRIVADO}")  # como un error de la base

    app.dependency_overrides[get_db] = boom
    try:
        with caplog.at_level(logging.ERROR, logger="immpetus.errores"):
            r = TestClient(app, raise_server_exceptions=False).get("/api/vacantes")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert r.status_code == 500
    assert r.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Ocurrió un error inesperado. Intenta de nuevo.",
            "field": None,
        }
    }
    assert "RuntimeError" in caplog.text and "/api/vacantes" in caplog.text
    assert (
        "maria.perez@ejemplo.com" not in caplog.text
    )  # el mensaje de la excepción nunca se registra
    assert "Traceback" not in r.text and "RuntimeError" not in r.text  # nada interno al cliente


def test_los_errores_esperados_no_pasan_por_el_manejador_de_500(client):
    assert client.get("/api/vacantes/no-existe").json()["error"]["code"] == "NOT_FOUND"
    assert client.get("/api/admin/me").json()["error"]["code"] == "UNAUTHENTICATED"
