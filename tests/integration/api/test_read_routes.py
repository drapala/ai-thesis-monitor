from fastapi.testclient import TestClient

from ai_thesis_monitor.api.app import create_app


def test_read_routes_are_available() -> None:
    client = TestClient(create_app())
    assert client.get("/health").status_code == 200
    assert client.get("/scores/latest").status_code == 200
    assert client.get("/alerts").status_code == 200
    assert client.get("/narratives/latest").status_code == 200
