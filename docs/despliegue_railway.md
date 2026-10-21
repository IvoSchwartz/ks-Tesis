# Despliegue en Railway

Resultado: tres servicios (base de datos, backend y frontend) que se actualizan solos cada vez que se sube código a la rama `main` de GitHub.

Hacé esto cuando el repositorio ya tenga el código subido.

## 1. Proyecto y base de datos

1. En Railway: **New Project** > **Deploy from GitHub repo** > elegí `ks-impuestos`. Si no aparece, tocá **Configure GitHub App** y dale acceso a ese repositorio.
2. Railway crea un servicio con el repositorio. Lo vamos a usar como backend (paso 2).
3. En el lienzo del proyecto: **+ New** > **Database** > **Add PostgreSQL**.

## 2. Backend

1. Entrá al servicio del repositorio > **Settings**:
   - **Service Name**: `backend`
   - **Root Directory**: `/backend`
   - El `Dockerfile` ya está en esa carpeta y al arrancar corre las migraciones y después la API.
2. **Variables** (pestaña Variables > **New Variable**). Reemplazá `Postgres` si el servicio de base de datos tiene otro nombre:
   - `ENTORNO` = `produccion`
   - `DATABASE_URL_MIGRADOR` = `postgresql+psycopg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}`
   - `APP_DB_PASSWORD` = una contraseña larga y aleatoria (la inventás vos; la migración la usa para crear el rol `ks_app`)
   - `DATABASE_URL_APP` = `postgresql+psycopg://ks_app:LA_MISMA_CONTRASEÑA@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}`
   - `JWT_SECRET` = un valor aleatorio de al menos 32 caracteres
   - `JWT_HORAS` = `8`
   - `CORS_ORIGINS` = la dirección pública del frontend (se completa en el paso 3)
3. **Settings** > **Networking** > **Generate Domain**. Anotá la dirección.
4. Verificá en los registros (**Deployments** > **View logs**) que la migración terminó sin errores.

> **Punto a confirmar:** la migración 0002 crea el rol de base de datos `ks_app`. Si el usuario de la base de Railway no permite crear roles, el despliegue falla en ese punto con un error de permisos. En ese caso, no sigas: avisame y lo resolvemos antes de continuar.

## 3. Frontend

1. En el lienzo: **+ New** > **GitHub Repo** > `ks-impuestos` (otra vez el mismo repositorio).
2. **Settings**:
   - **Service Name**: `frontend`
   - **Root Directory**: `/frontend`
3. **Variables**: `VITE_API_URL` = la dirección pública del backend (la del paso 2.3, con `https://`). Esta variable se usa al compilar, así que si cambia hay que volver a desplegar.
4. **Settings** > **Networking** > **Generate Domain**.
5. Volvé al backend y completá `CORS_ORIGINS` con la dirección del frontend (con `https://`, sin barra al final).

## 4. Primer administrador

El primer administrador se crea una sola vez desde tu computadora, apuntando a la base de Railway. Con la CLI de Railway instalada y el proyecto vinculado:

```
railway link
railway run --service backend python -m scripts.crear_admin
```

Te pide nombre, correo y contraseña (mínimo 10 caracteres). No cargues los datos de ejemplo en producción salvo para la defensa de la tesis (el script lo rechaza si no se lo permitís expresamente).

## 5. Comprobar

1. Abrí la dirección del frontend e ingresá con el administrador.
2. Abrí `https://DIRECCION_DEL_BACKEND/salud`: debe responder que está todo bien.
3. Verificá la auditoría: `railway run --service backend python -m scripts.verificar_auditoria`.

## Si algo falla

- **Pantalla que dice que no se puede conectar**: revisá `VITE_API_URL` y `CORS_ORIGINS`.
- **El backend no arranca**: mirá los registros; lo más común es una variable mal copiada.
