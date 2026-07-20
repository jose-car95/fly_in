from flyin.domain.connection import Connection
from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import Zone

_NB_DRONES_PREFIX = "nb_drones:"
_START_HUB_PREFIX = "start_hub:"
_END_HUB_PREFIX = "end_hub:"
_CONNECTION_PREFIX = "connection:"


def parse_map(text: str) -> FlyInMap:
    lines = _significant_lines(text)

    nb_drones = _parse_nb_drones(lines[0])
    zones: dict[str, Zone] = {}
    connections: list[Connection] = []
    start: Zone | None = None
    end: Zone | None = None

    for line in lines[1:]:
        if line.startswith(_START_HUB_PREFIX):
            start = _parse_zone(line, _START_HUB_PREFIX, is_start=True)
            zones[start.name] = start
        elif line.startswith(_END_HUB_PREFIX):
            end = _parse_zone(line, _END_HUB_PREFIX, is_end=True)
            zones[end.name] = end
        elif line.startswith(_CONNECTION_PREFIX):
            connections.append(_parse_connection(line))

    if start is None or end is None:
        raise ValueError("map must declare exactly one start_hub and one end_hub")

    return FlyInMap(
        nb_drones=nb_drones,
        zones=zones,
        connections=connections,
        start=start,
        end=end,
    )


def _significant_lines(text: str) -> list[str]:
    stripped = (line.strip() for line in text.splitlines())
    return [line for line in stripped if line and not line.startswith("#")]


def _parse_nb_drones(line: str) -> int:
    if not line.startswith(_NB_DRONES_PREFIX):
        raise ValueError(f"expected 'nb_drones:' as the first significant line, got: {line!r}")
    return int(line.removeprefix(_NB_DRONES_PREFIX).strip())


def _parse_zone(line: str, prefix: str, *, is_start: bool = False, is_end: bool = False) -> Zone:
    name, x_str, y_str = line.removeprefix(prefix).split()
    return Zone(name=name, x=int(x_str), y=int(y_str), is_start=is_start, is_end=is_end)


def _parse_connection(line: str) -> Connection:
    zone_a, zone_b = line.removeprefix(_CONNECTION_PREFIX).strip().split("-", maxsplit=1)
    return Connection(zone_a=zone_a, zone_b=zone_b)
