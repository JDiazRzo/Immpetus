import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.orm import Candidato, CandidatoHabilidad, CorreoSinAsignar, Estado, Habilidad
from tests.helpers import validador

PDF = b"%PDF-1.4 hoja de vida inventada"
T0 = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def _post(client, vacante, correo="ana@ejemplo.com", **extra):
    datos = {
        "vacante_id": str(vacante.id),
        "nombre": "Ana Prueba",
        "correo": correo,
        "celular": "3001234567",
        "autorizacion_datos": "true",
        **extra,
    }
    return client.post(
        "/api/postulaciones", data=datos, files={"archivo": ("hv.pdf", PDF, "application/pdf")}
    )


def _cand(db, vacante, estado="reserva", futuras=True, correo=None, **extra):
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
    db.add(Estado(candidato_id=c.id, validado_por=validador(db, estado), estado=estado))
    db.commit()
    return c


# ---------- POST /api/postulaciones con autorizacion_futuras ----------
def test_por_defecto_no_acepta_futuras(client, vacantes, db):
    assert _post(client, vacantes["activa"]).status_code == 201
    c = db.scalar(select(Candidato))
    assert c.acepta_futuras is False and c.acepta_futuras_fecha is None


def test_acepta_futuras_guarda_bandera_y_fecha(client, vacantes, db):
    antes = datetime.now(UTC)
    assert _post(client, vacantes["activa"], autorizacion_futuras="true").status_code == 201
    c = db.scalar(select(Candidato))
    assert c.acepta_futuras is True
    fecha = c.acepta_futuras_fecha
    fecha = fecha if fecha.tzinfo else fecha.replace(tzinfo=UTC)
    assert fecha >= antes
    assert c.autorizacion_fecha is not None  # la autorización obligatoria es independiente


def test_futuras_false_explicito(client, vacantes, db):
    assert _post(client, vacantes["activa"], autorizacion_futuras="false").status_code == 201
    assert db.scalar(select(Candidato)).acepta_futuras is False


def test_futuras_invalido_da_400(client, vacantes):
    r = _post(client, vacantes["activa"], autorizacion_futuras="quizas")
    assert r.status_code == 400 and r.json()["error"]["field"] == "autorizacion_futuras"


def test_futuras_sin_autorizacion_obligatoria_sigue_dando_400(client, vacantes, db):
    r = _post(client, vacantes["activa"], autorizacion_datos="false", autorizacion_futuras="true")
    assert r.status_code == 400 and r.json()["error"]["field"] == "autorizacion_datos"
    assert db.scalar(select(Candidato)) is None


# ---------- 409 por postulación duplicada ----------
def test_misma_persona_misma_vacante_da_409_y_no_sube_el_pdf(client, vacantes, db, subidas):
    assert _post(client, vacantes["activa"]).status_code == 201
    r = _post(client, vacantes["activa"], correo="ANA@ejemplo.com")  # sin distinguir mayúsculas
    assert r.status_code == 409 and r.json()["error"]["code"] == "CONFLICT"
    assert db.query(Candidato).count() == 1 and len(subidas) == 1  # Drive no se vuelve a llamar


def test_misma_persona_otra_vacante_si_puede(client, vacantes):
    assert _post(client, vacantes["activa"]).status_code == 201
    assert _post(client, vacantes["otra"]).status_code == 201


def test_quien_fue_no_apto_puede_volver_a_postularse(client, vacantes, db):
    _cand(db, vacantes["activa"], estado="no_apto", correo="ana@ejemplo.com")
    # (no_apto exige validado_por; el helper inserta solo el estado de prueba)
    assert _post(client, vacantes["activa"]).status_code == 201


def test_un_anonimizado_no_bloquea_a_nadie(client, vacantes, db):
    _cand(db, vacantes["activa"], estado="nuevo", correo="ana@ejemplo.com", anonimizado_en=T0)
    assert _post(client, vacantes["activa"]).status_code == 201


def test_duplicado_tambien_aplica_al_asignar_correo(client, login, vacantes, db):
    login("analista")
    _cand(db, vacantes["activa"], estado="nuevo", correo="laura@mail.com")
    m = CorreoSinAsignar(
        gmail_id="g1", remitente="Laura <laura@mail.com>", drive_file_id="d1", recibido_en=T0
    )
    db.add(m)
    db.commit()
    r = client.post(
        f"/api/admin/correos-sin-asignar/{m.id}/asignar",
        json={"vacante_id": str(vacantes["activa"].id)},
    )
    assert r.status_code == 409


