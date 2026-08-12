import pytest

from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone, ZoneType
from flyin.shared.exceptions import InvalidScheduleError
from flyin.simulation.schedule_validator import ScheduleValidator


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
