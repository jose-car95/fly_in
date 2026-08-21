"""Turn-based simulation of drones over a parsed map."""

from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import ZoneType
from flyin.graph.graph import Graph
from flyin.pathfinding.dijkstra import Dijkstra
from flyin.shared.exceptions import InvalidScheduleError, UnsolvableMapError
from flyin.simulation.drone import Drone
from flyin.simulation.schedule_validator import ScheduleValidator


class Simulator:
    """Runs the turn-by-turn movement of the drones and yields the output.

    It routes ``nb_drones`` drones along the single cheapest path found by
    Dijkstra and moves them one turn at a time. Each turn is computed as a
    whole plan against a snapshot of the world and applied atomically, so the
    output never depends on the order in which the drones are iterated: a
    zone admits a newcomer only if it has room once this turn's leavers have
    freed their slots. Normal/priority zones cost one turn; a restricted zone
    costs two (in-flight token, then arrival), and each zone and connection is
    held to its capacity.

    A fast optimistic pass pipelines restricted zones one drone per turn; on
    the rare map where that would overfill a restricted zone, the schedule is
    rejected by the independent validator and a conservative pass (which
    reserves a restricted zone across the whole transit) is used instead. The
    result is fast where it can be and always valid: a valid slow schedule
    beats an invalid fast one.

    Attributes:
        _map: The parsed map to simulate.
        _optimistic: Whether the current pass pipelines restricted zones.
    """

    def __init__(self, fly_in_map: FlyInMap) -> None:
        """Store the map to simulate.

        Args:
            fly_in_map: The parsed map whose drones will be routed.
        """
        self._map = fly_in_map
        self._optimistic = True

    def run(self) -> list[str]:
        """Simulate the drones and return the output, one line per turn.

        Runs the fast optimistic pass first; if its schedule is illegal (a
        restricted zone would overfill), falls back to the conservative pass,
        which is always valid.

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
        optimistic = self._simulate(route, optimistic=True)
        if self._is_valid(optimistic):
            return optimistic
        return self._simulate(route, optimistic=False)

    def _simulate(
        self, route: tuple[str, ...], optimistic: bool
    ) -> list[str]:
        """Run one full pass over the route and return its movement lines.

        A turn that grants no token means no drone can progress; the pass
        stops there instead of looping forever.

        Args:
            route: The shared cheapest route every drone follows.
            optimistic: Whether restricted zones pipeline one drone per turn.

        Returns:
            The movement lines produced by this pass.
        """
        self._optimistic = optimistic
        drones = [
            Drone(i, route)
            for i in range(1, self._map.nb_drones + 1)
        ]
        lines: list[str] = []
        while any(drone.is_active for drone in drones):
            tokens = self._play_turn(drones)
            if not tokens:
                break
            lines.append(" ".join(tokens))
        return lines

    def _is_valid(self, lines: list[str]) -> bool:
        """Whether the independent validator accepts these movement lines."""
        try:
            ScheduleValidator(self._map, lines).validate()
        except InvalidScheduleError:
            return False
        return True

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

        Each move was granted against the pre-turn snapshot and mutates only
        its own drone, so applying them in id order gives a deterministic line
        without affecting correctness.

        Args:
            drones: Every drone in the simulation (delivered ones included).

        Returns:
            The movement tokens produced this turn, ordered by drone id.
        """
        movers = self._grant_moves(drones)
        movers.sort(key=lambda drone: drone.id)
        return [self._apply_move(drone) for drone in movers]

    def _grant_moves(self, drones: list[Drone]) -> list[Drone]:
        """Decide, against the pre-turn snapshot, which drones may move.

        In-flight drones must land (they cannot wait on a connection). Parked
        drones are walked front-first (closest to the end first) so a zone's
        leavers free their slot before newcomers are admitted; ties at a zone
        break by ascending id for determinism. A move needs both room in the
        target zone and a free crossing on the connection it uses.

        A normal step and a restricted take-off gate identically: both leave
        the origin and claim the target. For a restricted target the claim
        reserves the arrival slot and the connection is metered only on this
        take-off turn, which is what keeps the mandatory landing next turn
        always legal.

        Args:
            drones: Every drone in the simulation.

        Returns:
            The drones granted a move this turn, unordered.
        """
        active = [drone for drone in drones if drone.is_active]
        granted = [drone for drone in active if drone.is_in_transit]
        parked = [drone for drone in active if drone.is_at_zone]
        free = self._free_slots(active)
        link_free = self._link_slots()
        parked.sort(key=lambda drone: (-drone.route_position, drone.id))
        for drone in parked:
            origin, target = drone.current_zone, drone.next_zone
            link = frozenset((origin, target))
            if free[target] > 0 and link_free[link] > 0:
                free[target] -= 1
                free[origin] += 1
                link_free[link] -= 1
                granted.append(drone)
        return granted

    def _free_slots(self, active: list[Drone]) -> dict[str, float]:
        """Room left in each zone before this turn's exits are applied.

        Parked drones always count against their zone. In the optimistic pass
        an in-flight drone does not hold its restricted destination, so a
        follower can take off toward that zone the same turn the occupant
        leaves it: restricted zones pipeline one drone per turn. In the
        conservative pass an in-flight drone keeps its destination reserved
        across the whole transit, which is always valid but pipelines one
        drone every two turns.

        Args:
            active: The drones still in play (parked or in flight).

        Returns:
            A zone-name to free-capacity map (``inf`` for the terminals).
        """
        free = {zone: self._capacity(zone) for zone in self._map.zones}
        for drone in active:
            if drone.is_at_zone:
                free[drone.current_zone] -= 1
            elif not self._optimistic:
                free[drone.next_zone] -= 1
        return free

    def _link_slots(self) -> dict[frozenset[str], int]:
        """Crossings each connection allows this turn, by undirected key.

        Returns:
            A map from ``frozenset({a, b})`` to its remaining crossings. The
            capacity is shared across both directions and defaults to 1.
        """
        slots: dict[frozenset[str], int] = {}
        for conn in self._map.connections:
            capacity = conn.max_link_capacity
            slots[frozenset((conn.zone_a, conn.zone_b))] = (
                capacity if capacity is not None else 1
            )
        return slots

    def _apply_move(self, drone: Drone) -> str:
        """Apply a granted move and return its token.

        Args:
            drone: A drone the plan granted a move this turn.

        Returns:
            The movement token: an in-transit drone lands (its mandatory
            second restricted turn), a drone bound for a restricted zone takes
            off (the first of the two turns), and any other drone steps once.
        """
        if drone.is_in_transit:
            return drone.advance()
        if self._is_restricted(drone.next_zone):
            return drone.takeoff()
        return drone.advance()

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
