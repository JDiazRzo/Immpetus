import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.orm import Calificacion, Candidato, CandidatoHabilidad, Estado, Habilidad, VacanteHabilidad

T0 = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def _cand(db, vacante, nombre="Cand", estado="nuevo", nota=None, minutos=0, **extra):
    c = Candidato(
        vacante_id=vacante.id,
        nombre=nombre,
        correo=f"{uuid.uuid4().hex[:6]}@x.co",
        celular="300",
        canal="web",
        estado=estado,
        autorizacion_datos=True,
        autorizacion_fecha=T0,
        autorizacion_version="1.0",
        creado_en=T0 + timedelta(minutes=minutos),
        **extra,
    )
    db.add(c)
    db.flush()
    db.add(Estado(candidato_id=c.id, estado="nuevo", fecha=T0 + timedelta(minutes=minutos)))
    if nota:
        db.add(
            Calificacion(
                candidato_id=c.id,
                nota=nota,
                origen="ia",
                resumen="Resumen IA",
                matriz={"formacion": "Ing."},
                fecha=T0 + timedelta(minutes=minutos, seconds=5),
            )
        )
    db.commit()
    return c


def test_lista_ordenada_filtrada_y_paginada(client, login, vacantes, db):
    login("analista")
    v = vacantes["activa"]
    _cand(db, v, "A", nota=2, estado="por_validar", minutos=1)
    _cand(db, v, "B", nota=5, minutos=2)
    _cand(db, v, "C", nota=4, minutos=3)
    _cand(db, v, "D", minutos=4)  # sin calificar
    base = f"/api/admin/vacantes/{v.id}/candidatos"
    r = client.get(base + "?orden=nota_desc").json()
    assert [c["nombre"] for c in r["items"]] == ["B", "C", "A", "D"] and r["total"] == 4
    assert [c["nombre"] for c in client.get(base + "?estado=por_validar").json()["items"]] == ["A"]
    assert [c["nombre"] for c in client.get(base).json()["items"]] == ["D", "C", "B", "A"]
    p2 = client.get(base + "?orden=nota_desc&page=2&page_size=3").json()
    assert [c["nombre"] for c in p2["items"]] == ["D"] and p2["page"] == 2
    assert client.get(f"/api/admin/vacantes/{uuid.uuid4()}/candidatos").status_code == 404


def test_habilidades_marcan_coincidencia_con_la_vacante(client, login, vacantes, db):
    login("analista")
    zen, py = (
        Habilidad(nombre="Freshdesk", categoria="herramienta"),
        Habilidad(nombre="Python", categoria="tecnica"),
    )
    db.add_all([zen, py])
    db.flush()
    db.add(
        VacanteHabilidad(vacante_id=vacantes["activa"].id, habilidad_id=zen.id, obligatoria=True)
    )
    c = _cand(db, vacantes["activa"], nota=4)
    db.add_all(
        [
            CandidatoHabilidad(candidato_id=c.id, habilidad_id=zen.id),
            CandidatoHabilidad(candidato_id=c.id, habilidad_id=py.id),
        ]
    )
    db.commit()
    r = client.get(f"/api/admin/candidatos/{c.id}").json()
    assert r["habilidades"] == [
        {"nombre": "Freshdesk", "coincide": True},
        {"nombre": "Python", "coincide": False},
    ]


def test_cambiar_estado_registra_usuario_y_valida_la_nota(client, login, vacantes, db):
    me = login("analista")
    c = _cand(db, vacantes["activa"], nota=2, estado="por_validar")
    antes = client.get(f"/api/admin/candidatos/{c.id}").json()
    assert antes["nota_validada"] is False and antes["validada_por"] is None
    r = client.post(
        f"/api/admin/candidatos/{c.id}/estado",
        json={"estado": "no_apto", "observacion": " No cumple "},
    )
    assert r.status_code == 200 and r.json()["estado"] == "no_apto"
    assert r.json()["nota_validada"] is True and r.json()["validada_por"] == "Ana Analista"
    fila = db.query(Estado).filter_by(candidato_id=c.id, estado="no_apto").one()
    assert str(fila.validado_por) == me["id"] and fila.observacion == "No cumple"


@pytest.mark.parametrize(
    "desde,hacia",
    [
        ("no_apto", "entrevista"),
        ("contratado", "reserva"),
        ("nuevo", "contratado"),
        ("nuevo", "por_validar"),
        ("reserva", "reserva"),
    ],
)
def test_transiciones_invalidas_dan_409(client, login, vacantes, db, desde, hacia):
    login("analista")
    c = _cand(db, vacantes["activa"], estado=desde)
    r = client.post(f"/api/admin/candidatos/{c.id}/estado", json={"estado": hacia})
    assert r.status_code == 409 and r.json()["error"]["code"] == "CONFLICT"


