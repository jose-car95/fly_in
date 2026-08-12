"""CLI adapter: map file -> application layer -> stdout."""

from pathlib import Path
from typing import TextIO

from flyin.adapters.cli.arguments import map_file_argument
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
    """

    def __init__(self, out: TextIO, err: TextIO) -> None:
        """Store the output and error streams to write to.

        Args:
            out: Where the exact per-turn movement lines are written.
            err: Where clear error messages are written, off stdout.
        """
        self._out = out
        self._err = err

    def run(self, argv: list[str]) -> int:
        """Run the CLI over its arguments and return a process exit code.

        Args:
            argv: Command-line arguments without the program name; exactly one
                map file path is expected.

        Returns:
            0 on success, 2 on a usage error, 1 on a read, parse or route
            failure.
        """
        map_file = map_file_argument(argv)
        if map_file is None:
            self._err.write("usage: flyin <map_file>\n")
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
        for line in result.movement_lines:
            self._out.write(f"{line}\n")
        return 0
