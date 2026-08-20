from fastapi.testclient import TestClient

from flyin.adapters.api.app import create_app


def test_api_allows_the_frontend_origin() -> None:
    # The browser only lets the page read the response when the API grants
    # its origin; TestClient is not a browser, so we check the header itself.
    client = TestClient(create_app())
    origin = "http://127.0.0.1:8080"

    response = client.get("/api/v1/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_api_does_not_grant_an_unknown_origin() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/v1/health", headers={"Origin": "http://evil.example"}
    )

    assert "access-control-allow-origin" not in response.headers
