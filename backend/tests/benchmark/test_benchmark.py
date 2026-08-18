from flyin.benchmark.benchmark import Benchmark
from flyin.benchmark.suite import BenchmarkSuite
from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone


def _queue_map() -> FlyInMap:
    """A start->a->goal map with 'a' at capacity 1 and two drones."""
    zones = {
        "start": Zone("start", 0, 0, is_start=True),
        "a": Zone("a", 1, 0),
        "goal": Zone("goal", 2, 0, is_end=True)
    }
    connections = [Connection("start", "a"), Connection("a", "goal")]
    return FlyInMap(
        nb_drones=2,
        zones=zones,
        connections=connections,
        start=zones["start"],
        end=zones["goal"]
    )


def test_measures_makespan_and_validity() -> None:
    result = Benchmark("queue", _queue_map(), target=4).measure()

    # Two drones pipeline through 'a' in 3 turns and the schedule is legal;
    # the target of 4 leaves a margin of -1 (one turn under the objective).
    assert result.name == "queue"
    assert result.drones == 2
    assert result.target == 4
    assert result.makespan == 3
    assert result.valid is True
    assert result.margin == -1


def test_suite_measures_every_official_map_as_valid() -> None:
    results = BenchmarkSuite().results()

    # All ten official maps are found, measured and legal.
    assert len(results) == 10
    assert all(result.valid for result in results)
