from fastapi.testclient import TestClient

from ai_thesis_monitor.api.app import create_app


def test_read_routes_are_available() -> None:
    client = TestClient(create_app())
    assert client.get("/health").status_code == 200
    scores_resp = client.get("/scores/latest")
    assert scores_resp.status_code == 200
    assert scores_resp.json() == {"items": []}
    alerts_resp = client.get("/alerts", follow_redirects=False)
    assert alerts_resp.status_code == 200
    assert alerts_resp.json() == {"items": []}
    narratives_resp = client.get("/narratives/latest")
    assert narratives_resp.status_code == 200
    assert narratives_resp.json() == {"snapshot": None}
    claims_resp = client.get("/reviews/claims")
    assert claims_resp.status_code == 200
    assert claims_resp.json() == {"items": []}
    claim_resp = client.post("/reviews/claims/1", params={"status": "approved"})
    assert claim_resp.status_code == 200
    assert claim_resp.json() == {"claim_id": 1, "status": "approved"}
    admin_resp = client.post("/admin/jobs/daily-sync")
    assert admin_resp.status_code == 200
    assert admin_resp.json() == {"job_name": "daily-sync", "status": "accepted"}
