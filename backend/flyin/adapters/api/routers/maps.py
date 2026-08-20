"""Map catalog route: lists the maps a client can simulate."""

from fastapi import APIRouter, Depends

from flyin.adapters.api.schemas import MapOption
from flyin.adapters.map_catalog import MapCatalog


maps_router = APIRouter(prefix="/maps")


def get_catalog() -> MapCatalog:
    """Provide the official catalog, injectable so tests can override it."""
    return MapCatalog.official()


@maps_router.get("", response_model=list[MapOption])
def handle_maps(
    catalog: MapCatalog = Depends(get_catalog)
) -> list[MapOption]:
    """List every known map as ``{index, path}`` in catalog order."""
    return [
        MapOption(index=option.index, path=option.display_path)
        for option in catalog.available_maps()
    ]
