"""Reasignaciones, historial y que un cliente nunca tenga dos responsables actuales."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import servicios
from app.constantes import Area, Rol
from app.db import SessionLocal
from app.modelos import Asignacion
from datetime import datetime, timezone
from tests.conftest import crear_usuario, entrar


def activas(db, cliente_id):
    db.expire_all()
    return list(db.scalars(select(Asignacion).where(Asignacion.cliente_id == cliente_id, Asignacion.fecha_fin.is_(None))))


def test_reasignar_cierra_la_anterior_y_abre_la_nueva(api, db, escenario):
    cabeceras = entrar(api, escenario["resp"])
    c1 = escenario["c1"].id
    r = api.post(f"/clientes/{c1}/reasignar", headers=cabeceras, json={"usuario_id": escenario["emp_b"].id})
    assert r.status_code == 200
    assert r.json()["responsable"]["id"] == escenario["emp_b"].id

    historial = list(db.scalars(select(Asignacion).where(Asignacion.cliente_id == c1).order_by(Asignacion.id)))
    assert len(historial) == 2
    assert historial[0].usuario_id == escenario["emp_a"].id and historial[0].fecha_fin is not None
    assert historial[1].usuario_id == escenario["emp_b"].id and historial[1].fecha_fin is None
    assert historial[0].fecha_fin <= historial[1].fecha_inicio

    # El empleado anterior ya no ve el cliente y el nuevo sí.
    assert api.get(f"/clientes/{c1}", headers=entrar(api, escenario["emp_a"])).status_code == 403
    assert api.get(f"/clientes/{c1}", headers=entrar(api, escenario["emp_b"])).status_code == 200


def test_no_se_pueden_tener_dos_responsables_actuales(db, escenario):
    db.add(Asignacion(cliente_id=escenario["c1"].id, usuario_id=escenario["emp_b"].id, fecha_inicio=datetime.now(timezone.utc)))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_dos_reasignaciones_simultaneas_dejan_un_solo_responsable(db, escenario):
    cliente_id = escenario["c1"].id
    candidatos = [escenario["emp_b"].id, escenario["resp"].id, escenario["emp_b"].id, escenario["resp"].id]

    def reasignar(usuario_id):
        with SessionLocal() as sesion:
            try:
                servicios.reasignar(sesion, cliente_id=cliente_id, nuevo_usuario_id=usuario_id, actor_id=None)
                sesion.commit()
                return "ok"
            except Exception as error:  # un "ya está asignado" también es un resultado válido
                sesion.rollback()
                return type(error).__name__

    with ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(reasignar, candidatos))

    assert "ok" in resultados
    assert len(activas(db, cliente_id)) == 1


def test_responsable_reasigna_solo_dentro_de_su_area(api, escenario):
    cabeceras = entrar(api, escenario["resp"])
    # Cliente de otra área: 403.
    r = api.post(
        f"/clientes/{escenario['c_lab'].id}/reasignar", headers=cabeceras, json={"usuario_id": escenario["emp_a"].id}
    )
    assert r.status_code == 403


def test_reasignar_a_una_persona_invalida(api, db, escenario):
    cabeceras = entrar(api, escenario["socio"])
    c1 = escenario["c1"].id
    baja = crear_usuario(db, "baja@ejemplo.test", Rol.EMPLEADO_IMPUESTOS, activo=False)
    db.commit()

    def reasignar(usuario_id):
        return api.post(f"/clientes/{c1}/reasignar", headers=cabeceras, json={"usuario_id": usuario_id})

    assert reasignar(baja.id).status_code == 422  # dada de baja
    assert reasignar(escenario["emp_laboral"].id).status_code == 422  # de otra área
    assert reasignar(escenario["secretaria"].id).status_code == 422  # su rol no puede ser responsable
    assert reasignar(escenario["socio"].id).status_code == 422
    assert reasignar(999999).status_code == 422  # no existe
    assert reasignar(escenario["emp_a"].id).status_code == 409  # ya es el responsable
    assert len(activas(db, c1)) == 1


def test_crear_cliente_con_varios_cuit_y_responsable(api, db, escenario):
    from app.cuit import cuit_inventado, formatear
    from app.constantes import TipoPersona

    cabeceras = entrar(api, escenario["resp"])
    c_a = cuit_inventado(501, TipoPersona.JURIDICA)
    c_b = cuit_inventado(502, TipoPersona.HUMANA)
    r = api.post(
        "/clientes",
        headers=cabeceras,
        json={
            "nombre": "Cliente Nuevo S.A.",
            "area": "impuestos",
            "responsable_id": escenario["emp_b"].id,
            "contribuyentes": [
                {"cuit": formatear(c_a), "nombre": "Nuevo S.A.", "tipo": "juridica", "condicion": "responsable_inscripto"},
                {"cuit": c_b, "nombre": "Socio Uno", "tipo": "humana", "condicion": "monotributista"},
            ],
        },
    )
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert len(cuerpo["contribuyentes"]) == 2
    assert cuerpo["responsable"]["id"] == escenario["emp_b"].id
    assert len(activas(db, cuerpo["id"])) == 1


def test_cuit_invalido_repetido_o_de_otro_tipo(api, escenario):
    from app.cuit import cuit_inventado
    from app.constantes import TipoPersona

    cabeceras = entrar(api, escenario["socio"])
    valido = cuit_inventado(601, TipoPersona.JURIDICA)

    def agregar(cuit, tipo="juridica"):
        return api.post(
            f"/clientes/{escenario['c1'].id}/contribuyentes",
            headers=cabeceras,
            json={"cuit": cuit, "nombre": "X", "tipo": tipo, "condicion": "otro"},
        )

    assert agregar(valido[:-1] + str((int(valido[-1]) + 1) % 10)).status_code == 422  # dígito verificador
    assert agregar(valido, tipo="humana").status_code == 422  # prefijo de persona jurídica, tipo humana
    assert agregar(valido).status_code == 201
    assert agregar(valido).status_code == 409  # ya existe


def test_responsable_de_area_no_crea_clientes_de_otra_area(api, escenario):
    r = api.post(
        "/clientes",
        headers=entrar(api, escenario["resp"]),
        json={"nombre": "X", "area": "laboral", "responsable_id": escenario["resp_laboral"].id},
    )
    assert r.status_code == 403
