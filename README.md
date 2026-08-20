*This project has been created as part of the 42 curriculum by jose-car.*

# Fly-In

Fly-In is a capacity-aware drone routing simulator. Given a map of zones,
connections and a fleet of drones, it moves every drone from the start hub to
the end hub in as few turns as possible while respecting the movement cost of
each zone and the capacity of every zone and connection. It prints the plan as
one line per turn.

## Description

The input is a text map describing:

- a fleet of `nb_drones` drones, all starting on the **start hub** and all
  bound for the **end hub**;
- **zones** (the nodes where drones can stand), each with a type that sets its
  movement cost and an optional capacity;
- **connections** (the bidirectional edges between zones).

Every turn, each drone either stays put or moves to an adjacent zone. The
simulator must deliver the whole fleet without ever overfilling a zone or a
connection, and it aims to do it in the fewest turns.

Movement cost depends on the **destination** zone:

| Zone type    | Cost to enter        |
| ------------ | -------------------- |
| `normal`     | 1 turn               |
| `priority`   | 1 turn (preferred on a tie) |
| `restricted` | 2 turns (a one-turn transit on the connection, then landing) |
| `blocked`    | impassable           |

Capacities default to 1 for both zones and connections. The start and end hubs
have unlimited capacity, so a `max_drones` declared on them is ignored.

The program stops exactly when every drone has reached the end hub.

## Instructions

**Requirements:** Python ≥ 3.10 and [uv](https://docs.astral.sh/uv/) (the
package manager used to create the environment and run the code).

All commands are driven by the `Makefile` at the repository root:

```sh
make install                                   # create the virtual environment
make run ARGS=maps/easy/01_linear_path.txt     # solve a map (evaluator output)
make run                                        # no map: pick one from a menu
make run-visual ARGS=maps/easy/01_linear_path.txt  # colored human view
make debug ARGS=maps/easy/01_linear_path.txt   # run under the pdb debugger
make test                                       # run the test suite
make lint                                        # flake8 + mypy
```

`make run` with no `ARGS` lists the known maps and lets you choose one by
number. The plan is written to **standard output**; warnings and errors go to
**standard error**, so the evaluator output stays clean and can be redirected
on its own.

## Example

Input map (`maps/easy/01_linear_path.txt`):

```
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Expected output (`make run ARGS=maps/easy/01_linear_path.txt`):

```
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each line is one turn. A token `D<id>-<zone>` means drone `<id>` arrives at
`<zone>` this turn; drones that do not move are omitted. Both drones share the
single-lane path, so the second drone follows one turn behind the first: the
whole fleet is delivered in 4 turns.

## Algorithm explanation

The engine is built as a pipeline of small, single-responsibility classes:

1. **Parsing** (`MapParser`) turns the text into domain objects
   (`Zone`, `Connection`, `FlyInMap`), reporting any error with its physical
   line number and cause.
2. **Graph** (`Graph`) builds the adjacency of *traversable* zones only:
   blocked zones never join the graph. Built in `O(V + E)`.
3. **Pathfinding** (`Dijkstra`) finds the cheapest route from start to end.
   Each edge weight is the destination's move cost (1 for normal/priority, 2
   for restricted), so "cheapest" means "fewest turns". Zones are ordered by
   the key `(turns, -priority_count)`: fewer turns always wins, and on a tie
   the route through more `priority` zones is preferred. A binary heap
   (`heapq`) supplies the priority queue, giving `O((V + E) log V)`.
4. **Scheduling / simulation** (`Simulator`) assigns drones to the route and
   advances the turns. The turn plan is applied atomically — exits are freed
   before entries are evaluated — so correctness never depends on the order in
   which the drones are iterated. Entering a restricted zone takes two turns:
   the drone occupies the connection for one turn and must land the next, so
   the departure is only legal when the destination's capacity is reserved for
   the arrival turn.
5. **Validation** (`ScheduleValidator`) is an independent judge that replays
   the produced plan and re-derives every rule from scratch. The simulator
   first solves in a fast *optimistic* mode; if the validator rejects the
   result, it falls back to a strictly-reserved *conservative* mode that is
   always legal. This guarantees a valid schedule while keeping the common
   case fast.

No graph or pathfinding library is used: the graph, Dijkstra and the scheduler
are implemented from scratch.

## Visual representation

`make run-visual ARGS=<map>` renders the same result for human eyes, in color,
without ever touching the evaluator output. It shows the state of every zone,
the turns with each token painted in its zone's color, and a summary of the
run:

```
Fly-In simulation
Drones: 2

Zones:
  ■ start      type=normal  capacity=unlimited  xy=(0,0)  color=green
  ■ waypoint1  type=normal  capacity=1          xy=(1,0)  color=blue
  ■ waypoint2  type=normal  capacity=1          xy=(2,0)  color=blue
  ■ goal       type=normal  capacity=unlimited  xy=(3,0)  color=red

Turns:
  Turn 1: D1-waypoint1
  Turn 2: D1-waypoint2 D2-waypoint1
  Turn 3: D1-goal D2-waypoint2
  Turn 4: D2-goal

Metrics:
  Turns:             4
  Total moves:       6
  Drones/turn (avg): 1.5
```

The metrics are counted straight from the movement lines: each token is one
drone spending one turn, so `Total moves` is the total path cost and
`Drones/turn` is the average parallelism of the plan.

## Resources

- Edsger W. Dijkstra, *A note on two problems in connexion with graphs* (1959)
  — the shortest-path algorithm.
- Python `heapq` — the binary-heap priority queue used by Dijkstra.
- ANSI escape codes — the terminal colors of the visual view.
- [uv](https://docs.astral.sh/uv/) — the environment and runner.

**Use of AI:** this project was developed with Claude Code (Anthropic) acting
as a pair-programming assistant and tutor. It helped explain the underlying
concepts (graphs, Dijkstra, capacity reservations), draft code and tests, and
review design decisions. Every algorithm, data structure and trade-off was
reviewed and understood by the author, who owns and can defend each part of the
implementation.
