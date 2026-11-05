import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.orm import Usuario
from app.services import usuarios as svc
from tests.conftest import TOKENS

SIN_LIDER = "Debe quedar al menos un líder activo. Asigne otro líder antes."
YA_EXISTE = "Este correo ya tiene acceso. Si está desactivado, actívelo."


def _crear(client, **cambios):
    cuerpo = {"correo": "juan@immpetus.co", "nombre": "Juan Pérez", "rol": "analista", **cambios}
    return client.post(
        "/api/admin/usuarios", json={k: v for k, v in cuerpo.items() if v is not ...}
    )


# ---------- GET ----------
def test_lista_usuarios_con_sus_campos(client, login, usuarios):
    login("lider")
    r = client.get("/api/admin/usuarios")
    assert r.status_code == 200
    filas = r.json()
    assert isinstance(filas, list) and len(filas) == 4
    assert set(filas[0]) == {"id", "correo", "nombre", "rol", "activo", "creado_en"}
    assert [u["activo"] for u in filas] == [True, True, True, False]  # activos primero


# ---------- POST ----------
def test_crea_usuario_en_minusculas_y_activo(client, login, db):
    login("lider")
    r = _crear(client, correo="Juan.Perez@Immpetus.co")
    assert r.status_code == 201
    j = r.json()
    assert (
        j["correo"] == "juan.perez@immpetus.co" and j["rol"] == "analista" and j["activo"] is True
    )
    assert db.scalar(select(Usuario).where(Usuario.correo == "juan.perez@immpetus.co"))


def test_el_usuario_creado_puede_entrar(client, login, db):
    login("lider")
    _crear(client, correo="nuevo@immpetus.co")
    TOKENS["tok-nuevo"] = {
        "email": "nuevo@immpetus.co",
        "hd": "immpetus.co",
        "email_verified": True,
    }
    try:
        otro = TestClient(app)
        r = otro.post("/api/auth/google", json={"id_token": "tok-nuevo"})
        assert r.status_code == 200 and r.json()["rol"] == "analista"
    finally:
        TOKENS.pop("tok-nuevo", None)


def test_correo_de_otro_dominio_da_400(client, login):
    login("lider")
    r = _crear(client, correo="juan@gmail.com")
    assert r.status_code == 400 and r.json()["error"]["field"] == "correo"
    assert "@immpetus.co" in r.json()["error"]["message"]


def test_correo_repetido_da_409_sin_distinguir_mayusculas(client, login, usuarios):
    login("lider")
    r = _crear(client, correo="ANA@immpetus.co")  # ya existe ana@immpetus.co
    assert r.status_code == 409 and r.json()["error"] == {
        "code": "CONFLICT",
        "message": YA_EXISTE,
        "field": None,
    }
    r = _crear(client, correo="baja@immpetus.co")  # existe pero está desactivado: también 409
    assert r.status_code == 409 and r.json()["error"]["message"] == YA_EXISTE


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("correo", "no-es-correo"),
        ("correo", ...),
        ("nombre", "x"),
        ("nombre", ...),
        ("rol", "admin"),
        ("rol", ...),
        ("rol", ""),
    ],
)
def test_validaciones_al_crear(client, login, db, campo, valor):
    login("lider")
    r = _crear(client, **{campo: valor})
    assert r.status_code == 400 and r.json()["error"]["field"] == campo


def test_no_se_pueden_enviar_campos_extra_al_crear(client, login):
    login("lider")
    r = client.post(
        "/api/admin/usuarios",
        json={"correo": "a@immpetus.co", "nombre": "Ana", "rol": "analista", "activo": False},
    )
    assert r.status_code == 400 and r.json()["error"]["field"] == "activo"


# ---------- PATCH ----------
def test_cambia_el_rol_y_deja_trazabilidad(client, login, usuarios, db):
    me = login("lider")
    r = client.patch(f"/api/admin/usuarios/{usuarios['analista'].id}", json={"rol": "gerencia"})
    assert r.status_code == 200 and r.json()["rol"] == "gerencia"
    db.refresh(usuarios["analista"])
    u = usuarios["analista"]
    assert u.actualizado_en is not None and str(u.actualizado_por) == me["id"]


def test_desactiva_y_reactiva(client, login, usuarios):
    login("lider")
    url = f"/api/admin/usuarios/{usuarios['analista'].id}"
    assert client.patch(url, json={"activo": False}).json()["activo"] is False
    assert client.patch(url, json={"activo": True}).json()["activo"] is True


