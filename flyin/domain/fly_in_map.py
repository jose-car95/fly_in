"""FlyInMap entity: the whole parsed map."""

from dataclasses import dataclass

from flyin.domain.connection import Connection
from flyin.domain.zone import Zone


@dataclass
class FlyInMap:
    """A fully parsed Fly-In map.

    Attributes:
        nb_drones: Number of drones to route from start to end.
        zones: All zones of the map, indexed by name for O(1) lookup.
        connections: All links of the map.
        start: The start hub (also present in ``zones``).
        end: The end hub (also present in ``zones``).
    """

    nb_drones: int
    zones: dict[str, Zone]
    connections: list[Connection]
    start: Zone
    end: Zone
