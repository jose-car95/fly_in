import pytest

from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone
from flyin.shared.exceptions import UnsolvableMapError
from flyin.simulation.simulator import Simulator


def _map(
    zones: dict[str, Zone], connections: list[Connection]
) -> FlyInMap:
    """Build a one-drone map from zones and connections for a sim test."""
    return FlyInMap(
        nb_drones=1,
        zones=zones,
        connections=connections,
        start=zones["start"],
        end=zones["goal"]
    )


def test_single_drone_walks_its_route() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0),
        "b": Zone("b", 2, 0),
        "goal": Zone("goal", 3, 0, is_end=True)
    }
    connections = [
        Connection("start", "a"),
        Connection("a", "b"),
        Connection("b", "goal")
    ]

    lines = Simulator(_map(zones, connections)).run()

    # One drone enters one zone per turn; each turn is a line with its token.
    assert lines == ["D1-a", "D1-b", "D1-goal"]


def test_unsolvable_map_raises() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "island": Zone("island", 1, 0),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    # 'goal' is in its own component: the map parses but has no route.
    connections = [Connection("start", "island")]

    with pytest.raises(UnsolvableMapError):
        Simulator(_map(zones, connections)).run()
