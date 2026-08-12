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
    assert FlyinSolver().solve_text(_LINEAR_MAP) == ["D1-a", "D1-goal"]


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