def test_un_usuario_reactivado_vuelve_a_poder_entrar(client, login, usuarios):
    login("lider")
    otro = TestClient(app)
    assert otro.post("/api/auth/google", json={"id_token": "tok-inactivo"}).status_code == 403
    client.patch(f"/api/admin/usuarios/{usuarios['inactivo'].id}", json={"activo": True})
    assert otro.post("/api/auth/google", json={"id_token": "tok-inactivo"}).status_code == 200


def test_cambio_sin_efecto_no_toca_la_trazabilidad(client, login, usuarios, db):
    login("lider")
    r = client.patch(f"/api/admin/usuarios/{usuarios['analista'].id}", json={"rol": "analista"})
    assert r.status_code == 200
    db.refresh(usuarios["analista"])
    assert usuarios["analista"].actualizado_en is None


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"rol": None},
        {"activo": None},
        {"rol": "admin"},
        {"activo": "quizas"},
        {"nombre": "Otro"},
        {"correo": "x@immpetus.co"},
    ],
)
def test_patch_solo_acepta_rol_o_activo(client, login, usuarios, cuerpo):
    login("lider")
    r = client.patch(f"/api/admin/usuarios/{usuarios['analista'].id}", json=cuerpo)
    assert r.status_code == 400 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_usuario_inexistente_da_404(client, login):
    login("lider")
    assert (
        client.patch(f"/api/admin/usuarios/{uuid.uuid4()}", json={"activo": False}).status_code
        == 404
    )


def test_no_existe_delete(client, login, usuarios, db):
    login("lider")
    r = client.delete(f"/api/admin/usuarios/{usuarios['analista'].id}")
    assert r.status_code == 405
    assert db.get(Usuario, usuarios["analista"].id) is not None


# ---------- el último líder activo ----------
def test_no_se_puede_desactivar_ni_degradar_al_ultimo_lider(client, login, usuarios, db):
    me = login("lider")
    url = f"/api/admin/usuarios/{me['id']}"
    for cuerpo in ({"activo": False}, {"rol": "analista"}, {"rol": "gerencia", "activo": False}):
        r = client.patch(url, json=cuerpo)
        assert r.status_code == 409, cuerpo
        assert r.json()["error"] == {"code": "CONFLICT", "message": SIN_LIDER, "field": None}
    db.refresh(usuarios["lider"])
    assert usuarios["lider"].rol == "lider" and usuarios["lider"].activo is True


def test_con_otro_lider_si_se_puede_pero_el_nuevo_ultimo_queda_protegido(client, login, usuarios):
    me = login("lider")
    segundo = client.post(
        "/api/admin/usuarios",
        json={"correo": "segundo@immpetus.co", "nombre": "Segundo", "rol": "lider"},
    ).json()
    assert (
        client.patch(f"/api/admin/usuarios/{me['id']}", json={"rol": "analista"}).status_code == 200
    )
    # Yo ya no soy líder: otro cliente entra como el segundo líder
    TOKENS["tok-segundo"] = {
        "email": "segundo@immpetus.co",
        "hd": "immpetus.co",
        "email_verified": True,
    }
    try:
        otro = TestClient(app)
        assert otro.post("/api/auth/google", json={"id_token": "tok-segundo"}).status_code == 200
        r = otro.patch(f"/api/admin/usuarios/{segundo['id']}", json={"activo": False})
        assert r.status_code == 409 and r.json()["error"]["message"] == SIN_LIDER
    finally:
        TOKENS.pop("tok-segundo", None)


def test_desactivar_a_un_no_lider_nunca_se_bloquea(client, login, usuarios):
    login("lider")
    assert (
        client.patch(
            f"/api/admin/usuarios/{usuarios['gerencia'].id}", json={"activo": False}
        ).status_code
        == 200
    )


def test_la_base_tambien_protege_al_ultimo_lider_y_el_backend_lo_traduce_a_409(
    client, login, usuarios, db, monkeypatch
):
    """Carrera: el chequeo de Python pasa, pero el trigger de la base (0007) lo frena."""
    if db.get_bind().dialect.name != "postgresql":
        pytest.skip("El trigger solo existe en Postgres (TEST_DATABASE_URL).")
    me = login("lider")
    monkeypatch.setattr(svc, "_otros_lideres_activos", lambda *_: 1)  # engaña al chequeo de Python
    r = client.patch(f"/api/admin/usuarios/{me['id']}", json={"activo": False})
    assert r.status_code == 409 and r.json()["error"]["message"] == SIN_LIDER
    db.expire_all()
    assert db.get(Usuario, usuarios["lider"].id).activo is True
