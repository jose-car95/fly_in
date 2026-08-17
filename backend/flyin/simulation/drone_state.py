"""The lifecycle states of a drone during simulation."""

from enum import Enum, auto


class DroneState(Enum):
    """Lifecycle of a single drone as it walks its route.

    A drone is ``AT_ZONE`` when it stands on a zone ready to move,
    ``IN_TRANSIT`` while it occupies a connection toward a restricted zone
    it must land on next turn, and ``DELIVERED`` once it reaches the end.
    """

    AT_ZONE = auto()
    IN_TRANSIT = auto()
    DELIVERED = auto()
