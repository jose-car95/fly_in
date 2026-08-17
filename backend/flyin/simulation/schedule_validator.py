"""Independent legality check for a produced schedule."""

from flyin.domain.fly_in_map import FlyInMap
from flyin.domain.zone import ZoneType
from flyin.shared.exceptions import InvalidScheduleError


class ScheduleValidator:
    """Judges whether a multi-drone schedule obeys the map's rules.

    It is deliberately independent of the planner: it replays the emitted
    movement lines and re-derives every rule from scratch, so a planner bug
    that yields an illegal schedule is caught here rather than trusted. Each
    drone is tracked by id (where it stands and whether it is mid restricted
    transit); after every turn no zone may hold more drones than its capacity.
    Link-capacity checking arrives in a later slice.

    Attributes:
        _map: The map the schedule was produced for.
        _lines: The movement lines to judge, one turn each.
        _links: Undirected connections as ``frozenset`` pairs for O(1) lookup.
        _position: Each drone's current zone, by id.
        _in_flight: Each drone's pending restricted destination, or ``None``.
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
            frozenset((c.zone_a, c.zone_b))
            for c in fly_in_map.connections
        }
        self._position: dict[int, str] = {}
        self._in_flight: dict[int, str | None] = {}

    def validate(self) -> None:
        """Replay the schedule and check every move and turn is legal.

        Raises:
            InvalidScheduleError: On the first illegal move, an overfilled
                zone, a drone left mid-flight, or one that never reaches end.
        """
        start = self._map.start.name
        ids = range(1, self._map.nb_drones + 1)
        self._position = {i: start for i in ids}
        self._in_flight = {i: None for i in ids}
        for line in self._lines:
            self._play_turn(line)
            self._check_occupancy()
        self._check_all_delivered()

    def _play_turn(self, line: str) -> None:
        """Apply one turn's tokens and enforce the per-turn drone rules.

        Args:
            line: One movement line, its tokens separated by spaces.

        Raises:
            InvalidScheduleError: If a drone moves twice, or a drone that was
                in flight fails to land this turn.
        """
        pending = {i for i, dest in self._in_flight.items() if dest}
        moved: set[int] = set()
        for token in line.split():
            drone_id = self._apply_token(token)
            if drone_id in moved:
                raise InvalidScheduleError(
                    f"drone {drone_id} appears twice in one turn"
                )
            moved.add(drone_id)
        stranded = pending - moved
        if stranded:
            raise InvalidScheduleError(
                f"drone {min(stranded)} left in flight instead of landing"
            )

    def _apply_token(self, token: str) -> int:
        """Validate a single token, mutate its drone's state, return its id.

        Args:
            token: A ``D<ID>-<zone>`` arrival or ``D<ID>-<a>-<b>`` in-flight
                token.

        Returns:
            The moving drone's id.

        Raises:
            InvalidScheduleError: If the token is malformed or its move is
                illegal.
        """
        drone_id, body = self._parse_token(token)
        parts = body.split("-")
        if len(parts) == 1:
            self._apply_arrival(drone_id, parts[0])
        elif len(parts) == 2:
            self._apply_takeoff(drone_id, parts[0], parts[1])
        else:
            raise InvalidScheduleError(f"malformed token {token!r}")
        return drone_id

    def _parse_token(self, token: str) -> tuple[int, str]:
        """Split a token into its drone id and body.

        Args:
            token: A single movement token, e.g. ``"D1-a"`` or ``"D2-a-r"``.

        Returns:
            The drone id and the token body (e.g. ``"a"`` or ``"a-r"``).

        Raises:
            InvalidScheduleError: If the token is malformed or names a drone
                outside the fleet.
        """
        prefix, sep, body = token.partition("-")
        digits = prefix[1:]
        if not sep or not body or prefix[:1] != "D" or not digits.isdigit():
            raise InvalidScheduleError(f"malformed token {token!r}")
        drone_id = int(digits)
        if drone_id not in self._position:
            raise InvalidScheduleError(f"unknown drone {drone_id}")
        return drone_id, body

    def _apply_takeoff(
        self, drone_id: int, origin: str, target: str
    ) -> None:
        """Validate a restricted take-off and mark the drone in flight.

        Args:
            drone_id: The moving drone.
            origin: The zone the drone leaves.
            target: The restricted zone it flies toward.

        Raises:
            InvalidScheduleError: If the drone is already flying, takes off
                from elsewhere, has no connection, or aims at a non-restricted
                zone (only restricted zones use the two-turn transit).
        """
        if self._in_flight[drone_id] is not None:
            raise InvalidScheduleError(
                f"drone {drone_id} took off while still in flight"
            )
        if origin != self._position[drone_id]:
            raise InvalidScheduleError(
                f"drone {drone_id} in-flight from {origin!r} but stands "
                f"at {self._position[drone_id]!r}"
            )
        if not self._are_connected(origin, target):
            raise InvalidScheduleError(f"no connection {origin!r}-{target!r}")
        if self._map.zones[target].zone_type is not ZoneType.RESTRICTED:
            raise InvalidScheduleError(
                f"in-flight token toward non-restricted zone {target!r}"
            )
        self._in_flight[drone_id] = target

    def _apply_arrival(self, drone_id: int, zone: str) -> None:
        """Validate a drone landing on or stepping into a zone.

        A pending flight must land exactly on its destination; otherwise this
        is a fresh one-turn move, legal only along a connection into a zone
        whose cost is one turn.

        Args:
            drone_id: The moving drone.
            zone: The zone named by the arrival token.

        Raises:
            InvalidScheduleError: On a wrong landing zone, a missing
                connection, or a zone that cannot be entered in one turn.
        """
        pending = self._in_flight[drone_id]
        if pending is not None:
            if zone != pending:
                raise InvalidScheduleError(
                    f"drone {drone_id} should land at {pending!r}, "
                    f"got {zone!r}"
                )
            self._in_flight[drone_id] = None
            self._position[drone_id] = zone
            return
        origin = self._position[drone_id]
        if not self._are_connected(origin, zone):
            raise InvalidScheduleError(f"no connection {origin!r}-{zone!r}")
        if self._map.zones[zone].zone_type.move_cost != 1:
            raise InvalidScheduleError(
                f"zone {zone!r} cannot be entered in a single turn"
            )
        self._position[drone_id] = zone

    def _check_occupancy(self) -> None:
        """Ensure no zone holds more parked drones than its capacity.

        In-flight drones sit on a connection, not a zone, so they are not
        counted here; they will count once they land.

        Raises:
            InvalidScheduleError: If any zone is over capacity this turn.
        """
        counts: dict[str, int] = {}
        for drone_id, zone in self._position.items():
            if self._in_flight[drone_id] is None:
                counts[zone] = counts.get(zone, 0) + 1
        for zone, count in counts.items():
            if count > self._capacity(zone):
                raise InvalidScheduleError(
                    f"zone {zone!r} holds {count} drones over capacity"
                )

    def _check_all_delivered(self) -> None:
        """Ensure every drone finished at the end and none is still flying.

        Raises:
            InvalidScheduleError: If a drone is left in flight or ends
                somewhere other than the end hub.
        """
        end = self._map.end.name
        for drone_id, zone in self._position.items():
            if self._in_flight[drone_id] is not None:
                raise InvalidScheduleError(
                    f"drone {drone_id} left in flight toward "
                    f"{self._in_flight[drone_id]!r}"
                )
            if zone != end:
                raise InvalidScheduleError(
                    f"drone {drone_id} ended at {zone!r}, not at end "
                    f"{end!r}"
                )

    def _capacity(self, zone_name: str) -> float:
        """The effective capacity of a zone (``inf`` for the terminals)."""
        zone = self._map.zones[zone_name]
        if zone.is_start or zone.is_end:
            return float("inf")
        return zone.max_drones if zone.max_drones is not None else 1

    def _are_connected(self, a: str, b: str) -> bool:
        """Whether an undirected connection ``a-b`` exists in the map."""
        return frozenset((a, b)) in self._links
