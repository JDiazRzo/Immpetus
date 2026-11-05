import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.orm import Candidato, CorreoSinAsignar, Estado, Vacante
from tests.helpers import validador

CERRADA = "La convocatoria está cerrada."
T0 = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def _cand(db, vacante, estado="nuevo", futuras=False, correo=None, **extra):
    c = Candidato(
        vacante_id=vacante.id,
        nombre="Cand",
        correo=correo or f"{uuid.uuid4().hex[:6]}@x.co",
        canal="web",
        estado=estado,
        autorizacion_datos=True,
        autorizacion_fecha=T0,
        autorizacion_version="1.0",
        acepta_futuras=futuras,
        acepta_futuras_fecha=T0 if futuras else None,
        **extra,
    )
    db.add(c)
    db.flush()
    db.add(Estado(candidato_id=c.id, estado=estado, validado_por=validador(db, estado)))
    db.commit()
    return c


def _cerrar(client, vacante, motivo="Cargo cubierto"):
    return client.post(f"/api/admin/vacantes/{vacante.id}/cerrar", json={"motivo": motivo})


# ---------- POST /vacantes/{id}/cerrar ----------
def test_cerrar_deja_estado_activa_y_trazabilidad(client, login, vacantes, db):
    me = login("lider")
    r = _cerrar(client, vacantes["activa"])
    assert r.status_code == 200
    j = r.json()
    assert j["estado"] == "cerrada" and j["activa"] is False
    assert j["cerrada_en"] and j["motivo_cierre"] == "Cargo cubierto"
    db.refresh(vacantes["activa"])
    assert str(vacantes["activa"].cerrada_por) == me["id"]


def test_una_cerrada_desaparece_de_la_web_publica(client, login, vacantes):
    login("lider")
    assert client.get("/api/vacantes/gestor-soporte").status_code == 200
    _cerrar(client, vacantes["activa"])
    assert client.get("/api/vacantes/gestor-soporte").status_code == 404
    assert "gestor-soporte" not in [v["slug"] for v in client.get("/api/vacantes").json()["items"]]


def test_la_cerrada_no_recibe_postulaciones(client, login, vacantes):
    login("lider")
    _cerrar(client, vacantes["activa"])
    r = client.post(
        "/api/postulaciones",
        data={
            "vacante_id": str(vacantes["activa"].id),
            "nombre": "Ana Prueba",
            "correo": "ana@ejemplo.com",
            "celular": "3001234567",
            "autorizacion_datos": "true",
        },
        files={"archivo": ("hv.pdf", b"%PDF-1.4 x", "application/pdf")},
    )
    assert r.status_code == 404


def test_cerrar_dos_veces_da_409(client, login, vacantes):
    login("lider")
    assert _cerrar(client, vacantes["activa"]).status_code == 200
    r = _cerrar(client, vacantes["activa"])
    assert r.status_code == 409 and r.json()["error"]["code"] == "CONFLICT"


def test_cerrar_exige_motivo_y_no_acepta_extras(client, login, vacantes):
    login("lider")
    url = f"/api/admin/vacantes/{vacantes['activa'].id}/cerrar"
    for cuerpo in (
        {},
        {"motivo": ""},
        {"motivo": "  "},
        {"motivo": "ab"},
        {"motivo": "x" * 501},
        {"motivo": "Cargo cubierto", "activa": True},
    ):
        r = client.post(url, json=cuerpo)
        assert r.status_code == 400, cuerpo
    assert client.get(f"/api/admin/vacantes/{vacantes['activa'].id}").json()["estado"] == "abierta"


def test_cerrar_vacante_inexistente_da_404(client, login):
    login("lider")
    assert (
        client.post(
            f"/api/admin/vacantes/{uuid.uuid4()}/cerrar", json={"motivo": "Cargo cubierto"}
        ).status_code
        == 404
    )


# ---------- GET /vacantes?estado= ----------
def test_el_listado_admin_trae_solo_abiertas_por_defecto(client, login, vacantes):
    login("analista")
    lider = login("lider")  # solo el líder cierra
    assert lider["rol"] == "lider"
    _cerrar(client, vacantes["otra"])
    abiertas = client.get("/api/admin/vacantes").json()
    assert abiertas["total"] == 2 and all(v["estado"] == "abierta" for v in abiertas["items"])
    assert client.get("/api/admin/vacantes?estado=abierta").json()["total"] == 2
    cerradas = client.get("/api/admin/vacantes?estado=cerrada").json()
    assert cerradas["total"] == 1 and cerradas["items"][0]["id"] == str(vacantes["otra"].id)
    assert cerradas["items"][0]["cerrada_en"]
    assert client.get("/api/admin/vacantes?estado=todas").status_code == 400


def test_vacante_abierta_trae_estado_y_cerrada_en_nulo(client, login, vacantes):
    login("gerencia")
    v = client.get(f"/api/admin/vacantes/{vacantes['activa'].id}").json()
    assert v["estado"] == "abierta" and v["cerrada_en"] is None and v["motivo_cierre"] is None


