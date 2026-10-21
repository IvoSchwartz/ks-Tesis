"""Reglas de negocio de clientes, contribuyentes y asignaciones.

Cada función deja la auditoría como último paso antes de que el llamador haga commit.
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import auditoria, cuit as cuit_util
from app.constantes import ETIQUETA_AREA, ROLES_RESPONSABLES, Area
from app.errores import ErrorNegocio
from app.esquemas import ClienteFichaOut, ClienteIn, ClienteListaOut, ContribuyenteIn
from app.esquemas import ContribuyenteFichaOut, ContribuyenteListaOut, PersonaOut
from app.modelos import Asignacion, Cliente, Contribuyente, Usuario
from app.permisos import Alcance, permisos_de


def responsables_actuales(db: Session, cliente_ids: list[int]) -> dict[int, PersonaOut]:
    """Responsable actual de cada cliente: la asignación sin fecha de fin."""
    if not cliente_ids:
        return {}
    filas = db.execute(
        select(Asignacion.cliente_id, Usuario.id, Usuario.nombre)
        .join(Usuario, Usuario.id == Asignacion.usuario_id)
        .where(Asignacion.fecha_fin.is_(None), Asignacion.cliente_id.in_(cliente_ids))
    ).all()
    return {cid: PersonaOut(id=uid, nombre=nombre) for cid, uid, nombre in filas}


def a_lista(cliente: Cliente, responsable: PersonaOut | None) -> ClienteListaOut:
    return ClienteListaOut(
        id=cliente.id,
        nombre=cliente.nombre,
        area=cliente.area,
        area_etiqueta=ETIQUETA_AREA[Area(cliente.area)],
        activo=cliente.activo,
        responsable=responsable,
        contribuyentes=[
            ContribuyenteListaOut(
                id=c.id,
                cuit_enmascarado=cuit_util.enmascarar(c.cuit),
                nombre=c.nombre,
                tipo=c.tipo,
                condicion=c.condicion,
            )
            for c in cliente.contribuyentes
        ],
    )


def a_ficha(cliente: Cliente, responsable: PersonaOut | None) -> ClienteFichaOut:
    return ClienteFichaOut(
        id=cliente.id,
        nombre=cliente.nombre,
        area=cliente.area,
        area_etiqueta=ETIQUETA_AREA[Area(cliente.area)],
        activo=cliente.activo,
        responsable=responsable,
        contribuyentes=[
            ContribuyenteFichaOut(
                id=c.id,
                cuit=cuit_util.formatear(c.cuit),
                nombre=c.nombre,
                tipo=c.tipo,
                condicion=c.condicion,
            )
            for c in cliente.contribuyentes
        ],
    )


def validar_responsable(db: Session, usuario_id: int, area_cliente: str) -> Usuario:
    persona = db.get(Usuario, usuario_id)
    if persona is None or not persona.activo:
        raise ErrorNegocio(422, "La persona elegida no existe o está dada de baja.")
    if persona.rol not in ROLES_RESPONSABLES:
        raise ErrorNegocio(422, "Esa persona no puede ser responsable de clientes.")
    if persona.area != area_cliente:
        raise ErrorNegocio(422, "La persona elegida es de otra área.")
    return persona


def _nuevo_contribuyente(db: Session, cliente_id: int, datos: ContribuyenteIn) -> Contribuyente:
    numero = cuit_util.normalizar(datos.cuit)
    if not cuit_util.es_valido(numero):
        raise ErrorNegocio(422, "El CUIT no es válido: revisá los números.")
    if not cuit_util.tipo_coincide(numero, datos.tipo):
        raise ErrorNegocio(422, "El CUIT no coincide con el tipo de persona elegido.")
    if db.scalar(select(Contribuyente.id).where(Contribuyente.cuit == numero)) is not None:
        raise ErrorNegocio(409, "Ya existe un contribuyente con ese CUIT.")
    contribuyente = Contribuyente(
        cuit=numero,
        nombre=datos.nombre.strip(),
        tipo=datos.tipo.value,
        condicion=datos.condicion.value,
        cliente_id=cliente_id,
    )
    db.add(contribuyente)
    return contribuyente


def crear_cliente(db: Session, actor: Usuario, datos: ClienteIn) -> Cliente:
    permisos = permisos_de(actor.rol, actor.area)
    if permisos.alcance == Alcance.AREA and datos.area.value != actor.area:
        raise ErrorNegocio(403, "Solo podés crear clientes de tu área.")
    validar_responsable(db, datos.responsable_id, datos.area.value)

    cliente = Cliente(nombre=datos.nombre.strip(), area=datos.area.value)
    db.add(cliente)
    db.flush()
    db.add(
        Asignacion(
            cliente_id=cliente.id,
            usuario_id=datos.responsable_id,
            fecha_inicio=datetime.now(timezone.utc),
        )
    )
    for c in datos.contribuyentes:
        _nuevo_contribuyente(db, cliente.id, c)
    db.flush()
    db.refresh(cliente, attribute_names=["contribuyentes"])

    auditoria.registrar(
        db,
        accion="cliente_crear",
        usuario_id=actor.id,
        entidad="cliente",
        entidad_id=cliente.id,
        cliente_id=cliente.id,
        detalle={"responsable_id": datos.responsable_id, "cantidad_contribuyentes": len(datos.contribuyentes)},
    )
    return cliente


def agregar_contribuyente(db: Session, actor: Usuario, cliente: Cliente, datos: ContribuyenteIn) -> Contribuyente:
    contribuyente = _nuevo_contribuyente(db, cliente.id, datos)
    db.flush()
    auditoria.registrar(
        db,
        accion="contribuyente_crear",
        usuario_id=actor.id,
        entidad="contribuyente",
        entidad_id=contribuyente.id,
        cliente_id=cliente.id,
    )
    return contribuyente


def reasignar(db: Session, *, cliente_id: int, nuevo_usuario_id: int, actor_id: int | None) -> Asignacion:
    """Cierra la asignación vigente y abre la nueva, en la misma transacción.

    Se bloquea la fila del cliente: dos reasignaciones simultáneas se ejecutan una después de la otra, y el
    índice único parcial de la base impide, en cualquier caso, dos responsables actuales.
    """
    cliente = db.execute(select(Cliente).where(Cliente.id == cliente_id).with_for_update()).scalar_one()
    nuevo = validar_responsable(db, nuevo_usuario_id, cliente.area)

    ahora = datetime.now(timezone.utc)  # después del bloqueo, para que las fechas queden en orden
    actual = db.scalar(
        select(Asignacion).where(Asignacion.cliente_id == cliente.id, Asignacion.fecha_fin.is_(None))
    )
    if actual is not None and actual.usuario_id == nuevo.id:
        raise ErrorNegocio(409, "El cliente ya está asignado a esa persona.")

    anterior_id = None
    if actual is not None:
        anterior_id = actual.usuario_id
        actual.fecha_fin = ahora
        db.flush()
    nueva = Asignacion(cliente_id=cliente.id, usuario_id=nuevo.id, fecha_inicio=ahora)
    db.add(nueva)
    db.flush()

    auditoria.registrar(
        db,
        accion="cliente_reasignar",
        usuario_id=actor_id,
        entidad="cliente",
        entidad_id=cliente.id,
        cliente_id=cliente.id,
        detalle={"de_usuario_id": anterior_id, "a_usuario_id": nuevo.id},
    )
    return nueva


def clientes_asignados_activos(db: Session, usuario_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Asignacion)
        .where(Asignacion.usuario_id == usuario_id, Asignacion.fecha_fin.is_(None))
    ) or 0


def puede_ser_responsable(rol: str) -> bool:
    return rol in ROLES_RESPONSABLES
