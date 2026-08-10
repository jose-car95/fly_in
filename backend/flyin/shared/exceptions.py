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
