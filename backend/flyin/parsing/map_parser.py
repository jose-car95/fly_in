"""Parse Fly-In map files into domain objects.

This module turns the raw text of a map file into a :class:`FlyInMap`. It only
covers the minimal happy path for now (``nb_drones`` plus one ``start_hub``, one
``end_hub`` and their connections); intermediate ``hub:`` lines, metadata,
capacities and duplicate/self-loop validation arrive in later slices, each with
its own failing test first.
"""

from enum import Enum

from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone


class LinePrefix(str, Enum):
    """Textual tags that mark the meaning of a significant map line.

    The members subclass :class:`str`, so each one can be used directly with
    string operations such as ``startswith`` and ``removeprefix`` while still
    being grouped under a single, typed name. These are immutable constants
    (data, not behaviour), so they live at module level rather than inside the
    parser class, and they do not violate the no-global-variables rule.
    """

    NB_DRONES = "nb_drones:"
    START_HUB = "start_hub:"
    END_HUB = "end_hub:"
    CONNECTION = "connection:"


class MapParser:
    """Parses the text of a single map file into a :class:`FlyInMap`.

    One instance represents one parsing session: the map text is handed in at
    construction and consumed by :meth:`parse`. Keeping the input as instance
    state (``self._text``) is what makes this object-oriented rather than a bag
    of loose functions, and it prepares the ground for later slices where the
    current line number and accumulated errors also become instance state
    (physical 1-based line numbers in parse errors).
    """

    def __init__(self, text: str) -> None:
        """Store the raw map text to be parsed.

        Args:
            text: Raw contents of a map file, comments and blank lines included.
        """
        self._text = text

    def parse(self) -> FlyInMap:
        """Parse the stored text into a :class:`FlyInMap`.

        Returns:
            The parsed map, with its zones indexed by name and its start/end
            hubs exposed directly.

        Raises:
            ValueError: If the first significant line is not ``nb_drones:``, or
                if the map does not declare exactly one start hub and one end hub.
        """
        lines = self._significant_lines()

        nb_drones = self._parse_nb_drones(lines[0])
        zones: dict[str, Zone] = {}
        connections: list[Connection] = []
        start: Zone | None = None
        end: Zone | None = None

        for line in lines[1:]:
            if line.startswith(LinePrefix.START_HUB):
                start = self._parse_zone(line, LinePrefix.START_HUB, is_start=True)
                zones[start.name] = start
            elif line.startswith(LinePrefix.END_HUB):
                end = self._parse_zone(line, LinePrefix.END_HUB, is_end=True)
                zones[end.name] = end
            elif line.startswith(LinePrefix.CONNECTION):
                connections.append(self._parse_connection(line))

        if start is None or end is None:
            raise ValueError("map must declare exactly one start_hub and one end_hub")

        return FlyInMap(
            nb_drones=nb_drones,
            zones=zones,
            connections=connections,
            start=start,
            end=end,
        )

    def _significant_lines(self) -> list[str]:
        """Return the meaningful lines of the map, stripped of noise.

        Blank lines and full-line comments (starting with ``#``) are dropped, so
        the first entry is always ``nb_drones:`` in a well-formed map.

        Returns:
            The non-empty, non-comment lines, each stripped of surrounding
            whitespace and kept in their original order.
        """
        stripped = (line.strip() for line in self._text.splitlines())
        return [line for line in stripped if line and not line.startswith("#")]

    def _parse_nb_drones(self, line: str) -> int:
        """Parse the ``nb_drones:`` line into the number of drones.

        Args:
            line: The first significant line of the map.

        Returns:
            The declared number of drones.

        Raises:
            ValueError: If the line does not start with ``nb_drones:``.
        """
        if not line.startswith(LinePrefix.NB_DRONES):
            raise ValueError(f"expected 'nb_drones:' as the first significant line, got: {line!r}")
        return int(line.removeprefix(LinePrefix.NB_DRONES).strip())

    def _parse_zone(
        self, line: str, prefix: LinePrefix, *, is_start: bool = False, is_end: bool = False
    ) -> Zone:
        """Parse a hub line (``<prefix> <name> <x> <y>``) into a :class:`Zone`.

        Args:
            line: The full hub line to parse.
            prefix: The prefix tag to strip before reading the fields.
            is_start: Whether the zone is the map's start hub.
            is_end: Whether the zone is the map's end hub.

        Returns:
            The zone described by the line.
        """
        name, x_str, y_str = line.removeprefix(prefix).split()
        return Zone(name=name, x=int(x_str), y=int(y_str), is_start=is_start, is_end=is_end)

    def _parse_connection(self, line: str) -> Connection:
        """Parse a ``connection:`` line (``<zone_a>-<zone_b>``) into a link.

        Args:
            line: The full connection line to parse.

        Returns:
            The connection between the two named zones.
        """
        zone_a, zone_b = line.removeprefix(LinePrefix.CONNECTION).strip().split("-", maxsplit=1)
        return Connection(zone_a=zone_a, zone_b=zone_b)
