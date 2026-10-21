"""Crea el primer Administrador/Socio. No hay usuario ni clave por defecto.

Uso (desde la carpeta backend):
    python -m scripts.crear_admin --nombre "Nombre Apellido" --correo persona@dominio.com
La contraseña se pide por teclado (dos veces). Para correrlo sin teclado, definí ADMIN_PASSWORD.
"""
import argparse
import getpass
import os
import re
import sys

from sqlalchemy import func, select

from app import auditoria
from app.constantes import Area, Rol
from app.db import SessionLocal
from app.esquemas import CORREO_PATRON
from app.modelos import Usuario
from app.seguridad import hashear


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea el primer Administrador/Socio")
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--correo", required=True)
    args = parser.parse_args()

    if not re.match(CORREO_PATRON, args.correo):
        print("El correo no es válido.", file=sys.stderr)
        return 1

    clave = os.environ.get("ADMIN_PASSWORD")
    if not clave:
        clave = getpass.getpass("Contraseña (mínimo 10 caracteres): ")
        if clave != getpass.getpass("Repetí la contraseña: "):
            print("Las contraseñas no coinciden.", file=sys.stderr)
            return 1
    if len(clave) < 10:
        print("La contraseña debe tener al menos 10 caracteres.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        if db.scalar(select(Usuario.id).where(func.lower(Usuario.correo) == args.correo.lower())):
            print("Ya existe una persona con ese correo.", file=sys.stderr)
            return 1
        usuario = Usuario(
            nombre=args.nombre.strip(),
            correo=args.correo.strip(),
            hash_contrasena=hashear(clave),
            area=Area.IMPUESTOS.value,
            rol=Rol.ADMIN_SOCIO.value,
            activo=True,
        )
        db.add(usuario)
        db.flush()
        auditoria.registrar(
            db,
            accion="usuario_crear",
            usuario_id=None,
            entidad="usuario",
            entidad_id=usuario.id,
            detalle={"rol": usuario.rol, "area": usuario.area, "origen": "script_crear_admin"},
        )
        db.commit()
    print("Administrador creado. Ya podés ingresar al sistema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
