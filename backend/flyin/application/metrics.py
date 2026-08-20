"""Summary figures of a solved run, counted from its movement lines.

An application-level value object used by any adapter that presents a run:
the CLI visual view and the HTTP API both build it from the same movement
lines, so their numbers can never disagree with the plan.
"""


class RunMetrics:
    """Summary figures of a solved run, counted from its output.

    The counting rests on one fact of the output format: each token is one
    drone spending one turn. A normal move prints one token and costs one
    turn; a two-turn restricted transit prints two (an in-flight token then
    a landing token). ``total_moves`` is therefore the token count, and it
    equals the total path cost (normal costs 1 and prints 1, restricted
    costs 2 and prints 2), with no move cost re-derived here.

    Attributes:
        _lines: The per-turn movement lines the run produced.
    """

    def __init__(self, movement_lines: list[str]) -> None:
        """Store the run's output.

        Args:
            movement_lines: The exact per-turn lines the engine produced.
        """
        self._lines = movement_lines

    @property
    def turns(self) -> int:
        """Turns taken to deliver every drone (the makespan)."""
        return len(self._lines)

    @property
    def total_moves(self) -> int:
        """Total drone-turns of movement, equal to the total path cost."""
        return sum(len(line.split()) for line in self._lines)

    @property
    def drones_per_turn(self) -> float:
        """Average number of drones moving on a turn (the throughput).

        Returns 0 for a run with no turns, so an already-solved map does not
        divide by zero.
        """
        if not self._lines:
            return 0.0
        return self.total_moves / self.turns
