from dataclasses import dataclass


@dataclass
class Connection:
    zone_a: str
    zone_b: str
    max_link_capacity: int | None = None
