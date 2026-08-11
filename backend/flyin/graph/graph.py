"""The traversable graph of a Fly-In map."""

from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import ZoneType


class Graph:
    """Undirected adjacency of the zones a drone may actually move through.

    Built once from a parsed :class:`FlyInMap`, the graph keeps, for each
    passable zone, the set of zones directly reachable from it. ``blocked``
    zones are impassable, so they are left out entirely: they are not nodes and
    no edge touches them. A connection whose endpoint is blocked contributes no
    edge. The adjacency is stored as a list (dict of node to neighbor set),
    which is the memory-efficient choice for the sparse maps of this project.

    Attributes:
        _adjacency: Maps each passable zone name to the set of its neighbors.
    """

    def __init__(self, fly_in_map: FlyInMap) -> None:
        """Build the traversable adjacency from a parsed map.

        Args:
            fly_in_map: The parsed map whose zones and connections define the
                graph.
        """
        self._adjacency = self._build_adjacency(fly_in_map)

    def neighbors(self, name: str) -> frozenset[str]:
        """Return the zones directly reachable from ``name``.

        Args:
            name: The zone whose neighbors are wanted.

        Returns:
            The neighbor names, empty for an isolated zone or for a name that
            is not a node of the graph (e.g. a blocked zone).
        """
        return frozenset(self._adjacency.get(name, set()))

    @staticmethod
    def _build_adjacency(fly_in_map: FlyInMap) -> dict[str, set[str]]:
        """Turn zones and connections into an undirected adjacency.

        Only passable (non-blocked) zones become nodes, and an edge is kept
        only when both of its endpoints are passable. This runs in O(V + E):
        each zone and connection is touched once.

        Args:
            fly_in_map: The parsed map to read zones and connections from.

        Returns:
            Each passable zone name mapped to its set of neighbor names.
        """
        passable = {
            name
            for name, zone in fly_in_map.zones.items()
            if zone.zone_type is not ZoneType.BLOCKED
        }
        adjacency: dict[str, set[str]] = {name: set() for name in passable}
        for connection in fly_in_map.connections:
            zone_a, zone_b = connection.zone_a, connection.zone_b
            if zone_a in passable and zone_b in passable:
                adjacency[zone_a].add(zone_b)
                adjacency[zone_b].add(zone_a)
        return adjacency
