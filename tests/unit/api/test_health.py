"""Unit tests for the health route."""

from __future__ import annotations

from fastapi.testclient import TestClient

from ai_thesis_monitor.api.app import create_app


def test_health_route_uses_app_settings(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "initial-service")
    app = create_app()
    monkeypatch.setenv("APP_NAME", "changed-service")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "initial-service"}
