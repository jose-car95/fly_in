"""Process entry point: ``python -m flyin [map_file]``.

Wires the real standard streams, the arguments and the repository's own map
catalog into the :class:`Cli` adapter; all the behaviour lives downstream so
this stays a bare bootstrap. Naming no map file offers the catalog to pick
from, which is why stdin and the catalog are wired in here too.
"""

import sys

from flyin.adapters.cli.cli import Cli
from flyin.adapters.map_catalog import MapCatalog

if __name__ == "__main__":
    raise SystemExit(
        Cli(
            sys.stdout,
            sys.stderr,
            sys.stdin,
            MapCatalog.official()
        ).run(sys.argv[1:])
    )
