"""CLI adapter: map file -> application layer -> stdout."""

from pathlib import Path
from typing import TextIO

from flyin.adapters.cli.arguments import CliArguments
from flyin.adapters.cli.visual import VisualRenderer
from flyin.adapters.map_catalog import MapCatalog
from flyin.application.solver import FlyinSolver
from flyin.shared.exceptions import MapParseError, UnsolvableMapError


class Cli:
    """CLI adapter: turns a map file into a solved, printed simulation.

    A thin front-end over the application use case: it reads the named file,
    hands its text to :class:`FlyinSolver`, and writes the movement lines to
    stdout, keeping errors on stderr. It never parses or simulates itself — it
    only knows the map gets solved, not how. Streams are injected so the whole
    flow is testable without a subprocess.

    Attributes:
        _out: Stream for the movement lines (stdout).
        _err: Stream for error messages, kept off stdout (stderr).
        _in: Stream a human types the map selection into (stdin).
        _catalog: The maps offered when no map file was named.
    """

    def __init__(
        self,
        out: TextIO,
        err: TextIO,
        in_: TextIO,
        catalog: MapCatalog
    ) -> None:
        """Store the streams and the catalog to work with.

        Args:
            out: Where the exact per-turn movement lines are written.
            err: Where clear error messages are written, off stdout.
            in_: Where the map selection is read from when none was given.
            catalog: Maps offered for selection; injected so a caller (or a
                test) decides which folder is on offer.
        """
        self._out = out
        self._err = err
        self._in = in_
        self._catalog = catalog

    def run(self, argv: list[str]) -> int:
        """Run the CLI over its arguments and return a process exit code.

        Naming no map file is not an error: the human is offered the catalog
        instead. That case is told apart by ``None`` rather than truthiness,
        since an empty path is a read error to report, not a reason to open
        the catalog. The colored view replaces the exact movement lines rather
        than joining them, because mixing both would break the output format
        the subject fixes.

        Args:
            argv: Command-line arguments without the program name; at most one
                map file path and an optional ``--visual`` flag are expected.
                Naming no map file offers the catalog.

        Returns:
            0 on success, 2 on a usage or selection error, 1 on a read, parse
            or route failure.
        """
        arguments = CliArguments.parse(argv)
        if arguments is None:
            self._err.write("usage: flyin [--visual] [map_file]\n")
            return 2
        map_file = arguments.map_file
        if map_file is None:
            map_file = self._selected_map()
        if map_file is None:
            return 2
        try:
            source_map = Path(map_file).read_text()
        except OSError as exc:
            self._err.write(f"cannot read map {map_file!r}: {exc}\n")
            return 1
        try:
            result = FlyinSolver().solve_text(source_map)
        except (MapParseError, UnsolvableMapError) as exc:
            self._err.write(f"{exc}\n")
            return 1
        for warning in result.warnings:
            self._err.write(f"{warning}\n")
        lines = (
            VisualRenderer(result.fly_in_map).render(result.movement_lines)
            if arguments.visual
            else result.movement_lines
        )
        for line in lines:
            self._out.write(f"{line}\n")
        return 0

    def _selected_map(self) -> str | None:
        """Offer the known maps and read back the one a human picks.

        The listing and the prompt are the answer to what was asked, so they
        belong on stdout; only the refusals go to stderr. Nothing here can
        reach the evaluator's output, which always names its map file.

        The option numbers are right-aligned so a two-digit option keeps the
        dots in one column. The prompt has no trailing newline, so it is
        flushed explicitly: a line-buffered stdout would otherwise hold it
        back until the answer was already typed. A blank line is written after
        the answer so the simulation does not start glued to what was typed.

        Returns:
            The path of the chosen map, or ``None`` when nothing valid was
            selected, the reason already written to stderr.
        """
        options = self._catalog.available_maps()
        if not options:
            self._err.write(
                f"no maps found under {self._catalog.root}\n"
            )
            return None
        self._out.write("\nAvailable maps:\n\n")
        width = len(str(len(options)))
        for option in options:
            self._out.write(
                f"  {option.index:>{width}}. {option.display_path}\n"
            )
        self._out.write("\nType the number of the map to run: ")
        self._out.flush()
        typed = self._in.readline().strip()
        try:
            index = int(typed)
        except ValueError:
            self._err.write(f"not a map number: {typed!r}\n")
            return None
        selected = self._catalog.option_for_index(index)
        if selected is None:
            self._err.write(f"no map numbered {index}\n")
            return None
        self._out.write("\n")
        return str(selected.path)
