from dataclasses import dataclass

from flyin.domain.connection import Connection
from flyin.domain.zone import Zone


@dataclass
class FlyInMap:
    nb_drones: int
    zones: dict[str, Zone]
    connections: list[Connection]
    start: Zone
    end: Zone
