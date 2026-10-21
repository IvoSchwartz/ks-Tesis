"""Carga datos de ejemplo INVENTADOS: 5 usuarios, 10 clientes con sus CUIT y el catálogo de estados.

Los CUIT tienen dígito verificador válido y los 8 dígitos centrales empiezan con 999 (se reconocen como
inventados). Los nombres son ficticios. Las contraseñas se generan al azar y se muestran UNA sola vez.

Uso (desde la carpeta backend):
    python -m scripts.seed_demo
En producción se niega, salvo que se agregue --permitir-produccion (por ejemplo para una demostración).
"""
import argparse
import secrets
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from app import auditoria
from app.config import get_settings
from app.constantes import Area, Condicion, ColorEstado, Rol, TipoPersona
from app.cuit import cuit_inventado
from app.db import SessionLocal
from app.modelos import Asignacion, Cliente, Contribuyente, Estado, Impuesto, Usuario
from app.seguridad import hashear

USUARIOS = [
    ("Usuario Socio", "socio@ejemplo.test", Area.IMPUESTOS, Rol.ADMIN_SOCIO),
    ("Usuario Responsable", "responsable@ejemplo.test", Area.IMPUESTOS, Rol.RESPONSABLE_AREA),
    ("Usuario Empleado A", "empleado.a@ejemplo.test", Area.IMPUESTOS, Rol.EMPLEADO_IMPUESTOS),
    ("Usuario Empleado B", "empleado.b@ejemplo.test", Area.IMPUESTOS, Rol.EMPLEADO_IMPUESTOS),
    ("Usuario Secretaria", "secretaria@ejemplo.test", Area.SECRETARIA, Rol.SECRETARIA),
]

# (nombre del cliente, cantidad de CUIT, correo del responsable)
CLIENTES = [
    ("Ejemplo S.A.", 4, "empleado.a@ejemplo.test"),
    ("Muestra S.R.L.", 1, "empleado.a@ejemplo.test"),
    ("Cliente Tres S.A.", 3, "empleado.a@ejemplo.test"),
    ("Cliente Cuatro S.R.L.", 5, "empleado.a@ejemplo.test"),
    ("Cliente Cinco S.A.", 1, "empleado.a@ejemplo.test"),
    ("Cliente Seis", 1, "empleado.b@ejemplo.test"),
    ("Cliente Siete S.A.", 3, "empleado.b@ejemplo.test"),
    ("Cliente Ocho S.R.L.", 2, "empleado.b@ejemplo.test"),
    ("Cliente Nueve", 1, "empleado.b@ejemplo.test"),
    ("Cliente Diez S.A.", 3, "empleado.b@ejemplo.test"),
]

# Secuencias de estados por impuesto (de la leyenda de la planilla actual, sin el estado "F. 2002").
# El naranja de acento no se usa como color de estado: cómo mostrar "Presentado" está sin definir.
CATALOGO = {
    ("IVA", 1): [
        ("Papel de trabajo listo sin retenciones", ColorEstado.ATENCION),
        ("Papel de trabajo listo con retenciones", ColorEstado.CORRECTO),
        ("Presentado", ColorEstado.NEUTRO),
        ("No se presenta", ColorEstado.NEUTRO),
    ],
    ("Ingresos Brutos", 2): [
        ("Ventas trabajadas", ColorEstado.CORRECTO),
        ("Presentado", ColorEstado.NEUTRO),
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga datos de ejemplo inventados")
    parser.add_argument("--permitir-produccion", action="store_true")
    args = parser.parse_args()

    if get_settings().es_produccion and not args.permitir_produccion:
        print("Los datos de ejemplo no se cargan en producción (usá --permitir-produccion si es a propósito).")
        return 1

    with SessionLocal() as db:
        if db.scalar(select(Usuario.id).where(Usuario.correo.like("%@ejemplo.test")).limit(1)):
            print("Los datos de ejemplo ya están cargados. No se hizo nada.")
            return 1

        credenciales: list[tuple[str, str]] = []
        por_correo: dict[str, Usuario] = {}
        for nombre, correo, area, rol in USUARIOS:
            clave = secrets.token_urlsafe(12)
            usuario = Usuario(
                nombre=nombre, correo=correo, hash_contrasena=hashear(clave), area=area.value, rol=rol.value
            )
            db.add(usuario)
            por_correo[correo] = usuario
            credenciales.append((correo, clave))
        db.flush()

        ahora = datetime.now(timezone.utc)
        contador = 100
        for nombre, cantidad, correo_resp in CLIENTES:
            cliente = Cliente(nombre=nombre, area=Area.IMPUESTOS.value)
            db.add(cliente)
            db.flush()
            db.add(Asignacion(cliente_id=cliente.id, usuario_id=por_correo[correo_resp].id, fecha_inicio=ahora))
            es_sociedad = nombre.endswith(("S.A.", "S.R.L."))
            for i in range(cantidad):
                # El primer CUIT de una sociedad es de persona jurídica; el resto, de personas humanas.
                tipo = TipoPersona.JURIDICA if (es_sociedad and i == 0) else TipoPersona.HUMANA
                condicion = (
                    Condicion.RESPONSABLE_INSCRIPTO if tipo == TipoPersona.JURIDICA else Condicion.MONOTRIBUTISTA
                )
                contador += 1
                db.add(
                    Contribuyente(
                        cuit=cuit_inventado(contador, tipo),
                        nombre=f"{nombre} (CUIT {i + 1})" if cantidad > 1 else nombre,
                        tipo=tipo.value,
                        condicion=condicion.value,
                        cliente_id=cliente.id,
                    )
                )

        for (nombre_impuesto, orden), estados in CATALOGO.items():
            impuesto = Impuesto(nombre=nombre_impuesto, orden=orden)
            db.add(impuesto)
            db.flush()
            for n, (nombre_estado, color) in enumerate(estados, start=1):
                db.add(Estado(impuesto_id=impuesto.id, nombre=nombre_estado, orden=n, color=color.value))

        auditoria.registrar(
            db,
            accion="seed_datos_demo",
            detalle={"usuarios": len(USUARIOS), "clientes": len(CLIENTES), "origen": "script_seed_demo"},
        )
        db.commit()

    print("Datos de ejemplo cargados. Contraseñas generadas (se muestran solo esta vez):")
    for correo, clave in credenciales:
        print(f"  {correo}  {clave}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
