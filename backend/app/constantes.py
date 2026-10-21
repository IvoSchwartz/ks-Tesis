"""Constantes del dominio. En la base se guardan las claves; las etiquetas son solo para mostrar."""
from enum import StrEnum


class Area(StrEnum):
    IMPUESTOS = "impuestos"
    SECRETARIA = "secretaria"
    LABORAL = "laboral"  # solo un valor del catálogo: no tiene módulos en este sistema
    CONTABILIDAD_AUDITORIA = "contabilidad_auditoria"


ETIQUETA_AREA: dict[Area, str] = {
    Area.IMPUESTOS: "Impuestos",
    Area.SECRETARIA: "Secretaría",
    Area.LABORAL: "Laboral",
    Area.CONTABILIDAD_AUDITORIA: "Contabilidad y Auditoría",
}

# Nombre provisional del rol: se cambia acá, en un único lugar.
NOMBRE_ROL_RESPONSABLE_AREA = "Responsable de área"


class Rol(StrEnum):
    ADMIN_SOCIO = "admin_socio"
    RESPONSABLE_AREA = "responsable_area"
    EMPLEADO_IMPUESTOS = "empleado_impuestos"
    SECRETARIA = "secretaria"


ETIQUETA_ROL: dict[Rol, str] = {
    Rol.ADMIN_SOCIO: "Administrador/Socio",
    Rol.RESPONSABLE_AREA: NOMBRE_ROL_RESPONSABLE_AREA,
    Rol.EMPLEADO_IMPUESTOS: "Empleado de Impuestos",
    Rol.SECRETARIA: "Secretaría",
}

# Roles que pueden ser el responsable de un cliente.
ROLES_RESPONSABLES = frozenset({Rol.EMPLEADO_IMPUESTOS, Rol.RESPONSABLE_AREA})


class TipoPersona(StrEnum):
    HUMANA = "humana"
    JURIDICA = "juridica"


class Condicion(StrEnum):
    RESPONSABLE_INSCRIPTO = "responsable_inscripto"
    MONOTRIBUTISTA = "monotributista"
    OTRO = "otro"


class ColorEstado(StrEnum):
    """Colores de estado de la guía de diseño. El naranja de acento no se usa como color de estado."""

    CORRECTO = "correcto"
    ATENCION = "atencion"
    ERROR = "error"
    NEUTRO = "neutro"


def valores(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]
