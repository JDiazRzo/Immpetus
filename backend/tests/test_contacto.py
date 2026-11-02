import uuid

import pytest
from sqlalchemy import select

from app.orm import Contacto

VALIDO = {
    "nombre": "Carolina Pérez",
    "empresa": "Acme S.A.S.",
    "correo": "Carolina@Acme.com",
    "telefono": "3001234567",
    "servicio": "talento_bpo",
    "mensaje": "Necesitamos apoyo para seleccionar 5 cargos comerciales.",
    "autorizacion_datos": True,
}


def _post(client, **cambios):
    datos = {**VALIDO, **cambios}
    datos = {k: v for k, v in datos.items() if v is not ...}  # `...` = quitar el campo
    return client.post("/api/contacto", json=datos)


# ---------- POST /api/contacto ----------
def test_crea_el_contacto_y_responde_201_con_id(client, db):
    r = _post(client)
    assert r.status_code == 201 and list(r.json()) == ["id"]
    c = db.scalar(select(Contacto))
    assert str(c.id) == r.json()["id"]
    assert c.correo == "carolina@acme.com"  # se normaliza
    assert c.atendido is False and c.autorizacion_datos is True and c.autorizacion_fecha


def test_solo_los_campos_obligatorios(client, db):
    r = _post(client, empresa=..., telefono=..., servicio=...)
    assert r.status_code == 201
    c = db.scalar(select(Contacto))
    assert (c.empresa, c.telefono, c.servicio) == (None, None, None)


def test_texto_vacio_en_opcionales_se_guarda_como_nulo(client, db):
    assert _post(client, empresa="  ", telefono="", servicio=None).status_code == 201
    c = db.scalar(select(Contacto))
    assert (c.empresa, c.telefono, c.servicio) == (None, None, None)


def test_recorta_espacios(client, db):
    _post(client, nombre="  Carolina Pérez  ")
    assert db.scalar(select(Contacto)).nombre == "Carolina Pérez"


@pytest.mark.parametrize(
    "servicio",
    [
        "adquisicion_talento",
        "talento_bpo",
        "gestion_estrategica",
        "formacion_liderazgo",
        "procesos",
        "otro",
    ],
)
def test_acepta_todos_los_servicios(client, servicio):
    assert _post(client, servicio=servicio).status_code == 201


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("nombre", "ab"),
        ("nombre", "   "),
        ("nombre", "x" * 121),
        ("empresa", "x" * 161),
        ("correo", "no-es-un-correo"),
        ("correo", ("a" * 250) + "@x.co"),
        ("telefono", "1" * 31),
        ("servicio", "marketing"),
        ("mensaje", "corto"),
        ("mensaje", "x" * 2001),
        ("mensaje", ...),
        ("nombre", ...),
        ("correo", ...),
        ("autorizacion_datos", ...),
    ],
)
def test_validaciones_dan_400_con_el_campo(client, db, campo, valor):
    r = _post(client, **{campo: valor})
    assert r.status_code == 400, (campo, valor)
    assert r.json()["error"]["code"] == "VALIDATION_ERROR" and r.json()["error"]["field"] == campo
    assert db.scalar(select(Contacto)) is None


def test_limites_exactos_se_aceptan(client):
    assert _post(client, nombre="abc", mensaje="x" * 10).status_code == 201
    assert (
        _post(
            client, nombre="n" * 120, empresa="e" * 160, telefono="1" * 30, mensaje="m" * 2000
        ).status_code
        == 201
    )


def test_sin_autorizacion_da_400_y_no_guarda(client, db):
    r = _post(client, autorizacion_datos=False)
    assert r.status_code == 400
    assert r.json()["error"]["field"] == "autorizacion_datos"
    assert "autorizar" in r.json()["error"]["message"]
    assert db.scalar(select(Contacto)) is None


def test_campos_extra_se_rechazan(client, db):
    for extra in ({"atendido": True}, {"id": str(uuid.uuid4())}, {"cualquiera": "x"}):
        r = _post(client, **extra)
        assert r.status_code == 400 and r.json()["error"]["field"] == next(iter(extra))
    assert db.scalar(select(Contacto)) is None


