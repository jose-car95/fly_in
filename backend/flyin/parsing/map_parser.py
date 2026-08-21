"""Parse Fly-In map files into domain objects.

Turns the raw text of a map file into a :class:`FlyInMap`: the drone count,
the ``start_hub``/``hub``/``end_hub`` zones with their optional metadata and
capacities, and the connections between them. A malformed map is rejected
with a clear error carrying its physical, 1-based line number.
"""

from enum import Enum

from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone, ZoneType
from flyin.shared.exceptions import MapParseError


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


class MetadataKeys(Enum):
    """Metadata tags accepted per line kind.

    Each member's value is the set of keys valid on that kind of line, so a
    tag placed in the wrong context (e.g. ``max_link_capacity`` on a zone) is
    rejected just like an invented key. Grouping them under one typed Enum
    keeps the whitelist in a single named place; the ``frozenset`` values are
    immutable constants, not mutable module state.
    """

    ZONE = frozenset({"zone", "max_drones", "color"})
    CONNECTION = frozenset({"max_link_capacity"})


class MapParser:
    """Parses the text of a single map file into a :class:`FlyInMap`.

    One instance represents one parsing session: the map text is handed in at
    construction and consumed by :meth:`parse`. Keeping the input as instance
    state (``self._text``) is what makes this object-oriented rather than a
    bag of loose functions.
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

        A single guard around each map line turns any raw ``ValueError`` from
        a malformed line (``int()``, tuple unpacking) into a ``MapParseError``
        carrying that line number; the parser's own ``MapParseError`` is not a
        ``ValueError``, so it passes through untouched.

        Returns:
            The parsed map, with its zones indexed by name and its start/end
            hubs exposed directly.

        Raises:
            MapParseError: If the map is malformed in any way: it is empty,
                the first significant line is not ``nb_drones:``, a line has
                the wrong shape or a non-integer field, a start or end hub is
                missing or declared more than once, a zone name is duplicated,
                or a connection is a self-loop, names an undefined zone, or
                repeats an undirected pair.
        """
        lines = self._significant_lines()
        if not lines:
            raise MapParseError(
                "map has no significant lines (empty or comments only)"
            )

        nb_drones = self._parse_nb_drones(lines[0])
        zones: dict[str, Zone] = {}
        pending: list[tuple[int, Connection]] = []
        start: Zone | None = None
        end: Zone | None = None

        for lineno, line in lines[1:]:
            try:
                if line.startswith(LinePrefix.START_HUB):
                    if start is not None:
                        raise MapParseError(
                            f"line {lineno}: multiple start_hub declared"
                        )
                    start = self._parse_zone(
                        line, LinePrefix.START_HUB, lineno, is_start=True
                    )
                    self._add_zone(zones, start, lineno)
                elif line.startswith(LinePrefix.END_HUB):
                    if end is not None:
                        raise MapParseError(
                            f"line {lineno}: multiple end_hub declared"
                        )
                    end = self._parse_zone(
                        line, LinePrefix.END_HUB, lineno, is_end=True
                    )
                    self._add_zone(zones, end, lineno)
                elif line.startswith(LinePrefix.HUB):
                    hub = self._parse_zone(line, LinePrefix.HUB, lineno)
                    self._add_zone(zones, hub, lineno)
                elif line.startswith(LinePrefix.CONNECTION):
                    connection = self._parse_connection(line, lineno)
                    pending.append((lineno, connection))
            except ValueError as exc:
                raise MapParseError(f"line {lineno}: {exc}") from exc

        if start is None or end is None:
            raise MapParseError(
                "map must declare exactly one start_hub and one end_hub"
            )

        connections = self._resolve_connections(pending, zones)

        return FlyInMap(
            nb_drones=nb_drones,
            zones=zones,
            connections=connections,
            start=start,
            end=end
        )

    def _add_zone(
        self, zones: dict[str, Zone], zone: Zone, lineno: int
    ) -> None:
        """Insert a zone, rejecting a name already used by another zone.

        The name is the zone's unique identifier, so a repeat would silently
        overwrite an earlier zone; instead it is a parse error.

        Args:
            zones: The name-to-zone map being built, mutated in place.
            zone: The zone to insert.
            lineno: Physical 1-based line number, used for error messages.

        Raises:
            MapParseError: If ``zone.name`` is already present.
        """
        if zone.name in zones:
            raise MapParseError(
                f"line {lineno}: duplicate zone name {zone.name!r}"
            )
        zones[zone.name] = zone

    def _resolve_connections(
        self,
        pending: list[tuple[int, Connection]],
        zones: dict[str, Zone]
    ) -> list[Connection]:
        """Validate every connection and return them in order.

        Connections are checked after the whole map is read, so a link may
        name a zone defined later in the file; the subject fixes no order
        between zone and connection lines. Each link must not be a self-loop,
        must name two defined zones, and must be unique as an *undirected*
        pair (``a-b`` and ``b-a`` are the same link, so declaring both is a
        duplicate).

        Args:
            pending: ``(physical_line_number, connection)`` pairs collected
                while scanning the map.
            zones: All zones of the map, indexed by name.

        Returns:
            The connections, in their original order.

        Raises:
            MapParseError: If a connection is a self-loop, names an undefined
                zone, or repeats an undirected pair already seen.
        """
        seen: set[frozenset[str]] = set()
        for lineno, connection in pending:
            if connection.zone_a == connection.zone_b:
                raise MapParseError(
                    f"line {lineno}: self-loop on zone {connection.zone_a!r}"
                )
            for endpoint in (connection.zone_a, connection.zone_b):
                if endpoint not in zones:
                    raise MapParseError(
                        f"line {lineno}: connection references undefined "
                        f"zone {endpoint!r}"
                    )
            link = frozenset((connection.zone_a, connection.zone_b))
            if link in seen:
                raise MapParseError(
                    f"line {lineno}: duplicate connection between "
                    f"{connection.zone_a!r} and {connection.zone_b!r}"
                )
            seen.add(link)
        return [connection for _, connection in pending]

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
            MapParseError: If the line does not start with ``nb_drones:`` or
                its value is not an integer.
        """
        lineno, line = numbered_line
        if not line.startswith(LinePrefix.NB_DRONES):
            raise MapParseError(
                f"line {lineno}: expected 'nb_drones:' as the first "
                f"significant line, got: {line!r}"
            )
        value = line.removeprefix(LinePrefix.NB_DRONES).strip()
        try:
            return int(value)
        except ValueError as exc:
            raise MapParseError(
                f"line {lineno}: nb_drones must be an integer, got {value!r}"
            ) from exc

    def _parse_zone(
        self,
        line: str,
        prefix: LinePrefix,
        lineno: int,
        *,
        is_start: bool = False,
        is_end: bool = False
    ) -> Zone:
        """Parse a hub line (``<prefix> <name> <x> <y>``) into a :class:`Zone`.

        Reads the name, the two integer coordinates, the ``zone=`` tag (default
        ``normal``), the ``max_drones=`` tag and the ``color=`` tag.
        ``max_drones`` is ignored on start/end hubs, which have unlimited
        capacity, and stays ``None`` when absent (meaning the default of 1).
        ``color`` is a free string kept for the colored view, ``None`` when
        absent.

        Args:
            line: The full hub line to parse.
            prefix: The prefix tag to strip before reading the fields.
            lineno: Physical 1-based line number, used for error messages.
            is_start: Whether the zone is the map's start hub.
            is_end: Whether the zone is the map's end hub.

        Returns:
            The zone described by the line.

        Raises:
            MapParseError: If the line carries a metadata tag that is not
                valid on a zone, or a ``max_drones`` capacity below 1.
        """
        name, x_str, y_str, *_ = line.removeprefix(prefix).split()
        metadata = self._parse_metadata(line, lineno, MetadataKeys.ZONE)
        zone_type = ZoneType(metadata.get("zone", "normal"))
        is_terminal = is_start or is_end
        max_drones = (
            None
            if is_terminal
            else self._optional_capacity(metadata, "max_drones", lineno)
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

    def _parse_metadata(
        self, line: str, lineno: int, allowed: MetadataKeys
    ) -> dict[str, str]:
        """Parse the ``[key=value ...]`` block of a line into a mapping.

        Tags may appear in any order, so they are keyed by name rather than by
        position; a line with no bracket block yields an empty mapping. Only
        the raw string values are returned — turning them into zone types,
        capacities, etc. is each caller's job. A key outside ``allowed`` is
        rejected so a typo or a tag in the wrong context cannot be silently
        ignored.

        Args:
            line: The full map line, brackets included.
            lineno: Physical 1-based line number, used for error messages.
            allowed: The whitelist of metadata keys valid for this line's kind.

        Returns:
            A ``{key: value}`` mapping for the tags inside the brackets, empty
            when the line carries no ``[...]`` block.

        Raises:
            MapParseError: If the ``[`` block is not closed or a tag key is
                not in ``allowed``.
        """
        open_bracket = line.find("[")
        if open_bracket == -1:
            return {}
        close_bracket = line.find("]", open_bracket)
        if close_bracket == -1:
            raise MapParseError(f"line {lineno}: unclosed '[' in metadata")
        body = line[open_bracket + 1:close_bracket]
        metadata: dict[str, str] = {}
        for token in body.split():
            key, value = token.split("=", maxsplit=1)
            if key not in allowed.value:
                raise MapParseError(
                    f"line {lineno}: unknown metadata key {key!r}"
                )
            metadata[key] = value
        return metadata

    def _optional_capacity(
        self, metadata: dict[str, str], key: str, lineno: int
    ) -> int | None:
        """Read an optional capacity tag, requiring it to be positive.

        A capacity of 0 or less means nothing fits through the zone or link,
        which is meaningless, so it is rejected. An absent tag yields ``None``,
        which downstream code treats as the default of 1.

        Args:
            metadata: The parsed ``{key: value}`` tag mapping.
            key: The capacity tag name to read.
            lineno: Physical 1-based line number, used for error messages.

        Returns:
            The tag's integer value, or ``None`` when the tag is absent.

        Raises:
            MapParseError: If the tag is present but not at least 1.
        """
        value = metadata.get(key)
        if value is None:
            return None
        capacity = int(value)
        if capacity < 1:
            raise MapParseError(
                f"line {lineno}: {key} must be at least 1, got {capacity}"
            )
        return capacity

    def _parse_connection(self, line: str, lineno: int) -> Connection:
        """Parse a ``connection:`` line into a link.

        The line is ``<zone_a>-<zone_b>`` optionally followed by a
        ``[max_link_capacity=...]`` block. The endpoints are read from the text
        before the brackets, so metadata never leaks into a zone name, and the
        capacity defaults to ``None`` (meaning 1) when the tag is absent.

        Args:
            line: The full connection line to parse.
            lineno: Physical 1-based line number, used for error messages.

        Returns:
            The connection between the two named zones.

        Raises:
            MapParseError: If the line carries a metadata tag that is not
                valid on a connection, or a ``max_link_capacity`` below 1.
        """
        metadata = self._parse_metadata(
            line, lineno, MetadataKeys.CONNECTION
        )
        endpoints = line.removeprefix(LinePrefix.CONNECTION)
        endpoints = endpoints.split("[", maxsplit=1)[0].strip()
        zone_a, zone_b = endpoints.split("-", maxsplit=1)
        return Connection(
            zone_a=zone_a,
            zone_b=zone_b,
            max_link_capacity=self._optional_capacity(
                metadata, "max_link_capacity", lineno
            )
        )
