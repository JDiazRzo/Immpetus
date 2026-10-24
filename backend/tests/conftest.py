import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_guardar_hv
from app.db import get_db
from app.main import app
from app.models.postulaciones import DriveFile
from app.orm import Base, Habilidad, Vacante, VacanteHabilidad


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
    yield TestClient(app)
    app.dependency_overrides.clear()
