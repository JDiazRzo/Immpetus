import re
import unicodedata
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import not_found, validation_error
from app.models.admin import CriterioAdmin, CriterioInput, VacanteAdmin, VacanteInput, VacanteUpdate
from app.orm import Habilidad, Usuario, Vacante, VacanteHabilidad

_PALABRAS_VACIAS = {"de", "del", "la", "el", "los", "las", "y", "e", "al", "en", "para", "a"}
_OBLIGATORIOS = ("cargo", "ciudad", "modalidad", "responsabilidades", "urgente", "activa")


def _slugify(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:80] or "vacante"


def _slug_unico(db: Session, cargo: str) -> str:
    base, n, slug = _slugify(cargo), 1, _slugify(cargo)
    while db.scalar(select(Vacante.id).where(Vacante.slug == slug)):
        n += 1
        slug = f"{base}-{n}"
    return slug


def _codigo_unico(db: Session, cargo: str) -> str:
    # Provisional: iniciales de las 3 primeras palabras + MMAA (formato por confirmar con Immpetus).
    palabras = [p for p in _slugify(cargo).split("-") if p not in _PALABRAS_VACIAS][:3]
    base = f"{''.join(p[0] for p in palabras).upper() or 'VAC'}-{datetime.now(UTC):%m%y}"
    n, codigo = 1, base
    while db.scalar(select(Vacante.id).where(Vacante.codigo == codigo)):
        n += 1
        codigo = f"{base}-{n}"
    return codigo


def _validar_criterios(db: Session, criterios: list[CriterioInput]) -> None:
    ids = [c.habilidad_id for c in criterios]
    if len(set(ids)) != len(ids):
        raise validation_error("Hay habilidades repetidas en los criterios.", "criterios")
    if ids:
        existentes = set(db.scalars(select(Habilidad.id).where(Habilidad.id.in_(ids))))
        if existentes != set(ids):
            raise validation_error("Alguna habilidad de los criterios no existe.", "criterios")


def _reemplazar_criterios(db: Session, vacante: Vacante, criterios: list[CriterioInput]) -> None:
    for fila in db.scalars(
        select(VacanteHabilidad).where(VacanteHabilidad.vacante_id == vacante.id)
    ):
        db.delete(fila)  # vacante_habilidades es configuración, no historial
    db.flush()
    for c in criterios:
        db.add(
            VacanteHabilidad(
                vacante_id=vacante.id,
                habilidad_id=c.habilidad_id,
                obligatoria=c.obligatoria,
                peso=c.peso,
            )
        )


def a_admin(db: Session, v: Vacante) -> VacanteAdmin:
    criterios = db.execute(
        select(Habilidad.id, Habilidad.nombre, VacanteHabilidad.obligatoria, VacanteHabilidad.peso)
        .join(VacanteHabilidad, VacanteHabilidad.habilidad_id == Habilidad.id)
        .where(VacanteHabilidad.vacante_id == v.id)
        .order_by(
            VacanteHabilidad.obligatoria.desc(), VacanteHabilidad.peso.desc(), Habilidad.nombre
        )
    ).all()
    return VacanteAdmin(
        id=v.id,
        codigo=v.codigo,
        slug=v.slug,
        cargo=v.cargo,
        cliente=v.cliente,
        ciudad=v.ciudad,
        modalidad=v.modalidad,
        modalidad_detalle=v.modalidad_detalle,
        jornada=v.jornada,
        salario_texto=v.salario_texto,
        descripcion=v.descripcion,
        responsabilidades=list(v.responsabilidades or []),
        urgente=v.urgente,
        activa=v.activa,
        publicada_en=v.publicada_en,
        criterios=[
            CriterioAdmin(habilidad_id=i, habilidad=n, obligatoria=o, peso=p)
            for i, n, o, p in criterios
        ],
    )


def obtener(db: Session, vacante_id: uuid.UUID) -> Vacante:
    v = db.get(Vacante, vacante_id)
    if v is None:
        raise not_found("La vacante no existe.")
    return v


def listar(db: Session, page: int, page_size: int) -> tuple[list[VacanteAdmin], int]:
    total = db.scalar(select(func.count()).select_from(Vacante)) or 0
    filas = db.scalars(
        select(Vacante)
        .order_by(Vacante.creada_en.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    return [a_admin(db, v) for v in filas], total


def crear(db: Session, usuario: Usuario, datos: VacanteInput) -> VacanteAdmin:
    _validar_criterios(db, datos.criterios)
    v = Vacante(
        codigo=_codigo_unico(db, datos.cargo),
        slug=_slug_unico(db, datos.cargo),
        creada_por=usuario.id,
        publicada_en=datetime.now(UTC) if datos.activa else None,
        **datos.model_dump(exclude={"criterios"}),
    )
    db.add(v)
    db.flush()
    _reemplazar_criterios(db, v, datos.criterios)
    db.commit()
    return a_admin(db, v)


def actualizar(db: Session, vacante_id: uuid.UUID, cambios: VacanteUpdate) -> VacanteAdmin:
    v = obtener(db, vacante_id)
    datos = cambios.model_dump(exclude_unset=True)
    for campo in _OBLIGATORIOS:
        if campo in datos and datos[campo] is None:
            raise validation_error("Este campo no puede quedar vacío.", campo)

    criterios = cambios.criterios if "criterios" in datos else None
    if criterios is not None:
        _validar_criterios(db, criterios)
    datos.pop("criterios", None)
    if "responsabilidades" in datos:
        datos["responsabilidades"] = [r.strip() for r in datos["responsabilidades"] if r.strip()]

    for campo, valor in datos.items():  # el slug no cambia: protege el SEO de la URL
        setattr(v, campo, valor)
    if datos.get("activa") and v.publicada_en is None:
        v.publicada_en = datetime.now(UTC)
    if criterios is not None:
        _reemplazar_criterios(db, v, criterios)
    db.commit()
    return a_admin(db, v)


def buscar_habilidades(db: Session, q: str | None) -> list[Habilidad]:
    consulta = select(Habilidad).order_by(Habilidad.nombre).limit(50)
    if q:
        consulta = consulta.where(Habilidad.nombre.ilike(f"%{q.strip()}%"))
    return list(db.scalars(consulta))
