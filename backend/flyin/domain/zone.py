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

    @property
    def move_cost(self) -> int | None:
        """Turns needed to enter a zone of this type.

        The cost is fixed by the subject and depends only on the destination
        type, so it belongs to the type itself. ``BLOCKED`` returns ``None``
        to mean impassable: a blocked zone is never entered and so never joins
        the traversable graph.

        Returns:
            1 for ``NORMAL`` and ``PRIORITY``, 2 for ``RESTRICTED``, or
            ``None`` for ``BLOCKED`` (impassable).
        """
        match self:
            case ZoneType.NORMAL | ZoneType.PRIORITY:
                return 1
            case ZoneType.RESTRICTED:
                return 2
            case ZoneType.BLOCKED:
                return None


@dataclass
class Zone:
    """A node of the map where drones can stand.

    Attributes:
        name: Unique identifier of the zone.
        x: X coordinate, used for visualization.
        y: Y coordinate, used for visualization.
        zone_type: Kind of the zone, which sets its movement cost.
        max_drones: Declared capacity, or ``None`` for the default (1). It is
            ignored for start/end hubs, which have unlimited capacity.
        color: Display color declared in the map, or ``None`` when absent. It
            is purely visual (used by the colored terminal view) and never
            affects routing or output.
        is_start: Whether this zone is the map's start hub.
        is_end: Whether this zone is the map's end hub.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    max_drones: int | None = None
    color: str | None = None
    is_start: bool = False
    is_end: bool = False
