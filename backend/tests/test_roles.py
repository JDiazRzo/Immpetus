"""Tabla 2.0 del contrato: cada endpoint de /api/admin/* contra cada rol."""

import uuid

import pytest

from app.orm import Usuario

OTRO = str(uuid.uuid4())
MENSAJE = "No tiene permiso para esta acción."
TODOS = {"analista", "lider", "gerencia"}
ESCRIBEN = {"analista", "lider"}
SOLO_LIDER = {"lider"}

# (método, ruta, cuerpo, roles permitidos)
ENDPOINTS = [
    # ---- ver: los tres roles ----
    ("GET", "/api/admin/me", None, TODOS),
    ("GET", "/api/admin/vacantes", None, TODOS),
    ("GET", f"/api/admin/vacantes/{OTRO}", None, TODOS),
    ("GET", f"/api/admin/vacantes/{OTRO}/resumen", None, TODOS),
    ("GET", f"/api/admin/vacantes/{OTRO}/candidatos", None, TODOS),
    ("GET", "/api/admin/candidatos", None, TODOS),
    ("GET", f"/api/admin/candidatos/{OTRO}", None, TODOS),
    ("GET", "/api/admin/habilidades", None, TODOS),
    ("GET", "/api/admin/reserva", None, TODOS),
    ("GET", "/api/admin/correos-sin-asignar", None, TODOS),
    ("GET", "/api/admin/contactos", None, TODOS),
    # ---- gestionar vacantes, decidir sobre candidatos, reporte: analista y líder ----
    ("POST", "/api/admin/vacantes", {}, ESCRIBEN),
    ("PATCH", f"/api/admin/vacantes/{OTRO}", {}, ESCRIBEN),
    ("POST", f"/api/admin/candidatos/{OTRO}/estado", {"estado": "reserva"}, ESCRIBEN),
    (
        "POST",
        f"/api/admin/candidatos/{OTRO}/calificacion",
        {"nota": 3, "motivo": "motivo ok"},
        ESCRIBEN,
    ),
    ("POST", f"/api/admin/reserva/{OTRO}/asociar", {"vacante_id": OTRO}, ESCRIBEN),
    ("POST", f"/api/admin/correos-sin-asignar/{OTRO}/asignar", {"vacante_id": OTRO}, ESCRIBEN),
    ("POST", f"/api/admin/vacantes/{OTRO}/reporte", {"destinatarios": ["g@immpetus.co"]}, ESCRIBEN),
    ("PATCH", f"/api/admin/contactos/{OTRO}", {"atendido": True}, ESCRIBEN),
    # ---- solo líder ----
    ("POST", f"/api/admin/vacantes/{OTRO}/cerrar", {"motivo": "Cargo cubierto"}, SOLO_LIDER),
    ("POST", f"/api/admin/candidatos/{OTRO}/anonimizar", None, SOLO_LIDER),
    ("GET", "/api/admin/usuarios", None, SOLO_LIDER),
    (
        "POST",
        "/api/admin/usuarios",
        {"correo": "x@immpetus.co", "nombre": "X", "rol": "analista"},
        SOLO_LIDER,
    ),
    ("PATCH", f"/api/admin/usuarios/{OTRO}", {"activo": False}, SOLO_LIDER),
]
IDS = [f"{m} {r.replace(OTRO, '{id}')}" for m, r, _, _ in ENDPOINTS]


def _llamar(client, metodo, ruta, cuerpo):
    return (
        client.request(metodo, ruta, json=cuerpo)
        if cuerpo is not None
        else client.request(metodo, ruta)
    )


@pytest.mark.parametrize("metodo,ruta,cuerpo,permitidos", ENDPOINTS, ids=IDS)
def test_cada_rol_solo_hace_lo_que_le_toca(client, login, metodo, ruta, cuerpo, permitidos):
    for rol in ("analista", "lider", "gerencia"):
        login(rol)
        r = _llamar(client, metodo, ruta, cuerpo)
        if rol in permitidos:
            assert r.status_code not in (401, 403), (rol, r.status_code, r.text)
        else:
            assert r.status_code == 403, (rol, r.status_code, r.text)
            assert r.json() == {"error": {"code": "FORBIDDEN", "message": MENSAJE, "field": None}}


@pytest.mark.parametrize("metodo,ruta,cuerpo,permitidos", ENDPOINTS, ids=IDS)
def test_sin_sesion_todo_da_401(client, metodo, ruta, cuerpo, permitidos):
    r = _llamar(client, metodo, ruta, cuerpo)
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_me_devuelve_el_rol_de_cada_usuario(client, login):
    for rol in ("analista", "lider", "gerencia"):
        login(rol)
        assert client.get("/api/admin/me").json()["rol"] == rol


def test_el_rol_se_lee_de_la_base_en_cada_peticion(client, login, db, usuarios):
    """Un cambio de rol aplica de inmediato, sin volver a iniciar sesión."""
    login("analista")
    cuerpo = {"cargo": "Cargo de prueba", "ciudad": "Bogotá", "modalidad": "remoto"}
    assert client.post("/api/admin/vacantes", json=cuerpo).status_code == 201
    usuarios["analista"].rol = "gerencia"
    db.commit()
    r = client.post("/api/admin/vacantes", json=cuerpo)  # misma cookie
    assert r.status_code == 403 and r.json()["error"]["message"] == MENSAJE
    assert client.get("/api/admin/me").json()["rol"] == "gerencia"
    usuarios["analista"].rol = "lider"
    db.commit()
    assert client.get("/api/admin/usuarios").status_code == 200


def test_un_usuario_desactivado_pierde_todo_acceso_de_inmediato(client, login, db, usuarios):
    login("lider")
    db.add(
        Usuario(correo="otro@immpetus.co", nombre="Otro", rol="lider")
    )  # antes: no puede quedar sin líder
    db.commit()
    usuarios["lider"].activo = False
    db.commit()
    assert client.get("/api/admin/usuarios").status_code == 403
    assert client.get("/api/admin/vacantes").status_code == 403


def test_reporte_con_gmail_configurado_pero_sin_entregar_da_502_claro(
    client, login, vacantes, monkeypatch
):
    """GMAIL_DELEGATED_USER viene prellenado en .env.example: sin gmail.py no debe dar un 500."""
    import sys

    from app.api.deps import get_enviar_reporte
    from app.config import get_settings
    from app.main import app

    app.dependency_overrides.pop(get_enviar_reporte, None)  # usar la dependencia real
    monkeypatch.setattr(get_settings(), "gmail_delegated_user", "seleccion@immpetus.co")
    monkeypatch.setitem(sys.modules, "app.integraciones.gmail", None)  # el módulo "no existe"
    monkeypatch.delattr("app.integraciones.gmail", raising=False)
    login("analista")
    r = client.post(
        f"/api/admin/vacantes/{vacantes['activa'].id}/reporte",
        json={"destinatarios": ["g@immpetus.co"]},
    )
    assert r.status_code == 502 and r.json()["error"]["code"] == "EMAIL_ERROR"
