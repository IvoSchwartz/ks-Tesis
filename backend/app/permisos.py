"""Tabla de permisos por rol y área. Es la ÚNICA fuente: el backend la usa para filtrar y para autorizar,
y de ella sale el menú que ve cada persona (el frontend solo lo dibuja).

Para cambiar qué puede hacer un rol (por ejemplo, Secretaría después de la reunión del 26/10) se edita
solo esta tabla.
"""
from dataclasses import dataclass
from enum import StrEnum

from app.constantes import Area, Rol


class Alcance(StrEnum):
    TODOS = "todos"  # todos los clientes
    AREA = "area"  # los clientes del área de la persona
    ASIGNADOS = "asignados"  # solo los que tiene asignados
    NINGUNO = "ninguno"


class Capacidad(StrEnum):
    VER_CLIENTES = "ver_clientes"
    CREAR_CLIENTES = "crear_clientes"
    EDITAR_CLIENTES = "editar_clientes"
    REASIGNAR_CLIENTES = "reasignar_clientes"
    ADMINISTRAR_USUARIOS = "administrar_usuarios"


@dataclass(frozen=True)
class PermisosRol:
    alcance: Alcance
    capacidades: frozenset[Capacidad]
    menu: tuple[str, ...]


# Ítems de menú que existen en este paso: clave -> (etiqueta, ruta)
ITEMS_MENU: dict[str, tuple[str, str]] = {
    "clientes": ("Clientes", "/clientes"),
    "usuarios": ("Usuarios", "/usuarios"),
}

V = Capacidad.VER_CLIENTES

PERMISOS: dict[Rol, PermisosRol] = {
    Rol.ADMIN_SOCIO: PermisosRol(
        alcance=Alcance.TODOS,
        capacidades=frozenset(
            {
                V,
                Capacidad.CREAR_CLIENTES,
                Capacidad.EDITAR_CLIENTES,
                Capacidad.REASIGNAR_CLIENTES,
                Capacidad.ADMINISTRAR_USUARIOS,
            }
        ),
        menu=("clientes", "usuarios"),
    ),
    Rol.RESPONSABLE_AREA: PermisosRol(
        alcance=Alcance.AREA,
        capacidades=frozenset(
            {V, Capacidad.CREAR_CLIENTES, Capacidad.EDITAR_CLIENTES, Capacidad.REASIGNAR_CLIENTES}
        ),
        menu=("clientes",),
    ),
    Rol.EMPLEADO_IMPUESTOS: PermisosRol(
        alcance=Alcance.ASIGNADOS,
        capacidades=frozenset({V}),
        menu=("clientes",),
    ),
    # Provisorio hasta la reunión del 26/10: lista amplia de clientes, sin acciones de administración.
    Rol.SECRETARIA: PermisosRol(
        alcance=Alcance.TODOS,
        capacidades=frozenset({V}),
        menu=("clientes",),
    ),
}

SIN_ACCESO = PermisosRol(alcance=Alcance.NINGUNO, capacidades=frozenset(), menu=())


def permisos_de(rol: str, area: str) -> PermisosRol:
    """Permisos de una persona según su rol y su área."""
    try:
        permisos = PERMISOS[Rol(rol)]
    except ValueError:
        return SIN_ACCESO
    # Un Empleado de Impuestos de otra área no tiene acceso a las pantallas del área impositiva.
    if rol == Rol.EMPLEADO_IMPUESTOS and area != Area.IMPUESTOS:
        return SIN_ACCESO
    return permisos


def menu_de(rol: str, area: str) -> list[dict[str, str]]:
    return [
        {"clave": clave, "etiqueta": ITEMS_MENU[clave][0], "ruta": ITEMS_MENU[clave][1]}
        for clave in permisos_de(rol, area).menu
    ]
