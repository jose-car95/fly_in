# Plan incremental

Cada milestone termina con: comportamiento demostrable, tests, `flake8` + `mypy` en verde,
explicación breve a Jose y actualización de `PROGRESS.md`. No empezar un milestone
posterior para que uno anterior "parezca útil".

## M0 — Repositorio y contrato ejecutable

- Confirmar versión de Python y flujo de paquetes; `make install` funciona.
- Rellenar el login en la primera línea del README.
- Ejecutar `/bootstrap-github` (issues, tablero, CI y protección de main).
- Primer test de aceptación en rojo: parsear el mapa mínimo (`tests/fixtures/edge-cases/valid_minimal.txt`).
- `mypy` y `flake8` configurados y ejecutables.

Salida: los comandos corren de forma predecible y el primer test rojo describe
comportamiento real.

## M1 — Parser (slices en este orden)

1. `nb_drones` + grafo mínimo start/end/conexión.
2. Hubs regulares y coordenadas.
3. Comentarios/blancos y números de línea físicos.
4. Metadatos, valores por defecto y orden libre de tags.
5. Unicidad de start/end/nombres; conexiones solo entre zonas ya definidas.
6. Duplicados de conexión no dirigidos (`a-b` = `b-a`).
7. Tipos de zona y representación de blocked.
8. Validación de capacidades + regla de ignorar capacidad en terminales.
9. Errores claros para entradas malformadas.

Salida: pasan los casos de parser de la rúbrica; el parser no sabe nada de pathfinding
ni de colores.

## M2 — Grafo propio y corrección de rutas

- Adyacencia transitable sin librerías; manejo de grafos desconexos.
- BFS base + camino mínimo ponderado por coste de destino.
- Política determinista de desempate y preferencia priority.
- Documentar complejidad.

Salida: un dron llega al final en fixtures lineal, fork, restricted, priority, blocked,
loop y dead-end. Sin optimización multi-dron todavía.

## M3 — Motor de simulación determinista

- Máquina de estados del dron explícita.
- Transición atómica `SimulationState -> TurnPlan -> SimulationState`.
- Movimiento de 1 turno; tránsito restricted de 2 turnos con llegada obligatoria.
- Retirada de drones entregados; formateador exacto de turnos/tokens.
- Validador de schedules independiente.

Salida: schedules conocidos validan y los tests de stdout exacto pasan.

## M4 — Scheduler consciente de capacidad

1. Cola en zonas de capacidad 1 (defecto).
2. Liberación por salida en el mismo turno.
3. `max_drones > 1`.
4. Capacidad de enlace por defecto; luego `max_link_capacity > 1`.
5. Reserva futura para llegadas restricted.
6. Múltiples caminos candidatos; reparto de rutas y espera estratégica.
7. Prevención/detección de deadlocks.

Salida: todos los mapas provistos obtienen schedules válidos y terminantes
(independientemente de los objetivos de turnos).

## M5 — Optimización con benchmarks

Primero línea base medida; optimizar solo a partir de mediciones.

- Coste de caminos candidatos + capacidad de cuello de botella.
- Estimar tiempo de finalización de la flota, no solo el camino más corto por dron.
- Repartir drones entre caminos beneficiosos; caching solo si el profiling muestra
  trabajo repetido.
- Runner de benchmarks determinista; comparar cada cambio contra validez y makespan previo.

Secuencia de objetivos: categoría Easy → Medium → Hard → cada objetivo individual del subject →
Challenger <45 (opcional).

Salida: tabla documentada con resultados frescos y explicación de los gaps restantes.

## M6 — Presentación y endurecimiento para la evaluación

- Modo visual de terminal coloreado usando los colores del mapa, sin tocar el stdout
  por defecto.
- README con todas las secciones obligatorias y ejemplos.
- `docs/EVALUATION.md` con evidencia por ítem de rúbrica.
- Ensayar el live coding `--capacity-info` (≤10 min) desde una rama limpia.
- Casos límite, mapas inválidos, muchos drones, ejecución desde clon limpio.

Salida: proyecto obligatorio defendible.

## Después (solo si se decide, fuera del alcance obligatorio)

Ideas del plan original, aparcadas deliberadamente para no meter ruido: eventos tipados
in-process → API FastAPI (+SSE) → visualización React. Ninguna se empieza sin decisión
explícita anotada en `PROGRESS.md`, y nunca antes de terminar M6. El dominio y el CLI
deben seguir funcionando solos si esas piezas no existen.
