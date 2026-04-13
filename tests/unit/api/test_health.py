"""Unit tests for the health route."""

from __future__ import annotations

from fastapi.testclient import TestClient

from ai_thesis_monitor.api.app import create_app


def test_health_route_exposes_status() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-thesis-monitor"}
