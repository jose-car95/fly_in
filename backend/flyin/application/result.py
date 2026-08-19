"""The result of solving a map: output lines plus any warnings."""

from dataclasses import dataclass, field

from flyin.domain.fly_in_map import FlyInMap


@dataclass(frozen=True)
class SolveResult:
    """What the application hands back to an adapter after solving a map.

    It carries data, not formatted output: an adapter decides where each part
    goes (the CLI prints the lines to stdout and the warnings to stderr; an API
    would serialize them). More fields (metrics, map views) join it when a
    consumer needs them.

    Attributes:
        movement_lines: The exact per-turn output lines (``D<ID>-<zone>``).
        fly_in_map: The map that was solved, carried so an adapter can render
            it (zone types, capacities and colors) without parsing it again.
        warnings: Non-fatal messages to surface off stdout; empty when the map
            had nothing worth flagging.
    """

    movement_lines: list[str]
    fly_in_map: FlyInMap
    warnings: list[str] = field(default_factory=list)
