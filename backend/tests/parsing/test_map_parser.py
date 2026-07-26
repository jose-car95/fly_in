from pathlib import Path

from flyin.domain.zone import Zone
from flyin.parsing.map_parser import parse_map

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "edge-cases"


def test_parses_minimal_map() -> None:
    text = (FIXTURES_DIR / "valid_minimal.txt").read_text()

    result = parse_map(text)

    assert result.nb_drones == 1
    assert result.start == Zone(name="start", x=0, y=0, is_start=True)
    assert result.end == Zone(name="goal", x=1, y=0, is_end=True)
    assert result.zones == {"start": result.start, "goal": result.end}
    assert len(result.connections) == 1
    assert result.connections[0].zone_a == "start"
    assert result.connections[0].zone_b == "goal"
