"""Zone entity: a single node of the Fly-In map."""

from dataclasses import dataclass
from enum import Enum


class ZoneType(Enum):
    """Kind of a zone, which decides the cost of moving into it.

    Movement cost depends on the destination zone: ``NORMAL`` and ``PRIORITY``
    cost 1 turn, ``RESTRICTED`` costs 2 turns, and ``BLOCKED`` is impassable.
    """

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


@dataclass
class Zone:
    """A node of the map where drones can stand.

    Attributes:
        name: Unique identifier of the zone.
        x: X coordinate (used only for visualization for now).
        y: Y coordinate (used only for visualization for now).
        zone_type: Kind of the zone, which sets its movement cost.
        max_drones: Declared capacity, or ``None`` for the default (1). It is
            ignored for start/end hubs, which have unlimited capacity.
        is_start: Whether this zone is the map's start hub.
        is_end: Whether this zone is the map's end hub.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    max_drones: int | None = None
    is_start: bool = False
    is_end: bool = False
