"""Dijkstra shortest path over the traversable graph."""

import heapq

from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import ZoneType
from flyin.graph.graph import Graph
from flyin.pathfinding.path import Path


class Dijkstra:
    """Cheapest-route search from the map's start to its end.

    Dijkstra explores the graph in order of accumulated cost, always expanding
    the cheapest known zone first. Because every move cost is positive, the
    first time a zone is popped its cost is final. The cost of entering a zone
    is its type's ``move_cost`` (normal/priority 1, restricted 2); the start
    zone is where the drone already sits, so reaching it costs nothing.

    Zones are ordered by the key ``(turns, -priority_count)``: fewer turns
    always wins, and on a tie the route through more ``priority`` zones is
    preferred (the subject asks priority to be preferred, but never at the
    cost of extra turns). The zone name is the final, deterministic tie-break.

    ``heapq`` supplies the priority queue (a plain data structure); the
    algorithm itself is written here, no graph/pathfinding library involved.

    An optional per-zone ``penalties`` map adds extra cost to entering named
    zones. It only biases the search toward avoiding them (used to find
    diverging candidate paths); it is not a real move cost, so a penalized
    run's reported ``Path.cost`` is inflated accordingly.

    Attributes:
        _graph: The traversable adjacency (blocked zones already excluded).
        _map: The parsed map, read for each zone's move cost and the endpoints.
        _penalties: Extra search cost per zone name (empty for a plain run).
    """

    def __init__(
        self,
        graph: Graph,
        fly_in_map: FlyInMap,
        penalties: dict[str, int] | None = None
    ) -> None:
        """Store the graph and map to search over.

        Args:
            graph: The traversable adjacency to walk.
            fly_in_map: The parsed map, for move costs and start/end zones.
            penalties: Optional extra search cost per zone name, to bias the
                search away from already-used zones.
        """
        self._graph = graph
        self._map = fly_in_map
        self._penalties = penalties or {}

    def shortest_path(self) -> Path | None:
        """Return the cheapest route from start to end.

        Runs in O((V + E) log V): each zone and edge is processed once
        and every heap operation costs O(log V).

        Returns:
            The cheapest :class:`Path`, or ``None`` when the end cannot be
            reached from the start (a disconnected or blocked-off map).
        """
        start = self._map.start.name
        end = self._map.end.name
        # Ordering key per zone: (turns, -priority_count). A smaller tuple is
        # better, so fewer turns wins and, on a tie, more priority zones wins.
        best: dict[str, tuple[int, int]] = {start: (0, 0)}
        came_from: dict[str, str] = {}
        frontier: list[tuple[int, int, str]] = [(0, 0, start)]
        while frontier:
            turns, neg_priority, zone = heapq.heappop(frontier)
            if zone == end:
                return self._reconstruct(came_from, end, turns)
            if (turns, neg_priority) > best[zone]:
                # A better route was already settled: this entry is stale.
                continue
            for neighbor in self._graph.neighbors(zone):
                zone_type = self._map.zones[neighbor].zone_type
                step = zone_type.move_cost
                if step is None:
                    # A blocked zone is impassable; never step into it.
                    continue
                # A penalty biases the search away from an already-used zone
                # without removing it, so a forced funnel is still reusable.
                step += self._penalties.get(neighbor, 0)
                priority_bonus = 1 if zone_type is ZoneType.PRIORITY else 0
                key = (turns + step, neg_priority - priority_bonus)
                if neighbor not in best or key < best[neighbor]:
                    best[neighbor] = key
                    came_from[neighbor] = zone
                    heapq.heappush(frontier, (key[0], key[1], neighbor))
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
