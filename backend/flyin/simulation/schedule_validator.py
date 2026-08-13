"""Independent legality check for a produced schedule."""

from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import ZoneType
from flyin.shared.exceptions import InvalidScheduleError


class ScheduleValidator:
    """Judges whether a schedule obeys the movement rules of a map.

    It is deliberately independent of the planner: it never asks how the
    schedule was produced, only whether the emitted moves are legal. Replaying
    a bad plan through it surfaces planner bugs the planner cannot see in
    itself. For now it judges a single drone (``D1``); multi-drone capacity
    checks arrive with the scheduler in M4.

    Attributes:
        _map: The map the schedule was produced for.
        _lines: The movement lines to judge, one turn each.
        _links: Undirected connections as ``frozenset`` pairs for O(1) lookup.
    """

    def __init__(
        self, fly_in_map: FlyInMap, movement_lines: list[str]
    ) -> None:
        """Store the map and the schedule to judge.

        Args:
            fly_in_map: The map the schedule was produced for.
            movement_lines: The movement lines, one per turn.
        """
        self._map = fly_in_map
        self._lines = movement_lines
        # Own adjacency, built straight from the map, so the check shares no
        # logic with the planner's Graph (that is the point of independence).
        self._links = {
            frozenset((c.zone_a, c.zone_b)) for c in fly_in_map.connections
        }

    def validate(self) -> None:
        """Replay the schedule and check every move is legal.

        Raises:
            InvalidScheduleError: On the first illegal move, or if the drone
                is left mid-flight or never reaches the end.
        """
        position = self._map.start.name
        in_flight_to: str | None = None
        for line in self._lines:
            parts = self._token_body(line).split("-")
            if len(parts) == 2:
                self._check_takeoff(position, in_flight_to, parts)
                in_flight_to = parts[1]
            elif len(parts) == 1:
                position, in_flight_to = self._check_step(
                    position, in_flight_to, parts[0]
                )
            else:
                raise InvalidScheduleError(f"malformed token {line!r}")
        if in_flight_to is not None:
            raise InvalidScheduleError(
                f"drone left in flight toward {in_flight_to!r}"
            )
        if position != self._map.end.name:
            raise InvalidScheduleError(
                f"drone ended at {position!r}, not at end "
                f"{self._map.end.name!r}"
            )

    def _check_takeoff(
        self, position: str, in_flight_to: str | None, parts: list[str]
    ) -> None:
        """Validate an in-flight ``origin-destination`` token.

        Args:
            position: The zone the drone currently stands on.
            in_flight_to: The pending destination if already mid-flight.
            parts: The token body split as ``[origin, destination]``.

        Raises:
            InvalidScheduleError: If the drone is already flying, takes off
                from elsewhere, has no connection, or aims at a non-restricted
                zone (only restricted zones use the two-turn transit).
        """
        origin, target = parts
        if in_flight_to is not None:
            raise InvalidScheduleError(
                f"took off toward {target!r} while still in flight"
            )
        if origin != position:
            raise InvalidScheduleError(
                f"in-flight from {origin!r} but drone is at {position!r}"
            )
        if not self._are_connected(origin, target):
            raise InvalidScheduleError(
                f"no connection {origin!r}-{target!r}"
            )
        if self._map.zones[target].zone_type is not ZoneType.RESTRICTED:
            raise InvalidScheduleError(
                f"in-flight token toward non-restricted zone {target!r}"
            )

    def _check_step(
        self, position: str, in_flight_to: str | None, target: str
    ) -> tuple[str, str | None]:
        """Validate a single ``D<ID>-<zone>`` arrival token.

        A pending flight must land exactly on its destination; otherwise this
        is a fresh one-turn move, legal only along a connection into a zone
        whose cost is one turn.

        Args:
            position: The zone the drone currently stands on.
            in_flight_to: The pending destination if mid-flight, else ``None``.
            target: The arrival zone named by the token.

        Returns:
            The new ``(position, in_flight_to)`` after the arrival.

        Raises:
            InvalidScheduleError: On a wrong landing zone, a missing
                connection, or a zone that cannot be entered in one turn.
        """
        if in_flight_to is not None:
            if target != in_flight_to:
                raise InvalidScheduleError(
                    f"expected arrival at {in_flight_to!r}, got {target!r}"
                )
            return target, None
        if not self._are_connected(position, target):
            raise InvalidScheduleError(
                f"no connection {position!r}-{target!r}"
            )
        if self._map.zones[target].zone_type.move_cost != 1:
            raise InvalidScheduleError(
                f"zone {target!r} cannot be entered in a single turn"
            )
        return target, None

    def _are_connected(self, a: str, b: str) -> bool:
        """Whether an undirected connection ``a-b`` exists in the map."""
        return frozenset((a, b)) in self._links

    @staticmethod
    def _token_body(line: str) -> str:
        """Strip the ``D<ID>-`` prefix and return the zone/connection body.

        Args:
            line: A single movement line, e.g. ``"D1-a"`` or ``"D1-a-r"``.

        Returns:
            The token body, e.g. ``"a"`` or ``"a-r"``.

        Raises:
            InvalidScheduleError: If the line is not a ``D<ID>-<body>`` token.
        """
        prefix, sep, body = line.strip().partition("-")
        if not sep or not prefix.startswith("D") or not body:
            raise InvalidScheduleError(f"malformed token {line!r}")
        return body
