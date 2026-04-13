from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ai_thesis_monitor.api.app import create_app
from ai_thesis_monitor.db.models.analytics import Alert, Claim, ModuleScore, NarrativeSnapshot, NormalizedMetric
from ai_thesis_monitor.db.models.core import (
    Document,
    DocumentChunk,
    JobRun,
    MetricDefinition,
    PipelineRun,
    RawObservation,
    Source,
)


@pytest.fixture(autouse=True)
def clean_api_tables(db_session: Session) -> None:
    db_session.execute(delete(JobRun))
    db_session.execute(delete(PipelineRun))
    db_session.execute(delete(Alert))
    db_session.execute(delete(NarrativeSnapshot))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()
    yield
    db_session.execute(delete(JobRun))
    db_session.execute(delete(PipelineRun))
    db_session.execute(delete(Alert))
    db_session.execute(delete(NarrativeSnapshot))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()


def test_read_routes_return_persisted_data(db_session: Session) -> None:
    _seed_module_scores(db_session)
    alert = _seed_alert(db_session)
    _seed_narratives(db_session)
    pending_claim = _seed_claim(db_session, dedupe_key="claim-pending", review_status="pending_review")
    _seed_claim(db_session, dedupe_key="claim-approved", review_status="approved")

    app = create_app()
    assert app.state.session_factory is not None
    client = TestClient(app)

    assert client.get("/health").status_code == 200

    scores_resp = client.get("/scores/latest")
    assert scores_resp.status_code == 200
    assert scores_resp.json() == {
        "items": [
            {
                "module_key": "labor",
                "score_date": "2026-04-13",
                "score_citadel": 0.2,
                "score_citrini": 0.8,
                "confidence": 0.7,
                "winning_thesis": "citrini",
                "regime": "leaning_citrini",
                "explanation": "latest score",
            }
        ]
    }

    alerts_resp = client.get("/alerts", follow_redirects=False)
    assert alerts_resp.status_code == 200
    assert alerts_resp.json() == {
        "items": [
            {
                "id": alert.id,
                "alert_key": "labor-watch",
                "module_key": "labor",
                "severity": "high",
                "title": "Labor alert",
                "message": "Monitoring labor deterioration.",
                "triggered_at": "2026-04-13T12:00:00Z",
                "acknowledged_at": None,
                "status": "open",
            }
        ]
    }

    narratives_resp = client.get("/narratives/latest")
    assert narratives_resp.status_code == 200
    assert narratives_resp.json() == {
        "snapshot": {
            "snapshot_date": "2026-04-13",
            "overall_winner": "citrini",
            "confidence": 0.88,
            "summary": "Latest narrative snapshot",
            "module_breakdown": {"labor": "citrini"},
            "supporting_evidence": {"claims": ["claim-pending"]},
        }
    }

    claims_resp = client.get("/reviews/claims")
    assert claims_resp.status_code == 200
    assert claims_resp.json() == {
        "items": [
            {
                "id": pending_claim.id,
                "module_key": "labor",
                "claim_type": "headcount_reduction_ai_efficiency",
                "entity": "Example Co",
                "claim_text": "Example Co said AI efficiency reduced labor demand.",
                "evidence_direction": "citrini",
                "strength": 0.9,
                "confidence": 0.85,
                "evidence_date": "2026-04-13",
                "published_date": "2026-04-13",
                "review_status": "pending_review",
            }
        ]
    }


def test_review_and_admin_routes_persist_mutations(db_session: Session) -> None:
    claim = _seed_claim(db_session, dedupe_key="claim-review", review_status="pending_review")
    client = TestClient(create_app())

    claim_resp = client.post(f"/reviews/claims/{claim.id}", params={"status": "approved"})
    assert claim_resp.status_code == 200
    assert claim_resp.json() == {"claim_id": claim.id, "status": "approved"}

    db_session.expire_all()
    persisted_claim = db_session.get(Claim, claim.id)
    assert persisted_claim is not None
    assert persisted_claim.review_status == "approved"

    admin_resp = client.post("/admin/jobs/daily-sync")
    assert admin_resp.status_code == 200
    assert admin_resp.json() == {"job_name": "daily-sync", "status": "accepted"}

    pipeline_runs = db_session.scalars(select(PipelineRun).order_by(PipelineRun.id)).all()
    assert len(pipeline_runs) == 1
    assert pipeline_runs[0].run_type == "daily-sync"
    assert pipeline_runs[0].status == "accepted"
    assert pipeline_runs[0].triggered_by == "api"
    assert pipeline_runs[0].inputs == {"job_name": "daily-sync"}
    assert pipeline_runs[0].outputs_summary == {}


