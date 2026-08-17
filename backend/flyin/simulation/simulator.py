"""Turn-based simulation of drones over a parsed map."""

from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import ZoneType
from flyin.graph.graph import Graph
from flyin.pathfinding.dijkstra import Dijkstra
from flyin.shared.exceptions import UnsolvableMapError
from flyin.simulation.drone import Drone


class Simulator:
    """Runs the turn-by-turn movement of the drones and yields the output.

    It routes ``nb_drones`` drones along the single cheapest path found by
    Dijkstra and moves them one turn at a time. Each turn is computed as a
    whole plan against a snapshot of the world and applied atomically, so the
    output never depends on the order in which the drones are iterated: a
    zone admits a newcomer only if it has room once this turn's leavers have
    freed their slots. Normal/priority zones cost one turn; a restricted zone
    costs two (in-flight token, then arrival). Splitting drones across several
    paths and link-capacity limits arrive in later slices.

    Attributes:
        _map: The parsed map to simulate.
    """

    def __init__(self, fly_in_map: FlyInMap) -> None:
        """Store the map to simulate.

        Args:
            fly_in_map: The parsed map whose drones will be routed.
        """
        self._map = fly_in_map

    def run(self) -> list[str]:
        """Simulate the drones and return the output, one line per turn.

        Returns:
            The movement lines, each a space-separated set of movement tokens
            ordered by ascending drone id. Entering a normal/priority zone is
            one ``D<ID>-<zone>`` turn; entering a restricted zone is two turns:
            an in-flight ``D<ID>-<from>-<to>`` token, then the arrival. Parked
            drones emit no token, so a busy turn may list fewer than every
            drone.

        Raises:
            UnsolvableMapError: If the start cannot reach the end.
        """
        route = self._shortest_route()
        drones = [
            Drone(i, route)
            for i in range(1, self._map.nb_drones + 1)
        ]
        lines: list[str] = []
        while any(drone.is_active for drone in drones):
            tokens = self._play_turn(drones)
            if not tokens:
                # No drone could move: a deadlock. Detecting and reporting
                # deadlocks is a later slice (M4.7); here we stop rather than
                # loop forever.
                break
            lines.append(" ".join(tokens))
        return lines

    def _shortest_route(self) -> tuple[str, ...]:
        """Return the cheapest start-to-end route, or fail if unreachable.

        Raises:
            UnsolvableMapError: If the start cannot reach the end.
        """
        path = Dijkstra(Graph(self._map), self._map).shortest_path()
        if path is None:
            raise UnsolvableMapError(
                f"no route from {self._map.start.name!r} to "
                f"{self._map.end.name!r}"
            )
        return path.zones

    def _play_turn(self, drones: list[Drone]) -> list[str]:
        """Plan and apply one atomic turn; return its tokens, id-ordered.

        Args:
            drones: Every drone in the simulation (delivered ones included).

        Returns:
            The movement tokens produced this turn, ordered by drone id.
        """
        movers = self._grant_moves(drones)
        movers.sort(key=lambda drone: drone.id)
        # Applying a granted move mutates only that drone, so the id order
        # gives a deterministic line without affecting correctness.
        return [self._apply_move(drone) for drone in movers]

    def _grant_moves(self, drones: list[Drone]) -> list[Drone]:
        """Decide, against the pre-turn snapshot, which drones may move.

        In-flight drones must land (they cannot wait on a connection). Parked
        drones are walked front-first (closest to the end first) so a zone's
        leavers free their slot before newcomers are admitted; ties at a zone
        break by ascending id for determinism.

        Args:
            drones: Every drone in the simulation.

        Returns:
            The drones granted a move this turn, unordered.
        """
        active = [drone for drone in drones if drone.is_active]
        granted = [drone for drone in active if drone.is_in_transit]
        parked = [drone for drone in active if drone.is_at_zone]
        free = self._free_slots(parked)
        parked.sort(key=lambda drone: (-drone.route_position, drone.id))
        for drone in parked:
            target = drone.next_zone
            if self._is_restricted(target):
                # Restricted take-off: reserving the arrival slot is M4.5
                # (open decision #15); a single drone has no contention.
                granted.append(drone)
            elif free[target] > 0:
                free[target] -= 1
                free[drone.current_zone] += 1  # its slot frees on exit
                granted.append(drone)
        return granted

    def _free_slots(self, parked: list[Drone]) -> dict[str, float]:
        """Room left in each zone before this turn's exits are applied.

        Args:
            parked: The drones currently parked on a zone.

        Returns:
            A zone-name to free-capacity map (``inf`` for the terminals).
        """
        free = {zone: self._capacity(zone) for zone in self._map.zones}
        for drone in parked:
            free[drone.current_zone] -= 1
        return free

    def _apply_move(self, drone: Drone) -> str:
        """Apply a granted move and return its token.

        Args:
            drone: A drone the plan granted a move this turn.

        Returns:
            The movement token for the move (take-off, landing, or step).
        """
        if drone.is_in_transit:
            return drone.advance()  # mandatory landing
        if self._is_restricted(drone.next_zone):
            return drone.takeoff()  # first of the two restricted turns
        return drone.advance()  # normal one-turn move

    def _capacity(self, zone_name: str) -> float:
        """The effective capacity of a zone (``inf`` for the terminals).

        Args:
            zone_name: The zone whose capacity is queried.

        Returns:
            The number of drones the zone holds at once; ``inf`` for start
            and end (their declared ``max_drones`` is ignored).
        """
        zone = self._map.zones[zone_name]
        if zone.is_start or zone.is_end:
            return float("inf")
        return zone.max_drones if zone.max_drones is not None else 1

    def _is_restricted(self, zone_name: str) -> bool:
        """Whether entering the named zone is a two-turn restricted transit."""
        return self._map.zones[zone_name].zone_type is ZoneType.RESTRICTED
