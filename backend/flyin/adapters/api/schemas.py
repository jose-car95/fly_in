"""Pydantic schemas: the shape of the JSON the API sends and receives."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Body of ``GET /health``: a fixed liveness flag.

    Attributes:
        status: Always ``"ok"`` while the adapter can answer.
    """

    status: Literal["ok"]


class MapOption(BaseModel):
    """One selectable map in ``GET /maps``.

    Attributes:
        index: 1-based number identifying the map in the catalog.
        path: Human-readable location, relative to the catalog root.
    """

    index: int
    path: str


class SimulateRequest(BaseModel):
    """Body of ``POST /simulate``: which catalog map to run.

    Attributes:
        index: 1-based number of the map in the catalog.
    """

    index: int


class RunMetricsResponse(BaseModel):
    """Summary figures of a solved run.

    Attributes:
        turns: Turns taken to deliver every drone (the makespan).
        total_moves: Total drone-turns of movement (the total path cost).
        drones_per_turn: Average number of drones moving on a turn.
    """

    turns: int
    total_moves: int
    drones_per_turn: float


class SimulateResponse(BaseModel):
    """Body returned by ``POST /simulate``: the plan and its metrics.

    Attributes:
        turns: The per-turn movement lines, one string per turn.
        metrics: Summary figures of the run.
        warnings: Non-fatal messages raised while solving.
    """

    turns: list[str]
    metrics: RunMetricsResponse
    warnings: list[str]
