"""Measure one map's makespan and validity against its target."""

from flyin.benchmark.result import BenchmarkResult
from flyin.domain.fly_in_map import FlyInMap
from flyin.shared.exceptions import InvalidScheduleError
from flyin.simulation.schedule_validator import ScheduleValidator
from flyin.simulation.simulator import Simulator


class Benchmark:
    """Runs one map through the engine and measures it against its target.

    The makespan is the number of turns the engine emits; validity is whether
    the independent ``ScheduleValidator`` accepts that output. Validity stays
    attached to the measurement so an illegal-but-fast schedule is never
    reported as a win.

    Attributes:
        _name: The map's name, carried into the result.
        _map: The parsed map to simulate.
        _target: The subject's turn objective for the map.
    """

    def __init__(
        self, name: str, fly_in_map: FlyInMap, target: int
    ) -> None:
        """Store the map and its target.

        Args:
            name: The map's name, carried into the result.
            fly_in_map: The parsed map to simulate.
            target: The subject's turn objective for the map.
        """
        self._name = name
        self._map = fly_in_map
        self._target = target

    def measure(self) -> BenchmarkResult:
        """Simulate the map and measure its makespan and validity.

        Returns:
            The map's :class:`BenchmarkResult`.
        """
        lines = Simulator(self._map).run()
        return BenchmarkResult(
            name=self._name,
            drones=self._map.nb_drones,
            target=self._target,
            makespan=len(lines),
            valid=self._is_valid(lines)
        )

    def _is_valid(self, lines: list[str]) -> bool:
        """Whether the independent validator accepts the engine's output."""
        try:
            ScheduleValidator(self._map, lines).validate()
        except InvalidScheduleError:
            return False
        return True
