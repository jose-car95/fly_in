import pytest

from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone, ZoneType
from flyin.shared.exceptions import UnsolvableMapError
from flyin.simulation.schedule_validator import ScheduleValidator
from flyin.simulation.simulator import Simulator


def _map(
    zones: dict[str, Zone],
    connections: list[Connection],
    nb_drones: int = 1
) -> FlyInMap:
    """Build a map from zones and connections for a sim test."""
    return FlyInMap(
        nb_drones=nb_drones,
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


def test_restricted_zone_takes_two_turns() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0),
        "r": Zone("r", 2, 0, zone_type=ZoneType.RESTRICTED),
        "goal": Zone("goal", 3, 0, is_end=True)
    }
    connections = [
        Connection("start", "a"),
        Connection("a", "r"),
        Connection("r", "goal")
    ]

    lines = Simulator(_map(zones, connections)).run()

    # Entering 'r' costs 2 turns: turn 1 the drone is in flight on the
    # 'a-r' connection, turn 2 it lands on 'r'. Normal zones stay 1 turn.
    assert lines == ["D1-a", "D1-a-r", "D1-r", "D1-goal"]


def test_two_drones_queue_on_a_capacity_one_zone() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    connections = [Connection("start", "a"), Connection("a", "goal")]

    lines = Simulator(_map(zones, connections, nb_drones=2)).run()

    # 'a' holds one drone at a time, so the drones pipeline through it. D1
    # enters 'a' alone (D2 waits at start, omitted); next turn D1 leaves for
    # 'goal', freeing 'a' the same turn, and D2 takes 'a'; then D2 reaches
    # 'goal'. Tokens on a line are ordered by ascending drone id.
    assert lines == ["D1-a", "D1-goal D2-a", "D2-goal"]


def test_zone_capacity_above_one_admits_several_drones() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0, max_drones=2),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    connections = [Connection("start", "a"), Connection("a", "goal")]

    lines = Simulator(_map(zones, connections, nb_drones=3)).run()

    # 'a' holds two drones at once, so D1 and D2 enter together while D3
    # waits; next turn both leave for 'goal', freeing 'a', and D3 enters.
    assert lines == ["D1-a D2-a", "D1-goal D2-goal D3-a", "D3-goal"]


def test_engine_output_passes_the_independent_validator() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0),
        "r": Zone("r", 2, 0, zone_type=ZoneType.RESTRICTED),
        "goal": Zone("goal", 3, 0, is_end=True)
    }
    connections = [
        Connection("start", "a"),
        Connection("a", "r"),
        Connection("r", "goal")
    ]
    fly_in_map = _map(zones, connections)

    lines = Simulator(fly_in_map).run()

    # The independent judge must accept the engine's own output: the two
    # M3 pieces check each other instead of trusting the planner.
    ScheduleValidator(fly_in_map, lines).validate()


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
