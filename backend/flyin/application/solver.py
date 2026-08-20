"""The use case that solves a raw map into a result."""

from flyin.application.result import SolveResult
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import ZoneType
from flyin.parsing.map_parser import MapParser
from flyin.simulation.simulator import Simulator


class FlyinSolver:
    """Solves a map given as text into a :class:`SolveResult`.

    This is the application's single use case: given the *text* of a map (from
    any source — a file, an HTTP request, a form), it orchestrates the core
    (parse it, normalize it, then simulate it) and hands back the result. It
    does no I/O and knows no front-end, so a CLI, an API or a test can all
    drive it the same way. Adapters call this; they never reach into the parser
    or the engine themselves.
    """

    def solve_text(self, source_map: str) -> SolveResult:
        """Parse, normalize and simulate a map given as text.

        Args:
            source_map: The raw contents of a map file.

        Returns:
            The movement lines and any non-fatal warnings.

        Raises:
            MapParseError: If the map text is malformed.
            UnsolvableMapError: If the start cannot reach the end.
        """
        fly_in_map = MapParser(source_map).parse()
        warnings = self._normalize_terminals(fly_in_map)
        movement_lines = Simulator(fly_in_map).run()
        return SolveResult(
            movement_lines=movement_lines,
            fly_in_map=fly_in_map,
            warnings=warnings
        )

    def load_text(self, source_map: str) -> FlyInMap:
        """Parse and normalize a map given as text, without simulating.

        For read-only consumers (the API map detail) that need the map's
        structure but not a run.

        Args:
            source_map: The raw contents of a map file.

        Returns:
            The parsed map, with any restricted terminal normalized.

        Raises:
            MapParseError: If the map text is malformed.
        """
        fly_in_map = MapParser(source_map).parse()
        self._normalize_terminals(fly_in_map)
        return fly_in_map

    @staticmethod
    def _normalize_terminals(fly_in_map: FlyInMap) -> list[str]:
        """Coerce a restricted terminal to normal and warn about it.

        A start/end hub is the special entry/exit point, so ``restricted`` (a
        capacity/transit type) makes no sense there. Rather than reject the
        map, it is treated as normal and the user is warned.

        Args:
            fly_in_map: The parsed map, mutated in place when a terminal is
                coerced.

        Returns:
            One warning message per coerced terminal (empty when none).
        """
        warnings: list[str] = []
        for zone in (fly_in_map.start, fly_in_map.end):
            if zone.zone_type is ZoneType.RESTRICTED:
                zone.zone_type = ZoneType.NORMAL
                warnings.append(
                    f"warning: terminal zone {zone.name!r} cannot be "
                    f"restricted; treated as normal"
                )
        return warnings
