# Estado del proyecto (fichero vivo)

Claude lo lee al empezar cada sesión y lo actualiza al cerrar cada slice.
Mantenerlo corto: es un puntero al estado real, no un diario exhaustivo.

## Estado actual

- Milestone: M0 (no empezado).
- Último slice completado: ninguno.
- Verificado con comandos: nada todavía. CI en rojo confirmado por causa esperada (cero
  ficheros `.py`: `mypy` no tiene nada que revisar, `pytest` no colecciona tests) — no es
  un bug, es M0 sin empezar.
- Siguiente paso propuesto: rellenar `<login>` en la primera línea de `README.md`, y
  después el primer slice de M0 (test rojo parseando `valid_minimal.txt`).

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

`/bootstrap-github` está **completo** (verificado 2026-07-20, corrige el estado
"pausado" anotado el 2026-07-18 — el bloqueo del scope `project` ya no existe: el token
actual de `gh` sí lo tiene):

- Hecho: 7 labels (`parser`, `sim`, `pathfinding`, `viz`, `ci`, `docs`, `epic`).
- Hecho: Project v2 "Fly-In" (`PVT_kwHOCIxH9M4BdxIv`), con campo propio
  `Flyin Milestone` (renombrado de `Milestone`, nombre reservado por GitHub — ver
  commit `f719986`).
- Hecho: 18 issues — M0 (#3, #4), M1.1–M1.9 (#5–#13), 2 decisiones abiertas como issues
  (#14, #15), épicas M2–M6 (#16–#20). Los 18 están en el board, columna `Todo`.
- Hecho: protección de `main` con `required_status_checks` (`lint`, `test`, strict).
- Pendiente/decisión abierta: `enforce_admins` está en `false` — como único admin, Jose
  puede mergear aunque la CI esté en rojo (así se colaron los merges de las PRs #1/#2/#21
  con CI roja). Decidir si se activa `enforce_admins` una vez el primer slice de M0 deje
  la CI en verde, para que la protección sea real.
- Movimientos manuales que le tocan a Jose: ninguno pendiente del bootstrap en sí.
  Sigue pendiente rellenar `<login>` en `README.md` (dato personal, no soy quien decide
  el valor).

## Registro de sesiones (una línea por sesión)

| Fecha | Qué se hizo | Estado al cerrar |
| --- | --- | --- |
| 2026-07-20 | Diagnóstico de CI roja (M0 sin código, esperado); verificado que el bootstrap de GitHub ya está completo (estaba mal anotado como pausado); añadido rol de profesor a `CLAUDE.md`; versionados subject PDF y maps.tar.gz | M0 no empezado; a la espera de aprobar el primer slice |
