"""Runtime state of a single drone as it walks its assigned route."""

from flyin.simulation.drone_state import DroneState


class Drone:
    """A drone moving along a fixed route, one hop at a time.

    It owns its own lifecycle: where it stands on the route and whether it is
    parked on a zone, in flight toward a restricted zone, or delivered. The
    simulator decides *whether* a move is allowed (capacity); the drone only
    knows *how* to advance along its own route.

    Attributes:
        id: The 1-based identifier used in the output tokens.
    """

    def __init__(self, drone_id: int, route: tuple[str, ...]) -> None:
        """Place the drone at the start of its route.

        Args:
            drone_id: The 1-based identifier for the output tokens.
            route: The ordered zone names from start to end.
        """
        self.id = drone_id
        self._route = route
        self._index = 0
        # A one-zone route means start is the end: nothing to deliver.
        self._state = (
            DroneState.DELIVERED if len(route) == 1
            else DroneState.AT_ZONE
        )

    @property
    def is_active(self) -> bool:
        """Whether the drone still has moves left (it is not delivered)."""
        return self._state is not DroneState.DELIVERED

    @property
    def is_at_zone(self) -> bool:
        """Whether the drone is parked on a zone, ready to move."""
        return self._state is DroneState.AT_ZONE

    @property
    def is_in_transit(self) -> bool:
        """Whether the drone is mid-flight toward a restricted zone."""
        return self._state is DroneState.IN_TRANSIT

    @property
    def route_position(self) -> int:
        """The drone's index along its route (0 is the start)."""
        return self._index

    @property
    def current_zone(self) -> str:
        """The zone the drone stands on (its origin while in transit)."""
        return self._route[self._index]

    @property
    def next_zone(self) -> str:
        """The next zone on the route; defined while the drone is active."""
        return self._route[self._index + 1]

    def takeoff(self) -> str:
        """Begin a two-turn restricted transit; return the in-flight token.

        The drone does not advance yet: it occupies the connection this turn
        and must land next turn.
        """
        origin, target = self.current_zone, self.next_zone
        self._state = DroneState.IN_TRANSIT
        return f"D{self.id}-{origin}-{target}"

    def advance(self) -> str:
        """Step onto the next zone and return the arrival token.

        Serves both a normal one-turn move and the landing that completes a
        restricted transit; both end with the drone parked on the next zone
        (or delivered if that zone is the end).
        """
        self._index += 1
        self._state = (
            DroneState.DELIVERED
            if self._index == len(self._route) - 1
            else DroneState.AT_ZONE
        )
        return f"D{self.id}-{self.current_zone}"
