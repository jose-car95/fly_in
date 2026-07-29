from pathlib import Path

import pytest

from flyin.domain.zone import Zone
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


def test_parses_regular_hub_ignoring_metadata() -> None:
    text = (FIXTURES_DIR / "valid_with_hub.txt").read_text()

    result = MapParser(text).parse()

    # A regular `hub:` becomes a NORMAL, non-terminal zone (Zone defaults),
    # and the trailing `[...]` metadata is ignored until M1.4.
    assert result.zones["junction"] == Zone(name="junction", x=1, y=0)
    # start/end lines also carry metadata brackets that must not break parsing.
    assert result.start == Zone(name="start", x=0, y=0, is_start=True)
    assert result.end == Zone(name="goal", x=2, y=0, is_end=True)


def test_error_reports_physical_line_number() -> None:
    text = (FIXTURES_DIR / "invalid_missing_nb_drones.txt").read_text()

    # The first significant line sits at physical line 6 (four comments plus a
    # blank line precede it); the error must point there, not at line 1.
    with pytest.raises(ValueError, match=r"line 6"):
        MapParser(text).parse()
