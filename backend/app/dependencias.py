"""Dependencias de FastAPI: quién es la persona, qué puede hacer y qué clientes puede ver.

Los permisos se aplican acá, en el servidor. Ocultar un ítem del menú no alcanza.
"""
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Select, exists, select
from sqlalchemy.orm import Session

from app import auditoria
from app.db import get_db
from app.modelos import Asignacion, Cliente, Usuario
from app.permisos import Alcance, Capacidad, permisos_de
from app.seguridad import leer_token

_esquema = HTTPBearer(auto_error=False)


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema),
    db: Session = Depends(get_db),
) -> Usuario:
    """Valida el token y que la persona siga activa. Si no, 401 (el frontend muestra "sesión vencida")."""
    error = HTTPException(status_code=401, detail="La sesión venció o no es válida. Ingresá de nuevo.")
    if credenciales is None:
        raise error
    usuario_id = leer_token(credenciales.credentials)
    if usuario_id is None:
        raise error
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise error
    return usuario


def denegar(db: Session, usuario: Usuario, detalle: dict, cliente_id: int | None = None) -> None:
    """Deja asentado el intento y responde 403."""
    auditoria.registrar(
        db,
        accion="acceso_denegado",
        usuario_id=usuario.id,
        cliente_id=cliente_id,
        detalle=detalle,
    )
    db.commit()
    raise HTTPException(status_code=403, detail="No tenés acceso a este recurso.")


def requiere(capacidad: Capacidad) -> Callable[..., Usuario]:
    def dependencia(
        request: Request,
        usuario: Usuario = Depends(usuario_actual),
        db: Session = Depends(get_db),
    ) -> Usuario:
        if capacidad not in permisos_de(usuario.rol, usuario.area).capacidades:
            denegar(db, usuario, {"capacidad": capacidad.value, "ruta": request.url.path})
        return usuario

    return dependencia


def clientes_visibles(usuario: Usuario) -> Select[tuple[Cliente]]:
    """Consulta de clientes que esta persona puede ver, según la tabla de permisos."""
    alcance = permisos_de(usuario.rol, usuario.area).alcance
    consulta = select(Cliente)
    if alcance == Alcance.TODOS:
        return consulta
    if alcance == Alcance.AREA:
        return consulta.where(Cliente.area == usuario.area)
    if alcance == Alcance.ASIGNADOS:
        return consulta.where(
            exists().where(
                Asignacion.cliente_id == Cliente.id,
                Asignacion.usuario_id == usuario.id,
                Asignacion.fecha_fin.is_(None),
            )
        )
    return consulta.where(False)


def cliente_autorizado(
    cliente_id: int,
    request: Request,
    usuario: Usuario = Depends(requiere(Capacidad.VER_CLIENTES)),
    db: Session = Depends(get_db),
) -> Cliente:
    """Devuelve el cliente solo si la persona puede verlo. Si no, 403 (también cuando el ID no existe,
    salvo que la persona vea todos los clientes: así no se puede explorar qué IDs existen)."""
    cliente = db.scalar(clientes_visibles(usuario).where(Cliente.id == cliente_id))
    if cliente is not None:
        return cliente
    if permisos_de(usuario.rol, usuario.area).alcance == Alcance.TODOS:
        raise HTTPException(status_code=404, detail="No encontramos ese cliente.")
    denegar(
        db,
        usuario,
        {"motivo": "cliente_fuera_de_alcance", "ruta": request.url.path},
        cliente_id=cliente_id,
    )
    raise AssertionError("inalcanzable")  # denegar() siempre lanza 403
