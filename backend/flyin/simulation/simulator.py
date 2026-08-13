"""Turn-based simulation of drones over a parsed map."""

from enum import Enum, auto

from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import ZoneType
from flyin.graph.graph import Graph
from flyin.pathfinding.dijkstra import Dijkstra
from flyin.shared.exceptions import UnsolvableMapError


class DroneState(Enum):
    """Lifecycle of a single drone as it walks its route.

    A drone is ``AT_ZONE`` when it stands on a zone ready to move,
    ``IN_TRANSIT`` while it occupies a connection toward a restricted zone
    it must land on next turn, and ``DELIVERED`` once it reaches the end.
    """

    AT_ZONE = auto()
    IN_TRANSIT = auto()
    DELIVERED = auto()


class Simulator:
    """Runs the turn-by-turn movement of the drones and yields the output.

    For now it routes a single drone (``D1``) along the cheapest path found by
    Dijkstra. Normal/priority zones cost one turn; a restricted zone costs two
    (in-flight token, then arrival). Multi-drone scheduling and capacities
    arrive in later slices.

    Attributes:
        _map: The parsed map to simulate.
    """

    def __init__(self, fly_in_map: FlyInMap) -> None:
        """Store the map to simulate.

        Args:
            fly_in_map: The parsed map whose drone(s) will be routed.
        """
        self._map = fly_in_map

    def run(self) -> list[str]:
        """Simulate the drone(s) and return the output, one line per turn.

        Returns:
            The movement lines, each a space-separated set of movement tokens
            (a single token per line while only one drone is routed). Entering
            a normal/priority zone is one ``D<ID>-<zone>`` turn; entering a
            restricted zone is two turns: an in-flight ``D<ID>-<from>-<to>``
            token, then the ``D<ID>-<zone>`` arrival.

        Raises:
            UnsolvableMapError: If the start cannot reach the end.
        """
        path = Dijkstra(Graph(self._map), self._map).shortest_path()
        if path is None:
            raise UnsolvableMapError(
                f"no route from {self._map.start.name!r} to "
                f"{self._map.end.name!r}"
            )
        zones = path.zones
        last = len(zones) - 1
        index = 0
        state = DroneState.DELIVERED if last == 0 else DroneState.AT_ZONE
        lines: list[str] = []
        # One loop turn = one output line. The drone's state drives the
        # transition: a restricted target splits into a take-off turn
        # (IN_TRANSIT) and a landing turn; any other move is a single turn.
        while state is not DroneState.DELIVERED:
            target = zones[index + 1]
            restricted = (
                self._map.zones[target].zone_type is ZoneType.RESTRICTED
            )
            if state is DroneState.AT_ZONE and restricted:
                lines.append(f"D1-{zones[index]}-{target}")
                state = DroneState.IN_TRANSIT
            else:
                lines.append(f"D1-{target}")
                index += 1
                state = (
                    DroneState.DELIVERED if index == last
                    else DroneState.AT_ZONE
                )
        return lines
