"""Conexión a la base con el rol de la aplicación (sin permiso para modificar la auditoría)."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url_app, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Una sesión por pedido. Quien escribe hace commit de forma explícita; si no, se descarta."""
    with SessionLocal() as db:
        yield db
