"""Command-line argument parsing for the Fly-In CLI."""

from dataclasses import dataclass

VISUAL_FLAG = "--visual"


@dataclass(frozen=True, slots=True)
class CliArguments:
    """What the CLI was asked to do, once the arguments are understood.

    Attributes:
        map_file: Path of the map to solve, or ``None`` when none was named
            and the human should be offered the catalog instead.
        visual: Whether the colored human view was requested.
    """

    map_file: str | None
    visual: bool

    @classmethod
    def parse(cls, argv: list[str]) -> "CliArguments | None":
        """Read the arguments, or reject them as a usage error.

        Kept hand-rolled rather than delegated to ``argparse``: the CLI has a
        single flag, and ``argparse`` writes straight to the real stderr and
        exits the process, which would break the injected streams that make
        this adapter testable without a subprocess.

        Args:
            argv: Command-line arguments without the program name.

        Returns:
            The parsed arguments, or ``None`` when the invocation is invalid
            (an unknown flag, or more than one map file).
        """
        flags = [word for word in argv if word.startswith("-")]
        map_files = [word for word in argv if not word.startswith("-")]
        if len(map_files) > 1 or any(flag != VISUAL_FLAG for flag in flags):
            return None
        return cls(
            map_file=map_files[0] if map_files else None,
            visual=VISUAL_FLAG in flags
        )
