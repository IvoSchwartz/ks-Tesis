"""Formas de los datos que entran y salen de la API. Nunca se devuelve el hash de contraseña ni una clave fiscal."""
from pydantic import BaseModel, ConfigDict, Field

from app.constantes import Area, Condicion, Rol, TipoPersona

CORREO_PATRON = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class LoginIn(BaseModel):
    correo: str = Field(min_length=3, max_length=254)
    contrasena: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en_segundos: int


class ItemMenuOut(BaseModel):
    clave: str
    etiqueta: str
    ruta: str


class MeOut(BaseModel):
    id: int
    nombre: str
    correo: str
    area: str
    area_etiqueta: str
    rol: str
    rol_etiqueta: str
    alcance: str
    capacidades: list[str]
    menu: list[ItemMenuOut]


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    area: str
    area_etiqueta: str
    rol: str
    rol_etiqueta: str
    activo: bool


class UsuarioIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    correo: str = Field(pattern=CORREO_PATRON, max_length=254)
    contrasena: str = Field(min_length=10, max_length=128)
    area: Area
    rol: Rol


class UsuarioPut(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    correo: str | None = Field(default=None, pattern=CORREO_PATRON, max_length=254)
    contrasena: str | None = Field(default=None, min_length=10, max_length=128)
    area: Area | None = None
    rol: Rol | None = None
    activo: bool | None = None


class PersonaOut(BaseModel):
    id: int
    nombre: str


class ContribuyenteIn(BaseModel):
    cuit: str = Field(min_length=11, max_length=13)
    nombre: str = Field(min_length=1, max_length=160)
    tipo: TipoPersona
    condicion: Condicion


class ContribuyenteListaOut(BaseModel):
    """En las listas el CUIT va siempre enmascarado."""

    id: int
    cuit_enmascarado: str
    nombre: str
    tipo: str
    condicion: str


class ContribuyenteFichaOut(BaseModel):
    id: int
    cuit: str
    nombre: str
    tipo: str
    condicion: str


class ClienteIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=160)
    area: Area
    responsable_id: int
    contribuyentes: list[ContribuyenteIn] = Field(default_factory=list, max_length=30)


class ClientePut(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=160)
    activo: bool | None = None


class ReasignarIn(BaseModel):
    usuario_id: int


class ClienteListaOut(BaseModel):
    id: int
    nombre: str
    area: str
    area_etiqueta: str
    activo: bool
    responsable: PersonaOut | None
    contribuyentes: list[ContribuyenteListaOut]


class ClienteFichaOut(BaseModel):
    id: int
    nombre: str
    area: str
    area_etiqueta: str
    activo: bool
    responsable: PersonaOut | None
    contribuyentes: list[ContribuyenteFichaOut]
