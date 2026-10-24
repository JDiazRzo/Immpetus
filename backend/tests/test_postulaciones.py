from sqlalchemy import select

from app.orm import Candidato, Estado

PDF = b"%PDF-1.4 hoja de vida inventada"


def _datos(vacante_id, **extra):
    base = {
        "vacante_id": str(vacante_id),
        "nombre": "Ana Prueba",
        "correo": "ana@ejemplo.com",
        "celular": "3001234567",
        "autorizacion_datos": "true",
        "autorizacion_version": "1.0",
    }
    return {**base, **extra}


def _post(client, datos, contenido=PDF, tipo="application/pdf"):
    return client.post(
        "/api/postulaciones", data=datos, files={"archivo": ("hv.pdf", contenido, tipo)}
    )


def test_postulacion_ok_guarda_candidato_y_estado(client, vacantes, db, subidas):
    r = _post(client, _datos(vacantes["activa"].id))
    assert r.status_code == 201
    assert r.json()["estado"] == "nuevo"
    cand = db.scalar(select(Candidato))
    assert cand.canal == "web" and cand.autorizacion_datos and cand.autorizacion_version == "1.0"
    assert cand.drive_file_id == "fake-id"
    assert [e.estado for e in db.scalars(select(Estado))] == ["nuevo"]
    assert subidas == ["SN - Ana Prueba - Gestor de Soporte.pdf"]


def test_sin_autorizacion_da_400_y_no_sube_nada(client, vacantes, db, subidas):
    r = _post(client, _datos(vacantes["activa"].id, autorizacion_datos="false"))
    assert r.status_code == 400
    assert r.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "Debes autorizar el tratamiento de tus datos personales para postularte.",
        "field": "autorizacion_datos",
    }
    assert subidas == [] and db.scalar(select(Candidato)) is None


def test_archivo_no_pdf_da_400(client, vacantes):
    r = _post(client, _datos(vacantes["activa"].id), b"hola", "text/plain")
    assert r.status_code == 400 and r.json()["error"]["field"] == "archivo"


def test_pdf_falso_con_content_type_pdf_da_400(client, vacantes):
    r = _post(client, _datos(vacantes["activa"].id), b"MZ ejecutable", "application/pdf")
    assert r.status_code == 400


def test_pdf_muy_grande_da_413(client, vacantes):
    grande = b"%PDF-" + b"0" * (5 * 1024 * 1024 + 10)
    r = _post(client, _datos(vacantes["activa"].id), grande)
    assert r.status_code == 413 and r.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_vacante_inactiva_da_404(client, vacantes):
    r = _post(client, _datos(vacantes["inactiva"].id))
    assert r.status_code == 404


def test_correo_invalido_da_400(client, vacantes):
    r = _post(client, _datos(vacantes["activa"].id, correo="no-es-correo"))
    assert r.status_code == 400 and r.json()["error"]["field"] == "correo"


def test_falta_campo_obligatorio_da_400_con_formato_contrato(client, vacantes):
    datos = _datos(vacantes["activa"].id)
    del datos["nombre"]
    r = _post(client, datos)
    assert r.status_code == 400 and r.json()["error"]["field"] == "nombre"
