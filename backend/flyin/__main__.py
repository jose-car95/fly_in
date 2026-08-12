"""Process entry point: ``python -m flyin <map_file>``.

Wires the real standard streams and arguments into the :class:`Cli` adapter;
all the behaviour lives downstream so this stays a bare bootstrap.
"""

import sys

from flyin.adapters.cli.cli import Cli

if __name__ == "__main__":
    raise SystemExit(Cli(sys.stdout, sys.stderr).run(sys.argv[1:]))
