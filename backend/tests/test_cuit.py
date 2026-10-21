from app import cuit
from app.constantes import TipoPersona


def test_cuit_inventado_es_valido_y_reconocible():
    for numero in (0, 1, 7, 12345, 80000):
        for tipo in (TipoPersona.JURIDICA, TipoPersona.HUMANA):
            c = cuit.cuit_inventado(numero, tipo)
            assert cuit.es_valido(c)
            assert c[2:5] == "999"  # los 8 dígitos centrales empiezan con 999
            assert cuit.tipo_coincide(c, tipo)


def test_numeros_distintos_dan_cuit_distintos():
    generados = {cuit.cuit_inventado(n, TipoPersona.JURIDICA) for n in range(300)}
    assert len(generados) == 300


def test_cuit_invalidos():
    valido = cuit.cuit_inventado(5, TipoPersona.JURIDICA)
    digito_malo = str((int(valido[-1]) + 1) % 10)
    assert not cuit.es_valido(valido[:-1] + digito_malo)
    assert not cuit.es_valido("123")
    assert not cuit.es_valido("abcdefghijk")
    assert not cuit.es_valido("99" + valido[2:])  # prefijo que no existe


def test_tipo_no_coincide():
    juridica = cuit.cuit_inventado(5, TipoPersona.JURIDICA)
    assert not cuit.tipo_coincide(juridica, TipoPersona.HUMANA)


def test_enmascarar_y_formatear():
    c = cuit.cuit_inventado(9, TipoPersona.JURIDICA)
    enmascarado = cuit.enmascarar(c)
    assert enmascarado == f"{c[:2]}-••••••••-{c[-1]}"
    assert c[2:10] not in enmascarado
    assert cuit.formatear(c) == f"{c[:2]}-{c[2:10]}-{c[10]}"


def test_normalizar_saca_guiones_y_espacios():
    c = cuit.cuit_inventado(3, TipoPersona.JURIDICA)
    assert cuit.normalizar(cuit.formatear(c)) == c
    assert cuit.normalizar(f" {c[:2]} {c[2:]} ") == c
