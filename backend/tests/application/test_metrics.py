from flyin.application.metrics import RunMetrics


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
