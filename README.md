# Sistema de Impuestos K&S

Sistema interno para el área de Impuestos de K&S Contadores Públicos. Proyecto de tesis (Práctica Profesionalizante 3, IES Córdoba).

Este paso incluye los cimientos: usuarios, roles, clientes con varios CUIT, asignaciones y auditoría inmutable.
Todos los datos de ejemplo son inventados.

## Probar en tu computadora

Necesitás Docker Desktop.

1. Copiá `.env.example` como `.env` y cambiá `JWT_SECRET` por un valor largo (mínimo 32 caracteres):
   `python -c "import secrets; print(secrets.token_urlsafe(48))"`
2. Corré `docker compose up --build`.
3. Creá el primer administrador (te pide la contraseña, mínimo 10 caracteres):
   `docker compose exec backend python -m scripts.crear_admin`
4. Opcional, cargar datos de ejemplo (muestra las contraseñas una sola vez):
   `docker compose exec backend python -m scripts.seed_demo`
5. Abrí http://localhost:5173 (la API está en http://localhost:8000/docs).

## Pruebas automáticas

Con Postgres corriendo (por ejemplo, el de `docker compose up db`):

```
cd backend
pip install -r requirements-dev.txt
pytest
```

Las pruebas de permisos intentan entrar a clientes ajenos llamando a la API directamente.

## Verificar la auditoría

`docker compose exec backend python -m scripts.verificar_auditoria` recorre la cadena de hashes y avisa si algún registro fue alterado.

## Estructura

- `backend/`: API (FastAPI), migraciones (Alembic) y pruebas (pytest).
- `frontend/`: interfaz (React + TypeScript).
- `docs/`: despliegue en Railway y lista de supuestos y dudas.
- `CLAUDE.md` y `Guia_de_diseno_KS.md`: reglas del proyecto y de las pantallas.
