"""Validación, formato y enmascarado de CUIT. También genera CUIT inventados para datos de ejemplo."""
import re

from app.constantes import TipoPersona

PREFIJOS_HUMANA = ("20", "23", "24", "27")
PREFIJOS_JURIDICA = ("30", "33", "34")
_PESOS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
_SOLO_DIGITOS = re.compile(r"^\d{11}$")


def normalizar(cuit: str) -> str:
    """Saca guiones y espacios."""
    return re.sub(r"[\s-]", "", cuit or "")


def digito_verificador(primeros_diez: str) -> int | None:
    """Devuelve el dígito verificador, o None si ese número de 10 dígitos no puede tener uno válido."""
    suma = sum(int(d) * p for d, p in zip(primeros_diez, _PESOS))
    resto = 11 - (suma % 11)
    if resto == 11:
        return 0
    if resto == 10:
        return None
    return resto


def es_valido(cuit: str) -> bool:
    if not _SOLO_DIGITOS.match(cuit):
        return False
    if cuit[:2] not in PREFIJOS_HUMANA + PREFIJOS_JURIDICA:
        return False
    return digito_verificador(cuit[:10]) == int(cuit[10])


def tipo_coincide(cuit: str, tipo: str) -> bool:
    prefijos = PREFIJOS_HUMANA if tipo == TipoPersona.HUMANA else PREFIJOS_JURIDICA
    return cuit[:2] in prefijos


def enmascarar(cuit: str) -> str:
    """30-••••••••-4: así se muestra en las listas."""
    return f"{cuit[:2]}-{'•' * 8}-{cuit[-1]}"


def formatear(cuit: str) -> str:
    return f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}"


def cuit_inventado(numero: int, tipo: TipoPersona) -> str:
    """CUIT de ejemplo reconocible: los 8 dígitos centrales empiezan con 999 y el dígito verificador es válido.

    Devuelve el CUIT válido número `numero` (empezando en 0) de ese tipo: números distintos dan CUIT distintos.
    Sirve para `numero` de 0 a 80000.
    """
    prefijo = "30" if tipo == TipoPersona.JURIDICA else "20"
    validos = 0
    for resto in range(100000):
        central = f"999{resto:05d}"
        dv = digito_verificador(prefijo + central)
        if dv is None:
            continue
        if validos == numero:
            return f"{prefijo}{central}{dv}"
        validos += 1
    raise ValueError("No se pudo generar un CUIT de ejemplo")
