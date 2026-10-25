import uuid

import pytest

from app.errors import AppError
from app.orm import Candidato
from app.services import estados


@pytest.mark.parametrize(
    "nota,esperado",
    [(5, "nuevo"), (4, "nuevo"), (3, "reserva"), (2, "por_validar"), (1, "por_validar")],
)
def test_mapeo_nota_estado(nota, esperado):
    assert estados.estado_inicial_por_nota(nota) == esperado


def test_el_mapeo_nunca_devuelve_no_apto():
    assert all(estados.estado_inicial_por_nota(n) != "no_apto" for n in range(1, 6))


def test_nota_fuera_de_rango():
    with pytest.raises(ValueError):
        estados.estado_inicial_por_nota(6)


def test_estados_finales_no_tienen_salida():
    assert estados.TRANSICIONES["no_apto"] == set() == estados.TRANSICIONES["contratado"]


def test_sistema_no_puede_asignar_no_apto(db):
    c = Candidato(
        vacante_id=uuid.uuid4(),
        nombre="x",
        correo="x@x.co",
        canal="web",
        autorizacion_datos=True,
        autorizacion_fecha=None,
        autorizacion_version="1.0",
    )
    with pytest.raises(AppError) as e:
        estados.registrar_estado_inicial(db, c, "no_apto")
    assert e.value.status == 409


def test_transicion_invalida_da_409(db):
    c = Candidato(id=uuid.uuid4(), estado="no_apto")
    with pytest.raises(AppError) as e:
        estados.cambiar_estado(db, c, "entrevista", uuid.uuid4(), None)
    assert e.value.status == 409 and e.value.code == "CONFLICT"
