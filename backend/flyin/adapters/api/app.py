"""FastAPI application for the Fly-In HTTP adapter.

This slice exposes only a health check; the map catalog and the simulate
endpoint arrive in later slices, registered on the same application.
"""

from fastapi import FastAPI


class FlyinApi:
    """Builds and holds the Fly-In HTTP application.

    Routes are registered as methods, so the adapter stays object oriented
    and grows (maps, simulate) without free module-level handlers.

    Attributes:
        _app: The configured FastAPI application, exposed via ``app``.
    """

    def __init__(self) -> None:
        """Create the application and register its routes."""
        self._app = FastAPI(title="Fly-In API", version="0.1.0")
        self._app.add_api_route(
            "/health", self._health, methods=["GET"]
        )

    @property
    def app(self) -> FastAPI:
        """The configured application, for uvicorn and the tests."""
        return self._app

    def _health(self) -> dict[str, str]:
        """Report that the HTTP adapter is up.

        Returns:
            A small body FastAPI serializes as ``{"status": "ok"}``.
        """
        return {"status": "ok"}


def create_app() -> FastAPI:
    """Application factory used by uvicorn (``--factory``) and the tests."""
    return FlyinApi().app
