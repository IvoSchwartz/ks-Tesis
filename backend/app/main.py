"""Punto de entrada de la API."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.db import SessionLocal
from app.errores import ErrorNegocio
from app.routers import auth, clientes, usuarios

ajustes = get_settings()

app = FastAPI(
    title="Sistema de Impuestos K&S",
    docs_url=None if ajustes.es_produccion else "/docs",
    redoc_url=None,
    openapi_url=None if ajustes.es_produccion else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ajustes.origenes_permitidos,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
)


@app.exception_handler(ErrorNegocio)
async def _error_negocio(_: Request, error: ErrorNegocio) -> JSONResponse:
    return JSONResponse(status_code=error.estado, content={"detail": error.mensaje})


@app.exception_handler(IntegrityError)
async def _integridad(_: Request, __: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409, content={"detail": "Ese cambio choca con datos que ya existen. Revisalo e intentá de nuevo."}
    )


app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(usuarios.router)


@app.get("/salud", tags=["sistema"])
def salud() -> JSONResponse:
    """Para el chequeo de Railway: responde 200 si la base contesta."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"estado": "sin_base"})
    return JSONResponse(content={"estado": "ok"})
