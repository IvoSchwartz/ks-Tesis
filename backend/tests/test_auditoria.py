"""La auditoría es de solo inserción, está encadenada por hash y aguanta escrituras simultáneas."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app import auditoria
from app.db import SessionLocal
from app.modelos import Auditoria
from tests.conftest import entrar


def _registrar_varias(db, cantidad=5):
    for i in range(cantidad):
        auditoria.registrar(db, accion="prueba", usuario_id=1, entidad="x", entidad_id=i, detalle={"n": i})
    db.commit()


def test_la_cadena_se_arma_y_verifica(db):
    _registrar_varias(db)
    ok, mala, total = auditoria.verificar_cadena(db)
    assert (ok, mala, total) == (True, None, 5)
    filas = db.query(Auditoria).order_by(Auditoria.id).all()
    assert filas[0].hash_anterior == auditoria.HASH_INICIAL
    for anterior, actual in zip(filas, filas[1:]):
        assert actual.hash_anterior == anterior.hash_propio


def test_la_aplicacion_no_puede_modificar_ni_borrar_ni_vaciar(db):
    _registrar_varias(db, 2)
    for sentencia in (
        "UPDATE auditoria SET accion = 'cambiada'",
        "DELETE FROM auditoria",
        "TRUNCATE auditoria",
    ):
        with pytest.raises(DBAPIError):
            db.execute(text(sentencia))
        db.rollback()
    assert db.query(Auditoria).count() == 2


def test_ni_el_dueno_de_las_tablas_puede_modificar_o_borrar_gracias_al_trigger(motor_migrador, db):
    _registrar_varias(db, 2)
    for sentencia in (
        "UPDATE auditoria SET accion = 'cambiada'",
        "DELETE FROM auditoria",
        "TRUNCATE auditoria",
    ):
        with pytest.raises(DBAPIError) as error:
            with motor_migrador.begin() as con:
                con.execute(text(sentencia))
        assert "solo insercion" in str(error.value)


def test_la_verificacion_detecta_una_fila_alterada(db, motor_migrador):
    _registrar_varias(db)
    with motor_migrador.begin() as con:  # se desactiva el trigger a propósito para simular un ataque a la base
        con.execute(text("ALTER TABLE auditoria DISABLE TRIGGER USER"))
        con.execute(text("UPDATE auditoria SET accion = 'otra_cosa' WHERE id = 3"))
        con.execute(text("ALTER TABLE auditoria ENABLE TRIGGER USER"))
    ok, mala, _ = auditoria.verificar_cadena(db)
    assert ok is False
    assert mala == 3


def test_la_verificacion_detecta_una_fila_sacada_del_medio(db, motor_migrador):
    _registrar_varias(db)
    with motor_migrador.begin() as con:
        con.execute(text("ALTER TABLE auditoria DISABLE TRIGGER USER"))
        con.execute(text("DELETE FROM auditoria WHERE id = 2"))
        con.execute(text("ALTER TABLE auditoria ENABLE TRIGGER USER"))
    ok, mala, _ = auditoria.verificar_cadena(db)
    assert ok is False
    assert mala == 3  # la fila 3 ya no encaja con la anterior


def test_la_verificacion_detecta_un_detalle_alterado(db, motor_migrador):
    auditoria.registrar(db, accion="a", detalle={"cantidad": 1})
    auditoria.registrar(db, accion="b", detalle={"cantidad": 2})
    db.commit()
    with motor_migrador.begin() as con:
        con.execute(text("ALTER TABLE auditoria DISABLE TRIGGER USER"))
        con.execute(text("UPDATE auditoria SET detalle = '{\"cantidad\": 99}' WHERE id = 1"))
        con.execute(text("ALTER TABLE auditoria ENABLE TRIGGER USER"))
    assert auditoria.verificar_cadena(db)[:2] == (False, 1)


def test_escrituras_simultaneas_no_rompen_la_cadena():
    def escribir(n):
        with SessionLocal() as sesion:
            auditoria.registrar(sesion, accion="simultanea", usuario_id=n, detalle={"n": n})
            sesion.commit()

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(escribir, range(40)))

    with SessionLocal() as db:
        ok, mala, total = auditoria.verificar_cadena(db)
        assert (ok, mala, total) == (True, None, 40)
        filas = db.query(Auditoria).all()
        anteriores = [f.hash_anterior for f in filas]
        assert len(set(anteriores)) == 40  # nadie tomó el mismo "hash anterior"


def test_el_detalle_rechaza_datos_sensibles_y_decimales(db):
    for malo in (
        {"contrasena": "x"},
        {"cuit": "20999000013"},
        {"anidado": {"clave_fiscal": "x"}},
        {"lista": [{"token": "x"}]},
        {"importe": 1.5},
    ):
        with pytest.raises(ValueError):
            auditoria.registrar(db, accion="mala", detalle=malo)
    db.rollback()


def test_el_detalle_normal_se_acepta(db):
    auditoria.registrar(db, accion="ok", detalle={"cantidad": 3, "ids": [1, 2], "activo": True, "nota": None})
    db.commit()
    assert auditoria.verificar_cadena(db)[0] is True


def test_acciones_de_escritura_quedan_auditadas(api, db, escenario):
    cabeceras = entrar(api, escenario["socio"])
    r = api.post(
        "/usuarios",
        headers=cabeceras,
        json={
            "nombre": "Persona Nueva",
            "correo": "nueva@ejemplo.test",
            "contrasena": "una-clave-larga-1",
            "area": "impuestos",
            "rol": "empleado_impuestos",
        },
    )
    assert r.status_code == 201
    nuevo_id = r.json()["id"]
    api.put(f"/usuarios/{nuevo_id}", headers=cabeceras, json={"nombre": "Otro Nombre"})
    api.delete(f"/usuarios/{nuevo_id}", headers=cabeceras)
    api.put(f"/clientes/{escenario['c1'].id}", headers=cabeceras, json={"nombre": "Ejemplo Editado"})
    db.expire_all()
    acciones = [f.accion for f in db.query(Auditoria).order_by(Auditoria.id)]
    for esperada in ("login_ok", "usuario_crear", "usuario_editar", "usuario_baja", "cliente_editar"):
        assert esperada in acciones
    assert auditoria.verificar_cadena(db)[0] is True


def test_la_auditoria_no_guarda_contrasenas_ni_cuit(api, db, escenario):
    cabeceras = entrar(api, escenario["socio"])
    api.post(
        "/usuarios",
        headers=cabeceras,
        json={
            "nombre": "Persona Nueva",
            "correo": "nueva@ejemplo.test",
            "contrasena": "una-clave-larga-1",
            "area": "impuestos",
            "rol": "empleado_impuestos",
        },
    )
    api.get(f"/clientes/{escenario['c1'].id}", headers=cabeceras)
    volcado = str([(f.detalle, f.accion) for f in db.query(Auditoria)])
    assert "una-clave-larga-1" not in volcado
    assert "argon2" not in volcado
    for contribuyente in escenario["c1"].contribuyentes:
        assert contribuyente.cuit not in volcado
