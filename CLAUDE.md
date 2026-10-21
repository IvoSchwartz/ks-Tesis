# CLAUDE.md — Sistema de Impuestos K&S

Copiar este archivo a la raíz de la carpeta del sistema. Actualizar la sección "Módulo actual" al empezar cada sesión.

## Qué es este proyecto

Sistema interno para el área de Impuestos de K&S Contadores Públicos (estudio de unas 15 personas, unos 60 clientes). Es una tesis (Práctica Profesionalizante 3, Analista en Sistemas, IES Córdoba). Objetivos:
1. Resolver la exposición de las claves fiscales de los clientes (hoy están en un archivo compartido).
2. Reemplazar las planillas de Excel del área (panel de estado, IVA, Monotributo, otros impuestos).

El sistema NUNCA presenta declaraciones juradas en ARCA. La persona las presenta en el portal y el sistema solo registra que lo hizo. La facturación electrónica es la excepción: los comprobantes se emiten desde el sistema por WSFE (módulo 8).

## Stack (no cambiar sin que Ivo lo pida)

- Backend: Python + FastAPI, SQLAlchemy, Alembic para migraciones, pytest.
- Frontend: React (TanStack Query y Table).
- Base de datos: PostgreSQL.
- Hosting: Railway.
- Cifrado de claves fiscales: AES-256-GCM, con la clave maestra fuera de la base de datos (variable de entorno).
- ARCA: WSAA (autenticación) y WSFE (facturación), detrás de una interfaz `ConectorArca` con una versión simulada (mock).
- Acceso al portal de ARCA: por bóveda de claves cifradas. Las delegaciones de servicio están descartadas.

## Reglas del dominio (importantes)

- **Cliente ≠ CUIT.** Un cliente tiene varios contribuyentes (CUIT). Modelar `Cliente` 1—N `Contribuyente`. Un IVA se liquida por CUIT.
- **Roles frente al sistema** (nunca nombres de personas): Administrador/Socio, Responsable de área, Empleado de Impuestos, Secretaría. No usar la palabra "Senior". El nombre "Responsable de área" es provisional: definirlo en una sola constante.
- **Áreas:** Impuestos, Secretaría, Laboral, Contabilidad y Auditoría. Cada usuario tiene un área y un rol; el menú y los permisos dependen de ambos. Laboral es solo un valor del catálogo: el área Laboral no tiene módulos ni funciones en este sistema.
- **Permisos en el backend.** El filtro por cliente asignado se aplica con una dependencia de FastAPI. Ocultar un ítem del menú no alcanza. Escribir pruebas que intenten acceder a clientes ajenos llamando a la API directamente.
- **Asignación:** cada cliente tiene un solo empleado responsable; el Responsable de área ve todos los clientes de su área y puede reasignar; el Socio ve todo. El responsable actual es la fila de `asignacion` sin fecha de fin (una sola por cliente); no se guarda en otro lugar para que no se desincronice.
- **Auditoría inmutable:** quién hizo qué, sobre qué cliente y cuándo. Solo se inserta, nunca se modifica ni se borra. Se garantiza con tres cosas: la aplicación se conecta con un rol de base de datos que solo puede hacer INSERT y SELECT sobre la tabla de auditoría, un trigger que bloquea UPDATE, DELETE y TRUNCATE, y un encadenamiento por hash. Como dos escrituras simultáneas romperían la cadena, la inserción se serializa (bloqueo de base de datos).
- **Aprobación del socio:** un socio debe aprobar el borrador de IVA antes de que se presente. Quedan registrados quién y cuándo.
- **Estados configurables:** los estados de cada seguimiento viven en una tabla, no escritos en el código. Cada impuesto tiene su propia secuencia de estados (por ejemplo, IVA e Ingresos Brutos no usan los mismos). El estado "F. 2002" no existe (era del aplicativo viejo). El panel es genérico: un seguimiento por contribuyente, impuesto y período.
- **Color de los estados:** en el estudio el naranja significa "presentado", pero en la guía de diseño el naranja es el único acento de la interfaz. Hasta que se defina cómo mostrarlo, no asignar el naranja de acento (#fa8500) a ningún estado.
- **Sin WhatsApp** (solo correo). Sin bandeja de comunicaciones de ARCA.

## Seguridad (obligatorio)

- Nunca escribir claves fiscales, CUIT reales ni datos de clientes en el código, los tests, los logs ni el repositorio.
- La clave fiscal nunca viaja al frontend ni aparece en una respuesta de la API. Solo se descifra en el servidor al abrir la sesión de ARCA.
- La clave maestra y los secretos van en variables de entorno. `.env` está en `.gitignore`.
- Contraseñas de usuarios con hash seguro (argon2 o bcrypt). Límite de intentos de login.
- Antes de implementar la bóveda o el acceso a ARCA: correr `/cso`.

## Datos

Todo desarrollo y prueba usa datos inventados. Los datos reales del estudio se cargan al final y no se hacen públicos.

Los CUIT inventados llevan dígito verificador válido y un patrón fijo y reconocible (los 8 dígitos centrales empiezan con 999), para reducir la posibilidad de coincidir con uno real. Los nombres de clientes de ejemplo son ficticios ("Ejemplo S.A.", "Muestra S.R.L.", etc.).

## Convenciones

- Nombres de tablas, campos y términos del dominio en español sin tildes ni eñes (`cliente`, `contribuyente`, `declaracion`, `periodo`). Palabras del lenguaje y de las librerías en inglés.
- Textos de la interfaz en español con voseo ("Ingresá", "Revisalo"); botones con verbo y objeto ("Emitir factura"). Sin signos de raya larga en los textos de la interfaz.
- Estilo visual y componentes: seguir `Guia_de_diseno_KS.md` (azul marino #0b2645, naranja #fa8500, Barlow y Open Sans). Los colores y la tipografía van como variables, una sola vez.
- Migraciones con Alembic; nunca editar la base a mano.
- Cada módulo con pruebas automáticas. Los permisos y el cifrado son lo que más se prueba.

## Cómo trabajar

- Un módulo por sesión. Terminar y abrir sesión nueva (`/clear`).
- Siempre pedir primero un plan (modo Plan). Después de aprobarlo, programar.
- Dar archivos completos, no diffs parciales.
- No ampliar el alcance ni agregar librerías sin avisar.
- Antes de cada módulo: `/plan-eng-review`. Al terminarlo: `/review`. Si toca claves o accesos: `/cso`. Con la interfaz lista: `/qa`.

## Fuera de alcance

Área Laboral/Bejerman, reproducir el puesto de trabajo remoto vía AnyDesk, herramientas externas de Contabilidad, lo que ya cubre el CPCE BOT PRO, presentar declaraciones en ARCA.

## Módulo actual

Pasos 0 y 1: cimientos, usuarios, roles, clientes con varios CUIT, asignaciones y auditoría. (Actualizar al cambiar de módulo.)

## Orden de construcción

0. Repositorio, entorno local y Railway.
1. Modelo de datos base, usuarios, roles, clientes y CUIT, asignaciones, auditoría.
2. Bóveda de claves (cifrado, "cambiar clave fiscal", nunca devolver la clave).
3. Conector con ARCA (mock primero) y prueba con un cliente.
4. Panel genérico de seguimiento por impuesto y período.
5. Libros IVA (registro de recepción).
6. Borrador de IVA con aprobación del socio y reparto por actividad.
7. Monotributo con alertas al socio responsable.
8. Facturación (WSFE en homologación).
9. Secundarios al final: calendario de vencimientos y Convenio Multilateral reducido.
