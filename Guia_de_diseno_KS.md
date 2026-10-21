# Guía de diseño — Sistema de Impuestos K&S

Documento de trabajo para programar las pantallas (Claude Code + Impeccable) y para mantener el mismo estilo en todo el programa. Última actualización: 19 de octubre de 2026.

Las 14 pantallas diseñadas están en el lienzo de Claude (artifact "Pantallas K&S"). Este documento resume las reglas que usan todas. Faltan diseñar dos pantallas más (calendario y Convenio Multilateral reducido, ver sección 8).

## 1. Identidad

- Sistema interno para el área de Impuestos de K&S Contadores Públicos. Lo usan empleados del estudio en computadora, desde un navegador común.
- Tono: profesional, sobrio y claro. Que se parezca al estudio (azul marino + naranja de la web ksyasoc.com.ar), sin adornos.
- Logo: monograma "K&S" y logo completo en blanco sobre fondo azul. Se dispone del logo como imagen. Conviene pedir a Diego el original en vector (SVG o PDF) o, si no hay, una imagen PNG con fondo transparente de al menos 1000 px de ancho, para que no se vea borroso. Adjuntarla como archivo, no pegada en el chat.
- Apellido del socio: se escribe **Kanoivicki** (todo con i latina), como figura en el logo y en la web. Toda la documentación de la tesis debe usar esa escritura.

## 2. Colores

| Uso | Valor |
|---|---|
| Azul marino (menú, títulos de acción) | #0b2645 |
| Azul marino 2 (ítem activo del menú) | #1d3a62 |
| Naranja (único acento, botón principal) | #fa8500 (hover #e87d00) |
| Fondo de la aplicación | #f4f5f8 |
| Superficies | #ffffff |
| Líneas y bordes | #dde1e9 |
| Texto | #1b2433 |
| Texto secundario | #556072 |
| Borde de campos | #8590a5 |

Estados (siempre con texto, nunca solo color):
- Correcto: fondo #e2f3e9, texto #17653f
- Atención: fondo #fff0cf, texto #7a4b00
- Error o vencido: fondo #fde3e0, texto #9b1c1c
- Neutro: fondo #eceff4, texto #3e4a5d

Regla: el botón naranja lleva texto azul marino (blanco sobre naranja no cumple el contraste). Un solo acento en todo el sistema.

## 3. Tipografía

- Títulos y botones: Barlow (600).
- Texto, tablas y formularios: Open Sans (400 y 600).
- Cuerpo 15 px, títulos de pantalla 36 px, títulos de sección 22 px.
- Sin signos de raya larga en los textos.

## 4. Componentes

- Una sola esquina redondeada: 8 px (solo los números dentro de un círculo usan círculo completo).
- Botones: principal (naranja), contorno (borde azul), discreto (sin borde). Alto mínimo 44 px. Hover solo con mouse. Al apretar se achica apenas.
- Un solo botón principal por pantalla o sección.
- Campos con la etiqueta arriba, nunca solo como texto de ayuda. Errores debajo del campo.
- Tablas: grilla con encabezado gris claro; si no entran, scroll horizontal dentro de su cuadro.
- Chips de estado: texto corto, 28 px de alto.
- Menú lateral azul marino. Los ítems que aparecen dependen del área y del rol de quien ingresó (ver sección 9). Ítems posibles: Clientes, Panel de estado, Libros IVA, Borrador de IVA, Monotributo, Facturación, Calendario, Convenio Multilateral, y para socios y administración: Usuarios y Aprobaciones (con el número de pendientes).
- Foco visible para quien usa teclado. Las animaciones se apagan si la persona pidió menos movimiento.

## 5. Voz de los textos

- Imperativo con voseo: "Ingresá", "Entrá a ARCA", "Revisalo".
- Botones con verbo y objeto: "Emitir factura", "Enviar a revisión", "Registrar recepción".
- Nada de "Registrarse": los usuarios los crea el administrador.
- Los roles se llaman: Administrador/Socio, Responsable de área, Empleado de Impuestos, Secretaría. Nunca "Senior".
- CUIT siempre enmascarado en las listas (30-••••••••-4).

## 6. Estados que hay que programar una vez y reutilizar

Cargando (barras grises), botón guardando, botón sin poder usarse, lista vacía, búsqueda sin resultados, error al cargar con "Reintentar", error de campo, aviso de "se guardó", cliente sin acceso, sesión vencida, ARCA no responde. Están en la pantalla 14.

## 7. Pantallas y de dónde sale cada una

