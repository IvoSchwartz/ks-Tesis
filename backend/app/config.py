"""Configuración por variables de entorno. Ningún secreto vive en el código."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    entorno: str = "desarrollo"
    database_url_migrador: str
    database_url_app: str
    app_db_password: str
    jwt_secret: str
    jwt_horas: int = 8  # una jornada de trabajo
    login_max_intentos: int = 5
    login_bloqueo_minutos: int = 15
    cors_origins: str = "http://localhost:5173"

    @field_validator("jwt_secret")
    @classmethod
    def _jwt_secret_largo(cls, valor: str) -> str:
        if len(valor) < 32:
            raise ValueError("JWT_SECRET debe tener al menos 32 caracteres")
        return valor

    @property
    def es_produccion(self) -> bool:
        return self.entorno.lower() == "produccion"

    @property
    def origenes_permitidos(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
