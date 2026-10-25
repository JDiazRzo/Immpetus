from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.errors import not_found
from app.models.vacantes import CriterioPublico, VacanteDetalle, VacanteResumen
from app.orm import Habilidad, Vacante, VacanteHabilidad


def listar_activas(
    db: Session, q: str | None, modalidad: str | None, page: int, page_size: int
) -> tuple[list[VacanteResumen], int]:
    filtros = [Vacante.activa.is_(True)]
    if modalidad:
        filtros.append(Vacante.modalidad == modalidad)
    if q:
        patron = f"%{q.strip()}%"
        filtros.append(or_(Vacante.cargo.ilike(patron), Vacante.descripcion.ilike(patron)))

    total = db.scalar(select(func.count()).select_from(Vacante).where(*filtros)) or 0
    filas = db.scalars(
        select(Vacante)
        .where(*filtros)
        .order_by(Vacante.publicada_en.desc().nulls_last(), Vacante.cargo)
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    return [VacanteResumen.model_validate(v) for v in filas], total


def obtener_activa_por_slug(db: Session, slug: str) -> VacanteDetalle:
    v = db.scalar(select(Vacante).where(Vacante.slug == slug, Vacante.activa.is_(True)))
    if v is None:
        raise not_found("Esta vacante no existe o ya no está disponible.")
    criterios = db.execute(
        select(Habilidad.nombre, VacanteHabilidad.obligatoria)
        .join(VacanteHabilidad, VacanteHabilidad.habilidad_id == Habilidad.id)
        .where(VacanteHabilidad.vacante_id == v.id)
        .order_by(
            VacanteHabilidad.obligatoria.desc(), VacanteHabilidad.peso.desc(), Habilidad.nombre
        )
    ).all()
    return VacanteDetalle(
        id=v.id,
        slug=v.slug,
        cargo=v.cargo,
        ciudad=v.ciudad,
        modalidad=v.modalidad,
        modalidad_detalle=v.modalidad_detalle,
        jornada=v.jornada,
        salario_texto=v.salario_texto,
        descripcion=v.descripcion,
        responsabilidades=list(v.responsabilidades or []),
        criterios=[CriterioPublico(habilidad=n, obligatoria=o) for n, o in criterios],
        publicada_en=v.publicada_en,
    )
