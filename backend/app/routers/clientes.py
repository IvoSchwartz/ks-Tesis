"""Clientes y sus contribuyentes (CUIT). Todo acceso pasa por el filtro de permisos del servidor."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload

from app import auditoria, servicios
from app.db import get_db
from app.dependencias import clientes_visibles, cliente_autorizado, requiere
from app.esquemas import (
    ClienteFichaOut,
    ClienteIn,
    ClienteListaOut,
    ClientePut,
    ContribuyenteFichaOut,
    ContribuyenteIn,
    ReasignarIn,
)
from app.modelos import Cliente, Usuario
from app import cuit as cuit_util
from app.permisos import Capacidad

router = APIRouter(prefix="/clientes", tags=["clientes"])


def _ficha(db: Session, cliente: Cliente) -> ClienteFichaOut:
    responsable = servicios.responsables_actuales(db, [cliente.id]).get(cliente.id)
    return servicios.a_ficha(cliente, responsable)


@router.get("", response_model=list[ClienteListaOut])
def listar(
    q: str | None = Query(default=None, max_length=80),
    usuario: Usuario = Depends(requiere(Capacidad.VER_CLIENTES)),
    db: Session = Depends(get_db),
) -> list[ClienteListaOut]:
    consulta = clientes_visibles(usuario).options(selectinload(Cliente.contribuyentes)).order_by(Cliente.nombre)
    if q and q.strip():
        consulta = consulta.where(Cliente.nombre.icontains(q.strip(), autoescape=True))
    clientes = list(db.scalars(consulta))
    responsables = servicios.responsables_actuales(db, [c.id for c in clientes])

    auditoria.registrar(
        db,
        accion="cliente_listar",
        usuario_id=usuario.id,
        entidad="cliente",
        detalle={"cantidad": len(clientes), "con_busqueda": bool(q and q.strip())},
    )
    db.commit()
    return [servicios.a_lista(c, responsables.get(c.id)) for c in clientes]


@router.post("", response_model=ClienteFichaOut, status_code=201)
def crear(
    datos: ClienteIn,
    actor: Usuario = Depends(requiere(Capacidad.CREAR_CLIENTES)),
    db: Session = Depends(get_db),
) -> ClienteFichaOut:
    cliente = servicios.crear_cliente(db, actor, datos)
    salida = _ficha(db, cliente)
    db.commit()
    return salida


@router.get("/{cliente_id}", response_model=ClienteFichaOut)
def ficha(
    cliente: Cliente = Depends(cliente_autorizado),
    usuario: Usuario = Depends(requiere(Capacidad.VER_CLIENTES)),
    db: Session = Depends(get_db),
) -> ClienteFichaOut:
    salida = _ficha(db, cliente)
    auditoria.registrar(
        db,
        accion="cliente_ver",
        usuario_id=usuario.id,
        entidad="cliente",
        entidad_id=cliente.id,
        cliente_id=cliente.id,
    )
    db.commit()
    return salida


@router.put("/{cliente_id}", response_model=ClienteFichaOut)
def editar(
    datos: ClientePut,
    cliente: Cliente = Depends(cliente_autorizado),
    actor: Usuario = Depends(requiere(Capacidad.EDITAR_CLIENTES)),
    db: Session = Depends(get_db),
) -> ClienteFichaOut:
    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    for campo, valor in cambios.items():
        setattr(cliente, campo, valor.strip() if isinstance(valor, str) else valor)
    db.flush()
    salida = _ficha(db, cliente)
    auditoria.registrar(
        db,
        accion="cliente_editar",
        usuario_id=actor.id,
        entidad="cliente",
        entidad_id=cliente.id,
        cliente_id=cliente.id,
        detalle={"campos": sorted(cambios.keys())},
    )
    db.commit()
    return salida


@router.get("/{cliente_id}/contribuyentes", response_model=list[ContribuyenteFichaOut])
def contribuyentes(
    cliente: Cliente = Depends(cliente_autorizado),
    usuario: Usuario = Depends(requiere(Capacidad.VER_CLIENTES)),
    db: Session = Depends(get_db),
) -> list[ContribuyenteFichaOut]:
    salida = [
        ContribuyenteFichaOut(
            id=c.id, cuit=cuit_util.formatear(c.cuit), nombre=c.nombre, tipo=c.tipo, condicion=c.condicion
        )
        for c in cliente.contribuyentes
    ]
    auditoria.registrar(
        db,
        accion="contribuyentes_listar",
        usuario_id=usuario.id,
        entidad="cliente",
        entidad_id=cliente.id,
        cliente_id=cliente.id,
        detalle={"cantidad": len(salida)},
    )
    db.commit()
    return salida


@router.post("/{cliente_id}/contribuyentes", response_model=ClienteFichaOut, status_code=201)
def agregar_contribuyente(
    datos: ContribuyenteIn,
    cliente: Cliente = Depends(cliente_autorizado),
    actor: Usuario = Depends(requiere(Capacidad.EDITAR_CLIENTES)),
    db: Session = Depends(get_db),
) -> ClienteFichaOut:
    servicios.agregar_contribuyente(db, actor, cliente, datos)
    db.refresh(cliente, attribute_names=["contribuyentes"])
    salida = _ficha(db, cliente)
    db.commit()
    return salida


@router.post("/{cliente_id}/reasignar", response_model=ClienteFichaOut)
def reasignar(
    datos: ReasignarIn,
    cliente: Cliente = Depends(cliente_autorizado),
    actor: Usuario = Depends(requiere(Capacidad.REASIGNAR_CLIENTES)),
    db: Session = Depends(get_db),
) -> ClienteFichaOut:
    servicios.reasignar(db, cliente_id=cliente.id, nuevo_usuario_id=datos.usuario_id, actor_id=actor.id)
    salida = _ficha(db, cliente)
    db.commit()
    return salida
