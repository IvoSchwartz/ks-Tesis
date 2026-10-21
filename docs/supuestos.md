# Supuestos y dudas (Pasos 0 y 1)

## Supuestos que tomé (aprobados)

- Librerías: psycopg 3, pydantic-settings, argon2-cffi, PyJWT, uvicorn, httpx; en el frontend Vite, React Router y las tipografías Barlow y Open Sans con @fontsource.
- Frontend en TypeScript.
- Sesión de 8 horas.
- Bloqueo tras 5 intentos fallidos durante 15 minutos, guardado en dos columnas extra de `usuario` (`intentos_fallidos`, `bloqueado_hasta`).
- Contraseñas de ejemplo al azar, mostradas una sola vez al cargar los datos de ejemplo.
- Primer administrador con `scripts/crear_admin.py`.

## Decisiones que tomé y conviene revisar

1. **Quién crea y edita clientes** es provisorio: Administrador/Socio y Responsable de área. Hay que confirmarlo.
2. **Permisos de Secretaría** son provisorios (ver todos los clientes, sin acciones de administración) hasta la reunión del 26/10. Se cambia en un solo archivo: `backend/app/permisos.py`.
3. **Cliente ajeno o inexistente**: para roles que no ven todo, ambos casos responden 403, así no se puede explorar qué números existen. Cada intento queda en la auditoría.
4. **Empleado de Impuestos fuera del área Impuestos** queda sin acceso.
5. **Un solo responsable por cliente**; la reasignación conserva el historial. La API de reasignar existe, pero no hay botón en la interfaz.
6. **Roles de base de datos**: `ks_migrador` (dueño de las tablas, corre migraciones) y `ks_app` (solo lo necesario; en auditoría, únicamente INSERT y SELECT). Cada tabla nueva necesita su GRANT en la migración.
7. **Auditoría**: trigger que bloquea UPDATE, DELETE y TRUNCATE, cadena de hashes SHA-256 y bloqueo que serializa las inserciones. No se guardan CUIT, claves ni tokens en el detalle. La verificación de la cadena es por línea de comandos, no hay pantalla.
8. **Token en sessionStorage**: se pierde al cerrar la pestaña. Es más simple que una cookie, pero queda expuesto si alguna vez hubiera una falla de scripts en la página. Revisar antes de producción real.
9. **Cambiar la contraseña de alguien no invalida sus tokens ya emitidos** (duran hasta 8 horas). Dar de baja a una persona sí la deja afuera de inmediato.
10. **Sin límite por dirección IP** en el ingreso: solo por usuario.
11. **Logo**: monograma de texto "K&S" hasta tener el logo en vector.
12. Las pantallas de usuarios y clientes se probaron compilando; no hay pruebas automáticas del frontend.

## Dudas abiertas

- **Color de "presentado"**: en el estudio el naranja significa presentado, pero en la guía de diseño el naranja es el único acento. No asigné el naranja a ningún estado. Falta decidir cómo se muestra.
- **Nombre del rol "Responsable de área"** es provisorio. Está en una sola constante (`NOMBRE_ROL_RESPONSABLE_AREA`) y en la lista de roles del frontend.
- **Railway y los roles de base de datos**: no pude comprobar desde acá si la base de Railway permite crear roles. Se confirma en el primer despliegue (ver `despliegue_railway.md`).

## Sin probar

- `docker compose up` (no hay Docker en mi entorno): lo probás vos.
- El despliegue en Railway: no hay acceso de red desde mi entorno.
