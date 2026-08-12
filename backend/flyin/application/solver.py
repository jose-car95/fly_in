"""The use case that solves a raw map into output lines."""

from flyin.parsing.map_parser import MapParser
from flyin.simulation.simulator import Simulator


class FlyinSolver:
    """Solves a map given as text into the exact per-turn movement lines.

    This is the application's single use case: given the *text* of a map (from
    any source — a file, an HTTP request, a form), it orchestrates the core
    (parse it, then simulate it) and hands back the result. It does no I/O and
    knows no front-end, so a CLI, an API or a test can all drive it the same
    way. Adapters call this; they never reach into the parser or the engine
    themselves.
    """

    def solve_text(self, source_map: str) -> list[str]:
        """Parse and simulate a map given as text.

        Args:
            source_map: The raw contents of a map file.

        Returns:
            The exact per-turn movement lines (``D<ID>-<zone>``).

        Raises:
            MapParseError: If the map text is malformed.
            UnsolvableMapError: If the start cannot reach the end.
        """
        fly_in_map = MapParser(source_map).parse()
        return Simulator(fly_in_map).run()
