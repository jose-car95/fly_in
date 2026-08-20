"""Root API router: groups every versioned router under ``/api/v1``."""

from fastapi import APIRouter

from flyin.adapters.api.routers.health import health_router


api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
