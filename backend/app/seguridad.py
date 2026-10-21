"""Contraseñas con argon2 y tokens de sesión."""
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import get_settings

_hasher = PasswordHasher()
# Se usa cuando el correo no existe, para que tardar lo mismo no delate qué correos están registrados.
HASH_FALSO = _hasher.hash("contrasena-que-nadie-usa")
ALGORITMO = "HS256"


def hashear(contrasena: str) -> str:
    return _hasher.hash(contrasena)


def verificar(hash_guardado: str, contrasena: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, contrasena)
    except (VerificationError, InvalidHashError):
        return False


def necesita_rehash(hash_guardado: str) -> bool:
    try:
        return _hasher.check_needs_rehash(hash_guardado)
    except InvalidHashError:
        return False


def crear_token(usuario_id: int) -> tuple[str, int]:
    """Devuelve (token, segundos de duración). Dura la jornada laboral (JWT_HORAS, 8 por defecto)."""
    s = get_settings()
    ahora = datetime.now(timezone.utc)
    segundos = s.jwt_horas * 3600
    payload = {"sub": str(usuario_id), "iat": ahora, "exp": ahora + timedelta(seconds=segundos)}
    return jwt.encode(payload, s.jwt_secret, algorithm=ALGORITMO), segundos


def leer_token(token: str) -> int | None:
    """Devuelve el id de usuario, o None si el token es inválido o venció."""
    try:
        datos = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITMO])
        return int(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