| N° | Pantalla | Base en los documentos |
|---|---|---|
| 1 | Ingreso | RF-03 (los usuarios los crea el administrador) |
| 2 | Clientes | Cliente con varios CUIT y un responsable (Entrevista 3) |
| 3 | Ficha del cliente | RF-01, RF-02, RF-04; un IVA por CUIT |
| 4 | Panel de estado | RF-08; estados del IVA del plan; agrupado por día de vencimiento |
| 5 | Libros IVA | RF-09; fecha límite día 10 |
| 6 | Registrar recepción | RF-09; el control del CUIT del archivo depende del formato (pendiente) |
| 7 | Monotributo | RF-10; acumulado de 12 meses, porcentaje del tope, aviso anticipado |
| 8 | Nuevo cliente | RF-12; consulta por CUIT; varios CUIT por cliente |
| 9 | Usuarios | RF-03; los cuatro roles |
| 10 | Borrador de IVA | RF-06; estados Pendiente a Presentada |
| 11 | Aprobaciones | El socio aprueba antes de presentar (Entrevista 3) |
| 12 | Facturación | RF-11 |
| 13 | Emitir factura | RF-11; punto de venta habilitado por cliente |
| 14 | Estados | Reglas de la sección 6 |

## 8. Pantallas por diseñar (secundarias, se pueden quitar sin afectar el resto)

Se diseñan igual que las demás y se programan al final. Si no alcanza el tiempo o se decide no ofrecerlas, se retiran del menú sin tocar el resto del sistema.

- **Calendario de vencimientos.** Secundario según Diego. El sistema arma el calendario de cada cliente según la terminación del CUIT y los días hábiles, con feriados y prórrogas editables. Los empleados ya lo trabajan por su cuenta, así que es una ayuda extra, no el núcleo.
- **Convenio Multilateral (versión reducida).** Alcance a confirmar. Lo que Diego marcó como valioso es agilizar los papeles de trabajo: el sistema calcula la distribución de ingresos por provincia y arma el borrador y el papel de trabajo. La presentación en SIFERE la sigue haciendo la persona y se registra a mano en el panel. Todavía no se sabe qué tan lejos se puede llegar, y Diego pidió no abarcar de más.

Quedan fuera:
- Bandeja de comunicaciones de ARCA (descartada: las notificaciones ya llegan al estudio por mail).
- Una pantalla para administrar permisos. No hace falta mostrarla; el menú se ajusta solo según el área y el rol (sección 9).

## 9. Qué ve cada usuario según su área y su rol

Idea que planteó Diego: en el estudio hay empleados de distintas áreas (Impuestos, Laboral, Contabilidad y Auditoría, Secretaría). Quienes no son de Impuestos no deberían ver las pantallas del área impositiva. El sistema muestra en el menú solo lo que corresponde al área y al rol de quien ingresó, y bloquea el resto también en el servidor (no alcanza con ocultar el ítem).

Propuesta inicial, a validar con las empleadas en la reunión de la semana del 26 de octubre:

| Ítem del menú | Socio / Administrador | Responsable de área (Impuestos) | Empleado de Impuestos | Secretaría | Empleado de otras áreas |
|---|---|---|---|---|---|
| Clientes | Todos | Los del área | Solo los asignados | A definir | Sin acceso a este sistema |
| Panel de estado | Sí | Sí | Sus clientes | A definir | No |
| Libros IVA / Registrar recepción | Sí | Sí | Ver | Sí (recepción y reclamo) | No |
| Borrador de IVA | Sí | Sí | Sus clientes | No | No |
| Aprobaciones | Sí | No | No | No | No |
| Monotributo | Sí | A definir | No (lo ve Secretaría) | Sí | No |
| Facturación | Sí | A definir | No (lo ve Secretaría) | Sí | No |
| Calendario | Sí | Sí | Sí | A definir | No |
| Convenio Multilateral | Sí | Sí | Sí | No | No |
| Usuarios | Sí | No | No | No | No |

Notas:
- Diego explicó que Monotributo y facturación los hace Secretaría, no el área de Impuestos, y que Impuestos se dedica a liquidar los impuestos mensuales.
- Quedan abiertas dos cosas: si las otras áreas (Laboral, Contabilidad y Auditoría) necesitan al menos la lista de sus clientes y el botón "Entrar a ARCA" (Diego dijo que necesitan ver deudas y presentar algunas declaraciones), y qué ve exactamente Secretaría. No se deciden hasta hablar con ellos.
- El filtro por cliente asignado y por área se aplica en el backend. Cambiar los ítems del menú es solo una ayuda visual.

## 10. Para la etapa de código

1. Instalar Impeccable en Claude Code cuando esté creado el repositorio del frontend (no hace falta esperar la información de Diego) y generar PRODUCT.md y DESIGN.md a partir de este documento, usando los comandos de la propia herramienta para que queden en el formato que ella espera.
2. Pasar los colores y la tipografía a variables (tokens) una sola vez y reutilizarlas.
3. Programar primero los componentes de la sección 4 y los estados de la sección 6, y después las pantallas.
4. Armar el menú a partir de una tabla de permisos por área y rol (sección 9), para poder cambiarla sin tocar las pantallas.
5. Mostrar las pantallas a las empleadas en la reunión de la semana del 26 de octubre antes de programar los módulos que dependen de ellas.
