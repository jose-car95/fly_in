"""FastAPI application for the Fly-In HTTP adapter.

Builds the app that exposes the engine over HTTP (health, maps, simulate)
and allows the separate frontend origin to call it (CORS). ``FRONTEND_ORIGINS``
lists the origins the static frontend is served from in development; a browser
only lets a page read the API when its own origin is on that list.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from flyin.adapters.api.router import api_v1_router

FRONTEND_ORIGINS = [
    "http://127.0.0.1:8080",
    "http://localhost:8080"
]


def create_app() -> FastAPI:
    """Application factory used by uvicorn (``--factory``) and the tests."""
    app = FastAPI(title="jose-car Fly-In API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=FRONTEND_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"]
    )
    app.include_router(api_v1_router)
    return app
