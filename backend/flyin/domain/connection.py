"""Connection entity: a bidirectional link between two zones."""

from dataclasses import dataclass


@dataclass
class Connection:
    """A bidirectional link between two zones.

    Connections are undirected: ``a-b`` and ``b-a`` denote the same link, and
    declaring both is a duplicate. Only the zone names are stored here, not the
    Zone objects, to avoid duplicating state.

    Attributes:
        zone_a: Name of one endpoint zone.
        zone_b: Name of the other endpoint zone.
        max_link_capacity: Declared shared capacity of the link, or ``None``
            for the default (1).
    """

    zone_a: str
    zone_b: str
    max_link_capacity: int | None = None
