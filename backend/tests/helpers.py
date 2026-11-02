"""Ayudas de prueba. Postgres exige que no_apto y contratado tengan quién los validó."""

from sqlalchemy import select

from app.orm import Usuario

FINALES = ("no_apto", "contratado")


def validador(db, estado):
    """Id de un usuario válido si el estado es final; None en los demás."""
    if estado not in FINALES:
        return None
    u = db.scalar(select(Usuario).where(Usuario.correo == "validador@immpetus.co"))
    if u is None:
        u = Usuario(correo="validador@immpetus.co", nombre="Validador", rol="analista")
        db.add(u)
        db.flush()
    return u.id
