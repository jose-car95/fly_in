"""Discovery of the map files an adapter can offer to pick from.

Lives beside the adapters rather than inside ``cli`` because the catalog is
not a CLI idea: any front-end that lets a human choose a known map needs the
very same numbered list (an HTTP endpoint would serve it as JSON).
"""

from dataclasses import dataclass
from pathlib import Path

MAPS_DIRNAME = "maps"


@dataclass(frozen=True, slots=True)
class MapFileOption:
    """One selectable map file, as offered to a human.

    Attributes:
        index: 1-based position in the catalog, the number a human types.
        path: Location of the file, ready to be read.
        display_path: Short label to show, relative to the catalog root.
    """

    index: int
    path: Path
    display_path: str


class MapCatalog:
    """The map files under one directory, numbered for selection.

    Attributes:
        root: Directory scanned recursively for ``.txt`` map files.
    """

    def __init__(self, root: Path) -> None:
        """Store the directory to scan.

        Args:
            root: Directory holding the map files, scanned recursively.
        """
        self.root = root

    @classmethod
    def official(cls) -> "MapCatalog":
        """Return the catalog of the repository's own map folder.

        Walks up from this file until a ``maps`` directory shows up, so the
        catalog keeps working wherever the package sits in the tree; counting
        parent levels would silently break the day a module moves.

        Returns:
            A catalog rooted at the repository maps folder, or at a bare
            ``maps`` path when none was found, which simply lists nothing.
        """
        for folder in Path(__file__).parents:
            candidate = folder / MAPS_DIRNAME
            if candidate.is_dir():
                return cls(candidate)
        return cls(Path(MAPS_DIRNAME))

    def available_maps(self) -> tuple[MapFileOption, ...]:
        """Return every map file, numbered from 1 in a stable order.

        Sorting by path keeps the numbering reproducible across runs and
        machines, so a number a human read stays the same map.

        Returns:
            The options in ascending path order, empty when the root is
            missing or holds no map file.
        """
        paths = sorted(
            path for path in self.root.rglob("*.txt") if path.is_file()
        )
        return tuple(
            MapFileOption(
                index=index,
                path=path,
                display_path=self._label(path)
            )
            for index, path in enumerate(paths, start=1)
        )

    def option_for_index(self, index: int) -> MapFileOption | None:
        """Return the option a human selected by number.

        Args:
            index: The 1-based number typed in, not trusted to be in range.

        Returns:
            The matching option, or ``None`` when no option carries that
            number.
        """
        for option in self.available_maps():
            if option.index == index:
                return option
        return None

    def _label(self, path: Path) -> str:
        """Return the display label of one map file.

        Keeps the root folder name in front so the label reads like the path
        a human would type (``maps/easy/01_linear_path.txt``).

        Args:
            path: A map file found under the root.

        Returns:
            The label to print next to the option number.
        """
        relative = path.relative_to(self.root)
        return f"{self.root.name}/{relative.as_posix()}"
