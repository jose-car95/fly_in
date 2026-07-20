# Estado del proyecto (fichero vivo)

Claude lo lee al empezar cada sesión y lo actualiza al cerrar cada slice.
Mantenerlo corto: es un puntero al estado real, no un diario exhaustivo.

## Estado actual

- Milestone: M1 en progreso (M0 cerrado).
- Último slice completado: M1.1 — `parse_map()` convierte el mapa mínimo
  (`nb_drones` + `start_hub`/`end_hub`/`connection`) en `Zone`/`Connection`/`FlyInMap`.
  Solo camino feliz: sin metadatos, sin tipos de zona no-normal, sin validación de
  duplicados/capacidades — eso llega con sus propios tests en M1.2+.
- Verificado con comandos: `pytest` (1 passed), `flake8 .` (limpio), `mypy .` con los
  flags de `make lint` (sin errores, 8 ficheros fuente). `make lint` y `make test`
  también en verde tal cual los corre la CI.
- Siguiente paso propuesto: M1.2 — zonas `hub:` regulares (no start/end) y sus
  coordenadas.

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
| 2026-07-20 | Slice M1.1: parser del mapa mínimo (`flyin/domain`, `flyin/parsing`); fix de `pyproject.toml` (setuptools confundía `maps/` con un paquete) | CI real en verde (pytest/flake8/mypy) con el primer código del repo |
