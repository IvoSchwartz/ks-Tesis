"""Administración de usuarios: alta, edición y baja, solo para Administrador/Socio."""
from tests.conftest import entrar

NUEVO = {
    "nombre": "Persona Nueva",
    "correo": "nueva@ejemplo.test",
    "contrasena": "una-clave-larga-1",
    "area": "impuestos",
    "rol": "empleado_impuestos",
}


def test_solo_el_socio_administra_usuarios(api, escenario):
    for clave in ("resp", "emp_a", "secretaria"):
        cabeceras = entrar(api, escenario[clave])
        assert api.get("/usuarios", headers=cabeceras).status_code == 403
        assert api.post("/usuarios", headers=cabeceras, json=NUEVO).status_code == 403
        assert api.put(f"/usuarios/{escenario['emp_b'].id}", headers=cabeceras, json={"nombre": "x"}).status_code == 403
        assert api.delete(f"/usuarios/{escenario['emp_b'].id}", headers=cabeceras).status_code == 403


def test_alta_listado_y_login_del_usuario_nuevo(api, escenario):
    cabeceras = entrar(api, escenario["socio"])
    r = api.post("/usuarios", headers=cabeceras, json=NUEVO)
    assert r.status_code == 201
    assert r.json()["rol_etiqueta"] == "Empleado de Impuestos"
    assert "contrasena" not in r.text and "hash" not in r.text
    assert "nueva@ejemplo.test" in [u["correo"] for u in api.get("/usuarios", headers=cabeceras).json()]
    ingreso = api.post("/auth/login", json={"correo": NUEVO["correo"], "contrasena": NUEVO["contrasena"]})
    assert ingreso.status_code == 200


def test_validaciones_del_alta(api, escenario):
    cabeceras = entrar(api, escenario["socio"])
    assert api.post("/usuarios", headers=cabeceras, json={**NUEVO, "contrasena": "corta"}).status_code == 422
    assert api.post("/usuarios", headers=cabeceras, json={**NUEVO, "correo": "no-es-un-correo"}).status_code == 422
    assert api.post("/usuarios", headers=cabeceras, json={**NUEVO, "rol": "senior"}).status_code == 422
    assert api.post("/usuarios", headers=cabeceras, json={**NUEVO, "area": "marketing"}).status_code == 422
    assert api.post("/usuarios", headers=cabeceras, json=NUEVO).status_code == 201
    repetido = api.post("/usuarios", headers=cabeceras, json={**NUEVO, "correo": "NUEVA@ejemplo.test"})
    assert repetido.status_code == 409


def test_edicion_cambia_nombre_y_contrasena(api, escenario):
    cabeceras = entrar(api, escenario["socio"])
    destino = escenario["emp_b"].id
    r = api.put(
        f"/usuarios/{destino}",
        headers=cabeceras,
        json={"nombre": "Nombre Cambiado", "contrasena": "otra-clave-larga-2"},
    )
    assert r.status_code == 200
    assert r.json()["nombre"] == "Nombre Cambiado"
    assert api.post("/auth/login", json={"correo": "emp.b@ejemplo.test", "contrasena": "otra-clave-larga-2"}).status_code == 200


def test_baja_desactiva_y_no_borra(api, db, escenario):
    from app.modelos import Usuario

    cabeceras = entrar(api, escenario["socio"])
    sin_clientes = escenario["secretaria"].id
    r = api.delete(f"/usuarios/{sin_clientes}", headers=cabeceras)
    assert r.status_code == 200 and r.json()["activo"] is False
    assert db.get(Usuario, sin_clientes) is not None  # sigue existiendo (queda el historial)
    assert api.post("/auth/login", json={"correo": "secre@ejemplo.test", "contrasena": "clave-de-prueba-123"}).status_code == 401


def test_no_se_da_de_baja_a_quien_tiene_clientes_asignados(api, escenario):
    cabeceras = entrar(api, escenario["socio"])
    r = api.delete(f"/usuarios/{escenario['emp_a'].id}", headers=cabeceras)
    assert r.status_code == 409
    assert "Reasignalos" in r.json()["detail"]
    # Tampoco se le puede cambiar el rol a uno que no puede ser responsable.
    r = api.put(f"/usuarios/{escenario['emp_a'].id}", headers=cabeceras, json={"rol": "secretaria"})
    assert r.status_code == 409


def test_el_socio_no_puede_quitarse_su_propio_acceso(api, escenario):
    cabeceras = entrar(api, escenario["socio"])
    mismo = escenario["socio"].id
    assert api.delete(f"/usuarios/{mismo}", headers=cabeceras).status_code == 409
    assert api.put(f"/usuarios/{mismo}", headers=cabeceras, json={"rol": "secretaria"}).status_code == 409
    assert api.put(f"/usuarios/{mismo}", headers=cabeceras, json={"activo": False}).status_code == 409


def test_usuario_inexistente(api, escenario):
    cabeceras = entrar(api, escenario["socio"])
    assert api.put("/usuarios/99999", headers=cabeceras, json={"nombre": "x"}).status_code == 404
    assert api.delete("/usuarios/99999", headers=cabeceras).status_code == 404
