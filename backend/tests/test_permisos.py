"""Lo más importante del paso 1: que nadie vea clientes ajenos, llamando a la API directamente."""
from sqlalchemy import select

from app.modelos import Auditoria
from tests.conftest import entrar


def ids(respuesta):
    return {c["id"] for c in respuesta.json()}


# --- Empleado de Impuestos: solo sus clientes asignados -------------------------------------------------

def test_empleado_solo_lista_sus_clientes(api, escenario):
    r = api.get("/clientes", headers=entrar(api, escenario["emp_a"]))
    assert r.status_code == 200
    assert ids(r) == {escenario["c1"].id}


def test_empleado_con_id_de_cliente_ajeno_recibe_403_y_no_los_datos(api, escenario):
    cabeceras = entrar(api, escenario["emp_a"])
    ajeno = escenario["c2"].id
    for r in (
        api.get(f"/clientes/{ajeno}", headers=cabeceras),
        api.get(f"/clientes/{ajeno}/contribuyentes", headers=cabeceras),
    ):
        assert r.status_code == 403
        assert "Muestra" not in r.text  # no se filtra ningún dato del cliente
        assert "cuit" not in r.text.lower()


def test_empleado_no_puede_editar_ni_reasignar_ni_agregar_cuit_en_cliente_ajeno(api, escenario):
    cabeceras = entrar(api, escenario["emp_a"])
    ajeno = escenario["c2"].id
    assert api.put(f"/clientes/{ajeno}", headers=cabeceras, json={"nombre": "Hackeado"}).status_code == 403
    assert (
        api.post(
            f"/clientes/{ajeno}/reasignar", headers=cabeceras, json={"usuario_id": escenario["emp_a"].id}
        ).status_code
        == 403
    )
    assert (
        api.post(
            f"/clientes/{ajeno}/contribuyentes",
            headers=cabeceras,
            json={"cuit": "20999000013", "nombre": "x", "tipo": "humana", "condicion": "otro"},
        ).status_code
        == 403
    )


def test_empleado_tampoco_puede_editar_ni_reasignar_el_propio_cliente(api, escenario):
    """Ver no es administrar: sus capacidades son solo de lectura."""
    cabeceras = entrar(api, escenario["emp_a"])
    propio = escenario["c1"].id
    assert api.put(f"/clientes/{propio}", headers=cabeceras, json={"nombre": "Otro"}).status_code == 403
    assert (
        api.post(
            f"/clientes/{propio}/reasignar", headers=cabeceras, json={"usuario_id": escenario["emp_b"].id}
        ).status_code
        == 403
    )


def test_id_inexistente_tambien_da_403_para_quien_no_ve_todo(api, escenario):
    """Así no se puede averiguar qué IDs existen."""
    assert api.get("/clientes/99999", headers=entrar(api, escenario["emp_a"])).status_code == 403
    assert api.get("/clientes/99999", headers=entrar(api, escenario["socio"])).status_code == 404


def test_empleado_no_entra_a_usuarios(api, escenario):
    assert api.get("/usuarios", headers=entrar(api, escenario["emp_a"])).status_code == 403


# --- Otras áreas -----------------------------------------------------------------------------------------

def test_empleado_de_otra_area_no_ve_clientes_de_impuestos(api, escenario):
    cabeceras = entrar(api, escenario["emp_laboral"])
    assert api.get("/clientes", headers=cabeceras).status_code == 403
    assert api.get(f"/clientes/{escenario['c1'].id}", headers=cabeceras).status_code == 403


def test_responsable_de_impuestos_ve_los_de_su_area_y_no_los_de_otra(api, escenario):
    cabeceras = entrar(api, escenario["resp"])
    r = api.get("/clientes", headers=cabeceras)
    assert ids(r) == {escenario["c1"].id, escenario["c2"].id}
    assert api.get(f"/clientes/{escenario['c1'].id}", headers=cabeceras).status_code == 200
    assert api.get(f"/clientes/{escenario['c_lab'].id}", headers=cabeceras).status_code == 403


