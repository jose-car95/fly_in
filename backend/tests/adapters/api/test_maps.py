from pathlib import Path

from fastapi.testclient import TestClient

from flyin.adapters.api.app import create_app
from flyin.adapters.api.routers.maps import get_catalog
from flyin.adapters.map_catalog import MapCatalog


def test_maps_lists_the_catalog_as_json(tmp_path: Path) -> None:
    # Override the injected catalog with a controlled one, so the test does
    # not depend on the real maps folder.
    (tmp_path / "easy").mkdir()
    (tmp_path / "easy" / "a.txt").write_text("")
    (tmp_path / "easy" / "b.txt").write_text("")
    app = create_app()
    app.dependency_overrides[get_catalog] = lambda: MapCatalog(tmp_path)

    response = TestClient(app).get("/api/v1/maps")

    assert response.status_code == 200
    body = response.json()
    assert [item["index"] for item in body] == [1, 2]
    assert body[0]["path"].endswith("easy/a.txt")
    assert body[1]["path"].endswith("easy/b.txt")


def test_maps_serves_the_real_official_catalog() -> None:
    # Without an override it wires to the repository's own maps folder.
    response = TestClient(create_app()).get("/api/v1/maps")

    assert response.status_code == 200
    paths = [item["path"] for item in response.json()]
    assert any(path.endswith("01_linear_path.txt") for path in paths)


_DETAIL_MAP = (
    "nb_drones: 2\n"
    "start_hub: start 0 0 [color=green]\n"
    "hub: mid 1 0 [color=blue]\n"
    "end_hub: goal 2 0 [color=red]\n"
    "connection: start-mid\n"
    "connection: mid-goal\n"
)


def test_map_detail_returns_zones_and_connections(tmp_path: Path) -> None:
    (tmp_path / "m.txt").write_text(_DETAIL_MAP)
    app = create_app()
    app.dependency_overrides[get_catalog] = lambda: MapCatalog(tmp_path)

    response = TestClient(app).get("/api/v1/maps/1")

    assert response.status_code == 200
    body = response.json()
    assert body["nb_drones"] == 2
    assert body["start"] == "start"
    assert body["end"] == "goal"
    zones = {zone["name"]: zone for zone in body["zones"]}
    assert zones["start"] == {
        "name": "start", "x": 0, "y": 0,
        "type": "normal", "color": "green"
    }
    assert {tuple(sorted((c["a"], c["b"]))) for c in body["connections"]} == {
        ("mid", "start"), ("goal", "mid")
    }


def test_map_detail_unknown_index_is_404() -> None:
    response = TestClient(create_app()).get("/api/v1/maps/999999")

    assert response.status_code == 404
