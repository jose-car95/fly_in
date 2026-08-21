"""Figures analysed from a solved run: summary numbers and per-turn capacity.

An application-level value object used by any adapter that presents a run:
the CLI visual view and the HTTP API both build it from the same movement
lines, so their numbers can never disagree with the plan.
"""

from flyin.domain.fly_in_map import FlyInMap


class RunMetrics:
    """Figures analysed from a solved run, read from its movement lines.

    The summary counting rests on one fact of the output format: each token
    is one drone spending one turn. A normal move prints one token and costs
    one turn; a two-turn restricted transit prints two (an in-flight token
    then a landing token). ``total_moves`` is therefore the token count, and
    it equals the total path cost (normal costs 1 and prints 1, restricted
    costs 2 and prints 2), with no move cost re-derived here. The same replay
    also yields, given the map, the per-turn capacity usage.

    Attributes:
        _lines: The per-turn movement lines the run produced.
    """

    def __init__(self, movement_lines: list[str]) -> None:
        """Store the run's output.

        Args:
            movement_lines: The exact per-turn lines the engine produced.
        """
        self._lines = movement_lines

    @property
    def turns(self) -> int:
        """Turns taken to deliver every drone (the makespan)."""
        return len(self._lines)

    @property
    def total_moves(self) -> int:
        """Total drone-turns of movement, equal to the total path cost."""
        return sum(len(line.split()) for line in self._lines)

    @property
    def drones_per_turn(self) -> float:
        """Average number of drones moving on a turn (the throughput).

        Returns 0 for a run with no turns, so an already-solved map does not
        divide by zero.
        """
        if not self._lines:
            return 0.0
        return self.total_moves / self.turns

    def capacity_lines(self, fly_in_map: FlyInMap) -> list[str]:
        """Return the per-turn zone occupancy and connection usage.

        Replays the same movement lines against the map's capacities and
        reports, after every turn, how full each zone and connection is. The
        map is passed in only for the declared capacities.

        Args:
            fly_in_map: The solved map, for the zone and link capacities.

        Returns:
            A ``Turn N capacity:`` header per turn, then a
            ``Zone <name>: used/cap drones`` line per zone and a
            ``Connection <a>-<b>: used/cap used`` line per connection.
        """
        positions: dict[int, str | None] = {
            drone: fly_in_map.start.name
            for drone in range(1, fly_in_map.nb_drones + 1)
        }
        report: list[str] = []
        for turn, movement in enumerate(self._lines, start=1):
            crossings = self._apply_turn(movement, positions)
            report.append(f"Turn {turn} capacity:")
            report.extend(self._zone_lines(fly_in_map, positions))
            report.extend(self._connection_lines(fly_in_map, crossings))
        return report

    @staticmethod
    def _apply_turn(
        movement: str, positions: dict[int, str | None]
    ) -> dict[frozenset[str], int]:
        """Advance the drones over one turn and count its crossings.

        A ``D<id>-<zone>`` token lands the drone and crosses the connection
        from where it stood; a ``D<id>-<a>-<b>`` token is a restricted
        take-off, which crosses the connection and leaves the drone in flight
        (no zone) until it lands. Zone names carry no dashes, so splitting the
        token on ``-`` is unambiguous.

        Args:
            movement: One movement line, its tokens space-separated.
            positions: Each drone's zone, mutated in place; ``None`` while a
                drone is mid restricted transit.

        Returns:
            How many times each connection was crossed this turn.
        """
        crossings: dict[frozenset[str], int] = {}
        for token in movement.split():
            drone, *rest = token.split("-")
            drone_id = int(drone[1:])
            if len(rest) == 1:
                origin = positions[drone_id]
                if origin is not None:
                    link = frozenset((origin, rest[0]))
                    crossings[link] = crossings.get(link, 0) + 1
                positions[drone_id] = rest[0]
            else:
                positions[drone_id] = None
                link = frozenset((rest[0], rest[1]))
                crossings[link] = crossings.get(link, 0) + 1
        return crossings

    @staticmethod
    def _zone_lines(
        fly_in_map: FlyInMap, positions: dict[int, str | None]
    ) -> list[str]:
        """Return one occupancy line per zone for the current positions."""
        counts: dict[str, int] = {}
        for where in positions.values():
            if where is not None:
                counts[where] = counts.get(where, 0) + 1
        report = []
        for name, zone in fly_in_map.zones.items():
            capacity = (
                "inf" if zone.is_start or zone.is_end
                else str(zone.max_drones or 1)
            )
            report.append(
                f"  Zone {name}: {counts.get(name, 0)}/{capacity} drones"
            )
        return report

    @staticmethod
    def _connection_lines(
        fly_in_map: FlyInMap, crossings: dict[frozenset[str], int]
    ) -> list[str]:
        """Return one usage line per connection for this turn's crossings."""
        report = []
        for conn in fly_in_map.connections:
            link = frozenset((conn.zone_a, conn.zone_b))
            capacity = conn.max_link_capacity or 1
            report.append(
                f"  Connection {conn.zone_a}-{conn.zone_b}: "
                f"{crossings.get(link, 0)}/{capacity} used"
            )
        return report
