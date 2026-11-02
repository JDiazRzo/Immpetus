import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.orm import Candidato, CandidatoHabilidad, Estado, Habilidad
from tests.helpers import validador

T0 = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def _cand(db, vacante, nombre="Cand", estado="reserva", correo=None, futuras=True, **extra):
    c = Candidato(
        vacante_id=vacante.id,
        nombre=nombre,
        correo=correo or f"{uuid.uuid4().hex[:6]}@x.co",
        celular="300",
        canal="web",
        estado=estado,
        autorizacion_datos=True,
        autorizacion_fecha=T0,
        autorizacion_version="1.0",
        drive_file_id="f-1",
        drive_url="https://drive.invalid/f-1",
        archivo_nombre="3 - X.pdf",
        acepta_futuras=futuras,
        acepta_futuras_fecha=T0 if futuras else None,
        **extra,
    )
    db.add(c)
    db.flush()
    db.add(Estado(candidato_id=c.id, validado_por=validador(db, estado), estado=estado))
    db.commit()
    return c


def _hab(db, nombre):
    h = Habilidad(nombre=nombre, categoria="herramienta")
    db.add(h)
    db.commit()
    return h


def test_busca_solo_reserva_con_todas_las_habilidades(client, login, vacantes, db):
    login("analista")
    a, b = _hab(db, "Excel"), _hab(db, "SQL")
    c1, c2 = _cand(db, vacantes["activa"], "Ambas"), _cand(db, vacantes["activa"], "Solo Excel")
    c3 = _cand(db, vacantes["activa"], "No reserva", estado="nuevo")
    db.add_all(
        [
            CandidatoHabilidad(candidato_id=c1.id, habilidad_id=a.id),
            CandidatoHabilidad(candidato_id=c1.id, habilidad_id=b.id),
            CandidatoHabilidad(candidato_id=c2.id, habilidad_id=a.id),
            CandidatoHabilidad(candidato_id=c3.id, habilidad_id=a.id),
        ]
    )
    db.commit()
    r = client.get(f"/api/admin/reserva?habilidad_id={a.id}&habilidad_id={b.id}").json()
    assert [c["nombre"] for c in r["items"]] == ["Ambas"] and r["total"] == 1
    r = client.get(f"/api/admin/reserva?habilidad_id={a.id}").json()
    assert {c["nombre"] for c in r["items"]} == {"Ambas", "Solo Excel"}
    assert client.get("/api/admin/reserva").json()["total"] == 2


def test_busca_por_cargo_y_excluye_anonimizados(client, login, vacantes, db):
    login("gerencia")
    _cand(db, vacantes["activa"], "Soporte")
    _cand(db, vacantes["otra"], "Admin")
    _cand(db, vacantes["activa"], "Anon", anonimizado_en=T0)
    r = client.get("/api/admin/reserva?cargo=soporte").json()
    assert [c["nombre"] for c in r["items"]] == ["Soporte"]


def test_asociar_crea_nueva_postulacion_y_deja_el_original(client, login, vacantes, db):
    me = login("analista")
    h = _hab(db, "Excel")
    origen = _cand(db, vacantes["activa"], "María", correo="maria@x.co")
    db.add(CandidatoHabilidad(candidato_id=origen.id, habilidad_id=h.id))
    db.commit()
    r = client.post(
        f"/api/admin/reserva/{origen.id}/asociar", json={"vacante_id": str(vacantes["otra"].id)}
    )
    assert r.status_code == 201
    j = r.json()
    assert j["vacante_id"] == str(vacantes["otra"].id) and j["estado"] == "nuevo"
    assert j["nota"] is None and j["habilidades"][0]["nombre"] == "Excel"
    db.refresh(origen)
    assert origen.estado == "reserva"  # el original sigue en la Reserva
    nuevo = db.get(Candidato, uuid.UUID(j["id"]))
    assert nuevo.autorizacion_version == "1.0" and nuevo.drive_file_id == "f-1"
    fila = db.scalar(select(Estado).where(Estado.candidato_id == nuevo.id))
    assert str(fila.validado_por) == me["id"] and "Reserva" in fila.observacion


def test_asociar_validaciones(client, login, vacantes, db):
    login("analista")
    origen = _cand(db, vacantes["activa"], correo="maria@x.co")
    url = f"/api/admin/reserva/{origen.id}/asociar"
    assert (
        client.post(url, json={"vacante_id": str(vacantes["activa"].id)}).status_code == 409
    )  # misma
    assert client.post(url, json={"vacante_id": str(vacantes["inactiva"].id)}).status_code == 409
    assert client.post(url, json={"vacante_id": str(uuid.uuid4())}).status_code == 404
    _cand(db, vacantes["otra"], "Ya está", correo="MARIA@x.co")
    assert (
        client.post(url, json={"vacante_id": str(vacantes["otra"].id)}).status_code == 409
    )  # duplicado
    no_reserva = _cand(db, vacantes["activa"], estado="nuevo")
    r = client.post(
        f"/api/admin/reserva/{no_reserva.id}/asociar", json={"vacante_id": str(vacantes["otra"].id)}
    )
    assert r.status_code == 409
    anon = _cand(db, vacantes["activa"], anonimizado_en=T0)
    r = client.post(
        f"/api/admin/reserva/{anon.id}/asociar", json={"vacante_id": str(vacantes["otra"].id)}
    )
    assert r.status_code == 409


def test_gerencia_no_puede_asociar(client, login, vacantes, db):
    login("gerencia")
    origen = _cand(db, vacantes["activa"])
    r = client.post(
        f"/api/admin/reserva/{origen.id}/asociar", json={"vacante_id": str(vacantes["otra"].id)}
    )
    assert r.status_code == 403
    assert client.get("/api/admin/reserva").status_code == 200


def test_reserva_exige_sesion(client):
    assert client.get("/api/admin/reserva").status_code == 401