def test_una_vacante_nueva_nace_abierta(client, login):
    login("analista")
    v = client.post(
        "/api/admin/vacantes",
        json={"cargo": "Cargo nuevo", "ciudad": "Bogotá", "modalidad": "remoto"},
    ).json()
    assert v["estado"] == "abierta"


# ---------- acciones sobre una cerrada → 409 ----------
def test_no_se_edita_ni_se_reactiva_una_cerrada(client, login, vacantes):
    login("lider")
    _cerrar(client, vacantes["activa"])
    for cuerpo in ({"cargo": "Otro cargo distinto"}, {"activa": True}, {}):
        r = client.patch(f"/api/admin/vacantes/{vacantes['activa'].id}", json=cuerpo)
        assert r.status_code == 409 and r.json()["error"]["message"] == CERRADA, cuerpo


def test_no_se_decide_sobre_candidatos_de_una_cerrada(client, login, vacantes, db):
    login("lider")
    c = _cand(db, vacantes["activa"])
    _cerrar(client, vacantes["activa"])
    r = client.post(f"/api/admin/candidatos/{c.id}/estado", json={"estado": "entrevista"})
    assert r.status_code == 409 and r.json()["error"]["message"] == CERRADA
    r = client.post(
        f"/api/admin/candidatos/{c.id}/calificacion", json={"nota": 4, "motivo": "motivo válido"}
    )
    assert r.status_code == 409 and r.json()["error"]["message"] == CERRADA
    db.refresh(c)
    assert c.estado == "nuevo"


def test_no_se_asocia_ni_se_asigna_hacia_una_cerrada(client, login, vacantes, db):
    login("lider")
    origen = _cand(db, vacantes["activa"], estado="reserva", futuras=True)
    m = CorreoSinAsignar(
        gmail_id="g1", remitente="Ana <ana@mail.com>", drive_file_id="d1", recibido_en=T0
    )
    db.add(m)
    db.commit()
    _cerrar(client, vacantes["otra"])
    destino = {"vacante_id": str(vacantes["otra"].id)}
    r = client.post(f"/api/admin/reserva/{origen.id}/asociar", json=destino)
    assert r.status_code == 409 and r.json()["error"]["message"] == CERRADA
    r = client.post(f"/api/admin/correos-sin-asignar/{m.id}/asignar", json=destino)
    assert r.status_code == 409 and r.json()["error"]["message"] == CERRADA
    assert (
        db.scalar(select(CorreoSinAsignar).where(CorreoSinAsignar.asignado_a.is_not(None))) is None
    )


# ---------- lo que SÍ se puede hacer con una cerrada ----------
def test_una_cerrada_sigue_siendo_consultable_y_su_reserva_se_reutiliza(
    client, login, vacantes, db
):
    login("lider")
    reserva = _cand(db, vacantes["activa"], estado="reserva", futuras=True)
    _cerrar(client, vacantes["activa"])
    vid = vacantes["activa"].id
    assert client.get(f"/api/admin/vacantes/{vid}").status_code == 200
    assert client.get(f"/api/admin/vacantes/{vid}/resumen").json()["reserva"] == 1
    assert client.get(f"/api/admin/vacantes/{vid}/candidatos").json()["total"] == 1
    assert client.get(f"/api/admin/candidatos/{reserva.id}").status_code == 200
    assert client.get("/api/admin/reserva").json()["total"] == 1  # su reserva sigue disponible
    # …y se puede asociar DESDE una convocatoria cerrada HACIA una abierta
    r = client.post(
        f"/api/admin/reserva/{reserva.id}/asociar", json={"vacante_id": str(vacantes["otra"].id)}
    )
    assert r.status_code == 201


def test_se_puede_anonimizar_y_reportar_aunque_este_cerrada(
    client, login, vacantes, db, integraciones
):
    login("lider")
    c = _cand(db, vacantes["activa"], correo="m@x.co")
    _cerrar(client, vacantes["activa"])
    assert (
        client.post(f"/api/admin/candidatos/{c.id}/anonimizar").status_code == 200
    )  # derecho de supresión
    r = client.post(
        f"/api/admin/vacantes/{vacantes['activa'].id}/reporte",
        json={"destinatarios": ["g@immpetus.co"]},
    )
    assert r.status_code == 202


def test_las_demas_convocatorias_no_se_afectan(client, login, vacantes, db):
    login("lider")
    otra = _cand(db, vacantes["otra"])
    _cerrar(client, vacantes["activa"])
    assert (
        client.post(
            f"/api/admin/candidatos/{otra.id}/estado", json={"estado": "entrevista"}
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/admin/vacantes/{vacantes['otra'].id}", json={"cargo": "Cargo distinto"}
        ).status_code
        == 200
    )
    assert db.get(Vacante, vacantes["otra"].id).estado == "abierta"
