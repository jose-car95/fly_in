from pathlib import Path

import pytest

from flyin.domain.zone import Zone, ZoneType
from flyin.parsing.map_parser import MapParser
from flyin.shared.exceptions import MapParseError

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

    # A regular `hub:` is a non-terminal zone; its max_drones and color tags
    # are parsed and it stays NORMAL since it carries no zone= tag.
    assert result.zones["junction"] == Zone(
        name="junction", x=1, y=0, max_drones=2, color="yellow"
    )
    # start/end carry color tags too, parsed like any other zone.
    assert result.start == Zone(
        name="start", x=0, y=0, color="green", is_start=True
    )
    assert result.end == Zone(
        name="goal", x=2, y=0, color="green", is_end=True
    )


def test_error_reports_physical_line_number() -> None:
    text = (FIXTURES_DIR / "invalid_missing_nb_drones.txt").read_text()

    # The first significant line sits at physical line 6 (four comments plus a
    # blank line precede it); the error must point there, not at line 1.
    with pytest.raises(MapParseError, match=r"line 6"):
        MapParser(text).parse()


def test_parses_zone_type_metadata_in_any_order() -> None:
    text = (FIXTURES_DIR / "valid_zone_types.txt").read_text()

    result = MapParser(text).parse()

    assert result.zones["slow"].zone_type is ZoneType.RESTRICTED
    # zone= after color= proves the tag order does not matter.
    assert result.zones["fast"].zone_type is ZoneType.PRIORITY
    # No zone= tag (only color/max_drones) falls back to the NORMAL default.
    assert result.zones["plain"].zone_type is ZoneType.NORMAL
    # blocked is parsed like any other type (its impassability is domain
    # behaviour, tested in tests/domain, not a parsing concern).
    assert result.zones["wall"].zone_type is ZoneType.BLOCKED
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


def test_parses_zone_color_as_free_string() -> None:
    text = (FIXTURES_DIR / "valid_zone_color.txt").read_text()

    result = MapParser(text).parse()

    # Color is stored on any zone, terminals included, as a free string.
    assert result.start.color == "green"
    assert result.end.color == "red"
    # No color= tag leaves color as None.
    assert result.zones["mid"].color is None


def test_rejects_unknown_metadata_key() -> None:
    text = (FIXTURES_DIR / "invalid_unknown_zone_key.txt").read_text()

    # 'speed' is not a valid tag anywhere; the error names the offending key
    # and its physical line so a typo cannot slip through silently.
    with pytest.raises(MapParseError, match=r"line 6.*speed"):
        MapParser(text).parse()


def test_rejects_metadata_key_in_wrong_context() -> None:
    text = (FIXTURES_DIR / "invalid_misplaced_metadata_key.txt").read_text()

    # max_link_capacity is valid on a connection but not on a zone; the
    # context-aware whitelist rejects it here.
    with pytest.raises(MapParseError, match=r"line 6.*max_link_capacity"):
        MapParser(text).parse()


def test_rejects_duplicate_zone_name() -> None:
    text = (FIXTURES_DIR / "invalid_duplicate_zone_name.txt").read_text()

    # A repeated name would silently overwrite the first zone; the name is
    # the zone's identifier, so the duplicate is an error at its line.
    with pytest.raises(MapParseError, match=r"line 7.*duplicate zone name"):
        MapParser(text).parse()


def test_rejects_multiple_start_hub() -> None:
    text = (FIXTURES_DIR / "invalid_multiple_start_hub.txt").read_text()

    # A map must declare exactly one start hub; the second one is rejected.
    with pytest.raises(MapParseError, match=r"line 6.*start_hub"):
        MapParser(text).parse()


def test_rejects_multiple_end_hub() -> None:
    text = (FIXTURES_DIR / "invalid_multiple_end_hub.txt").read_text()

    # Symmetric to the start hub: exactly one end hub is allowed.
    with pytest.raises(MapParseError, match=r"line 7.*end_hub"):
        MapParser(text).parse()


