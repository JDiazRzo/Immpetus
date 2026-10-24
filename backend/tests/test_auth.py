from app.services import sesion

LOGIN = "/api/auth/google"


def test_login_ok_crea_cookie_httponly_y_devuelve_usuario(client, usuarios):
    r = client.post(LOGIN, json={"id_token": "tok-analista"})
    assert r.status_code == 200
    assert r.json() == {
        "id": str(usuarios["analista"].id),
        "correo": "ana@immpetus.co",
        "nombre": "Ana Analista",
        "rol": "analista",
    }
    cookie = r.headers["set-cookie"].lower()
    assert "immpetus_sesion=" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    assert "max-age=28800" in cookie
    assert client.get("/api/admin/me").json()["correo"] == "ana@immpetus.co"


def test_token_invalido_da_401(client, usuarios):
    r = client.post(LOGIN, json={"id_token": "token-falso-123"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_correo_no_verificado_da_401(client, usuarios):
    assert client.post(LOGIN, json={"id_token": "tok-noverificado"}).status_code == 401


def test_dominio_distinto_da_403(client, usuarios):
    r = client.post(LOGIN, json={"id_token": "tok-gmail"})
    assert r.status_code == 403
    assert r.json()["error"]["message"] == "Solo pueden entrar cuentas @immpetus.co."


def test_correo_no_registrado_o_inactivo_da_403(client, usuarios):
    for tok in ("tok-sinregistro", "tok-inactivo"):
        r = client.post(LOGIN, json={"id_token": tok})
        assert r.status_code == 403 and "no está registrada" in r.json()["error"]["message"]


def test_admin_sin_cookie_da_401(client):
    for ruta in ("/api/admin/me", "/api/admin/vacantes", "/api/admin/habilidades"):
        r = client.get(ruta)
        assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_cookie_alterada_o_vencida_da_401(client, usuarios, monkeypatch):
    client.cookies.set(sesion.COOKIE, "basura.firmada.mal")
    assert client.get("/api/admin/me").status_code == 401
    client.cookies.set(sesion.COOKIE, sesion.crear_token(usuarios["analista"].id))
    assert client.get("/api/admin/me").status_code == 200
    monkeypatch.setattr(sesion, "MAX_AGE_SEGUNDOS", -1)
    assert client.get("/api/admin/me").status_code == 401


def test_usuario_desactivado_despues_de_entrar_da_403(client, login, usuarios, db):
    login("analista")
    usuarios["analista"].activo = False
    db.commit()
    r = client.get("/api/admin/me")
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN"


def test_logout_borra_la_cookie_y_siempre_da_204(client, login):
    assert client.post("/api/auth/logout").status_code == 204  # sin sesión también
    login("analista")
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/admin/me").status_code == 401


def test_secreto_corto_falla_claro(monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "session_secret", "corto")
    import uuid

    import pytest

    with pytest.raises(RuntimeError):
        sesion.crear_token(uuid.uuid4())
