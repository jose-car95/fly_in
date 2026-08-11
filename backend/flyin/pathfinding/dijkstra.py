"""Dijkstra shortest path over the traversable graph."""

import heapq

from flyin.domain.fly_in_map import FlyInMap
from flyin.graph.graph import Graph
from flyin.pathfinding.path import Path


class Dijkstra:
    """Cheapest-route search from the map's start to its end.

    Dijkstra explores the graph in order of accumulated cost, always expanding
    the cheapest known zone first. Because every move cost is positive, the
    first time a zone is popped its cost is final. The cost of entering a zone
    is its type's ``move_cost`` (normal/priority 1, restricted 2); the start
    zone is where the drone already sits, so reaching it costs nothing.

    ``heapq`` supplies the priority queue (a plain data structure); the
    algorithm itself is written here, no graph/pathfinding library involved.

    Attributes:
        _graph: The traversable adjacency (blocked zones already excluded).
        _map: The parsed map, read for each zone's move cost and the endpoints.
    """

    def __init__(self, graph: Graph, fly_in_map: FlyInMap) -> None:
        """Store the graph and map to search over.

        Args:
            graph: The traversable adjacency to walk.
            fly_in_map: The parsed map, for move costs and start/end zones.
        """
        self._graph = graph
        self._map = fly_in_map

    def shortest_path(self) -> Path | None:
        """Return the cheapest route from start to end.

        Returns:
            The cheapest :class:`Path`, or ``None`` when the end cannot be
            reached from the start (a disconnected or blocked-off map).
        """
        start = self._map.start.name
        end = self._map.end.name
        best: dict[str, int] = {start: 0}
        came_from: dict[str, str] = {}
        # (accumulated_cost, zone); heapq keeps the cheapest entry on top.
        frontier: list[tuple[int, str]] = [(0, start)]
        while frontier:
            cost, zone = heapq.heappop(frontier)
            if zone == end:
                return self._reconstruct(came_from, end, cost)
            if cost > best[zone]:
                # A cheaper route was already settled: this entry is stale.
                continue
            for neighbor in self._graph.neighbors(zone):
                step = self._map.zones[neighbor].zone_type.move_cost
                if step is None:
                    # A blocked zone is impassable; never step into it.
                    continue
                new_cost = cost + step
                if neighbor not in best or new_cost < best[neighbor]:
                    best[neighbor] = new_cost
                    came_from[neighbor] = zone
                    heapq.heappush(frontier, (new_cost, neighbor))
        return None

    @staticmethod
    def _reconstruct(came_from: dict[str, str], end: str, cost: int) -> Path:
        """Walk predecessors back from end to start to build the route.

        Args:
            came_from: Predecessor of each settled zone.
            end: The end zone the search reached.
            cost: The total cost of reaching the end.

        Returns:
            The path from start to end with its total cost.
        """
        zones = [end]
        while zones[-1] in came_from:
            zones.append(came_from[zones[-1]])
        zones.reverse()
        return Path(zones=tuple(zones), cost=cost)
