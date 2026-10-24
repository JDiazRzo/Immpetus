import uuid
from datetime import UTC, datetime

from app.orm import Candidato, CorreoSinAsignar, Estado

T0 = datetime(2026, 10, 22, 9, 0, tzinfo=UTC)


def _correo(
    db, remitente="Laura Gómez <laura@mail.com>", archivo="hv laura.pdf", drive="d-9", **extra
):
    m = CorreoSinAsignar(
        gmail_id=uuid.uuid4().hex,
        remitente=remitente,
        asunto="Postulación",
        archivo_nombre=archivo,
        drive_file_id=drive,
        recibido_en=T0,
        **extra,
    )
    db.add(m)
    db.commit()
    return m


def test_lista_solo_pendientes(client, login, db, vacantes):
    login("analista")
    pendiente = _correo(db)
    ya = _correo(db, "Otro <o@mail.com>")
    c = Candidato(
        vacante_id=vacantes["activa"].id,
        nombre="x",
        correo="o@mail.com",
        canal="correo",
        autorizacion_datos=True,
        autorizacion_fecha=T0,
        autorizacion_version="correo-1.0",
    )
    db.add(c)
    db.flush()
    ya.asignado_a = c.id
    db.commit()
    r = client.get("/api/admin/correos-sin-asignar").json()
    assert r["total"] == 1 and r["items"][0]["id"] == str(pendiente.id)
    assert r["items"][0]["archivo_nombre"] == "hv laura.pdf"


def test_asignar_crea_candidato_mueve_pdf_y_enlaza(client, login, db, vacantes, integraciones):
    me = login("analista")
    m = _correo(db)
    r = client.post(
        f"/api/admin/correos-sin-asignar/{m.id}/asignar",
        json={"vacante_id": str(vacantes["activa"].id)},
    )
    assert r.status_code == 201
    j = r.json()
    assert (j["nombre"], j["correo"], j["canal"], j["estado"]) == (
        "Laura Gómez",
        "laura@mail.com",
        "correo",
        "nuevo",
    )
    assert j["nota"] is None and j["archivo_nombre"] == "hv laura.pdf"
    assert integraciones["movidos"] == [("d-9", "GSC-1")]
    db.refresh(m)
    assert str(m.asignado_a) == j["id"]
    cand = db.get(Candidato, uuid.UUID(j["id"]))
    assert cand.autorizacion_version == "correo-1.0" and cand.autorizacion_datos
    fila = db.query(Estado).filter_by(candidato_id=cand.id).one()
    assert str(fila.validado_por) == me["id"]
    # ya asignado: no se puede asignar otra vez ni sale en la bandeja
    again = client.post(
        f"/api/admin/correos-sin-asignar/{m.id}/asignar",
        json={"vacante_id": str(vacantes["activa"].id)},
    )
    assert again.status_code == 404
    assert client.get("/api/admin/correos-sin-asignar").json()["total"] == 0


def test_asignar_usa_el_correo_si_no_hay_nombre(client, login, db, vacantes):
    login("lider")
    m = _correo(db, "ana.perez@mail.com")
    j = client.post(
        f"/api/admin/correos-sin-asignar/{m.id}/asignar",
        json={"vacante_id": str(vacantes["activa"].id)},
    ).json()
    assert j["nombre"] == "ana.perez"


def test_asignar_errores(client, login, db, vacantes, integraciones):
    login("analista")
    m = _correo(db)
    url = f"/api/admin/correos-sin-asignar/{m.id}/asignar"
    assert client.post(url, json={"vacante_id": str(uuid.uuid4())}).status_code == 404
    integraciones["falla_drive"] = True
    r = client.post(url, json={"vacante_id": str(vacantes["activa"].id)})
    assert r.status_code == 502 and r.json()["error"]["code"] == "STORAGE_ERROR"
    db.refresh(m)
    assert m.asignado_a is None and db.query(Candidato).count() == 0  # nada quedó a medias
    integraciones["falla_drive"] = False
    sin_pdf = _correo(db, "Sin <s@mail.com>", drive=None)
    r = client.post(
        f"/api/admin/correos-sin-asignar/{sin_pdf.id}/asignar",
        json={"vacante_id": str(vacantes["activa"].id)},
    )
    assert r.status_code == 409
    malo = _correo(db, "sin arroba")
    r = client.post(
        f"/api/admin/correos-sin-asignar/{malo.id}/asignar",
        json={"vacante_id": str(vacantes["activa"].id)},
    )
    assert r.status_code == 400


def test_asignar_duplicado_en_la_misma_vacante_da_409(client, login, db, vacantes):
    login("analista")
    primero = _correo(db)
    segundo = _correo(db, "Laura <LAURA@mail.com>", drive="d-10")
    body = {"vacante_id": str(vacantes["activa"].id)}
    assert (
        client.post(f"/api/admin/correos-sin-asignar/{primero.id}/asignar", json=body).status_code
        == 201
    )
    assert (
        client.post(f"/api/admin/correos-sin-asignar/{segundo.id}/asignar", json=body).status_code
        == 409
    )


def test_gerencia_ve_pero_no_asigna(client, login, db, vacantes):
    login("gerencia")
    m = _correo(db)
    assert client.get("/api/admin/correos-sin-asignar").status_code == 200
    r = client.post(
        f"/api/admin/correos-sin-asignar/{m.id}/asignar",
        json={"vacante_id": str(vacantes["activa"].id)},
    )
    assert r.status_code == 403
