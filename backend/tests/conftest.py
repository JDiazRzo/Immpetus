import os

os.environ.update(
    SESSION_SECRET="x" * 40,
    COOKIE_SECURE="false",
    GOOGLE_OAUTH_CLIENT_ID="cliente-prueba",
    ALLOWED_EMAIL_DOMAIN="immpetus.co",
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import (
    get_borrar_hv,
    get_enviar_reporte,
    get_guardar_hv,
    get_mover_hv,
    get_verificador_google,
)
from app.db import get_db
from app.main import app
from app.models.postulaciones import DriveFile
from app.orm import Base, Habilidad, Usuario, Vacante, VacanteHabilidad


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as s:
        yield s


@pytest.fixture
def vacantes(db: Session):
    activa = Vacante(
        codigo="GSC-1",
        slug="gestor-soporte",
        cargo="Gestor de Soporte",
        ciudad="Bogotá",
        modalidad="remoto",
        activa=True,
        responsabilidades=["a"],
    )
    remota2 = Vacante(
        codigo="AAF-1",
        slug="asistente",
        cargo="Asistente Administrativo",
        ciudad="Bogotá",
        modalidad="presencial",
        activa=True,
        responsabilidades=[],
    )
    inactiva = Vacante(
        codigo="OLD-1",
        slug="vieja",
        cargo="Vieja",
        ciudad="Cali",
        modalidad="hibrido",
        activa=False,
        responsabilidades=[],
    )
    db.add_all([activa, remota2, inactiva])
    db.flush()
    zen = Habilidad(nombre="Zendesk", categoria="herramienta")
    db.add(zen)
    db.flush()
    db.add(VacanteHabilidad(vacante_id=activa.id, habilidad_id=zen.id, obligatoria=True, peso=4))
    db.commit()
    return {"activa": activa, "otra": remota2, "inactiva": inactiva}


@pytest.fixture
def subidas():
    return []


@pytest.fixture
def client(db, subidas):
    def fake_drive(pdf: bytes, vacante, nombre: str) -> DriveFile:
        subidas.append(nombre)
        return DriveFile(id="fake-id", url="https://drive.invalid/fake")

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_guardar_hv] = lambda: fake_drive

    def fake_google(token: str) -> dict:
        if token not in TOKENS:
            raise ValueError("token inválido")
        return TOKENS[token]

    app.dependency_overrides[get_verificador_google] = lambda: fake_google
    yield TestClient(app)
    app.dependency_overrides.clear()


TOKENS = {
    "tok-analista": {"email": "ana@immpetus.co", "hd": "immpetus.co", "email_verified": True},
    "tok-lider": {"email": "lider@immpetus.co", "hd": "immpetus.co", "email_verified": True},
    "tok-gerencia": {"email": "gerencia@immpetus.co", "hd": "immpetus.co", "email_verified": True},
    "tok-inactivo": {"email": "baja@immpetus.co", "hd": "immpetus.co", "email_verified": True},
    "tok-sinregistro": {"email": "nadie@immpetus.co", "hd": "immpetus.co", "email_verified": True},
    "tok-gmail": {"email": "x@gmail.com", "email_verified": True},
    "tok-noverificado": {"email": "ana@immpetus.co", "hd": "immpetus.co", "email_verified": False},
}


@pytest.fixture
def usuarios(db: Session):
    u = {
        "analista": Usuario(correo="ana@immpetus.co", nombre="Ana Analista", rol="analista"),
        "lider": Usuario(correo="lider@immpetus.co", nombre="Luis Líder", rol="lider"),
        "gerencia": Usuario(correo="gerencia@immpetus.co", nombre="Gina Gerencia", rol="gerencia"),
        "inactivo": Usuario(correo="baja@immpetus.co", nombre="Baja", rol="analista", activo=False),
    }
    db.add_all(u.values())
    db.commit()
    return u


@pytest.fixture
def login(client, usuarios):
    """login('analista') inicia sesión y deja la cookie en el cliente."""

    def _login(rol: str):
        r = client.post("/api/auth/google", json={"id_token": f"tok-{rol}"})
        assert r.status_code == 200, r.text
        return r.json()

    return _login


@pytest.fixture
def integraciones():
    """Registro de lo que el backend le pide a Drive/Gmail (nunca se llama a Google)."""
    return {
        "movidos": [],
        "borrados": [],
        "correos": [],
        "falla_drive": False,
        "falla_correo": False,
    }


@pytest.fixture(autouse=True)
def _dobles_integraciones(client, integraciones):
    def mover(drive_file_id, vacante):
        if integraciones["falla_drive"]:
            raise RuntimeError("drive caído")
        integraciones["movidos"].append((drive_file_id, vacante.codigo))
        return DriveFile(id=drive_file_id, url=f"https://drive.invalid/{drive_file_id}")

    def borrar(drive_file_id):
        if integraciones["falla_drive"]:
            raise RuntimeError("drive caído")
        integraciones["borrados"].append(drive_file_id)

    def enviar(destinatarios, html):
        if integraciones["falla_correo"]:
            raise RuntimeError("gmail caído")
        integraciones["correos"].append((destinatarios, html))

    app.dependency_overrides[get_mover_hv] = lambda: mover
    app.dependency_overrides[get_borrar_hv] = lambda: borrar
    app.dependency_overrides[get_enviar_reporte] = lambda: enviar