# ---------- Reserva Estratégica ----------
def test_reserva_solo_muestra_a_quien_acepto(client, login, vacantes, db):
    login("analista")
    si = _cand(db, vacantes["activa"], futuras=True)
    _cand(db, vacantes["activa"], futuras=False)
    r = client.get("/api/admin/reserva").json()
    assert r["total"] == 1 and r["items"][0]["id"] == str(si.id)
    assert r["items"][0]["acepta_futuras"] is True


def test_reserva_con_filtro_de_habilidad_tambien_respeta_la_autorizacion(
    client, login, vacantes, db
):
    login("analista")
    h = Habilidad(nombre="Excel", categoria="herramienta")
    db.add(h)
    db.commit()
    for futuras in (True, False):
        c = _cand(db, vacantes["activa"], futuras=futuras)
        db.add(CandidatoHabilidad(candidato_id=c.id, habilidad_id=h.id))
    db.commit()
    assert client.get(f"/api/admin/reserva?habilidad_id={h.id}").json()["total"] == 1


def test_asociar_sin_autorizacion_da_409(client, login, vacantes, db):
    login("analista")
    sin = _cand(db, vacantes["activa"], futuras=False)
    r = client.post(
        f"/api/admin/reserva/{sin.id}/asociar", json={"vacante_id": str(vacantes["otra"].id)}
    )
    assert r.status_code == 409 and "autorizó" in r.json()["error"]["message"]
    assert db.query(Candidato).count() == 1  # no se creó nada


def test_asociar_conserva_la_autorizacion_y_su_fecha(client, login, vacantes, db):
    login("analista")
    origen = _cand(db, vacantes["activa"], futuras=True)
    r = client.post(
        f"/api/admin/reserva/{origen.id}/asociar", json={"vacante_id": str(vacantes["otra"].id)}
    )
    assert r.status_code == 201 and r.json()["acepta_futuras"] is True
    nuevo = db.get(Candidato, uuid.UUID(r.json()["id"]))
    assert nuevo.acepta_futuras is True and nuevo.acepta_futuras_fecha is not None


def test_los_de_correo_entran_sin_autorizacion_y_no_aparecen_en_la_reserva(
    client, login, vacantes, db
):
    login("analista")
    m = CorreoSinAsignar(
        gmail_id="g2", remitente="Ana <ana@mail.com>", drive_file_id="d2", recibido_en=T0
    )
    db.add(m)
    db.commit()
    j = client.post(
        f"/api/admin/correos-sin-asignar/{m.id}/asignar",
        json={"vacante_id": str(vacantes["activa"].id)},
    ).json()
    assert j["acepta_futuras"] is False
    c = db.get(Candidato, uuid.UUID(j["id"]))
    c.estado = "reserva"
    db.commit()
    assert client.get("/api/admin/reserva").json()["total"] == 0


# ---------- respuestas de candidatos ----------
def test_acepta_futuras_viene_en_lista_y_detalle(client, login, vacantes, db):
    login("gerencia")
    c = _cand(db, vacantes["activa"], estado="nuevo", futuras=True)
    lista = client.get(f"/api/admin/vacantes/{vacantes['activa'].id}/candidatos").json()
    assert lista["items"][0]["acepta_futuras"] is True
    assert client.get(f"/api/admin/candidatos/{c.id}").json()["acepta_futuras"] is True


# ---------- anonimizar retira la autorización ----------
def test_anonimizar_retira_la_autorizacion_para_futuras(client, login, vacantes, db):
    login("lider")
    a = _cand(db, vacantes["activa"], futuras=True, correo="m@x.co")
    b = _cand(db, vacantes["otra"], futuras=True, correo="M@x.co")
    client.post(f"/api/admin/candidatos/{a.id}/anonimizar")
    for fila in (a, b):
        db.refresh(fila)
        assert fila.acepta_futuras is False and fila.acepta_futuras_fecha is None
    assert client.get("/api/admin/reserva").json()["total"] == 0
