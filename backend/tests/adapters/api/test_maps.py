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