def test_cuerpo_que_no_es_json_da_400(client):
    r = client.post("/api/contacto", content=b"hola", headers={"content-type": "application/json"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_avisa_al_correo_comercial_con_los_datos(client, integraciones):
    _post(client)
    (aviso,) = integraciones["avisos"]
    assert aviso["nombre"] == "Carolina Pérez" and aviso["correo"] == "carolina@acme.com"
    assert aviso["servicio"] == "talento_bpo" and "5 cargos" in aviso["mensaje"]


def test_si_el_aviso_falla_el_contacto_igual_queda_guardado(client, db, integraciones):
    integraciones["falla_aviso"] = True
    assert _post(client).status_code == 201
    assert db.query(Contacto).count() == 1


def test_no_exige_sesion(client):
    assert _post(client).status_code == 201


# ---------- /api/admin/contactos ----------
def _crear(client, n):
    for i in range(n):
        assert _post(client, nombre=f"Persona {i:02d}", correo=f"p{i}@acme.com").status_code == 201


def test_admin_exige_sesion(client):
    assert client.get("/api/admin/contactos").status_code == 401
    assert (
        client.patch(f"/api/admin/contactos/{uuid.uuid4()}", json={"atendido": True}).status_code
        == 401
    )


def test_lista_los_mas_recientes_primero_y_pagina(client, login):
    _crear(client, 5)
    login("gerencia")
    r = client.get("/api/admin/contactos?page_size=2").json()
    assert r["total"] == 5 and len(r["items"]) == 2 and r["page_size"] == 2
    assert [c["nombre"] for c in r["items"]] == ["Persona 04", "Persona 03"]
    item = r["items"][0]
    assert set(item) == {
        "id",
        "nombre",
        "empresa",
        "correo",
        "telefono",
        "servicio",
        "mensaje",
        "atendido",
        "creado_en",
    }
    p3 = client.get("/api/admin/contactos?page=3&page_size=2").json()
    assert [c["nombre"] for c in p3["items"]] == ["Persona 00"]


def test_filtra_por_atendido(client, login):
    _crear(client, 3)
    login("analista")
    primero = client.get("/api/admin/contactos").json()["items"][0]["id"]
    assert (
        client.patch(f"/api/admin/contactos/{primero}", json={"atendido": True}).status_code == 200
    )
    pendientes = client.get("/api/admin/contactos?atendido=false").json()
    atendidos = client.get("/api/admin/contactos?atendido=true").json()
    assert pendientes["total"] == 2 and atendidos["total"] == 1
    assert atendidos["items"][0]["id"] == primero and atendidos["items"][0]["atendido"] is True
    assert client.get("/api/admin/contactos").json()["total"] == 3


def test_marcar_y_desmarcar_atendido(client, login):
    _crear(client, 1)
    login("lider")
    cid = client.get("/api/admin/contactos").json()["items"][0]["id"]
    assert (
        client.patch(f"/api/admin/contactos/{cid}", json={"atendido": True}).json()["atendido"]
        is True
    )
    assert (
        client.patch(f"/api/admin/contactos/{cid}", json={"atendido": False}).json()["atendido"]
        is False
    )


def test_patch_validaciones(client, login):
    _crear(client, 1)
    login("analista")
    cid = client.get("/api/admin/contactos").json()["items"][0]["id"]
    assert (
        client.patch(f"/api/admin/contactos/{uuid.uuid4()}", json={"atendido": True}).status_code
        == 404
    )
    assert client.patch(f"/api/admin/contactos/{cid}", json={}).status_code == 400
    r = client.patch(f"/api/admin/contactos/{cid}", json={"atendido": True, "mensaje": "otro"})
    assert r.status_code == 400  # solo se puede cambiar `atendido`
    assert client.get("/api/admin/contactos").json()["items"][0]["mensaje"] == VALIDO["mensaje"]


def test_gerencia_ve_pero_no_modifica(client, login):
    _crear(client, 1)
    login("gerencia")
    cid = client.get("/api/admin/contactos").json()["items"][0]["id"]
    r = client.patch(f"/api/admin/contactos/{cid}", json={"atendido": True})
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN"


def test_el_aviso_es_opcional_aunque_gmail_este_configurado_y_falte_la_funcion(monkeypatch):
    """Si Fabian aún no entrega gmail.enviar_aviso_contacto, el formulario no debe romperse."""
    from app.api import deps
    from app.config import get_settings
    from app.services import integraciones_dev

    monkeypatch.setattr(get_settings(), "gmail_delegated_user", "seleccion@immpetus.co")
    assert deps.get_enviar_aviso_contacto() is integraciones_dev.enviar_aviso_contacto