def test_responsable_de_otra_area_no_ve_clientes_de_impuestos(api, escenario):
    cabeceras = entrar(api, escenario["resp_laboral"])
    assert ids(api.get("/clientes", headers=cabeceras)) == {escenario["c_lab"].id}
    assert api.get(f"/clientes/{escenario['c1'].id}", headers=cabeceras).status_code == 403


# --- Socio y Secretaría ----------------------------------------------------------------------------------

def test_socio_ve_todo(api, escenario):
    cabeceras = entrar(api, escenario["socio"])
    assert ids(api.get("/clientes", headers=cabeceras)) == {
        escenario["c1"].id,
        escenario["c2"].id,
        escenario["c_lab"].id,
    }


def test_secretaria_ve_la_lista_pero_no_administra(api, escenario):
    cabeceras = entrar(api, escenario["secretaria"])
    assert len(api.get("/clientes", headers=cabeceras).json()) == 3
    assert api.get("/usuarios", headers=cabeceras).status_code == 403
    assert api.put(f"/clientes/{escenario['c1'].id}", headers=cabeceras, json={"nombre": "x"}).status_code == 403
    assert (
        api.post(
            f"/clientes/{escenario['c1'].id}/reasignar",
            headers=cabeceras,
            json={"usuario_id": escenario["emp_b"].id},
        ).status_code
        == 403
    )
    assert (
        api.post(
            "/clientes",
            headers=cabeceras,
            json={"nombre": "Nuevo", "area": "impuestos", "responsable_id": escenario["emp_a"].id},
        ).status_code
        == 403
    )


# --- CUIT y datos sensibles ------------------------------------------------------------------------------

def test_la_lista_nunca_trae_el_cuit_completo(api, db, escenario):
    from app.modelos import Contribuyente

    r = api.get("/clientes", headers=entrar(api, escenario["socio"]))
    cuits = [c.cuit for c in db.scalars(select(Contribuyente))]
    assert cuits
    for cuit in cuits:
        assert cuit not in r.text
        assert cuit[2:10] not in r.text
    assert "•" in r.text


def test_la_ficha_si_trae_los_cuit_completos(api, db, escenario):
    r = api.get(f"/clientes/{escenario['c1'].id}", headers=entrar(api, escenario["emp_a"]))
    assert r.status_code == 200
    cuerpo = r.json()
    assert len(cuerpo["contribuyentes"]) == 3
    assert all(len(c["cuit"]) == 13 for c in cuerpo["contribuyentes"])  # 30-99912345-6
    assert cuerpo["responsable"]["id"] == escenario["emp_a"].id


def test_busqueda_por_nombre(api, escenario):
    cabeceras = entrar(api, escenario["socio"])
    assert ids(api.get("/clientes?q=ejemplo", headers=cabeceras)) == {escenario["c1"].id}
    assert api.get("/clientes?q=zzz", headers=cabeceras).json() == []
    # Los comodines se tratan como texto común.
    assert api.get("/clientes?q=%25", headers=cabeceras).json() == []


# --- Auditoría de accesos --------------------------------------------------------------------------------

def test_accesos_a_clientes_quedan_en_la_auditoria(api, db, escenario):
    cabeceras = entrar(api, escenario["emp_a"])
    api.get("/clientes", headers=cabeceras)
    api.get(f"/clientes/{escenario['c1'].id}", headers=cabeceras)
    api.get(f"/clientes/{escenario['c2'].id}", headers=cabeceras)  # denegado
    db.expire_all()
    filas = list(db.scalars(select(Auditoria).where(Auditoria.usuario_id == escenario["emp_a"].id)))
    acciones = [f.accion for f in filas]
    assert acciones.count("cliente_listar") == 1  # un evento por consulta de lista, no uno por cliente
    assert acciones.count("cliente_ver") == 1
    assert acciones.count("acceso_denegado") == 1
    denegado = next(f for f in filas if f.accion == "acceso_denegado")
    assert denegado.cliente_id == escenario["c2"].id
    ver = next(f for f in filas if f.accion == "cliente_ver")
    assert ver.cliente_id == escenario["c1"].id
