"""Tablas del paso 1. Los nombres van en español sin tildes. Las migraciones son la fuente de verdad."""
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str] = mapped_column(String(254))
    hash_contrasena: Mapped[str] = mapped_column(String(255))
    area: Mapped[str] = mapped_column(String(40))
    rol: Mapped[str] = mapped_column(String(40))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Cliente(Base):
    __tablename__ = "cliente"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160))
    area: Mapped[str] = mapped_column(String(40))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contribuyentes: Mapped[list["Contribuyente"]] = relationship(
        back_populates="cliente", order_by="Contribuyente.id"
    )


class Contribuyente(Base):
    __tablename__ = "contribuyente"

    id: Mapped[int] = mapped_column(primary_key=True)
    cuit: Mapped[str] = mapped_column(String(11))
    nombre: Mapped[str] = mapped_column(String(160))
    tipo: Mapped[str] = mapped_column(String(20))
    condicion: Mapped[str] = mapped_column(String(30))
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))

    cliente: Mapped[Cliente] = relationship(back_populates="contribuyentes")


class Asignacion(Base):
    __tablename__ = "asignacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Impuesto(Base):
    __tablename__ = "impuesto"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    orden: Mapped[int] = mapped_column(Integer, default=0)


class Estado(Base):
    __tablename__ = "estado"

    id: Mapped[int] = mapped_column(primary_key=True)
    impuesto_id: Mapped[int] = mapped_column(ForeignKey("impuesto.id"))
    nombre: Mapped[str] = mapped_column(String(80))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[str] = mapped_column(String(20))


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer)
    accion: Mapped[str] = mapped_column(String(60))
    entidad: Mapped[str | None] = mapped_column(String(40))
    entidad_id: Mapped[int | None] = mapped_column(Integer)
    cliente_id: Mapped[int | None] = mapped_column(Integer)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    detalle: Mapped[dict[str, Any]] = mapped_column(JSONB)
    hash_anterior: Mapped[str] = mapped_column(String(64))
    hash_propio: Mapped[str] = mapped_column(String(64))
