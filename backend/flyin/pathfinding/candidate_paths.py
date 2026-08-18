"""Find several diverging start-to-end routes for load spreading."""

from enum import IntEnum

from flyin.domain.fly_in_map import FlyInMap
from flyin.graph.graph import Graph
from flyin.pathfinding.dijkstra import Dijkstra
from flyin.pathfinding.path import Path


class SearchPenalty(IntEnum):
    """Extra search cost that biases Dijkstra away from a used zone.

    ``USED_ZONE`` is large next to any real route cost, so a search avoids a
    zone a previous candidate path used whenever an alternative exists, yet
    still reuses a forced funnel (a zone with no alternative at all).
    """

    USED_ZONE = 1000


class CandidatePaths:
    """Finds up to ``count`` diverging routes via penalized Dijkstra.

    It runs Dijkstra, then penalizes the intermediate zones of each route
    found so the next search prefers a different middle, and repeats. Forced
    funnels (a zone with no alternative) are reused despite the penalty, so
    the routes share unavoidable bottlenecks but diverge where the map allows.
    It stops early when a search repeats a route or finds none, so it never
    returns more routes than actually exist.

    Attributes:
        _map: The map to search over.
        _count: The maximum number of routes to return.
    """

    def __init__(self, fly_in_map: FlyInMap, count: int) -> None:
        """Store the map and how many routes to look for.

        Args:
            fly_in_map: The map to search over.
            count: The maximum number of routes to return.
        """
        self._map = fly_in_map
        self._count = count

    def find(self) -> list[Path]:
        """Return up to ``count`` diverging routes, cheapest first.

        Reported ``Path.cost`` is the penalized search cost, not the real
        makespan, for every route after the first; callers route on the
        zones and measure the makespan by running the engine.

        Returns:
            The routes found, in the order they were discovered.
        """
        graph = Graph(self._map)
        penalties: dict[str, int] = {}
        paths: list[Path] = []
        seen: set[tuple[str, ...]] = set()
        for _ in range(self._count):
            path = Dijkstra(graph, self._map, penalties).shortest_path()
            if path is None or path.zones in seen:
                break
            paths.append(path)
            seen.add(path.zones)
            for zone in path.zones[1:-1]:
                penalties[zone] = (
                    penalties.get(zone, 0) + SearchPenalty.USED_ZONE
                )
        return paths
