from __future__ import annotations

import httpx
import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.analytics import Claim
from ai_thesis_monitor.db.models.core import Document, DocumentChunk, RawObservation, Source
from ai_thesis_monitor.domain.claims.extract import extract_claims
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
    _seed_rss_source(db_session)

    result = run_text_pipeline(db_session, client=rss_client, source_keys=["rss_corporate_ir"])
    assert result.claims_created == 1

    claim = db_session.scalar(select(Claim))
    assert claim is not None
    assert claim.module_key == "labor"
    assert claim.claim_type == "headcount_reduction_ai_efficiency"
    assert claim.review_status == "pending_review"


def test_text_pipeline_replay_identical_item_is_idempotent(
    db_session: Session, rss_client: httpx.Client
) -> None:
    _seed_rss_source(db_session)

    run_text_pipeline(db_session, client=rss_client, source_keys=["rss_corporate_ir"])
    run_text_pipeline(db_session, client=rss_client, source_keys=["rss_corporate_ir"])

    raw_count = db_session.scalar(select(func.count()).select_from(RawObservation))
    document_count = db_session.scalar(select(func.count()).select_from(Document))
    chunk_count = db_session.scalar(select(func.count()).select_from(DocumentChunk))
    claim_count = db_session.scalar(select(func.count()).select_from(Claim))

    assert raw_count == 1
    assert document_count == 1
    assert chunk_count == 1
    assert claim_count == 1


def test_text_pipeline_distinct_items_same_description_create_distinct_claims(db_session: Session) -> None:
    source = _seed_rss_source(db_session, base_url="https://rss.example.test/multi.xml")
    xml = """
<rss version="2.0">
  <channel>
    <item>
      <title>ServiceNow reduces workforce while increasing AI investment (Q1)</title>
      <link>https://example.com/servicenow-ai-q1</link>
      <description>ServiceNow said it would reduce workforce and invest more in AI efficiency programs.</description>
      <pubDate>Mon, 13 Apr 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>ServiceNow reduces workforce while increasing AI investment (Q2)</title>
      <link>https://example.com/servicenow-ai-q2</link>
      <description>ServiceNow said it would reduce workforce and invest more in AI efficiency programs.</description>
      <pubDate>Tue, 14 Apr 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".strip()
    client = _rss_client(xml, expected_url=source.base_url)
    try:
        result = run_text_pipeline(db_session, client=client, source_keys=["rss_corporate_ir"])
    finally:
        client.close()

    raw_count = db_session.scalar(select(func.count()).select_from(RawObservation))
    claim_count = db_session.scalar(select(func.count()).select_from(Claim))

    assert result.raw_observations == 2
    assert result.claims_created == 2
    assert raw_count == 2
    assert claim_count == 2


def test_extract_claims_requires_ai_word_boundary() -> None:
    claims = extract_claims(
        title="Company announces layoffs",
        text="The company said it would layoff 100 workers",
    )
    assert claims == []


def _seed_rss_source(db_session: Session, *, base_url: str = "https://rss.example.test/corporate-ir.xml") -> Source:
    source = Source(
        source_key="rss_corporate_ir",
        source_name="Corporate IR RSS",
        source_type="rss",
        base_url=base_url,
        config={},
        reliability_score=0.8,
        active=True,
    )
    db_session.add(source)
    db_session.commit()
    return source


def _rss_client(xml_body: str, *, expected_url: str) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == expected_url
        return httpx.Response(200, text=xml_body)

    return httpx.Client(base_url="https://rss.example.test", transport=httpx.MockTransport(handler))
