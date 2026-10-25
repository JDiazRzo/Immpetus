from app.orm import Habilidad


def _habilidad(db, nombre="Excel"):
    h = Habilidad(nombre=nombre, categoria="herramienta")
    db.add(h)
    db.commit()
    return h


def _cuerpo(**extra):
    return {
        "cargo": "Gestor de Soporte y Servicio",
        "ciudad": "Bogotá",
        "modalidad": "remoto",
        "responsabilidades": ["Atender tickets", "  "],
        **extra,
    }


def test_crear_genera_slug_codigo_y_criterios(client, login, db):
    login("analista")
    h = _habilidad(db)
    r = client.post(
        "/api/admin/vacantes",
        json=_cuerpo(criterios=[{"habilidad_id": str(h.id), "obligatoria": True, "peso": 4}]),
    )
    assert r.status_code == 201
    v = r.json()
    assert v["slug"] == "gestor-de-soporte-y-servicio" and v["codigo"].startswith("GSS-")
    assert v["activa"] is False and v["publicada_en"] is None
    assert v["responsabilidades"] == ["Atender tickets"]
    assert v["criterios"] == [
        {"habilidad_id": str(h.id), "habilidad": "Excel", "obligatoria": True, "peso": 4}
    ]
    # mismo cargo: slug y código no chocan
    v2 = client.post("/api/admin/vacantes", json=_cuerpo()).json()
    assert v2["slug"].endswith("-2") and v2["codigo"].endswith("-2")


def test_interruptor_publica_la_vacante_en_la_web(client, login):
    login("analista")
    v = client.post("/api/admin/vacantes", json=_cuerpo()).json()
    assert client.get(f"/api/vacantes/{v['slug']}").status_code == 404
    r = client.patch(f"/api/admin/vacantes/{v['id']}", json={"activa": True})
    assert r.status_code == 200 and r.json()["activa"] is True and r.json()["publicada_en"]
    assert client.get(f"/api/vacantes/{v['slug']}").status_code == 200
    r = client.patch(f"/api/admin/vacantes/{v['id']}", json={"activa": False})
    assert r.json()["publicada_en"] is not None  # conserva la fecha original
    assert client.get(f"/api/vacantes/{v['slug']}").status_code == 404


def test_patch_parcial_no_cambia_slug_y_reemplaza_criterios(client, login, db):
    login("lider")
    h1, h2 = _habilidad(db, "A"), _habilidad(db, "B")
    v = client.post(
        "/api/admin/vacantes", json=_cuerpo(criterios=[{"habilidad_id": str(h1.id)}])
    ).json()
    r = client.patch(
        f"/api/admin/vacantes/{v['id']}",
        json={
            "cargo": "Otro cargo distinto",
            "criterios": [{"habilidad_id": str(h2.id), "peso": 2}],
        },
    ).json()
    assert r["slug"] == v["slug"] and r["cargo"] == "Otro cargo distinto"
    assert [c["habilidad"] for c in r["criterios"]] == ["B"]


def test_validaciones(client, login, db):
    login("analista")
    h = _habilidad(db)
    r = client.post(
        "/api/admin/vacantes",
        json=_cuerpo(criterios=[{"habilidad_id": "00000000-0000-4000-8000-000000000000"}]),
    )
    assert r.status_code == 400 and r.json()["error"]["field"] == "criterios"
    r = client.post(
        "/api/admin/vacantes",
        json=_cuerpo(criterios=[{"habilidad_id": str(h.id)}, {"habilidad_id": str(h.id)}]),
    )
    assert r.status_code == 400
    assert client.post("/api/admin/vacantes", json=_cuerpo(modalidad="otra")).status_code == 400
    v = client.post("/api/admin/vacantes", json=_cuerpo()).json()
    r = client.patch(f"/api/admin/vacantes/{v['id']}", json={"cargo": None})
    assert r.status_code == 400 and r.json()["error"]["field"] == "cargo"
    assert (
        client.patch(
            "/api/admin/vacantes/00000000-0000-4000-8000-000000000000", json={}
        ).status_code
        == 404
    )


def test_gerencia_consulta_pero_no_modifica(client, login, vacantes):
    login("gerencia")
    assert client.get("/api/admin/vacantes").json()["total"] == 3  # activas e inactivas
    r = client.post("/api/admin/vacantes", json=_cuerpo())
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN"


def test_habilidades_con_busqueda(client, login, db):
    login("analista")
    _habilidad(db, "Excel avanzado")
    _habilidad(db, "Zendesk")
    assert [h["nombre"] for h in client.get("/api/admin/habilidades?q=excel").json()] == [
        "Excel avanzado"
    ]
    assert len(client.get("/api/admin/habilidades").json()) == 2
