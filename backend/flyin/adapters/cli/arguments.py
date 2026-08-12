"""Command-line argument parsing for the Fly-In CLI."""


def map_file_argument(argv: list[str]) -> str | None:
    """Return the single map-file path from the arguments.

    Only one positional argument is expected (the map file). This is kept a
    tiny function of its own so argument parsing stays a separate concern from
    the flow; ``argparse`` would earn its place once the CLI grows flags.

    Args:
        argv: Command-line arguments without the program name.

    Returns:
        The map file path when exactly one argument is given, else ``None``.
    """
    return argv[0] if len(argv) == 1 else None
