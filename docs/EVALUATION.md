# Matriz de evaluación

Estados: `NOT_STARTED`, `IN_PROGRESS`, `EVIDENCED`, `BLOCKED`.
Solo marcar `EVIDENCED` con un test, comando, fichero o demo concreta.

| Ítem de rúbrica | Comportamiento / evidencia requerida | Evidencia planeada | Estado |
| --- | --- | --- | --- |
| README | Primera línea 42, Description, Instructions, Resources/uso de IA, algoritmo, visual, ejemplo | Revisión del README raíz | NOT_STARTED |
| OOP | Separación/encapsulación; herencia solo justificada | Diseño de paquetes + explicación | NOT_STARTED |
| Type safety | `mypy .` sin errores, hints completos | Log del comando | NOT_STARTED |
| Grafo propio | Sin librería prohibida; saber explicarlo | Auditoría de deps + tests de grafo | NOT_STARTED |
| Parser válido | nb_drones, prefijos, conexiones, defaults, comentarios (≥4/5) | Tests de contrato del parser | NOT_STARTED |
| Parser errores | Malformado, tipos inválidos, terminales ausentes, capacidades, duplicados (≥4/5) | Matriz de errores en tests | NOT_STARTED |
| Ocupación de zonas | Capacidad defecto/explícita, terminales ilimitados, liberación mismo turno | Tests de validador/simulador | NOT_STARTED |
| Costes de movimiento | normal/priority 1, restricted 2, blocked inaccesible | Tests de transición de estado | NOT_STARTED |
| Capacidad de enlace | Defecto/explícita, simultaneidad | Tests de reservas | NOT_STARTED |
| Visualización | Posiciones/movimientos/colores/capacidad claros | Demo de terminal | NOT_STARTED |
| Escenarios básicos | 1 dron, varios drones, mapas provistos, formato, omisión de parados (≥4/5) | Tests de integración CLI | NOT_STARTED |
| Terminación | Parar exactamente al entregar todos | Test CLI/simulador | NOT_STARTED |
| Caminos válidos | Lineal, múltiple, cuellos de botella, tipos | Tests planner + validador | NOT_STARTED |
| Conflictos | Competición, simultaneidad, restricted multi-turno | Tests de scheduler | NOT_STARTED |
| Eficiencia | 10+ drones, grafos complejos, tiempo razonable | Informe de benchmarks | NOT_STARTED |
| Explicación | Complejidad, diseño, trade-offs de capacidad/optimización | README + notas de defensa | NOT_STARTED |
| Benchmarks Easy | Categoría <10; objetivos 6/8/6 con 2/4/4 drones | Tabla fresca | NOT_STARTED |
| Benchmarks Medium | 10–30; objetivos 12/15/12 con 5/6/5 | Tabla fresca | NOT_STARTED |
| Benchmarks Hard | <60; objetivos 30/35/45 con 8/12/15 | Tabla fresca | NOT_STARTED |
| Casos límite | 1 dron, cuellos, desconexo, conexiones inválidas, capacidad 0/alta (≥4/5) | Suite de edge cases | NOT_STARTED |
| Gestión de errores | Mensajes claros para inválido/desconexo | Tests CLI | NOT_STARTED |
| Calidad de código | Estructura, docs, estilo, visual integrado | Review + lint | NOT_STARTED |
| Live coding | Añadir `--capacity-info` en ≤10 min | Registro de ensayo | NOT_STARTED |
| Bonus rendimiento | Igualar/batir TODOS los objetivos individuales | Evidencia de benchmarks | NOT_STARTED |
| Challenger | Impossible Dream en ≤44 turnos | Benchmark opcional | NOT_STARTED |

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

| Mapa | Drones | Objetivo | Resultado | Válido | Fecha/commit |
| --- | ---: | ---: | ---: | --- | --- |
| maps/easy/01_linear_path.txt | 2 | ≤6 | — | — | — |
| maps/easy/02_simple_fork.txt | 4 | ≤8 | — | — | — |
| maps/easy/03_basic_capacity.txt | 4 | ≤6 | — | — | — |
| maps/medium/01_dead_end_trap.txt | 5 | ≤12 | — | — | — |
| maps/medium/02_circular_loop.txt | 6 | ≤15 | — | — | — |
| maps/medium/03_priority_puzzle.txt | 5 | ≤12 | — | — | — |
| maps/hard/01_maze_nightmare.txt | 8 | ≤30 | — | — | — |
| maps/hard/02_capacity_hell.txt | 12 | ≤35 | — | — | — |
| maps/hard/03_ultimate_challenge.txt | 15 | ≤45 | — | — | — |
| maps/challenger/01_the_impossible_dream.txt | 25 | <45 (opcional) | — | — | — |
