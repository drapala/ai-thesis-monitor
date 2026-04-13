from fastapi.testclient import TestClient

from ai_thesis_monitor.api.app import create_app


def test_read_routes_are_available() -> None:
    client = TestClient(create_app())
    assert client.get("/health").status_code == 200
    assert client.get("/scores/latest").status_code == 200
    alerts_resp = client.get("/alerts", follow_redirects=False)
    assert alerts_resp.status_code == 200
    assert client.get("/narratives/latest").status_code == 200
    claim_resp = client.post("/reviews/claims/1", params={"status": "approved"})
    assert claim_resp.status_code == 200
    assert claim_resp.json() == {"claim_id": 1, "status": "approved"}
    admin_resp = client.post("/admin/jobs/daily-sync")
    assert admin_resp.status_code == 200
    assert admin_resp.json() == {"job_name": "daily-sync", "status": "accepted"}
