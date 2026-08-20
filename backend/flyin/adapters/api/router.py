"""Root API router: groups every versioned router under ``/api/v1``."""

from fastapi import APIRouter

from flyin.adapters.api.routers.health import health_router
from flyin.adapters.api.routers.maps import maps_router
from flyin.adapters.api.routers.simulate import simulate_router


api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(maps_router)
api_v1_router.include_router(simulate_router)
