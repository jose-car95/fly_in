from fastapi.testclient import TestClient

from flyin.adapters.api.app import create_app


def test_health_endpoint_reports_ok() -> None:
    # TestClient calls the app in-process, without opening a real port.
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
