import pytest
from sqlalchemy import select
from starlette.requests import Request

from app.config import get_settings
from app.limiter import ip_cliente, limiter
from app.orm import Candidato, Contacto

PDF = b"%PDF-1.4 hoja de vida inventada"
CONTACTO = {
    "nombre": "Carolina Pérez",
    "correo": "c@acme.com",
    "mensaje": "Necesitamos apoyo para seleccionar cargos.",
    "autorizacion_datos": True,
}


@pytest.fixture
def con_limites():
    """Activa el límite de peticiones (en los demás tests está apagado)."""
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.enabled = False
    limiter.reset()


def _postular(client, vacante, n, ip=None):
    datos = {
        "vacante_id": str(vacante.id),
        "nombre": "Ana Prueba",
        "correo": f"ana{n}@ejemplo.com",
        "celular": "3001234567",
        "autorizacion_datos": "true",
    }
    cabeceras = {"x-forwarded-for": ip} if ip else {}
    return client.post(
        "/api/postulaciones",
        data=datos,
        files={"archivo": ("hv.pdf", PDF, "application/pdf")},
        headers=cabeceras,
    )


# ---------- límite de peticiones ----------
def test_postulaciones_5_por_hora_y_la_6_da_429(client, vacantes, con_limites):
    for n in range(5):
        assert _postular(client, vacantes["activa"], n).status_code == 201
    r = _postular(client, vacantes["activa"], 5)
    assert r.status_code == 429
    assert r.json() == {
        "error": {
            "code": "RATE_LIMITED",
            "message": "Demasiados intentos. Intenta de nuevo más tarde.",
            "field": None,
        }
    }


def test_contacto_3_por_hora_y_la_4_da_429(client, db, con_limites):
    for _ in range(3):
        assert client.post("/api/contacto", json=CONTACTO).status_code == 201
    r = client.post("/api/contacto", json=CONTACTO)
    assert r.status_code == 429 and r.json()["error"]["code"] == "RATE_LIMITED"
    assert db.query(Contacto).count() == 3  # el rechazado no se guardó


def test_login_10_por_minuto_y_el_11_da_429(client, usuarios, con_limites):
    for _ in range(10):
        assert client.post("/api/auth/google", json={"id_token": "token-falso"}).status_code == 401
    r = client.post("/api/auth/google", json={"id_token": "tok-analista"})
    assert r.status_code == 429  # ni siquiera un token bueno pasa mientras dure el bloqueo


def test_los_limites_son_independientes_por_endpoint(client, vacantes, con_limites):
    for n in range(5):
        _postular(client, vacantes["activa"], n)
    assert _postular(client, vacantes["activa"], 99).status_code == 429
    assert client.post("/api/contacto", json=CONTACTO).status_code == 201  # contacto sigue libre


def test_endpoints_sin_limite_no_se_afectan(client, vacantes, con_limites):
    for _ in range(30):
        assert client.get("/api/vacantes").status_code == 200
        assert client.get("/health").status_code == 200


def test_cada_ip_tiene_su_propio_cupo_con_proxy_de_confianza(
    client, vacantes, con_limites, monkeypatch
):
    monkeypatch.setattr(get_settings(), "trusted_proxy_hops", 1)
    for n in range(5):
        assert _postular(client, vacantes["activa"], n, ip="1.1.1.1").status_code == 201
    assert _postular(client, vacantes["activa"], 5, ip="1.1.1.1").status_code == 429
    assert _postular(client, vacantes["activa"], 6, ip="2.2.2.2").status_code == 201


def test_falsificar_x_forwarded_for_no_evita_el_limite(client, vacantes, con_limites, monkeypatch):
    monkeypatch.setattr(get_settings(), "trusted_proxy_hops", 1)
    for n in range(5):  # el atacante cambia la primera entrada; la última la puso NUESTRO proxy
        ip = f"9.9.9.{n}, 1.1.1.1"
        assert _postular(client, vacantes["activa"], n, ip=ip).status_code == 201
    assert _postular(client, vacantes["activa"], 5, ip="7.7.7.7, 1.1.1.1").status_code == 429


def _req(xff=None, host="10.0.0.1"):
    cabeceras = [(b"x-forwarded-for", xff.encode())] if xff else []
    return Request({"type": "http", "headers": cabeceras, "client": (host, 1234)})


