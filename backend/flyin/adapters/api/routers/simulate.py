"""Simulation route: runs a catalog map through the engine."""

from fastapi import APIRouter, Depends, HTTPException

from flyin.adapters.api.routers.maps import get_catalog
from flyin.adapters.api.schemas import (
    RunMetricsResponse,
    SimulateRequest,
    SimulateResponse
)
from flyin.adapters.map_catalog import MapCatalog
from flyin.application.metrics import RunMetrics
from flyin.application.solver import FlyinSolver


simulate_router = APIRouter(prefix="/simulate")


@simulate_router.post("", response_model=SimulateResponse)
def handle_simulate(
    request: SimulateRequest,
    catalog: MapCatalog = Depends(get_catalog)
) -> SimulateResponse:
    """Solve the catalog map at ``request.index`` and return its plan.

    Args:
        request: The body naming the map to run, by catalog index.
        catalog: The map catalog, injected so tests can override it.

    Returns:
        The per-turn movement lines, the run metrics and any warnings.

    Raises:
        HTTPException: 404 when no map carries the requested index.
    """
    option = catalog.option_for_index(request.index)
    if option is None:
        raise HTTPException(
            status_code=404,
            detail=f"no map with index {request.index}"
        )
    result = FlyinSolver().solve_text(option.path.read_text())
    metrics = RunMetrics(result.movement_lines)
    return SimulateResponse(
        turns=result.movement_lines,
        metrics=RunMetricsResponse(
            turns=metrics.turns,
            total_moves=metrics.total_moves,
            drones_per_turn=metrics.drones_per_turn
        ),
        warnings=result.warnings
    )
