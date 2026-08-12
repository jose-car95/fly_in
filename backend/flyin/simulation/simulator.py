"""Turn-based simulation of drones over a parsed map."""

from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import ZoneType
from flyin.graph.graph import Graph
from flyin.pathfinding.dijkstra import Dijkstra
from flyin.shared.exceptions import UnsolvableMapError


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
        lines: list[str] = []
        # The drone stands on the first zone; each following zone is one hop.
        for origin, target in zip(path.zones, path.zones[1:]):
            if self._map.zones[target].zone_type is ZoneType.RESTRICTED:
                # A restricted target takes 2 turns: the drone is first in
                # flight on the connection, then lands the next turn.
                lines.append(f"D1-{origin}-{target}")
            lines.append(f"D1-{target}")
        return lines
