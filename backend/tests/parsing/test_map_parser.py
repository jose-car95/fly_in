from pathlib import Path

import pytest

from flyin.domain.zone import Zone, ZoneType
from flyin.parsing.map_parser import MapParser

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "edge-cases"


def test_parses_minimal_map() -> None:
    text = (FIXTURES_DIR / "valid_minimal.txt").read_text()

    result = MapParser(text).parse()

    assert result.nb_drones == 1
    assert result.start == Zone(name="start", x=0, y=0, is_start=True)
    assert result.end == Zone(name="goal", x=1, y=0, is_end=True)
    assert result.zones == {"start": result.start, "goal": result.end}
    assert len(result.connections) == 1
    assert result.connections[0].zone_a == "start"
    assert result.connections[0].zone_b == "goal"


def test_parses_regular_hub_with_metadata() -> None:
    text = (FIXTURES_DIR / "valid_with_hub.txt").read_text()

    result = MapParser(text).parse()

    # A regular `hub:` is a non-terminal zone; its max_drones tag is parsed
    # (M1.4b) and it stays NORMAL since it carries no zone= tag.
    assert result.zones["junction"] == Zone(
        name="junction", x=1, y=0, max_drones=2
    )
    # start/end lines also carry metadata brackets that must not break parsing.
    assert result.start == Zone(name="start", x=0, y=0, is_start=True)
    assert result.end == Zone(name="goal", x=2, y=0, is_end=True)


def test_error_reports_physical_line_number() -> None:
    text = (FIXTURES_DIR / "invalid_missing_nb_drones.txt").read_text()

    # The first significant line sits at physical line 6 (four comments plus a
    # blank line precede it); the error must point there, not at line 1.
    with pytest.raises(ValueError, match=r"line 6"):
        MapParser(text).parse()


def test_parses_zone_type_metadata_in_any_order() -> None:
    text = (FIXTURES_DIR / "valid_zone_types.txt").read_text()

    result = MapParser(text).parse()

    assert result.zones["slow"].zone_type is ZoneType.RESTRICTED
    # zone= after color= proves the tag order does not matter.
    assert result.zones["fast"].zone_type is ZoneType.PRIORITY
    # No zone= tag (only color/max_drones) falls back to the NORMAL default.
    assert result.zones["plain"].zone_type is ZoneType.NORMAL
    assert result.start.zone_type is ZoneType.NORMAL


def test_parses_max_drones_ignoring_terminals() -> None:
    text = (FIXTURES_DIR / "valid_zone_capacity.txt").read_text()

    result = MapParser(text).parse()

    assert result.zones["narrow"].max_drones == 2
    # No max_drones tag stays None (the default-1 sentinel).
    assert result.zones["wide"].max_drones is None
    # max_drones on start/end is ignored: terminals are unlimited.
    assert result.start.max_drones is None
    assert result.end.max_drones is None


def test_parses_link_capacity_and_clean_endpoints() -> None:
    text = (FIXTURES_DIR / "valid_link_capacity.txt").read_text()

    result = MapParser(text).parse()

    start_mid, mid_goal = result.connections
    # The [...] block must not leak into the endpoint names.
    assert start_mid.zone_a == "start"
    assert start_mid.zone_b == "mid"
    assert start_mid.max_link_capacity == 3
    # No tag → None (the default-1 sentinel).
    assert mid_goal.zone_b == "goal"
    assert mid_goal.max_link_capacity is None
