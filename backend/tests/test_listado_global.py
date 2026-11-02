import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import event

from app.orm import Calificacion, Candidato, Estado
from tests.helpers import validador

T0 = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def _cand(db, vacante, nombre, estado="nuevo", nota=None, minutos=0):
    c = Candidato(
        vacante_id=vacante.id,
        nombre=nombre,
        correo=f"{uuid.uuid4().hex[:8]}@x.co",
        canal="web",
        estado=estado,
        autorizacion_datos=True,
        autorizacion_fecha=T0,
        autorizacion_version="1.0",
        creado_en=T0 + timedelta(minutes=minutos),
    )
    db.add(c)
    db.flush()
    db.add(
        Estado(
            candidato_id=c.id,
            validado_por=validador(db, estado),
            estado=estado,
            fecha=T0 + timedelta(minutes=minutos),
        )
    )
    if nota:
        db.add(
            Calificacion(
                candidato_id=c.id,
                nota=nota,
                origen="ia",
                fecha=T0 + timedelta(minutes=minutos, seconds=5),
            )
        )
    db.commit()
    return c


def test_trae_candidatos_de_todas_las_vacantes_filtrados_por_estado(client, login, vacantes, db):
    login("analista")
    _cand(db, vacantes["activa"], "A", "por_validar", nota=2, minutos=1)
    _cand(db, vacantes["otra"], "B", "por_validar", nota=1, minutos=2)
    _cand(
        db, vacantes["inactiva"], "C", "por_validar", nota=2, minutos=3
    )  # vacante inactiva también
    _cand(db, vacantes["activa"], "D", "nuevo", nota=5, minutos=4)
    r = client.get("/api/admin/candidatos?estado=por_validar").json()
    assert r["total"] == 3 and {c["nombre"] for c in r["items"]} == {"A", "B", "C"}
    assert {c["vacante_id"] for c in r["items"]} == {str(v.id) for v in vacantes.values()}
    assert client.get("/api/admin/candidatos").json()["total"] == 4  # sin filtro: todos


def test_ordenes_y_paginacion(client, login, vacantes, db):
    login("gerencia")
    _cand(db, vacantes["activa"], "n2", nota=2, minutos=1)
    _cand(db, vacantes["otra"], "n5", nota=5, minutos=2)
    _cand(db, vacantes["activa"], "n4", nota=4, minutos=3)
    _cand(db, vacantes["otra"], "sin", minutos=4)

    def nombres(q):
        return [c["nombre"] for c in client.get(f"/api/admin/candidatos?{q}").json()["items"]]

    assert nombres("orden=nota_desc") == ["n5", "n4", "n2", "sin"]  # sin nota, al final
    assert nombres("orden=nota_asc") == ["n2", "n4", "n5", "sin"]
    assert nombres("") == ["sin", "n4", "n5", "n2"]  # reciente por defecto
    assert nombres("orden=nota_desc&page=2&page_size=3") == ["sin"]
    p = client.get("/api/admin/candidatos?page=2&page_size=3").json()
    assert p["total"] == 4 and p["page"] == 2 and p["page_size"] == 3


def test_usa_la_ultima_nota_aunque_se_haya_corregido(client, login, vacantes, db):
    login("analista")
    a = _cand(db, vacantes["activa"], "a", nota=2, minutos=1)
    _cand(db, vacantes["activa"], "b", nota=3, minutos=2)
    client.post(
        f"/api/admin/candidatos/{a.id}/calificacion",
        json={"nota": 5, "motivo": "Revisé la HV completa"},
    )
    r = client.get("/api/admin/candidatos?orden=nota_desc").json()["items"]
    assert [(c["nombre"], c["nota"]) for c in r] == [("a", 5), ("b", 3)]


def test_validaciones_y_permisos(client, login, vacantes):
    assert client.get("/api/admin/candidatos").status_code == 401
    login("gerencia")  # gerencia puede consultar
    assert client.get("/api/admin/candidatos?estado=volando").status_code == 400
    assert client.get("/api/admin/candidatos?orden=raro").status_code == 400
    assert client.get("/api/admin/candidatos?page=0").status_code == 400
    assert client.get("/api/admin/candidatos?page_size=101").status_code == 400


def test_la_ruta_global_no_choca_con_la_de_detalle(client, login, vacantes, db):
    login("analista")
    c = _cand(db, vacantes["activa"], "x", nota=4)
    assert client.get(f"/api/admin/candidatos/{c.id}").json()["nombre"] == "x"
    assert client.get("/api/admin/candidatos").json()["total"] == 1


def _consultas(db, llamar) -> int:
    contador = {"n": 0}

    def contar(*_):
        contador["n"] += 1

    motor = db.get_bind()
    event.listen(motor, "before_cursor_execute", contar)
    try:
        llamar()
    finally:
        event.remove(motor, "before_cursor_execute", contar)
    return contador["n"]


def test_el_numero_de_consultas_no_crece_con_la_cantidad_de_candidatos(client, login, vacantes, db):
    """Es lo que lo hace rápido: con 3 o con 60 candidatos son las mismas consultas SQL."""
    login("analista")
    for i in range(3):
        _cand(db, vacantes["activa"], f"c{i}", "por_validar", nota=2, minutos=i)
    url = "/api/admin/candidatos?estado=por_validar&orden=nota_desc&page_size=20"
    pocas = _consultas(db, lambda: client.get(url))
    for i in range(3, 60):
        _cand(db, vacantes["otra"], f"c{i}", "por_validar", nota=(i % 5) + 1, minutos=i)
    muchas = _consultas(db, lambda: client.get(url))
    assert muchas == pocas and muchas <= 10
    r = client.get(url).json()
    assert r["total"] == 60 and len(r["items"]) == 20  # solo se arma la página pedida


# ---------- publicada_en ----------
def test_publicada_en_se_llena_al_crear_activa_y_al_activar_por_primera_vez(client, login):
    login("analista")
    cuerpo = {"cargo": "Cargo de prueba", "ciudad": "Bogotá", "modalidad": "remoto"}
    activa = client.post("/api/admin/vacantes", json={**cuerpo, "activa": True}).json()
    assert activa["publicada_en"] is not None
    borrador = client.post("/api/admin/vacantes", json=cuerpo).json()
    assert borrador["publicada_en"] is None
    primera = client.patch(f"/api/admin/vacantes/{borrador['id']}", json={"activa": True}).json()
    assert primera["publicada_en"] is not None
    client.patch(f"/api/admin/vacantes/{borrador['id']}", json={"activa": False})
    otra_vez = client.patch(f"/api/admin/vacantes/{borrador['id']}", json={"activa": True}).json()
    # conserva la fecha original (se ignora la "Z": SQLite devuelve la fecha sin zona)
    assert otra_vez["publicada_en"].rstrip("Z") == primera["publicada_en"].rstrip("Z")
