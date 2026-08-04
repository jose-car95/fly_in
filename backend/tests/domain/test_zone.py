from flyin.domain.zone import ZoneType


def test_move_cost_of_passable_zone_types() -> None:
    # Normal and priority both cost one turn to enter; restricted costs two.
    assert ZoneType.NORMAL.move_cost == 1
    assert ZoneType.PRIORITY.move_cost == 1
    assert ZoneType.RESTRICTED.move_cost == 2


def test_blocked_zone_is_impassable() -> None:
    # A blocked zone cannot be entered, encoded as no movement cost (None),
    # so it never joins the traversable graph built in M2.
    assert ZoneType.BLOCKED.move_cost is None
