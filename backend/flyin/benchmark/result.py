"""The measured outcome of benchmarking one map."""

from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """One map's measured makespan and validity against its target.

    Attributes:
        name: The map's name.
        drones: The number of drones routed (``nb_drones``).
        target: The subject's turn objective for the map.
        makespan: The turns the engine took (one line per turn).
        valid: Whether the independent validator accepted the schedule.
    """

    name: str
    drones: int
    target: int
    makespan: int
    valid: bool

    @property
    def margin(self) -> int:
        """Turns over the target (negative means under it, i.e. better)."""
        return self.makespan - self.target
