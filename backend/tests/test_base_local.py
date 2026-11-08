"""Frenos para no escribir datos de prueba (semilla) ni vaciar tablas (tests) en una base real."""

import pytest

from app.config import get_settings
from app.db import es_base_local, host_de
from scripts import seed

LOCALES = [
    "postgresql+psycopg://postgres:postgres@localhost:54322/postgres",
    "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/immpetus",
    "postgresql+psycopg://postgres:postgres@[::1]:5432/immpetus",
    "postgresql+psycopg://postgres:postgres@host.docker.internal:54322/postgres",
    "postgresql+psycopg:///immpetus",  # socket unix
]
REMOTAS = [
    "postgresql+psycopg://postgres:SECRETO@db.abcdefgh.supabase.co:5432/postgres",
    "postgresql+psycopg://postgres.abc:SECRETO@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
    "postgresql+psycopg://u:SECRETO@10.0.0.5:5432/x",
]


@pytest.mark.parametrize("url", LOCALES)
def test_bases_locales(url):
    assert es_base_local(url) is True


@pytest.mark.parametrize("url", REMOTAS)
def test_bases_remotas(url):
    assert es_base_local(url) is False


def test_host_de_nunca_muestra_la_contrasena():
    assert host_de(REMOTAS[0]) == "db.abcdefgh.supabase.co"
    assert all("SECRETO" not in host_de(u) for u in REMOTAS)


def test_la_semilla_se_niega_a_correr_contra_una_base_remota(monkeypatch):
    monkeypatch.setattr(get_settings(), "database_url", REMOTAS[0])
    monkeypatch.delenv("SEED_PERMITIR_REMOTA", raising=False)
    with pytest.raises(SystemExit) as e:
        seed._exigir_base_local()
    mensaje = str(e.value)
    assert "db.abcdefgh.supabase.co" in mensaje and "SECRETO" not in mensaje
    assert "SEED_PERMITIR_REMOTA=si" in mensaje


def test_la_semilla_corre_en_local_y_con_el_permiso_explicito(monkeypatch):
    monkeypatch.setattr(get_settings(), "database_url", LOCALES[0])
    seed._exigir_base_local()  # no lanza
    monkeypatch.setattr(get_settings(), "database_url", REMOTAS[0])
    monkeypatch.setenv("SEED_PERMITIR_REMOTA", "si")
    seed._exigir_base_local()  # permiso explícito: no lanza
    monkeypatch.setenv("SEED_PERMITIR_REMOTA", "true")  # solo el valor exacto "si" cuenta
    with pytest.raises(SystemExit):
        seed._exigir_base_local()
