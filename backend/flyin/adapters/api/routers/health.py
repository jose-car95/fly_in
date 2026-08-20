"""Health-check route: reports that the HTTP adapter is up."""

from fastapi import APIRouter

from flyin.adapters.api.schemas import HealthResponse


health_router = APIRouter(prefix="/health")


@health_router.get("", response_model=HealthResponse)
def handle_health() -> HealthResponse:
    """Report that the HTTP adapter is available."""
    return HealthResponse(status="ok")
