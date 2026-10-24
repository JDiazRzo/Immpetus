import uuid
from datetime import UTC, datetime

from app.orm import Calificacion, Candidato, CorreoSinAsignar, Estado

T0 = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def _cand(
    db, vacante, nombre="Marta Ruiz", correo="marta@x.co", nota=None, estado="nuevo", file_id="f-1"
):
    c = Candidato(
        vacante_id=vacante.id,
        nombre=nombre,
        correo=correo,
        celular="300",
        canal="web",
        estado=estado,
        autorizacion_datos=True,
        autorizacion_fecha=T0,
        autorizacion_version="1.0",
        drive_file_id=file_id,
        drive_url="https://drive.invalid/x",
        archivo_nombre="4 - M.pdf",
    )
    db.add(c)
    db.flush()
    db.add(Estado(candidato_id=c.id, estado=estado))
    if nota:
        db.add(
            Calificacion(
                candidato_id=c.id, nota=nota, origen="ia", resumen="Vive en Chapinero, 34 años"
            )
        )
    db.commit()
    return c


# ---------- anonimizar ----------
def test_anonimiza_todas_las_postulaciones_del_titular(client, login, vacantes, db, integraciones):
    me = login("lider")
    a = _cand(db, vacantes["activa"], nota=4)
    b = _cand(db, vacantes["otra"], correo="MARTA@x.co")  # mismo titular, otra vacante, mismo PDF
    otro = _cand(db, vacantes["activa"], "Otro", "otro@x.co", file_id="f-2")
    sin_asignar = CorreoSinAsignar(
        gmail_id="g1",
        remitente="Marta <marta@x.co>",
        asunto="HV",
        archivo_nombre="m.pdf",
        drive_file_id="f-3",
        recibido_en=T0,
    )
    db.add(sin_asignar)
    db.commit()
    r = client.post(f"/api/admin/candidatos/{a.id}/anonimizar")
    assert r.status_code == 200
    j = r.json()
    assert j["nombre"] == "Titular anonimizado" and j["correo"].endswith("@invalid.local")
    assert j["celular"] is None and j["drive_url"] is None and j["archivo_nombre"] is None
    for fila in (a, b):
        db.refresh(fila)
        assert fila.anonimizado_en is not None and fila.drive_file_id is None
    db.refresh(otro)
    assert otro.anonimizado_en is None and otro.nombre == "Otro"  # otros titulares intactos
    db.refresh(sin_asignar)
    assert (
        sin_asignar.remitente == "anonimizado@invalid.local" and sin_asignar.drive_file_id is None
    )
    assert sorted(integraciones["borrados"]) == ["f-1", "f-3"]  # PDF compartido se borra una vez
    # el historial queda (inmodificable) y deja constancia, sin datos personales
    ev = db.query(Estado).filter_by(candidato_id=a.id).order_by(Estado.fecha).all()[-1]
    assert (
        str(ev.validado_por) == me["id"] and "Ley 1581" in ev.observacion and ev.estado == "nuevo"
    )
    assert db.query(Calificacion).filter_by(candidato_id=a.id).count() == 1  # no se borra


def test_anonimizado_no_expone_resumen_ni_se_repite(client, login, vacantes, db):
    login("lider")
    a = _cand(db, vacantes["activa"], nota=4)
    client.post(f"/api/admin/candidatos/{a.id}/anonimizar")
    d = client.get(f"/api/admin/candidatos/{a.id}").json()
    assert d["resumen_ia"] is None and d["matriz"] is None and d["nombre"] == "Titular anonimizado"
    assert client.post(f"/api/admin/candidatos/{a.id}/anonimizar").status_code == 409


def test_si_drive_falla_no_se_anonimiza_nada(client, login, vacantes, db, integraciones):
    login("lider")
    a = _cand(db, vacantes["activa"])
    integraciones["falla_drive"] = True
    r = client.post(f"/api/admin/candidatos/{a.id}/anonimizar")
    assert r.status_code == 502 and r.json()["error"]["code"] == "STORAGE_ERROR"
    db.refresh(a)
    assert a.anonimizado_en is None and a.nombre == "Marta Ruiz"


def test_solo_el_lider_puede_anonimizar(client, login, vacantes, db):
    a = _cand(db, vacantes["activa"])
    for rol in ("analista", "gerencia"):
        login(rol)
        r = client.post(f"/api/admin/candidatos/{a.id}/anonimizar")
        assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN"
    assert client.post(f"/api/admin/candidatos/{uuid.uuid4()}/anonimizar").status_code in (403, 404)


# ---------- reporte ----------
def test_reporte_envia_ranking_sin_no_aptos_ni_anonimizados(
    client, login, vacantes, db, integraciones
):
    login("analista")
    v = vacantes["activa"]
    _cand(db, v, "Ana <script>", "a@x.co", nota=5)
    _cand(db, v, "Beto", "b@x.co", nota=3, estado="reserva")
    _cand(db, v, "Descartado", "d@x.co", nota=1, estado="no_apto")
    r = client.post(
        f"/api/admin/vacantes/{v.id}/reporte",
        json={"destinatarios": ["Gerencia@immpetus.co", "gerencia@immpetus.co"]},
    )
    assert r.status_code == 202 and r.json() == {"enviado": True}
    ((para, html),) = integraciones["correos"]
    assert para == ["gerencia@immpetus.co"]  # normaliza y quita repetidos
    assert "Gestor de Soporte" in html and "Beto" in html and "Descartado" not in html
    assert "<script>" not in html and "&lt;script&gt;" in html  # HTML escapado
    assert "<title>" in html  # Fabian lo usa como asunto
    assert html.index("Ana") < html.index("Beto")  # ordenado por nota


def test_reporte_validaciones(client, login, vacantes, integraciones):
    login("lider")
    url = f"/api/admin/vacantes/{vacantes['activa'].id}/reporte"
    for body in ({"destinatarios": []}, {"destinatarios": ["no-es-correo"]}, {}):
        r = client.post(url, json=body)
        assert r.status_code == 400 and r.json()["error"]["field"] == "destinatarios"
    r = client.post(url, json={"destinatarios": ["jefe@gmail.com"]})
    assert r.status_code == 400 and "@immpetus.co" in r.json()["error"]["message"]
    assert (
        client.post(
            f"/api/admin/vacantes/{uuid.uuid4()}/reporte", json={"destinatarios": ["a@immpetus.co"]}
        ).status_code
        == 404
    )
    assert integraciones["correos"] == []


def test_reporte_si_gmail_falla_da_502(client, login, vacantes, integraciones):
    login("analista")
    integraciones["falla_correo"] = True
    r = client.post(
        f"/api/admin/vacantes/{vacantes['activa'].id}/reporte",
        json={"destinatarios": ["g@immpetus.co"]},
    )
    assert r.status_code == 502 and r.json()["error"]["code"] == "EMAIL_ERROR"


def test_reporte_vacio_y_gerencia_no_envia(client, login, vacantes, integraciones):
    login("analista")
    client.post(
        f"/api/admin/vacantes/{vacantes['otra'].id}/reporte",
        json={"destinatarios": ["g@immpetus.co"]},
    )
    assert "Aún no hay candidatos calificados" in integraciones["correos"][0][1]
    login("gerencia")
    r = client.post(
        f"/api/admin/vacantes/{vacantes['otra'].id}/reporte",
        json={"destinatarios": ["g@immpetus.co"]},
    )
    assert r.status_code == 403
