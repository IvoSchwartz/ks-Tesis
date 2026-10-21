from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select, text

from app.config import get_settings
from app.constantes import Rol
from app.modelos import Auditoria, Usuario
from tests.conftest import CLAVE_USUARIOS, crear_usuario, entrar


def _login(api, correo, clave):
    return api.post("/auth/login", json={"correo": correo, "contrasena": clave})


def test_login_correcto_y_token_de_8_horas(api, db):
    u = crear_usuario(db, "uno@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    db.commit()
    r = _login(api, "UNO@ejemplo.test", CLAVE_USUARIOS)  # el correo no distingue mayúsculas
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["expira_en_segundos"] == 8 * 3600
    datos = jwt.decode(cuerpo["access_token"], get_settings().jwt_secret, algorithms=["HS256"])
    assert datos["exp"] - datos["iat"] == 8 * 3600
    assert datos["sub"] == str(u.id)


def test_contrasenas_se_guardan_con_argon2(db):
    u = crear_usuario(db, "uno@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    assert u.hash_contrasena.startswith("$argon2id$")
    assert CLAVE_USUARIOS not in u.hash_contrasena


def test_clave_incorrecta_y_correo_inexistente_dan_el_mismo_error(api, db):
    crear_usuario(db, "uno@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    db.commit()
    a = _login(api, "uno@ejemplo.test", "mala")
    b = _login(api, "nadie@ejemplo.test", "mala")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_usuario_dado_de_baja_no_ingresa(api, db):
    crear_usuario(db, "baja@ejemplo.test", Rol.EMPLEADO_IMPUESTOS, activo=False)
    db.commit()
    assert _login(api, "baja@ejemplo.test", CLAVE_USUARIOS).status_code == 401


def test_bloqueo_tras_5_intentos_fallidos(api, db, motor_migrador):
    crear_usuario(db, "uno@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    db.commit()
    for _ in range(5):
        assert _login(api, "uno@ejemplo.test", "mala").status_code == 401
    # Ahora está bloqueado: ni siquiera la clave correcta entra.
    assert _login(api, "uno@ejemplo.test", CLAVE_USUARIOS).status_code == 429

    # Pasado el tiempo de bloqueo vuelve a funcionar.
    with motor_migrador.begin() as con:
        con.execute(text("UPDATE usuario SET bloqueado_hasta = now() - interval '1 minute'"))
    assert _login(api, "uno@ejemplo.test", CLAVE_USUARIOS).status_code == 200


def test_login_exitoso_reinicia_el_contador(api, db):
    crear_usuario(db, "uno@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    db.commit()
    for _ in range(4):
        _login(api, "uno@ejemplo.test", "mala")
    assert _login(api, "uno@ejemplo.test", CLAVE_USUARIOS).status_code == 200
    for _ in range(4):
        assert _login(api, "uno@ejemplo.test", "mala").status_code == 401
    assert _login(api, "uno@ejemplo.test", CLAVE_USUARIOS).status_code == 200


def test_el_login_queda_en_la_auditoria(api, db):
    u = crear_usuario(db, "uno@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    db.commit()
    _login(api, "uno@ejemplo.test", "mala")
    _login(api, "nadie@ejemplo.test", "mala")
    _login(api, "uno@ejemplo.test", CLAVE_USUARIOS)
    db.expire_all()
    acciones = [(f.accion, f.usuario_id) for f in db.scalars(select(Auditoria).order_by(Auditoria.id))]
    assert acciones == [("login_fallido", u.id), ("login_fallido", None), ("login_ok", u.id)]


def test_sin_token_o_con_token_invalido_es_401(api):
    assert api.get("/me").status_code == 401
    assert api.get("/me", headers={"Authorization": "Bearer basura"}).status_code == 401
    assert api.get("/clientes").status_code == 401


def test_token_vencido_es_401(api, db):
    u = crear_usuario(db, "uno@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    db.commit()
    ayer = datetime.now(timezone.utc) - timedelta(days=1)
    vencido = jwt.encode(
        {"sub": str(u.id), "iat": ayer, "exp": ayer + timedelta(hours=8)},
        get_settings().jwt_secret,
        algorithm="HS256",
    )
    assert api.get("/me", headers={"Authorization": f"Bearer {vencido}"}).status_code == 401


def test_token_firmado_con_otra_clave_es_401(api, db):
    u = crear_usuario(db, "uno@ejemplo.test", Rol.EMPLEADO_IMPUESTOS)
    db.commit()
    falso = jwt.encode({"sub": str(u.id)}, "otra-clave-distinta-de-32-caracteres-o-mas-xx", algorithm="HS256")
    assert api.get("/me", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_al_dar_de_baja_el_token_deja_de_valer_al_instante(api, db, escenario):
    cabeceras = entrar(api, escenario["emp_a"])
    assert api.get("/me", headers=cabeceras).status_code == 200
    usuario = db.get(Usuario, escenario["emp_a"].id)
    usuario.activo = False
    db.commit()
    assert api.get("/me", headers=cabeceras).status_code == 401


def test_me_devuelve_el_menu_segun_el_rol(api, escenario):
    socio = api.get("/me", headers=entrar(api, escenario["socio"])).json()
    assert [i["clave"] for i in socio["menu"]] == ["clientes", "usuarios"]
    assert socio["rol_etiqueta"] == "Administrador/Socio"

    resp = api.get("/me", headers=entrar(api, escenario["resp"])).json()
    assert [i["clave"] for i in resp["menu"]] == ["clientes"]
    assert resp["rol_etiqueta"] == "Responsable de área"

    emp = api.get("/me", headers=entrar(api, escenario["emp_a"])).json()
    assert [i["clave"] for i in emp["menu"]] == ["clientes"]
    assert emp["alcance"] == "asignados"
    assert "hash_contrasena" not in emp

    # Un Empleado de Impuestos de otra área no tiene menú.
    lab = api.get("/me", headers=entrar(api, escenario["emp_laboral"])).json()
    assert lab["menu"] == []
    assert lab["alcance"] == "ninguno"
