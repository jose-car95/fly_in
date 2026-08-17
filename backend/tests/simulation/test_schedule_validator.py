import pytest

from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone, ZoneType
from flyin.shared.exceptions import InvalidScheduleError
from flyin.simulation.schedule_validator import ScheduleValidator


def _map(
    zones: dict[str, Zone],
    connections: list[Connection],
    nb_drones: int = 1
) -> FlyInMap:
    """Build a map from zones and connections for a validator test."""
    return FlyInMap(
        nb_drones=nb_drones,
        zones=zones,
        connections=connections,
        start=zones["start"],
        end=zones["goal"]
    )


_LINEAR = _map(
    {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0),
        "goal": Zone("goal", 2, 0, is_end=True)
    },
    [Connection("start", "a"), Connection("a", "goal")]
)

_WITH_RESTRICTED = _map(
    {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0),
        "r": Zone("r", 2, 0, zone_type=ZoneType.RESTRICTED),
        "goal": Zone("goal", 3, 0, is_end=True)
    },
    [
        Connection("start", "a"),
        Connection("a", "r"),
        Connection("r", "goal")
    ]
)


def test_accepts_a_legal_single_drone_schedule() -> None:
    # A legal walk start->a->goal must not raise.
    ScheduleValidator(_LINEAR, ["D1-a", "D1-goal"]).validate()


def test_accepts_a_restricted_two_turn_transit() -> None:
    # The in-flight token followed by its arrival is the legal shape.
    ScheduleValidator(
        _WITH_RESTRICTED, ["D1-a", "D1-a-r", "D1-r", "D1-goal"]
    ).validate()


def test_rejects_a_jump_over_a_missing_connection() -> None:
    # 'start' and 'goal' share no connection: hopping straight there is
    # a teleport the validator must reject.
    with pytest.raises(InvalidScheduleError):
        ScheduleValidator(_LINEAR, ["D1-goal"]).validate()


def test_rejects_a_schedule_that_does_not_reach_end() -> None:
    # The drone stops at 'a' and never reaches 'goal'.
    with pytest.raises(InvalidScheduleError):
        ScheduleValidator(_LINEAR, ["D1-a"]).validate()


def test_rejects_an_in_flight_token_without_its_arrival() -> None:
    # An in-flight 'D1-a-r' must be followed by the 'D1-r' arrival, not by
    # some other zone.
    with pytest.raises(InvalidScheduleError):
        ScheduleValidator(
            _WITH_RESTRICTED, ["D1-a", "D1-a-r", "D1-goal"]
        ).validate()


def _two_drone_linear() -> FlyInMap:
    """A start->a->goal map with 'a' at capacity 1 and two drones."""
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    connections = [Connection("start", "a"), Connection("a", "goal")]
    return _map(zones, connections, nb_drones=2)


def test_accepts_a_legal_two_drone_queue() -> None:
    # Two drones pipeline through 'a' one at a time: a legal schedule.
    ScheduleValidator(
        _two_drone_linear(), ["D1-a", "D1-goal D2-a", "D2-goal"]
    ).validate()


def test_rejects_two_drones_in_a_capacity_one_zone() -> None:
    # Both drones sit in 'a' (capacity 1) on the same turn: illegal even
    # though each drone's own walk start->a->goal is legal.
    with pytest.raises(InvalidScheduleError):
        ScheduleValidator(
            _two_drone_linear(), ["D1-a D2-a", "D1-goal D2-goal"]
        ).validate()


def test_rejects_a_drone_left_in_flight_mid_schedule() -> None:
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "r1": Zone("r1", 1, 1, zone_type=ZoneType.RESTRICTED),
        "r2": Zone("r2", 1, -1, zone_type=ZoneType.RESTRICTED),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    connections = [
        Connection("start", "r1"),
        Connection("start", "r2"),
        Connection("r1", "goal"),
        Connection("r2", "goal")
    ]
    # D1 takes off toward r1, but the next turn only moves D2: D1 is
    # stranded on the connection instead of landing, which is illegal.
    with pytest.raises(InvalidScheduleError):
        ScheduleValidator(
            _map(zones, connections, nb_drones=2),
            ["D1-start-r1", "D2-start-r2"]
        ).validate()
