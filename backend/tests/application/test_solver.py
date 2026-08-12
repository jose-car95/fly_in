import pytest

from flyin.application.solver import FlyinSolver
from flyin.shared.exceptions import MapParseError, UnsolvableMapError

_LINEAR_MAP = (
    "nb_drones: 1\n"
    "start_hub: start 0 0\n"
    "hub: a 1 0\n"
    "end_hub: goal 2 0\n"
    "connection: start-a\n"
    "connection: a-goal\n"
)


def test_solves_map_text_into_movement_lines() -> None:
    result = FlyinSolver().solve_text(_LINEAR_MAP)

    assert result.movement_lines == ["D1-a", "D1-goal"]
    assert result.warnings == []


def test_warns_and_normalizes_a_restricted_terminal() -> None:
    text = (
        "nb_drones: 1\n"
        "start_hub: start 0 0 [zone=restricted]\n"
        "hub: a 1 0\n"
        "end_hub: goal 2 0\n"
        "connection: start-a\n"
        "connection: a-goal\n"
    )

    result = FlyinSolver().solve_text(text)

    # The nonsensical restricted terminal is treated as normal (the map still
    # solves) and reported as a warning naming the zone.
    assert result.movement_lines == ["D1-a", "D1-goal"]
    assert len(result.warnings) == 1
    assert "start" in result.warnings[0]


def test_propagates_parse_error() -> None:
    # No nb_drones header: the parser rejects it, and the solver lets it out.
    with pytest.raises(MapParseError):
        FlyinSolver().solve_text("start_hub: s 0 0\nend_hub: goal 1 0\n")


def test_propagates_unsolvable_map() -> None:
    text = (
        "nb_drones: 1\n"
        "start_hub: start 0 0\n"
        "hub: island 1 0\n"
        "end_hub: goal 2 0\n"
        "connection: start-island\n"
    )
    with pytest.raises(UnsolvableMapError):
        FlyinSolver().solve_text(text)
