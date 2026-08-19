"""Colored terminal view of a solved map, for human eyes only.

The subject requires visual feedback of the simulation; this renders it as
ANSI-colored terminal output. It is a second rendering of the very same
result, never a replacement: the exact movement lines the evaluator reads
stay untouched and this view is only produced behind an explicit flag.
"""

from typing import Iterator

from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone

RESET = "\033[0m"
RAINBOW = "rainbow"
# The eight basic ANSI codes plus 256-color ones (``38;5;N``) for the shades
# the official maps declare. "black" maps to bright black: true black is
# unreadable on the dark terminals these are viewed on.
COLOR_CODES = {
    "black": "90",
    "gray": "90",
    "grey": "90",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "purple": "35",
    "cyan": "36",
    "white": "37",
    "orange": "38;5;208",
    "gold": "38;5;220",
    "brown": "38;5;94",
    "maroon": "38;5;88",
    "crimson": "38;5;161",
    "darkred": "38;5;52",
    "lime": "38;5;118",
    "violet": "38;5;177"
}
RAINBOW_CODES = ("31", "33", "32", "36", "34", "35")


class AnsiPalette:
    """Turns a color name from a map into ANSI terminal escape codes."""

    def paint(self, text: str, color: str | None) -> str:
        """Wrap text in the escape codes of one color.

        The subject accepts any single word as a color and fixes no list of
        allowed values, so an unrecognized name is not an error: the text is
        returned plain and the declared value is still reported in the view.

        Args:
            text: The text to colorize.
            color: Color name declared in the map, or ``None`` when absent.

        Returns:
            The text wrapped in escape codes, or unchanged when the color is
            missing or unknown.
        """
        name = (color or "").lower()
        if name == RAINBOW:
            return self._paint_rainbow(text)
        code = COLOR_CODES.get(name)
        if code is None:
            return text
        return f"\033[{code}m{text}{RESET}"

    @staticmethod
    def _paint_rainbow(text: str) -> str:
        """Paint each character in the next hue of the cycle.

        One official map declares ``color=rainbow``, which names no single
        hue, so it is honoured by cycling the colors letter by letter.

        Args:
            text: The text to colorize.

        Returns:
            The text with every character wrapped in its own color.
        """
        return "".join(
            f"\033[{RAINBOW_CODES[index % len(RAINBOW_CODES)]}m"
            f"{letter}{RESET}"
            for index, letter in enumerate(text)
        )


class VisualRenderer:
    """Renders a solved map as colored terminal lines.

    Attributes:
        _fly_in_map: The solved map, read for zone states and colors.
        _palette: Translates the declared colors into escape codes.
    """

    def __init__(self, fly_in_map: FlyInMap) -> None:
        """Store the map to describe.

        Args:
            fly_in_map: The map that was solved, as parsed.
        """
        self._fly_in_map = fly_in_map
        self._palette = AnsiPalette()

    def render(self, movement_lines: list[str]) -> list[str]:
        """Return the whole human view: zone states, then the turns.

        Args:
            movement_lines: The exact per-turn lines the engine produced.

        Returns:
            The lines of the colored view, ready to print.
        """
        lines = [
            "Fly-In simulation",
            f"Drones: {self._fly_in_map.nb_drones}",
            "",
            "Zones:"
        ]
        lines.extend(self._zone_lines())
        lines.extend(["", "Turns:"])
        lines.extend(
            f"  Turn {number}: {self._paint_movements(line)}"
            for number, line in enumerate(movement_lines, start=1)
        )
        return lines

    def _zone_lines(self) -> list[str]:
        """Return one line per zone, in columns that line up.

        Every column is padded to its widest value so the states can be read
        down the screen instead of hunting for them along each line.
        """
        zones = list(self._fly_in_map.zones.values())
        return [
            self._zone_line(
                zone,
                name_width=self._widest(len(zone.name) for zone in zones),
                type_width=self._widest(
                    len(zone.zone_type.value) for zone in zones
                ),
                capacity_width=self._widest(
                    len(self._capacity(zone)) for zone in zones
                ),
                position_width=self._widest(
                    len(f"xy=({zone.x},{zone.y})") for zone in zones
                )
            )
            for zone in zones
        ]

    @staticmethod
    def _widest(lengths: Iterator[int]) -> int:
        """Return the widest of some lengths, or 0 when there are none."""
        return max(lengths, default=0)

    def _zone_line(
        self,
        zone: Zone,
        name_width: int,
        type_width: int,
        capacity_width: int,
        position_width: int
    ) -> str:
        """Return the state line of one zone.

        The name is padded before being painted: escape codes have no width
        on screen but do count as characters, so padding afterwards would
        break the alignment of every colored column.

        Args:
            zone: The zone to describe.
            name_width: Width of the longest zone name.
            type_width: Width of the longest zone type.
            capacity_width: Width of the longest capacity value.
            position_width: Width of the longest coordinate pair.

        Returns:
            A line with the zone's marker, name, type, capacity and color.
        """
        painted = self._palette.paint(zone.name.ljust(name_width), zone.color)
        position = f"xy=({zone.x},{zone.y})"
        kind = f"type={zone.zone_type.value}".ljust(type_width + 5)
        capacity = (
            f"capacity={self._capacity(zone)}".ljust(capacity_width + 9)
        )
        return (
            f"  {self._palette.paint('■', zone.color)} {painted}"
            f"  {kind}  {capacity}  {position.ljust(position_width)}"
            f"  color={zone.color or 'none'}"
        )

    @staticmethod
    def _capacity(zone: Zone) -> str:
        """Return the effective capacity of a zone, as shown to a human.

        Args:
            zone: The zone to report on.

        Returns:
            ``unlimited`` for the terminals, whose ``max_drones`` the subject
            says to ignore, else the declared capacity or the default of 1.
        """
        if zone.is_start or zone.is_end:
            return "unlimited"
        return str(zone.max_drones or 1)

    def _paint_movements(self, line: str) -> str:
        """Color the zone names inside one turn line.

        Args:
            line: One movement line, tokens separated by spaces.

        Returns:
            The same line with every zone name painted in its color.
        """
        return " ".join(
            self._paint_token(token) for token in line.split()
        )

    def _paint_token(self, token: str) -> str:
        """Color the zone names of a single ``D<ID>-...`` token.

        Zone names cannot contain dashes (the subject forbids them so the
        connection syntax stays unambiguous), so splitting on dashes is safe:
        the first field is always the drone, and what follows is either one
        zone or the two ends of a connection in flight.

        Args:
            token: One movement token, such as ``D1-goal``.

        Returns:
            The token with its zone names painted.
        """
        drone, *zone_names = token.split("-")
        return "-".join(
            [drone] + [self._paint_zone(name) for name in zone_names]
        )

    def _paint_zone(self, name: str) -> str:
        """Return a zone name painted in its own declared color."""
        zone = self._fly_in_map.zones.get(name)
        return self._palette.paint(name, zone.color if zone else None)
