# Fly-In 1.5 — contrato de trabajo con Claude Code

## Misión

Implementar Fly-In 1.5 de forma incremental, correcta y defendible. Mario debe entender y
poder explicar cada línea importante en la defensa (peer review de 42). Primero el proyecto
obligatorio (CLI en Python); las extensiones (API, UI) solo después y solo si se deciden.

Habla con Mario en español. Usa inglés para identificadores, docstrings, comentarios,
commits y el README final orientado al evaluador.

## Al empezar cada sesión

1. Lee `docs/PROGRESS.md` (estado actual, decisiones, preguntas abiertas).
2. Ejecuta `git status` y mira el último diff relevante; no asumas que el árbol está limpio.
3. Di en qué milestone estamos, qué está verificado y cuál es el siguiente paso más pequeño.
4. No implementes hasta que Mario apruebe el alcance del slice.

## Fuentes

Única fuente de verdad: el enunciado Fly-In **v1.5** y la hoja de corrección de Intra
(ambos en los ficheros del Proyecto de Claude). Los mapas en `maps/` son los adjuntos
oficiales v1.5: no editarlos nunca. `maps/README.md` es orientativo, no normativo.
Fixtures propias van en `tests/fixtures/` con un comentario inicial que explique su
propósito. Las zonas grises del subject y su interpretación están en `docs/SPEC_NOTES.md`.

## Reglas de producto no negociables

- Python ≥3.10, completamente orientado a objetos y type-safe. `mypy .` y `flake8 .` deben
  pasar sin errores (gates obligatorios antes de dar un slice por terminado).
- Prohibido networkx, graphlib o cualquier librería de grafos/pathfinding.
- Coste de movimiento según el **destino**: normal/priority = 1 turno, restricted = 2,
  blocked = intransitable.
- Tránsito hacia zona restricted: el dron ocupa la conexión un turno y DEBE llegar al
  siguiente; no puede esperar en la conexión → la salida solo es legal si la capacidad del
  destino está reservada para el turno de llegada.
- Capacidades por defecto = 1 (zona y conexión). `max_drones` en start/end se ignora sin
  error (capacidad ilimitada). Conexiones bidireccionales; `a-b` y `b-a` son duplicados.
- Los drones que salen de una zona liberan capacidad ese mismo turno (evaluar salidas antes
  que entradas). El plan de turno se aplica de forma atómica: la corrección nunca puede
  depender del orden de iteración de los drones.
- stdout obligatorio: una línea por turno, tokens `D<ID>-<zona>` o `D<ID>-<conexión>`,
  drones parados omitidos, fin al entregar todos. Visualización/métricas nunca contaminan
  ese stdout (flag aparte o stderr).
- Errores de parseo: parar el programa con mensaje claro indicando línea (física, 1-based)
  y causa.
- Interpretación de las zonas grises del subject: `docs/SPEC_NOTES.md`.

## Arquitectura (proyecto obligatorio)

Módulos con dependencias hacia dentro, sin frameworks en el dominio:

- `domain` — entidades e invariantes (Zone, Connection, Drone, estados).
- `parsing` — texto → dominio, con errores por línea.
- `graph` / `pathfinding` — grafo propio y algoritmos de rutas.
- `scheduling` — reservas de capacidad/tiempo y asignación de rutas.
- `simulation` — transición de turnos determinista + validador independiente.
- `cli` — argumentos, salida exacta y visualización coloreada.

No añadas API, eventos, base de datos, Docker ni frontend de forma especulativa. Si algún
día se cruza esa frontera, se decide antes y se anota en `docs/PROGRESS.md`.

## Flujo de trabajo: vertical slices

1. Define UN comportamiento observable y sus ejemplos de aceptación.
2. Escribe el test mínimo que falla.
3. Implementa lo mínimo para que pase.
4. Ejecuta el test, luego `make lint`, `make type`, `make test`.
5. Explica a Mario el flujo, las clases implicadas y el trade-off clave (breve, en español).
6. Actualiza `docs/PROGRESS.md`.
7. Para en el límite del slice aprobado. Nunca generes una fase entera de golpe.

No afirmes que algo funciona sin salida fresca de comandos. No debilites ni borres un test
para que pase la implementación, salvo que el requisito fuera erróneo y quede documentado.

## GitHub y comandos

- Todas las operaciones de GitHub se hacen con `gh`. Si un comando `gh` falla por scope o
  permiso insuficiente: PARAR, no rodearlo. Decir a Mario exactamente qué scope falta e
  imprimir literal `gh auth refresh -s <scope>` para que él complete el device flow;
  después reintentar.
- Convención: una rama por issue; los PRs llevan `Closes #N` en la descripción para que
  el issue y el tablero se cierren solos al mergear. `main` está protegida: los stages
  `lint` y `test` del CI deben pasar antes de mergear.
- Slash commands disponibles: `/explica <concepto>` (tutor en subagent de solo lectura),
  `/decide <tema>` (opciones + trade-offs + registrar decisión), `/checkrubric` (estado
  vs rúbrica), `/bootstrap-github` (issues, tablero y protección de rama; una sola vez).
- Antes de cualquier acción destructiva (borrar ficheros, mapas o secciones de docs):
  mostrar la lista completa de lo que se va a eliminar y esperar el OK explícito de Mario.

## Preparación de la defensa

- Cada ítem de la rúbrica debe tener evidencia (test, comando o demo): `docs/EVALUATION.md`.
- Ensaya el live coding `--capacity-info` (≤10 min): el CLI y los snapshots de ocupación
  deben dejar esa costura preparada, pero sin commitearlo hecho.
- Mario debe poder explicar complejidad, decisiones de diseño y gestión de capacidad sin
  prosa generada; usa el "Teaching" de cada slice para eso.
