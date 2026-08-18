from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone
from flyin.pathfinding.candidate_paths import CandidatePaths


def _map(
    zones: dict[str, Zone], connections: list[Connection]
) -> FlyInMap:
    """Build a one-drone map from zones and connections for a test."""
    return FlyInMap(
        nb_drones=1,
        zones=zones,
        connections=connections,
        start=zones["start"],
        end=zones["goal"]
    )


def test_finds_two_paths_diverging_after_a_shared_gate() -> None:
    # start and goal are forced funnels (a single exit/entry), so both
    # candidate paths reuse 'gate' but diverge across the parallel middle.
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "gate": Zone("gate", 1, 0),
        "mid_a": Zone("mid_a", 2, 1),
        "mid_b": Zone("mid_b", 2, -1),
        "goal": Zone("goal", 3, 0, is_end=True)
    }
    connections = [
        Connection("start", "gate"),
        Connection("gate", "mid_a"),
        Connection("gate", "mid_b"),
        Connection("mid_a", "goal"),
        Connection("mid_b", "goal")
    ]

    routes = [
        path.zones
        for path in CandidatePaths(_map(zones, connections), 2).find()
    ]

    assert len(routes) == 2
    assert ("start", "gate", "mid_a", "goal") in routes
    assert ("start", "gate", "mid_b", "goal") in routes


def test_returns_only_the_paths_that_actually_exist() -> None:
    # A single linear route: asking for two candidates yields just one,
    # because penalizing 'a' still leaves it as the only way through.
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    connections = [Connection("start", "a"), Connection("a", "goal")]

    paths = CandidatePaths(_map(zones, connections), 2).find()

    assert len(paths) == 1
    assert paths[0].zones == ("start", "a", "goal")
