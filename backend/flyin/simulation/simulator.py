"""Turn-based simulation of drones over a parsed map."""

from flyin.domain.fly_in_map import FlyInMap
from flyin.graph.graph import Graph
from flyin.pathfinding.dijkstra import Dijkstra
from flyin.shared.exceptions import UnsolvableMapError


class Simulator:
    """Runs the turn-by-turn movement of the drones and yields the output.

    For now it routes a single drone (``D1``) along the cheapest path found by
    Dijkstra, emitting one movement token per turn. Multi-drone scheduling,
    restricted two-turn transit and capacities arrive in later slices.

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
            The movement lines, each a space-separated set of ``D<ID>-<zone>``
            tokens (a single token per line while only one drone is routed).

        Raises:
            UnsolvableMapError: If the start cannot reach the end.
        """
        path = Dijkstra(Graph(self._map), self._map).shortest_path()
        if path is None:
            raise UnsolvableMapError(
                f"no route from {self._map.start.name!r} to "
                f"{self._map.end.name!r}"
            )
        # The drone starts at 'start' and enters one zone per turn, so each
        # entered zone (the path without start) is that turn's movement token.
        return [f"D1-{zone}" for zone in path.zones[1:]]
