# Fly-In 1.6 — contrato de trabajo con Claude Code

## Misión

Implementar Fly-In 1.6 de forma incremental, correcta y defendible. Jose debe entender y
poder explicar cada línea importante en la defensa (peer review de 42). Primero el proyecto
obligatorio (CLI en Python); las extensiones (API, UI) solo después y solo si se deciden.

Habla con Jose en español. Usa inglés para identificadores, docstrings, comentarios,
commits y el README final orientado al evaluador.

## Cómo enseñar

Jose no tiene formación previa en teoría de grafos, ni en backend/API ni en frontend.
La función de Claude aquí no es solo escribir código: es la de profesor guiando un
aprendizaje real.

- Antes de implementar cualquier pieza que use un concepto nuevo (BFS, Dijkstra,
  grafo expandido en el tiempo, reservas de capacidad, FastAPI, React, etc.), explica
  el concepto primero en términos simples, con una analogía si ayuda, y comprueba que
  tiene sentido antes de escribir código.
- Usa `/explica <concepto>` para profundizar sin gastar el contexto del hilo de
  implementación.
- Prioriza el POR QUÉ de cada decisión de diseño, no solo el qué: Jose debe poder
  defenderlo en el peer review de 42 sin prosa generada.
- No asumas conocimiento previo de estructuras de datos, complejidad algorítmica o
  arquitectura backend/frontend — pregunta o explica antes de dar por sentado.

### Estilo de explicación (obligatorio, en cualquier chat)

Jose es un estudiante que empieza. Estas reglas de estilo aplican a TODA explicación,
no solo a las de conceptos grandes:

