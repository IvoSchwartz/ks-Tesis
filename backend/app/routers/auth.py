"""Ingreso y datos de la persona que ingresó."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import auditoria
from app.config import get_settings
from app.constantes import ETIQUETA_AREA, ETIQUETA_ROL, Area, Rol
from app.db import get_db
from app.dependencias import usuario_actual
from app.esquemas import LoginIn, MeOut, TokenOut
from app.modelos import Usuario
from app.permisos import menu_de, permisos_de
from app.seguridad import HASH_FALSO, crear_token, hashear, necesita_rehash, verificar

router = APIRouter(tags=["ingreso"])


@router.post("/auth/login", response_model=TokenOut)
def login(datos: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    ajustes = get_settings()
    ahora = datetime.now(timezone.utc)
    usuario = db.scalar(select(Usuario).where(func.lower(Usuario.correo) == datos.correo.strip().lower()))

    if usuario is not None and usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > ahora:
        auditoria.registrar(
            db, accion="login_bloqueado", usuario_id=usuario.id, entidad="usuario", entidad_id=usuario.id
        )
        db.commit()
        raise HTTPException(
            status_code=429, detail="Hubo demasiados intentos. Esperá unos minutos y probá de nuevo."
        )

    # Se verifica siempre una contraseña (con un hash falso si el correo no existe) para tardar lo mismo.
    clave_correcta = verificar(usuario.hash_contrasena if usuario else HASH_FALSO, datos.contrasena)

    if usuario is None or not clave_correcta or not usuario.activo:
        detalle: dict = {}
        if usuario is not None:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= ajustes.login_max_intentos:
                usuario.bloqueado_hasta = ahora + timedelta(minutes=ajustes.login_bloqueo_minutos)
                usuario.intentos_fallidos = 0
                detalle["bloqueo_activado"] = True
        auditoria.registrar(
            db,
            accion="login_fallido",
            usuario_id=usuario.id if usuario else None,
            entidad="usuario" if usuario else None,
            entidad_id=usuario.id if usuario else None,
            detalle=detalle,
        )
        db.commit()
        raise HTTPException(status_code=401, detail="El correo o la contraseña no son correctos.")

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    if necesita_rehash(usuario.hash_contrasena):
        usuario.hash_contrasena = hashear(datos.contrasena)
    auditoria.registrar(db, accion="login_ok", usuario_id=usuario.id, entidad="usuario", entidad_id=usuario.id)
    db.commit()

    token, segundos = crear_token(usuario.id)
    return TokenOut(access_token=token, expira_en_segundos=segundos)


@router.get("/me", response_model=MeOut)
def yo(usuario: Usuario = Depends(usuario_actual)) -> MeOut:
    permisos = permisos_de(usuario.rol, usuario.area)
    return MeOut(
        id=usuario.id,
        nombre=usuario.nombre,
        correo=usuario.correo,
        area=usuario.area,
        area_etiqueta=ETIQUETA_AREA[Area(usuario.area)],
        rol=usuario.rol,
        rol_etiqueta=ETIQUETA_ROL[Rol(usuario.rol)],
        alcance=permisos.alcance.value,
        capacidades=sorted(c.value for c in permisos.capacidades),
        menu=menu_de(usuario.rol, usuario.area),
    )
