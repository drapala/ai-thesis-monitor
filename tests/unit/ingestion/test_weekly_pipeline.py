from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.analytics import (
    Alert,
    Claim,
    ModuleScore,
    NarrativeSnapshot,
    NormalizedMetric,
    ScoreEvidence,
    TripwireEvent,
)
from ai_thesis_monitor.db.models.core import Document, DocumentChunk, MetricDefinition, RawObservation, Source
from ai_thesis_monitor.ingestion.pipelines.weekly import run_weekly_pipeline


@pytest.fixture(autouse=True)
def clean_weekly_tables(db_session: Session) -> None:
    db_session.execute(delete(Alert))
    db_session.execute(delete(TripwireEvent))
    db_session.execute(delete(NarrativeSnapshot))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(ScoreEvidence))
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()
    yield
    db_session.execute(delete(Alert))
    db_session.execute(delete(TripwireEvent))
    db_session.execute(delete(NarrativeSnapshot))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(ScoreEvidence))
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()


def test_run_weekly_pipeline_persists_outputs_for_explicit_score_date(db_session: Session) -> None:
    score_date = date(2026, 4, 6)
    _seed_weekly_inputs(db_session, score_date=score_date)

    result = run_weekly_pipeline(session=db_session, score_date=score_date)

    assert result.module_scores_written == 1
    assert result.tripwires_written == 1
    assert result.alerts_written == 1
    assert result.narratives_written == 1

    assert db_session.scalar(select(func.count()).select_from(ScoreEvidence)) == 2
    assert db_session.scalar(select(func.count()).select_from(ModuleScore)) == 1
    assert db_session.scalar(select(func.count()).select_from(TripwireEvent)) == 1
    assert db_session.scalar(select(func.count()).select_from(Alert)) == 1
    assert db_session.scalar(select(func.count()).select_from(NarrativeSnapshot)) == 1

    module_score = db_session.scalar(select(ModuleScore))
    assert module_score is not None
    assert module_score.module_key == "labor"
    assert module_score.score_date == score_date
    assert module_score.winning_thesis == "citrini"

    tripwire = db_session.scalar(select(TripwireEvent))
    assert tripwire is not None
    assert tripwire.tripwire_key == "labor_critical_claim"
    assert tripwire.event_date == score_date

    narrative = db_session.scalar(select(NarrativeSnapshot))
    assert narrative is not None
    assert narrative.snapshot_date == score_date
    assert narrative.overall_winner == "citrini"

    rerun = run_weekly_pipeline(session=db_session, score_date=score_date)

    assert rerun == result
    assert db_session.scalar(select(func.count()).select_from(ScoreEvidence)) == 2
    assert db_session.scalar(select(func.count()).select_from(ModuleScore)) == 1
    assert db_session.scalar(select(func.count()).select_from(TripwireEvent)) == 1
    assert db_session.scalar(select(func.count()).select_from(Alert)) == 1
    assert db_session.scalar(select(func.count()).select_from(NarrativeSnapshot)) == 1


def _seed_weekly_inputs(db_session: Session, *, score_date: date) -> None:
    source = Source(
        source_key="weekly_unit_source",
        source_name="Weekly Unit Source",
        source_type="test",
        base_url="https://example.test/weekly",
        config={},
        reliability_score=0.82,
        active=True,
    )
    metric_definition = MetricDefinition(
        metric_key="software_postings_yoy",
        module_key="labor",
        name="Software Job Postings YoY",
        description="Synthetic test metric for weekly scoring",
        frequency="weekly",
        unit="index",
        lag_category="short",
        weight=1.2,
        expected_direction_citadel="up",
        expected_direction_citrini="down",
        primary_feature_key="value",
        signal_transform="identity",
        min_history_points=1,
        is_leading=True,
        config={},
        is_active=True,
    )
    db_session.add(source)
    db_session.add(metric_definition)
    db_session.flush()

    raw_observation = RawObservation(
        source_id=source.id,
        external_id="weekly-unit-raw",
        payload={"kind": "weekly"},
        content_hash="weekly-unit-raw",
        published_at=datetime(2026, 4, 5, tzinfo=timezone.utc),
    )
    db_session.add(raw_observation)
    db_session.flush()

    document = Document(
        source_id=source.id,
        raw_observation_id=raw_observation.id,
        title="Weekly labor evidence",
        url="https://example.test/weekly/labor",
        body_text="Synthetic weekly evidence body",
        published_at=raw_observation.published_at,
    )
    db_session.add(document)
    db_session.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        chunk_text="Synthetic weekly evidence chunk",
        chunk_hash="weekly-unit-chunk",
    )
    db_session.add(chunk)
    db_session.flush()

    db_session.add(
        NormalizedMetric(
            metric_definition_id=metric_definition.id,
            source_id=source.id,
            raw_observation_id=raw_observation.id,
            geo=None,
            segment=None,
            observed_date=score_date,
            value=Decimal("-0.900"),
            quality_score=Decimal("0.850"),
            notes="Negative normalized trend for labor",
        )
    )
    db_session.add(
        Claim(
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
            evidence_date=score_date,
            published_date=score_date,
            dedupe_key="weekly-unit-claim",
            review_status="pending_review",
        )
    )
    db_session.commit()
