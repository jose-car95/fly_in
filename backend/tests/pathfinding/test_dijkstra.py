from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone, ZoneType
from flyin.graph.graph import Graph
from flyin.pathfinding.dijkstra import Dijkstra


def _dijkstra(
    zones: dict[str, Zone], connections: list[Connection]
) -> Dijkstra:
    """Wire a Dijkstra over a map built from zones and connections."""
    fly_in = FlyInMap(
        nb_drones=1,
        zones=zones,
        connections=connections,
        start=zones["start"],
        end=zones["goal"]
    )
    return Dijkstra(Graph(fly_in), fly_in)


def test_prefers_the_cheaper_path_by_cost() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "cheap": Zone("cheap", 1, 1),
        "slow": Zone("slow", 1, -1, zone_type=ZoneType.RESTRICTED),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    connections = [
        Connection("start", "cheap"),
        Connection("cheap", "goal"),
        Connection("start", "slow"),
        Connection("slow", "goal")
    ]

    path = _dijkstra(zones, connections).shortest_path()

    # Both routes are two hops, but 'slow' is restricted (cost 2), so the
    # route through the normal 'cheap' zone wins on total cost.
    assert path is not None
    assert path.zones == ("start", "cheap", "goal")
    assert path.cost == 2


def test_more_hops_but_cheaper_beats_fewer_expensive_hops() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "r1": Zone("r1", 1, 1, zone_type=ZoneType.RESTRICTED),
        "r2": Zone("r2", 2, 1, zone_type=ZoneType.RESTRICTED),
        "n1": Zone("n1", 1, -1),
        "n2": Zone("n2", 2, -1),
        "n3": Zone("n3", 3, -1),
        "goal": Zone("goal", 4, 0, is_end=True)
    }
    connections = [
        Connection("start", "r1"),
        Connection("r1", "r2"),
        Connection("r2", "goal"),
        Connection("start", "n1"),
        Connection("n1", "n2"),
        Connection("n2", "n3"),
        Connection("n3", "goal")
    ]

    path = _dijkstra(zones, connections).shortest_path()

    # Short route: 3 hops through two restricted zones -> cost 2+2+1 = 5.
    # Long route: 4 hops through normal zones -> cost 1+1+1+1 = 4. Dijkstra
    # picks the cheaper one; plain BFS (counting hops) would pick the short.
    assert path is not None
    assert path.zones == ("start", "n1", "n2", "n3", "goal")
    assert path.cost == 4


def test_returns_none_when_end_is_unreachable() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "island": Zone("island", 1, 0),
        "goal": Zone("goal", 3, 0, is_end=True)
    }
    # start reaches 'island' but nothing reaches 'goal': the graph is split.
    connections = [Connection("start", "island")]

    assert _dijkstra(zones, connections).shortest_path() is None


def test_prefers_a_priority_zone_on_equal_cost() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "plain": Zone("plain", 1, 1),
        "vip": Zone("vip", 1, -1, zone_type=ZoneType.PRIORITY),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    connections = [
        Connection("start", "plain"),
        Connection("plain", "goal"),
        Connection("start", "vip"),
        Connection("vip", "goal")
    ]

    path = _dijkstra(zones, connections).shortest_path()

    # Both routes cost 2 turns, but the route through the priority zone 'vip'
    # wins the tie -- even though 'plain' sorts first by name.
    assert path is not None
    assert path.zones == ("start", "vip", "goal")
    assert path.cost == 2


def test_priority_preference_never_sacrifices_turns() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "vip": Zone("vip", 1, 1, zone_type=ZoneType.PRIORITY),
        "mid": Zone("mid", 2, 1),
        "plain": Zone("plain", 1, -1),
        "goal": Zone("goal", 3, 0, is_end=True)
    }
    connections = [
        Connection("start", "vip"),
        Connection("vip", "mid"),
        Connection("mid", "goal"),
        Connection("start", "plain"),
        Connection("plain", "goal")
    ]

    path = _dijkstra(zones, connections).shortest_path()

    # The priority route start-vip-mid-goal costs 3 turns; the plain route
    # costs 2. Priority only breaks ties, so the cheaper route still wins.
    assert path is not None
    assert path.zones == ("start", "plain", "goal")
    assert path.cost == 2
