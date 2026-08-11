"""A route through the map with its total cost."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Path:
    """An ordered route of zones and the total turns to traverse it.

    Attributes:
        zones: Zone names from start to end, in visiting order.
        cost: Total movement cost (turns) of entering each zone after start.
    """

    zones: tuple[str, ...]
    cost: int
