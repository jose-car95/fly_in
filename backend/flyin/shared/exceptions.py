"""Common exception types shared across the Fly-In layers."""


class MapParseError(Exception):
    """Raised when a map file cannot be parsed into a valid world.

    Every failure while reading a map is reported as this single type, so a
    caller can catch parse failures without knowing which low-level check
    tripped. Messages carry the physical 1-based line and the cause whenever a
    specific line is to blame. It deliberately does not subclass ``ValueError``
    so the parser can wrap the raw ``ValueError``/``IndexError`` of malformed
    input without catching its own errors by accident.
    """


class UnsolvableMapError(Exception):
    """Raised when the start hub cannot reach the end hub.

    The map is well-formed (it parsed), but no route exists, so simulating it
    would never finish. Distinct from :class:`MapParseError`, which is about
    malformed input rather than an unreachable goal.
    """


class InvalidScheduleError(Exception):
    """Raised when a produced schedule breaks a movement rule.

    The independent ``ScheduleValidator`` raises this on the first illegal
    move (a hop with no connection, a wrong restricted-transit shape, or a
    drone that never reaches the end). It judges an already-produced
    schedule, so a planner bug that yields an illegal output is caught here
    rather than trusted.
    """