def test_review_claim_rejects_invalid_status(db_session: Session) -> None:
    claim = _seed_claim(db_session, dedupe_key="claim-invalid-status", review_status="pending_review")
    client = TestClient(create_app())

    response = client.post(f"/reviews/claims/{claim.id}", params={"status": "bogus"})

    assert response.status_code == 422


def test_review_claim_returns_404_for_missing_claim() -> None:
    client = TestClient(create_app())

    response = client.post("/reviews/claims/999999", params={"status": "approved"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Claim not found"}


def _seed_module_scores(db_session: Session) -> None:
    db_session.add(
        ModuleScore(
            module_key="labor",
            score_date=date(2026, 4, 6),
            score_citadel=Decimal("0.600"),
            score_citrini=Decimal("0.400"),
            confidence=Decimal("0.550"),
            winning_thesis="citadel",
            regime="balanced",
            explanation="older score",
        )
    )
    db_session.add(
        ModuleScore(
            module_key="labor",
            score_date=date(2026, 4, 13),
            score_citadel=Decimal("0.200"),
            score_citrini=Decimal("0.800"),
            confidence=Decimal("0.700"),
            winning_thesis="citrini",
            regime="leaning_citrini",
            explanation="latest score",
        )
    )
    db_session.commit()


def _seed_alert(db_session: Session) -> Alert:
    alert = Alert(
        alert_key="labor-watch",
        module_key="labor",
        severity="high",
        title="Labor alert",
        message="Monitoring labor deterioration.",
        triggered_at=datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc),
        acknowledged_at=None,
        status="open",
    )
    db_session.add(alert)
    db_session.commit()
    return alert


def _seed_narratives(db_session: Session) -> None:
    db_session.add(
        NarrativeSnapshot(
            snapshot_date=date(2026, 4, 6),
            overall_winner="citadel",
            confidence=Decimal("0.610"),
            summary="Older narrative snapshot",
            module_breakdown={"labor": "citadel"},
            supporting_evidence={"claims": ["claim-old"]},
        )
    )
    db_session.add(
        NarrativeSnapshot(
            snapshot_date=date(2026, 4, 13),
            overall_winner="citrini",
            confidence=Decimal("0.880"),
            summary="Latest narrative snapshot",
            module_breakdown={"labor": "citrini"},
            supporting_evidence={"claims": ["claim-pending"]},
        )
    )
    db_session.commit()


def _seed_claim(db_session: Session, *, dedupe_key: str, review_status: str) -> Claim:
    source = Source(
        source_key=f"source-{dedupe_key}",
        source_name=f"Source {dedupe_key}",
        source_type="rss",
        base_url=f"https://example.test/{dedupe_key}",
        config={},
        reliability_score=0.8,
        active=True,
    )
    db_session.add(source)
    db_session.flush()

    raw_observation = RawObservation(
        source_id=source.id,
        external_id=dedupe_key,
        payload={"dedupe_key": dedupe_key},
        content_hash=dedupe_key,
        published_at=datetime(2026, 4, 13, tzinfo=timezone.utc),
    )
    db_session.add(raw_observation)
    db_session.flush()

    document = Document(
        source_id=source.id,
        raw_observation_id=raw_observation.id,
        title=f"Document {dedupe_key}",
        url=f"https://example.test/docs/{dedupe_key}",
        body_text="Synthetic claim body",
        published_at=raw_observation.published_at,
    )
    db_session.add(document)
    db_session.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        chunk_text="Synthetic claim chunk",
        chunk_hash=f"{dedupe_key}-chunk",
    )
    db_session.add(chunk)
    db_session.flush()

    claim = Claim(
        source_id=source.id,
        raw_observation_id=raw_observation.id,
        document_id=document.id,
        chunk_id=chunk.id,
        module_key="labor",
        claim_type="headcount_reduction_ai_efficiency",
        entity="Example Co",
        claim_text="Example Co said AI efficiency reduced labor demand.",
        evidence_direction="citrini",
        strength=Decimal("0.900"),
        confidence=Decimal("0.850"),
        evidence_date=date(2026, 4, 13),
        published_date=date(2026, 4, 13),
        dedupe_key=dedupe_key,
        review_status=review_status,
    )
    db_session.add(claim)
    db_session.commit()
    return claim
