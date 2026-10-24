def test_lista_solo_activas(client, vacantes):
    r = client.get("/api/vacantes")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2 and {v["slug"] for v in body["items"]} == {
        "gestor-soporte",
        "asistente",
    }
    assert body["page"] == 1 and body["page_size"] == 20


def test_filtra_por_modalidad_y_texto(client, vacantes):
    assert client.get("/api/vacantes?modalidad=remoto").json()["total"] == 1
    assert client.get("/api/vacantes?q=asistente").json()["total"] == 1
    assert client.get("/api/vacantes?modalidad=otra").status_code == 400


def test_detalle_no_expone_ids_ni_pesos(client, vacantes):
    r = client.get("/api/vacantes/gestor-soporte")
    assert r.status_code == 200
    assert r.json()["criterios"] == [{"habilidad": "Zendesk", "obligatoria": True}]


def test_vacante_inactiva_o_inexistente_da_404(client, vacantes):
    for slug in ("vieja", "no-existe"):
        r = client.get(f"/api/vacantes/{slug}")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "NOT_FOUND"
