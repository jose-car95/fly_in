"""FastAPI application for the Fly-In HTTP adapter.

This slice exposes only a health check; the map catalog and the simulate
endpoint arrive in later slices, registered on the same application.
"""

from fastapi import FastAPI

from flyin.adapters.api.router import api_v1_router


def create_app() -> FastAPI:
    """Application factory used by uvicorn (``--factory``) and the tests."""
    app = FastAPI(title="jose-car Fly-In API")  
    app.include_router(api_v1_router)
    return app
