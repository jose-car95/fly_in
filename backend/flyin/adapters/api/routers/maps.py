"""Map catalog routes: list the maps and describe one for drawing."""

from fastapi import APIRouter, Depends, HTTPException

from flyin.adapters.api.schemas import (
    ConnectionDetail,
    MapDetail,
    MapOption,
    ZoneDetail
)
from flyin.adapters.map_catalog import MapCatalog
from flyin.application.solver import FlyinSolver


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


@maps_router.get("/{index}", response_model=MapDetail)
def handle_map_detail(
    index: int,
    catalog: MapCatalog = Depends(get_catalog)
) -> MapDetail:
    """Return the structure of the catalog map at ``index``, for drawing.

    Args:
        index: 1-based number of the map in the catalog.
        catalog: The map catalog, injected so tests can override it.

    Returns:
        The map's drones, terminals, zones and connections.

    Raises:
        HTTPException: 404 when no map carries the requested index.
    """
    option = catalog.option_for_index(index)
    if option is None:
        raise HTTPException(
            status_code=404,
            detail=f"no map with index {index}"
        )
    fly_in_map = FlyinSolver().load_text(option.path.read_text())
    return MapDetail(
        nb_drones=fly_in_map.nb_drones,
        start=fly_in_map.start.name,
        end=fly_in_map.end.name,
        zones=[
            ZoneDetail(
                name=zone.name,
                x=zone.x,
                y=zone.y,
                type=zone.zone_type.value,
                color=zone.color
            )
            for zone in fly_in_map.zones.values()
        ],
        connections=[
            ConnectionDetail(a=connection.zone_a, b=connection.zone_b)
            for connection in fly_in_map.connections
        ]
    )
