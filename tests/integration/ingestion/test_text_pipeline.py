from __future__ import annotations

import httpx
import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.analytics import Claim
from ai_thesis_monitor.db.models.core import Document, DocumentChunk, RawObservation, Source
from ai_thesis_monitor.ingestion.pipelines.text import run_text_pipeline


@pytest.fixture(autouse=True)
def clean_tables(db_session: Session) -> None:
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(Source))
    db_session.commit()
    yield
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(Source))
    db_session.commit()


def test_text_pipeline_extracts_pending_review_claim(db_session: Session, rss_client: httpx.Client) -> None:
    source = Source(
        source_key="rss_corporate_ir",
        source_name="Corporate IR RSS",
        source_type="rss",
        base_url="https://rss.example.test/corporate-ir.xml",
        config={},
        reliability_score=0.8,
        active=True,
    )
    db_session.add(source)
    db_session.commit()

    result = run_text_pipeline(db_session, client=rss_client, source_keys=["rss_corporate_ir"])
    assert result.claims_created == 1

    claim = db_session.scalar(select(Claim))
    assert claim is not None
    assert claim.module_key == "labor"
    assert claim.claim_type == "headcount_reduction_ai_efficiency"
    assert claim.review_status == "pending_review"
