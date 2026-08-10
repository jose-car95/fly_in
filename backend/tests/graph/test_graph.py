from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone, ZoneType
from flyin.graph.graph import Graph


def _map(zones: dict[str, Zone], connections: list[Connection]) -> FlyInMap:
    """Build a FlyInMap from zones and connections for a graph test."""
    return FlyInMap(
        nb_drones=1,
        zones=zones,
        connections=connections,
        start=zones["start"],
        end=zones["goal"]
    )


def test_neighbors_are_undirected() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "mid": Zone("mid", 1, 0),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    graph = Graph(_map(
        zones, [Connection("start", "mid"), Connection("mid", "goal")]
    ))

    # An undirected edge a-b makes each endpoint a neighbor of the other.
    assert graph.neighbors("mid") == frozenset({"start", "goal"})
    assert graph.neighbors("start") == frozenset({"mid"})
    assert graph.neighbors("goal") == frozenset({"mid"})


def test_blocked_zone_is_excluded_from_the_graph() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "plain": Zone("plain", 1, 0),
        "wall": Zone("wall", 2, 0, zone_type=ZoneType.BLOCKED),
        "goal": Zone("goal", 3, 0, is_end=True)
    }
    graph = Graph(_map(zones, [
        Connection("start", "plain"),
        Connection("plain", "wall"),
        Connection("plain", "goal"),
        Connection("wall", "goal")
    ]))

    # A blocked zone is impassable: no edge leads into it and it has none out,
    # so it never appears in the traversable graph.
    assert graph.neighbors("plain") == frozenset({"start", "goal"})
    assert "wall" not in graph.neighbors("goal")
    assert graph.neighbors("wall") == frozenset()
