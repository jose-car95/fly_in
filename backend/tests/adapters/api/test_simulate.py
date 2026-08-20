from pathlib import Path

from fastapi.testclient import TestClient

from flyin.adapters.api.app import create_app
from flyin.adapters.api.routers.maps import get_catalog
from flyin.adapters.map_catalog import MapCatalog

_LINEAR_MAP = (
    "nb_drones: 2\n"
    "start_hub: start 0 0\n"
    "hub: waypoint1 1 0\n"
    "hub: waypoint2 2 0\n"
    "end_hub: goal 3 0\n"
    "connection: start-waypoint1\n"
    "connection: waypoint1-waypoint2\n"
    "connection: waypoint2-goal\n"
)


def _client_for(catalog_root: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_catalog] = lambda: MapCatalog(catalog_root)
    return TestClient(app)


def test_simulate_returns_turns_and_metrics(tmp_path: Path) -> None:
    (tmp_path / "linear.txt").write_text(_LINEAR_MAP)

    response = _client_for(tmp_path).post(
        "/api/v1/simulate", json={"index": 1}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["turns"] == [
        "D1-waypoint1",
        "D1-waypoint2 D2-waypoint1",
        "D1-goal D2-waypoint2",
        "D2-goal"
    ]
    assert body["metrics"] == {
        "turns": 4,
        "total_moves": 6,
        "drones_per_turn": 1.5
    }


def test_simulate_unknown_index_is_404() -> None:
    response = TestClient(create_app()).post(
        "/api/v1/simulate", json={"index": 999999}
    )

    assert response.status_code == 404


def test_simulate_requires_an_index() -> None:
    # FastAPI validates the body against the schema and rejects it itself.
    response = TestClient(create_app()).post("/api/v1/simulate", json={})

    assert response.status_code == 422
