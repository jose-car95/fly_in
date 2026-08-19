# Matriz de evaluación

Estados: `NOT_STARTED`, `IN_PROGRESS`, `EVIDENCED`, `BLOCKED`.
Solo marcar `EVIDENCED` con un test, comando, fichero o demo concreta.

| Ítem de rúbrica | Comportamiento / evidencia requerida | Evidencia planeada | Estado |
| --- | --- | --- | --- |
| Makefile | Reglas `install`, `run`, `debug` (pdb), `clean`, `lint` con los flags del subject III.2 | `make debug` arranca pdb y para en breakpoints; `make lint` caza una función sin tipos que `mypy .` a secas deja pasar | EVIDENCED |
| README | Primera línea 42, Description, Instructions, Resources/uso de IA, algoritmo, visual, ejemplo | Revisión del README raíz | NOT_STARTED |
| OOP | Separación/encapsulación; herencia solo justificada | Diseño de paquetes + explicación | IN_PROGRESS |
| Type safety | `mypy .` sin errores, hints completos | `make lint` (mypy, 36 ficheros sin errores) | EVIDENCED |
| Grafo propio | Sin librería prohibida; saber explicarlo | `tests/graph`, `tests/pathfinding`; sin networkx/graphlib | EVIDENCED |
| Parser válido | nb_drones, prefijos, conexiones, defaults, comentarios (≥4/5) | `tests/parsing/test_map_parser.py` (26 tests) | EVIDENCED |
| Parser errores | Malformado, tipos inválidos, terminales ausentes, capacidades, duplicados (≥4/5) | Matriz de malformados en `tests/parsing` | EVIDENCED |
| Ocupación de zonas | Capacidad defecto/explícita, terminales ilimitados, liberación mismo turno | `test_simulator` (cola, cap>1) + `test_schedule_validator` (ocupación) + `test_official_maps` | EVIDENCED |
| Costes de movimiento | normal/priority 1, restricted 2, blocked inaccesible | `test_zone` (move_cost) + `test_simulator` (restricted 2 turnos) | EVIDENCED |
| Capacidad de enlace | Defecto/explícita, simultaneidad | `test_simulator` (throttle) + `test_schedule_validator` (cruces) | EVIDENCED |
| Visualización | Posiciones/movimientos/colores/capacidad claros | Demo de terminal | NOT_STARTED |
| Escenarios básicos | 1 dron, varios drones, mapas provistos, formato, omisión de parados (≥4/5) | `test_official_maps` (10 mapas) + `tests/adapters/cli` + cola | EVIDENCED |
| Terminación | Parar exactamente al entregar todos | `test_official_maps` (terminan) + `test_simulator` | EVIDENCED |
| Caminos válidos | Lineal, múltiple, cuellos de botella, tipos | `test_official_maps` (validador acepta los 10) | EVIDENCED |
| Conflictos | Competición, simultaneidad, restricted multi-turno | `test_simulator` (cola, serialize restricted) + validador | EVIDENCED |
| Eficiencia | 10+ drones, grafos complejos, tiempo razonable | `make bench` (12/15/25 drones; suite <0.1s) | EVIDENCED |
| Explicación | Complejidad, diseño, trade-offs de capacidad/optimización | README + notas de defensa | NOT_STARTED |
| Benchmarks Easy | Categoría <10; objetivos 6/8/6 con 2/4/4 drones | `make bench`: 4/6/4, todos válidos y ≤ objetivo | EVIDENCED |
| Benchmarks Medium | 10–30; objetivos 12/15/12 con 5/6/5 | `make bench`: 8/15/8, todos válidos y ≤ objetivo | EVIDENCED |
| Benchmarks Hard | <60; objetivos 30/35/45 con 8/12/15 | `make bench`: 13/16/26, todos válidos y ≤ objetivo | EVIDENCED |
| Casos límite | 1 dron, cuellos, desconexo, conexiones inválidas, capacidad 0/alta (≥4/5) | Suite de edge cases | NOT_STARTED |
| Gestión de errores | Mensajes claros para inválido/desconexo | Tests CLI | NOT_STARTED |
| Calidad de código | Estructura, docs, estilo, visual integrado | Review + lint | NOT_STARTED |
| Live coding | Añadir `--capacity-info` en ≤10 min | Registro de ensayo | NOT_STARTED |
| Bonus rendimiento | Igualar/batir TODOS los objetivos individuales | `make bench`: los 10 mapas por debajo de su objetivo | EVIDENCED |
| Challenger | Impossible Dream en ≤44 turnos | `make bench`: 43 turnos, válido (pipeline restricted a 1/turno) | EVIDENCED |

## Costura de live coding (`--capacity-info`)

La rúbrica pedirá algo como:

```text
./main.py --capacity-info map.txt
```

con salida adicional por turno tipo `Zone X: Y/Z drones, Connection A-B: Y/Z capacity used`.

Preparar sin sobreajustar:

- Parseo de opciones del CLI aislado.
- El resultado de simulación/snapshot de turno expone ocupación sin reparsear texto.
- Un formateador adicional puede añadir la vista diagnóstica.
- La salida por defecto no cambia.
- Ensayar desde una rama limpia y cronometrar. No commitear una "modificación en vivo"
  falsa: el objetivo es entenderlo y tener la costura limpia.

## Registro de benchmarks

Línea base (motor de un solo camino, `make bench`), 2026-08-18:

| Mapa | Drones | Objetivo | Resultado | Válido | Fecha/commit |
| --- | ---: | ---: | ---: | --- | --- |
| maps/easy/01_linear_path.txt | 2 | ≤6 | 4 | sí | 2026-08-18 (baseline) |
| maps/easy/02_simple_fork.txt | 4 | ≤8 | 6 | sí | 2026-08-18 (baseline) |
| maps/easy/03_basic_capacity.txt | 4 | ≤6 | 4 | sí | 2026-08-18 (baseline) |
| maps/medium/01_dead_end_trap.txt | 5 | ≤12 | 8 | sí | 2026-08-18 (baseline) |
| maps/medium/02_circular_loop.txt | 6 | ≤15 | 10 | sí | 2026-08-18 (M5.3) |
| maps/medium/03_priority_puzzle.txt | 5 | ≤12 | 8 | sí | 2026-08-18 (baseline) |
| maps/hard/01_maze_nightmare.txt | 8 | ≤30 | 13 | sí | 2026-08-18 (baseline) |
| maps/hard/02_capacity_hell.txt | 12 | ≤35 | 16 | sí | 2026-08-18 (baseline) |
| maps/hard/03_ultimate_challenge.txt | 15 | ≤45 | 26 | sí | 2026-08-18 (baseline) |
| maps/challenger/01_the_impossible_dream.txt | 25 | <45 (opcional) | 43 | sí | 2026-08-18 (M5.3) |

Lectura: los 9 mapas obligatorios (easy/medium/hard) ya cumplen su objetivo con
el motor de un solo camino (8 por debajo, `circular_loop` justo en 15). El único
por encima es el challenger opcional (67 vs 45). Multi-camino solo aportaría en
el challenger (y quizá margen en `circular_loop`); no es necesario para el
listón obligatorio de turnos.
