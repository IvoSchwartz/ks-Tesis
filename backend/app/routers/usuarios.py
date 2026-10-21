"""Administración de usuarios: solo Administrador/Socio. La baja desactiva, nunca borra."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import auditoria
from app.constantes import ETIQUETA_AREA, ETIQUETA_ROL, Area, Rol
from app.db import get_db
from app.dependencias import requiere
from app.errores import ErrorNegocio
from app.esquemas import UsuarioIn, UsuarioOut, UsuarioPut
from app.modelos import Usuario
from app.permisos import Capacidad
from app.seguridad import hashear
from app.servicios import clientes_asignados_activos, puede_ser_responsable

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
administrador = requiere(Capacidad.ADMINISTRAR_USUARIOS)


def _salida(u: Usuario) -> UsuarioOut:
    return UsuarioOut(
        id=u.id,
        nombre=u.nombre,
        correo=u.correo,
        area=u.area,
        area_etiqueta=ETIQUETA_AREA[Area(u.area)],
        rol=u.rol,
        rol_etiqueta=ETIQUETA_ROL[Rol(u.rol)],
        activo=u.activo,
    )


def _correo_libre(db: Session, correo: str, excepto_id: int | None = None) -> None:
    consulta = select(Usuario.id).where(func.lower(Usuario.correo) == correo.strip().lower())
    if excepto_id is not None:
        consulta = consulta.where(Usuario.id != excepto_id)
    if db.scalar(consulta) is not None:
        raise ErrorNegocio(409, "Ya hay una persona con ese correo.")


@router.get("", response_model=list[UsuarioOut])
def listar(_: Usuario = Depends(administrador), db: Session = Depends(get_db)) -> list[UsuarioOut]:
    return [_salida(u) for u in db.scalars(select(Usuario).order_by(Usuario.nombre))]


@router.post("", response_model=UsuarioOut, status_code=201)
def crear(
    datos: UsuarioIn, actor: Usuario = Depends(administrador), db: Session = Depends(get_db)
) -> UsuarioOut:
    _correo_libre(db, datos.correo)
    usuario = Usuario(
        nombre=datos.nombre.strip(),
        correo=datos.correo.strip(),
        hash_contrasena=hashear(datos.contrasena),
        area=datos.area.value,
        rol=datos.rol.value,
        activo=True,
    )
    db.add(usuario)
    db.flush()
    auditoria.registrar(
        db,
        accion="usuario_crear",
        usuario_id=actor.id,
        entidad="usuario",
        entidad_id=usuario.id,
        detalle={"rol": usuario.rol, "area": usuario.area},
    )
    db.commit()
    return _salida(usuario)


def _validar_cambio(db: Session, actor: Usuario, usuario: Usuario, cambios: dict) -> None:
    quita_acceso = cambios.get("activo") is False
    deja_de_ser_admin = "rol" in cambios and cambios["rol"] != Rol.ADMIN_SOCIO.value
    if usuario.id == actor.id and (quita_acceso or deja_de_ser_admin):
        raise ErrorNegocio(409, "No podés quitarte tu propio acceso de administración.")

    cambia_perfil = (
        quita_acceso
        or ("rol" in cambios and not puede_ser_responsable(cambios["rol"]))
        or ("area" in cambios and cambios["area"] != usuario.area)
    )
    if cambia_perfil:
        pendientes = clientes_asignados_activos(db, usuario.id)
        if pendientes:
            raise ErrorNegocio(
                409,
                f"Esa persona tiene {pendientes} cliente(s) asignado(s). Reasignalos antes de hacer este cambio.",
            )


@router.put("/{usuario_id}", response_model=UsuarioOut)
def editar(
    usuario_id: int,
    datos: UsuarioPut,
    actor: Usuario = Depends(administrador),
    db: Session = Depends(get_db),
) -> UsuarioOut:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorNegocio(404, "No encontramos a esa persona.")

    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    for campo in ("area", "rol"):
        if campo in cambios:
            cambios[campo] = cambios[campo].value
    if "correo" in cambios:
        _correo_libre(db, cambios["correo"], excepto_id=usuario.id)
    _validar_cambio(db, actor, usuario, cambios)

    for campo, valor in cambios.items():
        if campo == "contrasena":
            usuario.hash_contrasena = hashear(valor)
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
        else:
            setattr(usuario, campo, valor.strip() if isinstance(valor, str) else valor)
    db.flush()
    auditoria.registrar(
        db,
        accion="usuario_editar",
        usuario_id=actor.id,
        entidad="usuario",
        entidad_id=usuario.id,
        detalle={"campos": sorted(cambios.keys())},
    )
    db.commit()
    return _salida(usuario)


@router.delete("/{usuario_id}", response_model=UsuarioOut)
def dar_de_baja(
    usuario_id: int, actor: Usuario = Depends(administrador), db: Session = Depends(get_db)
) -> UsuarioOut:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorNegocio(404, "No encontramos a esa persona.")
    _validar_cambio(db, actor, usuario, {"activo": False})
    usuario.activo = False
    db.flush()
    auditoria.registrar(
        db, accion="usuario_baja", usuario_id=actor.id, entidad="usuario", entidad_id=usuario.id
    )
    db.commit()
    return _salida(usuario)
