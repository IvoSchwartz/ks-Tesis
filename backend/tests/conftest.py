"""Pruebas contra un PostgreSQL REAL (la auditoría depende de roles, triggers y bloqueos propios de Postgres).

Variable opcional: TEST_ADMIN_URL, conexión de un superusuario a la base "postgres". Por defecto:
    postgresql+psycopg://ks_migrador:ks_test_migrador@localhost:5432/postgres
Se crea (y se recrea en cada corrida) la base "ks_test". Todos los datos son inventados.
"""
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ADMIN_URL = os.environ.get(
    "TEST_ADMIN_URL", "postgresql+psycopg://ks_migrador:ks_test_migrador@localhost:5432/postgres"
)
NOMBRE_BD = "ks_test"
CLAVE_APP = "ks_test_app_clave"

_url_migrador = make_url(ADMIN_URL).set(database=NOMBRE_BD)
_url_app = _url_migrador.set(username="ks_app", password=CLAVE_APP)

# Las variables se definen ANTES de importar la aplicación.
os.environ["ENTORNO"] = "pruebas"
os.environ["DATABASE_URL_MIGRADOR"] = _url_migrador.render_as_string(hide_password=False)
os.environ["DATABASE_URL_APP"] = _url_app.render_as_string(hide_password=False)
os.environ["APP_DB_PASSWORD"] = CLAVE_APP
os.environ["JWT_SECRET"] = "clave-de-pruebas-que-no-es-un-secreto-real-0123456789"
os.environ["JWT_HORAS"] = "8"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.constantes import Area, Condicion, Rol, TipoPersona  # noqa: E402
from app.cuit import cuit_inventado  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.modelos import Asignacion, Cliente, Contribuyente, Usuario  # noqa: E402
from app.seguridad import hashear  # noqa: E402

RAIZ_BACKEND = Path(__file__).resolve().parents[1]
CLAVE_USUARIOS = "clave-de-prueba-123"
# Se hashea una sola vez: argon2 es lento a propósito y no hace falta repetirlo en cada prueba.
HASH_USUARIOS = hashear(CLAVE_USUARIOS)


@pytest.fixture(scope="session", autouse=True)
def base_de_datos():
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as con:
        con.execute(text(f'DROP DATABASE IF EXISTS "{NOMBRE_BD}" WITH (FORCE)'))
        con.execute(text(f'CREATE DATABASE "{NOMBRE_BD}"'))
    admin.dispose()
    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ_BACKEND / "alembic"))
    command.upgrade(config, "head")
    yield


@pytest.fixture
def motor_migrador():
    """Conexión del dueño de las tablas: solo para preparar y para provocar casos que la app no puede."""
    motor = create_engine(str(_url_migrador.render_as_string(hide_password=False)))
    yield motor
    motor.dispose()


@pytest.fixture(autouse=True)
def limpiar(motor_migrador):
    with motor_migrador.begin() as con:
        con.execute(text("ALTER TABLE auditoria DISABLE TRIGGER USER"))
        con.execute(
            text(
                "TRUNCATE auditoria, asignacion, contribuyente, cliente, estado, impuesto, usuario "
                "RESTART IDENTITY CASCADE"
            )
        )
        con.execute(text("ALTER TABLE auditoria ENABLE TRIGGER USER"))
    yield


@pytest.fixture
def db():
    with SessionLocal() as sesion:
        yield sesion


@pytest.fixture
def api():
    return TestClient(app)


def crear_usuario(db, correo, rol, area=Area.IMPUESTOS, nombre=None, activo=True) -> Usuario:
    usuario = Usuario(
        nombre=nombre or correo.split("@")[0],
        correo=correo,
        hash_contrasena=HASH_USUARIOS,
        area=Area(area).value,
        rol=Rol(rol).value,
        activo=activo,
    )
    db.add(usuario)
    db.flush()
    return usuario


_contador_cuit = [0]


def crear_cliente(db, nombre, responsable, area=Area.IMPUESTOS, cantidad_cuit=2) -> Cliente:
    from datetime import datetime, timezone

    cliente = Cliente(nombre=nombre, area=Area(area).value)
    db.add(cliente)
    db.flush()
    db.add(
        Asignacion(
            cliente_id=cliente.id, usuario_id=responsable.id, fecha_inicio=datetime.now(timezone.utc)
        )
    )
    for _ in range(cantidad_cuit):
        _contador_cuit[0] += 1
        db.add(
            Contribuyente(
                cuit=cuit_inventado(_contador_cuit[0], TipoPersona.JURIDICA),
                nombre=f"{nombre} contribuyente {_contador_cuit[0]}",
                tipo=TipoPersona.JURIDICA.value,
                condicion=Condicion.RESPONSABLE_INSCRIPTO.value,
                cliente_id=cliente.id,
            )
        )
    db.flush()
    return cliente


@pytest.fixture
def escenario(db):
    """Personas y clientes inventados para probar permisos.

    Impuestos: socio, resp (Responsable de área), emp_a, emp_b, secretaria.
    Otras áreas: emp_laboral (rol Empleado de Impuestos pero del área Laboral) y resp_laboral.
    Clientes: c1 (de emp_a), c2 (de emp_b), c_lab (área Laboral, de resp_laboral).
    """
    socio = crear_usuario(db, "socio@ejemplo.test", Rol.ADMIN_SOCIO)
    resp = crear_usuario(db, "resp@ejemplo.test", Rol.RESPONSABLE_AREA)
    emp_a = crear_usuario(db, "emp.a@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    emp_b = crear_usuario(db, "emp.b@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    secretaria = crear_usuario(db, "secre@ejemplo.test", Rol.SECRETARIA, area=Area.SECRETARIA)
    emp_laboral = crear_usuario(db, "emp.lab@ejemplo.test", Rol.EMPLEADO_IMPUESTOS, area=Area.LABORAL)
    resp_laboral = crear_usuario(db, "resp.lab@ejemplo.test", Rol.RESPONSABLE_AREA, area=Area.LABORAL)
    c1 = crear_cliente(db, "Ejemplo S.A.", emp_a, cantidad_cuit=3)
    c2 = crear_cliente(db, "Muestra S.R.L.", emp_b, cantidad_cuit=1)
    c_lab = crear_cliente(db, "Cliente Laboral S.A.", resp_laboral, area=Area.LABORAL, cantidad_cuit=1)
    db.commit()
    return {
        "socio": socio, "resp": resp, "emp_a": emp_a, "emp_b": emp_b, "secretaria": secretaria,
        "emp_laboral": emp_laboral, "resp_laboral": resp_laboral,
        "c1": c1, "c2": c2, "c_lab": c_lab,
    }


def entrar(api, usuario) -> dict:
    """Inicia sesión y devuelve los encabezados con el token."""
    r = api.post("/auth/login", json={"correo": usuario.correo, "contrasena": CLAVE_USUARIOS})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
