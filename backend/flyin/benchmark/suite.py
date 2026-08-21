"""Run the whole official-map suite and format a benchmark table.

``_TARGETS`` holds the subject's turn objective for each official map, keyed
by its path under ``maps/``: immutable reference data kept as a module-level
constant.
"""

from pathlib import Path

from flyin.benchmark.benchmark import Benchmark
from flyin.benchmark.result import BenchmarkResult
from flyin.parsing.map_parser import MapParser

_TARGETS = {
    "easy/01_linear_path.txt": 6,
    "easy/02_simple_fork.txt": 8,
    "easy/03_basic_capacity.txt": 6,
    "medium/01_dead_end_trap.txt": 12,
    "medium/02_circular_loop.txt": 15,
    "medium/03_priority_puzzle.txt": 12,
    "hard/01_maze_nightmare.txt": 30,
    "hard/02_capacity_hell.txt": 35,
    "hard/03_ultimate_challenge.txt": 45,
    "challenger/01_the_impossible_dream.txt": 45
}

_DEFAULT_MAPS_DIR = Path(__file__).resolve().parents[3] / "maps"


class BenchmarkSuite:
    """Measures every official map against its target and reports a table.

    It is the runner: it locates each map, parses it, and drives a
    :class:`Benchmark` per map. The measurement stays deterministic because
    the engine is (Dijkstra breaks ties by name, turns by drone id).

    Attributes:
        _maps_dir: The directory the official maps live in.
    """

    def __init__(self, maps_dir: Path | None = None) -> None:
        """Store where the maps live.

        Args:
            maps_dir: The maps directory; defaults to the repo's ``maps/``.
        """
        self._maps_dir = maps_dir or _DEFAULT_MAPS_DIR

    def results(self) -> list[BenchmarkResult]:
        """Measure every official map, in the target table's order.

        Returns:
            One :class:`BenchmarkResult` per map.
        """
        results: list[BenchmarkResult] = []
        for relpath, target in _TARGETS.items():
            text = (self._maps_dir / relpath).read_text()
            fly_in_map = MapParser(text).parse()
            name = relpath.removesuffix(".txt")
            results.append(Benchmark(name, fly_in_map, target).measure())
        return results

    def report(self) -> str:
        """Format the measurements as an aligned text table.

        Returns:
            A multi-line string: a header plus one row per map.
        """
        results = self.results()
        width = max(len(result.name) for result in results)
        rows = [
            f"{'map':<{width}}  drones  target  makespan  margin  valid"
        ]
        for result in results:
            valid = "yes" if result.valid else "NO"
            rows.append(
                f"{result.name:<{width}}  {result.drones:>6}  "
                f"{result.target:>6}  {result.makespan:>8}  "
                f"{result.margin:>+6}  {valid:>5}"
            )
        return "\n".join(rows)
