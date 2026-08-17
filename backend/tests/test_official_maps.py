"""The engine's output on every official map passes the independent judge.

This is M4's validity bar proven end to end: for each official map the engine
produces a schedule and the independent ``ScheduleValidator`` accepts it. No
official map has a restricted terminal, so the solver's terminal normalization
is a no-op here and simulating the parsed map directly matches the CLI.
"""

from pathlib import Path

import pytest

from flyin.parsing.map_parser import MapParser
from flyin.simulation.schedule_validator import ScheduleValidator
from flyin.simulation.simulator import Simulator

_MAPS_DIR = Path(__file__).resolve().parents[2] / "maps"
_MAP_FILES = sorted(_MAPS_DIR.glob("**/*.txt"))


def test_official_maps_are_present() -> None:
    # Guard against a wrong path silently collecting zero parametrized cases.
    assert _MAP_FILES, f"no official maps found under {_MAPS_DIR}"


@pytest.mark.parametrize("map_file", _MAP_FILES, ids=lambda p: p.stem)
def test_engine_output_validates_on_official_map(map_file: Path) -> None:
    fly_in_map = MapParser(map_file.read_text()).parse()
    lines = Simulator(fly_in_map).run()
    # The independent judge must accept the engine's own output: M4's validity
    # bar, proven on the real maps rather than merely asserted.
    ScheduleValidator(fly_in_map, lines).validate()
