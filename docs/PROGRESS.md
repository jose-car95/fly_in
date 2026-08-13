# Estado del proyecto (fichero vivo)

Claude lo lee al empezar cada sesión y lo actualiza al cerrar cada slice.
Mantenerlo corto: es un puntero al estado real, no un diario exhaustivo.

## Estado actual

- Milestone: **M3 en progreso** (M0, M1, M2 cerrados). Motor + CLI + capas + warnings.
- Último slice completado: M3.6 — máquina de estados del dron explícita. `Simulator.run()`
  deja de recorrer pares de zonas (hop-driven) y pasa a un bucle por turnos (turn-driven):
  una vuelta = un turno = una línea. Nace el `Enum` `DroneState` (`AT_ZONE`, `IN_TRANSIT`,
  `DELIVERED`); el estado decide la transición (restricted se parte en despegue IN_TRANSIT +
  aterrizaje). Salida idéntica (refactor, no cambio de comportamiento): la red son los tests
  del `Simulator` + el `ScheduleValidator`. Test nuevo: la salida del motor pasa por el
  validador independiente (las dos piezas de M3 se comprueban mutuamente). La transición
  atómica `SimulationState → TurnPlan → SimulationState` se difiere a M4 (sin varios drones
  no hay contención que arbitrar; ver decisión).
- Anteriores (breve): M3.5 `ScheduleValidator` independiente (`position`+`in_flight_to`,
  adyacencia propia, `InvalidScheduleError`) · M3.4 tránsito restricted de 2 turnos en
  `Simulator.run()` (token en
  vuelo `D1-<origen>-<destino>` + llegada) · M3.3 `SolveResult(movement_lines, warnings)` +
  normalización de terminal `restricted`→`normal` con warning · M3.2 capa de aplicación
  (`FlyinSolver`) +
  adaptadores (`adapters/cli`, clase `Cli`) · M3.1 motor `Simulator` (`D1-<zona>`,
  `UnsolvableMapError`) · M2 grafo + Dijkstra `(turnos,−nº_priority)` + complejidad
  documentada · M1 parser completo (`MapParseError`) · M0 entorno/CI. Detalle en el
  registro de sesiones y en la tabla de decisiones.
- Verificado con comandos: `pytest` (53 passed), `flake8 .` (limpio, límite 79),
  `mypy .` con los flags de `make lint` (sin errores, 33 ficheros). `make lint` y
  `make test` en verde como en la CI.
