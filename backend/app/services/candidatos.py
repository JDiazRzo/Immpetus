"""Lectura de candidatos para el centro de mando y corrección de nota.

`nota`, `nota_validada` y `validada_por` se derivan igual que la vista v_candidatos (contrato 5.2).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import AppError, not_found
from app.models.admin import (
    CandidatoDetalle,
    CandidatoLista,
    EventoHistorial,
    HabilidadCandidato,
    ResumenVacante,
)
from app.orm import (
    Calificacion,
    Candidato,
    CandidatoHabilidad,
    Estado,
    Habilidad,
    Usuario,
    Vacante,
    VacanteHabilidad,
)


def _utc(fecha: datetime) -> datetime:
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=UTC)


def obtener(db: Session, candidato_id: uuid.UUID) -> Candidato:
    c = db.get(Candidato, candidato_id)
    if c is None:
        raise not_found("El candidato no existe.")
    return c


def exigir_no_anonimizado(c: Candidato) -> None:
    if c.anonimizado_en is not None:
        raise AppError(409, "CONFLICT", "El candidato fue anonimizado y ya no se puede modificar.")


def _calificaciones(db: Session, ids: list[uuid.UUID]) -> dict[uuid.UUID, list[Calificacion]]:
    por: dict[uuid.UUID, list[Calificacion]] = {i: [] for i in ids}
    if ids:
        filas = db.scalars(select(Calificacion).where(Calificacion.candidato_id.in_(ids)))
        for f in sorted(filas, key=lambda x: _utc(x.fecha)):
            por[f.candidato_id].append(f)
    return por


def _estados(db: Session, ids: list[uuid.UUID]) -> dict[uuid.UUID, list[Estado]]:
    por: dict[uuid.UUID, list[Estado]] = {i: [] for i in ids}
    if ids:
        filas = db.scalars(select(Estado).where(Estado.candidato_id.in_(ids)))
        for f in sorted(filas, key=lambda x: _utc(x.fecha)):
            por[f.candidato_id].append(f)
    return por


def _nombres(db: Session, ids: set[uuid.UUID | None]) -> dict[uuid.UUID, str]:
    reales = {i for i in ids if i}
    if not reales:
        return {}
    return {u.id: u.nombre for u in db.scalars(select(Usuario).where(Usuario.id.in_(reales)))}


def armar_listas(db: Session, candidatos: list[Candidato]) -> list[CandidatoLista]:
    ids = [c.id for c in candidatos]
    cals, ests = _calificaciones(db, ids), _estados(db, ids)
    usuarios = _nombres(
        db,
        {c.usuario_id for lst in cals.values() for c in lst}
        | {e.validado_por for lst in ests.values() for e in lst},
    )

    habs: dict[uuid.UUID, list[HabilidadCandidato]] = {i: [] for i in ids}
    if ids:
        pedidas = {
            (v.vacante_id, v.habilidad_id)
            for v in db.scalars(
                select(VacanteHabilidad).where(
                    VacanteHabilidad.vacante_id.in_({c.vacante_id for c in candidatos})
                )
            )
        }
        vacante_de = {c.id: c.vacante_id for c in candidatos}
        filas = db.execute(
            select(CandidatoHabilidad.candidato_id, Habilidad.id, Habilidad.nombre)
            .join(Habilidad, Habilidad.id == CandidatoHabilidad.habilidad_id)
            .where(CandidatoHabilidad.candidato_id.in_(ids))
            .order_by(Habilidad.nombre)
        ).all()
        for cand_id, hab_id, nombre in filas:
            habs[cand_id].append(
                HabilidadCandidato(nombre=nombre, coincide=(vacante_de[cand_id], hab_id) in pedidas)
            )

    salida = []
    for c in candidatos:
        ultima = cals[c.id][-1] if cals[c.id] else None
        validada, por = False, None
        if ultima is not None:
            if ultima.origen == "analista":
                validada, por = True, usuarios.get(ultima.usuario_id)
            else:
                humano = next(
                    (
                        e
                        for e in reversed(ests[c.id])
                        if e.validado_por and _utc(e.fecha) >= _utc(ultima.fecha)
                    ),
                    None,
                )
                if humano:
                    validada, por = True, usuarios.get(humano.validado_por)
        anonimo = c.anonimizado_en is not None
        salida.append(
            CandidatoLista(
                id=c.id,
                vacante_id=c.vacante_id,
                nombre=c.nombre,
                correo=c.correo,
                celular=c.celular,
                canal=c.canal,
                drive_url=None if anonimo else c.drive_url,
                archivo_nombre=None if anonimo else c.archivo_nombre,
                nota=ultima.nota if ultima else None,
                nota_validada=validada,
                validada_por=por,
                estado=c.estado,
                acepta_futuras=c.acepta_futuras,
                habilidades=habs[c.id],
                creado_en=c.creado_en,
            )
        )
    return salida


def existe_postulacion_activa(db: Session, vacante_id: uuid.UUID, correo: str) -> bool:
    """¿Ese correo ya tiene una postulación activa a la vacante? (409 en los 3 caminos de ingreso)

    Activa = no anonimizada y no descartada: quien fue `no_apto` puede volver a postularse.
    """
    return (
        db.scalar(
            select(Candidato.id).where(
                Candidato.vacante_id == vacante_id,
                func.lower(Candidato.correo) == correo.strip().lower(),
                Candidato.anonimizado_en.is_(None),
                Candidato.estado != "no_apto",
            )
        )
        is not None
    )


def _ultima_nota():
    """Nota vigente (la última calificación) como subconsulta, para ordenar y paginar en SQL."""
    return (
        select(Calificacion.nota)
        .where(Calificacion.candidato_id == Candidato.id)
        .order_by(Calificacion.fecha.desc())
        .limit(1)
        .scalar_subquery()
    )


def listar(
    db: Session,
    *,
    vacante_id: uuid.UUID | None = None,
    estado: str | None = None,
    orden: str = "reciente",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CandidatoLista], int]:
    """Candidatos de una vacante o de TODAS (vacante_id=None); filtra, ordena y pagina en SQL.

    Solo se cargan y se arman los de la página pedida: no depende de cuántos candidatos haya.
    """
    if vacante_id is not None and db.get(Vacante, vacante_id) is None:
        raise not_found("La vacante no existe.")
    filtros = []
    if vacante_id is not None:
        filtros.append(Candidato.vacante_id == vacante_id)
    if estado:
        filtros.append(Candidato.estado == estado)

    total = db.scalar(select(func.count()).select_from(Candidato).where(*filtros)) or 0
    nota = _ultima_nota()
    criterio = {
        "nota_desc": [nota.desc().nulls_last(), Candidato.creado_en.desc()],
        "nota_asc": [nota.asc().nulls_last(), Candidato.creado_en.desc()],
    }.get(orden, [Candidato.creado_en.desc()])
    filas = db.scalars(
        select(Candidato)
        .where(*filtros)
        .order_by(*criterio, Candidato.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    return armar_listas(db, list(filas)), total


def resumen(db: Session, vacante_id: uuid.UUID) -> ResumenVacante:
    if db.get(Vacante, vacante_id) is None:
        raise not_found("La vacante no existe.")
    todos = armar_listas(
        db, list(db.scalars(select(Candidato).where(Candidato.vacante_id == vacante_id)))
    )
    cuenta = lambda e: sum(1 for c in todos if c.estado == e)  # noqa: E731
    return ResumenVacante(
        recibidas=len(todos),
        nota_4_5=sum(1 for c in todos if c.nota is not None and c.nota >= 4),
        reserva=cuenta("reserva"),
        por_validar=cuenta("por_validar"),
        entrevista=cuenta("entrevista"),
    )


def detalle(db: Session, c: Candidato) -> CandidatoDetalle:
    base = armar_listas(db, [c])[0]
    cals, ests = _calificaciones(db, [c.id])[c.id], _estados(db, [c.id])[c.id]
    nombres = _nombres(db, {x.usuario_id for x in cals} | {e.validado_por for e in ests})

    eventos = [
        EventoHistorial(
            fecha=c.creado_en,
            evento="postulacion_recibida",
            detalle=f"Canal {c.canal}. Autorización v{c.autorizacion_version}",
            usuario=None,
        )
    ]
    if c.drive_file_id and c.anonimizado_en is None:
        eventos.append(
            EventoHistorial(
                fecha=c.creado_en,
                evento="hv_guardada",
                detalle="Hoja de vida guardada en Drive",
                usuario=None,
            )
        )
    for k in cals:
        es_ia = k.origen == "ia"
        detalle_k = f"Nota {k.nota}" + ("" if es_ia or not k.motivo else f". {k.motivo}")
        eventos.append(
            EventoHistorial(
                fecha=k.fecha,
                evento="calificacion_ia" if es_ia else "calificacion_analista",
                detalle=detalle_k,
                usuario=nombres.get(k.usuario_id),
            )
        )
    for e in ests[1:]:  # el primero es la recepción de la postulación
        extra = f". {e.observacion}" if e.observacion else ""
        sistema = "" if e.validado_por else " (asignado por el sistema según la nota)"
        eventos.append(
            EventoHistorial(
                fecha=e.fecha,
                evento="cambio_estado",
                detalle=f"Estado: {e.estado}{extra}{sistema}",
                usuario=nombres.get(e.validado_por),
            )
        )
    eventos.sort(key=lambda x: _utc(x.fecha))

    ultima_ia = next((k for k in reversed(cals) if k.origen == "ia"), None)
    anonimo = c.anonimizado_en is not None  # el resumen puede tener datos personales
    return CandidatoDetalle(
        **base.model_dump(),
        resumen_ia=None if anonimo or not ultima_ia else ultima_ia.resumen,
        matriz=None if anonimo or not ultima_ia else ultima_ia.matriz,
        historial=eventos,
    )


def corregir_nota(
    db: Session, c: Candidato, usuario: Usuario, nota: int, motivo: str
) -> CandidatoLista:
    """Contrato 5.4: guarda la nota con origen 'analista' y NUNCA cambia el estado."""
    exigir_no_anonimizado(c)
    db.add(
        Calificacion(
            candidato_id=c.id, nota=nota, origen="analista", motivo=motivo, usuario_id=usuario.id
        )
    )
    db.commit()
    return armar_listas(db, [c])[0]