def test_rejects_connection_to_undefined_zone() -> None:
    text = (FIXTURES_DIR / "invalid_undefined_connection_zone.txt").read_text()

    # 'ghost' is never defined as a zone; the dangling reference is rejected
    # at the connection's physical line.
    with pytest.raises(MapParseError, match=r"line 9.*ghost"):
        MapParser(text).parse()


def test_parses_connection_before_zone_definition() -> None:
    text = (FIXTURES_DIR / "valid_forward_connection.txt").read_text()

    result = MapParser(text).parse()

    # Zones and connections may interleave in any order: the link to 'mid' is
    # declared before 'mid' exists, yet resolves once the whole map is read.
    assert set(result.zones) == {"start", "mid", "goal"}
    assert len(result.connections) == 2


def test_rejects_duplicate_undirected_connection() -> None:
    text = (FIXTURES_DIR / "invalid_duplicate_connection.txt").read_text()

    # A-B and B-A denote the same undirected link; the second declaration is
    # a duplicate, rejected at its physical line.
    with pytest.raises(MapParseError, match=r"line 8.*duplicate connection"):
        MapParser(text).parse()


def test_rejects_self_loop_connection() -> None:
    text = (FIXTURES_DIR / "invalid_self_loop.txt").read_text()

    # A connection from a zone to itself is meaningless for routing and is
    # not defined by the subject, so it is rejected.
    with pytest.raises(MapParseError, match=r"line 9.*self-loop"):
        MapParser(text).parse()


def test_rejects_zero_max_drones() -> None:
    text = (FIXTURES_DIR / "invalid_zero_capacity.txt").read_text()

    # A capacity of 0 means no drone fits; it must be at least 1.
    with pytest.raises(MapParseError, match=r"line 6.*max_drones.*at least 1"):
        MapParser(text).parse()


def test_rejects_zero_link_capacity() -> None:
    text = (FIXTURES_DIR / "invalid_zero_link_capacity.txt").read_text()

    # Link capacity is validated just like zone capacity.
    with pytest.raises(
        MapParseError, match=r"line 8.*max_link_capacity.*at least 1"
    ):
        MapParser(text).parse()


def test_ignores_invalid_max_drones_on_terminal() -> None:
    text = (
        FIXTURES_DIR / "valid_terminal_zero_capacity_ignored.txt"
    ).read_text()

    result = MapParser(text).parse()

    # max_drones is ignored on terminals before the >= 1 check runs, so an
    # invalid 0 there is not an error: the terminal stays unlimited (None).
    assert result.start.max_drones is None


@pytest.mark.parametrize(
    "text, match",
    [
        ("", r"no significant lines"),
        (
            "nb_drones: two\nstart_hub: s 0 0\nend_hub: e 1 0\n"
            "connection: s-e\n",
            r"line 1.*nb_drones"
        ),
        (
            "nb_drones: 1\nstart_hub: s 0\nend_hub: e 1 0\n"
            "connection: s-e\n",
            r"line 2"
        ),
        (
            "nb_drones: 1\nstart_hub: s x 0\nend_hub: e 1 0\n"
            "connection: s-e\n",
            r"line 2"
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nhub: m 2 0 [max_drones=x]\n"
            "end_hub: e 1 0\nconnection: s-m\nconnection: m-e\n",
            r"line 3"
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0 [color=green\nend_hub: e 1 0\n"
            "connection: s-e\n",
            r"line 2.*unclosed"
        ),
        (
            "nb_drones: 1\nstart_hub: s 0 0\nend_hub: e 1 0\n"
            "connection: se\n",
            r"line 4"
        )
    ]
)
def test_rejects_malformed_input(text: str, match: str) -> None:
    # Every malformed line raises a typed MapParseError carrying its physical
    # line, never a bare Python ValueError or IndexError.
    with pytest.raises(MapParseError, match=match):
        MapParser(text).parse()
