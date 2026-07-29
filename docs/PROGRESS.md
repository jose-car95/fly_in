# Estado del proyecto (fichero vivo)

Claude lo lee al empezar cada sesión y lo actualiza al cerrar cada slice.
Mantenerlo corto: es un puntero al estado real, no un diario exhaustivo.

## Estado actual

- Milestone: M1 en progreso (M0 cerrado).
- Último slice completado: M1.4c — `max_link_capacity=` fija la capacidad de una
  conexión (sin tag → `None`, default 1). Se arregla la deuda de M1.2: los extremos se
  leen del texto ANTES del `[`, así el bloque `[...]` ya no se cuela en `zone_b`. Nuevo
  helper `_optional_int(metadata, key)` reutilizado por `max_drones` y
  `max_link_capacity`. Falta `color` (M1.4d) y claves desconocidas (M1.4e).
- Verificado con comandos: `pytest` (6 passed), `flake8 .` (limpio, límite 79),
  `mypy .` con los flags de `make lint` (sin errores, 8 ficheros fuente). `make lint`
  y `make test` también en verde tal cual los corre la CI.
- Siguiente paso propuesto: M1.4d — `color=` (decidir si se guarda para la
  visualización de M6 o se ignora; hoy no hay campo `color` en el dominio).

## Decisiones tomadas

| Fecha | Decisión | Motivo |
| --- | --- | --- |
| — | `nb_drones` = primera línea significativa (no física) | Los mapas oficiales anteponen comentarios |
| — | Claves de metadatos desconocidas → error | Un typo cambiaría rutas en silencio |
| — | Self-loops rechazados | No especificados por el subject |
| — | Salida ordenada por ID de dron ascendente | Determinismo y tests estables |
| — | Priority = desempate lexicográfico a coste igual | Ver SPEC_NOTES §3 |
| 2026-07-26 | Split `backend/` + `frontend/` con Makefile orquestador en la raíz | Objetivo de aprendizaje decidido (infra completa backend+frontend); mover cuesta menos con el repo pequeño y solo crece con el tiempo |
| 2026-07-26 | API (FastAPI) + UI (React) confirmadas como extensión post-mandatory | Aprender REST/frontend de verdad; se hacen DESPUÉS del CLI obligatorio (mandatory-first de 42) |
| 2026-07-26 | Full-OOP: el comportamiento va en clases, no en funciones sueltas. Parser → clase `MapParser` (hecho) | El subject exige OOP explícito; funciones de módulo con estado son un riesgo en el peer review. Regla fina en `CLAUDE.md` |
| 2026-07-26 | `MapParser`: texto en el constructor, `parse()` sin args (una instancia = un parseo) | Prepara el estado de instancia para números de línea en errores (M1.3); reutilizar la instancia ensuciaría estado, así que es de un solo uso |
| 2026-07-28 | M1.2: los metadatos `[...]` de las líneas de zona se IGNORAN, no se rechazan | Todos los mapas oficiales los llevan; rechazarlos bloquearía el parseo. Se interpretan en M1.4 con sus propios tests |

## Roadmap de arquitectura (cuándo nace cada carpeta y por qué)

Las carpetas emergen cuando el código las justifica, no de forma especulativa. La
frontera raíz (`backend/`↔`frontend/`) ya existe; las internas siguen este mapa:

| Nace en | Carpeta | Por qué nace ahí |
| --- | --- | --- |
| M1 (hecho) | `backend/flyin/domain`, `.../parsing` | Entidades puras; entrada texto→dominio |
| M1.9 | `shared/exceptions.py` | Cuando los errores de parseo se repiten y piden un tipo común |
| M2 | `pathfinding` | Grafo propio + algoritmos de rutas |
| M3 | `simulation` (motor `simulate()`) + `cli` | La costura reusable + su primer cliente |
| M4 | `scheduling` | Reservas de capacidad/tiempo |
| M5 | `benchmark` | Comparar algoritmos / métricas |
| Post-mandatory | `api` (FastAPI) | 2º cliente del motor: frontera REST |
| Post-mandatory | `visualization` | Cuando haya un 2º renderer además del CLI |
| Último | `frontend/` (React) | Consumir el JSON de la API; cero lógica de negocio |

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
| 2026-07-20 | Diagnóstico de CI roja (M0 sin código, esperado); verificado que el bootstrap de GitHub ya está completo (estaba mal anotado como pausado); añadido rol de profesor y regla de variables globales a `CLAUDE.md`; versionados subject PDF y maps.tar.gz; renombrado Mario→Jose en todo el repo | M0 no empezado |
| 2026-07-20 | Slice M1.1: parser del mapa mínimo (`flyin/domain`, `flyin/parsing`); fix de `pyproject.toml` (setuptools confundía `maps/` con un paquete) | CI real en verde (pytest/flake8/mypy) con el primer código del repo |
| 2026-07-26 | Pase de convenciones: docstrings Google style + comentarios en inglés en todo el código, `__init__.py` con docstring de paquete, prefijos de parseo agrupados en `LinePrefix(str, Enum)`; aclarado constante-vs-global en `CLAUDE.md` y añadida sección de convenciones de doc | lint/type/test en verde; sin cambios de comportamiento |
| 2026-07-26 | Split físico `backend/` + `frontend/`: movido el paquete Python a `backend/` (git mv, historial intacto), Makefile orquestador en la raíz, `frontend/README` puerta; registrada la decisión y el roadmap de carpetas. PR apilada (stacked) sobre la de convenciones | lint/type/test en verde vía orquestador; CI sin cambios (llama a make desde la raíz) |
| 2026-07-26 | Reglas full-OOP y estilo de enseñanza en `CLAUDE.md` (#29). Refactor del parser a clase `MapParser` (texto en constructor, `parse()`); test actualizado a la nueva interfaz | lint/type/test en verde; refactor sin cambios de comportamiento |
| 2026-07-28 | Norma de 42: límite duro de 79 caracteres por línea. `flake8` `max-line-length = 79`, reformateado `map_parser.py`/`connection.py`, regla no negociable añadida a `CLAUDE.md`. Va en la PR #30 | lint/type/test en verde; sin cambios de comportamiento |
| 2026-07-28 | Slice M1.2 (#6): `hub:` intermedios → `Zone` NORMAL; `_parse_zone` toma los 3 primeros trozos e ignora los metadatos `[...]` (arregla la deuda de M1.1 con corchetes en start/end); fixture `valid_with_hub.txt` | pytest 2 passed, lint/type en verde |
| 2026-07-28 | Root Makefile de dos niveles (`clean`/`fclean` barren la raíz además de delegar en backend) + regla `re`; quitados `build`/`dist`/`egg-info` de ambos fclean (nunca se generan con `package = false`); estilo escueto sin comentarios (#32) | `make re` + `make quality` en verde desde cero |
| 2026-07-29 | Slice M1.3 (#7): números de línea físicos 1-based en errores. `_significant_lines` → pares `(línea, texto)` con `enumerate`+morsa; error de `nb_drones` con `line N:`; fixture `invalid_missing_nb_drones.txt` | pytest 3 passed, lint/type en verde |
| 2026-07-29 | Slice M1.4a (#8, parte 1/5): `zone=` → `ZoneType` con default `normal` y orden libre; helper `_parse_metadata` (bloque `[...]` → dict); `color`/`max_drones` aún ignorados; fixture `valid_zone_types.txt` | pytest 4 passed, lint/type en verde |
| 2026-07-29 | Slice M1.4b (#8, parte 2/5): `max_drones=` → capacidad de zona, ignorado en terminales; test de M1.2 actualizado a `max_drones=2`; fixture `valid_zone_capacity.txt` | pytest 5 passed, lint/type en verde |
| 2026-07-29 | Slice M1.4c (#8, parte 3/5): `max_link_capacity=` → capacidad de conexión; arreglada la deuda de M1.2 (extremos leídos antes del `[`); helper `_optional_int` reutilizado; fixture `valid_link_capacity.txt` | pytest 6 passed, lint/type en verde |