def test_ip_cliente(monkeypatch):
    cfg = get_settings()
    monkeypatch.setattr(cfg, "trusted_proxy_hops", 0)
    assert ip_cliente(_req("1.1.1.1")) == "10.0.0.1"  # sin proxy de confianza, XFF se ignora
    monkeypatch.setattr(cfg, "trusted_proxy_hops", 1)
    assert ip_cliente(_req("8.8.8.8, 1.1.1.1")) == "1.1.1.1"
    monkeypatch.setattr(cfg, "trusted_proxy_hops", 2)
    assert ip_cliente(_req("1.1.1.1, 3.3.3.3")) == "1.1.1.1"
    assert (
        ip_cliente(_req("3.3.3.3")) == "10.0.0.1"
    )  # cadena más corta de lo esperado: no se confía
    assert ip_cliente(_req(None)) == "10.0.0.1"


# ---------- 413 por tamaño, antes de leer el cuerpo ----------
MB = 1024 * 1024


def test_413_si_content_length_supera_6_mb(client, vacantes, db, subidas):
    grande = b"%PDF-" + b"0" * (7 * MB)
    r = client.post(
        "/api/postulaciones",
        data={
            "vacante_id": str(vacantes["activa"].id),
            "nombre": "Ana Prueba",
            "correo": "ana@ejemplo.com",
            "celular": "3001234567",
            "autorizacion_datos": "true",
        },
        files={"archivo": ("hv.pdf", grande, "application/pdf")},
    )
    assert r.status_code == 413
    assert r.json() == {
        "error": {
            "code": "FILE_TOO_LARGE",
            "message": "El PDF no debe superar 5 MB.",
            "field": "archivo",
        }
    }
    assert db.scalar(select(Candidato)) is None and subidas == []


def test_413_cuando_no_hay_content_length(client, vacantes, db, subidas):
    """Subida en trozos (chunked) sin Content-Length: se corta al pasar el límite."""
    borde = "frontera"
    vacante_id = vacantes["activa"].id
    cabeza = (
        f'--{borde}\r\nContent-Disposition: form-data; name="vacante_id"\r\n\r\n{vacante_id}\r\n'
        f'--{borde}\r\nContent-Disposition: form-data; name="archivo"; filename="hv.pdf"\r\n'
        "Content-Type: application/pdf\r\n\r\n"
    ).encode()
    cola = f"\r\n--{borde}--\r\n".encode()

    def trozos():
        yield cabeza
        for _ in range(7 * 16):  # 7 MB en trozos de 64 KB
            yield b"0" * 65536
        yield cola

    r = client.post(
        "/api/postulaciones",
        content=trozos(),
        headers={"content-type": f"multipart/form-data; boundary={borde}"},
    )
    assert r.status_code == 413 and r.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert db.scalar(select(Candidato)) is None and subidas == []


def test_pdf_dentro_del_limite_sigue_pasando(client, vacantes, db):
    cuatro_mb = b"%PDF-" + b"0" * (4 * MB)
    r = client.post(
        "/api/postulaciones",
        data={
            "vacante_id": str(vacantes["activa"].id),
            "nombre": "Ana Prueba",
            "correo": "ana@ejemplo.com",
            "celular": "3001234567",
            "autorizacion_datos": "true",
        },
        files={"archivo": ("hv.pdf", cuatro_mb, "application/pdf")},
    )
    assert r.status_code == 201


def test_entre_5_y_6_mb_lo_rechaza_el_endpoint_con_el_mismo_413(client, vacantes):
    medio = b"%PDF-" + b"0" * (5 * MB + 1000)  # pasa el middleware (≤ 6 MB) pero excede MAX_PDF_MB
    r = client.post(
        "/api/postulaciones",
        data={
            "vacante_id": str(vacantes["activa"].id),
            "nombre": "Ana Prueba",
            "correo": "ana@ejemplo.com",
            "celular": "3001234567",
            "autorizacion_datos": "true",
        },
        files={"archivo": ("hv.pdf", medio, "application/pdf")},
    )
    assert r.status_code == 413 and r.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_json_enorme_en_contacto_y_login_da_413(client):
    enorme = {**CONTACTO, "mensaje": "x" * (70 * 1024)}
    r = client.post("/api/contacto", json=enorme)
    assert r.status_code == 413 and r.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    r = client.post("/api/auth/google", json={"id_token": "x" * (70 * 1024)})
    assert r.status_code == 413


def test_el_limite_de_tamano_solo_aplica_a_post_de_esas_rutas(client):
    assert client.get("/api/vacantes", headers={"content-length": "0"}).status_code == 200
