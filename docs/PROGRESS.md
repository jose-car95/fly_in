# Estado del proyecto (fichero vivo)

Claude lo lee al empezar cada sesión y lo actualiza al cerrar cada slice.
Mantenerlo corto: es un puntero al estado real, no un diario exhaustivo.

## Estado actual

- Milestone: **M5 en progreso** (M0–M4 cerrados). Benchmarks + optimización.
- Último slice completado: M5.3 — pipeline restricted a 1/turno. `_free_slots` deja de
  contar al dron en vuelo contra su destino (simplificación, quita código): un dron puede
  despegar hacia una restricted el mismo turno que el ocupante sale, así las zonas restricted
  pasan de 1 dron/2 turnos a 1/turno. **RESULTADO: challenger 67 → 43 (bonus <45 conseguido,
  single-path, sin multi-camino)**; `circular_loop` 15 → 10; los 10 mapas siguen VÁLIDOS.
  CAVEAT: el motor pasa de "correcto por construcción" a OPTIMISTA — en un mapa patológico
  (restricted que se atasca) podría dar salida inválida; el validador lo detectaría pero no
  hay reintento. Todos los mapas provistos validan. Red de seguridad pendiente (ver siguiente).
- Anteriores (breve): M5.2 `CandidatePaths` (Dijkstra con `penalties` + penalización; halla
  las 3 cadenas paralelas del challenger) — YA NO necesario para el bonus, se retirará.
- Contexto (medir antes de optimizar): la línea base (M5.1) mostró que los 9 obligatorios ya
  cumplen objetivo; el único por encima es el challenger (67 vs 45). Es el bonus
  (100→125 pts, +25), y por eso Jose decidió PERSEGUIR multi-camino (2026-08-18) para bajar
  el challenger a <45. Cota inferior analizada ≈ 43 (embudos de entrada/salida a 1 dron/turno)
  → alcanzable pero AJUSTADO. El cuello actual: los 25 drones por 1 cadena restricted cap-1
  (1 dron/2 turnos). Palanca: repartir por las 3 cadenas paralelas.
