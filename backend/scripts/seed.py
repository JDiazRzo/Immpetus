"""Datos semilla: las 4 vacantes de prueba (mismas que frontend/src/mocks/vacantes.ts).

Uso:  uv run python -m scripts.seed      (idempotente: no duplica)
Solo datos inventados. Nunca cargar HV reales.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.orm import Habilidad, Vacante, VacanteHabilidad

RESP = ["[Responsabilidad]", "[Responsabilidad]", "[Responsabilidad]"]
DESC = "[Propósito del cargo, equipo al que pertenece y principales retos.]"

VACANTES = [
    (
        "CMG-1020",
        "content-manager-estratega-de-marca",
        "Content Manager, Estratega de Marca",
        "Bogotá",
        "hibrido",
        "Híbrido",
        None,
        True,
        "2026-10-20T13:00:00+00:00",
        [
            ("Estrategia de contenido", "tecnica", True),
            ("Gestión de marca", "tecnica", True),
            ("Redes sociales", "herramienta", False),
        ],
    ),
    (
        "AAF-1018",
        "asistente-administrativo-y-financiero",
        "Asistente Administrativo y Financiero",
        "Bogotá",
        "presencial",
        "Presencial",
        None,
        False,
        "2026-10-18T13:00:00+00:00",
        [("Contabilidad básica", "tecnica", True), ("Excel", "herramienta", True)],
    ),
    (
        "GSC-1015",
        "gestor-soporte-servicio-cliente",
        "Gestor de Soporte y Servicio al Cliente",
        "Bogotá, Sabana Norte",
        "remoto",
        "80 % remoto",
        "$2.700.000",
        False,
        "2026-10-15T13:00:00+00:00",
        [
            ("Servicio al cliente", "blanda", True),
            ("Herramientas de tickets", "herramienta", True),
            ("Comunicación escrita", "blanda", False),
        ],
    ),
    (
        "HME-1012",
        "head-of-marketplace-ecommerce",
        "Head of Marketplace & Ecommerce",
        "LATAM",
        "remoto",
        "Remoto",
        "USD 2.500+",
        False,
        "2026-10-12T13:00:00+00:00",
        [
            ("Marketplaces", "tecnica", True),
            ("Ecommerce", "tecnica", True),
            ("Liderazgo de equipos", "blanda", False),
        ],
    ),
]


def main() -> None:
    with Session(get_engine()) as db:
        for cod, slug, cargo, ciudad, mod, det, sal, urg, pub, crit in VACANTES:
            if db.scalar(select(Vacante).where(Vacante.slug == slug)):
                continue
            v = Vacante(
                codigo=cod,
                slug=slug,
                cargo=cargo,
                ciudad=ciudad,
                modalidad=mod,
                modalidad_detalle=det,
                jornada="Tiempo completo",
                salario_texto=sal,
                descripcion=DESC,
                responsabilidades=RESP,
                urgente=urg,
                activa=True,
                publicada_en=datetime.fromisoformat(pub),
            )
            db.add(v)
            db.flush()
            for nombre, cat, obligatoria in crit:
                h = db.scalar(select(Habilidad).where(Habilidad.nombre == nombre))
                if h is None:
                    h = Habilidad(nombre=nombre, categoria=cat)
                    db.add(h)
                    db.flush()
                db.add(
                    VacanteHabilidad(
                        vacante_id=v.id,
                        habilidad_id=h.id,
                        obligatoria=obligatoria,
                        peso=3 if obligatoria else 1,
                    )
                )
        db.commit()
    print("Semilla lista.")


if __name__ == "__main__":
    main()
