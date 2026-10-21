"""Auditoría inmutable con encadenamiento por hash.

Reglas:
- Solo se inserta. La protección real está en la base (rol ks_app sin UPDATE/DELETE y un trigger).
- Cada fila guarda el hash de la anterior, así que alterar o sacar una fila rompe la cadena.
- La inserción se serializa con un bloqueo de base de datos: dos escrituras simultáneas no pueden
  tomar el mismo "hash anterior".
- REGLA DE ORDEN: la auditoría es lo último que se hace antes del commit. El bloqueo se mantiene hasta
  el commit y, si otra operación tomara un bloqueo de fila después, podría haber un abrazo mortal.
- El detalle nunca lleva contraseñas, claves, tokens ni CUIT: solo identificadores.
- El detalle no admite números con decimales (para que el hash sea reproducible).
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modelos import Auditoria

HASH_INICIAL = "0" * 64
CLAVE_BLOQUEO = 7340101  # número arbitrario, propio de la auditoría
_PALABRAS_PROHIBIDAS = ("contrasena", "password", "clave", "cuit", "token", "secret")


def _revisar_detalle(valor: Any, ruta: str = "detalle") -> None:
    if isinstance(valor, dict):
        for k, v in valor.items():
            if any(p in str(k).lower() for p in _PALABRAS_PROHIBIDAS):
                raise ValueError(f"El detalle de auditoría no puede incluir datos sensibles ({ruta}.{k})")
            _revisar_detalle(v, f"{ruta}.{k}")
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            _revisar_detalle(v, f"{ruta}[{i}]")
    elif isinstance(valor, float):
        raise ValueError(f"El detalle de auditoría no admite decimales ({ruta})")


def _campos_para_hash(
    *,
    usuario_id: int | None,
    accion: str,
    entidad: str | None,
    entidad_id: int | None,
    cliente_id: int | None,
    fecha: datetime,
    detalle: dict[str, Any],
) -> dict[str, Any]:
    return {
        "usuario_id": usuario_id,
        "accion": accion,
        "entidad": entidad,
        "entidad_id": entidad_id,
        "cliente_id": cliente_id,
        "fecha": fecha.astimezone(timezone.utc).isoformat(),
        "detalle": detalle,
    }


def calcular_hash(campos: dict[str, Any], hash_anterior: str) -> str:
    canonico = json.dumps(campos, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256((hash_anterior + canonico).encode("utf-8")).hexdigest()


def registrar(
    db: Session,
    *,
    accion: str,
    usuario_id: int | None = None,
    entidad: str | None = None,
    entidad_id: int | None = None,
    cliente_id: int | None = None,
    detalle: dict[str, Any] | None = None,
) -> Auditoria:
    """Agrega una fila a la cadena dentro de la transacción actual. No hace commit."""
    detalle = detalle or {}
    _revisar_detalle(detalle)

    db.execute(text("SELECT pg_advisory_xact_lock(:clave)"), {"clave": CLAVE_BLOQUEO})
    anterior = db.scalar(select(Auditoria.hash_propio).order_by(Auditoria.id.desc()).limit(1))
    hash_anterior = anterior or HASH_INICIAL

    fecha = datetime.now(timezone.utc)
    campos = _campos_para_hash(
        usuario_id=usuario_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        cliente_id=cliente_id,
        fecha=fecha,
        detalle=detalle,
    )
    fila = Auditoria(
        usuario_id=usuario_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        cliente_id=cliente_id,
        fecha=fecha,
        detalle=detalle,
        hash_anterior=hash_anterior,
        hash_propio=calcular_hash(campos, hash_anterior),
    )
    db.add(fila)
    db.flush()
    return fila


def verificar_cadena(db: Session) -> tuple[bool, int | None, int]:
    """Recorre toda la cadena. Devuelve (está_bien, id_de_la_primera_fila_con_problema, filas_revisadas).

    Detecta filas alteradas y filas sacadas del medio. No puede detectar que se hayan borrado las últimas
    filas (eso lo impide el trigger de la base).
    """
    esperado_anterior = HASH_INICIAL
    revisadas = 0
    filas = db.execute(select(Auditoria).order_by(Auditoria.id)).scalars()
    for fila in filas:
        revisadas += 1
        campos = _campos_para_hash(
            usuario_id=fila.usuario_id,
            accion=fila.accion,
            entidad=fila.entidad,
            entidad_id=fila.entidad_id,
            cliente_id=fila.cliente_id,
            fecha=fila.fecha,
            detalle=fila.detalle,
        )
        if fila.hash_anterior != esperado_anterior or fila.hash_propio != calcular_hash(
            campos, fila.hash_anterior
        ):
            return False, fila.id, revisadas
        esperado_anterior = fila.hash_propio
    return True, None, revisadas