- Siguiente paso propuesto: **M4** (multi-dron): colas, capacidad de zona/enlace, y la
  transición atómica `SimulationState → TurnPlan → SimulationState` diferida en M3.6 —
  el plan de turno se aplica de forma atómica para que la corrección no dependa del orden
  de iteración de los drones. Incluye la reserva futura de la llegada restricted (decisión
  abierta #15: ventana de capacidad del enlace, fijar con `/decide` antes de implementar).

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
| 2026-08-01 | M1.4d: `color=` se GUARDA en `Zone.color` (no se ignora) | El parser es el único lector del mapa y M6 exige la vista coloreada; capturarlo ahora (1 campo opcional) evita re-tocar el parser en M6. Coste: campo sin uso hasta M6 |
| 2026-08-03 | M1.4e: claves de metadatos válidas POR CONTEXTO (zona vs conexión), no una lista global | Una clave válida en el sitio equivocado (p.ej. `max_link_capacity` en una zona) se ignoraría en silencio; el objetivo del slice es justo evitar ese error mudo. Coste: dos `frozenset` en vez de uno |
| 2026-08-04 | M1.5: las conexiones se validan en dos pasadas (tras leer todo el mapa), no sobre la marcha | El subject no fija que las zonas se definan antes que las conexiones; validar al final acepta cualquier orden y solo rechaza referencias realmente rotas. Coste: guardar el nº de línea de cada conexión para el error |
| 2026-08-04 | M1.6: self-loops (`a-a`) se rechazan aquí, cerrando la decisión de SPEC_NOTES que ningún slice implementaba | Misma zona de código que el duplicado (bien-formación de conexión); error propio más claro que dejarlo caer en el check de duplicado. Coste: un `if a == b` y un test/fixture |
| 2026-08-04 | M1.7: el coste de movimiento vive en `ZoneType.move_cost` (dominio), no en el grafo | La tabla de coste es una FACT del subject que depende solo del tipo; ponerla en el enum la deja lista para que M2 solo la consuma. `blocked=None` codifica intransitable sin una segunda propiedad |
| 2026-08-04 | M1.8: la validación de capacidad ≥1 vive en `_optional_capacity`, no en cada llamador | Único punto por donde pasan `max_drones` y `max_link_capacity`; validar ahí lo cubre para ambos. El orden ignorar-antes-de-validar deja el 0 terminal como no-error sin código extra |
| 2026-08-04 | M1.9: `MapParseError` hereda de `Exception`, no de `ValueError` | Así el `try/except ValueError` envolvente no captura los errores propios del parser (sin doble-envoltura); a cambio se migran los tests a `pytest.raises(MapParseError)`, que además quedan más precisos |
| 2026-08-04 | M1.9: un único `try/except` por línea en vez de blindar cada `int()`/unpack | Convierte cualquier excepción cruda de línea malformada en `MapParseError` con línea en un solo sitio; guardianes explícitos solo donde hay bug silencioso o cabe un mensaje más claro |
| 2026-08-04 | Un solo tipo `MapParseError` ahora; código (enum) + atributos estructurados solo cuando llegue la API | El único caller (CLI) maneja todos los errores igual (imprime y para); el detalle vive en el mensaje. Subclases o códigos legibles por máquina solo se justifican si un caller reacciona distinto o la API los serializa como datos — YAGNI hasta entonces. `MapParseError` como base deja esa evolución abierta y aditiva |
| 2026-08-04 | M2: un único Dijkstra, sin BFS suelto | El grafo es ponderado (restricted=2), así que el camino mínimo es por coste → Dijkstra, no BFS. Dijkstra además da la alcanzabilidad gratis (end en coste infinito → mapa no resoluble), así que un BFS aparte para eso sería código redundante. BFS se usa como modelo mental para explicar Dijkstra, no se implementa |
| 2026-08-12 | M3.2: el mapa entra como fichero-argumento; el núcleo es agnóstico a la fuente | El subject no fija stdin vs argumento; argumento es explícito, da mejores errores y encaja con un futuro menú de mapas. El motor recibe texto/objetos, así que futuras fuentes (stdin, menú, API, HTML) son adaptadores nuevos sin tocar el núcleo (puertos y adaptadores) |
| 2026-08-12 | Introducir la capa de aplicación (`FlyinSolver`) YA, con un solo llamador (el CLI), en vez de esperar al 2º adaptador | Decisión de Jose: inversión de aprendizaje para entender las capas y dejar la costura lista para la API (consumidor futuro decidido). Se asume el "coste YAGNI" (abstracción con un cliente) a cambio de la claridad arquitectónica; la implementación se mantiene mínima (adaptador fino + orquestador fino) |
| 2026-08-12 | Capa `adapters/` (con `cli/` dentro) y el CLI como CLASE, no función | La familia de adaptadores (cli, api, frontend) está decidida → agrupar bajo `adapters/` hace visible la capa de presentación sin ser especulativo. El CLI vuelve a clase para respetar el contrato full-OOP (defendible en 42) |
| 2026-08-12 | #14: el token de conexión en vuelo usa `origen-destino` → `D<ID>-<origen>-<destino>` | Refleja la dirección del viaje (de dónde viene, a dónde va), es determinista y es la propuesta por defecto de SPEC_NOTES. El subject no fija la forma; origen-destino es la más informativa |
| 2026-08-13 | M3.6: máquina de estados del dron con `Enum` `DroneState`, no un `bool in_flight` | El subject pide "máquina de estados explícita"; el enum nombra los estados y se defiende mejor en 42. Coste: ~6 líneas sobre el bool equivalente |
| 2026-08-13 | M3.6: se difiere la transición atómica `SimulationState → TurnPlan → SimulationState` a M4 | Con un solo dron no hay contención de capacidad que arbitrar; construir el `TurnPlan` atómico ahora sería abstracción especulativa (ponytail). Se hace turn-driven ahora (la costura que M4 rellena) y la atomicidad llega cuando varios drones la hacen real |

## Roadmap de arquitectura (cuándo nace cada carpeta y por qué)

Las carpetas emergen cuando el código las justifica, no de forma especulativa. La
frontera raíz (`backend/`↔`frontend/`) ya existe; las internas siguen este mapa:

| Nace en | Carpeta | Por qué nace ahí |
| --- | --- | --- |
| M1 (hecho) | `backend/flyin/domain`, `.../parsing` | Entidades puras; entrada texto→dominio |
| M1.9 (hecho) | `shared/exceptions.py` | Nació con `MapParseError`: los errores de parseo se repetían y pedían un tipo común |
| M2.1 (hecho) | `graph` | La adyacencia transitable propia, sin librerías |
| M2.2 (hecho) | `pathfinding` | Dijkstra sobre el grafo (camino de menor coste + resoluble) |
| M3.1 (hecho) | `simulation` (motor `Simulator`) | La costura reusable de simulación |
| M3.2 (hecho) | `application` (`FlyinSolver`) + `adapters/cli` | Caso de uso + su primer adaptador |
| M4 | `scheduling` | Reservas de capacidad/tiempo |
| M5 | `benchmark` | Comparar algoritmos / métricas |
| Post-mandatory | `api` (FastAPI) | 2º cliente del motor: frontera REST |
| Post-mandatory | `visualization` | Cuando haya un 2º renderer además del CLI |
| Último | `frontend/` (React) | Consumir el JSON de la API; cero lógica de negocio |

## Preguntas abiertas

- Ventana exacta de consumo de capacidad del enlace durante el tránsito restricted
  (¿un turno o los dos?). Fijar con tests en M3/M4 (decisión abierta #15).

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
| 2026-08-01 | Slice M1.4d (#8, parte 4/5): `color=` → nuevo campo `Zone.color` (string libre, visual para M6); DECISIÓN guardarlo vs ignorarlo; test de metadatos actualizado con colores; fixture `valid_zone_color.txt` | pytest 7 passed, lint/type en verde |
| 2026-08-03 | Slice M1.4e (#8, parte 5/5): claves de metadatos desconocidas → error con línea física; whitelist por contexto en un Enum (`MetadataKeys.ZONE`/`.CONNECTION`, valores `frozenset`); `lineno` hilado hasta los parsers; fixtures `invalid_unknown_zone_key.txt` e `invalid_misplaced_metadata_key.txt`. Cierra M1.4/#8 | pytest 9 passed, lint/type en verde |
| 2026-08-04 | Slice M1.5 (#9): unicidad de nombres (`_add_zone`), exactamente un start/end, y conexiones solo entre zonas definidas (`_resolve_connections`, dos pasadas); 5 fixtures nuevas (4 inválidas + `valid_forward_connection.txt`). Cierra #9 | pytest 14 passed, lint/type en verde |
| 2026-08-04 | Slice M1.6 (#10): duplicados de conexión no dirigidos (`frozenset({a,b})` + `set` de vistos) y self-loops rechazados en `_resolve_connections`; fixtures `invalid_duplicate_connection.txt` e `invalid_self_loop.txt`. Cierra #10 | pytest 16 passed, lint/type en verde |
| 2026-08-04 | Slice M1.7 (#11): `ZoneType.move_cost` (`match`: normal/priority=1, restricted=2, blocked=None); `tests/domain/test_zone.py` nuevo; fixture `valid_zone_types.txt` extendida con `blocked`. Cierra #11 | pytest 18 passed, lint/type en verde |
| 2026-08-04 | Slice M1.8 (#12): validación de capacidad ≥1 en `_optional_capacity` (antes `_optional_int`) con línea física; 0 terminal ignorado (no error); adoptado `invalid_zero_capacity.txt`, nuevos `invalid_zero_link_capacity.txt` y `valid_terminal_zero_capacity_ignored.txt`. Cierra #12 | pytest 21 passed, lint/type en verde |
| 2026-08-04 | Slice M1.9 (#13): nace `flyin/shared/` con `MapParseError`; 11 raises migrados; `try/except` envolvente por línea + guardianes (mapa vacío, nb_drones no numérico, corchete sin cerrar); tests migrados a `MapParseError` + parametrizado de input malformado. Cierra #13 y M1 | pytest 28 passed, lint/type en verde |
| 2026-08-04 | Housekeeping: borradas 3 fixtures huérfanas; borradas 8 ramas remotas mergeadas; activado `deleteBranchOnMerge`; registrada decisión de Dijkstra único (épica #16 y PROGRESS) | 28 passed, sin cambios de código |
| 2026-08-04 | Slice M2.1 (épica #16): nace `flyin/graph/` con `Graph`; adyacencia transitable no dirigida (`dict[str, set]`), `blocked` fuera; `neighbors()` → `frozenset`; `tests/graph/` nuevo | pytest 30 passed, lint/type en verde |
| 2026-08-11 | Slice M2.2 (épica #16): nace `flyin/pathfinding/` con `Dijkstra`+`Path`; camino de menor coste con `heapq`, borrado perezoso, `None` si inalcanzable; `tests/pathfinding/` nuevo | pytest 33 passed, lint/type en verde |
| 2026-08-11 | Slice M2.3 (épica #16): clave de Dijkstra `(turnos, −nº_priority)` → preferencia priority a coste igual sin sacrificar turnos, desempate final por nombre; 2 tests nuevos | pytest 35 passed, lint/type en verde |
| 2026-08-11 | Cierre M2 (épica #16): documentada la complejidad — O(V+E) grafo, O((V+E)·log V) Dijkstra — en docstrings y en `docs/explication/complexity.html` (Big-O desde cero). Cierra la épica | 35 passed, lint/type en verde |
| 2026-08-11 | Slice M3.1 (épica #17): nace `flyin/simulation/` con `Simulator`; un dron recorre su ruta → líneas exactas `D1-<zona>`; `UnsolvableMapError` para mapa sin ruta; `tests/simulation/` nuevo | pytest 37 passed, lint/type en verde |
| 2026-08-12 | Slice M3.2 (épica #17): capa de aplicación `FlyinSolver.solve_text` + capa `flyin/adapters/` con `adapters/cli` (clase `Cli.run`) + `arguments.py` + `__main__.py`; el CLI no llama al parser, solo al solver; `tests/adapters/cli/` y `tests/application/` | pytest 44 passed, lint/type en verde |
| 2026-08-12 | Slice M3.3 (épica #17): nace `SolveResult(movement_lines, warnings)`; `FlyinSolver` normaliza terminal `restricted`→`normal` con warning; el CLI reparte lines→stdout, warnings→stderr (exit 0); tests en solver y CLI | pytest 46 passed, lint/type en verde |
| 2026-08-12 | Slice M3.4 (épica #17): tránsito restricted de 2 turnos en `Simulator.run()` (bucle por pares, token en vuelo `D1-<origen>-<destino>` + llegada); decisión #14 registrada (SPEC_NOTES §1 + tabla); test `test_restricted_zone_takes_two_turns`. Cierra #14 | pytest 47 passed, lint/type en verde |
| 2026-08-12 | Slice M3.5 (épica #17): nace `ScheduleValidator` (validador independiente) + `InvalidScheduleError`; reproduce el recorrido de un dron (`position`+`in_flight_to`) y rechaza salto sin conexión, forma restricted mala o no-llegada a `end`; adyacencia propia (no reutiliza `Graph`); 5 tests nuevos | pytest 52 passed, lint/type en verde |
| 2026-08-13 | Slice M3.6 (épica #17): máquina de estados del dron explícita; `Simulator.run()` pasa de hop-driven a turn-driven con `Enum` `DroneState` (`AT_ZONE`/`IN_TRANSIT`/`DELIVERED`); salida idéntica (refactor); test nuevo motor⊨validador; `TurnPlan` atómico diferido a M4 (decisión) | pytest 53 passed, lint/type en verde |
