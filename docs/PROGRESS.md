# Estado del proyecto (fichero vivo)

Claude lo lee al empezar cada sesión y lo actualiza al cerrar cada slice.
Mantenerlo corto: es un puntero al estado real, no un diario exhaustivo.

## Estado actual

- Milestone: M0 (no empezado).
- Último slice completado: ninguno.
- Verificado con comandos: nada todavía.
- Siguiente paso propuesto: resolver el permiso `project` del token de `gh` (ver sección
  GitHub) y terminar `/bootstrap-github`; después, el primer slice de M0.

## Decisiones tomadas

| Fecha | Decisión | Motivo |
| --- | --- | --- |
| — | `nb_drones` = primera línea significativa (no física) | Los mapas oficiales anteponen comentarios |
| — | Claves de metadatos desconocidas → error | Un typo cambiaría rutas en silencio |
| — | Self-loops rechazados | No especificados por el subject |
| — | Salida ordenada por ID de dron ascendente | Determinismo y tests estables |
| — | Priority = desempate lexicográfico a coste igual | Ver SPEC_NOTES §3 |

## Preguntas abiertas

- Token textual exacto de la conexión en vuelo (`<origen>-<destino>`?). Fijar antes de M3.
- Ventana exacta de consumo de capacidad del enlace durante el tránsito restricted
  (¿un turno o los dos?). Fijar con tests en M3/M4.

## GitHub: qué se mueve solo y qué muevo a mano

`/bootstrap-github` se ejecutó parcialmente y quedó **pausado** (2026-07-18):

- Hecho: 7 labels creadas (`parser`, `sim`, `pathfinding`, `viz`, `ci`, `docs`, `epic`).
- Pendiente: Project v2, issues M0/M1, épicas M2-M6, protección de `main`.
- Bloqueante: `gh project create` falló por falta del scope `project`. El `gh` de este
  entorno se autentica con un token inyectado (`GITHUB_TOKEN`, tipo GitHub App), no con un
  login personal — `gh auth refresh -s project` no aplica a ese token. El permiso hay que
  concedérselo a la app/integración desde su origen (permisos del GitHub App instalado),
  no desde la terminal.
- Decisión: pausar el resto del bootstrap hasta resolver el permiso, para no dejar el
  repo con Project/issues a medias mientras se investiga.
- Automatizaciones del Project activas: — (Project no creado todavía)
- Automatizaciones que requieren clics en la web: — (pendiente de retomar)
- Movimientos manuales que me tocan a mí: revisar permisos del GitHub App instalado en el
  repo/cuenta y volver a lanzar `/bootstrap-github` cuando esté resuelto.

## Registro de sesiones (una línea por sesión)

| Fecha | Qué se hizo | Estado al cerrar |
| --- | --- | --- |
| — | — | — |