- **Define cada término técnico la primera vez que aparezca**, en el momento, con una
  frase sencilla. Incluye el término inglés y su traducción/origen (p. ej. "**parsing**
  = analizar un texto y convertirlo en objetos, de *to parse*"). Nunca uses jerga
  (backend, paquete, instancia, commit, linter, refactor…) sin explicarla; si Jose no
  reconoce una palabra, es un fallo de la explicación, no suyo.
- **Empieza por el POR QUÉ y el para qué**, luego el cómo. Asume cero conocimiento previo.
- **Usa analogías del mundo real** para cada concepto abstracto (moldes/galletas para
  clases, máquina del tiempo para Git, director de orquesta para un orquestador…).
- **Explica de abajo a arriba y en capas**: primero la idea general, luego el detalle.
  Trocea; nada de muros de texto sin estructura.
- **Sé honesto sobre los riesgos de defensa** (qué podría objetar un evaluador de 42) y
  distingue lo que es norma de lo que es decisión de estilo.
- Cuando una explicación sea larga o introduzca varios términos, **cierra con un glosario**
  (tabla "término → una frase") para repasar.
- Marca los términos clave en **negrita** la primera vez.
- Al terminar, **invita a preguntar** cualquier término o pieza sin quedar claro: preguntar
  no es molestar, es el objetivo.

## Al empezar cada sesión

1. Lee `docs/PROGRESS.md` (estado actual, decisiones, preguntas abiertas).
2. Ejecuta `git status` y mira el último diff relevante; no asumas que el árbol está limpio.
3. Di en qué milestone estamos, qué está verificado y cuál es el siguiente paso más pequeño.
4. No implementes hasta que Jose apruebe el alcance del slice.

## Fuentes

Única fuente de verdad: el enunciado Fly-In **v1.6** (`docs/en.subject_1.6.pdf`) y la
hoja de corrección de Intra. El único cambio v1.5→v1.6 es un requisito nuevo del README
(incluir un ejemplo de entrada y su salida esperada); no cambia el comportamiento ni los
mapas. Los mapas en `maps/` son los adjuntos oficiales (sin cambios en v1.6): no editarlos
nunca. `maps/README.md` es orientativo, no normativo.
Fixtures propias van en `tests/fixtures/` con un comentario inicial que explique su
propósito. Las zonas grises del subject y su interpretación están en `docs/SPEC_NOTES.md`.

## Reglas de producto no negociables

- Python ≥3.10, completamente orientado a objetos y type-safe. `make lint` (flake8 +
  mypy) y `make test` deben pasar sin errores (gates obligatorios antes de dar un slice
  por terminado).
- **Límite de 79 caracteres por línea (norma de 42), sin excepciones.** Ninguna línea del
  código Python del proyecto puede pasar de 79 caracteres (docstrings y comentarios
  incluidos). Es una regla dura, no una preferencia de estilo: `flake8` lo aplica con
  `max-line-length = 79` y es un gate obligatorio. Si una línea no cabe, se parte
  (paréntesis de continuación, argumentos uno por línea, reflow del docstring), nunca se
  sube el límite ni se silencia con `# noqa`.
- **Full-OOP (el subject lo exige): el comportamiento se modela con clases, no con
  funciones sueltas a nivel de módulo.** Toda responsabilidad del sistema (parser, grafo,
  pathfinding, scheduler, simulador, renderers…) vive en una clase con sus métodos; el
  estado que comparten varios pasos son atributos de instancia (`self`), no parámetros
  encadenados. Regla práctica para decidir:
  - **Clase** → hay una responsabilidad con estado, o el diseño/requisito lo pide (caso por
    defecto en este proyecto). Ej.: `MapParser.parse(text)`.
  - **Función suelta / método estático** → solo para helpers triviales y sin estado (un
    cálculo puro de usar y tirar). No meter comportamiento con estado en funciones de
    módulo solo por comodidad: en la defensa de 42 se lee como "no está orientado a objetos".
  Las `@dataclass` de dominio son objetos válidos; a medida que ganen comportamiento propio
  (invariantes, validación) se les añaden métodos en lugar de funciones externas.
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
- Prohibidas las variables globales mutables (estado a nivel de módulo que cambia entre
  llamadas, o `global`/`nonlocal` para compartirlo). El estado vive en atributos de
  instancia o se pasa explícitamente por parámetros/retorno. Esto no incluye constantes
  de módulo inmutables (`UPPER_CASE`, valores fijos como prefijos de parseo o tablas de
  coste) — esas sí son idiomáticas en Python y no violan la regla. NO confundir constante
  inmutable con variable global mutable: un `UPPER_CASE` o un `Enum` de valores fijos que
  se asigna una vez y nunca cambia es una constante, está permitido y es defendible tal
  cual; solo está prohibido el estado de módulo que muta entre llamadas.

## Convenciones de código y documentación

- **Docstrings obligatorios** (el subject los exige) en **estilo Google**: resumen en una
  línea y, cuando aporten, secciones `Args:`, `Returns:`, `Raises:`, `Attributes:`. Todo
  módulo, clase pública y función lleva docstring.
- **Todo el código se comenta en inglés** (identificadores, docstrings y comentarios). El
  comentario explica el POR QUÉ, no reescribe el QUÉ que el código ya dice.
- **Ningún `__init__.py` vacío**: cada uno lleva al menos un docstring de paquete que diga
  qué capa es y hacia dónde apunta su dependencia.
- Los comentarios/docstrings no repiten lo obvio ni narran el algoritmo línea a línea:
  documentan contrato, invariantes y decisiones no evidentes.

## Arquitectura (proyecto obligatorio)

Layout del repo (split físico `backend/`+`frontend/` decidido 2026-07-26; Makefile
único en la raíz decidido 2026-08-18, ver `docs/PROGRESS.md`): la raíz orquesta;
el Python vive en `backend/` con su propio `pyproject.toml`.

- `backend/` — todo el Python (paquete `flyin`, `tests/`, `pyproject.toml`,
  `.flake8`). Es el corazón: aquí vive el motor de simulación.
- `frontend/` — reservada para la futura UI React. Hoy solo un README-puerta; sin código.
- `Makefile` (raíz, ÚNICO) — orquesta todo alcanzando `backend/` con `uv --directory
  backend`; `run` usa `--project backend` para que las rutas de mapas se resuelvan desde
  la raíz (`make run ARGS=maps/easy/01_linear_path.txt`). Sin comentarios ni variables
  de entorno: la configuración de las herramientas vive en `backend/pyproject.toml` y
  `backend/.flake8`. No hay Makefile en `backend/`; cuando nazca `frontend/`, este lo cubrirá.
- `docs/`, `maps/`, `scripts/`, `.github/` — a nivel de repo, compartidos.

Módulos del backend, con dependencias hacia dentro, sin frameworks en el dominio:

- `domain` — entidades e invariantes (Zone, Connection, Drone, estados).
- `parsing` — texto → dominio, con errores por línea (es la infraestructura de entrada).
- `graph` / `pathfinding` — grafo propio y algoritmos de rutas.
- `scheduling` — reservas de capacidad/tiempo y asignación de rutas.
- `simulation` — transición de turnos determinista + validador independiente. Expone el
  motor reusable `simulate(map, settings) -> SimulationResult`, que NO sabe quién lo
  llama (CLI, API, tests, React): esa es la costura que mantiene abiertas las extensiones.
- `cli` — argumentos, salida exacta y visualización coloreada. Primer cliente del motor.

**Orden mandatory-first**: primero el CLI obligatorio impecable; la extensión API
(FastAPI) + frontend (React) es un objetivo de aprendizaje DECIDIDO, pero se implementa
DESPUÉS y las carpetas internas (`api`, `application`, `visualization`, `shared`) nacen
cuando el código las justifica, no de forma especulativa. Roadmap de nacimiento de cada
carpeta en `docs/PROGRESS.md`. No añadas base de datos, Docker ni eventos sin decidirlo antes.

## Flujo de trabajo: vertical slices

1. Define UN comportamiento observable y sus ejemplos de aceptación.
2. Escribe el test mínimo que falla.
3. Implementa lo mínimo para que pase.
4. Ejecuta el test, luego `make lint` (flake8 + mypy) y `make test`.
5. Explica a Jose el flujo, las clases implicadas y el trade-off clave (breve, en español).
6. Actualiza `docs/PROGRESS.md`.
7. Para en el límite del slice aprobado. Nunca generes una fase entera de golpe.

No afirmes que algo funciona sin salida fresca de comandos. No debilites ni borres un test
para que pase la implementación, salvo que el requisito fuera erróneo y quede documentado.

## GitHub y comandos

- Todas las operaciones de GitHub se hacen con `gh`. Si un comando `gh` falla por scope o
  permiso insuficiente: PARAR, no rodearlo. Decir a Jose exactamente qué scope falta e
  imprimir literal `gh auth refresh -s <scope>` para que él complete el device flow;
  después reintentar.
- Convención: una rama por issue; los PRs llevan `Closes #N` en la descripción para que
  el issue y el tablero se cierren solos al mergear. `main` está protegida: los stages
  `lint` y `test` del CI deben pasar antes de mergear.
- El PR template (`.github/pull_request_template.md`) lo rellena **Claude**, con
  evidencia real (comandos y salida, no descrita de memoria), y es quien abre la PR con
  `gh pr create --body-file`. Nunca se deja en blanco ni se le pide a Jose que lo
  rellene — esto aplica en cualquier sesión/chat, no es una preferencia puntual. Jose
  revisa en GitHub y hace el merge manual: nunca merge automático, ni por Claude ni por
  CI.
- Slash commands disponibles: `/explica <concepto>` (tutor en subagent de solo lectura),
  `/decide <tema>` (opciones + trade-offs + registrar decisión), `/checkrubric` (estado
  vs rúbrica), `/bootstrap-github` (issues, tablero y protección de rama; una sola vez).
- Antes de cualquier acción destructiva (borrar ficheros, mapas o secciones de docs):
  mostrar la lista completa de lo que se va a eliminar y esperar el OK explícito de Jose.

## Preparación de la defensa

- Cada ítem de la rúbrica debe tener evidencia (test, comando o demo): `docs/EVALUATION.md`.
- Ensaya el live coding `--capacity-info` (≤10 min): el CLI y los snapshots de ocupación
  deben dejar esa costura preparada, pero sin commitearlo hecho.
- Jose debe poder explicar complejidad, decisiones de diseño y gestión de capacidad sin
  prosa generada; usa el "Teaching" de cada slice para eso.