def test_estado_desconocido_da_400(client, login, vacantes, db):
    login("analista")
    c = _cand(db, vacantes["activa"])
    assert (
        client.post(f"/api/admin/candidatos/{c.id}/estado", json={"estado": "volando"}).status_code
        == 400
    )


def test_corregir_nota_no_cambia_el_estado(client, login, vacantes, db):
    login("lider")
    c = _cand(db, vacantes["activa"], nota=3, estado="reserva")
    r = client.post(
        f"/api/admin/candidatos/{c.id}/calificacion",
        json={"nota": 1, "motivo": "Experiencia no equivalente"},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["nota"] == 1 and j["estado"] == "reserva"  # regla 5.4
    assert j["nota_validada"] is True and j["validada_por"] == "Luis Líder"
    assert db.query(Calificacion).filter_by(candidato_id=c.id).count() == 2  # historial intacto


def test_corregir_nota_exige_motivo_y_rango(client, login, vacantes, db):
    login("analista")
    c = _cand(db, vacantes["activa"], nota=3)
    url = f"/api/admin/candidatos/{c.id}/calificacion"
    assert client.post(url, json={"nota": 6, "motivo": "motivo válido"}).status_code == 400
    assert client.post(url, json={"nota": 4, "motivo": "  "}).status_code == 400
    assert client.post(url, json={"nota": 4}).status_code == 400


def test_gerencia_no_puede_cambiar_estado_ni_nota(client, login, vacantes, db):
    login("gerencia")
    c = _cand(db, vacantes["activa"], nota=3, estado="reserva")
    assert (
        client.post(
            f"/api/admin/candidatos/{c.id}/estado", json={"estado": "entrevista"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/admin/candidatos/{c.id}/calificacion",
            json={"nota": 4, "motivo": "motivo válido"},
        ).status_code
        == 403
    )
    assert client.get(f"/api/admin/candidatos/{c.id}").status_code == 200


def test_detalle_con_historial_ordenado(client, login, vacantes, db):
    login("analista")
    c = _cand(db, vacantes["activa"], nota=4, drive_file_id="d1")
    client.post(
        f"/api/admin/candidatos/{c.id}/estado",
        json={"estado": "entrevista", "observacion": "Cita lunes"},
    )
    r = client.get(f"/api/admin/candidatos/{c.id}").json()
    assert r["resumen_ia"] == "Resumen IA" and r["matriz"] == {"formacion": "Ing."}
    assert [e["evento"] for e in r["historial"]] == [
        "postulacion_recibida",
        "hv_guardada",
        "calificacion_ia",
        "cambio_estado",
    ]
    assert r["historial"][0]["detalle"] == "Canal web. Autorización v1.0"
    assert r["historial"][-1]["usuario"] == "Ana Analista"
    assert client.get(f"/api/admin/candidatos/{uuid.uuid4()}").status_code == 404


def test_candidato_anonimizado_no_expone_datos_ni_se_modifica(client, login, vacantes, db):
    login("lider")
    c = _cand(
        db,
        vacantes["activa"],
        nota=4,
        drive_url="https://drive/x",
        archivo_nombre="a.pdf",
        anonimizado_en=T0,
    )
    r = client.get(f"/api/admin/candidatos/{c.id}").json()
    assert r["resumen_ia"] is None and r["matriz"] is None
    assert r["drive_url"] is None and r["archivo_nombre"] is None
    assert (
        client.post(f"/api/admin/candidatos/{c.id}/estado", json={"estado": "reserva"}).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/admin/candidatos/{c.id}/calificacion",
            json={"nota": 2, "motivo": "motivo válido"},
        ).status_code
        == 409
    )


def test_resumen_de_la_vacante(client, login, vacantes, db):
    login("gerencia")
    v = vacantes["activa"]
    _cand(db, v, nota=5)
    _cand(db, v, nota=4)
    _cand(db, v, nota=3, estado="reserva")
    _cand(db, v, nota=1, estado="por_validar")
    _cand(db, v, nota=4, estado="entrevista")
    r = client.get(f"/api/admin/vacantes/{v.id}/resumen").json()
    assert r == {"recibidas": 5, "nota_4_5": 3, "reserva": 1, "por_validar": 1, "entrevista": 1}
