"""Parse Fly-In map files into domain objects.

This module turns the raw text of a map file into a :class:`FlyInMap`. It
only covers the minimal happy path for now (``nb_drones`` plus one
``start_hub``, one ``end_hub`` and their connections); intermediate
``hub:`` lines, metadata, capacities and duplicate/self-loop validation
arrive in later slices, each with its own failing test first.
"""

from enum import Enum

from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone, ZoneType


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
    HUB = "hub:"
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
            text: Raw contents of a map file, with comments and blank lines
                included.
        """
        self._text = text

    def parse(self) -> FlyInMap:
        """Parse the stored text into a :class:`FlyInMap`.

        Returns:
            The parsed map, with its zones indexed by name and its start/end
            hubs exposed directly.

        Raises:
            ValueError: If the first significant line is not ``nb_drones:``,
                or if the map does not declare exactly one start hub and one
                end hub.
        """
        lines = self._significant_lines()

        nb_drones = self._parse_nb_drones(lines[0])
        zones: dict[str, Zone] = {}
        connections: list[Connection] = []
        start: Zone | None = None
        end: Zone | None = None

        for _, line in lines[1:]:
            if line.startswith(LinePrefix.START_HUB):
                start = self._parse_zone(
                    line, LinePrefix.START_HUB, is_start=True
                )
                zones[start.name] = start
            elif line.startswith(LinePrefix.END_HUB):
                end = self._parse_zone(line, LinePrefix.END_HUB, is_end=True)
                zones[end.name] = end
            elif line.startswith(LinePrefix.HUB):
                hub = self._parse_zone(line, LinePrefix.HUB)
                zones[hub.name] = hub
            elif line.startswith(LinePrefix.CONNECTION):
                connections.append(self._parse_connection(line))

        if start is None or end is None:
            raise ValueError(
                "map must declare exactly one start_hub and one end_hub"
            )

        return FlyInMap(
            nb_drones=nb_drones,
            zones=zones,
            connections=connections,
            start=start,
            end=end
        )

    def _significant_lines(self) -> list[tuple[int, str]]:
        """Return the meaningful lines paired with their physical line number.

        Blank lines and full-line comments (starting with ``#``) are dropped,
        so the first entry is always ``nb_drones:`` in a well-formed map. Each
        kept line carries its 1-based position in the original file (counting
        the dropped comments and blanks), so parse errors can point at the
        physical line the user sees in their editor.

        Returns:
            ``(physical_line_number, text)`` pairs for the non-empty,
            non-comment lines, each stripped of surrounding whitespace and
            kept in their original order.
        """
        return [
            (lineno, stripped)
            for lineno, raw in enumerate(self._text.splitlines(), start=1)
            if (stripped := raw.strip()) and not stripped.startswith("#")
        ]

    def _parse_nb_drones(self, numbered_line: tuple[int, str]) -> int:
        """Parse the ``nb_drones:`` line into the number of drones.

        Args:
            numbered_line: The first significant line as a
                ``(physical_line_number, text)`` pair.

        Returns:
            The declared number of drones.

        Raises:
            ValueError: If the line does not start with ``nb_drones:``.
        """
        lineno, line = numbered_line
        if not line.startswith(LinePrefix.NB_DRONES):
            raise ValueError(
                f"line {lineno}: expected 'nb_drones:' as the first "
                f"significant line, got: {line!r}"
            )
        return int(line.removeprefix(LinePrefix.NB_DRONES).strip())

    def _parse_zone(
        self,
        line: str,
        prefix: LinePrefix,
        *,
        is_start: bool = False,
        is_end: bool = False
    ) -> Zone:
        """Parse a hub line (``<prefix> <name> <x> <y>``) into a :class:`Zone`.

        Reads the name, the two integer coordinates, the ``zone=`` tag (default
        ``normal``), the ``max_drones=`` tag and the ``color=`` tag.
        ``max_drones`` is ignored on start/end hubs, which have unlimited
        capacity, and stays ``None`` when absent (meaning the default of 1).
        ``color`` is a free string kept for the M6 colored view, ``None`` when
        absent.

        Args:
            line: The full hub line to parse.
            prefix: The prefix tag to strip before reading the fields.
            is_start: Whether the zone is the map's start hub.
            is_end: Whether the zone is the map's end hub.

        Returns:
            The zone described by the line.
        """
        name, x_str, y_str, *_ = line.removeprefix(prefix).split()
        metadata = self._parse_metadata(line)
        zone_type = ZoneType(metadata.get("zone", "normal"))
        is_terminal = is_start or is_end
        max_drones = (
            None
            if is_terminal
            else self._optional_int(metadata, "max_drones")
        )
        return Zone(
            name=name,
            x=int(x_str),
            y=int(y_str),
            zone_type=zone_type,
            max_drones=max_drones,
            color=metadata.get("color"),
            is_start=is_start,
            is_end=is_end
        )

    def _parse_metadata(self, line: str) -> dict[str, str]:
        """Parse the ``[key=value ...]`` block of a line into a mapping.

        Tags may appear in any order, so they are keyed by name rather than by
        position; a line with no bracket block yields an empty mapping. Only
        the raw string values are returned — turning them into zone types,
        capacities, etc. is each caller's job.

        Args:
            line: The full map line, brackets included.

        Returns:
            A ``{key: value}`` mapping for the tags inside the brackets, empty
            when the line carries no ``[...]`` block.
        """
        open_bracket = line.find("[")
        if open_bracket == -1:
            return {}
        close_bracket = line.find("]", open_bracket)
        body = line[open_bracket + 1:close_bracket]
        metadata: dict[str, str] = {}
        for token in body.split():
            key, value = token.split("=", maxsplit=1)
            metadata[key] = value
        return metadata

    def _optional_int(self, metadata: dict[str, str], key: str) -> int | None:
        """Read an optional integer tag from parsed metadata.

        Args:
            metadata: The parsed ``{key: value}`` tag mapping.
            key: The tag name to read.

        Returns:
            The tag's integer value, or ``None`` when the tag is absent (which
            downstream code treats as the default of 1).
        """
        value = metadata.get(key)
        return int(value) if value is not None else None

    def _parse_connection(self, line: str) -> Connection:
        """Parse a ``connection:`` line into a link.

        The line is ``<zone_a>-<zone_b>`` optionally followed by a
        ``[max_link_capacity=...]`` block. The endpoints are read from the text
        before the brackets, so metadata never leaks into a zone name, and the
        capacity defaults to ``None`` (meaning 1) when the tag is absent.

        Args:
            line: The full connection line to parse.

        Returns:
            The connection between the two named zones.
        """
        metadata = self._parse_metadata(line)
        endpoints = line.removeprefix(LinePrefix.CONNECTION)
        endpoints = endpoints.split("[", maxsplit=1)[0].strip()
        zone_a, zone_b = endpoints.split("-", maxsplit=1)
        return Connection(
            zone_a=zone_a,
            zone_b=zone_b,
            max_link_capacity=self._optional_int(
                metadata, "max_link_capacity"
            )
        )
