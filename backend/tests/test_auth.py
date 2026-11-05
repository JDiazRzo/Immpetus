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


# ---------- REQUIRE_HD ----------
SIN_HD = {"email": "ana@immpetus.co", "email_verified": True}  # cuenta de Google sin Workspace
HD_AJENO = {"email": "ana@immpetus.co", "hd": "otra.com", "email_verified": True}


def _con_tokens(**tokens):
    from tests.conftest import TOKENS

    TOKENS.update(tokens)
    return TOKENS


def test_require_hd_activo_por_defecto_exige_el_claim_hd(client, usuarios):
    from app.config import get_settings

    assert get_settings().require_hd is True
    tokens = _con_tokens(**{"tok-sin-hd": SIN_HD})
    try:
        r = client.post(LOGIN, json={"id_token": "tok-sin-hd"})
        assert r.status_code == 403 and "@immpetus.co" in r.json()["error"]["message"]
        assert client.post(LOGIN, json={"id_token": "tok-analista"}).status_code == 200  # con hd
    finally:
        tokens.pop("tok-sin-hd", None)


def test_sin_require_hd_se_acepta_una_cuenta_del_dominio_sin_hd(client, usuarios, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "require_hd", False)
    tokens = _con_tokens(**{"tok-sin-hd": SIN_HD})
    try:
        r = client.post(LOGIN, json={"id_token": "tok-sin-hd"})
        assert r.status_code == 200 and r.json()["correo"] == "ana@immpetus.co"
    finally:
        tokens.pop("tok-sin-hd", None)


def test_sin_require_hd_un_hd_de_otro_dominio_sigue_rechazado(client, usuarios, monkeypatch):
    from app.config import get_settings

    tokens = _con_tokens(**{"tok-hd-ajeno": HD_AJENO})
    try:
        for valor in (True, False):
            monkeypatch.setattr(get_settings(), "require_hd", valor)
            assert client.post(LOGIN, json={"id_token": "tok-hd-ajeno"}).status_code == 403
    finally:
        tokens.pop("tok-hd-ajeno", None)


def test_el_correo_del_dominio_es_obligatorio_con_o_sin_require_hd(client, usuarios, monkeypatch):
    from app.config import get_settings

    for valor in (True, False):
        monkeypatch.setattr(get_settings(), "require_hd", valor)
        assert client.post(LOGIN, json={"id_token": "tok-gmail"}).status_code == 403


def test_sin_require_hd_la_cuenta_debe_seguir_registrada_y_activa(client, usuarios, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "require_hd", False)
    tokens = _con_tokens(
        **{
            "tok-sin-hd": SIN_HD,
            "tok-sin-hd-baja": {**SIN_HD, "email": "baja@immpetus.co"},
            "tok-sin-hd-nadie": {**SIN_HD, "email": "nadie@immpetus.co"},
        }
    )
    try:
        assert (
            client.post(LOGIN, json={"id_token": "tok-sin-hd-nadie"}).status_code == 403
        )  # no registrada
        assert (
            client.post(LOGIN, json={"id_token": "tok-sin-hd-baja"}).status_code == 403
        )  # inactiva
    finally:
        for t in ("tok-sin-hd", "tok-sin-hd-baja", "tok-sin-hd-nadie"):
            tokens.pop(t, None)


def test_sin_require_hd_el_correo_no_verificado_sigue_dando_401(client, usuarios, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "require_hd", False)
    assert client.post(LOGIN, json={"id_token": "tok-noverificado"}).status_code == 401