- Anteriores (breve): M5.1 benchmark harness (`Benchmark`/`BenchmarkResult`/`BenchmarkSuite`,
  `make bench`, línea base) · Path A slice 2 capacidad de enlace en el validador (juez completo
  zona+enlace) · M4.6 validador multi-dron (replay por id, ocupación de zona, aterrizaje
  obligatorio, start→end) · M4.5 reserva de llegadas restricted (dron en vuelo cuenta contra su
  destino; despegue unificado con movimiento normal; decisión #15 Opción A) · M4.4 capacidad
  de enlace (`_link_slots`, clave `frozenset`, defecto 1)
  · M4.3 test de caracterización de `max_drones > 1` · M4.1 multi-dron con
  plan de turno atómico (decidir/aplicar, front-first) + clase `Drone` + capacidad efectiva
  (∞ terminales) · M3.6 máquina de estados del dron (`DroneState`, turn-driven) · M3.5
  `ScheduleValidator` independiente (`position`+`in_flight_to`,
  adyacencia propia, `InvalidScheduleError`) · M3.4 tránsito restricted de 2 turnos en
  `Simulator.run()` (token en
  vuelo `D1-<origen>-<destino>` + llegada) · M3.3 `SolveResult(movement_lines, warnings)` +
  normalización de terminal `restricted`→`normal` con warning · M3.2 capa de aplicación
  (`FlyinSolver`) +
  adaptadores (`adapters/cli`, clase `Cli`) · M3.1 motor `Simulator` (`D1-<zona>`,
  `UnsolvableMapError`) · M2 grafo + Dijkstra `(turnos,−nº_priority)` + complejidad
  documentada · M1 parser completo (`MapParseError`) · M0 entorno/CI. Detalle en el
  registro de sesiones y en la tabla de decisiones.
- Verificado con comandos: `pytest` (77 passed), `flake8 .` (limpio, límite 79),
  `mypy .` con los flags de `make lint` (sin errores, 44 ficheros). `make lint`,
  `make test` y `make bench` en verde.
- Siguiente paso (decidido con Jose): (1) **retirar el multi-camino** (`CandidatePaths` +
  su test + el parámetro `penalties` de Dijkstra) porque el bonus ya se logró single-path y
  ya no aporta — código muerto; (2) **red de seguridad**: el solver valida su propia salida
  y, si fuera inválida (un mapa patológico), cae al modo conservador (reserva estricta), para
  recuperar la corrección demostrable en cualquier mapa sin perder la velocidad en los que
  fluyen.
- Contexto histórico (Jose, 2026-08-18): PERSEGUIR multi-camino. Motivo: el
  challenger es el bonus (100→125 pts, +25). Aunque no aporta al listón obligatorio, sí a la
  nota máxima. Objetivo: bajar `the_impossible_dream` de 67 a <45 turnos repartiendo drones
  entre varios caminos. El benchmark harness (M5.1) es el juez de progreso: cada cambio se
  mide contra makespan previo y validez. Después, M6 (presentación).

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
| 2026-08-13 | M4.1: la arbitración de capacidad vive en `Simulator` (fase decidir/aplicar), sin crear aún la carpeta `scheduling/` | Con un único camino compartido el turno atómico es pequeño y cohesivo dentro del simulador; separar una capa `scheduling` con un solo cliente sería especular. Nace cuando la reserva de tiempo/enlace o el multi-camino lo justifiquen (M4.4–M4.6) |
| 2026-08-13 | M4.1: la clase `Drone` es dueña de su ciclo de vida; el `Simulator` decide la capacidad | El dron sabe *cómo* avanzar (`takeoff`/`advance`); el simulador decide *si* puede (capacidad). Separa responsabilidades y respeta full-OOP (comportamiento en clases). `DroneState` a su módulo para compartirlo sin import circular |
| 2026-08-13 | M4.1: capacidad efectiva = ∞ en terminales, `max_drones` (o 1) en el resto; no se hardcodea 1 | Hardcodear 1 sería incorrecto: los drones se apilan en `start` (∞). Leer `max_drones` es la semántica correcta mínima y deja M4.3 (`max_drones > 1`) casi resuelto (será un test) |
| 2026-08-13 | M4.1: turno front-first (drones más avanzados primero) para "salidas antes que entradas" | Recorrer del final hacia atrás garantiza que quien sale libera su hueco antes de admitir al de detrás, sin depender del orden de iteración (invariante SPEC_NOTES §2). Empates en la misma zona por id ascendente para determinismo |
| 2026-08-17 | M4.4: capacidad de enlace con clave no dirigida `frozenset{a,b}`, cupo compartido entre ambos sentidos, defecto 1; solo movimientos normales | Refleja la FACT del subject (conexión bidireccional, capacidad compartida). El consumo durante tránsito restricted es la decisión abierta #15 → se difiere a M4.5 para no prejuzgarla. El fixture de M4.3 pasa a `max_link_capacity=2` porque, sin ello, mover 2 drones por la misma conexión sería ilegal bajo las reglas completas (no es debilitar el test: es corregir el mapa al modelo completo conservando lo que demuestra) |
| 2026-08-17 | #15: el tránsito restricted consume el enlace SOLO en el turno de salida (T1), no en el de llegada (T2) | Uniforme con el movimiento normal (1 travesía en 1 turno; el 2º turno es entrar en la zona, no cruzar) y coherente con el orden del turno de §2 (llegadas antes que salidas → un aterrizaje libera el enlace para un despegue el mismo turno). Cierra la decisión abierta #15; también en SPEC_NOTES §1 |
| 2026-08-17 | M4.5: la reserva restricted se modela contando al dron en vuelo contra su destino en `_free_slots`, unificando despegue y movimiento normal en `_grant_moves` | El despegue y el paso normal se comportan igual (liberan origen, reclaman destino); la única diferencia es en `_apply_move` (takeoff vs advance). Borra el caso especial en vez de añadir uno, y la reserva persistente hace que el aterrizaje obligatorio sea siempre legal sin lógica extra de "calendario" |
| 2026-08-17 | Path A: cerrar M4 probando validez con el validador multi-dron; mover multi-camino y deadlock a M5 (optimización) | El motor de un camino ya da schedules válidos y terminantes en los 10 mapas (listón de M4). Multi-camino es optimización de makespan; el subject pide "primero línea base medida, optimizar solo a partir de mediciones" (M5). Construirlo antes de tener benchmark sería optimizar a ciegas (ponytail). Reordena el PLAN: M4.6/M4.7 pasan a M5 |

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

- (ninguna abierta ahora mismo; la #15 se cerró el 2026-08-17, ver tabla de decisiones)

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
| 2026-08-13 | Slice M4.1 (épica #18): multi-dron con plan de turno atómico (decidir/aplicar) y cola en zona de capacidad 1; nace la clase `Drone`, `DroneState` a su módulo; capacidad efectiva (∞ terminales); front-first para salidas-antes-de-entradas; test 2 drones en cola; enlace/restricted/multi-camino/deadlock diferidos | pytest 54 passed, lint/type en verde |
| 2026-08-17 | Slice M4.3 (épica #18): test de caracterización de `max_drones > 1` (zona cap.2 admite 2 drones, encola al 3º); sin código nuevo (M4.1 ya leía la capacidad); cubre también M4.2 (salidas liberan hueco el mismo turno) | pytest 55 passed, lint/type en verde |
| 2026-08-17 | Slice M4.4 (épica #18): capacidad de enlace en `_grant_moves` (`_link_slots`, clave `frozenset`, defecto 1, ambos sentidos); test RED enlace-estrangula-zona; fixture de M4.3 a `max_link_capacity=2`; consumo en tránsito restricted diferido a #15/M4.5 | pytest 56 passed, lint/type en verde |
| 2026-08-17 | Decisión #15 (Opción A): el enlace se mide solo en el turno de salida del tránsito restricted; registrada en SPEC_NOTES §1 y tabla de decisiones (vía `/decide`) | — |
| 2026-08-17 | Slice M4.5 (épica #18): reserva de llegadas restricted; despegue unificado con movimiento normal (se borra el caso especial); `_free_slots` cuenta al dron en vuelo contra su destino; test 2 drones se serializan por cuello restricted cap.1 | pytest 57 passed, lint/type en verde |
| 2026-08-17 | Decisión estratégica Path A: validador-primero para cerrar M4; multi-camino/deadlock → M5 (medir antes de optimizar). Registrada en tabla de decisiones y reflejada en PLAN.md | — |
| 2026-08-17 | Slice M4.6/Path A (épica #18): `ScheduleValidator` a multi-dron; replay por id (`_position`/`_in_flight`), ocupación de zona por turno, un movimiento por dron/turno, aterrizaje obligatorio, start→end; `_capacity`/`_links` propios; capacidad de enlace diferida; 3 tests nuevos | pytest 60 passed, lint/type en verde |
| 2026-08-17 | Slice Path A-2 (épica #18): capacidad de enlace en el validador (`_link_caps`, cuenta cruces por turno, aterrizaje no cuenta por #15); juez completo (zona+enlace); 2 tests nuevos | pytest 62 passed, lint/type en verde |
| 2026-08-17 | Cierre M4 (épica #18): `tests/test_official_maps.py` corre el motor y valida su salida en los 10 mapas oficiales (11 tests con guard); los 10 validan, sin bugs. Validez demostrada por el juez independiente. EVALUATION.md: 11 ítems a EVIDENCED | pytest 73 passed, lint/type en verde |
| 2026-08-18 | Slice M5.1 (épica #19): benchmark harness (`flyin/benchmark/`: `Benchmark`, `BenchmarkResult`, `BenchmarkSuite`, `make bench`); línea base registrada en EVALUATION.md; 3 ítems de benchmarks + eficiencia a EVIDENCED. Hallazgo: los 9 obligatorios ya cumplen objetivo | pytest 75 passed, lint/type en verde |
| 2026-08-18 | Slice M5.2 (épica #19): `CandidatePaths` (Dijkstra con `penalties` opcional + penalización de zonas intermedias); halla varias rutas que divergen en el medio y comparten embudos; verificado que encuentra las 3 cadenas paralelas del challenger; 2 tests | pytest 77 passed, lint/type en verde |
| 2026-08-18 | Slice M5.3 (épica #19): pipeline restricted a 1/turno (`_free_slots` no cuenta al dron en vuelo). CHALLENGER 67→43 (bonus conseguido, single-path); circular_loop 15→10; 10 mapas siguen válidos. Motor ahora optimista (caveat); red de seguridad pendiente. Analizado el repo de mario-asenjo para entender la técnica | pytest 77 passed, lint/type en verde |
