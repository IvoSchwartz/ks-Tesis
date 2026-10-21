"""Recorre la cadena de hashes de la auditoría y avisa si alguna fila fue alterada o sacada.

Uso (desde la carpeta backend):
    python -m scripts.verificar_auditoria
Termina con código 0 si está todo bien y 1 si encuentra un problema.
"""
import sys

from app.auditoria import verificar_cadena
from app.db import SessionLocal


def main() -> int:
    with SessionLocal() as db:
        ok, fila_mala, revisadas = verificar_cadena(db)
    if ok:
        print(f"La cadena de auditoría está íntegra ({revisadas} filas revisadas).")
        return 0
    print(f"PROBLEMA: la cadena de auditoría se rompe en la fila {fila_mala} ({revisadas} filas revisadas).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
