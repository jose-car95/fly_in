"""Pydantic schemas: the shape of the JSON the API sends and receives."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Body of ``GET /health``: a fixed liveness flag.

    Attributes:
        status: Always ``"ok"`` while the adapter can answer.
    """

    status: Literal["ok"]
