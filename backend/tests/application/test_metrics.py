from flyin.application.metrics import RunMetrics
from flyin.application.solver import FlyinSolver

_LINEAR = (
    "nb_drones: 2\n"
    "start_hub: start 0 0\n"
    "hub: waypoint1 1 0\n"
    "hub: waypoint2 2 0\n"
    "end_hub: goal 3 0\n"
    "connection: start-waypoint1\n"
    "connection: waypoint1-waypoint2\n"
    "connection: waypoint2-goal\n"
)


def test_turns_is_the_number_of_movement_lines() -> None:
    stats = RunMetrics(["D1-a", "D1-b D2-a", "D1-goal"])

    assert stats.turns == 3


def test_total_moves_counts_every_token() -> None:
    # Two tokens on the middle line: total moves counts each one.
    stats = RunMetrics(["D1-a", "D1-b D2-a", "D1-goal"])

    assert stats.total_moves == 4


def test_restricted_transit_counts_as_two_moves() -> None:
    # A two-turn restricted move prints an in-flight token then a landing
    # token: two tokens, matching its cost of 2. Counting tokens therefore
    # yields the total path cost without re-deriving any move cost.
    stats = RunMetrics(["D1-a-vault", "D1-vault"])

    assert stats.total_moves == 2


def test_drones_per_turn_is_total_moves_over_turns() -> None:
    stats = RunMetrics(["D1-a", "D1-b D2-a", "D1-goal"])

    # Four moves across three turns.
    assert stats.drones_per_turn == 4 / 3


def test_an_empty_run_reports_zeros_without_dividing_by_zero() -> None:
    stats = RunMetrics([])

    assert stats.turns == 0
    assert stats.total_moves == 0
    assert stats.drones_per_turn == 0.0


def test_capacity_lines_track_zones_and_connections() -> None:
    result = FlyinSolver().solve_text(_LINEAR)

    lines = RunMetrics(result.movement_lines).capacity_lines(result.fly_in_map)
    text = "\n".join(lines)

    assert "Turn 1 capacity:" in text
    assert "  Zone start: 1/inf drones" in text
    assert "  Zone waypoint1: 1/1 drones" in text
    assert "  Connection start-waypoint1: 1/1 used" in text


def test_capacity_lines_have_a_block_per_turn() -> None:
    result = FlyinSolver().solve_text(_LINEAR)

    lines = RunMetrics(result.movement_lines).capacity_lines(result.fly_in_map)

    headers = [line for line in lines if line.startswith("Turn ")]
    assert len(headers) == len(result.movement_lines)
