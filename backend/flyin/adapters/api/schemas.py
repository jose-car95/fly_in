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
